
import os
import json
import time
import subprocess
import ast

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EchoGuard Backend",
    description="AI-powered scam call detection backend",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)
UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

M1_PYTHON = os.path.join(
    BASE_DIR, "m1", "m1_venv", "Scripts", "python.exe"
)

M1_SCRIPT = os.path.join(
    BASE_DIR, "m1", "predict.py"
)

M2_PYTHON = os.path.join(
    BASE_DIR, "m2", "m2_venv", "Scripts", "python.exe"
)

M2_SCRIPT = os.path.join(
    BASE_DIR, "m2", "transcribe_and_analyze.py"
)


@app.get("/")
def root():
    return {
        "message": "EchoGuard Backend Running",
        "status": "active"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):

    try:
        filename = os.path.basename(file.filename)

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        data = await file.read()

        with open(file_path, "wb") as f:
            f.write(data)

        return {
            "message": "Audio uploaded successfully",
            "filename": filename,
            "path": file_path
        }

    except Exception as e:
        return {
            "error": "Upload failed",
            "details": str(e)
        }


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):

    start_time = time.time()

    try:

        # --------------------------------------------------
        # SAVE AUDIO
        # --------------------------------------------------

        filename = os.path.basename(file.filename)

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        data = await file.read()

        with open(file_path, "wb") as f:
            f.write(data)

        print(
            f"Audio saved: {file_path}",
            flush=True
        )


        # --------------------------------------------------
        # CHECK M1
        # --------------------------------------------------

        if not os.path.exists(M1_PYTHON):
            return {
                "error": "M1 Python environment not found",
                "path": M1_PYTHON
            }

        if not os.path.exists(M1_SCRIPT):
            return {
                "error": "M1 script not found",
                "path": M1_SCRIPT
            }


        # --------------------------------------------------
        # CHECK M2
        # --------------------------------------------------

        if not os.path.exists(M2_PYTHON):
            return {
                "error": "M2 Python environment not found",
                "path": M2_PYTHON
            }

        if not os.path.exists(M2_SCRIPT):
            return {
                "error": "M2 script not found",
                "path": M2_SCRIPT
            }


        # ==================================================
        # M1
        # ==================================================

        print("Running M1...", flush=True)

        m1_start = time.time()

        m1_process = subprocess.run(
            [
                M1_PYTHON,
                M1_SCRIPT
            ],
            input=file_path + "\n",
            text=True,
            capture_output=True
        )

        m1_time = time.time() - m1_start

        print(
            f"M1 completed in {m1_time:.2f}s",
            flush=True
        )

        print(
            "M1 stdout:",
            repr(m1_process.stdout),
            flush=True
        )

        print(
            "M1 stderr:",
            repr(m1_process.stderr),
            flush=True
        )


        if m1_process.returncode != 0:
            return {
                "error": "M1 analysis failed",
                "details": m1_process.stderr,
                "raw_output": m1_process.stdout
            }


        # --------------------------------------------------
        # PARSE M1
        # --------------------------------------------------

        m1_output = m1_process.stdout.strip()

        m1_result = None

        for line in reversed(m1_output.splitlines()):

            line = line.strip()

            if (
                line.startswith("{")
                and
                line.endswith("}")
            ):

                try:
                    m1_result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass

                try:
                    m1_result = ast.literal_eval(line)

                    if isinstance(m1_result, dict):
                        break

                except Exception:
                    pass


        if m1_result is None:
            return {
                "error": "M1 returned invalid result",
                "raw_output": m1_output,
                "stderr": m1_process.stderr
            }


        m1_score = m1_result.get("score")

        m1_label = m1_result.get(
            "label",
            "unknown"
        )


        if m1_score is None:
            return {
                "error": "M1 returned no score",
                "m1_result": m1_result
            }


        m1_score = float(m1_score)

        m1_score = min(
            max(m1_score, 0.0),
            1.0
        )


        # ==================================================
        # M2
        # ==================================================

        print("Running M2...", flush=True)

        m2_start = time.time()

        m2_process = subprocess.run(
            [
                M2_PYTHON,
                M2_SCRIPT,
                file_path
            ],
            text=True,
            capture_output=True
        )

        m2_time = time.time() - m2_start

        print(
            f"M2 completed in {m2_time:.2f}s",
            flush=True
        )

        print(
            "M2 stdout:",
            repr(m2_process.stdout),
            flush=True
        )

        print(
            "M2 stderr:",
            repr(m2_process.stderr),
            flush=True
        )


        if m2_process.returncode != 0:
            return {
                "error": "M2 analysis failed",
                "details": m2_process.stderr,
                "raw_output": m2_process.stdout
            }


        # --------------------------------------------------
        # PARSE M2
        # --------------------------------------------------

        m2_output = m2_process.stdout.strip()

        m2_result = None

        for line in reversed(m2_output.splitlines()):

            line = line.strip()

            if (
                line.startswith("{")
                and
                line.endswith("}")
            ):

                try:
                    m2_result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass


        if m2_result is None:
            return {
                "error": "M2 returned invalid JSON",
                "type": "JSONDecodeError",
                "raw_output": m2_output,
                "stderr": m2_process.stderr
            }


        if "error" in m2_result:
            return {
                "error": "M2 analysis failed",
                "details": m2_result["error"]
            }


        # ==================================================
        # NORMALIZE M2 SCORE
        # ==================================================

        m2_score = float(
            m2_result.get(
                "score",
                0
            )
        )

        if m2_score > 1:
            m2_score = m2_score / 10.0

        m2_score = min(
            max(m2_score, 0.0),
            1.0
        )


        # ==================================================
        # M3 RISK ENGINE
        # ==================================================

        final_score = (
            (m1_score * 0.40)
            +
            (m2_score * 0.60)
        )

        final_score = round(
            final_score,
            2
        )


        if final_score >= 0.70:
            risk_level = "HIGH"

        elif final_score >= 0.40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"


        # ==================================================
        # REASONS
        # ==================================================

        reasons = list(
            m2_result.get(
                "reasons",
                []
            )
        )


        if m1_score >= 0.70:

            reasons.append(
                "Voice characteristics indicate "
                "possible synthetic or cloned audio"
            )


        # ==================================================
        # FINAL RESULT
        # ==================================================

        processing_time = (
            time.time()
            - start_time
        )


        result = {
            "message": "Audio analysis completed",

            "processing_time_seconds": round(
                processing_time,
                2
            ),

            "m1_time_seconds": round(
                m1_time,
                2
            ),

            "m2_time_seconds": round(
                m2_time,
                2
            ),

            "filename": filename,

            "m1_voice_score": round(
                m1_score,
                4
            ),

            "m1_label": m1_label,

            "m2_score": round(
                m2_score,
                2
            ),

            "final_risk_score": final_score,

            "final_risk_level": risk_level,

            "reasons": reasons,

            "transcript": m2_result.get(
                "transcript",
                ""
            ),

            "language": m2_result.get(
                "language",
                "unknown"
            )
        }


        print(
            "Final result:",
            json.dumps(result),
            flush=True
        )


        return result


    except Exception as e:

        print(
            "INTERNAL ERROR:",
            repr(e),
            flush=True
        )

        return {
            "error": "Internal analysis error",
            "type": type(e).__name__,
            "details": str(e)
        }


@app.post("/analyze-combined")
async def analyze_combined(data: dict):

    try:

        m1_score = float(
            data.get(
                "m1_voice_score",
                0
            )
        )

        m2_result = data.get(
            "m2_result",
            {}
        )

        m2_score = float(
            m2_result.get(
                "score",
                0
            )
        )


        if m2_score > 1:
            m2_score = m2_score / 10.0


        m2_score = min(
            max(m2_score, 0.0),
            1.0
        )


        final_score = (
            (m1_score * 0.40)
            +
            (m2_score * 0.60)
        )

        final_score = round(
            final_score,
            2
        )


        if final_score >= 0.70:
            risk_level = "HIGH"

        elif final_score >= 0.40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"


        reasons = list(
            m2_result.get(
                "reasons",
                []
            )
        )


        if m1_score >= 0.70:

            reasons.append(
                "Voice characteristics indicate "
                "possible synthetic or cloned audio"
            )


        return {
            "m1_voice_score": round(
                m1_score,
                4
            ),

            "m2_score": round(
                m2_score,
                2
            ),

            "final_risk_score": final_score,

            "final_risk_level": risk_level,

            "reasons": reasons,

            "transcript": m2_result.get(
                "transcript",
                ""
            ),

            "language": m2_result.get(
                "language",
                "unknown"
            )
        }


    except Exception as e:

        return {
            "error": "Risk analysis failed",
            "type": type(e).__name__,
            "details": str(e)
        }
