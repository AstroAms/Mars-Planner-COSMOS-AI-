"""
COSMOS AI — Mars Mission Planner
Command-Line Mission Evaluation Interface
"""

import argparse
import json
from datetime import datetime
from core.pipeline import MissionSimulationPipeline

def main():
    parser = argparse.ArgumentParser(description="COSMOS AI Mars Mission Planner CLI")
    parser.add_argument("--launch", type=str, default="2026-06-01", help="Launch date (YYYY-MM-DD)")
    parser.add_argument("--arrival", type=str, default="2026-12-18", help="Mars arrival date (YYYY-MM-DD)")
    parser.add_argument("--mass", type=float, default=500.0, help="Rover payload mass in kg (nominal: 500)")
    parser.add_argument("--sols", type=int, default=500, help="Surface mission duration in Sols")
    parser.add_argument("--power", type=str, default="mmrtg", choices=["mmrtg", "solar"], help="Power source")
    parser.add_argument("--terrain", type=str, default="sand_dune", choices=["sand_dune", "firm_regolith", "bedrock"], help="Surface terrain")
    parser.add_argument("--wheel", type=str, default="dynamic", choices=["dynamic", "static"], help="Mobility traction mode")
    parser.add_argument("--band", type=str, default="X-band", choices=["X-band", "S-band", "Ka-band"], help="Telecom band")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    launch_date = datetime.strptime(args.launch, "%Y-%m-%d").date()
    arrival_date = datetime.strptime(args.arrival, "%Y-%m-%d").date()

    pipeline = MissionSimulationPipeline()
    result = pipeline.run_mission_evaluation(
        launch_date=launch_date,
        arrival_date=arrival_date,
        rover_mass_kg=args.mass,
        surface_mission_sols=args.sols,
        power_source=args.power,
        terrain_key=args.terrain,
        wheel_mode=args.wheel,
        telecom_band=args.band
    )

    if args.json:
        # Convert non-serializable fields
        def serialize(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            if hasattr(obj, "tolist"):
                return obj.tolist()
            return str(obj)
        print(json.dumps(result, default=serialize, indent=2))
        return

    # Print Formatted Report
    print("=" * 80)
    print(" COSMOS AI — MARS MISSION PLANNER (SIMULATION REPORT)")
    print("=" * 80)
    print(f" Mission Status:     [{result['overall_feasibility']}]")
    print(f" Summary Rationale:  {result['summary_rationale']}")
    print("-" * 80)
    print(f" Launch Window:      {args.launch}  -->  Mars Arrival: {args.arrival}")
    print(f" Transit Duration:   {result['transfer']['tof_days']:.1f} days ({result['transfer']['tof_months']:.1f} months)")
    print(f" Departure Energy:   C3 = {result['transfer']['c3_km2_s2']:.2f} km²/s² (V_inf_dep = {result['transfer']['v_inf_dep_km_s']:.2f} km/s)")
    print(f" Mars Arrival Speed: V_inf_arr = {result['transfer']['v_inf_arr_km_s']:.2f} km/s | V_entry = {result['transfer']['v_entry_m_s']/1000.0:.2f} km/s")
    print(f" Entry Flight Path:  {result['transfer']['efpa_deg']:.2f}° (Corridor Target: -15.50° ± 0.20°)")
    print("-" * 80)
    print(" ENTRY, DESCENT & LANDING (EDL) & PROPULSION:")
    print(f" Parachute Opening:  {result['edl']['peak_opening_load_kn']:.1f} kN (Rating Limit: {result['edl']['structural_limit_kn']:.0f} kN | Margin: {result['edl']['parachute_margin']:.2f}x)")
    print(f" Powered Landing:    {result['propulsion']['delta_v_landing_m_s']:.1f} m/s (Propellant Consumed: {result['propulsion']['propellant_consumed_kg']:.1f} kg)")
    print(f" Descent Stage TRL:  TRL {result['propulsion']['trl_rating']} ({result['propulsion']['propulsion_architecture']})")
    print("-" * 80)
    print(" SURFACE MOBILITY & DYNAMIC TRACTION:")
    mob = result['surface_power']['mobility_details']
    print(f" Terrain / Mode:     {mob['terrain_name']} | Wheel Mode: {mob['wheel_mode'].upper()}")
    print(f" Wheel Slip Ratio:   {mob['measured_slip_ratio']*100:.1f}% | Dynamic Cleats: {'DEPLOYED (Autonomous)' if mob['cleats_deployed'] else 'RETRACTED'}")
    print(f" Entrapment Risk:    {'YES (WARNING - Wheel Trenching)' if mob['entrapment_risk'] else 'NO (Optimal Traction)'}")
    print(f" Power Draw:         Drive: {mob['drive_power_w']:.0f} W | Transient Actuator Spike: {mob['actuator_power_spike_w']:.0f} W")
    print("-" * 80)
    print(" SURFACE POWER & 500-SOL CONSUMABLES:")
    pwr = result['surface_power']
    print(f" Daily Generation:   {pwr['daily_energy_generated_wh']:.0f} Wh/sol ({pwr['power_source']})")
    print(f" Daily Consumption:  {pwr['total_daily_consumption_wh']:.0f} Wh/sol (Net Margin: {pwr['daily_net_margin_wh']:+.0f} Wh/sol)")
    print(f" Longevity Outlook:  {pwr['sustainable_sols']} Sols achievable")
    print("-" * 80)
    print(" CONSOLIDATED DELTA-V BUDGET:")
    bgt = result['budget']
    for it in bgt['budget_items']:
        val = it['delta_v_str']
        print(f"  • {it['phase']:<38} : {val:<18} [{it['status']}]")
    print(f"  --> TOTAL MANEUVERING DELTA-V ON CRAFT: {bgt['total_maneuvering_delta_v_m_s']:.1f} m/s")
    print("-" * 80)
    print(" CONSTRAINT CHECK MATRIX:")
    for c in result['constraints']:
        badge = f"[{c['status']}]"
        print(f"  {badge:<14} {c['name']:<42} : {c['measured']}")
    print("=" * 80)

if __name__ == "__main__":
    main()
