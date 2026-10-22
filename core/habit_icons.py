"""The catalog shared with Aether's searchable icon picker."""

import json
from pathlib import Path
from typing import Literal

HABIT_ICON_CATALOG = json.loads(Path(__file__).with_suffix('.json').read_text(encoding='utf-8'))
HABIT_ICON_IDS = tuple(icon['id'] for icon in HABIT_ICON_CATALOG)
HabitIcon = Literal[HABIT_ICON_IDS]
