"""
Test Unit Consistency & MCO Prevention
"""

import unittest
from core.units import (
    assert_si_distance,
    assert_si_velocity,
    assert_si_mass,
    assert_si_force,
    lbf_to_newtons,
    UnitValidationError
)

class TestUnitConsistency(unittest.TestCase):
    def test_lbf_to_newtons_conversion(self):
        # 1 lbf = ~4.44822 N
        f_lbf = 100.0
        f_n = lbf_to_newtons(f_lbf)
        self.assertAlmostEqual(f_n, 444.822, places=2)

    def test_mco_check_valid_inputs(self):
        self.assertEqual(assert_si_mass(500.0, "Rover Mass"), 500.0)
        self.assertEqual(assert_si_velocity(225.0, "Landing Delta-v"), 225.0)
        self.assertEqual(assert_si_force(153800.0, "Parachute Load"), 153800.0)

    def test_mco_check_invalid_type(self):
        with self.assertRaises(UnitValidationError):
            assert_si_mass("500 kg", "Rover Mass") # non-numeric type rejected

    def test_mco_check_out_of_bounds(self):
        with self.assertRaises(UnitValidationError):
            assert_si_velocity(-10.0, "Negative Velocity")

if __name__ == "__main__":
    unittest.main()
