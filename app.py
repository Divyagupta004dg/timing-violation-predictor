import streamlit as st
import subprocess
import os

st.title("ML Timing Violation Predictor")

uploaded = st.file_uploader("Upload RTL (.v)", type=["v"])

clock = st.number_input("Clock Period (ns)", value=10.0)
input_delay = st.number_input("Input Delay (ns)", value=0.5)
output_delay = st.number_input("Output Delay (ns)", value=0.5)

if uploaded:
    st.success("RTL Uploaded")
    module = uploaded.name.replace(".v", "")

    if st.button("Predict"):
        temp = "temp.v"
        with open(temp, "wb") as f:
            f.write(uploaded.read())

        result = subprocess.run(
            [
                "python3",
                "ml/predict_user_design.py",
                temp,
                module,
                str(clock),
                str(input_delay),
                str(output_delay)
            ],
            capture_output=True,
            text=True
        )

        st.code(result.stdout)
        if result.stderr:
            st.error("Error occurred:")
            st.code(result.stderr)
        if "TIMING PASS" in result.stdout:
            st.success("✅ TIMING PASS")
        if "TIMING VIOLATED" in result.stdout:
            st.error("❌ TIMING VIOLATED")

        st.subheader("Live Timing Sweep — This Design")
        live_plot = f"ml/live_{module}_sweep.png"
        if os.path.exists(live_plot):
            st.image(live_plot, caption=f"WNS vs Clock Period — {module}")

        st.subheader("Model Visualizations")

        if os.path.exists("ml/feature_importance.png"):
            st.image("ml/feature_importance.png", caption="Feature Importance")
        if os.path.exists("ml/confusion_matrix.png"):
            st.image("ml/confusion_matrix.png", caption="Confusion Matrix")
        if os.path.exists("ml/model_comparison.png"):
            st.image("ml/model_comparison.png", caption="Model Comparison")
        if os.path.exists("ml/violation_heatmap.png"):
            st.image("ml/violation_heatmap.png", caption="Violation Heatmap")
