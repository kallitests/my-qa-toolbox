import { useState } from "react";
import JiraGenerator from "./components/JiraGenerator";

export default function App() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--color-background-tertiary, #f5f5f5)" }}>
      <JiraGenerator />
    </div>
  );
}
