"""
Test End-to-End Mission Pipeline with COSMOS-MARS-01 Baseline
"""

import unittest
from datetime import date
from core.pipeline import MissionSimulationPipeline

class TestMissionPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = MissionSimulationPipeline()

    def test_baseline_cosmos_mars_01_feasible(self):
        # 2026 Mars Launch Window baseline: Launch 2026-06-01, Arrival 2026-12-18 (~200 days / ~6.6 months)
        launch_date = date(2026, 6, 1)
        arrival_date = date(2026, 12, 18)
        
        result = self.pipeline.run_mission_evaluation(
            launch_date=launch_date,
            arrival_date=arrival_date,
            rover_mass_kg=500.0,
            surface_mission_sols=500,
            power_source="mmrtg",
            terrain_key="sand_dune",
            wheel_mode="dynamic",
            telecom_band="X-band"
        )

        self.assertIn(result["overall_feasibility"], ["FEASIBLE", "CONDITIONALLY FEASIBLE"])
        
        # Check Delta-v budget matches ~263 m/s resolved expectation
        budget = result["budget"]
        self.assertAlmostEqual(budget["total_maneuvering_delta_v_m_s"], 263.0, delta=30.0)

        # Check parachute structural margin > 1.0 (limit 289 kN)
        edl = result["edl"]
        self.assertTrue(edl["parachute_pass"])
        self.assertLess(edl["peak_opening_load_kn"], 289.0)

        # Check MMRTG sustains 500 sols
        surface = result["surface_power"]
        self.assertEqual(surface["sustainable_sols"], 500)

    def test_heavy_payload_flags_srp_trl_risk(self):
        # Scaled up payload: 2500 kg (requires supersonic retropropulsion)
        launch_date = date(2026, 6, 1)
        arrival_date = date(2026, 12, 18)

        result = self.pipeline.run_mission_evaluation(
            launch_date=launch_date,
            arrival_date=arrival_date,
            rover_mass_kg=2500.0,
            surface_mission_sols=500,
            power_source="mmrtg",
            wheel_mode="dynamic"
        )

        self.assertEqual(result["propulsion"]["trl_rating"], 3)
        self.assertTrue(result["propulsion"]["trl_risk_flag"])
        self.assertIn(result["overall_feasibility"], ["HIGH RISK", "INFEASIBLE"])

if __name__ == "__main__":
    unittest.main()
