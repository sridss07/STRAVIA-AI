import os
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
class DataIntegrator:
    """Combines trade structure features with GDELT event risk indicators."""
    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.country_lookup = pd.read_csv(os.path.join(raw_dir, "country_codes.csv"))
        self.product_lookup = pd.read_csv(os.path.join(raw_dir, "product_hs_codes.csv"))
    def integrate(self, df_baci_feats: pd.DataFrame, df_gdelt_feats: pd.DataFrame) -> pd.DataFrame:
        """
        Joins BACI trade features with GDELT risk features by matching:
        - Exporter Country (M49 -> ISO3)
        - Year
        """
        code_to_iso3 = dict(zip(self.country_lookup["country_code"], self.country_lookup["country_iso3"]))
        code_to_name = dict(zip(self.country_lookup["country_code"], self.country_lookup["country_name"]))
        hs_to_name = dict(zip(self.product_lookup["code"], self.product_lookup["short_name"]))
        df_baci = df_baci_feats.copy()
        df_baci["exporter_iso3"] = df_baci["exporter_code"].map(code_to_iso3)
        df_baci["exporter_name"] = df_baci["exporter_code"].map(code_to_name)
        df_baci["importer_iso3"] = df_baci["importer_code"].map(code_to_iso3)
        df_baci["importer_name"] = df_baci["importer_code"].map(code_to_name)
        df_baci["product_name"] = df_baci["hs_code"].map(hs_to_name)
        integrated = pd.merge(
            df_baci,
            df_gdelt_feats,
            left_on=["exporter_iso3", "year"],
            right_on=["country_iso3", "year"],
            how="left"
        )
        event_cols = [
            "event_count", "conflict_event_count", "instability_event_count",
            "disaster_event_count", "sanction_event_count", "negative_event_intensity",
            "avg_tone", "event_trend", "recent_event_risk"
        ]
        for col in event_cols:
            if col in integrated.columns:
                integrated[col] = integrated[col].fillna(0.0)
        if "country_iso3" in integrated.columns:
            integrated.drop(columns=["country_iso3"], inplace=True)
        integrated = self._construct_risk_target(integrated)
        out_path = os.path.join(self.processed_dir, "integrated_dataset.csv")
        integrated.to_csv(out_path, index=False)
        print(f"Data Integration complete. Integrated dataset saved to {out_path} with {len(integrated)} rows.")
        return integrated
    def _construct_risk_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs an academically defensible, reproducible Risk Score (0-100) and Target Label:
        Risk Score = 0.25 * HHI_norm +
                     0.20 * Trade_Decline_norm +
                     0.15 * Volatility_norm +
                     0.20 * GDELT_Intensity_norm +
                     0.20 * Conflict_Sanction_norm
        Mapped Risk Levels:
        - LOW (0): Risk Score < 35
        - MEDIUM (1): 35 <= Risk Score < 60
        - HIGH (2): Risk Score >= 60
        """
        res = df.copy()
        hhi_norm = np.clip(res["supplier_hhi"] / 100.0, 0, 100)
        trade_decline = np.where(res["yoy_trade_change"] < 0, np.abs(res["yoy_trade_change"]), 0.0)
        trade_decline_norm = np.clip(trade_decline * 2.0, 0, 100)
        volatility_norm = np.clip(res["trade_volatility"] * 100.0, 0, 100)
        gdelt_intensity_norm = np.clip(res["negative_event_intensity"], 0, 100)
        conflict_sanctions = (res["conflict_event_count"] + res["sanction_event_count"]) * 10.0
        conflict_sanctions_norm = np.clip(conflict_sanctions, 0, 100)
        risk_score = (
            0.25 * hhi_norm +
            0.20 * trade_decline_norm +
            0.15 * volatility_norm +
            0.20 * gdelt_intensity_norm +
            0.20 * conflict_sanctions_norm
        )
        res["risk_score"] = np.round(risk_score, 2)
        conditions = [
            (res["risk_score"] < 35),
            (res["risk_score"] >= 35) & (res["risk_score"] < 60),
            (res["risk_score"] >= 60)
        ]
        choices_label = ["LOW", "MEDIUM", "HIGH"]
        choices_code = [0, 1, 2]
        res["risk_level"] = np.select(conditions, choices_label, default="MEDIUM")
        res["risk_class"] = np.select(conditions, choices_code, default=1)
        print("\nTarget Variable Distribution:")
        print(res["risk_level"].value_counts(normalize=True).map(lambda x: f"{x*100:.1f}%"))
        return res
if __name__ == "__main__":
    from baci_features import BACIFeatureEngineer
    from gdelt_features import GDELTFeatureEngineer
    baci_path = os.path.join(PROCESSED_DIR, "baci_cleaned.csv")
    gdelt_path = os.path.join(RAW_DIR, "gdelt_events_2022_2024.csv")
    if os.path.exists(baci_path) and os.path.exists(gdelt_path):
        df_baci = pd.read_csv(baci_path)
        df_gdelt = pd.read_csv(gdelt_path)
        baci_fe = BACIFeatureEngineer()
        gdelt_fe = GDELTFeatureEngineer()
        df_baci_feats = baci_fe.compute_features(df_baci)
        df_gdelt_feats = gdelt_fe.compute_features(df_gdelt)
        integrator = DataIntegrator()
        integrated = integrator.integrate(df_baci_feats, df_gdelt_feats)
    else:
        print("Required processed files not found. Run preprocessing.py first.")