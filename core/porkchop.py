"""
COSMOS AI — Mars Mission Planner
Porkchop Plot Generator for Launch Window Trajectory Optimization
"""

from datetime import date, timedelta
from typing import Dict, Any, List, Tuple
import numpy as np
from core.lambert import evaluate_mars_transfer

def generate_porkchop_data(center_launch_date: date, 
                           launch_window_days: int = 40, 
                           tof_min_days: int = 170, 
                           tof_max_days: int = 260, 
                           resolution: int = 15) -> Dict[str, Any]:
    """
    Generates a 2D grid of departure C3 and arrival V_infinity values
    across candidate launch dates and times of flight.
    """
    half_window = launch_window_days // 2
    start_launch = center_launch_date - timedelta(days=half_window)
    
    launch_offsets = np.linspace(0, launch_window_days, resolution)
    tofs = np.linspace(tof_min_days, tof_max_days, resolution)
    
    c3_grid = np.zeros((resolution, resolution))
    vinf_arr_grid = np.zeros((resolution, resolution))
    launch_dates_str = []
    arrival_dates_str = []

    for i, l_offset in enumerate(launch_offsets):
        l_date = start_launch + timedelta(days=int(l_offset))
        launch_dates_str.append(l_date.strftime("%Y-%m-%d"))
        for j, tof in enumerate(tofs):
            a_date = l_date + timedelta(days=int(tof))
            if i == 0:
                arrival_dates_str.append(a_date.strftime("%Y-%m-%d"))
            try:
                res = evaluate_mars_transfer(l_date, a_date)
                c3_grid[j, i] = min(float(res["c3_km2_s2"]), 120.0)
                vinf_arr_grid[j, i] = min(float(res["v_inf_arr_km_s"]), 12.0)
            except Exception:
                c3_grid[j, i] = 120.0
                vinf_arr_grid[j, i] = 12.0

    return {
        "launch_dates": launch_dates_str,
        "tofs_days": [int(t) for t in tofs],
        "c3_grid": c3_grid.tolist(),
        "vinf_arr_grid": vinf_arr_grid.tolist()
    }
