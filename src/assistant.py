import os
import json
import requests
import streamlit as st
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.translations import SUPPORTED_LANGUAGES, t
except ImportError:
    from translations import SUPPORTED_LANGUAGES, t
class StraviaAssistant:
    """Grounded decision assistant service for STRAVIA AI."""
    def __init__(self):
        self.api_key, self.provider = self._get_api_key_and_provider()
    def _get_api_key_and_provider(self):
        """Retrieves API key from environment variables or Streamlit secrets."""
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not gemini_key:
            try:
                if hasattr(st, "secrets"):
                    gemini_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
            except Exception:
                gemini_key = None
        if gemini_key:
            return gemini_key, "gemini"
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            try:
                if hasattr(st, "secrets"):
                    openai_key = st.secrets.get("OPENAI_API_KEY")
            except Exception:
                openai_key = None
        if openai_key:
            return openai_key, "openai"
        return None, None
    def has_active_api_key(self) -> bool:
        return self.api_key is not None
    def build_context_summary(self, pred_res: dict, alts_df, selected_product: str, selected_supplier: str, selected_year: int) -> str:
        """
        Constructs a compact structured text summary of current STRAVIA assessment state.
        This summary is passed to the LLM to ground its response without hallucination.
        """
        best_alt = "None identified"
        if alts_df is not None and not alts_df.empty:
            top_alt = alts_df.iloc[0]
            best_alt = f"{top_alt['Country']} (Match Score: {top_alt['Match Score']}/100, Risk Level: {top_alt['Risk Level']})"
        factors_str = "\n".join([f"- {f}" for f in pred_res.get("top_risk_factors", [])])
        context = f"""
STRAVIA AI CURRENT ASSESSMENT CONTEXT:
- Selected Product/Commodity: {selected_product}
- Selected Supplier Country: {selected_supplier}
- Target Year: {selected_year}
- Predicted Risk Level: {pred_res.get('predicted_risk_level', 'UNKNOWN')}
- Composite Risk Score: {pred_res.get('risk_score', 0):.1f} / 100
- Trade Value (USD 1,000): ${pred_res.get('trade_value_usd_k', 0):,.2f}
- Traded Quantity (Metric Tons): {pred_res.get('quantity_tons', 0):,.2f}
- Supplier Market Share: {pred_res.get('supplier_share', 0):.2f}%
- Supplier Concentration (HHI Index): {pred_res.get('supplier_hhi', 0):.1f}
- Year-over-Year Trade Change: {pred_res.get('yoy_trade_change', 0):+.2f}%
- Trade Volatility Index: {pred_res.get('trade_volatility', 0):.2f}
- GDELT External Event Count: {pred_res.get('recent_event_count', 0)} events recorded
- GDELT Conflict Event Count: {pred_res.get('conflict_event_count', 0)}
- GDELT Sanction/Restriction Count: {pred_res.get('sanction_event_count', 0)}
- Negative Event Intensity Score: {pred_res.get('negative_event_intensity', 0):.1f} / 100
- ML Model Used: {pred_res.get('model_used', 'XGBoost')}
- Class Probabilities: Low={pred_res.get('probabilities', {}).get('Low', 0):.1%}, Medium={pred_res.get('probabilities', {}).get('Medium', 0):.1%}, High={pred_res.get('probabilities', {}).get('High', 0):.1%}
- Top Contributing Risk Factors:
{factors_str}
- Top Recommended Alternative Supplier: {best_alt}
"""
        return context.strip()
    def generate_response(self, question: str, context_summary: str, lang_code: str = "en") -> str:
        """Generates grounded answer using configured LLM API."""
        if not self.has_active_api_key():
            return t("msg_no_api_key", lang=lang_code)
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, "English")
        system_instruction = f"""You are the STRAVIA AI Multimodal Decision Intelligence Assistant.
Your sole purpose is to answer the user's decision-support question strictly and exclusively based on the provided STRAVIA AI CURRENT ASSESSMENT CONTEXT.
CRITICAL GROUNDING RULES:
1. Do NOT invent, fabricate, or guess risk scores, trade numbers, supplier names, statistics, or dataset values.
2. If the user asks a question whose answer is not present in the context payload, respond explicitly: "I don't have sufficient data in the current STRAVIA assessment to determine that."
3. Respond clearly and concisely in {lang_name} ({lang_code}).
4. Preserve global technical terms (BACI, GDELT, HHI, XGBoost, Random Forest, Logistic Regression, ML, AI) and exact numerical values without altering them.
5. Provide helpful, professional decision-support explanations.
"""
        prompt = f"{system_instruction}\n\n{context_summary}\n\nUSER QUESTION: {question}\n\nASSISTANT ANSWER ({lang_name}):"
        try:
            if self.provider == "gemini":
                return self._call_gemini_api(prompt)
            elif self.provider == "openai":
                return self._call_openai_api(system_instruction, context_summary, question)
            else:
                return t("msg_no_api_key", lang=lang_code)
        except Exception as e:
            return f"Error communicating with AI assistant API: {str(e)}"
    def _call_gemini_api(self, full_prompt: str) -> str:
        """REST API call to Gemini API with robust model fallback list."""
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 800
            }
        }
        candidate_models = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-3.1-flash-lite"]
        last_error = "No active Gemini model responded."
        for model_name in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                else:
                    last_error = f"Model {model_name} HTTP {resp.status_code}: {resp.text[:150]}"
            except Exception as ex:
                last_error = f"Model {model_name} request error: {str(ex)}"
        raise Exception(last_error)
    def _call_openai_api(self, system_instruction: str, context_summary: str, question: str) -> str:
        """REST API call to OpenAI API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"{context_summary}\n\nQuestion: {question}"}
            ],
            "temperature": 0.2,
            "max_tokens": 800
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            raise Exception(f"OpenAI API returned status {resp.status_code}: {resp.text}")
if __name__ == "__main__":
    assistant = StraviaAssistant()
    print(f"Assistant Initialized. Active API Key Found: {assistant.has_active_api_key()} ({assistant.provider})")