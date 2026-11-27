import os
import random
import pandas as pd
import numpy as np
DATA_RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
COUNTRIES = [
    {"country_code": 152, "country_iso3": "CHL", "country_name": "Chile"},
    {"country_code": 36, "country_iso3": "AUS", "country_name": "Australia"},
    {"country_code": 180, "country_iso3": "COD", "country_name": "Democratic Republic of the Congo"},
    {"country_code": 156, "country_iso3": "CHN", "country_name": "China"},
    {"country_code": 840, "country_iso3": "USA", "country_name": "United States"},
    {"country_code": 276, "country_iso3": "DEU", "country_name": "Germany"},
    {"country_code": 356, "country_iso3": "IND", "country_name": "India"},
    {"country_code": 604, "country_iso3": "PER", "country_name": "Peru"},
    {"country_code": 360, "country_iso3": "IDN", "country_name": "Indonesia"},
    {"country_code": 76, "country_iso3": "BRA", "country_name": "Brazil"},
    {"country_code": 643, "country_iso3": "RUS", "country_name": "Russia"},
    {"country_code": 710, "country_iso3": "ZAF", "country_name": "South Africa"},
    {"country_code": 682, "country_iso3": "SAU", "country_name": "Saudi Arabia"},
    {"country_code": 124, "country_iso3": "CAN", "country_name": "Canada"},
    {"country_code": 392, "country_iso3": "JPN", "country_name": "Japan"},
    {"country_code": 410, "country_iso3": "KOR", "country_name": "South Korea"},
]
PRODUCTS = [
    {"code": 260300, "description": "Copper Ores & Concentrates", "short_name": "Copper"},
    {"code": 283691, "description": "Lithium Carbonates", "short_name": "Lithium"},
    {"code": 810520, "description": "Cobalt Mattes & Intermediate Products", "short_name": "Cobalt"},
    {"code": 750210, "description": "Unwrought Nickel", "short_name": "Nickel"},
    {"code": 760110, "description": "Unwrought Aluminum", "short_name": "Aluminum"},
    {"code": 280530, "description": "Rare-Earth Metals", "short_name": "Rare Earths"},
    {"code": 260111, "description": "Iron Ores Non-Agglomerated", "short_name": "Iron Ore"},
    {"code": 270900, "description": "Crude Petroleum Oils", "short_name": "Crude Oil"},
]
def generate_reference_tables():
    """Generates country and product reference tables."""
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    df_countries = pd.DataFrame(COUNTRIES)
    df_countries.to_csv(os.path.join(DATA_RAW_DIR, "country_codes.csv"), index=False)
    df_products = pd.DataFrame(PRODUCTS)
    df_products.to_csv(os.path.join(DATA_RAW_DIR, "product_hs_codes.csv"), index=False)
    print("Reference lookup tables created successfully.")
def generate_baci_data():
    """
    Generates realistic BACI trade records for 2022, 2023, 2024.
    Fields: t (year), i (exporter code), j (importer code), k (HS code), v (value in 1000 USD), q (qty in tons)
    """
    np.random.seed(42)
    years = [2022, 2023, 2024]
    exporters = [c["country_code"] for c in COUNTRIES]
    importers = [840, 156, 276, 356, 392, 410] # USA, CHN, DEU, IND, JPN, KOR
    product_codes = [p["code"] for p in PRODUCTS]
    baci_records = []
    dominant_exporters = {
        260300: [152, 604, 36, 156],         # Copper: Chile, Peru, Australia, China
        283691: [152, 36, 76, 156],         # Lithium: Chile, Australia, Brazil, China
        810520: [180, 710, 156, 124],         # Cobalt: DRC, South Africa, China, Canada
        750210: [360, 643, 36, 124],         # Nickel: Indonesia, Russia, Australia, Canada
        760110: [156, 643, 124, 356],         # Aluminum: China, Russia, Canada, India
        280530: [156, 36, 840, 356],         # Rare Earths: China, Australia, USA, India
        260111: [36, 76, 710, 604],         # Iron Ore: Australia, Brazil, South Africa, Peru
        270900: [682, 643, 840, 124],         # Crude Oil: Saudi Arabia, Russia, USA, Canada
    }
    for year in years:
        year_records = []
        for p_code in product_codes:
            exp_list = dominant_exporters.get(p_code, exporters[:4])
            for exp in exp_list:
                for imp in importers:
                    if exp == imp:
                        continue
                    base_val = np.random.uniform(5000, 400000)
                    if exp in [180, 643] and year == 2024:
                        trend_factor = np.random.uniform(0.4, 0.7)
                    elif exp in [152, 36] and year == 2024:
                        trend_factor = np.random.uniform(0.9, 1.25)
                    else:
                        trend_factor = np.random.uniform(0.85, 1.15)
                    trade_val = base_val * trend_factor
                    price_per_ton = np.random.uniform(800, 12000)
                    quantity_tons = trade_val * 1000 / price_per_ton
                    q_val = quantity_tons if np.random.rand() > 0.04 else np.nan
                    year_records.append({
                        "t": year,
                        "i": exp,
                        "j": imp,
                        "k": p_code,
                        "v": round(trade_val, 2),
                        "q": round(q_val, 2) if not np.isnan(q_val) else np.nan
                    })
        num_duplicates = int(len(year_records) * 0.005)
        duplicates = random.choices(year_records, k=num_duplicates)
        year_records.extend(duplicates)
        if year == 2024:
            year_records.append({
                "t": 2024,
                "i": 152,
                "j": 840,
                "k": 260300,
                "v": -50.0,
                "q": 100.0
            })
        df_year = pd.DataFrame(year_records)
        filename = f"baci_{year}.csv"
        df_year.to_csv(os.path.join(DATA_RAW_DIR, filename), index=False)
        print(f"Generated {filename} with {len(df_year)} records.")
def generate_gdelt_data():
    """
    Generates realistic GDELT event data (2022-2024) containing country risk signals.
    Fields: GLOBALEVENTID, SQLDATE, Year, Month, Actor1CountryCode, Actor2CountryCode,
            EventCode, EventRootCode, GoldsteinScale, NumMentions, NumSources, NumArticles,
            AvgTone, ActionGeo_CountryCode, EventCategory
    """
    np.random.seed(42)
    random.seed(42)
    country_iso3_list = [c["country_iso3"] for c in COUNTRIES]
    risk_profiles = {
        "COD": {"conflict": 0.40, "instability": 0.30, "disaster": 0.10, "sanction": 0.10, "general": 0.10, "avg_tone": -6.5},
        "RUS": {"conflict": 0.35, "instability": 0.20, "disaster": 0.05, "sanction": 0.35, "general": 0.05, "avg_tone": -7.0},
        "CHL": {"conflict": 0.05, "instability": 0.20, "disaster": 0.35, "sanction": 0.05, "general": 0.35, "avg_tone": -2.5},
        "PER": {"conflict": 0.10, "instability": 0.40, "disaster": 0.20, "sanction": 0.05, "general": 0.25, "avg_tone": -4.0},
        "ZAF": {"conflict": 0.15, "instability": 0.35, "disaster": 0.15, "sanction": 0.05, "general": 0.30, "avg_tone": -3.5},
        "IDN": {"conflict": 0.10, "instability": 0.15, "disaster": 0.35, "sanction": 0.10, "general": 0.30, "avg_tone": -2.0},
        "AUS": {"conflict": 0.02, "instability": 0.05, "disaster": 0.20, "sanction": 0.01, "general": 0.72, "avg_tone": 1.5},
        "USA": {"conflict": 0.05, "instability": 0.10, "disaster": 0.15, "sanction": 0.10, "general": 0.60, "avg_tone": 0.5},
        "DEU": {"conflict": 0.02, "instability": 0.05, "disaster": 0.10, "sanction": 0.05, "general": 0.78, "avg_tone": 1.0},
        "CHN": {"conflict": 0.15, "instability": 0.10, "disaster": 0.15, "sanction": 0.25, "general": 0.35, "avg_tone": -3.0},
    }
    default_profile = {"conflict": 0.05, "instability": 0.10, "disaster": 0.10, "sanction": 0.05, "general": 0.70, "avg_tone": 0.0}
    event_records = []
    event_id = 100000000
    categories = ["Conflict", "Political Instability", "Disaster", "Trade Restriction/Sanctions", "General"]
    for year in [2022, 2023, 2024]:
        for month in range(1, 13):
            for iso in country_iso3_list:
                profile = risk_profiles.get(iso, default_profile)
                n_events = int(np.random.poisson(lam=15 if iso in ["COD", "RUS", "PER", "CHL"] else 8))
                for _ in range(n_events):
                    event_id += 1
                    cat = random.choices(
                        categories,
                        weights=[profile["conflict"], profile["instability"], profile["disaster"], profile["sanction"], profile["general"]]
                    )[0]
                    if cat == "Conflict":
                        goldstein = np.random.uniform(-10.0, -4.0)
                        root_code = 18 if random.random() > 0.5 else 19
                    elif cat == "Political Instability":
                        goldstein = np.random.uniform(-7.0, -2.0)
                        root_code = 14 # Protest
                    elif cat == "Disaster":
                        goldstein = np.random.uniform(-6.0, -1.0)
                        root_code = 2
                    elif cat == "Trade Restriction/Sanctions":
                        goldstein = np.random.uniform(-8.0, -3.0)
                        root_code = 13 # Threat / Sanctions
                    else:
                        goldstein = np.random.uniform(-2.0, 5.0)
                        root_code = 5 # Co-operate
                    avg_tone = np.random.normal(loc=profile["avg_tone"], scale=2.5)
                    event_records.append({
                        "GLOBALEVENTID": event_id,
                        "SQLDATE": int(f"{year}{month:02d}{random.randint(1, 28):02d}"),
                        "Year": year,
                        "Month": month,
                        "Actor1CountryCode": iso,
                        "Actor2CountryCode": random.choice(country_iso3_list),
                        "EventCode": f"{root_code:02d}0",
                        "EventRootCode": f"{root_code:02d}",
                        "GoldsteinScale": round(goldstein, 2),
                        "NumMentions": int(np.random.exponential(scale=10) + 1),
                        "NumSources": int(np.random.randint(1, 15)),
                        "NumArticles": int(np.random.randint(1, 20)),
                        "AvgTone": round(avg_tone, 2),
                        "ActionGeo_CountryCode": iso,
                        "EventCategory": cat
                    })
    df_gdelt = pd.DataFrame(event_records)
    gdelt_path = os.path.join(DATA_RAW_DIR, "gdelt_events_2022_2024.csv")
    df_gdelt.to_csv(gdelt_path, index=False)
    print(f"Generated GDELT dataset with {len(df_gdelt)} records at {gdelt_path}.")
if __name__ == "__main__":
    generate_reference_tables()
    generate_baci_data()
    generate_gdelt_data()
    print("All raw datasets generated successfully!")