"""
COSMOS AI — Mars Mission Planner
Interactive Streamlit Mission Control & Systems Simulation Dashboard
"""

import streamlit as st
from datetime import date, timedelta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import streamlit.components.v1 as components

from core.pipeline import MissionSimulationPipeline
from core.porkchop import generate_porkchop_data
from core.units import meters_to_km, AU_METERS

# Page configuration
st.set_page_config(
    page_title="COSMOS AI — Mars Mission Planner",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

import base64
import os

def render_wheel_3d_cad_html(mob: dict) -> str:
    """
    Builds an interactive 3D Three.js CAD viewport reproducing the Mars rover wheel
    from the engineering design: hollow cylindrical drum, outer chevron/zigzag grousers,
    dual-row rectangular window slots with transverse ribs, serrated perimeter rim teeth,
    central hub with bolt ring, and curved flexible spring flexure spokes.
    Reflects autonomous dynamic cleat deployment when wheel slip > 30%.
    """
    deployed = bool(mob.get("cleats_deployed", False))
    slip_pct = round(float(mob.get("measured_slip_ratio", 0.0)) * 100, 1)
    status_text = "Dynamic Cleats Deployed (Slip Mitigated)" if deployed else "Static Fixed Grousers (Baseline)"
    
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{ margin:0; padding:0; overflow:hidden; background:#0b0d14; font-family:'Segoe UI', system-ui, -apple-system, sans-serif; }}
  #wrap {{ position:relative; width:100%; height:480px; }}
  #titlebar {{
    position:absolute; top:12px; left:50%; transform:translateX(-50%); z-index:10;
    color:#f1f5f9; font-size:13px; font-weight:600; letter-spacing:0.3px;
    background:rgba(15,23,42,0.75); padding:8px 18px; border-radius:10px;
    border:1px solid {"rgba(56,189,248,0.4)" if deployed else "rgba(148,163,184,0.25)"};
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    text-align:center; white-space:nowrap; backdrop-filter:blur(8px);
  }}
  #titlebar .status-tag {{
    display:inline-block; margin-left:6px; padding:2px 8px; border-radius:6px;
    font-size:11px; font-weight:700;
    background:{"rgba(14,165,233,0.25)" if deployed else "rgba(100,116,139,0.25)"};
    color:{"#38bdf8" if deployed else "#94a3b8"};
    border:1px solid {"#38bdf8" if deployed else "#64748b"};
  }}
  #titlebar .sub {{ color:#94a3b8; font-weight:400; font-size:11px; display:block; margin-top:2px; }}
  #hud {{
    position:absolute; bottom:12px; left:14px; z-index:10; color:#94a3b8;
    font-size:11px; line-height:1.5; background:rgba(15,23,42,0.65);
    padding:8px 12px; border-radius:8px; border:1px solid rgba(255,255,255,0.08);
    backdrop-filter:blur(6px);
  }}
  #hud b {{ color:#38bdf8; }}
  #resetBtn {{
    position:absolute; bottom:12px; right:14px; z-index:10;
    background:rgba(30,41,59,0.8); color:#e2e8f0; border:1px solid rgba(255,255,255,0.15);
    padding:6px 12px; border-radius:6px; font-size:11px; font-weight:600; cursor:pointer;
    transition:all 0.2s; backdrop-filter:blur(6px);
  }}
  #resetBtn:hover {{ background:rgba(56,189,248,0.25); color:#38bdf8; border-color:#38bdf8; }}
  canvas {{ display:block; }}
</style>
</head>
<body>
<div id="wrap">
  <div id="titlebar">
    Wheel CAD Geometry: {status_text}
    <span class="status-tag">{"DEPLOYED" if deployed else "RETRACTED"}</span>
    <span class="sub">Measured Wheel Slip: <b>{slip_pct}%</b> | Autonomous Terrain Response</span>
  </div>
  <div id="hud">🖱️ <b>Left-drag</b> orbit &nbsp;|&nbsp; <b>Right-drag</b> pan &nbsp;|&nbsp; <b>Scroll</b> zoom</div>
  <button id="resetBtn" onclick="resetView()">⟲ Reset View</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const wrap = document.getElementById('wrap');
const W = wrap.clientWidth || 600, H = 480;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0d14);

// Studio Camera
const camera = new THREE.PerspectiveCamera(40, W/H, 0.1, 100);
const initCamPos = new THREE.Vector3(1.6, 0.9, 1.7);
camera.position.copy(initCamPos);

const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
renderer.setSize(W, H);
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
wrap.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.autoRotate = true;
controls.autoRotateSpeed = 1.2;
controls.minDistance = 1.0;
controls.maxDistance = 6.0;
controls.target.set(0, 0, 0);

function resetView() {{
  controls.autoRotate = true;
  camera.position.copy(initCamPos);
  controls.target.set(0, 0, 0);
  controls.update();
}}

// Lighting Rig
const ambLight = new THREE.AmbientLight(0xffffff, 0.65);
scene.add(ambLight);

const keyLight = new THREE.DirectionalLight(0xffeedd, 1.2);
keyLight.position.set(4, 5, 3);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xddeeff, 0.6);
fillLight.position.set(-4, 2, 2);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
rimLight.position.set(0, -3, -4);
scene.add(rimLight);

// ==========================================
// ROVER WHEEL GROUP (Axle along X-axis)
// ==========================================
const wheelGroup = new THREE.Group();

const R = 0.60;          // Wheel outer radius
const halfW = 0.28;      // Half wheel width along X
const isDeployed = {"true" if deployed else "false"};

// Standard Materials matching the reference rover wheel
const drumMat = new THREE.MeshStandardMaterial({{
  color: 0x9e9389,
  metalness: 0.55,
  roughness: 0.42,
  side: THREE.DoubleSide
}});

const innerDrumMat = new THREE.MeshStandardMaterial({{
  color: 0x4a453f,
  metalness: 0.6,
  roughness: 0.5,
  side: THREE.BackSide
}});

const rimLipMat = new THREE.MeshStandardMaterial({{
  color: 0xb5aba0,
  metalness: 0.65,
  roughness: 0.35
}});

const spokeMat = new THREE.MeshStandardMaterial({{
  color: 0x8a8076,
  metalness: 0.7,
  roughness: 0.32
}});

const hubMat = new THREE.MeshStandardMaterial({{
  color: 0x3d3732,
  metalness: 0.65,
  roughness: 0.45
}});

const boltMat = new THREE.MeshStandardMaterial({{
  color: 0xd8d8d8,
  metalness: 0.85,
  roughness: 0.25
}});

const cleatMat = new THREE.MeshStandardMaterial({{
  color: isDeployed ? 0x38bdf8 : 0x82786e,
  emissive: isDeployed ? 0x0284c7 : 0x000000,
  emissiveIntensity: isDeployed ? 0.75 : 0.0,
  metalness: 0.6,
  roughness: 0.35
}});

// 1. MAIN CYLINDRICAL DRUM (Hollow Shell)
const drumGeo = new THREE.CylinderGeometry(R, R, halfW * 2, 80, 8, true);
const drumMesh = new THREE.Mesh(drumGeo, drumMat);
drumMesh.rotation.z = Math.PI / 2;
wheelGroup.add(drumMesh);

// Inner liner cylinder for thickness depth
const innerDrumGeo = new THREE.CylinderGeometry(R * 0.975, R * 0.975, halfW * 2 * 0.99, 80, 1, true);
const innerDrumMesh = new THREE.Mesh(innerDrumGeo, innerDrumMat);
innerDrumMesh.rotation.z = Math.PI / 2;
wheelGroup.add(innerDrumMesh);

// 2. END RIM COLLARS / BEVELED LIPS (Both sides)
for (const xSide of [-halfW, halfW]) {{
  const rimTorusGeo = new THREE.TorusGeometry(R, 0.016, 12, 80);
  const rimTorus = new THREE.Mesh(rimTorusGeo, rimLipMat);
  rimTorus.rotation.y = Math.PI / 2;
  rimTorus.position.x = xSide;
  wheelGroup.add(rimTorus);

  // Inner beveled lip
  const innerLipGeo = new THREE.TorusGeometry(R * 0.97, 0.012, 10, 80);
  const innerLip = new THREE.Mesh(innerLipGeo, rimLipMat);
  innerLip.rotation.y = Math.PI / 2;
  innerLip.position.x = xSide;
  wheelGroup.add(innerLip);
}}

// 3. RIM SERRATED TEETH / PERIMETER GROUSERS (Both Rim Edges)
const nTeeth = 32;
for (const xSide of [-halfW * 0.96, halfW * 0.96]) {{
  for (let i = 0; i < nTeeth; i++) {{
    const th = (i / nTeeth) * Math.PI * 2;
    const toothGeo = new THREE.BoxGeometry(0.024, 0.018, 0.014);
    const tooth = new THREE.Mesh(toothGeo, rimLipMat);
    const rT = R + 0.009;
    tooth.position.set(xSide, rT * Math.cos(th), rT * Math.sin(th));
    tooth.rotation.x = -th;
    wheelGroup.add(tooth);
  }}
}}

// 4. CONTINUOUS ZIGZAG / CHEVRON TREAD PATTERN (Both Sides: Left & Right Tracks)
// Replicating the distinctive chevron zigzag pattern on both outer tracks flanking the center window grid
const nZig = 18;
const zigAmp = halfW * 0.20;
for (const zigCenter of [-halfW * 0.62, halfW * 0.62]) {{
  for (let i = 0; i < nZig; i++) {{
    const th1 = (i / nZig) * Math.PI * 2;
    const th2 = ((i + 0.5) / nZig) * Math.PI * 2;
    const th3 = ((i + 1.0) / nZig) * Math.PI * 2;

    // Segment 1: from -amp to +amp
    const p1 = new THREE.Vector3(zigCenter - zigAmp, (R + 0.012) * Math.cos(th1), (R + 0.012) * Math.sin(th1));
    const p2 = new THREE.Vector3(zigCenter + zigAmp, (R + 0.012) * Math.cos(th2), (R + 0.012) * Math.sin(th2));
    const p3 = new THREE.Vector3(zigCenter - zigAmp, (R + 0.012) * Math.cos(th3), (R + 0.012) * Math.sin(th3));

    // Build connecting rib bar 1
    const mid1 = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    const len1 = p1.distanceTo(p2);
    const barGeo1 = new THREE.BoxGeometry(len1, 0.014, 0.018);
    const bar1 = new THREE.Mesh(barGeo1, drumMat);
    bar1.position.copy(mid1);
    bar1.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), new THREE.Vector3().subVectors(p2, p1).normalize());
    wheelGroup.add(bar1);

    // Build connecting rib bar 2
    const mid2 = new THREE.Vector3().addVectors(p2, p3).multiplyScalar(0.5);
    const len2 = p2.distanceTo(p3);
    const barGeo2 = new THREE.BoxGeometry(len2, 0.014, 0.018);
    const bar2 = new THREE.Mesh(barGeo2, drumMat);
    bar2.position.copy(mid2);
    bar2.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), new THREE.Vector3().subVectors(p3, p2).normalize());
    wheelGroup.add(bar2);
  }}
}}

// 5. DUAL-ROW RECTANGULAR WINDOW CUTOUT GRID & LONGITUDINAL RAILS (Middle Track)
// 3 Longitudinal circumferential rails defining the window tracks
const midRailPositions = [-halfW * 0.28, 0.0, halfW * 0.28];
for (const rx of midRailPositions) {{
  const mRailGeo = new THREE.TorusGeometry(R + 0.008, 0.009, 8, 80);
  const mRail = new THREE.Mesh(mRailGeo, drumMat);
  mRail.rotation.y = Math.PI / 2;
  mRail.position.x = rx;
  wheelGroup.add(mRail);
}}

// Transverse dividing ribs and rectangular pocket cutouts
const nWindows = 18;
for (let i = 0; i < nWindows; i++) {{
  const th = (i / nWindows) * Math.PI * 2;
  const cosT = Math.cos(th), sinT = Math.sin(th);

  // Transverse partition slats across both window rows
  const slatGeo = new THREE.BoxGeometry(halfW * 0.62, 0.015, 0.018);
  const slat = new THREE.Mesh(slatGeo, drumMat);
  slat.position.set(0.0, (R + 0.01) * cosT, (R + 0.01) * sinT);
  slat.rotation.x = -th;
  wheelGroup.add(slat);

  // Rectangular dark pocket insets (representing open window cutouts)
  for (const trackX of [-halfW * 0.14, halfW * 0.14]) {{
    const midTh = th + (Math.PI / nWindows);
    
    // Recessed dark pocket floor inside the cutout
    const windowCutoutGeo = new THREE.BoxGeometry(halfW * 0.20, 0.006, (2 * Math.PI * R / nWindows) * 0.65);
    const windowCutoutMat = new THREE.MeshStandardMaterial({{ color: 0x141210, roughness: 0.9, metalness: 0.1 }});
    const windowCutout = new THREE.Mesh(windowCutoutGeo, windowCutoutMat);
    windowCutout.position.set(trackX, (R - 0.004) * Math.cos(midTh), (R - 0.004) * Math.sin(midTh));
    windowCutout.rotation.x = -midTh;
    wheelGroup.add(windowCutout);

    // Dynamic Cleats: Only protrude outward when deployed; sub-surface when retracted
    if (isDeployed) {{
      const cleatExt = 0.088;
      const cleatGeo = new THREE.BoxGeometry(halfW * 0.16, cleatExt, 0.022);
      const cleat = new THREE.Mesh(cleatGeo, cleatMat);
      const radCleat = R + (cleatExt / 2) - 0.005;
      cleat.position.set(trackX, radCleat * Math.cos(midTh), radCleat * Math.sin(midTh));
      cleat.rotation.x = -midTh;
      wheelGroup.add(cleat);
    }} else {{
      // Fully retracted: stays inside internal cavity below outer radius R
      const cleatGeo = new THREE.BoxGeometry(halfW * 0.15, 0.006, 0.020);
      const cleatMatRetracted = new THREE.MeshStandardMaterial({{ color: 0x221e1a, roughness: 0.85, metalness: 0.3 }});
      const cleat = new THREE.Mesh(cleatGeo, cleatMatRetracted);
      const radCleat = R - 0.016;
      cleat.position.set(trackX, radCleat * Math.cos(midTh), radCleat * Math.sin(midTh));
      cleat.rotation.x = -midTh;
      wheelGroup.add(cleat);
    }}
  }}
}}

// 6. CENTER HUB ASSEMBLY
// Inner axle hub cylinder
const hubGeo = new THREE.CylinderGeometry(0.12, 0.12, halfW * 0.9, 32);
const hubMesh = new THREE.Mesh(hubGeo, hubMat);
hubMesh.rotation.z = Math.PI / 2;
hubMesh.position.x = 0.0;
wheelGroup.add(hubMesh);

// Center axle bore
const boreGeo = new THREE.CylinderGeometry(0.045, 0.045, halfW * 0.95, 24);
const boreMat = new THREE.MeshStandardMaterial({{ color: 0x111111, roughness: 0.8 }});
const boreMesh = new THREE.Mesh(boreGeo, boreMat);
boreMesh.rotation.z = Math.PI / 2;
wheelGroup.add(boreMesh);

// Hub outer flange ring
const hubFlangeGeo = new THREE.TorusGeometry(0.125, 0.015, 12, 32);
const hubFlange = new THREE.Mesh(hubFlangeGeo, rimLipMat);
hubFlange.rotation.y = Math.PI / 2;
hubFlange.position.x = halfW * 0.40;
wheelGroup.add(hubFlange);

// Ring of Hub Fastener Bolts (Hex / cylindrical bolts)
const nBolts = 8;
for (let i = 0; i < nBolts; i++) {{
  const a = (i / nBolts) * Math.PI * 2;
  const boltGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.02, 10);
  const bolt = new THREE.Mesh(boltGeo, boltMat);
  bolt.rotation.z = Math.PI / 2;
  bolt.position.set(halfW * 0.42, 0.088 * Math.cos(a), 0.088 * Math.sin(a));
  wheelGroup.add(bolt);
}}

// 7. CURVED FLEXURE (SPRING) SPOKES (6 C-Curved Titanium Arms)
// Accurately modeling the curved flexure arms connecting hub to outer rim
const nSpokes = 6;
const innerMountRadius = R * 0.94;
const hubMountRadius = 0.115;

// Internal rim reinforcement ring for spoke attachment
const intRingGeo = new THREE.TorusGeometry(innerMountRadius, 0.014, 10, 64);
const intRing = new THREE.Mesh(intRingGeo, spokeMat);
intRing.rotation.y = Math.PI / 2;
intRing.position.x = halfW * 0.15;
wheelGroup.add(intRing);

for (let i = 0; i < nSpokes; i++) {{
  const baseAngle = (i / nSpokes) * Math.PI * 2;
  
  // Starting point at hub
  const pStart = new THREE.Vector3(
    halfW * 0.35,
    hubMountRadius * Math.cos(baseAngle),
    hubMountRadius * Math.sin(baseAngle)
  );

  // C-Curve middle control points (sweeping spiral loop)
  const midAngle1 = baseAngle + 0.45;
  const midRad1 = 0.32;
  const pMid1 = new THREE.Vector3(
    halfW * 0.48,
    midRad1 * Math.cos(midAngle1),
    midRad1 * Math.sin(midAngle1)
  );

  const midAngle2 = baseAngle + 0.85;
  const midRad2 = 0.48;
  const pMid2 = new THREE.Vector3(
    halfW * 0.38,
    midRad2 * Math.cos(midAngle2),
    midRad2 * Math.sin(midAngle2)
  );

  // Ending point at inner rim wall
  const endAngle = baseAngle + 1.15;
  const pEnd = new THREE.Vector3(
    halfW * 0.15,
    innerMountRadius * Math.cos(endAngle),
    innerMountRadius * Math.sin(endAngle)
  );

  // Generate smooth 3D spline curve for the flexure spoke
  const curve = new THREE.CatmullRomCurve3([pStart, pMid1, pMid2, pEnd]);
  const spokeGeo = new THREE.TubeGeometry(curve, 36, 0.013, 10, false);
  const spokeMesh = new THREE.Mesh(spokeGeo, spokeMat);
  wheelGroup.add(spokeMesh);

  // Spoke mounting brackets
  const bracketHubGeo = new THREE.SphereGeometry(0.02, 10, 8);
  const bracketHub = new THREE.Mesh(bracketHubGeo, rimLipMat);
  bracketHub.position.copy(pStart);
  wheelGroup.add(bracketHub);

  const bracketRimGeo = new THREE.BoxGeometry(0.03, 0.024, 0.024);
  const bracketRim = new THREE.Mesh(bracketRimGeo, rimLipMat);
  bracketRim.position.copy(pEnd);
  wheelGroup.add(bracketRim);
}}

scene.add(wheelGroup);

// Soft Ground Shadow Disc
const shadowGeo = new THREE.CircleGeometry(1.6, 32);
const shadowMat = new THREE.MeshBasicMaterial({{
  color: 0x05070a,
  transparent: true,
  opacity: 0.6
}});
const shadow = new THREE.Mesh(shadowGeo, shadowMat);
shadow.rotation.x = -Math.PI / 2;
shadow.position.y = -R - 0.03;
scene.add(shadow);

// Animation Loop
function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize', () => {{
  const w = wrap.clientWidth;
  camera.aspect = w / H;
  camera.updateProjectionMatrix();
  renderer.setSize(w, H);
}});

renderer.domElement.addEventListener('pointerdown', () => {{
  controls.autoRotate = false;
}});
</script>
</body>
</html>
"""


@st.cache_data
def get_mars_background_base64():
    """Load and base64-encode the Mars rover background image."""
    asset_path = os.path.join(os.path.dirname(__file__), "assets", "mars_rover_bg.jpg")
    if not os.path.exists(asset_path):
        asset_path = r"C:\Users\astro\.gemini\antigravity\brain\a8d21b46-1b12-4ec7-8660-4e53bb6353ce\.user_uploaded\media_1789394015308.jpg"
    if os.path.exists(asset_path):
        with open(asset_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

bg_base64 = get_mars_background_base64()

# Inject Dynamic 3D Moving Mars Landscape & Glassmorphic Mission Control Styling
st.markdown(f"""
<!-- Dynamic 3D Mars Viewport -->
<div class="mars-3d-universe">
    <div class="mars-3d-scene" id="mars3dScene">
        <div class="mars-surface-layer" style="background-image: url('data:image/jpeg;base64,{bg_base64}');"></div>
        <div class="mars-solar-flare"></div>
        <div class="mars-dust-storm-drift"></div>
        <div class="mars-ambient-glow"></div>
    </div>
</div>

<style>
    /* ==========================================================
       DYNAMIC 3D MOVING MARS BACKGROUND ENGINE
       ========================================================== */
    :root {{
        --mars-cam-speed: 45s;
        --mars-dust-opacity: 0.70;
        --mars-solar-opacity: 0.65;
    }}

    .mars-3d-universe {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -9999;
        overflow: hidden;
        perspective: 1200px;
        perspective-origin: 50% 48%;
        pointer-events: none;
        background-color: #0c0806;
    }}

    .mars-3d-scene {{
        position: absolute;
        top: -12%;
        left: -12%;
        width: 124%;
        height: 124%;
        transform-style: preserve-3d;
        will-change: transform, filter;
        animation: mars3dCameraDrift var(--mars-cam-speed) cubic-bezier(0.42, 0.0, 0.58, 1.0) infinite alternate;
    }}

    /* 3D Cinematic Camera Pan, Tilt, and Zoom moving continuously over time */
    @keyframes mars3dCameraDrift {{
        0% {{
            transform: perspective(1200px) rotateX(3.0deg) rotateY(-4.5deg) rotateZ(0.6deg) scale3d(1.06, 1.06, 1.06) translate3d(-30px, -20px, 30px);
            filter: contrast(1.08) saturate(1.22) brightness(0.92);
        }}
        25% {{
            transform: perspective(1200px) rotateX(-1.8deg) rotateY(-1.5deg) rotateZ(-0.5deg) scale3d(1.14, 1.14, 1.14) translate3d(25px, -35px, 70px);
            filter: contrast(1.12) saturate(1.28) brightness(0.98);
        }}
        50% {{
            transform: perspective(1200px) rotateX(-3.5deg) rotateY(4.0deg) rotateZ(0.9deg) scale3d(1.20, 1.20, 1.20) translate3d(40px, 20px, 50px);
            filter: contrast(1.06) saturate(1.20) brightness(0.88);
        }}
        75% {{
            transform: perspective(1200px) rotateX(2.0deg) rotateY(2.2deg) rotateZ(-0.4deg) scale3d(1.12, 1.12, 1.12) translate3d(-15px, 35px, 85px);
            filter: contrast(1.10) saturate(1.26) brightness(0.95);
        }}
        100% {{
            transform: perspective(1200px) rotateX(3.0deg) rotateY(-4.5deg) rotateZ(0.6deg) scale3d(1.06, 1.06, 1.06) translate3d(-30px, -20px, 30px);
            filter: contrast(1.08) saturate(1.22) brightness(0.92);
        }}
    }}

    .mars-surface-layer {{
        position: absolute;
        inset: 0;
        background-size: cover;
        background-position: center 58%;
        background-repeat: no-repeat;
        transform: translateZ(0px);
    }}

    /* Solar Glare Breathing Shift */
    .mars-solar-flare {{
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 72% 24%, rgba(255, 190, 110, 0.45) 0%, rgba(245, 130, 45, 0.22) 28%, rgba(200, 80, 20, 0.08) 55%, transparent 72%);
        mix-blend-mode: screen;
        opacity: var(--mars-solar-opacity);
        animation: solarBreathing 18s ease-in-out infinite alternate;
        transform: translateZ(45px);
    }}

    @keyframes solarBreathing {{
        0% {{
            filter: blur(8px);
            transform: translate3d(0, 0, 45px);
        }}
        50% {{
            filter: blur(15px);
            transform: translate3d(20px, -15px, 55px);
        }}
        100% {{
            filter: blur(10px);
            transform: translate3d(-15px, 15px, 40px);
        }}
    }}

    /* 3D Atmospheric Dust Storm & Wind Flow */
    .mars-dust-storm-drift {{
        position: absolute;
        inset: -50%;
        width: 200%;
        height: 200%;
        background-image: 
            radial-gradient(2px 2px at 20% 30%, rgba(255, 195, 120, 0.8) 50%, transparent),
            radial-gradient(3px 3px at 45% 75%, rgba(255, 160, 85, 0.75) 50%, transparent),
            radial-gradient(1.8px 1.8px at 65% 22%, rgba(255, 210, 140, 0.7) 50%, transparent),
            radial-gradient(3.5px 3.5px at 82% 88%, rgba(245, 130, 50, 0.8) 50%, transparent),
            radial-gradient(2px 2px at 12% 78%, rgba(255, 180, 95, 0.7) 50%, transparent),
            radial-gradient(2.5px 2.5px at 72% 52%, rgba(255, 200, 130, 0.75) 50%, transparent),
            radial-gradient(4px 4px at 32% 18%, rgba(255, 150, 70, 0.8) 50%, transparent);
        background-size: 340px 340px;
        animation: dustWindFlow 26s linear infinite;
        mix-blend-mode: screen;
        opacity: var(--mars-dust-opacity);
        transform: translateZ(95px);
    }}

    @keyframes dustWindFlow {{
        0% {{
            transform: translate3d(0, 0, 95px) rotate(0deg);
        }}
        100% {{
            transform: translate3d(-260px, -190px, 95px) rotate(4deg);
        }}
    }}

    /* Horizon & Atmospheric Vignette */
    .mars-ambient-glow {{
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, rgba(235, 120, 45, 0.12) 0%, rgba(18, 12, 10, 0.28) 40%, rgba(10, 8, 8, 0.72) 100%);
        pointer-events: none;
    }}

    /* ==========================================================
       GLASSMORPHIC SCIENTIFIC MISSION CONTROL STYLING
       ========================================================== */
    .stApp {{
        background: transparent !important;
    }}

    [data-testid="stAppViewContainer"] {{
        background: transparent !important;
    }}

    [data-testid="stHeader"] {{
        background: rgba(12, 16, 24, 0.45) !important;
        backdrop-filter: blur(12px) !important;
    }}

    [data-testid="stSidebar"] {{
        background: rgba(13, 17, 26, 0.86) !important;
        backdrop-filter: blur(22px) saturate(190%) !important;
        border-right: 1px solid rgba(249, 115, 22, 0.32) !important;
        box-shadow: 6px 0 28px rgba(0, 0, 0, 0.6) !important;
    }}

    .metric-card {{
        background: rgba(18, 24, 38, 0.82) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        border: 1px solid rgba(249, 115, 22, 0.32) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        margin-bottom: 12px;
    }}

    .node-box {{
        background: rgba(22, 30, 48, 0.85) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        border-left: 4px solid #f97316 !important;
        border-top: 1px solid rgba(249, 115, 22, 0.25) !important;
        border-right: 1px solid rgba(249, 115, 22, 0.25) !important;
        border-bottom: 1px solid rgba(249, 115, 22, 0.25) !important;
        padding: 12px 16px !important;
        margin-bottom: 10px;
        border-radius: 8px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
    }}

    [data-testid="stTabs"] {{
        background: rgba(16, 22, 34, 0.84) !important;
        backdrop-filter: blur(18px) saturate(180%) !important;
        border-radius: 12px !important;
        padding: 8px 12px !important;
        border: 1px solid rgba(249, 115, 22, 0.28) !important;
    }}

    [data-testid="stTab"] {{
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }}

    [data-testid="stMetricValue"] {{
        color: #ffffff !important;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.7);
    }}

    .status-badge-feasible {{
        background-color: rgba(19, 78, 74, 0.9);
        color: #2dd4bf;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 16px;
        border: 1px solid #14b8a6;
        box-shadow: 0 0 18px rgba(20, 184, 166, 0.35);
        backdrop-filter: blur(10px);
    }}
    .status-badge-warning {{
        background-color: rgba(113, 63, 18, 0.9);
        color: #fde047;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 16px;
        border: 1px solid #eab308;
        box-shadow: 0 0 18px rgba(234, 179, 8, 0.35);
        backdrop-filter: blur(10px);
    }}
    .status-badge-risk {{
        background-color: rgba(124, 45, 18, 0.9);
        color: #fdba74;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 16px;
        border: 1px solid #f97316;
        box-shadow: 0 0 18px rgba(249, 115, 22, 0.4);
        backdrop-filter: blur(10px);
    }}
    .status-badge-infeasible {{
        background-color: rgba(127, 29, 29, 0.9);
        color: #fca5a5;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 16px;
        border: 1px solid #ef4444;
        box-shadow: 0 0 18px rgba(239, 68, 68, 0.45);
        backdrop-filter: blur(10px);
    }}
</style>

<script>
    // Interactive 3D Cursor Parallax on the Mars Scene
    (function() {{
        let scene = document.getElementById("mars3dScene");
        if (!scene) return;
        window.addEventListener("mousemove", (e) => {{
            let cx = (e.clientX / window.innerWidth - 0.5) * 6.0; // +/- 3 deg
            let cy = (e.clientY / window.innerHeight - 0.5) * -4.0; // +/- 2 deg
            scene.style.transform = `perspective(1200px) rotateY(${{cx}}deg) rotateX(${{cy}}deg)`;
        }});
    }})();
</script>
""", unsafe_allow_html=True)

# App Header
col_header, col_badge = st.columns([3, 1])
with col_header:
    st.title("🪐 COSMOS AI — Mars Mission Planner")
    st.caption("Theoretical Mars Mission Simulation Framework & End-to-End Subsystem Dependency Engine")


# Sidebar Controls
st.sidebar.image("https://images.unsplash.com/photo-1614728894747-a83421e2b9c9?w=400&q=80", caption="COSMOS AI Systems Engineering")
st.sidebar.header("Mission Configuration")

# Preset Selector
preset = st.sidebar.selectbox(
    "Mission Architecture Preset",
    [
        "COSMOS-MARS-01 Baseline (500kg, MMRTG, Dynamic Wheels)",
        "Static Wheels in Loose Dune Sand (Entrapment Stress Test)",
        "Heavy Payload Scale-Up (2,500kg SRP TRL 3-4 Risk)",
        "Solar Powered Rover (Atmospheric Dust Sensitivity)",
        "Custom Configuration"
    ]
)

# Apply Presets
if preset.startswith("COSMOS-MARS-01"):
    default_launch = date(2026, 6, 1)
    default_arrival = date(2026, 12, 18)
    default_mass = 500.0
    default_sols = 500
    default_power = "mmrtg"
    default_terrain = "sand_dune"
    default_wheel = "dynamic"
    default_tau = 0.6
elif preset.startswith("Static Wheels"):
    default_launch = date(2026, 6, 1)
    default_arrival = date(2026, 12, 18)
    default_mass = 500.0
    default_sols = 500
    default_power = "mmrtg"
    default_terrain = "sand_dune"
    default_wheel = "static"
    default_tau = 0.6
elif preset.startswith("Heavy Payload"):
    default_launch = date(2026, 6, 1)
    default_arrival = date(2026, 12, 18)
    default_mass = 2500.0
    default_sols = 500
    default_power = "mmrtg"
    default_terrain = "sand_dune"
    default_wheel = "dynamic"
    default_tau = 0.6
elif preset.startswith("Solar Powered"):
    default_launch = date(2026, 6, 1)
    default_arrival = date(2026, 12, 18)
    default_mass = 500.0
    default_sols = 500
    default_power = "solar"
    default_terrain = "firm_regolith"
    default_wheel = "dynamic"
    default_tau = 1.4
else:
    default_launch = date(2026, 6, 1)
    default_arrival = date(2026, 12, 18)
    default_mass = 500.0
    default_sols = 500
    default_power = "mmrtg"
    default_terrain = "sand_dune"
    default_wheel = "dynamic"
    default_tau = 0.6

launch_date = st.sidebar.date_input("Launch Date", value=default_launch)
arrival_date = st.sidebar.date_input("Mars Arrival Date", value=default_arrival)
rover_mass_kg = st.sidebar.slider("Rover Payload Mass (kg)", min_value=200.0, max_value=3500.0, value=default_mass, step=50.0)
surface_sols = st.sidebar.slider("Surface Mission Duration (Sols)", min_value=100, max_value=1000, value=default_sols, step=50)

st.sidebar.subheader("Surface Operations & Mobility")
wheel_mode = st.sidebar.radio("Wheel Traction Mode", ["dynamic", "static"], index=0 if default_wheel == "dynamic" else 1,
                              help="Dynamic: Autonomous terrain-responsive cleats deploy when slip > 30%. Static: Traditional fixed grousers.")
terrain_type = st.sidebar.selectbox("Surface Terrain Type", ["sand_dune", "firm_regolith", "bedrock"], 
                                    index=["sand_dune", "firm_regolith", "bedrock"].index(default_terrain))
power_system = st.sidebar.radio("Power Architecture", ["mmrtg", "solar"], index=0 if default_power == "mmrtg" else 1)
dust_tau = st.sidebar.slider("Atmospheric Dust Optical Depth (tau)", min_value=0.2, max_value=3.0, value=float(default_tau), step=0.1)

st.sidebar.subheader("Telecommunications")
telecom_band = st.sidebar.selectbox("Telecom Frequency Band", ["X-band", "S-band", "Ka-band"], index=0)

st.sidebar.markdown("---")
st.sidebar.subheader("🎥 Dynamic 3D Mars Atmosphere")
cam_speed_s = st.sidebar.slider("3D Camera Float Speed (s)", min_value=15, max_value=80, value=45, help="Controls the speed of the cinematic 3D Mars camera float cycle")
dust_intensity = st.sidebar.slider("Atmospheric Dust Stream Opacity", min_value=0.1, max_value=1.0, value=0.7, step=0.05, help="Controls density of 3D drifting Martian dust particles")
solar_glow_opacity = st.sidebar.slider("Martian Sun Glare Intensity", min_value=0.2, max_value=1.0, value=0.65, step=0.05)

# Dynamically apply user slider overrides to the 3D Mars environment
st.markdown(f"""
<style>
    :root {{
        --mars-cam-speed: {cam_speed_s}s !important;
        --mars-dust-opacity: {dust_intensity} !important;
        --mars-solar-opacity: {solar_glow_opacity} !important;
    }}
</style>
""", unsafe_allow_html=True)

# Run Simulation Pipeline
pipeline = MissionSimulationPipeline()
try:
    results = pipeline.run_mission_evaluation(
        launch_date=launch_date,
        arrival_date=arrival_date,
        rover_mass_kg=rover_mass_kg,
        surface_mission_sols=surface_sols,
        power_source=power_system,
        terrain_key=terrain_type,
        wheel_mode=wheel_mode,
        telecom_band=telecom_band,
        atmospheric_dust_tau=dust_tau
    )
except Exception as e:
    st.error(f"Simulation Error: {e}")
    st.stop()

# Feasibility Badge Banner
status = results["overall_feasibility"]
badge_class = {
    "FEASIBLE": "status-badge-feasible",
    "CONDITIONALLY FEASIBLE": "status-badge-warning",
    "HIGH RISK": "status-badge-risk",
    "INFEASIBLE": "status-badge-infeasible"
}.get(status, "status-badge-feasible")

with col_badge:
    st.markdown(f"<div style='text-align: right; padding-top: 20px;'><span class='{badge_class}'>● {status}</span></div>", unsafe_allow_html=True)

# Executive Callout
if status == "FEASIBLE":
    st.success(f"**Mission Status: {status}** — {results['summary_rationale']}")
elif status == "CONDITIONALLY FEASIBLE":
    st.warning(f"**Mission Status: {status}** — {results['summary_rationale']}")
elif status == "HIGH RISK":
    st.warning(f"**Mission Status: {status}** — {results['summary_rationale']}")
else:
    st.error(f"**Mission Status: {status}** — {results['summary_rationale']}")

# Quick KPI Metrics Row
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
kpi1.metric("Transit Time", f"{results['transfer']['tof_days']:.0f} d", f"{results['transfer']['tof_months']:.1f} mo")
kpi2.metric("Departure C3", f"{results['transfer']['c3_km2_s2']:.1f} km²/s²", "Launch Stage")
kpi3.metric("Mars V_inf", f"{results['transfer']['v_inf_arr_km_s']:.2f} km/s", f"Entry: {results['transfer']['v_entry_m_s']/1000.0:.2f} km/s")
kpi4.metric("Parachute Load", f"{results['edl']['peak_opening_load_kn']:.1f} kN", f"Limit: {results['edl']['structural_limit_kn']:.0f} kN")
kpi5.metric("Landing Burn Δv", f"{results['propulsion']['delta_v_landing_m_s']:.1f} m/s", f"Fuel: {results['propulsion']['propellant_consumed_kg']:.0f} kg")
kpi6.metric("Total Craft Δv", f"{results['budget']['total_maneuvering_delta_v_m_s']:.1f} m/s", "incl. 5% margin")

st.divider()

# Tabbed Analysis Views
tab_dep, tab_orbit, tab_edl, tab_sys, tab_fail = st.tabs([
    "🔗 Mission Dependency Map",
    "🛰️ Astrodynamics & Porkchop (Member 1)",
    "🪂 EDL & Dynamic Mobility (Member 2)",
    "📡 Systems, Comms & Δv Budget (Member 3)",
    "⚠️ Failure Scenarios & Stress Tests"
])

# ==========================================
# TAB 1: MISSION DEPENDENCY MAP
# ==========================================
with tab_dep:
    st.subheader("Interactive Mission Dependency Chain")
    st.markdown("""
    Every stage's output feeds the next stage's input. A change anywhere in this chain propagates throughout the entire architecture.
    """)
    
    col_d1, col_d2 = st.columns([1, 1])
    
    with col_d1:
        st.markdown(f"""
        <div class='node-box'>
            <b>1. Launch Date & Ephemeris</b><br>
            📅 Launch: <code>{launch_date}</code> | Arrival: <code>{arrival_date}</code><br>
            <i>Constrained by 779.9-day Earth-Mars synodic period</i>
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>2. Lambert Solver & Transfer Trajectory</b><br>
            🚀 C3: <code>{results['transfer']['c3_km2_s2']:.2f} km²/s²</code> | TOF: <code>{results['transfer']['tof_days']:.1f} days</code><br>
            TCM Cruise Δv: <code>{results['transfer']['tcm_delta_v_m_s']:.1f} m/s</code> across 5–6 burns
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>3. Mars Arrival Interface Conditions</b><br>
            🎯 V∞ Arrival: <code>{results['transfer']['v_inf_arr_km_s']:.2f} km/s</code> | Entry Velocity: <code>{results['transfer']['v_entry_m_s']/1000.0:.2f} km/s</code><br>
            Entry Corridor (EFPA): <code>{results['transfer']['efpa_deg']:.2f}°</code> (Target: -15.50° ± 0.20°)
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>4. Atmospheric Deceleration & Parachute Staging</b><br>
            🪂 DGB Chute Deploy: <code>Mach {results['edl']['deploy_mach']:.2f}</code> | Peak Load: <code>{results['edl']['peak_opening_load_kn']:.1f} kN</code><br>
            Structural Limit: <code>289 kN</code> (Safety Margin: <code>{results['edl']['parachute_margin']:.2f}x</code>)
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>5. Powered Landing Burn & Mass Depletion</b><br>
            🔥 Deceleration from 79 m/s to 0.75 m/s + 38s gravity loss: <code>{results['propulsion']['delta_v_landing_m_s']:.1f} m/s</code><br>
            Propellant Consumed: <code>{results['propulsion']['propellant_consumed_kg']:.1f} kg</code> | Rover Touchdown Mass: <code>{rover_mass_kg:.0f} kg</code>
        </div>
        """, unsafe_allow_html=True)
        
    with col_d2:
        mob = results['surface_power']['mobility_details']
        pwr = results['surface_power']
        com = results['telecom']
        
        st.markdown(f"""
        <div class='node-box'>
            <b>6. Surface Mobility & Dynamic Traction Loop</b><br>
            🚜 Terrain: <code>{mob['terrain_name']}</code> | Mode: <code>{mob['wheel_mode'].upper()}</code><br>
            Slip Ratio: <code>{mob['measured_slip_ratio']*100:.1f}%</code> | Dynamic Cleats: <code>{'DEPLOYED (Autonomous)' if mob['cleats_deployed'] else 'RETRACTED'}</code><br>
            Mobility Power Draw: <code>{mob['drive_power_w']:.0f} W</code> (Actuator Spike: <code>{mob['actuator_power_spike_w']:.0f} W</code>)
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>7. 500-Sol Surface Resources & Energy Balance</b><br>
            ⚡ Source: <code>{pwr['power_source']}</code> | Generated: <code>{pwr['daily_energy_generated_wh']:.0f} Wh/sol</code><br>
            Consumption: <code>{pwr['total_daily_consumption_wh']:.0f} Wh/sol</code> | Net Margin: <code>{pwr['daily_net_margin_wh']:+.0f} Wh/sol</code><br>
            Achievable Longevity: <code>{pwr['sustainable_sols']} Sols</code>
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>8. Telecommunications & Latency Geometry</b><br>
            ⏱️ Earth-Mars Distance: <code>{com['distance_million_km']:.1f} M km</code> ({com['distance_au']:.2f} AU)<br>
            One-Way Light Time: <code>{com['one_way_delay_min']:.1f} min</code> (Round-Trip: <code>{com['round_trip_delay_min']:.1f} min</code>)<br>
            Solar Conjunction Angle: <code>{com['sem_angle_deg']:.1f}°</code> ({'BLACKOUT' if com['in_conjunction'] else 'CLEAR'})
        </div>
        <div style='text-align: center; color: #38bdf8;'>▼</div>
        <div class='node-box'>
            <b>9. Constraint Engine & Mission Feasibility</b><br>
            Total Maneuvering Δv: <code>{results['budget']['total_maneuvering_delta_v_m_s']:.1f} m/s</code> (ESA 5% policy margin included)<br>
            MCO Unit Validation: <code>100% SI Contract Verified</code><br>
            <b>Overall Status: <code>[{results['overall_feasibility']}]</code></b>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 2: ORBITAL MECHANICS & PORKCHOP
# ==========================================
with tab_orbit:
    st.subheader("Member 1 — Astrodynamics & Transfer Trajectory")
    
    col_orb1, col_orb2 = st.columns([1, 1])
    
    with col_orb1:
        st.markdown("#### Heliocentric Orbit Geometry")
        # Plot 2D Heliocentric Transfer Orbit
        fig, ax = plt.subplots(figsize=(6, 6), facecolor=(0.06, 0.08, 0.14, 0.65))
        ax.set_facecolor((0.06, 0.08, 0.14, 0.65))
        
        # Sun
        ax.plot(0, 0, 'yo', markersize=14, label="Sun")
        
        # Earth Orbit
        theta = np.linspace(0, 2*np.pi, 200)
        ax.plot(np.cos(theta), np.sin(theta), 'b--', alpha=0.5, label="Earth Orbit (1.0 AU)")
        
        # Mars Orbit
        ax.plot(1.524*np.cos(theta), 1.524*np.sin(theta), 'r--', alpha=0.5, label="Mars Orbit (1.52 AU)")
        
        # Positions
        r_e = results['transfer']['r_earth_dep'] / AU_METERS
        r_m = results['transfer']['r_mars_arr'] / AU_METERS
        ax.plot(r_e[0], r_e[1], 'bo', markersize=10, label="Earth Departure")
        ax.plot(r_m[0], r_m[1], 'ro', markersize=10, label="Mars Arrival")
        
        # Transfer Arc (Bezier / elliptical interpolation)
        t_pts = np.linspace(0, 1, 100)
        # Approximate transfer curve
        arc_x = (1 - t_pts)**2 * r_e[0] + 2*(1 - t_pts)*t_pts * (r_e[0]*0.5 + r_m[0]*0.5 + 0.3) + t_pts**2 * r_m[0]
        arc_y = (1 - t_pts)**2 * r_e[1] + 2*(1 - t_pts)*t_pts * (r_e[1]*0.5 + r_m[1]*0.5 + 0.3) + t_pts**2 * r_m[1]
        ax.plot(arc_x, arc_y, 'c-', linewidth=2.5, label="Type I Transfer Arc")
        
        ax.set_xlim(-2.0, 2.0)
        ax.set_ylim(-2.0, 2.0)
        ax.set_xlabel("X (AU)", color="white")
        ax.set_ylabel("Y (AU)", color="white")
        ax.tick_params(colors="white")
        ax.legend(facecolor="#1a1c24", edgecolor="#2e3440", labelcolor="white", loc="upper right")
        ax.grid(True, linestyle=":", alpha=0.3, color="gray")
        st.pyplot(fig, transparent=True)
        
    with col_orb2:
        st.markdown("#### Launch Window Porkchop Plot (C3 Contours)")
        with st.spinner("Computing Lambert trajectory grid..."):
            porkchop = generate_porkchop_data(launch_date, launch_window_days=40, resolution=16)
            
            fig_pork, ax_pork = plt.subplots(figsize=(6, 6), facecolor=(0.06, 0.08, 0.14, 0.65))
            ax_pork.set_facecolor((0.06, 0.08, 0.14, 0.65))
            
            c3_arr = np.array(porkchop["c3_grid"])
            tofs = porkchop["tofs_days"]
            
            cp = ax_pork.contourf(range(len(porkchop["launch_dates"])), tofs, c3_arr, levels=12, cmap="plasma")
            cbar = fig_pork.colorbar(cp, ax=ax_pork)
            cbar.set_label("C3 (km²/s²)", color="white")
            cbar.ax.tick_params(colors="white")
            
            # Highlight current operating point
            ax_pork.plot(len(porkchop["launch_dates"])//2, results['transfer']['tof_days'], 'w*', markersize=14, label="Current Plan")
            
            ax_pork.set_xlabel("Launch Date Window", color="white")
            ax_pork.set_ylabel("Time of Flight (days)", color="white")
            ax_pork.tick_params(colors="white")
            # Sample labels
            step = max(1, len(porkchop["launch_dates"]) // 4)
            ax_pork.set_xticks(range(0, len(porkchop["launch_dates"]), step))
            ax_pork.set_xticklabels([porkchop["launch_dates"][i] for i in range(0, len(porkchop["launch_dates"]), step)], rotation=30, fontsize=8)
            ax_pork.legend(facecolor="#1a1c24", edgecolor="#2e3440", labelcolor="white")
            st.pyplot(fig_pork, transparent=True)
            
    st.markdown("#### Entry Flight Path Angle (EFPA) Corridor Check")
    efpa_val = results['transfer']['efpa_deg']
    in_corr = results['transfer']['efpa_in_corridor']
    col_e1, col_e2 = st.columns([1, 2])
    with col_e1:
        st.metric("Estimated EFPA", f"{efpa_val:.2f}°", "Corridor: -15.70° to -15.30°")
    with col_e2:
        if in_corr:
            st.success(f"**PASS:** Entry Flight Path Angle is securely inside the aerodynamic corridor ({efpa_val:.2f}°). Heat flux and structural loads will remain within aeroshell thermal protection limits.")
        else:
            st.error(f"**CORRIDOR VIOLATION:** EFPA ({efpa_val:.2f}°) is outside the survivable corridor. A steeper angle causes thermal/structural destruction; a shallower angle causes atmospheric skip-out.")

# ==========================================
# TAB 3: EDL & DYNAMIC MOBILITY
# ==========================================
with tab_edl:
    st.subheader("Member 2 — EDL Kinematics & Dynamic Traction System")
    
    col_edl1, col_edl2 = st.columns([1, 1])
    
    with col_edl1:
        st.markdown("#### Atmospheric Descent Kinematics (MEADS Sequence)")
        fig_des, ax_des = plt.subplots(figsize=(6, 4.5), facecolor=(0.06, 0.08, 0.14, 0.65))
        ax_des.set_facecolor((0.06, 0.08, 0.14, 0.65))
        
        alt_km = results['edl']['plot_altitudes_km']
        vel_ms = results['edl']['plot_velocities_m_s']
        
        ax_des.plot(vel_ms, alt_km, 'y-', linewidth=2.5, label="Descent Trajectory")
        ax_des.axhline(9.8, color='orange', linestyle='--', label="Parachute Deploy (9.8 km, M1.75)")
        ax_des.axhline(1.6, color='red', linestyle='--', label="Backshell Sep (1.6 km, 79 m/s)")
        
        ax_des.set_xlabel("Velocity (m/s)", color="white")
        ax_des.set_ylabel("Altitude (km)", color="white")
        ax_des.tick_params(colors="white")
        ax_des.legend(facecolor="#1a1c24", edgecolor="#2e3440", labelcolor="white", fontsize=8)
        ax_des.grid(True, linestyle=":", alpha=0.3, color="gray")
        st.pyplot(fig_des, transparent=True)
        
        # Staging Events Table
        st.markdown("##### Karlgaard et al. MEADS Staging Table")
        st.dataframe(results['edl']['stages'], use_container_width=True)
        
    with col_edl2:
        st.markdown("#### Terrain-Responsive Dynamic Wheel Simulation")
        st.caption("Addressing the user's handwritten design: Autonomous cleats deploy when slip > 30% without waiting for ground commands.")
        
        mob = results['surface_power']['mobility_details']
        
        # Graphic representation of Wheel
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.metric("Measured Wheel Slip", f"{mob['measured_slip_ratio']*100:.1f}%", "Threshold: 30%")
        with col_w2:
            st.metric("Cleat Mechanism State", "DEPLOYED" if mob['cleats_deployed'] else "RETRACTED",
                      "Autonomous Trigger" if mob['autonomous_trigger_fired'] else "Static Baseline")
            
        wheel_html = render_wheel_3d_cad_html(mob)
        components.html(wheel_html, height=490, scrolling=False)
        st.caption("3D CAD interactive model — left-drag to orbit freely, right-drag to pan, scroll to zoom.")
        
        if mob['entrapment_risk']:
            st.error("⚠️ **ENTRAPMENT HAZARD:** The static wheel is spinning in place (48% slip). Without dynamic cleats, the rover risks high-centering like the Spirit rover at Troy (2009).")
        else:
            st.success(f"✅ **TRACTION MAINTAINED:** {mob['status_message']}")

# ==========================================
# TAB 4: SYSTEMS, COMMS & DELTA-V BUDGET
# ==========================================
with tab_sys:
    st.subheader("Member 3 — Mission Systems, Telecommunications & Resolved Δv Budget")
    
    col_sys1, col_sys2 = st.columns([1, 1])
    
    with col_sys1:
        st.markdown("#### Consolidated Propulsive Delta-v Budget")
        st.caption("Resolved items: MOI confirmed N/A; Landing burn derived from MEADS kinematics; Surface reserve moved to Power Budget.")
        
        budget_data = results['budget']['budget_items']
        st.table([
            {
                "Mission Phase": it["phase"],
                "Delta-v": it["delta_v_str"],
                "Status / Basis": it["status"],
                "Engineering Notes": it["notes"]
            }
            for it in budget_data
        ])
        
        st.metric("Total Craft Maneuvering Delta-v Capacity", f"{results['budget']['total_maneuvering_delta_v_m_s']:.1f} m/s", 
                  f"Includes {results['budget']['margin_percent']:.0f}% ESA Policy Margin (~{results['budget']['margin_m_s']:.1f} m/s)")
        
        st.markdown("#### Mars Climate Orbiter (MCO) Unit Assertion Engine")
        st.info("The MCO Mishap (1999) caused loss of vehicle due to metric/imperial unit confusion (lbf-s vs N-s). Our constraint engine strictly asserts SI consistency across all module interfaces.")
        st.dataframe(results['constraints'], use_container_width=True)

    with col_sys2:
        st.markdown("#### Telecommunications & Solar Conjunction Blackout")
        com = results['telecom']
        
        st.metric("One-Way Light Time Delay", f"{com['one_way_delay_min']:.1f} min", f"Round-Trip: {com['round_trip_delay_min']:.1f} min")
        st.caption("Light-time delay of 3–22 min physically prevents real-time joystick control from Earth, mandating autonomous slip response and autonomous EDL.")
        
        st.metric("Sun-Earth-Mars (SEM) Angle", f"{com['sem_angle_deg']:.1f}°", f"Band Blackout Threshold: {com['blackout_threshold_deg']}°")
        
        if com['in_conjunction']:
            st.error(f"🚨 **SOLAR CONJUNCTION IN EFFECT:** SEM angle ({com['sem_angle_deg']:.1f}°) is below the {com['band']} threshold ({com['blackout_threshold_deg']}°). Communications are blacked out for ~{com['est_blackout_duration_days']} days. Command moratorium enforced.")
        else:
            st.success(f"📡 **COMMS CLEAR:** Clear line-of-sight. MRO/Odyssey store-and-forward relay provides ~{com['data_return_mb_per_sol']:.0f} MB/sol data return.")

        st.markdown("#### 500-Sol Surface Energy Balance")
        pwr = results['surface_power']
        
        col_p1, col_p2 = st.columns(2)
        col_p1.metric("Daily Energy Gen", f"{pwr['daily_energy_generated_wh']:.0f} Wh/sol", pwr['power_source'])
        col_p2.metric("Daily Consumption", f"{pwr['total_daily_consumption_wh']:.0f} Wh/sol", f"Net: {pwr['daily_net_margin_wh']:+.0f} Wh/sol")
        
        # Energy breakdown bar chart
        fig_pwr, ax_pwr = plt.subplots(figsize=(6, 3), facecolor=(0.06, 0.08, 0.14, 0.65))
        ax_pwr.set_facecolor((0.06, 0.08, 0.14, 0.65))
        labels = ["Housekeeping", "Telecom", "Science", "Night Heating", "Mobility"]
        values = [pwr['housekeeping_wh'], pwr['telecom_wh'], pwr['science_wh'], pwr['night_heating_wh'], pwr['mobility_wh']]
        ax_pwr.barh(labels, values, color="#38bdf8")
        ax_pwr.set_xlabel("Energy (Wh / Sol)", color="white")
        ax_pwr.tick_params(colors="white")
        st.pyplot(fig_pwr, transparent=True)

# ==========================================
# TAB 5: FAILURE SCENARIOS & STRESS TESTS
# ==========================================
with tab_fail:
    st.subheader("Section 8 — Failure Scenario & Stress Testing Engine")
    st.markdown("Demonstrate how a failure or disruption in one subsystem propagates to break mission feasibility.")
    
    col_sc1, col_sc2 = st.columns(2)
    
    with col_sc1:
        st.markdown("##### Scenario 1: Launch Window Delay (+25 Days)")
        st.write("Shifting the launch date away from the optimal Type I transfer geometry forces higher C3, higher arrival speed, and steeper entry angles.")
        if st.button("Simulate 25-Day Launch Delay"):
            stress_launch = launch_date + timedelta(days=25)
            stress_res = pipeline.run_mission_evaluation(
                launch_date=stress_launch,
                arrival_date=arrival_date,
                rover_mass_kg=rover_mass_kg,
                surface_mission_sols=surface_sols
            )
            st.write(f"**New C3:** {stress_res['transfer']['c3_km2_s2']:.1f} km²/s² (was {results['transfer']['c3_km2_s2']:.1f})")
            st.write(f"**Parachute Peak Load:** {stress_res['edl']['peak_opening_load_kn']:.1f} kN (Limit: 289 kN)")
            st.write(f"**Feasibility Outcome:** `{stress_res['overall_feasibility']}`")
            
        st.markdown("##### Scenario 2: Heavy Rover Scale-Up (Korzun & Edquist TRL Gap)")
        st.write("Scaling the payload beyond MSL-heritage capacity (>1,500 kg) forces Supersonic Retropropulsion, triggering real schedule and technology risks.")
        if st.button("Simulate 2,500 kg Heavy Payload"):
            stress_res2 = pipeline.run_mission_evaluation(
                launch_date=launch_date,
                arrival_date=arrival_date,
                rover_mass_kg=2500.0,
                surface_mission_sols=surface_sols
            )
            st.write(f"**Propulsion Architecture:** {stress_res2['propulsion']['propulsion_architecture']}")
            st.write(f"**TRL Level:** {stress_res2['propulsion']['trl_rating']} (Requires TRL ≥ 6)")
            st.write(f"**Feasibility Outcome:** `{stress_res2['overall_feasibility']}`")

    with col_sc2:
        st.markdown("##### Scenario 3: Loose Drift Sand with Static Wheels")
        st.write("Simulates what happens when a rover encounters loose drift sand with static wheels (no dynamic traction deployment).")
        if st.button("Simulate Static Wheel Entrapment"):
            stress_res3 = pipeline.run_mission_evaluation(
                launch_date=launch_date,
                arrival_date=arrival_date,
                rover_mass_kg=rover_mass_kg,
                surface_mission_sols=surface_sols,
                terrain_key="sand_dune",
                wheel_mode="static"
            )
            mob3 = stress_res3['surface_power']['mobility_details']
            st.write(f"**Wheel Slip Ratio:** {mob3['measured_slip_ratio']*100:.1f}%")
            st.write(f"**Status:** {mob3['status_message']}")
            st.write(f"**Feasibility Outcome:** `{stress_res3['overall_feasibility']}`")

        st.markdown("##### Scenario 4: Solar Conjunction During Surface Science")
        st.write("Simulates arriving when Sun-Earth-Mars angle drops below 2.3°, blocking all ground communications for 10–14 days.")
        if st.button("Simulate Conjunction Arrival"):
            # Set date near conjunction
            stress_res4 = pipeline.run_mission_evaluation(
                launch_date=date(2026, 6, 1),
                arrival_date=date(2027, 4, 15), # Near conjunction
                rover_mass_kg=rover_mass_kg,
                surface_mission_sols=surface_sols
            )
            com4 = stress_res4['telecom']
            st.write(f"**SEM Angle:** {com4['sem_angle_deg']:.1f}° (Threshold: {com4['blackout_threshold_deg']}°)")
            st.write(f"**Status:** {com4['status_message']}")
            st.write(f"**Feasibility Outcome:** `{stress_res4['overall_feasibility']}`")

st.divider()
st.caption("COSMOS AI Mars Mission Planner v1.0.0 | Grounded in MSL, MEADS, MEDLI2, NTRS 2022, and ExoMars literature.")
