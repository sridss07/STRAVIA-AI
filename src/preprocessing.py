import os
import pandas as pd
import numpy as np
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
class DataPreprocessor:
    def __init__(self, raw_dir: str = RAW_DIR, processed_dir: str = PROCESSED_DIR):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        os.makedirs(self.processed_dir, exist_ok=True)
        self.country_lookup = self._load_country_lookup()
        self.product_lookup = self._load_product_lookup()
        self.validation_summary = {}
    def _load_country_lookup(self) -> pd.DataFrame:
        path = os.path.join(self.raw_dir, "country_codes.csv")
        if os.path.exists(path):
            return pd.read_csv(path)
        return pd.DataFrame()
    def _load_product_lookup(self) -> pd.DataFrame:
        path = os.path.join(self.raw_dir, "product_hs_codes.csv")
        if os.path.exists(path):
            return pd.read_csv(path)
        return pd.DataFrame()
    def load_baci_raw(self) -> pd.DataFrame:
        """Loads and concatenates raw BACI trade files for 2022-2024."""
        dfs = []
        for year in [2022, 2023, 2024]:
            file_path = os.path.join(self.raw_dir, f"baci_{year}.csv")
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                dfs.append(df)
            else:
                print(f"Warning: File {file_path} not found.")
        if not dfs:
            raise FileNotFoundError("No BACI raw files found in raw directory.")
        baci_combined = pd.concat(dfs, ignore_index=True)
        print(f"Loaded raw BACI data. Initial shape: {baci_combined.shape}")
        return baci_combined
    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes exact duplicate rows using drop_duplicates().

        PREPROCESSING RATIONALE:
        Only exact duplicate records are removed. Similar-looking trade records
        are retained because legitimate international trade declarations can have
        identical values across separate valid shipments or customs sub-entries.
        """
        initial_count = len(df)
        cleaned_df = df.drop_duplicates().copy()
        removed_count = initial_count - len(cleaned_df)
        print(f"Duplicate Removal: Removed {removed_count} exact duplicate rows. Retained {len(cleaned_df)} rows.")
        self.validation_summary["exact_duplicates_removed"] = removed_count
        return cleaned_df
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Imputes missing values rationally.
        For trade quantity (q), impute using median unit price (v/q) per commodity (k).
        """
        df_imputed = df.copy()
        missing_v = df_imputed["v"].isna().sum()
        missing_q = df_imputed["q"].isna().sum()
        if missing_v > 0:
            df_imputed["v"] = df_imputed.groupby("k")["v"].transform(lambda x: x.fillna(x.median()))
        if missing_q > 0:
            df_imputed["unit_price"] = np.where(
                df_imputed["q"] > 0, (df_imputed["v"] * 1000) / df_imputed["q"], np.nan
            )
            median_unit_prices = df_imputed.groupby("k")["unit_price"].transform("median")
            missing_mask = df_imputed["q"].isna()
            df_imputed.loc[missing_mask, "q"] = (
                df_imputed.loc[missing_mask, "v"] * 1000 / median_unit_prices.loc[missing_mask]
            )
            df_imputed.drop(columns=["unit_price"], inplace=True)
        print(f"Missing Value Imputation: Imputed {missing_v} missing 'v' values and {missing_q} missing 'q' values.")
        self.validation_summary["missing_v_imputed"] = int(missing_v)
        self.validation_summary["missing_q_imputed"] = int(missing_q)
        return df_imputed
    def validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies strict domain validation rules:
        1. Trade Value (v) >= 0
        2. Quantity (q) >= 0
        3. Exporter (i) and Importer (j) in valid country list
        4. Commodity (k) in valid product list
        5. Year (t) in [2022, 2023, 2024]
        """
        initial_len = len(df)
        valid_countries = set(self.country_lookup["country_code"].unique()) if not self.country_lookup.empty else set(df["i"].unique())
        valid_products = set(self.product_lookup["code"].unique()) if not self.product_lookup.empty else set(df["k"].unique())
        valid_mask = (
            (df["v"] >= 0) &
            (df["q"] >= 0) &
            (df["i"].isin(valid_countries)) &
            (df["j"].isin(valid_countries)) &
            (df["i"] != df["j"]) &
            (df["k"].isin(valid_products)) &
            (df["t"].isin([2022, 2023, 2024]))
        )
        validated_df = df[valid_mask].copy()
        dropped_records = initial_len - len(validated_df)
        print(f"Data Validation: Dropped {dropped_records} corrupted/invalid rows out of {initial_len}.")
        self.validation_summary["invalid_records_dropped"] = dropped_records
        return validated_df
    def analyze_and_handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        for col in ["v", "q"]:
            q25 = df_out[col].quantile(0.25)
            q75 = df_out[col].quantile(0.75)
            iqr = q75 - q25
            upper_bound = q75 + 3.0 * iqr # Using 3x IQR for extreme outliers
            p995 = df_out[col].quantile(0.995)
            num_outliers = (df_out[col] > upper_bound).sum()
            df_out[col] = np.where(df_out[col] > p995, p995, df_out[col])
            print(f"Outlier Analysis ({col}): Identified {num_outliers} extreme outliers (>3x IQR). Capped at 99.5th percentile ({p995:.2f}).")
            self.validation_summary[f"outliers_capped_{col}"] = int(num_outliers)
        return df_out
    def process_baci(self) -> pd.DataFrame:
        """Runs complete BACI preprocessing pipeline and saves cleaned dataset."""
        print("\n--- Starting BACI Data Preprocessing ---")
        df_raw = self.load_baci_raw()
        df_dedup = self.remove_duplicates(df_raw)
        df_imputed = self.handle_missing_values(df_dedup)
        df_validated = self.validate_data(df_imputed)
        df_cleaned = self.analyze_and_handle_outliers(df_validated)
        out_path = os.path.join(self.processed_dir, "baci_cleaned.csv")
        df_cleaned.to_csv(out_path, index=False)
        print(f"Saved cleaned BACI dataset with {len(df_cleaned)} rows to {out_path}.")
        return df_cleaned
    def process_gdelt_raw(self) -> pd.DataFrame:
        """Loads and cleans raw GDELT event data."""
        gdelt_path = os.path.join(self.raw_dir, "gdelt_events_2022_2024.csv")
        if not os.path.exists(gdelt_path):
            raise FileNotFoundError(f"GDELT file not found at {gdelt_path}")
        df_gdelt = pd.read_csv(gdelt_path)
        df_gdelt = df_gdelt.drop_duplicates()
        df_gdelt = df_gdelt[df_gdelt["Year"].isin([2022, 2023, 2024])]
        print(f"Cleaned raw GDELT event data. Records: {len(df_gdelt)}")
        return df_gdelt
if __name__ == "__main__":
    from data_generator import generate_reference_tables, generate_baci_data, generate_gdelt_data
    generate_reference_tables()
    generate_baci_data()
    generate_gdelt_data()
    preprocessor = DataPreprocessor()
    df_baci = preprocessor.process_baci()
    df_gdelt = preprocessor.process_gdelt_raw()
    print("Preprocessing completed successfully!")