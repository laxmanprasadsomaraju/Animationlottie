import { useState, useCallback } from "react";
import "@/App.css";
import { Toaster, toast } from "sonner";
import { Toolbar } from "@/components/Toolbar";
import { PromptPanel } from "@/components/PromptPanel";
import { PreviewPanel } from "@/components/PreviewPanel";
import { SettingsModal } from "@/components/SettingsModal";
import { DownloadModal } from "@/components/DownloadModal";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [lottieJson, setLottieJson] = useState(null);
  const [currentPrompt, setCurrentPrompt] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showDownload, setShowDownload] = useState(false);
  const [apiKeys, setApiKeys] = useState({ openai: '', anthropic: '', gemini: '' });
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-5.2");
  const [animationName, setAnimationName] = useState("My Animation");

  const handleGenerate = useCallback(async (prompt) => {
    if (!prompt.trim()) {
      toast.error("Please enter a prompt");
      return;
    }
    setIsGenerating(true);
    setCurrentPrompt(prompt);
    try {
      const currentApiKey = apiKeys[provider] || undefined;
      const res = await axios.post(`${API}/generate`, {
        prompt: prompt.trim(),
        api_key: currentApiKey,
        provider,
        model,
      });
      if (res.data.success) {
        setLottieJson(res.data.lottie_json);
        setAnimationName(prompt.slice(0, 40));
        toast.success("Animation generated!");
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Generation failed";
      toast.error(msg);
    } finally {
      setIsGenerating(false);
    }
  }, [apiKeys, provider, model]);

  const handleEnhance = useCallback(async (enhancePrompt) => {
    if (!lottieJson) {
      toast.error("Generate an animation first");
      return;
    }
    if (!enhancePrompt.trim()) {
      toast.error("Enter enhancement details");
      return;
    }
    setIsEnhancing(true);
    try {
      const currentApiKey = apiKeys[provider] || undefined;
      const res = await axios.post(`${API}/enhance`, {
        lottie_json: lottieJson,
        prompt: enhancePrompt.trim(),
        api_key: currentApiKey,
        provider,
        model,
      });
      if (res.data.success) {
        setLottieJson(res.data.lottie_json);
        toast.success("Animation enhanced!");
      }
    } catch (err) {
      const msg = err.response?.data?.detail || "Enhancement failed";
      toast.error(msg);
    } finally {
      setIsEnhancing(false);
    }
  }, [lottieJson, apiKeys, provider, model]);

  const handleLoadTemplate = useCallback((template) => {
    setLottieJson(template.lottie_json);
    setAnimationName(template.name);
    setCurrentPrompt(template.description);
    toast.success(`Loaded template: ${template.name}`);
  }, []);

  const handleSave = useCallback(async () => {
    if (!lottieJson) return;
    try {
      await axios.post(`${API}/history`, {
        name: animationName,
        prompt: currentPrompt,
        lottie_json: lottieJson,
      });
      toast.success("Animation saved!");
    } catch {
      toast.error("Failed to save");
    }
  }, [lottieJson, animationName, currentPrompt]);

  const handleJsonEdit = useCallback((newJson) => {
    setLottieJson(newJson);
  }, []);

  return (
    <div data-testid="app-root" style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <Toaster
        position="top-right"
        toastOptions={{
          style: { background: "#1e293b", color: "#f8fafc", border: "1px solid #334155" },
        }}
      />
      <Toolbar
        onSettings={() => setShowSettings(true)}
        onDownload={() => setShowDownload(true)}
        onSave={handleSave}
        hasAnimation={!!lottieJson}
      />
      <div className="lf-studio">
        <PromptPanel
          onGenerate={handleGenerate}
          onEnhance={handleEnhance}
          onLoadTemplate={handleLoadTemplate}
          isGenerating={isGenerating}
          isEnhancing={isEnhancing}
          currentPrompt={currentPrompt}
        />
        <PreviewPanel
          lottieJson={lottieJson}
          onJsonEdit={handleJsonEdit}
          animationName={animationName}
        />
      </div>
      {showSettings && (
        <SettingsModal
          apiKey={apiKey}
          provider={provider}
          model={model}
          onApiKeyChange={setApiKey}
          onProviderChange={setProvider}
          onModelChange={setModel}
          onClose={() => setShowSettings(false)}
        />
      )}
      {showDownload && lottieJson && (
        <DownloadModal
          lottieJson={lottieJson}
          animationName={animationName}
          onClose={() => setShowDownload(false)}
        />
      )}
    </div>
  );
}

export default App;
