# 🐞 FixFlow — AI-Powered Bug Triage Orchestrator

FixFlow is a Streamlit web application that uses Google's Gemini AI to help development teams triage software bugs faster. Paste in a bug report (with optional supporting context files), and FixFlow generates two candidate fixes complete with code, reasoning, and a risk assessment. Developers can approve an AI-generated fix, or write their own and have the AI evaluate its compatibility and risk before approval. All triage activity is logged to a local database and visualized on a built-in analytics dashboard.

## Features

- **AI Bug Analysis** — Submit a bug description and optional context files (`.txt`, `.md`); Gemini returns two distinct proposed fixes, each with a title, code snippet, and reasoning.
- **Risk-Aware Review** — Every fix suggestion includes a risk level (Low / Medium / High) to help prioritize review effort.
- **Propose Your Own Fix** — Developers can write a custom fix instead of using an AI suggestion. The AI then compares it against the bug report and original suggestions, returning a compatibility score, identified risks, and a verdict (Proceed / Caution / Don't Use).
- **Approval Workflow** — Approve an AI fix or a custom fix with one click; approved and routed fixes are persisted to a SQLite database.
- **Analytics Dashboard** — View totals for analyzed, approved, and routed bugs, an AI-fix acceptance rate, a bar chart of bugs by risk level, and a recent activity table.
- **Pre-seeded Sample Data** — The database initializes with sample bug/fix records so the dashboard is populated immediately on first run.

## Tech Stack

- **Frontend/App Framework:** Streamlit
- **AI Model:** Google Gemini (gemini-2.5-flash) via the google-generativeai SDK
- **Database:** SQLite (local file fixflow.db)
- **Data Handling:** pandas
- **Language:** Python

## Project Structure

```
fixflow-bug-triage-agent/
├── .devcontainer/
│   └── devcontainer.json     # Dev Container configuration for consistent dev environments
├── app.py                    # Main Streamlit application (UI, AI calls, DB logic)
├── requirements.txt          # Python dependencies
├── .gitignore                # Excludes secrets, caches, DB files, etc.
└── fixflow.db                # SQLite database (auto-created on first run)
```

## Prerequisites

- Python 3.9+
- A Google AI Studio API key (Gemini API key)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/MunagalaDhanush/fixflow-bug-triage-agent.git
cd fixflow-bug-triage-agent
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

On Windows, use `venv\Scripts\activate` instead.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your Gemini API key

FixFlow reads the API key from either a local `.env` file or Streamlit secrets (for cloud deployment).

Local development — create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Streamlit Community Cloud — add the key to your app's Secrets:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

Never commit your API key to source control. The `.gitignore` in this repo is already configured to help protect secrets.

### 5. Run the app

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`.

## Usage

1. Open the app and use the sidebar to paste a Bug Report describing the issue.
2. Optionally upload supporting context files (`.txt` or `.md`) for additional background.
3. Click Analyze Bug to generate two AI-proposed fixes, each shown with its code, reasoning, and risk level.
4. Either click Approve Fix on the suggestion you want to accept, or click Write My Own Fix to submit your own fix for AI evaluation, then Analyze My Fix to get a compatibility score, risk callouts, and a verdict before approving.
5. Switch to the Dashboard tab to view aggregate metrics, a risk-level breakdown chart, and a table of recent triage activity.

## Development Container

This repo includes a `.devcontainer/devcontainer.json` for use with VS Code Dev Containers or GitHub Codespaces, enabling a consistent, pre-configured development environment.

## Notes on Data

FixFlow stores triage history locally in a `fixflow.db` SQLite file, created automatically on first launch. If the database is empty, it seeds itself with sample bug/fix records so the Dashboard has data to display immediately.

## License

No license has been specified for this project yet. Consider adding one (e.g., MIT, Apache 2.0) if you intend for others to use or contribute to this code.

## Contributing

This is currently a single-contributor project. Issues and pull requests are welcome if you'd like to propose improvements.
