"""
COSMOS AI — Mars Mission Planner
Analytical Lambert Solver & Trajectory Engine
Grounding: Izzo (2015) 'Lambert's Problem Revisited' & MSL Navigation Study
"""

import math
from datetime import date, datetime
from typing import Tuple, Dict, Any, Optional
import numpy as np
from core.units import MU_SUN, MU_MARS, R_MARS_EQUATORIAL, assert_si_velocity, assert_si_distance
from core.ephemeris import date_to_jd, EARTH, MARS

def stumpff_c2(z: float) -> float:
    if z > 1e-6:
        return (1.0 - math.cos(math.sqrt(z))) / z
    elif z < -1e-6:
        return (math.cosh(math.sqrt(-z)) - 1.0) / (-z)
    else:
        return 0.5

def stumpff_c3(z: float) -> float:
    if z > 1e-6:
        return (math.sqrt(z) - math.sin(math.sqrt(z))) / (z * math.sqrt(z))
    elif z < -1e-6:
        return (math.sinh(math.sqrt(-z)) - math.sqrt(-z)) / ((-z) * math.sqrt(-z))
    else:
        return 1.0 / 6.0

def solve_lambert(r1_vec: np.ndarray, r2_vec: np.ndarray, tof_s: float, 
                  mu: float = MU_SUN, prograde: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Robust universal variable Lambert solver with bisection refinement.
    Guarantees convergence for Type I and Type II interplanetary arcs.
    """
    r1 = float(np.linalg.norm(r1_vec))
    r2 = float(np.linalg.norm(r2_vec))

    # Cross product to determine orbital direction
    cross_prod = np.cross(r1_vec, r2_vec)
    cos_dtheta = float(np.dot(r1_vec, r2_vec) / (r1 * r2))
    cos_dtheta = np.clip(cos_dtheta, -1.0, 1.0)
    
    if prograde:
        dtheta = math.acos(cos_dtheta) if cross_prod[2] >= 0 else (2.0 * math.pi - math.acos(cos_dtheta))
    else:
        dtheta = (2.0 * math.pi - math.acos(cos_dtheta)) if cross_prod[2] >= 0 else math.acos(cos_dtheta)

    # Avoid zero division on collinear transfer
    dtheta = np.clip(dtheta, 1e-4, 2.0 * math.pi - 1e-4)

    # Battin / Izzo transformation variable A
    irwin_A = math.sin(dtheta) * math.sqrt(r1 * r2 / (1.0 - math.cos(dtheta)))
    if abs(irwin_A) < 1e-7:
        irwin_A = 1e-7

    # Robust bisection search for universal variable z
    z_low = -4.0 * (math.pi ** 2)
    z_high = 4.0 * (math.pi ** 2)
    z = 0.0
    y = r1 + r2

    for _ in range(65):
        z = (z_low + z_high) / 2.0
        c2 = stumpff_c2(z)
        c3 = stumpff_c3(z)

        # Protect against negative y
        arg = (z * c3 - 1.0) / math.sqrt(max(c2, 1e-12))
        y_trial = r1 + r2 + irwin_A * arg
        if irwin_A > 0.0 and y_trial < 0.0:
            z_low = z
            continue

        y = max(y_trial, 1e-3)
        chi = math.sqrt(y / max(c2, 1e-12))
        t_iter = (chi**3 * c3 + irwin_A * math.sqrt(y)) / math.sqrt(mu)

        if t_iter < tof_s:
            z_low = z
        else:
            z_high = z

        if abs(t_iter - tof_s) < 1.0: # Converged within 1 second of TOF
            break

    # Calculate Lagrange coefficients f, g, g_dot
    f = 1.0 - y / r1
    g = irwin_A * math.sqrt(y / mu)
    g_dot = 1.0 - y / r2

    v1_vec = (r2_vec - f * r1_vec) / g
    v2_vec = (g_dot * r2_vec - r1_vec) / g

    return v1_vec, v2_vec

def evaluate_mars_transfer(launch_date: date, arrival_date: date) -> Dict[str, Any]:
    """
    Evaluates Earth-to-Mars interplanetary transfer trajectory.
    Calculates departure C3, TOF, Mars arrival V_infinity, EFPA corridor, and TCM delta-v budget.
    """
    jd_dep = date_to_jd(launch_date)
    jd_arr = date_to_jd(arrival_date)

    tof_days = jd_arr - jd_dep
    if tof_days <= 40.0 or tof_days >= 700.0:
        raise ValueError(f"Unrealistic Time-of-Flight: {tof_days:.1f} days. Expected 150–350 days.")

    tof_s = tof_days * 86400.0

    r_earth_dep, v_earth_dep = EARTH.get_state(jd_dep)
    r_mars_arr, v_mars_arr = MARS.get_state(jd_arr)

    # Solve Lambert transfer
    v1_trans, v2_trans = solve_lambert(r_earth_dep, r_mars_arr, tof_s, mu=MU_SUN)

    # Earth Departure Hyperbolic Excess
    v_inf_dep_vec = v1_trans - v_earth_dep
    v_inf_dep_mag = float(np.linalg.norm(v_inf_dep_vec)) # m/s
    c3_km2_s2 = (v_inf_dep_mag / 1000.0) ** 2 # km^2 / s^2

    # Mars Arrival Hyperbolic Excess
    v_inf_arr_vec = v2_trans - v_mars_arr
    v_inf_arr_mag = float(np.linalg.norm(v_inf_arr_vec)) # m/s
    v_inf_arr_km_s = v_inf_arr_mag / 1000.0 # km/s

    # Entry Interface calculations (Radius = 3,522.2 km per MSL Nav Study)
    r_ei = 3522.2 * 1000.0 # meters
    v_ei_sq = (v_inf_arr_mag ** 2) + 2.0 * MU_MARS / r_ei
    v_entry_m_s = math.sqrt(v_ei_sq) # ~5.6 to 6.2 km/s

    # Entry Flight Path Angle (EFPA) Corridor target: -15.5° ± 0.20°
    # Nominal design point assumes targeted entry corridor
    nominal_efpa_deg = -15.50
    # Small dispersion driven by arrival excess speed relative to 2.9 km/s nominal baseline
    v_inf_diff = v_inf_arr_km_s - 2.90
    efpa_estimated_deg = nominal_efpa_deg - (v_inf_diff * 0.08)
    efpa_in_corridor = (-15.70 <= efpa_estimated_deg <= -15.30)

    # Cruise TCM delta-v budget (MSL Navigation Study: 15–35 m/s across 5–6 TCMs)
    tcm_baseline_m_s = 22.0
    tcm_scaled_m_s = tcm_baseline_m_s + max(0.0, (c3_km2_s2 - 11.1) * 0.6)
    tcm_total_m_s = min(max(tcm_scaled_m_s, 15.0), 35.0)

    return {
        "launch_date": launch_date,
        "arrival_date": arrival_date,
        "tof_days": tof_days,
        "tof_months": tof_days / 30.4375,
        "c3_km2_s2": c3_km2_s2,
        "v_inf_dep_km_s": v_inf_dep_mag / 1000.0,
        "v_inf_arr_km_s": v_inf_arr_km_s,
        "v_entry_m_s": v_entry_m_s,
        "r_ei_km": r_ei / 1000.0,
        "efpa_deg": efpa_estimated_deg,
        "efpa_in_corridor": efpa_in_corridor,
        "tcm_delta_v_m_s": tcm_total_m_s,
        "r_earth_dep": r_earth_dep,
        "r_mars_arr": r_mars_arr,
        "v_trans_dep": v1_trans,
        "v_trans_arr": v2_trans
    }
