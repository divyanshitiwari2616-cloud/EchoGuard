import json
import os
import subprocess
import sys
import requests


# ============================================================
# Paths
# ============================================================

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BACKEND_DIR)

M1_DIR = os.path.join(PROJECT_DIR, "m1")
M2_DIR = os.path.join(PROJECT_DIR, "m2")

M1_PYTHON = os.path.join(M1_DIR, "m1_venv", "Scripts", "python.exe")
M2_PYTHON = os.path.join(M2_DIR, "m2_venv", "Scripts", "python.exe")

M1_SCRIPT = os.path.join(M1_DIR, "predict.py")
M2_SCRIPT = os.path.join(M2_DIR, "transcribe_and_analyze.py")

M3_URL = "http://127.0.0.1:8000/analyze-combined"


# ============================================================
# Run M1
# ============================================================

def run_m1(audio_path):

    print("\n[M1] Running voice authenticity analysis...")

    process = subprocess.run(
        [
            M1_PYTHON,
            M1_SCRIPT
        ],
        input=audio_path + "\n",
        text=True,
        capture_output=True
    )

    print(process.stdout)

    if process.returncode != 0:
        print("[M1 ERROR]")
        print(process.stderr)
        return None

    # Find the M1 prediction line
    for line in process.stdout.splitlines():

        if line.startswith("{'score':"):

            result = line.replace("'", '"')
            return json.loads(result)

    print("[M1 ERROR] Could not find prediction.")
    return None


# ============================================================
# Run M2
# ============================================================


def run_m2(audio_path):

    import time

    print("\n[M2] Running Whisper + scam analysis...")

    start = time.perf_counter()

    process = subprocess.run(
        [
            M2_PYTHON,
            M2_SCRIPT,
            audio_path
        ],
        text=True,
        capture_output=True
    )

    elapsed = time.perf_counter() - start

    print(f"[M2] Processing time: {elapsed:.2f} seconds")

    if process.returncode != 0:
        print("[M2 ERROR]")
        print(process.stderr)
        return None

    try:
        result = json.loads(process.stdout)

        if "error" in result:
            print("[M2 ERROR]", result["error"])
            return None

        return {
            "risk": result.get("risk", "Low"),
            "score": result.get("score", 0),
            "reasons": result.get("reasons", []),
            "transcript": result.get("transcript", ""),
            "language": result.get("language", "")
        }

    except json.JSONDecodeError:
        print("[M2 ERROR] Invalid JSON output")
        print(process.stdout)
        return None
# ============================================================
# Send M1 + M2 to M3
# ============================================================

def send_to_m3(m1_result, m2_result):

    print("\n[M3] Sending real M1 + M2 results...")

    # M2 currently produces a rule-based raw score.
    # For now, normalize it to a 0-1 value.
    #
    # This is only an integration mapping.
    # We can tune the scoring later.

    m2_score = min(m2_result["score"] / 10.0, 1.0)

    payload = {
        "m1_voice_score": m1_result["score"],
        "m2_result": {
            "risk": m2_result["risk"],
            "score": m2_score,
            "reasons": m2_result["reasons"],
            "transcript": m2_result["transcript"],
            "language": m2_result["language"]
        }
    }

    response = requests.post(
        M3_URL,
        json=payload,
        timeout=30
    )

    print("\n[M3] HTTP Status:", response.status_code)

    try:
        print(json.dumps(response.json(), indent=4))
    except Exception:
        print(response.text)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print("==========================================")
    print("       SENTINELCALL ORCHESTRATOR")
    print("==========================================")

    audio_path = input(
        "\nEnter audio file path: "
    ).strip().strip('"')

    if not os.path.exists(audio_path):

        print("\nERROR: Audio file not found:")
        print(audio_path)

        sys.exit(1)

    m1_result = run_m1(audio_path)

    if not m1_result:
        sys.exit(1)

    m2_result = run_m2(audio_path)

    if not m2_result:
        sys.exit(1)

    send_to_m3(
        m1_result,
        m2_result
    )