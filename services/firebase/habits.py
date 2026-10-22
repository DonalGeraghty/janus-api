"""Transactional, account-generation-scoped Aether state and dated check-ins."""

import copy
import json
import re
from datetime import date, timedelta
from uuid import uuid4

from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from core.habit_service import habit_stats, habit_today, is_due
from . import db_state
from .account_state import ACCOUNT_DELETION_FIELD, ACCOUNT_DELETION_TOKEN_FIELD, account_id_matches
from .openai_credentials import normalize_user_email
from ..logging_service import logger


class HabitError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _empty(account_id):
    return {'account_id': account_id, 'habits': [], 'categories': [], 'groups': [], 'timezone': None}


def _valid_id(item_id):
    if not isinstance(item_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', item_id):
        raise HabitError('Invalid habit or label ID')


def _guard(user, account_id, deletion_token=None):
    if not user or not account_id_matches(account_id, user):
        raise HabitError('Account is unavailable', 401)
    if deletion_token:
        if not user.get(ACCOUNT_DELETION_FIELD) or user.get(ACCOUNT_DELETION_TOKEN_FIELD) != deletion_token:
            raise HabitError('Account deletion changed', 409)
    elif user.get(ACCOUNT_DELETION_FIELD):
        raise HabitError('Account deletion is in progress', 409)


def _query(collection, selection):
    query = collection
    if selection.get('habit_id'):
        query = query.where(filter=FieldFilter('habit_id', '==', selection['habit_id']))
    if selection.get('start'):
        query = query.where(filter=FieldFilter('date', '>=', selection['start']))
    if selection.get('end'):
        query = query.where(filter=FieldFilter('date', '<=', selection['end']))
    if selection.get('limit'):
        query = query.limit(selection['limit'])
    return query


def _operate(email, account_id, operation, selection=None, deletion_token=None):
    """Read every required document before writing; guard deletion and generation."""
    email = normalize_user_email(email)
    if not email:
        raise HabitError('Invalid account', 401)
    if db_state.users_collection_ref is not None:
        if db_state.db is None:
            raise HabitError('Habit storage is unavailable', 503)
        user_ref = db_state.users_collection_ref.document(email)
        state_ref = user_ref.collection('aether').document('state')
        collection = user_ref.collection('habit_checkins')

        @firestore.transactional
        def execute(transaction):
            user = user_ref.get(transaction=transaction)
            _guard(user.to_dict() if user.exists else None, account_id, deletion_token)
            document = state_ref.get(transaction=transaction)
            state = document.to_dict() if document.exists else _empty(account_id)
            if state.get('account_id') != account_id:
                raise HabitError('Account generation does not match habit data', 409)
            previous = copy.deepcopy(state)
            entries = [dict(item.to_dict(), id=item.id) for item in _query(collection, selection).stream(transaction=transaction)] if selection is not None else []
            result, writes, deletes = operation(state, entries)
            if len(json.dumps(state).encode('utf-8')) > 850_000:
                raise HabitError('Habit storage limit reached. Archive or remove unused habits.', 409)
            if state != previous:
                transaction.set(state_ref, state)
            for entry in writes:
                payload = {key: value for key, value in entry.items() if key != 'id'}
                transaction.set(collection.document(entry['id']), payload)
            for entry_id in deletes:
                transaction.delete(collection.document(entry_id))
            if deletion_token and result == 0:
                transaction.delete(state_ref)
            return result

        try:
            return execute(db_state.db.transaction())
        except HabitError:
            raise
        except Exception as error:
            logger.error('Habit storage failed: %s', type(error).__name__)
            raise HabitError('Habit storage is unavailable', 503) from error

    with db_state.memory_lock:
        _guard(db_state.auth_users_memory.get(email), account_id, deletion_token)
        state = copy.deepcopy(db_state.habits_memory.get(email, _empty(account_id)))
        if state.get('account_id') != account_id:
            raise HabitError('Account generation does not match habit data', 409)
        store = db_state.habit_checkins_memory.get(email, {})
        entries = []
        if selection is not None:
            entries = [copy.deepcopy(entry) for entry in store.values()
                       if (not selection.get('habit_id') or entry['habit_id'] == selection['habit_id'])
                       and (not selection.get('start') or entry['date'] >= selection['start'])
                       and (not selection.get('end') or entry['date'] <= selection['end'])]
            if selection.get('limit'):
                entries = entries[:selection['limit']]
        result, writes, deletes = operation(state, entries)
        if len(json.dumps(state).encode('utf-8')) > 850_000:
            raise HabitError('Habit storage limit reached', 409)
        db_state.habits_memory[email] = state
        for entry in writes:
            db_state.habit_checkins_memory.setdefault(email, {})[entry['id']] = entry
        for entry_id in deletes:
            db_state.habit_checkins_memory.get(email, {}).pop(entry_id, None)
        if deletion_token and result == 0:
            db_state.habits_memory.pop(email, None)
            db_state.habit_checkins_memory.pop(email, None)
        return copy.deepcopy(result)


def read_habits(email, account_id):
    def read(state, entries):
        today = habit_today(state['timezone'])
        visible = {habit['id'] for habit in state['habits']}
        result = {key: copy.deepcopy(value) for key, value in state.items() if key != 'account_id'}
        by_habit = {}
        for entry in entries:
            by_habit.setdefault(entry['habit_id'], []).append(entry)
        result['stats'] = {habit['id']: habit_stats(habit, by_habit.get(habit['id'], []), today) for habit in state['habits']}
        result['today_checkins'] = [entry for entry in entries if entry['date'] == today.isoformat() and entry['habit_id'] in visible]
        return result, [], []
    return _operate(email, account_id, read, selection={})


def list_checkins(email, account_id, start, end):
    try:
        first, last = date.fromisoformat(start), date.fromisoformat(end)
    except (ValueError, TypeError):
        raise HabitError('Use valid YYYY-MM-DD start and end dates')
    if first.isoformat() != start or last.isoformat() != end:
        raise HabitError('Use valid YYYY-MM-DD start and end dates')
    if first > last or (last - first).days > 365:
        raise HabitError('Choose a date range of at most 366 days')
    def read(state, entries):
        visible = {habit['id'] for habit in state['habits']}
        return [entry for entry in entries if entry['habit_id'] in visible], [], []
    return _operate(email, account_id, read, selection={'start': start, 'end': end})


def _reorder(items, item, order):
    items.remove(item)
    items.insert(min(order, len(items)), item)
    for index, entry in enumerate(items):
        entry['order'] = index


def _labels_exist(state, data):
    for field, collection in [('category_id', 'categories'), ('group_id', 'groups')]:
        if data.get(field) is not None and not any(item['id'] == data[field] for item in state[collection]):
            raise HabitError('Choose an existing category and group')


def create_habit(email, account_id, data):
    item_id = uuid4().hex
    def create(state, _):
        if len(state['habits']) >= 100:
            raise HabitError('You can have up to 100 habits', 409)
        today = habit_today(state['timezone'])
        start = date.fromisoformat(data['start_date'])
        if start < today or start > today + timedelta(days=3650):
            raise HabitError('Start date must be today or within the next ten years')
        _labels_exist(state, data)
        habit = dict(data, id=item_id, archived=False, order=len(state['habits']), schedule_history=[{'effective_from': data['start_date'], 'days': data['days'], 'archived': False}])
        state['habits'].append(habit)
        return {'habit': habit}, [], []
    return _operate(email, account_id, create)


def update_habit(email, account_id, item_id, data):
    _valid_id(item_id)
    def update(state, _):
        habit = next((item for item in state['habits'] if item['id'] == item_id), None)
        if habit is None:
            raise HabitError('Habit not found', 404)
        _labels_exist(state, data)
        if 'days' in data or 'archived' in data:
            effective = max((habit_today(state['timezone']) + timedelta(days=1)).isoformat(), habit['start_date'])
            revision = {'effective_from': effective, 'days': data.get('days', habit['days']), 'archived': data.get('archived', habit['archived'])}
            habit['schedule_history'] = [entry for entry in habit['schedule_history'] if entry['effective_from'] < effective] + [revision]
        habit.update(data)
        if 'order' in data:
            _reorder(state['habits'], habit, data['order'])
        return {'habit': habit}, [], []
    return _operate(email, account_id, update)


def delete_habit(email, account_id, item_id):
    _valid_id(item_id)
    def remove(state, _):
        state['habits'] = [habit for habit in state['habits'] if habit['id'] != item_id]
        for index, habit in enumerate(state['habits']):
            habit['order'] = index
        return {}, [], []
    _operate(email, account_id, remove)
    # Removal prevents new check-ins. Batches also make a failed cleanup retryable.
    while _operate(email, account_id, lambda state, entries: (len(entries), [], [entry['id'] for entry in entries]), selection={'habit_id': item_id, 'limit': 400}):
        pass
    return {}


def save_checkin(email, account_id, habit_id, day, data):
    _valid_id(habit_id)
    try:
        chosen = date.fromisoformat(day)
    except (ValueError, TypeError):
        raise HabitError('Use a valid YYYY-MM-DD date')
    if chosen.isoformat() != day:
        raise HabitError('Use a valid YYYY-MM-DD date')
    def save(state, _):
        habit = next((item for item in state['habits'] if item['id'] == habit_id), None)
        if habit is None:
            raise HabitError('Habit not found', 404)
        if chosen > habit_today(state['timezone']) or day < habit['start_date']:
            raise HabitError('Check-ins must be between the habit start date and today')
        if data['completed'] and not is_due(habit, chosen):
            raise HabitError('This habit was not scheduled on that date')
        entry = dict(data, id=f'{habit_id}_{day}', habit_id=habit_id, date=day)
        return {'checkin': entry}, [entry], []
    return _operate(email, account_id, save)


def save_settings(email, account_id, data):
    def save(state, _):
        state.update(data)
        return {'timezone': state['timezone']}, [], []
    return _operate(email, account_id, save)


def manage_label(email, account_id, kind, method, data=None, item_id=None):
    if kind not in ('categories', 'groups'):
        raise HabitError('Invalid label type')
    if item_id is not None:
        _valid_id(item_id)
    generated_id = uuid4().hex
    def manage(state, _):
        items = state[kind]
        item = next((entry for entry in items if entry['id'] == item_id), None)
        if method != 'POST' and item is None:
            raise HabitError('Category or group not found', 404)
        if method == 'DELETE':
            items.remove(item)
            field = 'category_id' if kind == 'categories' else 'group_id'
            for habit in state['habits']:
                if habit[field] == item_id:
                    habit[field] = None
        else:
            name = data.get('name')
            if name and any(entry['name'].casefold() == name.casefold() and entry['id'] != item_id for entry in items):
                raise HabitError('That category or group already exists', 409)
            if method == 'POST':
                if len(items) >= 50:
                    raise HabitError('You can have up to 50 categories or groups', 409)
                item = dict(data, id=generated_id, order=len(items))
                items.append(item)
            else:
                item.update(data)
                if 'order' in data:
                    _reorder(items, item, data['order'])
        for index, entry in enumerate(items):
            entry['order'] = index
        return {'item': item}, [], []
    return _operate(email, account_id, manage)


def delete_habit_data(email, account_id, deletion_token):
    try:
        while _operate(email, account_id, lambda state, entries: (len(entries), [], [entry['id'] for entry in entries]), selection={'limit': 400}, deletion_token=deletion_token):
            pass
        return True
    except HabitError:
        return False
