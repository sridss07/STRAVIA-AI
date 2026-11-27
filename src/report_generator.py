from datetime import datetime
from src.translations import t
class ExecutiveReportGenerator:
    """Generates structured executive decision reports."""
    @staticmethod
    def generate_markdown_report(
        pred_res: dict,
        alts_df,
        selected_product: str,
        selected_supplier: str,
        selected_year: int,
        lang_code: str = "en"
    ) -> str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        risk_label = pred_res.get("predicted_risk_level", "MEDIUM RISK")
        risk_score = pred_res.get("risk_score", 50.0)
        trade_val_m = pred_res.get("trade_value_usd_k", 0) / 1000.0
        quantity_tons = pred_res.get("quantity_tons", 0)
        hhi = pred_res.get("supplier_hhi", 0)
        share = pred_res.get("supplier_share", 0)
        yoy = pred_res.get("yoy_trade_change", 0)
        events = pred_res.get("recent_event_count", 0)
        conflicts = pred_res.get("conflict_event_count", 0)
        sanctions = pred_res.get("sanction_event_count", 0)
        model_used = pred_res.get("model_used", "XGBoost")
        best_alt_str = "None identified"
        if alts_df is not None and not alts_df.empty:
            top = alts_df.iloc[0]
            best_alt_str = f"{top['Country']} ({top['ISO Code']}) - Match Score: {top['Match Score']}/100"
        factors_md = "\n".join([f"- {f}" for f in pred_res.get("top_risk_factors", [])])
        alts_table_md = "No alternative suppliers identified."
        if alts_df is not None and not alts_df.empty:
            rows = []
            for _, r in alts_df.head(5).iterrows():
                rows.append(f"| {r['Rank']} | {r['Country']} | {r['ISO Code']} | {r['Trade Capability']} | ${r['Trade Volume ($k)']:,.2f} | {r['Risk Level']} | {r['Match Score']} |")
            alts_table_md = "| Rank | Country | ISO Code | Capability | Trade Volume ($k) | Risk Level | Match Score |\n|---|---|---|---|---|---|---|\n" + "\n".join(rows)
        report = f"""# 🛡️ STRAVIA AI – EXECUTIVE RISK BRIEFING REPORT
**Generated On:** {date_str}  
**Selected Commodity:** {selected_product}  
**Supplier Country:** {selected_supplier}  
**Target Year:** {selected_year}  
---
## 1. Executive Risk Assessment
- **Overall Predicted Risk Level:** **{risk_label}**
- **Composite Risk Score:** **{risk_score:.1f} / 100**
- **Machine Learning Model:** {model_used} (F1-Macro Optimized)
---
## 2. Key Bilateral Trade Metrics
| Metric Indicator | Value |
|---|---|
| Trade Value (USD) | ${trade_val_m:.2f} Million |
| Traded Quantity | {quantity_tons:,.2f} Metric Tons |
| Supplier Market Share | {share:.2f}% |
| Supplier HHI Concentration | {hhi:.1f} |
| Year-over-Year Trade Change | {yoy:+.2f}% |
| GDELT Event Signals | {events} total ({conflicts} conflicts, {sanctions} sanctions) |
---
## 3. Primary Risk Factor Analysis
{factors_md}
---
## 4. Recommended Alternative Suppliers
{alts_table_md}
---
## 5. Decision Intelligence Statement
> "The trade relationship for **{selected_product}** supplied by **{selected_supplier}** ({selected_year}) is classified as **{risk_label}** with a composite risk score of **{risk_score:.1f}/100**. Primary risk drivers include an HHI concentration index of {hhi:.0f} and {events} external GDELT geopolitical risk events. The top recommended alternative supplier is **{best_alt_str}**."
*STRAVIA AI Decision Intelligence Platform — Academic & Industry Supply Chain Resilience*
"""
        return report
if __name__ == "__main__":
    rep = ExecutiveReportGenerator.generate_markdown_report(
        {"predicted_risk_level": "HIGH RISK", "risk_score": 68.4, "trade_value_usd_k": 150000, "quantity_tons": 30000, "supplier_hhi": 3200, "supplier_share": 45, "yoy_trade_change": -18, "recent_event_count": 12, "conflict_event_count": 8, "sanction_event_count": 2, "top_risk_factors": ["High HHI", "Trade decline"], "model_used": "Random Forest"},
        None, "Copper", "Chile", 2024
    )
    print(rep[:300])