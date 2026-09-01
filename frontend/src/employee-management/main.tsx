import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "../index.css";
import { EmployeeManagementApp } from "./EmployeeManagementApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <EmployeeManagementApp />
  </StrictMode>
);
