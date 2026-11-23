"""
M2 - Day 2 Task
----------------
The core scam-language detector. Checks a piece of text (a transcript
line, or a full transcript) for three categories of red flags:

    1. OTP / sensitive-info requests   -> the single strongest signal
    2. Urgency language                -> "act now", "blocked", "immediately"
    3. Authority impersonation         -> "calling from RBI/bank/cybercrime"

This is deliberately RULE-BASED, not a trained ML model:
    - It's honest: you can explain exactly why any sentence was flagged
    - It's fast to build and needs no training data to "work"
    - It's genuinely how a first, real version of this feature should work

Later (Day 3), you can tune the word lists based on what your test
sentences reveal. That's the normal way this kind of system improves.
"""

import re

# ---- Red-flag word/phrase lists -------------------------------------------
# Add to these lists as you test and find gaps - this is the main thing
# you'll be tuning on Day 3.

OTP_PATTERNS = [
    r"\botp\b", r"\bone[\s-]?time password\b", r"\bpin\b", r"\bcvv\b",
    # next two: common speech-to-text mis-hearings of "OTP"
    r"\bo\.?\s?t\.?\s?p\b", r"\bopp\b",
    r"verification code", r"security code", r"six digit code",
    r"\bcode you (received|got)\b", r"share the code", r"read out the code",
    r"confirm the code", r"tell me the code",
    r"number on the back", r"card number", r"send the code",
    r"code that (came|was sent)", r"code (sent|received)",
]

# An OTP word alone is NOT a scam ("I got an OTP for my order").
# It only counts when someone is ASKING for it, so we also look for these.
REQUEST_PATTERN = (r"\b(share|tell|read|send|give|confirm|provide|say|need|"
                   r"enter|what is your|verify)\b")

URGENCY_PATTERNS = [
    r"\bblocked\b", r"\bimmediately\b", r"\burgent\b", r"\bact now\b",
    r"last chance", r"final warning", r"expires in", r"do not disconnect",
    r"do not hang up", r"right now", r"as soon as possible",
    r"suspended", r"deactivated", r"limited time",
    r"disconnected", r"\bhurry\b", r"only valid for", r"unless you",
    r"\bact fast\b", r"matter of urgency",
    r"verify now", r"stay on the line", r"in danger",
    r"within the next", r"has expired",
]

# NEW: scams that ask for money, bank details or a link click (no OTP needed)
MONEY_PATTERNS = [
    r"transfer the money", r"safe account", r"bank details",
    r"(click|using|open) (this|the) link", r"verification fee",
    r"processing fee", r"registration fee",
]

AUTHORITY_PATTERNS = [
    r"\brbi\b", r"cybercrime", r"income tax department", r"bank('s)? security",
    r"calling from your bank", r"calling on behalf of", r"legal case",
    r"kyc update", r"customs", r"\bkyc\b", r"fraud department",
    r"government benefit", r"this is (your|the) bank",
]


def _count_matches(text: str, patterns: list) -> list:
    text_lower = text.lower()
    found = []
    for pattern in patterns:
        if re.search(pattern, text_lower):
            found.append(pattern.replace(r"\b", "").strip())
    return found


def analyze_text(text: str) -> dict:
    """
    Takes a transcript (string) and returns a dict with:
        - flags found in each category
        - a risk level: Low / Medium / High
        - a plain-language reason list (for the dashboard)
    """
    otp_hits = _count_matches(text, OTP_PATTERNS)
    # only treat as an OTP REQUEST if a request word is also present
    if otp_hits and not re.search(REQUEST_PATTERN, text.lower()):
        otp_hits = []
    urgency_hits = _count_matches(text, URGENCY_PATTERNS)
    authority_hits = _count_matches(text, AUTHORITY_PATTERNS)
    money_hits = _count_matches(text, MONEY_PATTERNS)

    reasons = []
    if money_hits:
        reasons.append("Asks for money, bank details or a link click - a common scam tactic")
    if otp_hits:
        reasons.append("Requests a sensitive code (OTP/PIN/CVV) - legitimate banks never ask for this over a call")
    if urgency_hits:
        reasons.append("Uses urgency/pressure language to rush a decision")
    if authority_hits:
        reasons.append("Claims to be calling from a bank/government authority")

    # --- risk scoring logic ---
    # OTP request is the single strongest signal - weight it heavily
    score = len(otp_hits) * 3 + len(urgency_hits) * 1 + len(authority_hits) * 1 + len(money_hits) * 2

    if otp_hits:
        risk = "High"
    elif money_hits and (urgency_hits or authority_hits):
        risk = "High"   # money request + pressure/authority = very strong scam sign
    elif score >= 2:
        risk = "Medium"
    elif score == 1:
        risk = "Low"
    else:
        risk = "None"

    return {
        "text": text,
        "risk": risk,
        "score": score,
        "otp_flags": otp_hits,
        "urgency_flags": urgency_hits,
        "authority_flags": authority_hits,
        "money_flags": money_hits,
        "reasons": reasons,
    }


if __name__ == "__main__":
    # Quick manual test - run: python scam_classifier.py
    test_sentences = [
        "Please share the OTP you just received to confirm your identity.",
        "Hi, are we still meeting for lunch tomorrow?",
        "This is an urgent call from your bank's security department, please verify now.",
    ]
    for s in test_sentences:
        result = analyze_text(s)
        print(f"\nText: {s}")
        print(f"Risk: {result['risk']} (score={result['score']})")
        print(f"Reasons: {result['reasons']}")
