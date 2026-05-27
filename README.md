# # Hyperion Task - AI-Powered Workflow Automation Platform
<p align="center">
<img src="[https://img.shields.io/badge/Status-Beta-red?style=flat-square](https://img.shields.io/badge/Status-Beta-red?style=flat-square)" alt="Status">
<img src="[https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)" alt="FastAPI">
<img src="[https://img.shields.io/badge/AI-Ollama-orange?style=flat-square](https://img.shields.io/badge/AI-Ollama-orange?style=flat-square)" alt="Ollama">
<img src="[https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square)" alt="SQLite">
<img src="[https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)" alt="Python">
</p>
**Hyperion Task** is an AI‑driven workflow automation platform designed for small to medium‑sized enterprises. It enables you to create, execute, and monitor automated workflows integrated with various services (email, databases, ERP, HTTP, documents, etc.), powered by a **Local Large Language Model (LLM)** for Natural Language Understanding (NLU).
Built with **Python asyncio**, **FastAPI**, **Ollama**, and **SQLite**, Hyperion Task can be easily run via Docker Compose or natively.
## 🔐 Why Local LLM (Ollama)?
Hyperion Task uses **Ollama** to run Large Language Models entirely on **your own infrastructure**. Unlike cloud‑based AI services (OpenAI, Anthropic, Google Gemini, etc.) that send your data to third‑party servers, **Ollama runs locally** inside your network.
### Benefits for your business
| Aspect | Cloud LLM (OpenAI, etc.) | Local LLM (Ollama) |
|---|---|---|
| **Data privacy** | ❌ Data sent to external servers | ✅ Data never leaves your premises |
| **Compliance** | ⚠️ GDPR, HIPAA risks | ✅ Full compliance control |
| **Internet required** | ✅ Always needed | ❌ Works offline |
| **Cost** | 💸 Per‑token / per‑request fees | 🆓 Free after setup |
| **Vendor lock‑in** | ✅ Yes | ❌ No, you can swap models anytime |
| **Custom models** | ❌ Limited | ✅ Any Ollama‑compatible model |
 * **Default model:** mistral (7B parameters – fast and capable)
 * **Other compatible models:** llama3, phi3, gemma2, qwen2, codellama, deepseek‑coder, and any model supported by Ollama.
## ✨ Key Advantages Over Competitors (n8n, Zapier, Airbyte, etc.)
| Feature | Hyperion Task | n8n / Zapier | Airbyte |
|---|---|---|---|
| **AI Native NLU** | ✅ Built‑in local LLM | ❌ Needs external AI | ❌ |
| **Data privacy** | ✅ Complete (local) | ❌ Cloud‑only | ⚠️ Partial |
| **Human‑in‑the‑loop** | ✅ Approval dashboard | ⚠️ Limited | ❌ |
| **Full code control** | ✅ Open source | ❌ Closed source | ⚠️ Limited |
| **Operational cost** | 🆓 Very low (self‑hosted) | 💸 High (per task/API) | 💸 Medium |
| **ERP via Notion** | ✅ Native support | ❌ | ✅ (limited) |
| **Loop & Condition** | ✅ Native | ✅ (some) | ❌ |
| **Email polling** | ✅ Gmail / Microsoft 365 | ✅ (limited) | ❌ |
| **Real‑time dashboard** | ✅ Streaming tasks | ✅ | ❌ |
| **Retry & Timeout** | ✅ Per‑node configurable | ⚠️ Limited | ❌ |
| **Template engine** | ✅ {{path.to.value}} | ✅ | ❌ |
> **Verdict:** Hyperion Task excels in **data privacy, flexibility, cost, and AI integration depth**. Ideal for companies that require internal automation without exposing sensitive data to third parties.
> 
## 🔧 Changing the LLM Model
You are free to use any Ollama‑compatible model. The NLU engine will automatically use the model you specify—no code changes required.
### Method 1 – Environment variable (Docker)
```bash
OLLAMA_MODEL=llama3.1 docker compose up

```
### Method 2 – Modify docker-compose.yml
```yaml
environment:
  - OLLAMA_MODEL=llama3.1:8b
  - LLM_BACKEND=ollama

```
### Method 3 – Native run (without Docker)
```bash
ollama pull llama3.1
python -m hyperion_task.main

```
### 🧠 Popular models to try
| Model | Size | Best for |
|---|---|---|
| mistral | 7B | Default – balance speed & quality |
| llama3.1 | 8B | Strong reasoning |
| phi3 | 3.8B | Very fast, good for simple tasks |
| gemma2 | 9B | High accuracy |
| qwen2 | 7B | Multilingual support |
| codellama | 7B | Code understanding |
## 📋 System Requirements
 * Docker & Docker Compose (recommended) **OR** Python 3.11+, pip
 * Minimum **4 GB RAM** (8 GB recommended for larger models)
 * *(Optional)* credentials.json from Google Cloud Platform for Gmail/Google Workspace
 * *(Optional)* Environment variables for Microsoft 365 Graph API
## 🚀 Installation & Running Tutorial
### 1. Clone the repository
```bash
git clone https://github.com/yourusername/hyperion_task.git
cd hyperion_task

```
### 2. Run with Docker Compose (Easiest)
```bash
docker compose up -d

```
**This will automatically:**
 * Start Ollama with the mistral model *(pull may take a few minutes the first time)*.
 * Start the Hyperion Task application on port 8000.
### 3. Without Docker (Manual Setup)
```bash
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
ollama pull mistral
python -m hyperion_task.main

```
### 4. Access the Dashboard
Open your browser and navigate to: **http://localhost:8000/?token=hyperion-secret**
> ⚠️ **Security Warning:** Change the default token immediately! Set the DASHBOARD_API_TOKEN environment variable before deploying.
> 
## ⚙️ Configuration Variables (.env)
Create a .env file or set these environment variables in your deployment:
| Variable | Default | Description |
|---|---|---|
| DASHBOARD_API_TOKEN | hyperion-secret | **MUST CHANGE** – API authentication token |
| OLLAMA_MODEL | mistral | Ollama model to use (e.g., llama3.1, phi3) |
| EMAIL_PROVIDER | *(empty)* | google or microsoft – enables email polling |
| TIMEZONE | UTC | Timezone for meetings (e.g., Asia/Jakarta) |
| NOTION_API_TOKEN | *(empty)* | Notion integration token |
| NOTION_DB_ORDERS | *(empty)* | Notion database ID for orders |
| NOTION_DB_TICKETS | *(empty)* | Notion database ID for tickets |
| NOTION_DB_TRANSACTIONS | *(empty)* | Notion database ID for transactions |
| NOTION_DB_INVENTORY | *(empty)* | Notion database ID for inventory |
| MS365_TENANT_ID | *(empty)* | For Microsoft 365 integration |
| MS365_CLIENT_ID | *(empty)* | App registration client ID |
| MS365_CLIENT_SECRET | *(empty)* | Client secret |
| LLM_BACKEND | ollama | Currently only ollama is supported |
| PORT | 8000 | Web dashboard port |
## 📁 Project Structure
```text
hyperion_task/
├── core/               # Template engine, NLU, workflow engine, manager
├── integrations/       # Google Workspace, Microsoft365, LibreOffice, ERP (Notion/Dummy)
├── database/           # SQLite async wrapper
├── web/                # FastAPI dashboard + template
├── main.py             # Entry point
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .gitignore

```
## 🧩 Creating Your First Workflow
Workflows are defined as JSON. The example below reads a customer email, checks order status from a database, and replies.
```json
{
  "name": "Auto-reply order status",
  "trigger": "email",
  "nodes": [
    {
      "temp_id": "query_db",
      "action_type": "database_query",
      "config": {
        "query": "SELECT status FROM orders WHERE order_id = :oid",
        "params": {"oid": "{{input.order_id}}"}
      },
      "next_node": "send_reply"
    },
    {
      "temp_id": "send_reply",
      "action_type": "send_email",
      "config": {
        "to": "{{input.from_email}}",
        "subject": "Order status",
        "body": "Your status: {{node_outputs.query_db.0.status}}"
      }
    }
  ],
  "start_node": "query_db"
}

```
*Workflows can be added via the database (workflows table) or triggered automatically by email polling.*
## 🖥️ Dashboard & Monitoring
 * **Live Task Stream:** See tasks incoming, running, failed, or waiting for approval in real-time.
 * **Human Approval:** Tasks requiring human confirmation show a "Review" button. You can approve/reject with custom notes.
 * **Analytics & Statistics:** Total tasks, status breakdown, and executor performance metrics (success/fail rates).
 * **API Endpoints:** All orchestration data is fully accessible via REST API secured with a Bearer token.
## 🔧 Customization & Extensibility
 * **Add a new action type:** Register a custom function in WorkflowExecutor.registered_actions.
 * **New integrations:** Create a new class module inside the integrations/ folder and initialize it in main.py.
 * **Modify template engine:** The core/template.py file supports deep nesting via {{a.b.c}} expressions and list indexing.
## 🐛 Common Troubleshooting
| Issue | Solution |
|---|---|
| ollama: command not found | Install Ollama locally or use the recommended Docker Compose environment. |
| Model pull takes too long | Network issue or low bandwidth. Choose a smaller model like phi3 or tinyllama. |
| Dashboard login fails | Verify your DASHBOARD_API_TOKEN; ensure you use ?token=... appended to the URL. |
| Email not processed | Double-check that EMAIL_PROVIDER is explicitly set and your tokens/credentials are valid. |
| Workflow stuck in pending | Check internal process logs using command: docker compose logs app. |
| sqlite3.OperationalError | Delete the corrupted tasks.db file and restart—tables will auto‑create on startup. |
## 📄 License
Distributed under the **MIT License**. See LICENSE for more information (free to use, modify, and distribute).
## 🤝 Contributing
Pull requests are always welcome! For major structural changes, please open an issue first to discuss what you would like to alter.