import { useState } from "react";
import { X, Key, ChevronDown, Eye, EyeOff, Check } from "lucide-react";

const PROVIDERS = [
  { id: "openai", name: "OpenAI", models: ["gpt-5.2", "gpt-5.1", "gpt-4.1", "gpt-4o"], placeholder: "sk-...", color: "#10b981" },
  { id: "anthropic", name: "Anthropic", models: ["claude-4-sonnet-20250514", "claude-sonnet-4-5-20250929", "claude-haiku-4-5-20251001"], placeholder: "sk-ant-...", color: "#f59e0b" },
  { id: "gemini", name: "Google Gemini", models: ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-3-flash-preview"], placeholder: "AIza...", color: "#3b82f6" },
];

export const SettingsModal = ({
  apiKeys,
  provider,
  model,
  onApiKeysChange,
  onProviderChange,
  onModelChange,
  onClose,
}) => {
  const [localKeys, setLocalKeys] = useState(apiKeys || { openai: '', anthropic: '', gemini: '' });
  const [showKeys, setShowKeys] = useState({ openai: false, anthropic: false, gemini: false });
  const selectedProvider = PROVIDERS.find((p) => p.id === provider) || PROVIDERS[0];

  const handleSave = () => {
    onApiKeysChange(localKeys);
    onClose();
  };

  const handleKeyChange = (providerId, value) => {
    setLocalKeys(prev => ({ ...prev, [providerId]: value }));
  };

  const toggleShowKey = (providerId) => {
    setShowKeys(prev => ({ ...prev, [providerId]: !prev[providerId] }));
  };

  const handleProviderChange = (newProvider) => {
    onProviderChange(newProvider);
    const p = PROVIDERS.find((pr) => pr.id === newProvider);
    if (p) onModelChange(p.models[0]);
  };

  return (
    <div className="lf-modal-overlay" onClick={onClose} data-testid="settings-modal">
      <div className="lf-modal" onClick={(e) => e.stopPropagation()}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
          }}
        >
          <h3
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontWeight: 600,
              fontSize: "18px",
              color: "#f8fafc",
              margin: 0,
            }}
          >
            Settings
          </h3>
          <button className="lf-btn-ghost" onClick={onClose} data-testid="settings-close-btn">
            <X size={18} />
          </button>
        </div>

        {/* API Keys Section */}
        <div style={{ marginBottom: "20px" }}>
          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "13px",
              fontWeight: 500,
              color: "#e2e8f0",
              marginBottom: "8px",
            }}
          >
            <Key size={14} />
            API Keys
          </label>
          <p style={{ fontSize: "11px", color: "#64748b", margin: "0 0 12px 0" }}>
            Optional. Leave empty to use the default Emergent key. Add your own keys for unlimited usage.
          </p>
          
          {/* Individual Provider API Keys */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {PROVIDERS.map((p) => (
              <div key={p.id} style={{ 
                background: "#0f172a", 
                borderRadius: "8px", 
                padding: "12px",
                border: provider === p.id ? `1px solid ${p.color}` : "1px solid #1e293b",
                transition: "border-color 0.2s"
              }}>
                <div style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  justifyContent: "space-between",
                  marginBottom: "8px"
                }}>
                  <span style={{ 
                    fontSize: "12px", 
                    fontWeight: 600, 
                    color: p.color,
                    display: "flex",
                    alignItems: "center",
                    gap: "6px"
                  }}>
                    {p.name}
                    {localKeys[p.id] && (
                      <Check size={12} style={{ color: "#10b981" }} />
                    )}
                  </span>
                  {provider === p.id && (
                    <span style={{ 
                      fontSize: "9px", 
                      background: p.color, 
                      color: "#000",
                      padding: "2px 6px",
                      borderRadius: "4px",
                      fontWeight: 600
                    }}>
                      ACTIVE
                    </span>
                  )}
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <input
                    type={showKeys[p.id] ? "text" : "password"}
                    value={localKeys[p.id] || ''}
                    onChange={(e) => handleKeyChange(p.id, e.target.value)}
                    placeholder={p.placeholder}
                    style={{
                      flex: 1,
                      background: "#020617",
                      border: "1px solid #1e293b",
                      borderRadius: "6px",
                      padding: "8px 12px",
                      fontSize: "12px",
                      color: "#e2e8f0",
                      fontFamily: "'JetBrains Mono', monospace",
                      outline: "none",
                    }}
                    data-testid={`api-key-input-${p.id}`}
                  />
                  <button
                    className="lf-btn-ghost"
                    onClick={() => toggleShowKey(p.id)}
                    style={{ padding: "8px", minWidth: "36px" }}
                    title={showKeys[p.id] ? "Hide" : "Show"}
                  >
                    {showKeys[p.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Provider */}
        <div style={{ marginBottom: "20px" }}>
          <label
            style={{
              fontSize: "13px",
              fontWeight: 500,
              color: "#e2e8f0",
              marginBottom: "8px",
              display: "block",
            }}
          >
            AI Provider
          </label>
          <div style={{ display: "flex", gap: "8px" }}>
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                className={provider === p.id ? "lf-btn-primary" : "lf-btn-secondary"}
                onClick={() => handleProviderChange(p.id)}
                style={{ flex: 1, justifyContent: "center", fontSize: "12px", padding: "8px" }}
                data-testid={`provider-${p.id}`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>

        {/* Model */}
        <div style={{ marginBottom: "24px" }}>
          <label
            style={{
              fontSize: "13px",
              fontWeight: 500,
              color: "#e2e8f0",
              marginBottom: "8px",
              display: "block",
            }}
          >
            Model
          </label>
          <div style={{ position: "relative" }}>
            <select
              value={model}
              onChange={(e) => onModelChange(e.target.value)}
              style={{
                width: "100%",
                background: "#020617",
                border: "1px solid #1e293b",
                borderRadius: "6px",
                padding: "8px 32px 8px 12px",
                fontSize: "13px",
                color: "#e2e8f0",
                fontFamily: "'JetBrains Mono', monospace",
                outline: "none",
                appearance: "none",
                cursor: "pointer",
              }}
              data-testid="model-select"
            >
              {selectedProvider.models.map((m) => (
                <option key={m} value={m} style={{ background: "#020617" }}>
                  {m}
                </option>
              ))}
            </select>
            <ChevronDown
              size={14}
              style={{
                position: "absolute",
                right: "10px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "#64748b",
                pointerEvents: "none",
              }}
            />
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <button className="lf-btn-secondary" onClick={onClose} data-testid="settings-cancel-btn">
            Cancel
          </button>
          <button className="lf-btn-primary" onClick={handleSave} data-testid="settings-save-btn">
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
