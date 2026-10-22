"""Fixed Garmin dashboard resources; never accept upstream paths from callers."""

PANEL_IDS = ("steps", "sleep", "activities", "stress", "hrv", "movement", "weight", "hydration")
HEALTH_RESOURCES = frozenset(PANEL_IDS) - {"steps", "sleep", "activities"}
RETIRED_PANEL_IDS = frozenset({"body-battery", "heart-rate", "fitness-age"})
