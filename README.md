# COSMOS AI — Mars Mission Planner
**Theoretical Mars Mission Simulation Framework & Working Prototype**

An educational/engineering-level working prototype of the **COSMOS AI Mars Mission Planner**, implementing the end-to-end dependency pipeline from launch window selection to surface operations and autonomous dynamic mobility. This is not a flight-certified tool — see "Research Grounding & Flight Telemetry" below for what the underlying models (a Kepler-orbit + universal-variable Lambert solver, among others) do and don't validate.

---

## Architecture Overview

```
Launch Date (779.9-day synodic period)
   │
   ▼
Planetary State (Ephemerides: Earth & Mars state vectors)
   │
   ▼
Lambert Solver (Izzo Universal Variable formulation)
   │
   ▼
Trajectory Parameters (C3 departure energy, TCM budget, Time of Flight)
   │
   ▼
Mars Arrival Conditions (V∞ excess speed, Entry Flight Path Angle corridor: -15.5° ± 0.20°)
   │
   ▼
EDL Simulation (Cruz et al. DGB Parachute, Karlgaard et al. MEADS staging)
   │
   ▼
Powered Descent Landing Burn (~225–233 m/s deceleration + Martian gravity loss + divert)
   │
   ▼
Touchdown Mass (Tsiolkovsky propellant depletion → Landed 500 kg rover)
   │
   ▼
Autonomous Dynamic Mobility (Slip-detection threshold s > 30% → deploy active cleats)
   │
   ▼
Surface Resources & Power (MMRTG vs. Solar with atmospheric tau dust factor → 500 Sols life)
   │
   ▼
Communications (Earth-Mars light-time: 3–22 min, Solar Conjunction Blackout detection)
   │
   ▼
Constraint Engine (Mars Climate Orbiter 100% SI interface verification)
   │
   ▼
Mission Feasibility (FEASIBLE / CONDITIONALLY FEASIBLE / HIGH RISK / INFEASIBLE)
```

---

## Research Grounding & Flight Telemetry

Every parameter in this simulation prototype is anchored in peer-reviewed aerospace literature:

| Subsystem | Research Paper | Flight Baseline / Key Implementation Values |
| :--- | :--- | :--- |
| **Orbital** | **NASA Mars Mission Design Handbook** | Synodic period $T_{syn} \approx 779.9\text{ days}$; Type I transfer geometry. |
| **Orbital** | **Izzo, D. (2015)** | Analytical Universal Variable Lambert Solver for rapid porkchop plot generation. |
| **Orbital** | **MSL Navigation Study** | Cruise $\Delta v = 15\text{--}35\text{ m/s}$ (5–6 TCMs); Entry Corridor $\gamma_{EI} = -15.5^\circ \pm 0.20^\circ$. |
| **EDL** | **Cruz et al.** | $21.35\text{ m}$ DGB parachute; Mach 1.75 deploy; $153.8\text{ kN}$ peak load vs. $289\text{ kN}$ structural limit. |
| **EDL** | **Karlgaard et al. (MEADS)** | Flight-validated staging: Heatshield jettison at Mach 0.7 $\to$ Backshell separation at $1.6\text{ km} / 79\text{ m/s}$. |
| **EDL** | **Korzun & Edquist** | Gating check: Payloads $> 1,500\text{ kg}$ trigger Supersonic Retropropulsion TRL 3–4 schedule & aerodynamic risk. |
| **Mobility** | **Dynamic Traction Wheel** | Autonomous cleat deployment when slip $> 30\%$ without waiting for 3–22 min ground-control latency. |
| **Systems** | **Ely et al. (NASA NTRS 2022)** | One-way light-time $\tau = 3\text{ to } 22\text{ min}$; Solar conjunction blackouts ($4^\circ$ S-band, $2.3^\circ$ X-band, $1^\circ$ Ka-band). |
| **Systems** | **MCO Mishap Report (1999)** | Strict SI unit assertions preventing unit-conversion errors (lbf vs. N). |
| **Systems** | **Cano et al. (ExoMars)** | Consolidated delta-v accounting + 5% ESA policy margin ($\approx 263\text{--}272\text{ m/s}$ total craft $\Delta v$). |

---

## Running the Interactive Mission Control Dashboard

To launch the web-based interactive mission dashboard:

```powershell
streamlit run app.py
```

Features:
- **Interactive Mission Presets**: Instantly load `COSMOS-MARS-01` baseline or failure stress tests.
- **Dynamic Wheel Simulation**: Live animation and terramechanics slip gauge comparing static wheels vs. deployed dynamic cleats.
- **Porkchop Plot Heatmap**: Real-time contour map of $C_3$ departure energy across launch windows.
- **MEADS Descent Kinematics**: Altitude vs. Velocity profile from 125 km entry to sky-crane touchdown.
- **Consolidated Delta-v Budget**: Complete breakdown table with resolved items and margins.

---

## Running the Standalone CLI

To run a headless mission evaluation:

```powershell
# Run baseline COSMOS-MARS-01
python run_cli.py --launch 2026-06-01 --arrival 2026-12-18 --mass 500 --wheel dynamic

# Run with static wheels on soft sand dunes (triggers entrapment warning)
python run_cli.py --launch 2026-06-01 --arrival 2026-12-18 --wheel static --terrain sand_dune

# Output raw JSON for pipeline automation
python run_cli.py --json
```

---

## Running the Test Suite

Run the full automated test suite:

```powershell
python -m unittest discover -s tests -p "test_*.py"
```
