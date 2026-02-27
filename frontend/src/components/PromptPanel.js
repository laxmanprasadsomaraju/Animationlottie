import { useState, useEffect } from "react";
import { Send, Sparkles, Clock, LayoutGrid, Wand2 } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SUGGESTIONS = [
  "A pulsing neon heart",
  "Loading spinner with morphing shapes",
  "Bouncing ball with trail effect",
  "Rotating 3D cube wireframe",
  "Animated check mark success",
  "Wave animation for music player",
  "Typing indicator dots",
  "Floating particles background",
  "Rocket launch animation",
  "Glowing progress ring",
];

export const PromptPanel = ({
  onGenerate,
  onEnhance,
  onLoadTemplate,
  isGenerating,
  isEnhancing,
  currentPrompt,
}) => {
  const [prompt, setPrompt] = useState("");
  const [enhancePrompt, setEnhancePrompt] = useState("");
  const [activeTab, setActiveTab] = useState("create");
  const [templates, setTemplates] = useState([]);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchTemplates();
    fetchHistory();
  }, []);

  const fetchTemplates = async () => {
    try {
      const res = await axios.get(`${API}/templates`);
      setTemplates(res.data);
    } catch (err) {
      console.error("Failed to load templates:", err);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API}/history`);
      setHistory(res.data);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onGenerate(prompt);
  };

  const handleEnhanceSubmit = (e) => {
    e.preventDefault();
    onEnhance(enhancePrompt);
    setEnhancePrompt("");
  };

  return (
    <div className="lf-panel-left" data-testid="prompt-panel">
      {/* Tabs */}
      <div
        style={{
          display: "flex",
          borderBottom: "1px solid #1e293b",
          padding: "0 20px",
          gap: "4px",
        }}
      >
        <button
          className={`lf-tab ${activeTab === "create" ? "active" : ""}`}
          onClick={() => setActiveTab("create")}
          data-testid="tab-create"
        >
          <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Sparkles size={14} />
            Create
          </span>
        </button>
        <button
          className={`lf-tab ${activeTab === "templates" ? "active" : ""}`}
          onClick={() => setActiveTab("templates")}
          data-testid="tab-templates"
        >
          <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <LayoutGrid size={14} />
            Templates
          </span>
        </button>
        <button
          className={`lf-tab ${activeTab === "history" ? "active" : ""}`}
          onClick={() => { setActiveTab("history"); fetchHistory(); }}
          data-testid="tab-history"
        >
          <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Clock size={14} />
            History
          </span>
        </button>
      </div>

      {/* Create Tab */}
      {activeTab === "create" && (
        <div className="lf-prompt-area">
          <div>
            <label
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 600,
                fontSize: "15px",
                color: "#e2e8f0",
                marginBottom: "8px",
                display: "block",
              }}
            >
              Describe your animation
            </label>
            <p
              style={{
                fontSize: "12px",
                color: "#64748b",
                margin: "0 0 12px 0",
                lineHeight: "1.5",
              }}
            >
              Be specific about shapes, colors, motion, and timing for best results.
            </p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <textarea
              className="lf-textarea"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. A blue circle that pulses smoothly, with a glowing ring expanding outward..."
              rows={5}
              data-testid="prompt-input"
            />
            <button
              type="submit"
              className="lf-btn-primary"
              disabled={isGenerating || !prompt.trim()}
              data-testid="generate-btn"
              style={{ width: "100%", justifyContent: "center" }}
            >
              {isGenerating ? (
                <>
                  <div className="lf-spinner" />
                  Generating...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Generate Animation
                </>
              )}
            </button>
          </form>

          {/* Suggestions */}
          <div>
            <p
              style={{
                fontSize: "11px",
                color: "#64748b",
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                fontFamily: "'JetBrains Mono', monospace",
                margin: "0 0 10px 0",
              }}
            >
              Quick ideas
            </p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  className="lf-chip"
                  onClick={() => setPrompt(s)}
                  data-testid={`suggestion-${s.slice(0, 10).toLowerCase().replace(/\s/g, "-")}`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Enhance section */}
          {currentPrompt && (
            <div
              style={{
                marginTop: "auto",
                borderTop: "1px solid #1e293b",
                paddingTop: "16px",
              }}
            >
              <label
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontWeight: 500,
                  fontSize: "13px",
                  color: "#94a3b8",
                  marginBottom: "8px",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <Wand2 size={14} style={{ color: "#ec4899" }} />
                Enhance current animation
              </label>
              <form onSubmit={handleEnhanceSubmit} className="lf-enhance-bar" style={{ padding: 0, border: "none", background: "none" }}>
                <input
                  className="lf-enhance-input"
                  value={enhancePrompt}
                  onChange={(e) => setEnhancePrompt(e.target.value)}
                  placeholder="Add glow effect, change color to red..."
                  data-testid="enhance-input"
                />
                <button
                  type="submit"
                  className="lf-btn-secondary"
                  disabled={isEnhancing}
                  data-testid="enhance-btn"
                >
                  {isEnhancing ? <div className="lf-spinner" /> : <Wand2 size={14} />}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === "templates" && (
        <div style={{ padding: "20px", overflow: "auto", flex: 1 }}>
          <p
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 600,
              fontSize: "15px",
              color: "#e2e8f0",
              margin: "0 0 4px 0",
            }}
          >
            Starter Templates
          </p>
          <p style={{ fontSize: "12px", color: "#64748b", margin: "0 0 16px 0" }}>
            Click a template to load it, then enhance with prompts.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {templates.map((t) => (
              <div
                key={t.id}
                className="lf-template-card"
                onClick={() => onLoadTemplate(t)}
                data-testid={`template-${t.id}`}
              >
                <div
                  style={{
                    width: "100%",
                    aspectRatio: "1",
                    background: "#020617",
                    borderRadius: "6px",
                    marginBottom: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                  }}
                >
                  <TemplatePreview lottie={t.lottie_json} />
                </div>
                <p
                  style={{
                    fontSize: "13px",
                    fontWeight: 600,
                    color: "#e2e8f0",
                    margin: "0 0 2px 0",
                  }}
                >
                  {t.name}
                </p>
                <p style={{ fontSize: "11px", color: "#64748b", margin: 0 }}>
                  {t.category}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === "history" && (
        <div style={{ padding: "20px", overflow: "auto", flex: 1 }}>
          <p
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 600,
              fontSize: "15px",
              color: "#e2e8f0",
              margin: "0 0 16px 0",
            }}
          >
            Saved Animations
          </p>
          {history.length === 0 ? (
            <div
              style={{
                textAlign: "center",
                padding: "40px 20px",
                color: "#64748b",
                fontSize: "13px",
              }}
            >
              <Clock size={32} style={{ margin: "0 auto 12px", opacity: 0.3 }} />
              <p>No saved animations yet.</p>
              <p style={{ fontSize: "12px" }}>Generate and save animations to see them here.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {history.map((h) => (
                <div
                  key={h.id}
                  className="lf-template-card"
                  onClick={() => onLoadTemplate({ ...h, lottie_json: h.lottie_json })}
                  data-testid={`history-${h.id}`}
                >
                  <p style={{ fontSize: "13px", fontWeight: 600, color: "#e2e8f0", margin: "0 0 4px 0" }}>
                    {h.name}
                  </p>
                  <p style={{ fontSize: "11px", color: "#64748b", margin: 0 }}>
                    {h.prompt?.slice(0, 60) || "No prompt"}
                  </p>
                  <p style={{ fontSize: "10px", color: "#475569", margin: "4px 0 0 0", fontFamily: "'JetBrains Mono', monospace" }}>
                    {new Date(h.created_at).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const TemplatePreview = ({ lottie }) => {
  try {
    const LottieReact = require("lottie-react").default;
    return (
      <LottieReact
        animationData={lottie}
        loop={true}
        autoplay={true}
        style={{ width: "80%", height: "80%" }}
      />
    );
  } catch {
    return <div style={{ color: "#475569", fontSize: "12px" }}>Preview</div>;
  }
};
