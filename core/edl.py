"""
COSMOS AI — Mars Mission Planner
Entry, Descent & Landing (EDL) Simulation Engine
Grounding: Cruz et al. (MSL Parachute), Karlgaard et al. (MEADS), & Hwang et al. (MEDLI2)
"""

import math
from typing import Dict, Any, List, Tuple
import numpy as np
from core.units import G_MARS, assert_si_velocity, assert_si_mass, assert_si_force

# Flight-validated parachute structural rating
PARACHUTE_STRUCTURAL_LIMIT_N = 289000.0  # 289 kN
PARACHUTE_DIAMETER_M = 21.35             # 21.35 m Disk-Gap-Band (DGB)
PARACHUTE_AREA_M2 = math.pi * (PARACHUTE_DIAMETER_M / 2.0)**2
PARACHUTE_CD = 0.624                     # Reconstructed drag coefficient

def mars_atmospheric_density(altitude_m: float) -> float:
    """Standard Martian atmospheric exponential density profile (kg/m^3)."""
    # Surface density rho0 ~ 0.015 kg/m^3, scale height H ~ 11.1 km
    if altitude_m < 0.0:
        altitude_m = 0.0
    h_scale = 11100.0 # meters
    rho0 = 0.0155     # kg/m^3
    return rho0 * math.exp(-altitude_m / h_scale)

def simulate_edl(entry_velocity_m_s: float, entry_angle_deg: float, total_entry_mass_kg: float) -> Dict[str, Any]:
    """
    Simulates Mars atmospheric entry down to terminal descent.
    Validates parachute deployment conditions, peak structural load, and MEADS staging.
    """
    assert_si_velocity(entry_velocity_m_s, "Entry Velocity")
    assert_si_mass(total_entry_mass_kg, "Total Entry Mass")

    gamma_rad = math.radians(abs(entry_angle_deg))

    # Aeroshell properties (MSL heritage: diameter 4.5m, Cd ~ 1.6 in hypersonic flow)
    aeroshell_diameter_m = 4.5
    s_aeroshell = math.pi * (aeroshell_diameter_m / 2.0)**2
    cd_hypersonic = 1.62
    ballistic_coef = total_entry_mass_kg / (cd_hypersonic * s_aeroshell) # ~140 kg/m^2

    # Peak deceleration during hypersonic entry:
    # a_max ~ (V_E^2 * sin(gamma)) / (2 * e * H)
    h_scale = 11100.0
    a_max_m_s2 = (entry_velocity_m_s**2 * math.sin(gamma_rad)) / (2.0 * math.e * h_scale)
    peak_g_load = a_max_m_s2 / 9.80665 # Earth g's (~10 to 14 g)

    # Parachute deployment condition (Karlgaard / Cruz baseline: Mach 1.75)
    # Speed of sound in cold CO2 atmosphere ~ 235 m/s
    speed_of_sound_deploy = 235.0
    deploy_mach = 1.75
    deploy_velocity_m_s = deploy_mach * speed_of_sound_deploy # ~411 m/s
    deploy_altitude_m = 9800.0 # ~9.8 km AGL
    
    rho_deploy = mars_atmospheric_density(deploy_altitude_m)
    dynamic_pressure_pa = 0.5 * rho_deploy * (deploy_velocity_m_s ** 2) # ~493 Pa

    # Parachute Peak Opening Load
    # Cruz et al. reconstructed peak load: 153.8 kN
    opening_shock_factor = 1.18
    peak_opening_load_n = dynamic_pressure_pa * PARACHUTE_CD * PARACHUTE_AREA_M2 * opening_shock_factor
    peak_opening_load_kn = peak_opening_load_n / 1000.0

    # Safety margin check vs 289 kN limit
    parachute_margin = PARACHUTE_STRUCTURAL_LIMIT_N / peak_opening_load_n
    parachute_pass = peak_opening_load_n < PARACHUTE_STRUCTURAL_LIMIT_N

    # MEADS Staging Kinematics Reconstruction
    stages = [
        {"event": "Atmospheric Entry Interface", "altitude_m": 125000.0, "velocity_m_s": entry_velocity_m_s, "mach": entry_velocity_m_s / 240.0},
        {"event": "Peak Heating & Deceleration", "altitude_m": 29000.0, "velocity_m_s": 2900.0, "mach": 12.1},
        {"event": "Parachute Deploy", "altitude_m": deploy_altitude_m, "velocity_m_s": deploy_velocity_m_s, "mach": deploy_mach},
        {"event": "Heatshield Jettison", "altitude_m": 7200.0, "velocity_m_s": 160.0, "mach": 0.70},
        {"event": "Backshell Separation", "altitude_m": 1600.0, "velocity_m_s": 79.0, "mach": 0.34},
        {"event": "Powered Divert Complete", "altitude_m": 450.0, "velocity_m_s": 32.0, "mach": 0.14},
        {"event": "Throttle-Down / Constant Decel", "altitude_m": 140.0, "velocity_m_s": 0.75, "mach": 0.003},
        {"event": "Sky Crane Initiation", "altitude_m": 18.6, "velocity_m_s": 0.75, "mach": 0.003},
        {"event": "Rover Touchdown", "altitude_m": 0.0, "velocity_m_s": 0.0, "mach": 0.0}
    ]

    # Generate descent trajectory points for plotting
    altitudes = np.linspace(125000, 0, 100)
    velocities = []
    for h in altitudes:
        if h > deploy_altitude_m:
            # Hypersonic/supersonic atmospheric braking curve
            v = entry_velocity_m_s * math.exp(-0.5 * (mars_atmospheric_density(h) * cd_hypersonic * s_aeroshell / total_entry_mass_kg) * (h_scale / math.sin(gamma_rad)))
        elif h > 1600.0:
            # Parachute braking down to 79 m/s
            frac = (h - 1600.0) / (deploy_altitude_m - 1600.0)
            v = 79.0 + (deploy_velocity_m_s - 79.0) * frac
        else:
            # Powered descent from 79 m/s to 0 m/s
            frac = h / 1600.0
            v = 79.0 * math.sqrt(max(frac, 0.0))
        velocities.append(float(v))

    return {
        "entry_velocity_m_s": entry_velocity_m_s,
        "entry_angle_deg": entry_angle_deg,
        "peak_g_load": peak_g_load,
        "deploy_altitude_m": deploy_altitude_m,
        "deploy_mach": deploy_mach,
        "deploy_dynamic_pressure_pa": dynamic_pressure_pa,
        "peak_opening_load_kn": peak_opening_load_kn,
        "structural_limit_kn": PARACHUTE_STRUCTURAL_LIMIT_N / 1000.0,
        "parachute_margin": parachute_margin,
        "parachute_pass": parachute_pass,
        "backshell_sep_velocity_m_s": 79.0,
        "backshell_sep_altitude_m": 1600.0,
        "stages": stages,
        "plot_altitudes_km": [float(h / 1000.0) for h in altitudes],
        "plot_velocities_m_s": velocities
    }
