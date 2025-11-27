import streamlit as st

st.set_page_config(page_title="GPU SHOWDOWN", page_icon="🎮")

st.title("🎮 GPU SHOWDOWN")
st.write("Pick a GPU, use case, and resolution to estimate performance and value.")


def compute_gpu_setup(brand_choice, model_choice, use_choice, res_choice):
    # --------------------- BRAND + MODEL ---------------------
    if brand_choice == "NVIDIA":
        brand = "NVIDIA"
        driver = "Excellent driver stability (NVIDIA)."

        if model_choice == "RTX 4060 ($350)":
            model = "RTX 4060"
            price = 350
            base_fps = 120
        elif model_choice == "RTX 4070 ($600)":
            model = "RTX 4070"
            price = 600
            base_fps = 160
        elif model_choice == "RTX 4080 ($1200)":
            model = "RTX 4080"
            price = 1200
            base_fps = 200
        else:
            raise ValueError("Invalid NVIDIA model selected.")

    elif brand_choice == "AMD":
        brand = "AMD"
        driver = "Good drivers, improving quickly (AMD)."

        if model_choice == "RX 7600 ($350)":
            model = "RX 7600"
            price = 350
            base_fps = 115
        elif model_choice == "RX 7700 XT ($500)":
            model = "RX 7700 XT"
            price = 500
            base_fps = 155
        elif model_choice == "RX 7900 XT ($950)":
            model = "RX 7900 XT"
            price = 950
            base_fps = 195
        else:
            raise ValueError("Invalid AMD model selected.")
    else:
        raise ValueError("Invalid brand selected.")

    # ------------------ USE CASE ------------------
    if use_choice == "Gaming":
        use = "Gaming"
        use_mult = 1.0
    elif use_choice == "Rendering":
        use = "Rendering"
        use_mult = 0.85
    elif use_choice == "General Use":
        use = "General Use"
        use_mult = 0.60
    else:
        raise ValueError("Invalid use case.")

    # ------------------ RESOLUTION ------------------
    if res_choice == "1080p":
        resolution = "1080p"
        res_mult = 1.2
    elif res_choice == "1440p":
        resolution = "1440p"
        res_mult = 1.0
    elif res_choice == "4K":
        resolution = "4K"
        res_mult = 0.7
    else:
        raise ValueError("Invalid resolution.")

    # ------------------ FPS CALCULATION ------------------
    final_fps = int(base_fps * use_mult * res_mult)

    # ------------------ PERFORMANCE VERDICT ------------------
    if final_fps >= 140:
        perf_verdict = "Amazing performance! Great for high refresh-rate gaming."
    elif final_fps >= 90:
        perf_verdict = "Excellent performance. Smooth for all modern games."
    elif final_fps >= 60:
        perf_verdict = "Playable performance. Might need to lower settings."
    else:
        perf_verdict = "Low performance. Consider lowering resolution or upgrading."

    # ------------------ PRICE VERDICT ------------------
    if price <= 350:
        price_verdict = "Great budget value!"
    elif price >= 1000:
        price_verdict = "Premium high-end GPU for serious users."
    else:
        price_verdict = "Mid-range pricing with balanced value."

    # Bundle everything into a dict
    return {
        "brand": brand,
        "model": model,
        "price": price,
        "use": use,
        "resolution": resolution,
        "driver": driver,
        "final_fps": final_fps,
        "perf_verdict": perf_verdict,
        "price_verdict": price_verdict,
    }


# ------------- GUI CONTROLS -------------

st.subheader("Step 1: Choose a GPU brand")

brand_choice = st.selectbox("Brand", ["NVIDIA", "AMD"])

st.subheader("Step 2: Choose a specific model")

if brand_choice == "NVIDIA":
    model_choice = st.selectbox(
        "NVIDIA Models",
        [
            "RTX 4060 ($350)",
            "RTX 4070 ($600)",
            "RTX 4080 ($1200)",
        ],
    )
else:
    model_choice = st.selectbox(
        "AMD Models",
        [
            "RX 7600 ($350)",
            "RX 7700 XT ($500)",
            "RX 7900 XT ($950)",
        ],
    )

st.subheader("Step 3: Choose your main use case")

use_choice = st.selectbox(
    "Use Case",
    [
        "Gaming",
        "Rendering",
        "General Use",
    ],
)

st.subheader("Step 4: Choose resolution")

res_choice = st.selectbox(
    "Resolution",
    [
        "1080p",
        "1440p",
        "4K",
    ],
)

st.markdown("---")

if st.button("🔍 Calculate Performance"):
    result = compute_gpu_setup(
        brand_choice=brand_choice,
        model_choice=model_choice,
        use_choice=use_choice,
        res_choice=res_choice,
    )

    st.subheader("Results")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Brand:** {result['brand']}")
        st.write(f"**Model:** {result['model']}")
        st.write(f"**Price:** ${result['price']}")
        st.write(f"**Use Case:** {result['use']}")
        st.write(f"**Resolution:** {result['resolution']}")

    with col2:
        st.write(f"**Driver Quality:** {result['driver']}")
        st.write(f"**Estimated FPS:** `{result['final_fps']} fps`")

    st.markdown("---")
    st.subheader("Verdict")
    st.write(f"**Performance:** {result['perf_verdict']}")
    st.write(f"**Value:** {result['price_verdict']}")
else:
    st.info("Set your options above, then click **Calculate Performance**.")

