import numpy as np
import pandas as pd
class ScenarioSimulator:
    @staticmethod
    def simulate_scenario(
        row: pd.Series,
        volume_change_pct: float = 0.0,
        conflict_surge_count: int = 0,
        sanction_surge_count: int = 0,
        hhi_change_pct: float = 0.0
    ) -> dict:
        """
        Applies user-defined perturbations to a baseline trade relationship:
        - volume_change_pct: e.g. -30.0 for a 30% drop in trade volume
        - conflict_surge_count: e.g. +5 additional geopolitical conflict events
        - sanction_surge_count: e.g. +3 additional trade restriction events
        - hhi_change_pct: e.g. +20.0 for a 20% increase in market concentration
        """
        base_hhi = float(row.get("supplier_hhi", 2500))
        base_yoy = float(row.get("yoy_trade_change", 0.0))
        base_volatility = float(row.get("trade_volatility", 0.1))
        base_intensity = float(row.get("negative_event_intensity", 10.0))
        base_conflicts = int(row.get("conflict_event_count", 0))
        base_sanctions = int(row.get("sanction_event_count", 0))
        sim_hhi = np.clip(base_hhi * (1.0 + hhi_change_pct / 100.0), 0, 10000)
        sim_yoy = base_yoy + volume_change_pct # drops YoY further
        sim_conflicts = base_conflicts + conflict_surge_count
        sim_sanctions = base_sanctions + sanction_surge_count
        sim_intensity = np.clip(base_intensity + (conflict_surge_count * 5.0) + (sanction_surge_count * 8.0), 0, 100)
        hhi_norm = np.clip(sim_hhi / 100.0, 0, 100)
        trade_decline = np.abs(sim_yoy) if sim_yoy < 0 else 0.0
        decline_norm = np.clip(trade_decline * 2.0, 0, 100)
        volatility_norm = np.clip(base_volatility * 100.0, 0, 100)
        intensity_norm = np.clip(sim_intensity, 0, 100)
        conflict_sanctions_norm = np.clip((sim_conflicts + sim_sanctions) * 10.0, 0, 100)
        sim_risk_score = (
            0.25 * hhi_norm +
            0.20 * decline_norm +
            0.15 * volatility_norm +
            0.20 * intensity_norm +
            0.20 * conflict_sanctions_norm
        )
        sim_risk_score = float(np.round(sim_risk_score, 1))
        if sim_risk_score < 35:
            sim_risk_level = "LOW RISK"
        elif sim_risk_score < 60:
            sim_risk_level = "MEDIUM RISK"
        else:
            sim_risk_level = "HIGH RISK"
        base_score = float(row.get("risk_score", 50.0))
        score_delta = round(sim_risk_score - base_score, 1)
        return {
            "baseline_risk_score": base_score,
            "baseline_risk_level": str(row.get("risk_level", "MEDIUM")),
            "simulated_risk_score": sim_risk_score,
            "simulated_risk_level": sim_risk_level,
            "score_delta": score_delta,
            "simulated_hhi": round(sim_hhi, 1),
            "simulated_yoy_change": round(sim_yoy, 1),
            "simulated_conflicts": sim_conflicts,
            "simulated_sanctions": sim_sanctions,
            "simulated_intensity": round(sim_intensity, 1)
        }
if __name__ == "__main__":
    sample_row = pd.Series({
        "supplier_hhi": 2800.0,
        "yoy_trade_change": -5.0,
        "trade_volatility": 0.15,
        "negative_event_intensity": 15.0,
        "conflict_event_count": 1,
        "sanction_event_count": 0,
        "risk_score": 42.5,
        "risk_level": "MEDIUM"
    })
    res = ScenarioSimulator.simulate_scenario(sample_row, volume_change_pct=-25.0, conflict_surge_count=4)
    print(res)