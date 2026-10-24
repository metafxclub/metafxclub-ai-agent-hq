import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  build: {
    outDir: "dist/client",
  },
  optimizeDeps: {
    include: ["react", "react-dom/client"],
  },
  server: {
    host: "0.0.0.0",
    allowedHosts: ["terminal.local"],
    // QA files can be temporarily locked on Windows; they are not app inputs.
    watch: {
      ignored: [/(^|[/\\])(qa|reference|docs)([/\\]|$)/, /\.md$/i],
    },
    warmup: {
      clientFiles: ["./src/main.jsx"],
    },
  },
  // Handoff uses built files, without a development file watcher.
  preview: {
    host: "127.0.0.1",
    port: 4197,
    strictPort: true,
  },
  plugins: [react()],
});
