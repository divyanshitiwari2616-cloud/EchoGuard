def calculate_risk(
    voice_score,
    language_score,
    urgency=False,
    authority=False,
    otp_request=False
):

    # Calculate combined risk score
    final_score = (
        0.6 * voice_score +
        0.4 * language_score
    )

    # Determine risk level
    if final_score >= 0.70:
        risk_level = "HIGH"

    elif final_score >= 0.40:
        risk_level = "MEDIUM"

    else:
        risk_level = "LOW"

    # Generate explanations
    reasons = []

    if voice_score >= 0.70:
        reasons.append("Possible AI-generated voice")

    if urgency:
        reasons.append("Urgent language detected")

    if authority:
        reasons.append("Possible authority impersonation")

    if otp_request:
        reasons.append("OTP/PIN request detected")

    return {
        "voice_score": voice_score,
        "language_score": language_score,
        "risk_score": round(final_score, 2),
        "risk_level": risk_level,
        "reasons": reasons
    }