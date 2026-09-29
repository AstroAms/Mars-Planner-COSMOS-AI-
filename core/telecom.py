"""
COSMOS AI — Mars Mission Planner
Telecommunications, Latency & Solar Conjunction Blackout Engine
Grounding: Ely et al. (NASA NTRS 2022) & JPL DESCANSO Architecture
"""

import math
from datetime import date, datetime
from typing import Dict, Any, List
from core.units import SPEED_OF_LIGHT, AU_METERS
from core.ephemeris import get_planetary_geometry, date_to_jd

# Blackout threshold angles per band (Ely et al. NTRS 2022)
CONJUNCTION_THRESHOLDS_DEG = {
    "S-band": 4.0,
    "X-band": 2.3,
    "Ka-band": 1.0
}

def evaluate_telecom(dt: date, band: str = "X-band") -> Dict[str, Any]:
    """
    Computes communication latency and solar conjunction blackout status.
    """
    geom = get_planetary_geometry(dt)
    dist_m = geom["distance_m"]
    dist_au = geom["distance_au"]
    sem_angle_deg = geom["sem_angle_deg"]

    # One-way and Round-trip light time
    one_way_light_time_s = dist_m / SPEED_OF_LIGHT
    one_way_minutes = one_way_light_time_s / 60.0 # ~3.1 to 22.2 min
    round_trip_minutes = one_way_minutes * 2.0     # ~6.2 to 44.4 min

    # Conjunction Blackout Evaluation
    threshold_deg = CONJUNCTION_THRESHOLDS_DEG.get(band, 2.3)
    in_conjunction_blackout = sem_angle_deg < threshold_deg

    # Estimated blackout duration in days if conjunction occurs
    if sem_angle_deg < 1.0:
        est_blackout_days = 19.6
    elif sem_angle_deg < 2.3:
        est_blackout_days = 11.8
    elif sem_angle_deg < 4.0:
        est_blackout_days = 2.9
    else:
        est_blackout_days = 0.0

    # Relay throughput (MRO / Odyssey store-and-forward)
    # Typical 2 UHF passes per sol, ~10-15 minutes each, average 2.0 Mbps -> ~250-500 MB/sol
    if in_conjunction_blackout:
        data_volume_mb_per_sol = 0.0
        relay_status = "BLOCKED: Solar Conjunction Command Moratorium in effect. Autonomous safe-state mandatory."
    else:
        data_volume_mb_per_sol = 350.0 # Nominal science data volume per sol
        relay_status = "NOMINAL: UHF Store-and-Forward relay active via MRO / Odyssey (0.5–4.0 Mbps)."

    return {
        "date": dt,
        "band": band,
        "distance_au": dist_au,
        "distance_million_km": dist_m / 1e9,
        "one_way_delay_min": one_way_minutes,
        "round_trip_delay_min": round_trip_minutes,
        "sem_angle_deg": sem_angle_deg,
        "blackout_threshold_deg": threshold_deg,
        "in_conjunction": in_conjunction_blackout,
        "est_blackout_duration_days": est_blackout_days,
        "data_return_mb_per_sol": data_volume_mb_per_sol,
        "status_message": relay_status
    }
