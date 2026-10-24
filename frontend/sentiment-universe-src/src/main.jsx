import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./AppSentiment.jsx";
import "./sentiment.css";
import "./orbital-scene.css";
import "./sentiment-preview.css";
import "./fonts.css";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
