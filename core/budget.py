"""
COSMOS AI — Mars Mission Planner
Consolidated Delta-v Budget & Propulsive Accounting Engine
Grounding: Cano et al. (ExoMars) & Team Resolved Budget Specification
"""

from typing import Dict, Any, List

def build_delta_v_budget(tcm_delta_v_m_s: float, 
                         landing_burn_delta_v_m_s: float, 
                         esa_policy_margin_percent: float = 5.0) -> Dict[str, Any]:
    """
    Assembles consolidated mission propulsive delta-v budget.
    Reflects the team's resolution of the 3 open items:
    1. Mars Orbit Insertion -> N/A (Direct Entry)
    2. Landing Burn -> ~225 m/s (Terminal decel + gravity loss)
    3. Surface Reserve -> Reclassified to Power Budget
    """
    subtotal_maneuvering_m_s = tcm_delta_v_m_s + landing_burn_delta_v_m_s
    margin_m_s = subtotal_maneuvering_m_s * (esa_policy_margin_percent / 100.0)
    total_budget_m_s = subtotal_maneuvering_m_s + margin_m_s

    items = [
        {
            "phase": "Earth Departure",
            "delta_v_str": "Derived from C3 (~11.1 km²/s²)",
            "delta_v_m_s": None,
            "status": "Provided by Launch Vehicle Upper Stage",
            "notes": "Direct injection into heliocentric transfer arc"
        },
        {
            "phase": "Cruise Trajectory Correction (TCMs × 5–6)",
            "delta_v_str": f"{tcm_delta_v_m_s:.1f} m/s",
            "delta_v_m_s": tcm_delta_v_m_s,
            "status": "Flight-Allocated",
            "notes": "Mid-course trajectory fine-tuning (MSL Navigation baseline)"
        },
        {
            "phase": "Mars Orbit Insertion (MOI)",
            "delta_v_str": "N/A",
            "delta_v_m_s": 0.0,
            "status": "Confirmed Not Needed (Direct Entry)",
            "notes": "Direct atmospheric entry without orbital capture (like MSL/M2020)"
        },
        {
            "phase": "Powered Landing Burn",
            "delta_v_str": f"~{landing_burn_delta_v_m_s:.1f} m/s",
            "delta_v_m_s": landing_burn_delta_v_m_s,
            "status": "Quantified from MEADS Kinematics",
            "notes": "Deceleration from 79 m/s to 0.75 m/s + 38s gravity loss + divert"
        },
        {
            "phase": f"Navigation Margin (ESA {esa_policy_margin_percent:.0f}%)",
            "delta_v_str": f"{margin_m_s:.1f} m/s",
            "delta_v_m_s": margin_m_s,
            "status": "Policy Cushion",
            "notes": "Standard safety margin for trajectory dispersions"
        },
        {
            "phase": "Surface Operations Reserve",
            "delta_v_str": "RECLASSIFIED",
            "delta_v_m_s": 0.0,
            "status": "Moved to Surface Power Budget",
            "notes": "Surface rovers operate on electrical power, not delta-v propulsion"
        }
    ]

    return {
        "tcm_delta_v_m_s": tcm_delta_v_m_s,
        "landing_burn_delta_v_m_s": landing_burn_delta_v_m_s,
        "margin_percent": esa_policy_margin_percent,
        "margin_m_s": margin_m_s,
        "total_maneuvering_delta_v_m_s": total_budget_m_s, # ~263 m/s
        "budget_items": items
    }
