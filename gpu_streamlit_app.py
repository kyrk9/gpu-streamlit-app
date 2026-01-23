import streamlit as st
import sqlite3

# ✅ IMPORTANT: use the actual SQLite DB file you uploaded (likely pcparts.db)
conn = sqlite3.connect("pcparts.db", check_same_thread=False)
conn.row_factory = sqlite3.Row


def load_table(table_name: str):
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM "{table_name}"')
    return cur.fetchall()


def pick_row_by_label(rows, label: str):
    # rows: list[sqlite3.Row] that include 'name' and 'price'
    # label format: "NAME ($PRICE)"
    for r in rows:
        if f"{r['name']} (${r['price']})" == label:
            return r
    return None


st.set_page_config(page_title="PC Builder")

st.title("PC Builder")
st.write("Pick Your Parts for Your PC build.")





# =========================
# 🧩 PC BUILDER (DATABASE)
# =========================
st.markdown("---")
st.header("🧩 PC Builder (Compatibility Check)")
st.write("Select parts from the database and check hardware compatibility.")

# Load tables (MATCHING YOUR EXACT TABLE NAMES)
cpus = load_table("CPU")
motherboards = load_table("MOTHERBOARD")
rams = load_table("RAM")
gpus = load_table("GPU")
psus = load_table("PSU")
cases = load_table("CASE")

def pick_row(rows, label):
    for r in rows:
        if f"{r['name']} (${r['price']})" == label:
            return r
    return None

# Dropdowns
cpu_label = st.selectbox(
    "CPU",
    [f"{r['name']} (${r['price']})" for r in cpus]
)

mobo_label = st.selectbox(
    "Motherboard",
    [f"{r['name']} (${r['price']})" for r in motherboards]
)

ram_label = st.selectbox(
    "RAM",
    [f"{r['name']} (${r['price']})" for r in rams]
)

gpu_label = st.selectbox(
    "GPU",
    [f"{r['name']} (${r['price']})" for r in gpus]
)

psu_label = st.selectbox(
    "PSU",
    [f"{r['name']} (${r['price']})" for r in psus]
)

case_label = st.selectbox(
    "Case",
    [f"{r['name']} (${r['price']})" for r in cases]
)

if st.button("✅ Check Compatibility"):
    cpu = pick_row(cpus, cpu_label)
    mobo = pick_row(motherboards, mobo_label)
    ram = pick_row(rams, ram_label)
    gpu = pick_row(gpus, gpu_label)
    psu = pick_row(psus, psu_label)
    case = pick_row(cases, case_label)

    errors = []
    warnings = []
    passes = []

    # CPU ↔ Motherboard socket
    if cpu["socket"] != mobo["socket"]:
        errors.append(f"CPU socket ({cpu['socket']}) does not match motherboard socket ({mobo['socket']}).")
    else:
        passes.append("CPU socket matches motherboard.")

    # RAM type ↔ Motherboard
    if ram["ram_type"] != mobo["ram_type"]:
        errors.append(f"RAM type ({ram['ram_type']}) does not match motherboard ({mobo['ram_type']}).")
    else:
        passes.append("RAM type matches motherboard.")

    # Case form factor
    ff = mobo["form_factor"]
    if ff == "ATX" and case["supports_atx"] != 1:
        errors.append("Case does not support ATX motherboards.")
    elif ff == "mATX" and case["supports_matx"] != 1:
        errors.append("Case does not support mATX motherboards.")
    elif ff == "ITX" and case["supports_itx"] != 1:
        errors.append("Case does not support ITX motherboards.")
    else:
        passes.append("Case supports motherboard form factor.")

    # PSU headroom check
    estimated = cpu["tdp_w"] + gpu["power_w"] + 150
    if psu["watts"] < estimated:
        warnings.append(f"PSU may be underpowered ({psu['watts']}W vs ~{estimated}W needed).")
    else:
        passes.append("PSU wattage is sufficient.")

    # RAM size warning
    if ram["size_gb"] < 16:
        warnings.append("RAM is under 16GB (recommended minimum).")
    else:
        passes.append("RAM capacity is sufficient.")

    # Total price
    total_price = sum([
        cpu["price"],
        mobo["price"],
        ram["price"],
        gpu["price"],
        psu["price"],
        case["price"],
    ])

    st.subheader("Build Summary")
    st.write(f"**Total Price:** ${total_price}")

    st.subheader("Compatibility Report")

    if errors:
        st.error("❌ Incompatible configuration:")
        for e in errors:
            st.write(f"- {e}")
    else:
        st.success("✅ No critical incompatibilities found.")

    if warnings:
        st.warning("⚠️ Warnings:")
        for w in warnings:
            st.write(f"- {w}")

    if passes:
        st.info("✅ Passed checks:")
        for p in passes:
            st.write(f"- {p}")



