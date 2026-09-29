"""
COSMOS AI — Mars Mission Planner
Surface Power, Consumables & Battery State-of-Charge Engine
Grounding: MSL MMRTG Baselines & 500-Sol Mission Life Projections
"""

import math
from typing import Dict, Any, List

def evaluate_surface_power(power_source: str = "mmrtg",
                           mission_sols: int = 500,
                           daily_traverse_m: float = 80.0,
                           terrain_key: str = "sand_dune",
                           wheel_mode: str = "dynamic",
                           atmospheric_dust_tau: float = 0.6) -> Dict[str, Any]:
    """
    Evaluates 500-Sol surface power generation, consumption, and battery margins.
    Integrates the extra power draw of autonomous dynamic cleat actuation.
    """
    from core.mobility import simulate_traverse_step
    
    # 1. Power Generation (Wh per Sol)
    if power_source.lower() == "mmrtg":
        # Multi-Mission Radioisotope Thermoelectric Generator (Curiosity heritage)
        # ~110 W continuous electric power (110 W * 24.65 hr = ~2710 Wh/sol)
        # Decays at ~1.6% per Earth year (~1.0% per Martian year)
        power_gen_continuous_w = 110.0
        daily_energy_generated_wh = power_gen_continuous_w * 24.65 # ~2711 Wh/sol
        dust_penalty_factor = 1.0 # RTG is immune to dust deposition
        waste_heat_available_w = 2000.0 # Heat piped to avionics, reducing electric heating needs
        night_heating_power_wh = 150.0 # Small supplementary survival heat
    else: # solar
        # Solar Array (~3.5 m^2 triple-junction GaAs cells)
        # Peak daylight power ~450 W; daylight duration ~12.3 hours
        # Atmospheric dust extinction: I = I0 * exp(-tau / cos(theta))
        dust_penalty_factor = math.exp(-atmospheric_dust_tau * 0.75) # ~0.64 for tau=0.6
        peak_solar_w = 450.0 * dust_penalty_factor
        daily_energy_generated_wh = peak_solar_w * 6.5 # ~1870 Wh/sol under nominal tau
        waste_heat_available_w = 0.0
        night_heating_power_wh = 480.0 # High electric heating demand at night

    # 2. Power Consumption
    # Housekeeping & computer: ~65 W continuous
    housekeeping_wh = 65.0 * 24.65 # ~1602 Wh/sol
    # Communications (UHF relay + X-band DTE): ~180 Wh/sol
    telecom_wh = 180.0
    # Science payloads & instruments: ~280 Wh/sol
    science_wh = 280.0

    # 3. Mobility Energy Consumption (from dynamic wheel simulation)
    mobility_sim = simulate_traverse_step(
        terrain_key=terrain_key,
        wheel_mode=wheel_mode,
        distance_m=daily_traverse_m
    )
    mobility_wh = mobility_sim["total_energy_wh"]

    # 4. Total Daily Energy Balance
    total_daily_consumption_wh = (
        housekeeping_wh + 
        telecom_wh + 
        science_wh + 
        night_heating_power_wh + 
        mobility_wh
    )
    
    daily_net_margin_wh = daily_energy_generated_wh - total_daily_consumption_wh

    # 5. Battery State-of-Charge (SoC)
    # Rover battery capacity: 2x 43 Ah Li-ion batteries at 28V -> ~2400 Wh
    battery_capacity_wh = 2400.0
    
    # Check night-time minimum depth of discharge (DoD)
    # Night drain: housekeeping (12h) + night heating
    night_drain_wh = (65.0 * 12.3) + night_heating_power_wh
    min_night_soc_percent = max(0.0, (1.0 - (night_drain_wh / battery_capacity_wh)) * 100.0)

    # 500-Sol Longevity Assessment
    if daily_net_margin_wh >= 0:
        sustainable_sols = mission_sols
        power_feasibility = "PASS"
        power_status_message = f"Sustainable: Daily net energy margin is +{daily_net_margin_wh:.0f} Wh/sol."
    else:
        # Deficit mode: battery will drain
        deficit_per_sol = abs(daily_net_margin_wh)
        sustainable_sols = min(mission_sols, int(battery_capacity_wh / deficit_per_sol))
        power_feasibility = "FAIL"
        power_status_message = f"DEFICIT: Daily deficit of {deficit_per_sol:.0f} Wh/sol. Mission exhausts battery in ~{sustainable_sols} sols."

    return {
        "power_source": power_source.upper(),
        "mission_sols": mission_sols,
        "daily_energy_generated_wh": daily_energy_generated_wh,
        "dust_penalty_factor": dust_penalty_factor,
        "housekeeping_wh": housekeeping_wh,
        "telecom_wh": telecom_wh,
        "science_wh": science_wh,
        "night_heating_wh": night_heating_power_wh,
        "mobility_wh": mobility_wh,
        "total_daily_consumption_wh": total_daily_consumption_wh,
        "daily_net_margin_wh": daily_net_margin_wh,
        "battery_capacity_wh": battery_capacity_wh,
        "min_night_soc_percent": min_night_soc_percent,
        "sustainable_sols": sustainable_sols,
        "power_feasibility": power_feasibility,
        "status_message": power_status_message,
        "mobility_details": mobility_sim
    }
