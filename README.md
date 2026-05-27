# Hyperion Task - AI-Powered Workflow Automation Platform

<p align="left">
  <img src="https://img.shields.io/badge/Status-Beta-red?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/AI-Ollama-orange?style=flat-square" alt="Ollama">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square" alt="SQLite">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square" alt="Python">
</p>

**Hyperion Task** is an AI‑driven workflow automation platform designed for small to medium‑sized enterprises. It enables you to create, execute, and monitor automated workflows integrated with various services (email, databases, ERP, HTTP, documents, etc.), powered by a **Local Large Language Model (LLM)** for Natural Language Understanding (NLU).

Built with **Python asyncio**, **FastAPI**, **Ollama**, and **SQLite**, Hyperion Task can be easily run via Docker Compose or natively as a package module.

---

## 🔐 Why Local LLM (Ollama)?

Hyperion Task uses **Ollama** to run Large Language Models entirely on **your own infrastructure**. Unlike cloud‑based AI services (OpenAI, Anthropic, Google Gemini, etc.) that send your data to third‑party servers, **Ollama runs locally** inside your network.

### 💼 Benefits for your business

| Aspect | Cloud LLM (OpenAI, etc.) | Local LLM (Ollama) |
| :--- | :--- | :--- |
| **Data privacy** | ❌ Data sent to external servers | ✅ Data never leaves your premises |
| **Compliance** | ⚠️ GDPR, HIPAA risks | ✅ Full compliance control |
| **Internet required** | ✅ Always needed | ❌ Works offline |
| **Cost** | 💸 Per‑token / per‑request fees | 🆓 Free after setup |
| **Vendor lock‑in** | ✅ Yes | ❌ No, you can swap models anytime |
| **Custom models** | ❌ Limited | ✅ Any Ollama‑compatible model |

* **Default model:** `mistral` (7B parameters – fast and capable)  
* **Other compatible models:** `llama3.1`, `phi3`, `gemma2`, `qwen2`, `codellama`, `deepseek‑coder`, and any other model officially supported by Ollama.

---

## ✨ Key Advantages Over Competitors (n8n, Zapier, Airbyte, etc.)

| Feature | Hyperion Task | n8n / Zapier | Airbyte |
| :--- | :---: | :---: | :---: |
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
| **Template engine** | ✅ `{{path.to.value}}` | ✅ | ❌ |

> 💡 **Verdict:** Hyperion Task excels in **data privacy, flexibility, cost, and AI integration depth**. It is ideal for companies that require internal orchestration without exposing sensitive operation records to third parties.

---

## 📋 Pre-requisites Check

Before starting deployment, ensure your system matches the following requirement baselines:

### For Docker Setup:
- ✅ Docker installed (`docker --version`)
- ✅ Docker Compose installed (`docker compose --version`)
- ✅ Minimum 4GB RAM (8GB recommended)
- ✅ ~30GB disk space (for local Ollama model storage allocations)

### For Manual Setup:
- ✅ Python 3.11+ (`python3 --version`)
- ✅ pip (`pip --version`)
- ✅ Ollama installed (`ollama --version`)
- ✅ Minimum 4GB RAM (8GB recommended)
- ✅ ~15GB disk space

---

## 🚀 Installation & Deployment Guide

### 🐳 Option 1: Docker Compose (Recommended)

#### 1. Clone Repository
```bash
git clone [https://github.com/reyzzzl/Hyperion-task.git](https://github.com/reyzzzl/Hyperion-task.git)
cd Hyperion-task

```
#### 2. Start Services
```bash
docker compose up -d

```
*Note: This downloads core container stacks, prepares your environment, and automatically pulls the default mistral model (this initialization step might take 5-10 minutes depending on network bandwidth).*
#### 3. Monitor Pipeline Logs
```bash
docker compose ps              # Verify active containers
docker compose logs -f app     # Follow core application runtime tracking
docker compose logs -f ollama  # Follow internal local AI model instance loops

```
#### 4. Access Dashboard Interface
Launch your browser and navigate to: **http://localhost:8000/?token=hyperion-secret**
### 🔧 Option 2: Manual Installation (Module Execution Architecture)
To maintain structural integrity for internal absolute package paths, the application **must be executed as a pure Python module (python -m) from the parent directory** (one level above the cloned repository folder).
#### 1. Clone & Set Up the Virtual Environment
```bash
git clone [https://github.com/reyzzzl/Hyperion-task.git](https://github.com/reyzzzl/Hyperion-task.git)
cd Hyperion-task

# Create the sandbox environment
python3.11 -m venv venv

# Activate the Virtual Environment based on your OS environment:
source venv/bin/activate          # Linux/macOS
# venv\Scripts\Activate.ps1       # Windows PowerShell
# venv\Scripts\activate.bat       # Windows CMD

```
#### 2. Install Core Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt

```
#### 3. Pull Your Local Ollama Model
> 💡 **Note for Windows/macOS Users:** If the Ollama desktop engine is already running in your system tray, the required backend port 11434 is active. You can completely skip ollama serve and directly run the pull command.
> 
```bash
# Start the local daemon (Required for Linux CLI setups)
ollama serve

# Pull the default core operational network model
ollama pull mistral

# (Optional) High performance alternatives:
ollama pull llama3.1  # For advanced workflow reasoning structures
ollama pull phi3      # For lightweight, fast execution instances

```
#### 4. Execute the Application Instance
Step backward into the parent directory scope, then initiate the clean application module loop:
```bash
# Move to the parent directory level
cd ..

# Run the system module context securely
python -m Hyperion-task

```
## 🔧 Changing the LLM Model
You can update your system's operational NLU module engine to any alternate target network supported by Ollama.
#### Method 1 – Runtime Docker Variable Pass
```bash
OLLAMA_MODEL=llama3.1 docker compose up -d

```
#### Method 2 – Hardcoding Environment Blocks (docker-compose.yml)
```yaml
environment:
  - OLLAMA_MODEL=llama3.1:8b
  - LLM_BACKEND=ollama

```
#### Method 3 – Using Local Configuration (.env File)
Update the active parameter assignment block within your target environment file: OLLAMA_MODEL=llama3.1
### 🧠 Supported Model Characteristics
| Model | Size | Speed | Quality | Best For |
|---|---|---|---|---|
| **phi3** | 3.8B | ⚡⚡⚡ | Good | Basic automation rules and rapid parsing |
| **mistral** | 7B | ⚡⚡ | Excellent | Default standard (Balanced execution and context) |
| **llama3.1** | 8B | ⚡⚡ | Excellent | Multi-tier logical splits and deep data analysis |
| **gemma2** | 9B | ⚡ | Very High | Strict entity extraction and high-precision parsing |
## ⚙️ Configuration Variables (Environment Settings)
Create a custom .env file within the base repository folder (Hyperion-task/.env) to customize deployment keys:
| Variable | Default | Description |
|---|---|---|
| DASHBOARD_API_TOKEN | hyperion-secret | **CRITICAL SECURITY** – Master API access verification token |
| OLLAMA_MODEL | mistral | Targeted target name string of the selected local Ollama model |
| EMAIL_PROVIDER | *(empty)* | Toggle google or microsoft to initialize automated email polling workers |
| TIMEZONE | UTC | Local system coordination timezone (e.g., Asia/Jakarta) |
| NOTION_API_TOKEN | *(empty)* | Notion integration key to bridge core ERP systems |
| NOTION_DB_ORDERS | *(empty)* | Target Database ID mapping for customer transaction lists |
| NOTION_DB_TICKETS | *(empty)* | Target Database ID mapping for issue ticket tracking entries |
| NOTION_DB_TRANSACTIONS | *(empty)* | Target Database ID mapping for internal ledger records |
| NOTION_DB_INVENTORY | *(empty)* | Target Database ID mapping for global warehouse management assets |
| MS365_TENANT_ID | *(empty)* | Microsoft 365 Tenant ID string descriptor |
| MS365_CLIENT_ID | *(empty)* | Microsoft Application registration credential identifier |
| MS365_CLIENT_SECRET | *(empty)* | Microsoft Application platform production client secret key |
| LLM_BACKEND | ollama | Active AI backend framework selector |
| PORT | 8000 | Target web server hosting dashboard interface port |
## 🧩 Creating Your First Workflow
Orchestration tasks run on systematic structured JSON templates. This setup parses incoming message triggers, cross-references transaction databases, and responds automatically:
```
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
*Workflows can be provisioned by editing the target workflows operational table or directly via the control dashboard.*
## 🖥️ Control Dashboard & Monitoring
 * **Live Task Stream:** Monitor task transitions via real-time telemetry (Pending, Running, Succeeded, Failed states).
 * **Human-in-the-Loop Intercepts:** Specialized actions can pause and display a "Review" UI block, holding operations until manually approved by an operator.
 * **Operational Metrics:** Visual graphs for analysis of daily transaction loads and operational failure mitigation profiles.
 * **Secured API Access:** Internal telemetry data remains queryable over an internal REST stack via Bearer verification paths.
## 🔧 Extensibility & Customization
 * **Custom Action Nodes:** Append your procedural python rules into the core class handler block WorkflowExecutor.registered_actions.
 * **Third-Party Integrations:** Add separate custom scripts to the integrations/ folder, then link initialization bindings within main.py.
 * **String Parsing Engines:** The underlying parsing logic inside core/template.py handles recursive target objects ({{node.output.data}}) and list tracking indexes out of the box.

# Quick Docker Maintenance Commands
docker compose restart        # Soft restart runtime environments
docker compose down -v        # Terminate active services and wipe structural file system cache targets
docker compose logs -f app    # Attach to live application standard logging pipelines

```
## 📄 License
This platform is distributed open-source under the **MIT License**. You are free to run, fork, adjust, or utilize the system configuration setups in commercial enterprise deployments.
## 🤝 Contributing
Pull requests are welcome. For significant structural refactors, please open a design issue first to outline the proposed optimizations.