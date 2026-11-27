
import { useRef, useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  const handleFile = (selectedFile) => {
    if (!selectedFile) return;

    const valid =
      selectedFile.type.startsWith("audio/") ||
      /\.(wav|mp3|m4a|ogg|webm|flac)$/i.test(selectedFile.name);

    if (valid) {
      setFile(selectedFile);
      setResult(null);
      setError("");
    } else {
      setError("Please select a valid audio file.");
    }
  };

  const formatSize = (size) => {
    return size < 1024 * 1024
      ? `${(size / 1024).toFixed(1)} KB`
      : `${(size / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatScore = (score) => {
    if (score === null || score === undefined || score === "") {
      return "N/A";
    }

    const value = Number(score);
    if (Number.isNaN(value)) return score;

    return `${(value * 100).toFixed(1)}%`;
  };

  const analyzeAudio = async () => {
    if (!file) return;

    setAnalyzing(true);
    setResult(null);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/analyze-audio", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || data.error || "Audio analysis failed."
        );
      }

      if (data.error) {
        throw new Error(data.error);
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to EchoGuard's analysis service."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  const riskClass = (level) => {
    const normalized = String(level || "").toLowerCase();

    if (normalized.includes("high")) return "high";
    if (normalized.includes("medium")) return "medium";
    if (normalized.includes("low")) return "low";

    return "neutral";
  };

  const riskDescription = (level) => {
    const normalized = String(level || "").toLowerCase();

    if (normalized.includes("high")) {
      return "Strong warning signals detected. Treat this recording with caution.";
    }

    if (normalized.includes("medium")) {
      return "Some warning signals detected. Review the recording carefully.";
    }

    if (normalized.includes("low")) {
      return "Fewer warning signals detected. Stay cautious nonetheless.";
    }

    return "The analysis could not determine a clear risk level.";
  };

  const riskValue = result
    ? Math.min(
        100,
        Math.max(
          0,
          Number(result.final_risk_score || 0) * 100
        )
      )
    : 0;

  return (
    <div className="app-shell">
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M12 3L19 6V11C19 16 15.8 19.5 12 21C8.2 19.5 5 16 5 11V6L12 3Z" />
              <path d="M9 12H10.5L12 9L13.5 15L15 12H16" />
            </svg>
          </div>
          <span>EchoGuard</span>
        </div>

        <div className="nav-right">
          <span className="status-dot"></span>
          <span className="status-text">System ready</span>
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="eyebrow">
            <span className="eyebrow-line"></span>
            AUDIO INTELLIGENCE
          </div>

          <h1>
            A closer look at
            <br />
            <span>the voice you hear.</span>
          </h1>

          <p className="hero-description">
            Analyze voice authenticity and identify potential scam signals
            with AI-powered audio analysis.
          </p>
        </section>

        <section className="upload-section">
          <div className="section-heading">
            <div>
              <h2>Audio analysis</h2>
              <p>Upload a recording to begin your analysis.</p>
            </div>
            <span className="step-label">01 / INPUT</span>
          </div>

          <div
            className={`upload-box ${dragging ? "dragging" : ""} ${
              file ? "has-file" : ""
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              handleFile(e.dataTransfer.files[0]);
            }}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".wav,.mp3,.m4a,.ogg,.webm,.flac,audio/*"
              hidden
              onChange={(e) => handleFile(e.target.files[0])}
            />

            {!file ? (
              <>
                <div className="upload-icon">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M12 16V4" />
                    <path d="M7 9L12 4L17 9" />
                    <path d="M4 16V19C4 20 5 21 6 21H18C19 20 20 20 20 19V16" />
                  </svg>
                </div>

                <h3>Drop your audio here</h3>
                <p>
                  or{" "}
                  <button
                    className="browse-button"
                    onClick={() => inputRef.current?.click()}
                  >
                    browse files
                  </button>
                </p>

                <div className="file-types">
                  WAV <span>·</span> MP3 <span>·</span> M4A <span>·</span>{" "}
                  OGG
                </div>
              </>
            ) : (
              <div className="file-preview">
                <div className="file-icon">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M4 9V15M8 5V19M12 8V16M16 3V21M20 9V15" />
                  </svg>
                </div>

                <div className="file-info">
                  <h3>{file.name}</h3>
                  <p>{formatSize(file.size)}</p>
                </div>

                <button
                  className="remove-file"
                  onClick={() => {
                    setFile(null);
                    setResult(null);
                    setError("");
                    if (inputRef.current) inputRef.current.value = "";
                  }}
                  title="Remove file"
                >
                  ×
                </button>
              </div>
            )}
          </div>

          {file && (
            <div className="audio-preview">
              <audio controls src={URL.createObjectURL(file)} />
            </div>
          )}

          <button
            className="analyze-button"
            disabled={!file || analyzing}
            onClick={analyzeAudio}
          >
            <span>
              {analyzing ? "Analyzing recording..." : "Analyze recording"}
            </span>

            {!analyzing && (
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
              >
                <path d="M5 12H19" />
                <path d="M13 6L19 12L13 18" />
              </svg>
            )}
          </button>

          {analyzing && (
            <div className="loading-message">
              <span className="loading-spinner"></span>
              <p>
                Examining voice patterns and analyzing audio content.
                This may take a little while.
              </p>
            </div>
          )}

          {error && (
            <div className="error-message">
              <strong>Analysis error</strong>
              <p>{error}</p>
            </div>
          )}

          <p className="privacy-note">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            >
              <path d="M12 3L19 6V11C19 16 15.8 19.5 12 21C8.2 19.5 5 16 5 11V6L12 3Z" />
            </svg>
            Audio analysis is intended as an aid, not definitive proof.
          </p>
        </section>

        {result && (
          <section className="results-section">
            <div className="section-heading">
              <div>
                <h2>Analysis report</h2>
                <p>Results from your audio recording.</p>
              </div>
              <span className="step-label">02 / RESULTS</span>
            </div>

            {/* Overall risk panel */}
            <div className={`risk-banner ${riskClass(result.final_risk_level)}`}>
              <div className="risk-main">
                <span className="result-label">OVERALL RISK</span>

                <h2>{result.final_risk_level || "Unavailable"}</h2>

                <p className="risk-description">
                  {riskDescription(result.final_risk_level)}
                </p>

                <div className="risk-meter">
                  <div className="risk-meter-labels">
                    <span>Risk indicator</span>
                    <span>{riskValue.toFixed(1)}%</span>
                  </div>

                  <div className="risk-meter-track">
                    <div
                      className={`risk-meter-fill ${riskClass(
                        result.final_risk_level
                      )}`}
                      style={{ width: `${riskValue}%` }}
                    ></div>
                  </div>

                  <div className="risk-meter-scale">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                  </div>
                </div>
              </div>

              <div className="risk-score-circle">
                <div className="risk-score-inner">
                  <strong>{riskValue.toFixed(0)}%</strong>
                  <span>Risk score</span>
                </div>
              </div>
            </div>

            {/* Model results */}
            <div className="result-grid">
              <article className="result-card">
                <span className="result-label">VOICE AUTHENTICITY · M1</span>
                <h3>{result.m1_label || "Unavailable"}</h3>
                <p>Fake score: {formatScore(result.m1_voice_score)}</p>
              </article>

              <article className="result-card">
                <span className="result-label">SCAM ANALYSIS · M2</span>
                <h3>{formatScore(result.m2_score)}</h3>
                <p>Content risk score</p>
              </article>
            </div>

            {/* Transcript */}
            <div className="report-block">
              <h3>Transcript</h3>

              <p className="transcript">
                {result.transcript || "No transcript available."}
              </p>

              {result.language && (
                <p className="report-meta">
                  Detected language: {result.language}
                </p>
              )}
            </div>

            {/* Insights */}
            <div className="report-block">
              <h3>Analysis insights</h3>

              {Array.isArray(result.reasons) &&
              result.reasons.length > 0 ? (
                <ul className="reasons-list">
                  {result.reasons.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ul>
              ) : (
                <p>No additional indicators were returned.</p>
              )}
            </div>

            {/* Processing details */}
            <div className="report-block processing-block">
              <h3>Processing information</h3>

              <div className="processing-row">
                <span>File</span>
                <span>{result.filename || file?.name}</span>
              </div>

              <div className="processing-row">
                <span>Processing time</span>
                <span>
                  {result.processing_time !== undefined
                    ? `${result.processing_time} seconds`
                    : result.total_time !== undefined
                      ? `${result.total_time} seconds`
                      : "Not provided"}
                </span>
              </div>
            </div>

            <p className="disclaimer-result">
              AI predictions may be inaccurate. A risk score is not proof of
              fraud or voice manipulation.
            </p>
          </section>
        )}

        {/* Modules */}
        <section className="modules-section">
          <div className="section-heading">
            <div>
              <h2>What we examine</h2>
              <p>Two complementary layers of analysis.</p>
            </div>
          </div>

          <div className="modules-grid">
            <article className="module">
              <div className="module-top">
                <span className="module-number">01</span>
                <div className="module-symbol">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M4 10V14M8 6V18M12 3V21M16 7V17M20 10V14" />
                  </svg>
                </div>
              </div>

              <h3>Voice authenticity</h3>

              <p>
                Examines acoustic characteristics to estimate whether a voice
                may be genuine or synthetically generated.
              </p>

              <span className="module-tag">LFCC · SVM</span>
            </article>

            <article className="module">
              <div className="module-top">
                <span className="module-number">02</span>
                <div className="module-symbol">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  >
                    <path d="M5 4H19V17H9L5 21V4Z" />
                    <path d="M8 8H16M8 12H14" />
                  </svg>
                </div>
              </div>

              <h3>Content intelligence</h3>

              <p>
                Transcribes speech and examines language for patterns that
                could indicate scam-related activity.
              </p>

              <span className="module-tag">Whisper · NLP</span>
            </article>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="disclaimer">
          <span className="disclaimer-mark">i</span>
          <p>
            AI predictions can be inaccurate. EchoGuard should not be used as
            the sole basis for making security-related decisions.
          </p>
        </section>
      </main>

      <footer className="footer">
        <span>EchoGuard</span>
        <span>Voice intelligence, with caution.</span>
      </footer>
    </div>
  );
}

export default App;
