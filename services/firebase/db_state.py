import re
from threading import RLock

# Shared regex validators
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CELL_KEY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)$")

# Global database handles
db = None
users_collection_ref = None

# In-memory fallback stores
auth_users_memory = {}
nutrition_entries_memory = {}
# Legacy records are retained only for guarded account-deletion cleanup.
workout_history_memory = {}
habits_memory = {}
habit_checkins_memory = {}
flashcards_memory = {}
flashcard_reviews_memory = {}
push_subscriptions_memory = {}
memory_lock = RLock()
