import { useState, useRef, useCallback } from "react";
import Lottie from "lottie-react";
import { Play, Pause, RotateCcw, Code2, Eye, Copy, Check } from "lucide-react";

export const PreviewPanel = ({ lottieJson, onJsonEdit, animationName }) => {
  const [viewMode, setViewMode] = useState("preview");
  const [isPlaying, setIsPlaying] = useState(true);
  const [copied, setCopied] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const lottieRef = useRef(null);

  const handleTogglePlay = () => {
    if (!lottieRef.current) return;
    if (isPlaying) {
      lottieRef.current.pause();
    } else {
      lottieRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    if (!lottieRef.current) return;
    lottieRef.current.goToAndPlay(0);
    setIsPlaying(true);
  };

  const handleCopyJson = useCallback(() => {
    if (!lottieJson) return;
    navigator.clipboard.writeText(JSON.stringify(lottieJson, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [lottieJson]);

  const handleJsonChange = (e) => {
    setJsonText(e.target.value);
  };

  const handleApplyJson = () => {
    try {
      const parsed = JSON.parse(jsonText);
      onJsonEdit(parsed);
    } catch {
      // invalid JSON, ignore
    }
  };

  const switchToCode = () => {
    setViewMode("code");
    if (lottieJson) {
      setJsonText(JSON.stringify(lottieJson, null, 2));
    }
  };

  const syntaxHighlight = (json) => {
    if (!json) return "";
    const str = typeof json === "string" ? json : JSON.stringify(json, null, 2);
    return str.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
      (match) => {
        let cls = "json-number";
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = "json-key";
          } else {
            cls = "json-string";
          }
        } else if (/true|false/.test(match)) {
          cls = "json-boolean";
        } else if (/null/.test(match)) {
          cls = "json-null";
        }
        return `<span class="${cls}">${match}</span>`;
      }
    );
  };

  return (
    <div className="lf-panel-right" data-testid="preview-panel">
      {/* View Toggle */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 16px",
          borderBottom: "1px solid #1e293b",
        }}
      >
        <div style={{ display: "flex", gap: "4px" }}>
          <button
            className={`lf-tab ${viewMode === "preview" ? "active" : ""}`}
            onClick={() => setViewMode("preview")}
            data-testid="view-preview-btn"
          >
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Eye size={14} />
              Preview
            </span>
          </button>
          <button
            className={`lf-tab ${viewMode === "code" ? "active" : ""}`}
            onClick={switchToCode}
            data-testid="view-code-btn"
          >
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Code2 size={14} />
              JSON
            </span>
          </button>
        </div>
        {lottieJson && (
          <button
            className="lf-btn-ghost"
            onClick={handleCopyJson}
            data-testid="copy-json-btn"
          >
            {copied ? <Check size={14} style={{ color: "#10b981" }} /> : <Copy size={14} />}
            <span style={{ fontSize: "12px" }}>{copied ? "Copied!" : "Copy"}</span>
          </button>
        )}
      </div>

      {/* Preview Mode */}
      {viewMode === "preview" && (
        <div className="lf-preview-container pattern-grid" data-testid="lottie-preview">
          {lottieJson ? (
            <div className="lf-preview-canvas animate-fade-in">
              <Lottie
                lottieRef={lottieRef}
                animationData={lottieJson}
                loop={true}
                autoplay={true}
                style={{ width: "100%", height: "100%" }}
              />
            </div>
          ) : (
            <div
              style={{
                textAlign: "center",
                color: "#475569",
                padding: "40px",
              }}
            >
              <div
                style={{
                  width: "80px",
                  height: "80px",
                  margin: "0 auto 20px",
                  borderRadius: "50%",
                  border: "2px dashed #334155",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <Play size={28} style={{ color: "#334155", marginLeft: "4px" }} />
              </div>
              <p
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontWeight: 500,
                  fontSize: "16px",
                  color: "#64748b",
                  margin: "0 0 8px 0",
                }}
              >
                Your animation will appear here
              </p>
              <p style={{ fontSize: "12px", color: "#475569", margin: 0 }}>
                Write a prompt or pick a template to get started
              </p>
            </div>
          )}
        </div>
      )}

      {/* Code Mode */}
      {viewMode === "code" && (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          {lottieJson ? (
            <>
              <textarea
                className="lf-code-view"
                value={jsonText}
                onChange={handleJsonChange}
                spellCheck={false}
                data-testid="json-editor"
                style={{
                  flex: 1,
                  resize: "none",
                  border: "none",
                  outline: "none",
                  padding: "16px",
                }}
              />
              <div
                style={{
                  padding: "8px 16px",
                  borderTop: "1px solid #1e293b",
                  display: "flex",
                  justifyContent: "flex-end",
                  gap: "8px",
                }}
              >
                <button
                  className="lf-btn-secondary"
                  onClick={handleApplyJson}
                  data-testid="apply-json-btn"
                >
                  Apply Changes
                </button>
              </div>
            </>
          ) : (
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#475569",
                fontSize: "13px",
              }}
            >
              No animation JSON to display
            </div>
          )}
        </div>
      )}

      {/* Playback Controls */}
      {lottieJson && viewMode === "preview" && (
        <div className="lf-playback-bar" data-testid="playback-controls">
          <button
            className="lf-btn-ghost"
            onClick={handleTogglePlay}
            data-testid="play-pause-btn"
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          </button>
          <button
            className="lf-btn-ghost"
            onClick={handleRestart}
            data-testid="restart-btn"
          >
            <RotateCcw size={16} />
          </button>
          <div style={{ flex: 1 }} />
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "11px",
              color: "#64748b",
            }}
          >
            {animationName}
          </span>
        </div>
      )}
    </div>
  );
};
