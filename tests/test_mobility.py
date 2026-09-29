"""
Test Autonomous Dynamic Mobility & Slip Resiliency
"""

import unittest
from core.mobility import simulate_traverse_step

class TestDynamicMobility(unittest.TestCase):
    def test_sand_dune_static_mode_fails_with_entrapment(self):
        result = simulate_traverse_step(terrain_key="sand_dune", wheel_mode="static")
        self.assertTrue(result["entrapment_risk"])
        self.assertFalse(result["cleats_deployed"])
        self.assertGreater(result["measured_slip_ratio"], 0.40)

    def test_sand_dune_dynamic_mode_deploys_cleats_autonomously(self):
        result = simulate_traverse_step(terrain_key="sand_dune", wheel_mode="dynamic")
        self.assertFalse(result["entrapment_risk"])
        self.assertTrue(result["cleats_deployed"])
        self.assertTrue(result["autonomous_trigger_fired"])
        self.assertLess(result["measured_slip_ratio"], 0.20)
        self.assertGreater(result["actuator_power_spike_w"], 0.0)

    def test_bedrock_nominal_traction(self):
        result = simulate_traverse_step(terrain_key="bedrock", wheel_mode="dynamic")
        self.assertFalse(result["entrapment_risk"])
        self.assertFalse(result["cleats_deployed"]) # Bedrock does not need cleats
        self.assertLess(result["measured_slip_ratio"], 0.10)

if __name__ == "__main__":
    unittest.main()
