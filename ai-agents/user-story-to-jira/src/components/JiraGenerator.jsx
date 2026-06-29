import { useState, useRef } from "react";

const PROMPT_SYSTEM = `You are an expert Agile Business Analyst and QA Engineer.
Your job is to transform a raw user story into a structured, production-ready Jira ticket in JSON format.

Rules:
- Write all fields in the same language as the input user story
- Infer a realistic priority based on the story's business impact
- Generate at least 5 acceptance criteria in Given/When/Then format
- Generate at least 3 test cases covering: happy path, edge case, error case
- Each test case must include steps, expected result, and test type
- Add relevant labels based on the story's domain
- Assign a story point estimate using Fibonacci scale (1,2,3,5,8,13)
- Output ONLY valid JSON, no prose, no markdown fences, no explanation

Output this exact JSON schema:
{
  "summary": "string — concise title, max 10 words",
  "issue_type": "Story",
  "priority": "Highest | High | Medium | Low",
  "story_points": number,
  "labels": ["string"],
  "description": {
    "user_story": "As a [persona], I want [action], so that [benefit]",
    "context": "string — business context and motivation",
    "assumptions": ["string"],
    "out_of_scope": ["string"]
  },
  "acceptance_criteria": [
    {
      "id": "AC-01",
      "given": "string",
      "when": "string",
      "then": "string"
    }
  ],
  "test_cases": [
    {
      "id": "TC-01",
      "title": "string",
      "type": "happy_path | edge_case | error_case | security | performance",
      "preconditions": ["string"],
      "steps": ["string"],
      "expected_result": "string",
      "linked_ac": ["AC-01"]
    }
  ],
  "definition_of_done": ["string"],
  "technical_notes": ["string"]
}`;

const PRIORITY_COLORS = {
  Highest: { bg: "#fee2e2", text: "#991b1b", border: "#fca5a5" },
  High:    { bg: "#ffedd5", text: "#9a3412", border: "#fdba74" },
  Medium:  { bg: "#fef9c3", text: "#854d0e", border: "#fde047" },
  Low:     { bg: "#dcfce7", text: "#166534", border: "#86efac" },
};

const TYPE_LABELS = {
  happy_path:  { label: "Happy path",  color: "#166534", bg: "#dcfce7" },
  edge_case:   { label: "Edge case",   color: "#854d0e", bg: "#fef9c3" },
  error_case:  { label: "Error case",  color: "#991b1b", bg: "#fee2e2" },
  security:    { label: "Security",    color: "#1e3a5f", bg: "#dbeafe" },
  performance: { label: "Performance", color: "#5b21b6", bg: "#ede9fe" },
};

function Badge({ children, color, bg, border }) {
  return (
    <span style={{
      display: "inline-block",
      fontSize: 11,
      fontWeight: 500,
      padding: "2px 8px",
      borderRadius: 4,
      background: bg,
      color,
      border: `1px solid ${border || bg}`,
      letterSpacing: "0.02em",
    }}>
      {children}
    </span>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        color: "#6b7280",
        marginBottom: 10,
        paddingBottom: 6,
        borderBottom: "1px solid #e5e7eb",
      }}>
        {title}
      </div>
      {children}
    </div>
  );
}

function CriteriaCard({ item }) {
  return (
    <div style={{
      background: "#f9fafb",
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      padding: "10px 14px",
      marginBottom: 8,
      fontSize: 13,
    }}>
      <span style={{ fontWeight: 600, color: "#6366f1", marginRight: 8 }}>{item.id}</span>
      <div style={{ marginTop: 6, lineHeight: 1.7 }}>
        <span style={{ color: "#6b7280" }}>Given </span><span>{item.given}</span><br />
        <span style={{ color: "#6b7280" }}>When </span><span>{item.when}</span><br />
        <span style={{ color: "#6b7280" }}>Then </span><span>{item.then}</span>
      </div>
    </div>
  );
}

function TestCaseCard({ tc }) {
  const typeInfo = TYPE_LABELS[tc.type] || { label: tc.type, color: "#374151", bg: "#f3f4f6" };
  return (
    <div style={{
      background: "#f9fafb",
      border: "1px solid #e5e7eb",
      borderRadius: 8,
      padding: "12px 14px",
      marginBottom: 10,
      fontSize: 13,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <span style={{ fontWeight: 600 }}>
          <span style={{ color: "#6366f1", marginRight: 8 }}>{tc.id}</span>
          {tc.title}
        </span>
        <Badge color={typeInfo.color} bg={typeInfo.bg}>{typeInfo.label}</Badge>
      </div>
      {tc.preconditions?.length > 0 && (
        <div style={{ marginBottom: 6 }}>
          <span style={{ color: "#6b7280", fontWeight: 500 }}>Préconditions : </span>
          {tc.preconditions.join(" · ")}
        </div>
      )}
      <ol style={{ margin: "6px 0 6px 16px", padding: 0, lineHeight: 1.7 }}>
        {tc.steps.map((s, i) => <li key={i}>{s}</li>)}
      </ol>
      <div style={{ background: "#ecfdf5", borderRadius: 4, padding: "6px 10px", color: "#065f46", marginTop: 4 }}>
        <strong>Résultat attendu : </strong>{tc.expected_result}
      </div>
      {tc.linked_ac?.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 11, color: "#9ca3af" }}>
          Lié à : {tc.linked_ac.join(", ")}
        </div>
      )}
    </div>
  );
}

export default function JiraGenerator() {
  const [userStory, setUserStory] = useState("");
  const [loading, setLoading] = useState(false);
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("visual");
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef(null);

  const examples = [
    "En tant qu'utilisateur, je veux pouvoir me connecter avec mon compte Google, afin de ne pas avoir à créer un nouveau mot de passe.",
    "As a product manager, I want to export reports as PDF, so that I can share them with stakeholders who don't have app access.",
    "En tant qu'admin, je veux pouvoir désactiver un compte utilisateur sans le supprimer, afin de suspendre l'accès temporairement.",
  ];

  async function generate() {
    if (!userStory.trim()) return;
    setLoading(true);
    setError(null);
    setTicket(null);

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-6",
          max_tokens: 4000,
          system: PROMPT_SYSTEM,
          messages: [{ role: "user", content: userStory }],
        }),
      });

      const data = await res.json();
      const raw = data.content?.find(b => b.type === "text")?.text || "";
      const clean = raw.replace(/```json|```/g, "").trim();
      const parsed = JSON.parse(clean);
      setTicket(parsed);
      setActiveTab("visual");
    } catch (e) {
      setError("Erreur lors de la génération. Vérifiez votre clé API ou réessayez.");
    } finally {
      setLoading(false);
    }
  }

  function copyJson() {
    if (!ticket) return;
    navigator.clipboard.writeText(JSON.stringify(ticket, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const priority = ticket?.priority;
  const pColor = PRIORITY_COLORS[priority] || PRIORITY_COLORS.Medium;

  return (
    <div style={{ maxWidth: 820, margin: "0 auto", padding: "32px 16px", fontFamily: "system-ui, sans-serif" }}>

      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect width="28" height="28" rx="6" fill="#0052CC"/>
            <path d="M14 6L21 13.5L14 21L7 13.5L14 6Z" fill="white" opacity="0.9"/>
            <circle cx="14" cy="13.5" r="3" fill="#0052CC"/>
          </svg>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: "#111827" }}>
            User Story → Jira Ticket
          </h1>
        </div>
        <p style={{ margin: 0, fontSize: 14, color: "#6b7280", lineHeight: 1.6 }}>
          Collez une user story et obtenez un ticket Jira structuré avec critères d'acceptation et test cases.
        </p>
      </div>

      {/* Input */}
      <div style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        padding: 20,
        marginBottom: 20,
        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
      }}>
        <label style={{ fontSize: 13, fontWeight: 500, color: "#374151", display: "block", marginBottom: 8 }}>
          User story
        </label>
        <textarea
          ref={textareaRef}
          value={userStory}
          onChange={e => setUserStory(e.target.value)}
          placeholder="Ex: En tant qu'utilisateur, je veux pouvoir réinitialiser mon mot de passe..."
          style={{
            width: "100%",
            minHeight: 100,
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid #d1d5db",
            fontSize: 14,
            lineHeight: 1.6,
            resize: "vertical",
            fontFamily: "inherit",
            outline: "none",
            boxSizing: "border-box",
            color: "#111827",
          }}
        />

        <div style={{ marginTop: 10, marginBottom: 14 }}>
          <span style={{ fontSize: 12, color: "#9ca3af", marginRight: 8 }}>Exemples :</span>
          {examples.map((ex, i) => (
            <button
              key={i}
              onClick={() => setUserStory(ex)}
              style={{
                fontSize: 12,
                padding: "2px 8px",
                marginRight: 6,
                borderRadius: 4,
                border: "1px solid #d1d5db",
                background: "#f9fafb",
                color: "#374151",
                cursor: "pointer",
              }}
            >
              Exemple {i + 1}
            </button>
          ))}
        </div>

        <button
          onClick={generate}
          disabled={loading || !userStory.trim()}
          style={{
            background: loading || !userStory.trim() ? "#9ca3af" : "#0052CC",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 500,
            cursor: loading || !userStory.trim() ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          {loading ? (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: "spin 1s linear infinite" }}>
                <path d="M21 12a9 9 0 11-6.219-8.56"/>
              </svg>
              Génération en cours…
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
              Générer le ticket Jira
            </>
          )}
        </button>
      </div>

      {error && (
        <div style={{ background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 8, padding: "12px 16px", color: "#991b1b", fontSize: 14, marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Result */}
      {ticket && (
        <div style={{
          background: "#fff",
          border: "1px solid #e5e7eb",
          borderRadius: 12,
          overflow: "hidden",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
        }}>
          {/* Ticket header */}
          <div style={{ background: "#f8faff", borderBottom: "1px solid #e5e7eb", padding: "16px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10 }}>
              <div>
                <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4, fontWeight: 500 }}>STORY</div>
                <h2 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: "#111827", lineHeight: 1.4 }}>
                  {ticket.summary}
                </h2>
              </div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                <Badge color={pColor.text} bg={pColor.bg} border={pColor.border}>{priority}</Badge>
                <Badge color="#4b5563" bg="#f3f4f6">{ticket.story_points} pts</Badge>
                {ticket.labels?.slice(0, 3).map(l => (
                  <Badge key={l} color="#374151" bg="#f3f4f6">{l}</Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ borderBottom: "1px solid #e5e7eb", display: "flex" }}>
            {[["visual", "Vue structurée"], ["json", "JSON brut"]].map(([id, label]) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                style={{
                  padding: "10px 20px",
                  fontSize: 13,
                  fontWeight: activeTab === id ? 600 : 400,
                  color: activeTab === id ? "#0052CC" : "#6b7280",
                  borderBottom: activeTab === id ? "2px solid #0052CC" : "2px solid transparent",
                  background: "none",
                  border: "none",
                  borderBottom: activeTab === id ? "2px solid #0052CC" : "2px solid transparent",
                  cursor: "pointer",
                }}
              >
                {label}
              </button>
            ))}
            <div style={{ flex: 1 }} />
            <button
              onClick={copyJson}
              style={{
                fontSize: 12,
                padding: "8px 14px",
                margin: "6px 12px",
                borderRadius: 6,
                border: "1px solid #d1d5db",
                background: "#f9fafb",
                color: "#374151",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              {copied ? "✓ Copié !" : "⎘ Copier JSON"}
            </button>
          </div>

          <div style={{ padding: 20 }}>
            {activeTab === "visual" ? (
              <>
                <Section title="Description">
                  <p style={{ margin: 0, fontSize: 14, color: "#111827", lineHeight: 1.7, marginBottom: 10 }}>
                    {ticket.description.user_story}
                  </p>
                  <p style={{ margin: 0, fontSize: 13, color: "#6b7280", lineHeight: 1.7 }}>
                    {ticket.description.context}
                  </p>
                  {ticket.description.assumptions?.length > 0 && (
                    <div style={{ marginTop: 10 }}>
                      <span style={{ fontSize: 12, fontWeight: 500, color: "#6b7280" }}>Hypothèses : </span>
                      <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: 13, color: "#374151", lineHeight: 1.7 }}>
                        {ticket.description.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                      </ul>
                    </div>
                  )}
                  {ticket.description.out_of_scope?.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 500, color: "#6b7280" }}>Hors scope : </span>
                      <ul style={{ margin: "4px 0 0 16px", padding: 0, fontSize: 13, color: "#374151", lineHeight: 1.7 }}>
                        {ticket.description.out_of_scope.map((o, i) => <li key={i}>{o}</li>)}
                      </ul>
                    </div>
                  )}
                </Section>

                <Section title={`Critères d'acceptation (${ticket.acceptance_criteria?.length})`}>
                  {ticket.acceptance_criteria?.map(ac => <CriteriaCard key={ac.id} item={ac} />)}
                </Section>

                <Section title={`Test cases (${ticket.test_cases?.length})`}>
                  {ticket.test_cases?.map(tc => <TestCaseCard key={tc.id} tc={tc} />)}
                </Section>

                <Section title="Definition of Done">
                  <ul style={{ margin: 0, padding: "0 0 0 18px", fontSize: 13, color: "#374151", lineHeight: 1.85 }}>
                    {ticket.definition_of_done?.map((d, i) => <li key={i}>{d}</li>)}
                  </ul>
                </Section>

                {ticket.technical_notes?.length > 0 && (
                  <Section title="Notes techniques">
                    <ul style={{ margin: 0, padding: "0 0 0 18px", fontSize: 13, color: "#374151", lineHeight: 1.85 }}>
                      {ticket.technical_notes.map((n, i) => <li key={i}>{n}</li>)}
                    </ul>
                  </Section>
                )}
              </>
            ) : (
              <pre style={{
                margin: 0,
                fontFamily: "ui-monospace, monospace",
                fontSize: 12,
                color: "#111827",
                background: "#f9fafb",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                padding: 16,
                overflowX: "auto",
                whiteSpace: "pre",
                lineHeight: 1.65,
              }}>
                {JSON.stringify(ticket, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
