import os
import json
import joblib
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
FEATURE_COLUMNS = [
    "trade_value", "quantity", "supplier_count", "supplier_hhi", "supplier_share",
    "yoy_trade_change", "trade_volatility", "import_dependency", "supplier_diversification",
    "product_importance", "event_count", "conflict_event_count", "instability_event_count",
    "disaster_event_count", "sanction_event_count", "negative_event_intensity",
    "event_trend", "recent_event_risk"
]
class RiskPredictor:
    """Predicts risk levels and explains major contributing risk factors."""
    def __init__(self, models_dir: str = MODELS_DIR, processed_dir: str = PROCESSED_DIR):
        self.models_dir = models_dir
        self.processed_dir = processed_dir
        self.model, self.scaler, self.metrics_info = self._load_artifacts()
    def _load_artifacts(self):
        metrics_path = os.path.join(self.models_dir, "model_metrics.json")
        if not os.path.exists(metrics_path):
            raise FileNotFoundError("Model metrics not found. Run ml_pipeline.py first.")
        with open(metrics_path, "r") as f:
            metrics_info = json.load(f)
        best_model_path = os.path.join(self.models_dir, "best_model.joblib")
        model = joblib.load(best_model_path)
        scaler_path = os.path.join(self.models_dir, "scaler.joblib")
        scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None
        return model, scaler, metrics_info
    def predict_relationship(self, df_integrated: pd.DataFrame, product_name: str, supplier_name: str, year: int = 2024):
        """
        Extracts feature vector for a selected product, supplier country, and year,
        predicts risk level, and generates structured risk explanation.
        """
        mask = (
            (df_integrated["product_name"] == product_name) &
            (df_integrated["exporter_name"] == supplier_name) &
            (df_integrated["year"] == year)
        )
        sub_df = df_integrated[mask]
        if sub_df.empty:
            mask = (df_integrated["product_name"] == product_name) & (df_integrated["exporter_name"] == supplier_name)
            sub_df = df_integrated[mask]
        if sub_df.empty:
            return {
                "status": "error",
                "message": f"No trade record found for Product '{product_name}' and Supplier '{supplier_name}'."
            }
        row = sub_df.iloc[0]
        X_vec = pd.DataFrame([row[FEATURE_COLUMNS]])
        if self.metrics_info.get("best_model") == "Logistic Regression" and self.scaler is not None:
            X_input = self.scaler.transform(X_vec)
        else:
            X_input = X_vec
        pred_class = int(self.model.predict(X_input)[0])
        class_labels = {0: "LOW RISK", 1: "MEDIUM RISK", 2: "HIGH RISK"}
        predicted_label = class_labels.get(pred_class, "MEDIUM RISK")
        probs = [0.33, 0.33, 0.34]
        if hasattr(self.model, "predict_proba"):
            probs = [round(float(p), 4) for p in self.model.predict_proba(X_input)[0]]
        factors = self._explain_risk_factors(row)
        return {
            "status": "success",
            "product_name": product_name,
            "supplier_name": supplier_name,
            "year": int(row["year"]),
            "predicted_risk_level": predicted_label,
            "risk_score": float(row.get("risk_score", 50.0)),
            "probabilities": {
                "Low": probs[0] if len(probs) > 0 else 0,
                "Medium": probs[1] if len(probs) > 1 else 0,
                "High": probs[2] if len(probs) > 2 else 0
            },
            "model_used": self.metrics_info.get("best_model", "XGBoost"),
            "trade_value_usd_k": float(row["trade_value"]),
            "quantity_tons": float(row["quantity"]),
            "supplier_hhi": float(row["supplier_hhi"]),
            "supplier_share": float(row["supplier_share"]),
            "yoy_trade_change": float(row["yoy_trade_change"]),
            "trade_volatility": float(row["trade_volatility"]),
            "recent_event_count": int(row["event_count"]),
            "conflict_event_count": int(row["conflict_event_count"]),
            "sanction_event_count": int(row["sanction_event_count"]),
            "negative_event_intensity": float(row["negative_event_intensity"]),
            "top_risk_factors": factors
        }
    def _explain_risk_factors(self, row: pd.Series) -> list:
        factors = []
        if row["supplier_hhi"] > 2500:
            factors.append("High supplier concentration (HHI > 2500) indicates limited market alternative supply.")
        if row["yoy_trade_change"] < -15.0:
            factors.append(f"Significant trade decline of {row['yoy_trade_change']:.1f}% compared to previous period.")
        if row["conflict_event_count"] > 2:
            factors.append(f"Geopolitical conflict activity detected ({int(row['conflict_event_count'])} relevant conflict events recorded).")
        if row["sanction_event_count"] > 2:
            factors.append(f"Trade restriction & sanction risks present ({int(row['sanction_event_count'])} restriction signals).")
        if row["negative_event_intensity"] > 25.0:
            factors.append(f"Elevated negative news event intensity (Score: {row['negative_event_intensity']:.1f}).")
        if row["import_dependency"] > 0.40:
            factors.append(f"High import dependency on this supplier ({row['supplier_share']:.1f}% market share).")
        if not factors:
            factors.append("Supplier exhibits stable historical trade volume and minimal external geopolitical event signals.")
        return factors
if __name__ == "__main__":
    integrated_path = os.path.join(PROCESSED_DIR, "integrated_dataset.csv")
    if os.path.exists(integrated_path):
        df_int = pd.read_csv(integrated_path)
        predictor = RiskPredictor()
        res = predictor.predict_relationship(df_int, "Copper", "Chile", 2024)
        print(json.dumps(res, indent=2))
    else:
        print("Integrated dataset not found. Run data_integration.py first.")