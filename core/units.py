"""
COSMOS AI — Mars Mission Planner
Core Dimensional & Unit Consistency Engine
Grounding: NASA Mars Climate Orbiter Mishap Investigation Board Report (1999)
"""

from typing import Any, Union
import math

class UnitValidationError(ValueError):
    """Raised when cross-subsystem interface contract or unit sanity fails."""
    pass

# Fundamental Physical Constants (SI Units)
SPEED_OF_LIGHT = 299792458.0          # m/s
G_EARTH = 9.80665                     # m/s^2 (standard Earth surface gravity)
G_MARS = 3.72076                      # m/s^2 (Mars surface gravity)
MU_SUN = 1.32712440018e20             # m^3/s^2 (heliocentric gravitational parameter)
MU_MARS = 4.282837e13                 # m^3/s^2 (Mars gravitational parameter)
R_MARS_EQUATORIAL = 3396200.0         # m (Mars equatorial radius)
AU_METERS = 149597870700.0            # meters per Astronomical Unit

def assert_si_distance(val: float, name: str, min_val: float = 0.0, max_val: float = 1e15) -> float:
    """Validate distance is in meters within plausible interplanetary range."""
    if not isinstance(val, (int, float)) or math.isnan(val):
        raise UnitValidationError(f"[MCO Violation] {name} must be a valid numeric distance in meters (SI). Got {val}")
    if val < min_val or val > max_val:
        raise UnitValidationError(f"[Range Warning] {name} = {val} m outside expected bounds [{min_val}, {max_val}]")
    return float(val)

def assert_si_velocity(val: float, name: str, min_val: float = 0.0, max_val: float = 1e6) -> float:
    """Validate velocity is in meters per second (SI)."""
    if not isinstance(val, (int, float)) or math.isnan(val):
        raise UnitValidationError(f"[MCO Violation] {name} must be a valid velocity in m/s (SI). Got {val}")
    if val < min_val or val > max_val:
        raise UnitValidationError(f"[Range Warning] {name} = {val} m/s outside expected bounds [{min_val}, {max_val}]")
    return float(val)

def assert_si_mass(val: float, name: str, min_val: float = 0.1, max_val: float = 1e6) -> float:
    """Validate mass is in kilograms (SI)."""
    if not isinstance(val, (int, float)) or math.isnan(val):
        raise UnitValidationError(f"[MCO Violation] {name} must be a valid mass in kilograms (SI). Got {val}")
    if val < min_val or val > max_val:
        raise UnitValidationError(f"[Range Warning] {name} = {val} kg outside bounds [{min_val}, {max_val}]")
    return float(val)

def assert_si_force(val: float, name: str, min_val: float = 0.0, max_val: float = 1e8) -> float:
    """Validate force is in Newtons (SI). Not lbf!"""
    if not isinstance(val, (int, float)) or math.isnan(val):
        raise UnitValidationError(f"[MCO Violation] {name} must be a valid force in Newtons (SI). Got {val}")
    if val < min_val or val > max_val:
        raise UnitValidationError(f"[Range Warning] {name} = {val} N outside bounds [{min_val}, {max_val}]")
    return float(val)

def assert_si_angle_deg(val: float, name: str, min_val: float = -360.0, max_val: float = 360.0) -> float:
    """Validate angle is in degrees."""
    if not isinstance(val, (int, float)) or math.isnan(val):
        raise UnitValidationError(f"{name} must be a valid angle in degrees. Got {val}")
    if val < min_val or val > max_val:
        raise UnitValidationError(f"{name} = {val}° outside bounds [{min_val}, {max_val}]")
    return float(val)

# Explicit Unit Conversion Helpers with Logging
def lbf_to_newtons(lbf: float) -> float:
    """Conversion preventing the Mars Climate Orbiter unit mismatch."""
    return lbf * 4.4482216152605

def km_to_meters(km: float) -> float:
    return km * 1000.0

def meters_to_km(m: float) -> float:
    return m / 1000.0

def km_s_to_m_s(km_s: float) -> float:
    return km_s * 1000.0

def m_s_to_km_s(m_s: float) -> float:
    return m_s / 1000.0
