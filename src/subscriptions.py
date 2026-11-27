from datetime import datetime
from typing import Dict, Any, List, Optional
from src.database import get_db_connection
PLANS = {
    "free": {
        "name": "STRAVIA Free",
        "price_display": "₹0 / month",
        "price_amount": 0,
        "badge": "FREE",
        "color": "#64748B",
        "description": "Essential raw-material risk scoring and trade overview."
    },
    "pro": {
        "name": "STRAVIA Pro",
        "price_display": "₹499 / month",
        "price_amount": 499,
        "badge": "PRO",
        "color": "#0F766E",
        "description": "Full decision intelligence, SHAP explanations, alternative suppliers & report export."
    },
    "enterprise": {
        "name": "STRAVIA Enterprise",
        "price_display": "Custom Pricing",
        "price_amount": 4999,
        "badge": "ENTERPRISE",
        "color": "#1E3A8A",
        "description": "Organization-level risk monitoring, multi-user collaboration & enterprise reports."
    }
}
FEATURE_ROSTER = {
    "basic_risk_prediction": ["free", "pro", "enterprise"],
    "basic_trade_metrics": ["free", "pro", "enterprise"],
    "basic_event_count": ["free", "pro", "enterprise"],
    "basic_heatmap": ["free", "pro", "enterprise"],
    "limited_chatbot": ["free", "pro", "enterprise"],
    "detailed_risk_explanation": ["pro", "enterprise"],
    "advanced_gdelt_scatter": ["pro", "enterprise"],
    "hhi_supplier_dependency": ["pro", "enterprise"],
    "alternative_suppliers": ["pro", "enterprise"],
    "model_benchmark": ["pro", "enterprise"],
    "executive_report_export": ["pro", "enterprise"],
    "extended_chatbot": ["pro", "enterprise"],
    "early_warning_radar": ["pro", "enterprise"],
    "enterprise_team_access": ["enterprise"],
    "enterprise_custom_branding": ["enterprise"]
}
class SubscriptionManager:
    """Server-side source of truth for user subscription state and feature authorization."""
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
    def get_user_plan(self, user_id: int) -> str:
        """Queries the database for the user's current active subscription plan."""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT plan FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ORDER BY subscription_id DESC LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row["plan"] in PLANS:
            return row["plan"]
        return "free"
    def upgrade_subscription(self, user_id: int, new_plan: str) -> Dict[str, Any]:
        new_plan = new_plan.lower()
        if new_plan not in PLANS:
            return {"status": "error", "message": f"Invalid plan: {new_plan}"}
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        try:
            cursor.execute("""
                UPDATE subscriptions SET status = 'upgraded'
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan, status, start_date, created_at)
                VALUES (?, ?, 'active', ?, ?)
            """, (user_id, new_plan, now_str, now_str))
            conn.commit()
            conn.close()
            return {
                "status": "success",
                "message": f"Successfully upgraded to {PLANS[new_plan]['name']}!",
                "plan": new_plan
            }
        except Exception as e:
            conn.close()
            return {"status": "error", "message": f"Subscription upgrade failed: {str(e)}"}
    @staticmethod
    def can_access(user_plan: str, feature_key: str) -> bool:
        """Enforces backend feature-level authorization."""
        allowed_plans = FEATURE_ROSTER.get(feature_key, [])
        return user_plan.lower() in allowed_plans