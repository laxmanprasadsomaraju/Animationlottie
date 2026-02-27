import { useState, useRef, useCallback } from "react";
import Lottie from "lottie-react";
import { X, FileJson, Code2, Image, Film, Download, Check } from "lucide-react";

export const DownloadModal = ({ lottieJson, animationName, onClose }) => {
  const [downloading, setDownloading] = useState("");
  const [done, setDone] = useState("");
  const canvasRef = useRef(null);

  const safeName = (animationName || "animation").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 40);

  const downloadJson = useCallback(() => {
    setDownloading("json");
    const blob = new Blob([JSON.stringify(lottieJson, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeName}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setDownloading("");
    setDone("json");
    setTimeout(() => setDone(""), 2000);
  }, [lottieJson, safeName]);

  const downloadCode = useCallback(() => {
    setDownloading("code");
    const embedCode = `<!DOCTYPE html>
<html>
<head>
  <title>${animationName || "Lottie Animation"}</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
  <style>
    body { margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; background: #0f172a; }
    #lottie { width: 400px; height: 400px; }
  </style>
</head>
<body>
  <div id="lottie"></div>
  <script>
    const animationData = ${JSON.stringify(lottieJson)};
    lottie.loadAnimation({
      container: document.getElementById('lottie'),
      renderer: 'svg',
      loop: true,
      autoplay: true,
      animationData: animationData
    });
  </script>
</body>
</html>`;
    const blob = new Blob([embedCode], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeName}.html`;
    a.click();
    URL.revokeObjectURL(url);
    setDownloading("");
    setDone("code");
    setTimeout(() => setDone(""), 2000);
  }, [lottieJson, animationName, safeName]);

  const downloadPng = useCallback(() => {
    setDownloading("png");
    const svgEl = document.querySelector('[data-testid="lottie-preview"] svg');
    if (!svgEl) {
      setDownloading("");
      return;
    }
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const canvas = document.createElement("canvas");
    canvas.width = 1024;
    canvas.height = 1024;
    const ctx = canvas.getContext("2d");
    const img = new window.Image();
    img.onload = () => {
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, 1024, 1024);
      ctx.drawImage(img, 0, 0, 1024, 1024);
      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${safeName}.png`;
        a.click();
        URL.revokeObjectURL(url);
        setDownloading("");
        setDone("png");
        setTimeout(() => setDone(""), 2000);
      });
    };
    img.onerror = () => {
      setDownloading("");
    };
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  }, [safeName]);

  const downloadDotLottie = useCallback(() => {
    setDownloading("dotlottie");
    // Download as .lottie (which is just the JSON with .lottie extension for compatibility)
    const blob = new Blob([JSON.stringify(lottieJson)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${safeName}.lottie`;
    a.click();
    URL.revokeObjectURL(url);
    setDownloading("");
    setDone("dotlottie");
    setTimeout(() => setDone(""), 2000);
  }, [lottieJson, safeName]);

  const options = [
    {
      id: "json",
      icon: FileJson,
      title: "Lottie JSON",
      desc: "Raw JSON file for lottie-web, lottie-react, etc.",
      action: downloadJson,
    },
    {
      id: "code",
      icon: Code2,
      title: "HTML Embed",
      desc: "Self-contained HTML file with embedded animation.",
      action: downloadCode,
    },
    {
      id: "png",
      icon: Image,
      title: "PNG Image",
      desc: "Static frame capture of current animation state.",
      action: downloadPng,
    },
    {
      id: "dotlottie",
      icon: Film,
      title: "dotLottie",
      desc: "Optimized .lottie format for web and mobile.",
      action: downloadDotLottie,
    },
  ];

  return (
    <div className="lf-modal-overlay" onClick={onClose} data-testid="download-modal">
      <div className="lf-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "520px" }}>
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
            Export Animation
          </h3>
          <button className="lf-btn-ghost" onClick={onClose} data-testid="download-close-btn">
            <X size={18} />
          </button>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {options.map((opt) => {
            const Icon = opt.icon;
            const isActive = downloading === opt.id;
            const isDone = done === opt.id;
            return (
              <button
                key={opt.id}
                onClick={opt.action}
                disabled={isActive}
                data-testid={`download-${opt.id}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "14px",
                  padding: "14px 16px",
                  background: "#020617",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  cursor: isActive ? "wait" : "pointer",
                  textAlign: "left",
                  width: "100%",
                  transition: "border-color 0.2s, background-color 0.2s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "rgba(59,130,246,0.4)";
                  e.currentTarget.style.background = "#0f172a";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#1e293b";
                  e.currentTarget.style.background = "#020617";
                }}
              >
                <div
                  style={{
                    width: "40px",
                    height: "40px",
                    borderRadius: "8px",
                    background: "#1e293b",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  {isDone ? (
                    <Check size={18} style={{ color: "#10b981" }} />
                  ) : isActive ? (
                    <div className="lf-spinner" />
                  ) : (
                    <Icon size={18} style={{ color: "#3b82f6" }} />
                  )}
                </div>
                <div style={{ flex: 1 }}>
                  <p
                    style={{
                      fontSize: "14px",
                      fontWeight: 600,
                      color: "#e2e8f0",
                      margin: 0,
                    }}
                  >
                    {opt.title}
                  </p>
                  <p
                    style={{
                      fontSize: "12px",
                      color: "#64748b",
                      margin: "2px 0 0 0",
                    }}
                  >
                    {opt.desc}
                  </p>
                </div>
                <Download size={16} style={{ color: "#475569", flexShrink: 0 }} />
              </button>
            );
          })}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>
    </div>
  );
};
