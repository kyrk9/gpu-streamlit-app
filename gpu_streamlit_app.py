import streamlit as st
import sqlite3
import itertools
from typing import List, Optional, Tuple

# =========================
# CONFIG + STYLE
# =========================
st.set_page_config(
    page_title="PC Builder | Prebuilt Finder",
    page_icon="🧩",
    layout="wide",
)

st.markdown(
    """
<style>
/* overall page width + spacing */
.block-container {
    padding-top: 2rem;
    max-width: 1150px;
}

/* smoother typography */
h1, h2, h3 {
    letter-spacing: 0.2px;
}

/* soften default widgets */
div[data-baseweb="select"] > div {
    border-radius: 14px !important;
}
button[kind="primary"] {
    border-radius: 14px !important;
}

/* card-like containers (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.03);
}

/* nicer sidebar */
section[data-testid="stSidebar"] {
    border-right: 1px solid rgba(255,255,255,0.10);
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================
# DB CONNECTION
# =========================
DB_FILE = "pcparts.db"

@st.cache_resource
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def load_table(table_name: str) -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    return cur.fetchall()

def safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default

# =========================
# COMPATIBILITY + SCORING
# =========================
def is_compatible(cpu, mobo, ram, gpu, psu, case) -> bool:
    # Hard fails
    if cpu["socket"] != mobo["socket"]:
        return False
    if ram["ram_type"] != mobo["ram_type"]:
        return False

    ff = mobo["form_factor"]  # ATX / mATX / ITX (must match your DB)
    if ff == "ATX" and safe_int(case["supports_atx"]) != 1:
        return False
    if ff == "mATX" and safe_int(case["supports_matx"]) != 1:
        return False
    if ff == "ITX" and safe_int(case["supports_itx"]) != 1:
        return False

    return True

def estimate_wattage(cpu, gpu) -> int:
    # simple + defensible estimate
    return safe_int(cpu["tdp_w"]) + safe_int(gpu["power_w"]) + 150

def build_warnings(cpu, ram, gpu, psu) -> List[str]:
    warnings = []

    # PSU headroom
    needed = estimate_wattage(cpu, gpu)
    psu_w = safe_int(psu["watts"])
    if psu_w < needed:
        warnings.append(f"PSU may be underpowered: {psu_w}W vs ~{needed}W needed.")
    elif psu_w - needed < 100:
        warnings.append(f"Low PSU headroom: ~{needed}W needed, PSU is {psu_w}W.")

    # RAM capacity
    if safe_int(ram["size_gb"]) < 16:
        warnings.append("RAM is under 16GB (recommended minimum for modern usage).")

    return warnings

def score_build(cpu, mobo, ram, gpu, psu, case, total_price: int) -> float:
    """
    Heuristic scoring (no FPS):
    - reward GPU power (proxy for higher tier)
    - reward RAM size
    - reward PSU headroom
    - small reward for newer-ish platforms (AM5, DDR5) if you want it
    - penalty for price so it doesn't always max out
    """
    gpu_power = safe_int(gpu["power_w"])
    ram_gb = safe_int(ram["size_gb"])
    needed = estimate_wattage(cpu, gpu)
    headroom = max(0, safe_int(psu["watts"]) - needed)

    score = 0.0
    score += gpu_power * 2.0
    score += ram_gb * 12.0
    score += headroom * 0.25

    # Optional small platform preference (keeps it simple)
    if mobo["ram_type"] == "DDR5":
        score += 40
    if cpu["socket"] == "AM5":
        score += 25

    score -= total_price * 0.55
    return score

def recommend_best_build(
    budget: int,
    cpus: List[sqlite3.Row],
    mobos: List[sqlite3.Row],
    rams: List[sqlite3.Row],
    gpus: List[sqlite3.Row],
    psus: List[sqlite3.Row],
    cases: List[sqlite3.Row],
    prefer_brand: str = "Any",
    min_ram_gb: int = 16,
) -> Optional[Tuple]:
    best = None
    best_score = float("-inf")

    # Filter RAM upfront (faster)
    rams_filtered = [r for r in rams if safe_int(r["size_gb"]) >= min_ram_gb]

    # Filter GPU by preference
    if prefer_brand != "Any":
        gpus_filtered = [g for g in gpus if str(g.get("brand", "")).strip().upper() == prefer_brand.upper()]
        # If your GPU table doesn't have a "brand" column, this will filter to empty.
        # So if empty, fall back to all GPUs.
        if len(gpus_filtered) == 0:
            gpus_filtered = gpus
    else:
        gpus_filtered = gpus

    # Brute force all combos (OK for small DB)
    for cpu, mobo, ram, gpu, psu, case in itertools.product(cpus, mobos, rams_filtered, gpus_filtered, psus, cases):
        if not is_compatible(cpu, mobo, ram, gpu, psu, case):
            continue

        total = (
            safe_int(cpu["price"])
            + safe_int(mobo["price"])
            + safe_int(ram["price"])
            + safe_int(gpu["price"])
            + safe_int(psu["price"])
            + safe_int(case["price"])
        )
        if total > budget:
            continue

        s = score_build(cpu, mobo, ram, gpu, psu, case, total)
        if s > best_score:
            best_score = s
            best = (cpu, mobo, ram, gpu, psu, case, total, best_score)

    return best

# =========================
# LOAD DB DATA (with friendly errors)
# =========================
st.title("🧩 PC Builder — Prebuilt Finder")
st.write("Pick a budget in the sidebar. The app generates the best compatible build from your database.")

try:
    cpus = load_table("CPU")
    mobos = load_table("MOTHERBOARD")
    rams = load_table("RAM")
    gpus = load_table("GPU")
    psus = load_table("PSU")
    cases = load_table('"CASE"')
except Exception as e:
    st.error("Database load failed. Check that `pcparts.db` is in the repo and table names match exactly.")
    st.code(str(e))
    st.stop()

if not (cpus and mobos and rams and gpus and psus and cases):
    st.warning("One or more tables are empty. Add records in DB Browser (then Write Changes), re-upload pcparts.db, and refresh.")
    st.stop()

# =========================
# SIDEBAR (ONLY PREBUILT CONTROLS)
# =========================
with st.sidebar:
    st.header("💸 Prebuilt Controls")

    budget = st.slider("Budget ($)", min_value=400, max_value=4000, value=1200, step=50)

    min_ram_gb = st.selectbox("Minimum RAM", [8, 16, 32, 64], index=1)

    prefer_brand = st.radio("Preferred GPU brand", ["Any", "NVIDIA", "AMD"], horizontal=False)

    st.divider()

    run = st.button("✨ Generate Best Build", use_container_width=True)

# Auto-generate on first load too
if "has_run" not in st.session_state:
    st.session_state["has_run"] = True
    run = True

# =========================
# MAIN OUTPUT
# =========================
if run:
    best = recommend_best_build(
        budget=budget,
        cpus=cpus,
        mobos=mobos,
        rams=rams,
        gpus=gpus,
        psus=psus,
        cases=cases,
        prefer_brand=prefer_brand,
        min_ram_gb=min_ram_gb,
    )

    if best is None:
        st.error("No compatible build found under this budget.")
        st.write("Fix options:")
        st.write("- Increase the budget")
        st.write("- Add more parts to your database")
        st.write("- Ensure sockets/RAM types/form factors match across parts")
        st.stop()

    cpu, mobo, ram, gpu, psu, case, total, score = best
    needed = estimate_wattage(cpu, gpu)
    headroom = safe_int(psu["watts"]) - needed
    warnings = build_warnings(cpu, ram, gpu, psu)

    # Top metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Price", f"${total}")
    c2.metric("Estimated Power Need", f"{needed}W")
    c3.metric("PSU Headroom", f"{headroom}W")
    c4.metric("RAM", f"{ram['size_gb']}GB {ram['ram_type']}")

    st.divider()

    # Build card
    with st.container(border=True):
        st.subheader("✅ Recommended Build (from your database)")
        left, right = st.columns([1.2, 0.8])

        with left:
            st.write(f"**CPU:** {cpu['name']}  —  ${cpu['price']}  ·  Socket: `{cpu['socket']}`")
            st.write(f"**Motherboard:** {mobo['name']}  —  ${mobo['price']}  ·  Socket: `{mobo['socket']}` · RAM: `{mobo['ram_type']}` · Form: `{mobo['form_factor']}`")
            st.write(f"**RAM:** {ram['name']}  —  ${ram['price']}  ·  `{ram['ram_type']}` · {ram['size_gb']}GB")
            # GPU brand might not exist; guard it
            gpu_brand = gpu["brand"]
            st.write(f"**GPU:** {gpu_brand} {gpu['name']}  —  ${gpu['price']}  ·  Power: ~{gpu['power_w']}W")
            st.write(f"**PSU:** {psu['name']}  —  ${psu['price']}  ·  {psu['watts']}W")
            st.write(f"**Case:** {case['name']}  —  ${case['price']}")

        with right:
            st.markdown("#### Compatibility")
            st.success("CPU socket matches motherboard")
            st.success("RAM type matches motherboard")
            st.success("Case supports motherboard form factor")

            if warnings:
                st.markdown("#### Notes")
                for w in warnings:
                    st.warning(w)
            else:
                st.info("No warnings for this build.")

    # Export summary
    summary = f"""PC Builder — Prebuilt Finder

Budget: ${budget}
Total Price: ${total}

CPU: {cpu['name']} (${cpu['price']}) | socket={cpu['socket']} | tdp={cpu['tdp_w']}W
Motherboard: {mobo['name']} (${mobo['price']}) | socket={mobo['socket']} | ram={mobo['ram_type']} | form={mobo['form_factor']}
RAM: {ram['name']} (${ram['price']}) | type={ram['ram_type']} | size={ram['size_gb']}GB
GPU: {gpu.get('brand','')} {gpu['name']} (${gpu['price']}) | power={gpu['power_w']}W
PSU: {psu['name']} (${psu['price']}) | watts={psu['watts']}W
Case: {case['name']} (${case['price']})

Estimated power need: ~{needed}W
PSU headroom: {headroom}W

Warnings:
- {"; ".join(warnings) if warnings else "None"}
"""
    st.download_button(
        "⬇️ Download Build Summary (TXT)",
        data=summary,
        file_name="prebuilt_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )

else:
    st.info("Use the sidebar to set a budget, then click **Generate Best Build**.")





