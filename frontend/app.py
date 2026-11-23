import streamlit as st
import requests


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="EchoGuard",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #0e1117;
    }

    .main-title {
        font-size: 46px;
        font-weight: 800;
        color: white;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 18px;
        color: #a8b3c7;
        margin-bottom: 30px;
    }

    .upload-title {
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 10px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 700;
        color: white;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .risk-high {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        background-color: #ffe9ec;
        color: #b71c1c;
        border: 2px solid #ff4b5c;
        margin-top: 15px;
    }

    .risk-medium {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        background-color: #fff3cd;
        color: #a85d00;
        border: 2px solid #ffb300;
        margin-top: 15px;
    }

    .risk-low {
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: 800;
        background-color: #e8f5e9;
        color: #1b5e20;
        border: 2px solid #66bb6a;
        margin-top: 15px;
    }

    .transcript-box {
        background-color: #19324d;
        padding: 18px;
        border-radius: 10px;
        color: #d8e9ff;
        font-size: 17px;
        line-height: 1.6;
        margin-top: 10px;
    }

    .risk-indicator {
        background-color: #3d4210;
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin-top: 10px;
        border-left: 4px solid #ffc107;
    }

    .footer {
        text-align: center;
        color: #737b8c;
        margin-top: 40px;
        padding: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🛡️ EchoGuard")

    st.write(
        "AI-powered scam voice detection system."
    )

    st.caption(
        "Academic prototype for AI-assisted "
        "scam-call analysis."
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🛡️ EchoGuard</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Scam Voice Detection & Risk Analysis'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# AUDIO UPLOAD
# ============================================================

st.markdown(
    '<div class="upload-title">🎙️ Upload Call Recording</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Choose an audio file",
    type=["wav", "mp3", "m4a", "ogg"]
)


# ============================================================
# ANALYSIS
# ============================================================

if uploaded_file is not None:

    col1, col2 = st.columns([2, 1])

    with col1:
        st.audio(uploaded_file)

    with col2:

        st.write("**File name**")
        st.write(uploaded_file.name)

        st.write("**File size**")
        st.write(
            f"{uploaded_file.size / 1024:.2f} KB"
        )

    if st.button(
        "🔍 Analyze Audio",
        use_container_width=True
    ):

        with st.spinner(
            "EchoGuard AI is analyzing the audio..."
        ):

            try:

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type
                    )
                }

                response = requests.post(
                    "http://127.0.0.1:8000/analyze-audio",
                    files=files,
                    timeout=300
                )

                # ====================================================
                # BACKEND RESPONSE
                # ====================================================

                if response.status_code != 200:

                    st.error(
                        f"Backend error: {response.status_code}"
                    )

                    st.code(response.text)

                    st.stop()

                result = response.json()

                # ====================================================
                # DEBUG SAFETY
                # ====================================================

                if "error" in result:

                    st.error(
                        result.get(
                            "error",
                            "Unknown backend error"
                        )
                    )

                    if "details" in result:
                        st.code(
                            str(result["details"])
                        )

                    st.stop()

                # ====================================================
                # GET VALUES SAFELY
                # ====================================================

                voice_score = result.get(
                    "m1_voice_score",
                    result.get(
                        "voice_score",
                        result.get(
                            "m1",
                            0
                        )
                    )
                )

                risk_score = result.get(
                    "final_risk_score",
                    result.get(
                        "risk_score",
                        result.get(
                            "score",
                            0
                        )
                    )
                )

                risk_level = result.get(
                    "final_risk_level",
                    result.get(
                        "risk_level",
                        result.get(
                            "risk",
                            "UNKNOWN"
                        )
                    )
                )

                language = result.get(
                    "language",
                    "en"
                )

                transcript = result.get(
                    "transcript",
                    "No transcript available."
                )

                reasons = result.get(
                    "reasons",
                    []
                )

                # ====================================================
                # NORMALIZE SCORES
                # ====================================================

                voice_score = float(voice_score)

                risk_score = float(risk_score)

                # M2 may return 0-10, but final score should be 0-1
                if risk_score > 1:
                    risk_score = risk_score / 10

                # ====================================================
                # SUCCESS
                # ====================================================

                st.success(
                    "✅ Analysis completed successfully!"
                )

                # ====================================================
                # SUMMARY
                # ====================================================

                st.markdown(
                    '<div class="section-title">'
                    '📊 Analysis Summary'
                    '</div>',
                    unsafe_allow_html=True
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Voice Score",
                        f"{voice_score:.2f}"
                    )

                with col2:
                    st.metric(
                        "Risk Score",
                        f"{risk_score:.2f}"
                    )

                with col3:
                    st.metric(
                        "Language",
                        language.upper()
                    )

                # ====================================================
                # RISK SCORE
                # ====================================================

                st.markdown(
                    '<div class="section-title">'
                    'Risk Score'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.progress(
                    min(
                        max(
                            risk_score,
                            0.0
                        ),
                        1.0
                    )
                )

                st.caption(
                    f"Overall risk score: "
                    f"{risk_score:.2f} / 1.00"
                )

                # ====================================================
                # RISK LEVEL
                # ====================================================

                risk_level = str(
                    risk_level
                ).upper()

                if risk_level == "HIGH":

                    st.markdown(
                        '<div class="risk-high">'
                        '🔴 HIGH RISK'
                        '</div>',
                        unsafe_allow_html=True
                    )

                elif risk_level == "MEDIUM":

                    st.markdown(
                        '<div class="risk-medium">'
                        '🟠 MEDIUM RISK'
                        '</div>',
                        unsafe_allow_html=True
                    )

                else:

                    st.markdown(
                        '<div class="risk-low">'
                        '🟢 LOW RISK'
                        '</div>',
                        unsafe_allow_html=True
                    )

                # ====================================================
                # TRANSCRIPT
                # ====================================================

                st.markdown(
                    '<div class="section-title">'
                    '📝 Transcript'
                    '</div>',
                    unsafe_allow_html=True
                )

                st.markdown(
                    f'<div class="transcript-box">'
                    f'{transcript}'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # ====================================================
                # RISK INDICATORS
                # ====================================================

                st.markdown(
                    '<div class="section-title">'
                    '⚠️ Why was this flagged?'
                    '</div>',
                    unsafe_allow_html=True
                )

                if reasons:

                    for reason in reasons:

                        st.markdown(
                            f'<div class="risk-indicator">'
                            f'⚠️ &nbsp; {reason}'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                else:

                    st.success(
                        "✅ No specific scam indicators detected."
                    )

                # ====================================================
                # TECHNICAL DETAILS
                # ====================================================

                with st.expander(
                    "🔧 Technical Analysis Details"
                ):

                    st.write(
                        "**M1 Voice Label:**",
                        result.get(
                            "m1_label",
                            "N/A"
                        )
                    )

                    st.write(
                        "**M1 Voice Score:**",
                        voice_score
                    )

                    st.write(
                        "**M2 Scam Score:**",
                        result.get(
                            "m2_score",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Final Risk Score:**",
                        risk_score
                    )

                    st.write(
                        "**Final Risk Level:**",
                        risk_level
                    )

                    st.write(
                        "**Language:**",
                        language
                    )

                    st.write(
                        "**Processing Time:**",
                        f"{result.get('processing_time_seconds', 'N/A')} seconds"
                    )

            except requests.exceptions.Timeout:

                st.error(
                    "⏱️ Analysis timed out. "
                    "The backend took too long to respond."
                )

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Cannot connect to EchoGuard backend. "
                    "Please make sure FastAPI is running on port 8000."
                )

            except Exception as e:

                st.error(
                    "❌ Frontend error"
                )

                st.code(
                    str(e)
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    '<div class="footer">'
    '🛡️ EchoGuard — AI-Powered Scam Voice Detection'
    '<br>'
    'Academic Final Year Project Prototype'
    '</div>',
    unsafe_allow_html=True
)






