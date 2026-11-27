
# STRAVIA AI – Multimodal Global Supply Chain Resilience Platform



<p align="center">
  <a href="https://stravia-ai.streamlit.app/">
    <img src="https://img.shields.io/badge/LIVE_DEMO-Launch_Web_App-brightgreen?style=for-the-badge" alt="Live Demo">
  </a>
  <a href="https://github.com/sridss07/STRAVIA-AI/raw/refs/heads/main/STRAVIA_AI.apk">
    <img src="https://img.shields.io/badge/ANDROID-Download_APK-blue?style=for-the-badge&logo=android" alt="Download APK">
  </a>
  <a href="https://github.com/sridss07/STRAVIA-AI">
    <img src="https://img.shields.io/badge/GITHUB-View_Source_Code-black?style=for-the-badge&logo=github" alt="GitHub">
  </a>
</p>



## 🚀 Live Application

**Live Demo:** https://stravia-ai.streamlit.app/

**GitHub Repository:** https://github.com/sridss07/STRAVIA-AI

---

## 📌 Project Overview

STRAVIA AI is an AI-powered global supply chain resilience platform designed to analyze trade patterns, assess supplier risks, and support informed sourcing decisions.

The platform integrates machine learning, trade-related indicators, geopolitical event signals, and interactive visualizations to help identify potential supply chain vulnerabilities and explore alternative suppliers.

It provides an integrated analytical environment with supplier risk assessment, alternative supplier analysis, early warning insights, and AI-assisted recommendations.

## 🎯 Problem Statement

Global supply chains face several challenges, including geopolitical instability, trade restrictions, market volatility, and supplier dependency.

Traditional approaches may not provide a unified view of these risk factors.

STRAVIA AI addresses this challenge by combining trade-related data, risk indicators, and machine learning techniques into an interactive platform for supply chain risk analysis.

## ✨ Key Features

- **Supplier Risk Assessment:** Analyzes supplier and country-level risk indicators.
- **Machine Learning Predictions:** Classifies supply chain risk categories using trained ML models.
- **Alternative Supplier Analysis:** Helps explore alternative sourcing options.
- **Global Risk Visualization:** Interactive visualizations using Plotly.
- **Early Warning Radar:** Presents risk signals for proactive analysis.
- **AI Assistant:** Gemini-powered assistance for supply chain-related queries.
- **Executive Reports:** Generates downloadable analytical reports.
- **Multilingual Support:** Supports interaction in seven languages.
- **User Authentication:** Includes authentication and password hashing.
- **Subscription Management:** Provides Free, Pro, and Enterprise subscription tiers.

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Dashboard | Streamlit |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, XGBoost |
| Data Visualization | Plotly, Matplotlib |
| Database | SQLite |
| Generative AI | Google Gemini API |
| Security | PBKDF2-SHA256, Rate Limiting |
| Deployment | Streamlit Community Cloud |
| Version Control | Git, GitHub |

## 🧠 Machine Learning Approach

The platform uses machine learning classification techniques to analyze engineered supply chain risk features and classify risk categories.

The evaluated models include:

1. Logistic Regression
2. Random Forest
3. XGBoost

### Model Performance

| Model | Accuracy | Macro F1-Score |
|---|---:|---:|
| Logistic Regression | 66.12% | Not reported |
| Random Forest | 77.05% | 66.58% |
| XGBoost | 78.69% | 65.73% |

**Model Evaluation:**

- XGBoost achieved the highest classification accuracy.
- Random Forest achieved the highest Macro F1-score among the evaluated models.
- Model selection depends on the evaluation objective and the importance of balanced class performance.

### Feature Engineering

The analytical pipeline processes trade-related indicators and geopolitical event signals to generate features for machine learning.

The project also incorporates a composite risk-scoring approach that combines trade capability, risk, and volatility indicators.

## 📊 Dataset and Data Processing

The platform uses BACI-style trade data and GDELT-style geopolitical event data in its analytical workflow.

The project includes data generation, integration, preprocessing, and feature engineering modules to prepare records for machine learning analysis.

**Data Limitation:** The current implementation uses synthetically generated BACI-style and GDELT-style data. It does not represent direct live ingestion from the original BACI or GDELT services. Therefore, predictions and risk assessments should be interpreted as prototype analytical outputs rather than verified real-world forecasts.

## 🏗️ Project Structure

```text
STRAVIA-AI/
│
├── app.py
├── requirements.txt
│
├── data/
│
├── models/
│
├── src/
│   ├── __init__.py
│   ├── alternative_suppliers.py
│   ├── assistant.py
│   ├── auth.py
│   ├── baci_features.py
│   ├── data_generator.py
│   ├── data_integration.py
│   ├── database.py
│   ├── gdelt_features.py
│   ├── ml_pipeline.py
│   ├── preprocessing.py
│   ├── report_generator.py
│   ├── risk_prediction.py
│   ├── simulator.py
│   └── subscriptions.py
│
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/sridss07/STRAVIA-AI.git

cd STRAVIA-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Secrets

The Gemini API key is required for the AI assistant functionality.

Create the following file for local development:

`.streamlit/secrets.toml`

Add your API key:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

For Streamlit Community Cloud, configure the API key under the application's Settings → Secrets section.

**Important:** Never upload API keys, passwords, or sensitive database files to a public GitHub repository.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will normally be available at:

```text
http://localhost:8501
```

## 🔐 Security Features

- Password hashing using PBKDF2-SHA256.
- Rate limiting for authentication workflows.
- Secure API key configuration using Streamlit secrets.
- SQLite-based application data management.

## ☁️ Deployment

STRAVIA AI is deployed using **Streamlit Community Cloud** and connected to its GitHub repository.

**Live Application:** https://stravia-ai.streamlit.app/

## 🔮 Future Enhancements

- Integration with live and verified global trade datasets.
- Real-time geopolitical event ingestion.
- Improved predictive performance using larger datasets.
- Advanced supplier network analysis.
- Enhanced model explainability.
- Expanded forecasting and scenario simulation capabilities.

## 💡 Project Highlights

This project demonstrates practical implementation of:

- Data processing and feature engineering.
- Machine learning model development and evaluation.
- AI-powered analytical workflows.
- Interactive dashboard development.
- Database integration.
- Application security.
- Cloud deployment and version control.

---

<p align="center">
  <b>STRAVIA AI – Turning Global Supply Chain Data into Actionable Risk Insights.</b>
</p>
