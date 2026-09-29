"""
COSMOS AI — Mars Mission Planner
Powered Descent Propulsion & Landing Burn Engine
Grounding: Karlgaard et al. (MEADS), Korzun & Edquist (SRP Readiness), & Cano et al.
"""

import math
from typing import Dict, Any
from core.units import G_EARTH, G_MARS, assert_si_mass, assert_si_velocity

# Standard descent engine performance
DESCENT_ENGINE_ISP_S = 228.0 # Hydrazine monopropellant / bipropellant descent engines

def calculate_powered_landing_burn(backshell_velocity_m_s: float = 79.0, 
                                   rover_mass_kg: float = 500.0,
                                   burn_duration_s: float = 38.0,
                                   divert_delta_v_m_s: float = 15.0) -> Dict[str, Any]:
    """
    Computes powered landing burn delta-v and propellant consumption.
    Accounts for:
    1. Kinematic deceleration (79 m/s -> 0.75 m/s)
    2. Continuous Martian gravitational loss (g_mars * delta_t)
    3. Terminal divert maneuver delta-v
    """
    assert_si_velocity(backshell_velocity_m_s, "Backshell Separation Velocity")
    assert_si_mass(rover_mass_kg, "Rover Mass")

    # 1. Kinematic velocity change
    touchdown_velocity_m_s = 0.75
    delta_v_kinematic = backshell_velocity_m_s - touchdown_velocity_m_s # ~78.25 m/s

    # 2. Gravity loss penalty: Mars gravity * burn duration * average sine angle
    # Descent angle averages ~75° to 90° from horizontal during powered vertical descent
    effective_sin_theta = math.sin(math.radians(82.0))
    delta_v_gravity_loss = G_MARS * effective_sin_theta * burn_duration_s # ~3.72 * 0.99 * 38 ~ 140 m/s

    # 3. Total Powered Descent Delta-v
    delta_v_landing_m_s = delta_v_kinematic + delta_v_gravity_loss + divert_delta_v_m_s # ~233 m/s (~225-235 m/s)

    # Descent Stage Dry Mass (Descent Stage structure, avionics, rigging: ~0.75 * rover mass)
    descent_stage_dry_kg = rover_mass_kg * 0.78 # ~390 kg for 500 kg rover
    total_landed_dry_kg = rover_mass_kg + descent_stage_dry_kg # mass at touchdown

    # Tsiolkovsky Rocket Equation: m_wet = m_dry * exp(Delta_v / (Isp * g0))
    effective_c = DESCENT_ENGINE_ISP_S * G_EARTH # exhaust velocity ~2236 m/s
    mass_ratio = math.exp(delta_v_landing_m_s / effective_c)
    descent_stage_wet_kg = total_landed_dry_kg * mass_ratio
    propellant_consumed_kg = descent_stage_wet_kg - total_landed_dry_kg

    # Propellant reserve margin (10% flight reserve for descent fuel)
    propellant_reserve_kg = propellant_consumed_kg * 0.10
    total_propellant_loaded_kg = propellant_consumed_kg + propellant_reserve_kg

    # Korzun & Edquist Technology Readiness Level Check
    # MSL Sky Crane proven up to ~1,025 kg landed rover mass (TRL 9).
    # Heavier payloads (>1,500 kg) require Supersonic Retropropulsion (TRL 3-4).
    if rover_mass_kg <= 1050.0:
        trl_rating = 9
        propulsion_architecture = "MSL-Heritage Sky Crane (Flight Proven)"
        trl_risk_flag = False
        trl_notes = "Architecture flight-proven by Curiosity (2012) and Perseverance (2021)."
    else:
        trl_rating = 3
        propulsion_architecture = "Supersonic Retropropulsion (SRP)"
        trl_risk_flag = True
        trl_notes = "Supersonic retropropulsion sits at TRL 3-4 with unvalidated aero below Mach 1.4 and deep throttling risks (Korzun & Edquist)."

    return {
        "delta_v_kinematic_m_s": delta_v_kinematic,
        "delta_v_gravity_loss_m_s": delta_v_gravity_loss,
        "delta_v_divert_m_s": divert_delta_v_m_s,
        "delta_v_landing_m_s": delta_v_landing_m_s, # ~225 - 233 m/s
        "rover_mass_kg": rover_mass_kg,
        "descent_stage_dry_kg": descent_stage_dry_kg,
        "total_landed_dry_kg": total_landed_dry_kg,
        "propellant_consumed_kg": propellant_consumed_kg,
        "propellant_reserve_kg": propellant_reserve_kg,
        "total_propellant_loaded_kg": total_propellant_loaded_kg,
        "total_descent_wet_mass_kg": total_landed_dry_kg + total_propellant_loaded_kg,
        "trl_rating": trl_rating,
        "propulsion_architecture": propulsion_architecture,
        "trl_risk_flag": trl_risk_flag,
        "trl_notes": trl_notes
    }
