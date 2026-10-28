"""Read-only projection of the HQ-owned daily news interpretation artifact.

This process never dispatches AI, refreshes a provider, or writes the shared
artifact. A completed batch is bound to today's exact calendar assignment.
"""
import copy
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re
import stat


THAI = timezone(timedelta(hours=7))
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT.parents[2] / 'data' / 'runtime' / 'sentiment-news-ai'
MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
STATUSES = frozenset({'pending', 'queued', 'running', 'ready', 'failed', 'blocked', 'interrupted', 'stale', 'empty'})
CODE = re.compile(r'[a-z0-9_]{1,80}\Z')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}\Z')
DIGEST = re.compile(r'[a-f0-9]{64}\Z')


@lru_cache(maxsize=1)
def contract():
    path = ROOT.parent / 'hq_backend' / 'research' / 'sentiment_news_ai.py'
    spec = importlib.util.spec_from_file_location('_universe_news_ai_contract', path)
    if spec is None or spec.loader is None:
        raise ValueError('news_ai_contract_unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate_key')
        value[key] = item
    return value


def _constant(_value):
    raise ValueError('nonfinite_value')


def _identity(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def _read_artifact(path, maximum):
    """Bounded stable read; a replacement during the read retries next cycle."""
    before = path.lstat()
    if (not stat.S_ISREG(before.st_mode) or path.is_symlink()
            or getattr(before, 'st_file_attributes', 0) & 0x400
            or before.st_size > maximum):
        raise ValueError('artifact_invalid')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    after = path.lstat()
    if len(raw) > maximum or _identity(before) != _identity(after):
        raise ValueError('artifact_changed')
    value = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_pairs, parse_constant=_constant)
    if not isinstance(value, dict):
        raise ValueError('artifact_invalid')
    return value


def _stamp(value):
    if not isinstance(value, str) or len(value) > 80:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed if parsed.tzinfo is not None else None
    except ValueError:
        return None


def _safe(value, pattern):
    return value if isinstance(value, str) and pattern.fullmatch(value) else None


def _clean_news(news):
    result = copy.deepcopy(news) if isinstance(news, dict) else {}
    result.pop('aiAnalysis', None)
    if 'calendarEvents' in result:
        result['calendarEvents'] = [row for row in result['calendarEvents'] if isinstance(row, dict)] if isinstance(result['calendarEvents'], list) else []
    for key in ('events', 'calendarEvents'):
        for event in result.get(key, []) if isinstance(result.get(key), list) else []:
            if isinstance(event, dict):
                event.pop('ai', None)
                event['aiStatus'] = 'not_requested'
    return result


def _fallback(news, day, status, reason, state=None, digest=None):
    metadata = {'status': status, 'reason': reason, 'dayThai': day}
    if digest:
        metadata['inputDigest'] = digest
    if isinstance(state, dict):
        mission_id = _safe(state.get('missionId'), IDENTIFIER)
        if mission_id:
            metadata['missionId'] = mission_id
        if _stamp(state.get('updatedAt')):
            metadata['updatedAt'] = state['updatedAt']
        if type(state.get('attempted')) is bool:
            metadata['attempted'] = state['attempted']
    news['aiAnalysis'] = metadata
    news['aiStatus'] = status
    return news


def overlay_news(news, directory=None, *, now=None):
    """Return an isolated copy. Any stale, partial or invalid batch fails closed."""
    current = now or datetime.now(timezone.utc)
    day = current.astimezone(THAI).date().isoformat()
    clean = _clean_news(news)
    if clean.get('dayThai') != day:
        return _fallback(clean, day, 'stale', 'calendar_stale')
    try:
        rules = contract()
        assignment = rules.build_assignment(clean, day)
        if 'calendarEvents' in clean:
            calendar = {**clean, 'events': [row for row in clean['calendarEvents'] if row.get('dayThai') == day]}
            if rules.build_assignment(calendar, day)['inputDigest'] != assignment['inputDigest']:
                return _fallback(clean, day, 'stale', 'calendar_changed')
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError):
        return _fallback(clean, day, 'pending', 'waiting_calendar')
    digest = assignment['inputDigest']
    if not assignment['events']:
        return _fallback(clean, day, 'empty', 'empty_day', digest=digest)
    folder = Path(directory) if directory is not None else DEFAULT_DIRECTORY
    try:
        directory_link = folder.is_symlink() or bool(getattr(folder.lstat(), 'st_file_attributes', 0) & 0x400)
    except FileNotFoundError:
        directory_link = False
    except OSError:
        return _fallback(clean, day, 'failed', 'result_invalid', digest=digest)
    if directory_link:
        return _fallback(clean, day, 'failed', 'result_invalid', digest=digest)
    state = None
    try:
        candidate = _read_artifact(folder / 'state.json', 64 * 1024)
        if (candidate.get('schemaVersion') == 1 and type(candidate.get('schemaVersion')) is int
                and candidate.get('dayThai') == day):
            state = candidate
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    try:
        saved = _read_artifact(folder / 'result.json', MAX_ARTIFACT_BYTES)
    except FileNotFoundError:
        candidate_status = state.get('status') if state else None
        status = candidate_status if isinstance(candidate_status, str) and candidate_status in STATUSES else 'pending'
        if status in {'ready', 'empty'}:
            status = 'pending'
        reason = _safe(state.get('reason'), CODE) if state else None
        if state and state.get('inputDigest') not in (None, digest):
            return _fallback(clean, day, 'stale', 'calendar_changed', state, digest)
        return _fallback(clean, day, status, reason or 'waiting_analysis', state, digest)
    except (OSError, ValueError, TypeError, RecursionError):
        return _fallback(clean, day, 'failed', 'result_invalid', state, digest)
    try:
        if set(saved) != {'schemaVersion', 'dayThai', 'inputDigest', 'missionId', 'generatedAt', 'assignment', 'result'}:
            raise ValueError('envelope_fields')
        if type(saved['schemaVersion']) is not int or saved['schemaVersion'] != 1:
            raise ValueError('envelope_version')
        if saved['dayThai'] != day:
            if (state and state.get('status') in {'pending', 'queued', 'running', 'blocked', 'failed', 'interrupted'}
                    and state.get('inputDigest') in (None, digest)):
                return _fallback(clean, day, state['status'], _safe(state.get('reason'), CODE) or 'waiting_analysis', state, digest)
            return _fallback(clean, day, 'stale', 'day_expired', state, digest)
        if saved['inputDigest'] != digest:
            return _fallback(clean, day, 'stale', 'calendar_changed', state, digest)
        if not _safe(saved['missionId'], IDENTIFIER):
            raise ValueError('mission_invalid')
        generated = _stamp(saved['generatedAt'])
        if (generated is None or generated.astimezone(THAI).date().isoformat() != day
                or generated > current + timedelta(minutes=5)):
            raise ValueError('generated_at_invalid')
        if state and (state.get('inputDigest') not in (None, digest)
                      or state.get('missionId') not in (None, saved['missionId'])):
            return _fallback(clean, day, 'stale', 'calendar_changed', state, digest)
        rules.validate_assignment(saved['assignment'], day)
        if saved['assignment']['inputDigest'] != digest:
            raise ValueError('assignment_mismatch')
        rules.validate_result(saved['result'], saved['assignment'])
        projected = rules.project_news(clean, saved['result'], saved['assignment'], saved['generatedAt'])
        projected['aiAnalysis']['missionId'] = saved['missionId']
        for key in ('events', 'calendarEvents'):
            for event in projected.get(key, []) if isinstance(projected.get(key), list) else []:
                if isinstance(event, dict) and isinstance(event.get('ai'), dict):
                    event['aiStatus'] = 'ready'
        return projected
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        return _fallback(clean, day, 'failed', 'result_invalid', state, digest)
