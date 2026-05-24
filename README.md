# Multiagent Cybersecurity Intelligent System

![Python](https://img.shields.io/badge/Python-3.11-green.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A powerful AI-driven Security Operations Center dashboard and API that leverages four advanced models to automatically identify, classify, prioritize, and respond to threats—reducing SOC analyst workload by 3x vs traditional SIEM approaches.

> **Accuracy:** 97–100% | **Alert Reduction:** 3x | **Technology:** Python, FastAPI, PyTorch, Transformers, Vanilla JS

---

## 🚀 Quick Start

1. **Clone and Setup**
    ```bash
    git clone https://github.com/Tayanithaa/Multiagent_Cybersecurity_Intelligent_system.git
    cd Multiagent_Cybersecurity_Intelligent_system
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2. **Training (Optional/First Time)**
    ```bash
    python training/train_bert_model.py
    python training/train_correlation_roberta_model.py
    python training/train_ti_enrichment_bert_model.py
    python training/train_response_albert_model.py
    ```

3. **Testing**
    ```bash
    python test_real_logs.py csv data/sample_logs.csv
    python tests/test_integration.py
    ```

4. **Frontend Dashboard**
    ```bash
    cd frontend
    python3 -m http.server 8080 --bind 0.0.0.0
    # Access: http://localhost:8080 in browser
    ```

5. **Backend API**
    ```bash
    python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    ```

---

## 🏗️ System Architecture

- **Multi-agent Pipeline:** 
    - CSV Logs → Detection (BERT) → Correlation → TI Enrichment → Response Agent → Dashboard
- **Agents:**
    - Detection (bert_detection.py)
    - Correlation (correlation.py)
    - Threat Intel Enrichment (ti_enrichment.py)
    - Automated Response (response_agent.py)
- **Backend:** FastAPI (APIs), PostgreSQL integration
- **Frontend:** Vanilla JS, HTML, CSS (responsive, real-time)

---

## 🎯 Features

- **AI-Powered Log Classification** (8 threat types, 97–100% accuracy)
- **Intelligent Correlation** (3x alert reduction, less noise)
- **Threat Intelligence Enrichment** (risk, impacts, mitigations)
- **Automated Responses** (10+ action types, prioritization)
- **Modern Dashboard** (real-time charts, uploads, incident search)

---

## 📁 File Structure

- `agents/` — Core AI agents (BERT, correlation, enrichment, response)
- `backend/` — API, database, models
- `frontend/` — Dashboard (HTML/JS/CSS)
- `data/` — Synthetic and test log datasets
- `tests/` — Unit and integration tests
- `requirements.txt` — Python dependencies
- `README.md`, `LICENSE`
- Extensive documentation in `/docs` and technical deep dives in `STUDY.md`, `TRAINING_GUIDE.md`

---

## 📚 Documentation

- [START_HERE.md](START_HERE.md) – Setup Guide
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) – Production Guidance
- [TRAINING_GUIDE.md](docs/TRAINING_GUIDE.md) – Model Training
- [STUDY.md](docs/STUDY.md) – In-Depth Technical Study

---

## 🔧 API Endpoints

- **POST /analyze_logs**: Analyze uploaded CSV logs.
- **GET /incidents**: Incident summaries.
- **GET /stats**: Statistics for dashboard.

See [backend/main.py](backend/main.py) for detailed FastAPI implementation.

---

## 🧪 Testing & Performance

- **Run all tests:** `pytest tests/ -v`
- **Log throughput:** 550 logs/sec (GPU)
- **Incident reduction:** 2.5–3.0x

---

## 🤝 Contributions

PRs welcome! See "Contributing" in the README or open issues.

---

## 📄 License

Apache 2.0 – commercial use, modification, and distribution are allowed. See [LICENSE](LICENSE).

---

**Built by Tayanithaa and contributors. Combining advanced AI and practical SOC automation—built with PyTorch, Transformers, FastAPI, and love!**
