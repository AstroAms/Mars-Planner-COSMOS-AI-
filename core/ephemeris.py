"""
COSMOS AI — Mars Mission Planner
Heliocentric Planetary Ephemeris & Orbital State Vector Engine
Grounding: NASA Mars Mission Design Handbook & Keplerian Orbital Mechanics
"""

import math
from datetime import datetime, date
from typing import Tuple, Dict, Any, Union
import numpy as np
from core.units import MU_SUN, AU_METERS, assert_si_distance

class PlanetaryBody:
    def __init__(self, name: str, a_au: float, e: float, inc_deg: float, 
                 omega_deg: float, w_deg: float, M0_deg: float, epoch_jd: float = 2451545.0):
        self.name = name
        self.a = a_au * AU_METERS            # meters
        self.e = e                            # eccentricity
        self.inc = math.radians(inc_deg)      # inclination (rad)
        self.omega = math.radians(omega_deg)  # longitude of ascending node (rad)
        self.w = math.radians(w_deg)          # argument of periapsis (rad)
        self.M0 = math.radians(M0_deg)        # mean anomaly at epoch J2000 (rad)
        self.epoch_jd = epoch_jd
        self.period_s = 2.0 * math.pi * math.sqrt((self.a ** 3) / MU_SUN)
        self.period_days = self.period_s / 86400.0

    def mean_anomaly_at(self, jd: float) -> float:
        dt_days = jd - self.epoch_jd
        n = (2.0 * math.pi) / self.period_days
        M = (self.M0 + n * dt_days) % (2.0 * math.pi)
        return M

    def solve_kepler(self, M: float) -> float:
        """Solve Kepler's equation M = E - e*sin(E) using Newton-Raphson iteration."""
        E = M if self.e < 0.8 else math.pi
        for _ in range(15):
            f = E - self.e * math.sin(E) - M
            f_prime = 1.0 - self.e * math.cos(E)
            delta = f / f_prime
            E -= delta
            if abs(delta) < 1e-12:
                break
        return E

    def get_state(self, jd: float) -> Tuple[np.ndarray, np.ndarray]:
        """Returns heliocentric state (position [m], velocity [m/s]) as 3D vectors."""
        M = self.mean_anomaly_at(jd)
        E = self.solve_kepler(M)
        
        # True anomaly nu
        sin_nu = (math.sqrt(1.0 - self.e**2) * math.sin(E)) / (1.0 - self.e * math.cos(E))
        cos_nu = (math.cos(E) - self.e) / (1.0 - self.e * math.cos(E))
        nu = math.atan2(sin_nu, cos_nu)

        # Distance from Sun
        r = self.a * (1.0 - self.e * math.cos(E))

        # Position and velocity in orbital plane
        p = self.a * (1.0 - self.e**2)
        h = math.sqrt(MU_SUN * p) # specific angular momentum

        r_orb = np.array([r * math.cos(nu), r * math.sin(nu), 0.0])
        v_orb = np.array([
            -(MU_SUN / h) * math.sin(nu),
            (MU_SUN / h) * (self.e + math.cos(nu)),
            0.0
        ])

        # Rotation matrix from orbital plane to ecliptic J2000
        Rz_w = np.array([
            [math.cos(self.w), -math.sin(self.w), 0.0],
            [math.sin(self.w),  math.cos(self.w), 0.0],
            [0.0, 0.0, 1.0]
        ])
        Rx_i = np.array([
            [1.0, 0.0, 0.0],
            [0.0, math.cos(self.inc), -math.sin(self.inc)],
            [0.0, math.sin(self.inc),  math.cos(self.inc)]
        ])
        Rz_O = np.array([
            [math.cos(self.omega), -math.sin(self.omega), 0.0],
            [math.sin(self.omega),  math.cos(self.omega), 0.0],
            [0.0, 0.0, 1.0]
        ])
        Q = Rz_O @ Rx_i @ Rz_w

        r_vec = Q @ r_orb
        v_vec = Q @ v_orb
        return r_vec, v_vec

def date_to_jd(dt: Union[date, datetime]) -> float:
    """Convert a Python date or datetime object to Julian Date."""
    if isinstance(dt, datetime):
        year, month, day = dt.year, dt.month, dt.day + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0
    else:
        year, month, day = dt.year, dt.month, float(dt.day)

    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    return jd

# Standard J2000 Planetary Baselines
EARTH = PlanetaryBody(
    name="Earth",
    a_au=1.00000011,
    e=0.01671022,
    inc_deg=0.00005,
    omega_deg=-11.26064,
    w_deg=102.94719,
    M0_deg=100.46435
)

MARS = PlanetaryBody(
    name="Mars",
    a_au=1.52366231,
    e=0.09341233,
    inc_deg=1.85061,
    omega_deg=49.57854,
    w_deg=286.5016,
    M0_deg=19.3870
)

# Synodic Period (Handbook value: ~779.9 days)
SYNODIC_PERIOD_DAYS = 1.0 / abs(1.0 / EARTH.period_days - 1.0 / MARS.period_days)

def get_planetary_geometry(dt: Union[date, datetime]) -> Dict[str, Any]:
    """Computes instantaneous relative geometry between Earth, Sun, and Mars."""
    jd = date_to_jd(dt)
    r_earth, v_earth = EARTH.get_state(jd)
    r_mars, v_mars = MARS.get_state(jd)

    rel_pos = r_mars - r_earth
    distance_m = float(np.linalg.norm(rel_pos))
    distance_au = distance_m / AU_METERS

    # Sun-Earth-Mars (SEM) angle
    r_e_norm = r_earth / np.linalg.norm(r_earth)
    r_m_from_e_norm = rel_pos / np.linalg.norm(rel_pos)
    dot_sem = np.clip(np.dot(-r_e_norm, r_m_from_e_norm), -1.0, 1.0)
    sem_angle_deg = math.degrees(math.acos(dot_sem))

    return {
        "jd": jd,
        "date": dt,
        "r_earth": r_earth,
        "v_earth": v_earth,
        "r_mars": r_mars,
        "v_mars": v_mars,
        "distance_m": distance_m,
        "distance_au": distance_au,
        "sem_angle_deg": sem_angle_deg
    }
