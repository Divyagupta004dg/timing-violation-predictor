import streamlit as st
import subprocess
import tempfile

st.title("ML Timing Violation Predictor")

uploaded=st.file_uploader(
"Upload RTL (.v)",
type=["v"]
)

clock=st.number_input(
"Clock Period (ns)",
value=10.0
)

if uploaded:

    st.success("RTL Uploaded")

    module=uploaded.name.replace(".v","")

    if st.button("Predict"):

        temp="temp.v"

        with open(
            temp,
            "wb"
        ) as f:

            f.write(
                uploaded.read()
            )

        result=subprocess.run(

            [
                "python3",
                "ml/predict_user_design.py",
                temp,
                module,
                str(clock)

            ],

            capture_output=True,
            text=True

        )

        st.code(
            result.stdout
        )
        import os

        if "TIMING PASS" in result.stdout:
            st.success("✅ TIMING PASS")

        if "TIMING VIOLATED" in result.stdout:
            st.error("❌ TIMING VIOLATED")

        st.subheader("Model Visualizations")

        if os.path.exists("ml/feature_importance.png"):
            st.image(
                "ml/feature_importance.png",
                caption="Feature Importance"
            )

        if os.path.exists("ml/confusion_matrix.png"):
            st.image(
                "ml/confusion_matrix.png",
                caption="Confusion Matrix"
            )

        if os.path.exists("ml/model_comparison.png"):
            st.image(
                "ml/model_comparison.png",
                caption="Model Comparison"
            )

        if os.path.exists("ml/violation_heatmap.png"):
            st.image(
                "ml/violation_heatmap.png",
                caption="Violation Heatmap"
            )
