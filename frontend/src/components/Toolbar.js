import { Settings, Download, Save, Zap } from "lucide-react";

export const Toolbar = ({ onSettings, onDownload, onSave, hasAnimation }) => {
  return (
    <div className="lf-toolbar" data-testid="toolbar">
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Zap size={22} style={{ color: "#3b82f6" }} />
          <span
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 700,
              fontSize: "18px",
              color: "#f8fafc",
              letterSpacing: "-0.02em",
            }}
          >
            LottieFlow
          </span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "10px",
              color: "#64748b",
              background: "#1e293b",
              padding: "2px 8px",
              borderRadius: "4px",
              textTransform: "uppercase",
              letterSpacing: "0.1em",
            }}
          >
            Studio
          </span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        {hasAnimation && (
          <>
            <button
              className="lf-btn-ghost"
              onClick={onSave}
              data-testid="save-btn"
              title="Save to history"
            >
              <Save size={16} />
              <span>Save</span>
            </button>
            <button
              className="lf-btn-secondary"
              onClick={onDownload}
              data-testid="download-btn"
              title="Download animation"
            >
              <Download size={16} />
              <span>Export</span>
            </button>
          </>
        )}
        <button
          className="lf-btn-ghost"
          onClick={onSettings}
          data-testid="settings-btn"
          title="Settings"
        >
          <Settings size={16} />
        </button>
      </div>
    </div>
  );
};
