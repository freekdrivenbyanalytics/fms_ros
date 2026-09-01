import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../index.css";
import { AdminPortalApp } from "./AdminPortalApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AdminPortalApp />
  </StrictMode>
);
