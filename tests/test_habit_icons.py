import unittest

from pydantic import ValidationError
from core.habit_icons import HABIT_ICON_IDS
from core.habit_service import HabitInput, HabitUpdate
from services.ai_contract import HabitSuggestion


class HabitIconTests(unittest.TestCase):
    def test_all_catalog_icons_can_be_created_updated_and_suggested(self):
        self.assertGreater(len(HABIT_ICON_IDS), 250)
        self.assertEqual(len(HABIT_ICON_IDS), len(set(HABIT_ICON_IDS)))
        for icon in HABIT_ICON_IDS:
            self.assertEqual(HabitInput(name='Habit', days=[0], start_date='2026-10-09', icon=icon).icon, icon)
            self.assertEqual(HabitUpdate(icon=icon).icon, icon)
            suggestion = HabitSuggestion(name='Habit', description='', icon=icon, colour='#d9c5a3', days=[0], category='', group='')
            self.assertEqual(suggestion.icon, icon)

    def test_invalid_icons_are_rejected_and_legacy_ids_preserved(self):
        self.assertTrue(set(['check', 'book', 'walk', 'leaf', 'water', 'sun', 'moon', 'dumbbell', 'heart', 'plan']).issubset(HABIT_ICON_IDS))
        with self.assertRaises(ValidationError):
            HabitUpdate(icon='not-a-real-icon')
        self.assertEqual(HabitSuggestion.model_json_schema()['properties']['icon']['enum'], list(HABIT_ICON_IDS))
