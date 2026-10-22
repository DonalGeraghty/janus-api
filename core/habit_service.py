"""Habit definitions, immutable dated schedules, and deterministic streaks."""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

from .habit_icons import HabitIcon


class HabitInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default='', max_length=1000)
    icon: HabitIcon = 'check'
    colour: str = Field(default='#d9c5a3', pattern=r'^#[0-9a-fA-F]{6}$')
    days: list[int] = Field(min_length=1, max_length=7)
    category_id: str | None = Field(default=None, pattern=r'^[A-Za-z0-9_-]{1,128}$')
    group_id: str | None = Field(default=None, pattern=r'^[A-Za-z0-9_-]{1,128}$')
    start_date: date

    @field_validator('days', mode='before')
    @classmethod
    def validate_days(cls, days):
        if not isinstance(days, list) or any(type(day) is not int or day < 0 or day > 6 for day in days):
            raise ValueError('Choose weekdays from 0 (Monday) to 6 (Sunday)')
        if len(set(days)) != len(days):
            raise ValueError('Weekdays must be unique')
        return sorted(days)


class HabitUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    icon: HabitIcon | None = None
    colour: str | None = Field(default=None, pattern=r'^#[0-9a-fA-F]{6}$')
    days: list[int] | None = Field(default=None, min_length=1, max_length=7)
    category_id: str | None = Field(default=None, pattern=r'^[A-Za-z0-9_-]{1,128}$')
    group_id: str | None = Field(default=None, pattern=r'^[A-Za-z0-9_-]{1,128}$')
    archived: StrictBool | None = None
    order: int | None = Field(default=None, ge=0, le=100, strict=True)

    _days = field_validator('days', mode='before')(HabitInput.validate_days.__func__)

    @model_validator(mode='after')
    def forbid_null_fields(self):
        if not self.model_fields_set or any(getattr(self, name) is None for name in self.model_fields_set - {'category_id', 'group_id'}):
            raise ValueError('Supply at least one valid update')
        return self


class HabitLabelInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=60)


class HabitLabelUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str | None = Field(default=None, min_length=1, max_length=60)
    order: int | None = Field(default=None, ge=0, le=50, strict=True)

    @model_validator(mode='after')
    def valid_update(self):
        if not self.model_fields_set or any(getattr(self, name) is None for name in self.model_fields_set):
            raise ValueError('Supply a name or order')
        return self


class HabitCheckinInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    completed: StrictBool
    note: str = Field(default='', max_length=1000)


class HabitSettingsInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    timezone: str = Field(min_length=1, max_length=100)

    @field_validator('timezone')
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Use a valid IANA timezone')
        return value


def habit_today(timezone_name=None):
    return datetime.now(timezone.utc).astimezone(ZoneInfo(timezone_name or 'UTC')).date()


def schedule_on(habit, day):
    iso_day = day.isoformat() if isinstance(day, date) else day
    if iso_day < habit['start_date']:
        return None
    return next((revision for revision in reversed(habit['schedule_history']) if revision['effective_from'] <= iso_day), None)


def is_due(habit, day):
    day = date.fromisoformat(day) if isinstance(day, str) else day
    revision = schedule_on(habit, day)
    return bool(revision and not revision['archived'] and day.weekday() in revision['days'])


def habit_stats(habit, checkins, today):
    completed = {entry['date'] for entry in checkins if entry['habit_id'] == habit['id'] and entry['completed']}
    day = date.fromisoformat(habit['start_date'])
    current = best = total_recent = complete_recent = 0
    while day <= today:
        if is_due(habit, day):
            done = day.isoformat() in completed
            if done:
                current += 1
                best = max(best, current)
            elif day < today:
                current = 0
            # Today's unfinished check-in is pending, not a missed day.
            if day >= today - timedelta(days=29) and (day < today or done):
                total_recent += 1
                complete_recent += int(done)
        day += timedelta(days=1)
    return {'current': current, 'best': best, 'rate': round(100 * complete_recent / total_recent) if total_recent else 0}
