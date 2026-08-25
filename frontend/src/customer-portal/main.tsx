import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../index.css";
import { CustomerPortalApp } from "./CustomerPortalApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <CustomerPortalApp />
  </StrictMode>
);
