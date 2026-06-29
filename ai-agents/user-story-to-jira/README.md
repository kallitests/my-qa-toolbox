> ⚠️ **Work in progress** — This project and its prompt are currently under active development. Features, structure, and output format may evolve frequently.

# 🎫 User Story → Jira Ticket

> Transform any user story into a production-ready Jira ticket in seconds — with acceptance criteria, test cases, Definition of Done, and technical notes — powered by Claude AI.

![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-4-646CFF?logo=vite&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet%204.6-D97757?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **Paste, generate, done** — input any user story (French or English), get a full Jira ticket JSON
- **Structured output** every time — summary, priority, story points, labels, acceptance criteria (Given/When/Then), test cases, DoD, technical notes
- **Dual view** — toggle between a readable visual card and the raw JSON
- **One-click copy** — copy the JSON to paste directly into a Jira import or API call
- **3 built-in examples** to get started immediately
- **Language-aware** — the AI writes the ticket in the same language as your input

---

## 📸 Preview

```
┌─────────────────────────────────────────────────────┐
│  User Story → Jira Ticket                           │
│                                                     │
│  [ User story input textarea                      ] │
│  [ Exemple 1 ] [ Exemple 2 ] [ Exemple 3 ]         │
│  [ ⚡ Générer le ticket Jira ]                      │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ STORY  Réinitialisation du mot de passe      │  │
│  │        [High] [5 pts] [auth] [security]      │  │
│  │──────────────────────────────────────────────│  │
│  │ Vue structurée │ JSON brut        ⎘ Copy     │  │
│  │──────────────────────────────────────────────│  │
│  │ Description · Acceptance criteria · Tests    │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🗂️ Project structure

```
user-story-to-jira/
├── src/
│   ├── components/
│   │   └── JiraGenerator.jsx   # Main component — UI + API call
│   ├── App.jsx                 # Root component
│   └── main.jsx                # React entry point
├── index.html                  # HTML entry point
├── vite.config.js              # Vite config with CORS proxy
├── package.json
├── .env.example                # Environment variables template
├── .gitignore
├── PROMPT.md                   # System prompt documentation
└── README.md
```

---

## 🚀 Getting started

### Prerequisites

- Node.js ≥ 18
- An [Anthropic API key](https://console.anthropic.com/)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/user-story-to-jira.git
cd user-story-to-jira

# 2. Install dependencies
npm install

# 3. Configure your API key
cp .env.example .env
# Then edit .env and replace with your actual key:
# VITE_ANTHROPIC_API_KEY=sk-ant-...

# 4. Start the dev server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ⚙️ Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com/) |

> **Security note** — The `.env` file is listed in `.gitignore` and will never be committed. Never expose your API key in a public repository.

---

## 📦 Output format

Each generated ticket follows this JSON schema:

```json
{
  "summary": "Short ticket title, max 10 words",
  "issue_type": "Story",
  "priority": "High",
  "story_points": 5,
  "labels": ["authentication", "security"],
  "description": {
    "user_story": "As a user, I want to...",
    "context": "Business motivation...",
    "assumptions": ["..."],
    "out_of_scope": ["..."]
  },
  "acceptance_criteria": [
    {
      "id": "AC-01",
      "given": "...",
      "when": "...",
      "then": "..."
    }
  ],
  "test_cases": [
    {
      "id": "TC-01",
      "title": "...",
      "type": "happy_path | edge_case | error_case | security | performance",
      "preconditions": ["..."],
      "steps": ["..."],
      "expected_result": "...",
      "linked_ac": ["AC-01"]
    }
  ],
  "definition_of_done": ["..."],
  "technical_notes": ["..."]
}
```

See [`PROMPT.md`](./PROMPT.md) for the full system prompt and design rationale.

---

## 🔌 Integrating with the Jira API

The JSON output is designed to map directly to Jira's REST API v3. Example:

```js
const ticket = /* output from this app */;

await fetch("https://your-domain.atlassian.net/rest/api/3/issue", {
  method: "POST",
  headers: {
    "Authorization": `Basic ${btoa("email@example.com:your_jira_token")}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    fields: {
      project: { key: "YOUR_PROJECT_KEY" },
      summary: ticket.summary,
      issuetype: { name: ticket.issue_type },
      priority: { name: ticket.priority },
      description: {
        type: "doc",
        version: 1,
        content: [{ type: "paragraph", content: [{ type: "text", text: ticket.description.user_story }] }]
      },
      labels: ticket.labels,
      story_points: ticket.story_points,
    }
  })
});
```

---

## 🛠️ Build for production

```bash
npm run build
# Output in /dist — ready to deploy on Vercel, Netlify, GitHub Pages, etc.
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push to the branch: `git push origin feat/my-feature`
5. Open a Pull Request

### Ideas for contributions

- [ ] Export to Markdown or CSV
- [ ] Jira API direct push (one-click import)
- [ ] Support for sub-tasks generation
- [ ] Dark mode
- [ ] History of generated tickets (localStorage)
- [ ] Custom prompt editor in the UI

---

## 📄 License

MIT © 2026 — feel free to use, adapt, and share.

---

## 🙏 Built with

- [React](https://react.dev/) — UI framework
- [Vite](https://vitejs.dev/) — build tool
- [Claude API](https://docs.anthropic.com/) — AI backbone (model: `claude-sonnet-4-6`)
