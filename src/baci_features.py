import os
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
class BACIFeatureEngineer:
    """Computes trade risk features from cleaned BACI international trade data."""
    def __init__(self, processed_dir: str = PROCESSED_DIR):
        self.processed_dir = processed_dir
    def compute_features(self, df_baci: pd.DataFrame) -> pd.DataFrame:
        """
        Computes macroeconomic trade vulnerability features for each
        (Exporter, Importer, Commodity, Year) trade relationship.
        """
        df = df_baci.copy()
        group_imp_prod_year = df.groupby(["j", "k", "t"])["v"].transform("sum")
        df["total_importer_product_value"] = group_imp_prod_year
        df["supplier_share"] = np.where(
            df["total_importer_product_value"] > 0,
            (df["v"] / df["total_importer_product_value"]) * 100.0,
            0.0
        )
        supplier_counts = df.groupby(["j", "k", "t"])["i"].transform("nunique")
        df["supplier_count"] = supplier_counts
        df["share_squared"] = (df["supplier_share"]) ** 2
        hhi_series = df.groupby(["j", "k", "t"])["share_squared"].transform("sum")
        df["supplier_hhi"] = hhi_series
        df.drop(columns=["share_squared"], inplace=True)
        df["import_dependency"] = df["supplier_share"] / 100.0
        df["supplier_diversification"] = 1.0 - (df["supplier_hhi"] / 10000.0)
        total_bilateral_trade = df.groupby(["i", "j", "t"])["v"].transform("sum")
        df["product_importance"] = np.where(
            total_bilateral_trade > 0,
            (df["v"] / total_bilateral_trade) * 100.0,
            0.0
        )
        df = df.sort_values(by=["i", "j", "k", "t"]).reset_index(drop=True)
        df["prev_year_v"] = df.groupby(["i", "j", "k"])["v"].shift(1)
        df["yoy_trade_change"] = np.where(
            df["prev_year_v"].notna() & (df["prev_year_v"] > 0),
            ((df["v"] - df["prev_year_v"]) / df["prev_year_v"]) * 100.0,
            0.0
        )
        df.drop(columns=["prev_year_v"], inplace=True)
        volatility_series = df.groupby(["i", "j", "k"])["v"].transform(
            lambda x: (x.std() / (x.mean() + 1e-5)) if len(x) > 1 else 0.0
        )
        df["trade_volatility"] = volatility_series.fillna(0.0)
        df.rename(columns={
            "t": "year",
            "i": "exporter_code",
            "j": "importer_code",
            "k": "hs_code",
            "v": "trade_value",
            "q": "quantity"
        }, inplace=True)
        out_path = os.path.join(self.processed_dir, "baci_features.csv")
        df.to_csv(out_path, index=False)
        print(f"BACI Feature Engineering complete. Saved {len(df)} feature records to {out_path}.")
        return df
if __name__ == "__main__":
    baci_cleaned_path = os.path.join(PROCESSED_DIR, "baci_cleaned.csv")
    if os.path.exists(baci_cleaned_path):
        df_baci = pd.read_csv(baci_cleaned_path)
        fe = BACIFeatureEngineer()
        df_feats = fe.compute_features(df_baci)
    else:
        print("baci_cleaned.csv not found. Run preprocessing.py first.")