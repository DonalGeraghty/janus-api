"""Fixed Garmin dashboard resources; never accept upstream paths from callers."""

PANEL_IDS = ("steps", "sleep", "activities", "body-battery", "heart-rate", "stress", "hrv",
             "movement", "weight", "hydration", "fitness-age")
HEALTH_RESOURCES = frozenset(PANEL_IDS) - {"steps", "sleep", "activities"}
