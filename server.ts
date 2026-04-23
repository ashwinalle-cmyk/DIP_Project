import express from "express";
import { createServer as createViteServer } from "vite";
import path from "path";
import cors from "cors";
import { createProxyMiddleware } from "http-proxy-middleware";
import { spawn, spawnSync } from "child_process";

async function startServer() {
  const app = express();
  const PORT = 3000;

  // Install Python dependencies
  console.log("📦 Installing Python dependencies...");
  try {
    const pipInstall = spawnSync("python3", ["-m", "pip", "install", "-r", "roadguardian/requirements.txt"]);
    if (pipInstall.error) {
      console.error("❌ Failed to run pip install:", pipInstall.error);
    } else {
      console.log("✅ Pip install completed");
      if (pipInstall.stderr.toString().trim()) {
        console.log(`[Pip Output] ${pipInstall.stderr.toString()}`);
      }
    }
  } catch (err) {
    console.error("❌ Error during pip install:", err);
  }

  // Proxy API requests to the Python backend
  const pythonProxy = createProxyMiddleware({
    target: "http://127.0.0.1:8000",
    changeOrigin: true,
    pathFilter: ["/health", "/calibrate", "/analyze"],
    on: {
      error: (err, req, res) => {
        console.error(`[Proxy Error] ${req.url}: ${err.message}`);
        if (res && "status" in res) {
          (res as any).status(500).json({ error: "Python backend not reachable", details: err.message });
        }
      },
    },
  });

  app.use(pythonProxy);

  app.use(cors());
  app.use(express.json());

  // Serve Python source files for the "Source" tab
  app.use("/roadguardian", express.static(path.join(process.cwd(), "roadguardian")));

  // Health check endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "ok", system: "RoadGuardian Intelligence Engine" });
  });

  // Start Python backend in the background
  console.log("🚀 Starting Python backend (uvicorn roadguardian.app:app)...");
  const pythonProcess = spawn("python3", ["-m", "uvicorn", "roadguardian.app:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "info"]);
  
  pythonProcess.on("error", (err) => {
    console.error("❌ Failed to start Python process:", err);
  });

  pythonProcess.stdout.on("data", (data) => {
    const output = data.toString();
    console.log(`[Python] ${output.trim()}`);
  });

  pythonProcess.stderr.on("data", (data) => {
    const output = data.toString();
    console.error(`[Python Error] ${output.trim()}`);
  });

  pythonProcess.on("close", (code) => {
    console.error(`[Python Process] Exited with code ${code}`);
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on http://localhost:${PORT}`);
  });
}

startServer();
