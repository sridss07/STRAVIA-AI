import os
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
class AlternativeSupplierAnalyzer:
    """Identifies and ranks candidate alternative supplier countries for raw materials."""
    def __init__(self, processed_dir: str = PROCESSED_DIR):
        self.processed_dir = processed_dir
    def get_alternative_suppliers(self, df_integrated: pd.DataFrame, product_name: str, current_supplier: str, year: int = 2024) -> pd.DataFrame:
        """
        Ranks alternative suppliers exporting the same product (excluding current_supplier).
        Scoring Method:
        Alternative Score = 0.50 * Trade_Capability_Norm (Volume) +
                            0.30 * (100 - Risk_Score) +
                            0.20 * (100 - Volatility_Norm)
        """
        df_prod = df_integrated[(df_integrated["product_name"] == product_name) & (df_integrated["year"] == year)].copy()
        if df_prod.empty:
            df_prod = df_integrated[df_integrated["product_name"] == product_name].copy()
        if df_prod.empty:
            return pd.DataFrame()
        grouped = df_prod.groupby(["exporter_name", "exporter_iso3"]).agg(
            trade_value_usd_k=("trade_value", "mean"),
            quantity_tons=("quantity", "mean"),
            risk_score=("risk_score", "mean"),
            risk_level=("risk_level", lambda x: x.mode()[0] if not x.empty else "MEDIUM"),
            trade_volatility=("trade_volatility", "mean"),
            recent_events=("event_count", "mean")
        ).reset_index()
        alt_suppliers = grouped[grouped["exporter_name"] != current_supplier].copy()
        if alt_suppliers.empty:
            return pd.DataFrame()
        max_val = alt_suppliers["trade_value_usd_k"].max()
        alt_suppliers["trade_capability_norm"] = np.where(
            max_val > 0,
            (alt_suppliers["trade_value_usd_k"] / max_val) * 100.0,
            50.0
        )
        alt_suppliers["volatility_norm"] = np.clip(alt_suppliers["trade_volatility"] * 100.0, 0, 100)
        alt_suppliers["alternative_score"] = (
            0.50 * alt_suppliers["trade_capability_norm"] +
            0.30 * (100.0 - alt_suppliers["risk_score"]) +
            0.20 * (100.0 - alt_suppliers["volatility_norm"])
        )
        alt_suppliers["alternative_score"] = np.round(alt_suppliers["alternative_score"], 1)
        alt_suppliers = alt_suppliers.sort_values(by="alternative_score", ascending=False).reset_index(drop=True)
        alt_suppliers["Rank"] = alt_suppliers.index + 1
        def label_capability(val):
            if val >= 70:
                return "High"
            elif val >= 35:
                return "Medium"
            else:
                return "Moderate"
        alt_suppliers["Trade Capability"] = alt_suppliers["trade_capability_norm"].apply(label_capability)
        result = alt_suppliers[[
            "Rank", "exporter_name", "exporter_iso3", "Trade Capability",
            "trade_value_usd_k", "risk_level", "risk_score", "alternative_score"
        ]].copy()
        result.rename(columns={
            "exporter_name": "Country",
            "exporter_iso3": "ISO Code",
            "trade_value_usd_k": "Trade Volume ($k)",
            "risk_level": "Risk Level",
            "risk_score": "Risk Score",
            "alternative_score": "Match Score"
        }, inplace=True)
        return result
if __name__ == "__main__":
    integrated_path = os.path.join(PROCESSED_DIR, "integrated_dataset.csv")
    if os.path.exists(integrated_path):
        df_int = pd.read_csv(integrated_path)
        analyzer = AlternativeSupplierAnalyzer()
        alts = analyzer.get_alternative_suppliers(df_int, "Copper", "Chile", 2024)
        print(alts.to_string(index=False))