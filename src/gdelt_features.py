import os
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
class GDELTFeatureEngineer:
    """Processes GDELT event records into structured country-level risk features."""
    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
    def compute_features(self, df_gdelt: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates GDELT event logs by country (Actor1/ActionGeo ISO3) and Year.
        """
        df = df_gdelt.copy()
        df["country_iso3"] = df["ActionGeo_CountryCode"].fillna(df["Actor1CountryCode"])
        df = df[df["country_iso3"].notna()].copy()
        df["neg_goldstein"] = np.where(df["GoldsteinScale"] < 0, np.abs(df["GoldsteinScale"]), 0.0)
        df["negative_event_impact"] = df["neg_goldstein"] * df["NumMentions"]
        df["is_conflict"] = (df["EventCategory"] == "Conflict").astype(int)
        df["is_instability"] = (df["EventCategory"] == "Political Instability").astype(int)
        df["is_disaster"] = (df["EventCategory"] == "Disaster").astype(int)
        df["is_sanction"] = (df["EventCategory"] == "Trade Restriction/Sanctions").astype(int)
        grouped = df.groupby(["country_iso3", "Year"]).agg(
            event_count=("GLOBALEVENTID", "count"),
            conflict_event_count=("is_conflict", "sum"),
            instability_event_count=("is_instability", "sum"),
            disaster_event_count=("is_disaster", "sum"),
            sanction_event_count=("is_sanction", "sum"),
            negative_event_intensity=("negative_event_impact", "sum"),
            avg_tone=("AvgTone", "mean")
        ).reset_index()
        max_intensity = grouped["negative_event_intensity"].max()
        if max_intensity > 0:
            grouped["negative_event_intensity"] = (grouped["negative_event_intensity"] / max_intensity) * 100.0
        grouped = grouped.sort_values(by=["country_iso3", "Year"]).reset_index(drop=True)
        grouped["prev_event_count"] = grouped.groupby("country_iso3")["event_count"].shift(1)
        grouped["event_trend"] = np.where(
            grouped["prev_event_count"].notna() & (grouped["prev_event_count"] > 0),
            ((grouped["event_count"] - grouped["prev_event_count"]) / grouped["prev_event_count"]) * 100.0,
            0.0
        )
        grouped.drop(columns=["prev_event_count"], inplace=True)
        grouped["recent_event_risk"] = np.where(
            (grouped["Year"] == 2024) & (
                (grouped["conflict_event_count"] > 3) |
                (grouped["sanction_event_count"] > 3) |
                (grouped["negative_event_intensity"] > 30)
            ),
            1.0,
            0.0
        )
        grouped.rename(columns={"Year": "year"}, inplace=True)
        out_path = os.path.join(self.processed_dir, "gdelt_features.csv")
        grouped.to_csv(out_path, index=False)
        print(f"GDELT Feature Engineering complete. Saved {len(grouped)} country-year risk records to {out_path}.")
        return grouped
if __name__ == "__main__":
    gdelt_raw_path = os.path.join(RAW_DIR, "gdelt_events_2022_2024.csv")
    if os.path.exists(gdelt_raw_path):
        df_gdelt = pd.read_csv(gdelt_raw_path)
        fe = GDELTFeatureEngineer()
        df_feats = fe.compute_features(df_gdelt)
    else:
        print("gdelt_events_2022_2024.csv not found. Run data_generator.py first.")