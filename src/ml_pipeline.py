import os
import json
import joblib
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
)
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
TARGET_COLUMN = "risk_class" 
class MLPipeline:
    def __init__(self, processed_dir: str = PROCESSED_DIR, models_dir: str = MODELS_DIR):
        self.processed_dir = processed_dir
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        self.scaler = StandardScaler()
        self.models = {}
        self.metrics = {}
        self.best_model_name = None
    def load_data(self) -> pd.DataFrame:
        path = os.path.join(self.processed_dir, "integrated_dataset.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Integrated dataset not found at {path}")
        return pd.read_csv(path)
    def prepare_time_split(self, df: pd.DataFrame):
        """
        Time-aware split:
        - Train set: 2022 & 2023
        - Test set: 2024
        """
        train_mask = df["year"].isin([2022, 2023])
        test_mask = df["year"] == 2024
        X_train = df.loc[train_mask, FEATURE_COLUMNS].copy()
        y_train = df.loc[train_mask, TARGET_COLUMN].copy()
        X_test = df.loc[test_mask, FEATURE_COLUMNS].copy()
        y_test = df.loc[test_mask, TARGET_COLUMN].copy()
        print(f"Time-aware split complete: Train (2022-2023) = {len(X_train)} samples, Test (2024) = {len(X_test)} samples.")
        return X_train, y_train, X_test, y_test
    def train_and_evaluate(self):
        df = self.load_data()
        X_train, y_train, X_test, y_test = self.prepare_time_split(df)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        joblib.dump(self.scaler, os.path.join(self.models_dir, "scaler.joblib"))
        candidate_models = {
            "Logistic Regression": (
                LogisticRegression(max_iter=1000, random_state=42, C=1.0),
                X_train_scaled,
                X_test_scaled
            ),
            "Random Forest": (
                RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42),
                X_train,
                X_test
            ),
            "XGBoost": (
                XGBClassifier(n_estimators=150, max_depth=5, learning_rate=0.08, random_state=42, eval_metric="mlogloss"),
                X_train,
                X_test
            )
        }
        best_f1 = -1.0
        best_name = None
        print("\n================ MODEL TRAINING & EVALUATION ================")
        for name, (model, X_tr, X_te) in candidate_models.items():
            model.fit(X_tr, y_train)
            y_pred = model.predict(X_te)
            acc = float(accuracy_score(y_test, y_pred))
            prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
            rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
            f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
            f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
            cm = confusion_matrix(y_test, y_pred).tolist()
            self.metrics[name] = {
                "accuracy": round(acc, 4),
                "precision_macro": round(prec_macro, 4),
                "recall_macro": round(rec_macro, 4),
                "f1_macro": round(f1_macro, 4),
                "f1_weighted": round(f1_weighted, 4),
                "confusion_matrix": cm
            }
            self.models[name] = model
            model_filename = name.lower().replace(" ", "_") + ".joblib"
            joblib.dump(model, os.path.join(self.models_dir, model_filename))
            print(f"\nModel: {name}")
            print(f"  Accuracy:    {acc:.4f}")
            print(f"  Precision:   {prec_macro:.4f}")
            print(f"  Recall:      {rec_macro:.4f}")
            print(f"  F1-Score:    {f1_macro:.4f} (Macro)")
            if f1_macro > best_f1:
                best_f1 = f1_macro
                best_name = name
        self.best_model_name = best_name
        best_model = self.models[best_name]
        joblib.dump(best_model, os.path.join(self.models_dir, "best_model.joblib"))
        summary = {
            "best_model": self.best_model_name,
            "feature_columns": FEATURE_COLUMNS,
            "metrics": self.metrics
        }
        with open(os.path.join(self.models_dir, "model_metrics.json"), "w") as f:
            json.dump(summary, f, indent=4)
        print(f"\n>>> BEST MODEL SELECTED: {self.best_model_name} (Macro F1-Score: {best_f1:.4f}) <<<")
        print("Model training pipeline complete. Saved artifacts to models/ directory.")
        return summary
if __name__ == "__main__":
    from data_generator import generate_reference_tables, generate_baci_data, generate_gdelt_data
    from preprocessing import DataPreprocessor
    from baci_features import BACIFeatureEngineer
    from gdelt_features import GDELTFeatureEngineer
    from data_integration import DataIntegrator
    generate_reference_tables()
    generate_baci_data()
    generate_gdelt_data()
    preprocessor = DataPreprocessor()
    df_baci = preprocessor.process_baci()
    df_gdelt = preprocessor.process_gdelt_raw()
    baci_fe = BACIFeatureEngineer()
    gdelt_fe = GDELTFeatureEngineer()
    df_baci_feats = baci_fe.compute_features(df_baci)
    df_gdelt_feats = gdelt_fe.compute_features(df_gdelt)
    integrator = DataIntegrator()
    df_integrated = integrator.integrate(df_baci_feats, df_gdelt_feats)
    pipeline = MLPipeline()
    metrics_summary = pipeline.train_and_evaluate()