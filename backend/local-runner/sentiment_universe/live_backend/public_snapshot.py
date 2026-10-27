"""Explicit public market schema for the same-origin HQ static mirror.

Never copy provider configuration, authentication, terminal bindings or raw
exports into a web-served directory. Unknown fields are deliberately dropped.
"""
import math


def scalar_fields(value, names):
    value = value if isinstance(value, dict) else {}
    result = {}
    for name in names.split():
        item = value.get(name)
        if item is None or isinstance(item, (bool, int, str)) or isinstance(item, float) and math.isfinite(item):
            if name in value:
                result[name] = item[:4000] if isinstance(item, str) else item
    return result


def rows(value, names, limit):
    return [scalar_fields(row, names) for row in value[:limit] if isinstance(row, dict)] if isinstance(value, list) else []


AI_METADATA = 'status reason dayThai generatedAt inputDigest profile eventCount missionId updatedAt attempted'


def event_ai(value):
    if not isinstance(value, dict) or value.get('status') != 'ready':
        return None
    result = scalar_fields(value, AI_METADATA + ' eventId summaryTh caveatTh')
    result['explanationTh'] = [line[:180] for line in value.get('explanationTh', [])[:4] if isinstance(line, str)] if isinstance(value.get('explanationTh'), list) else []
    result['horizonNotesTh'] = scalar_fields(value.get('horizonNotesTh'), 'short medium long')
    result['sourceIds'] = [ref[:160] for ref in value.get('sourceIds', [])[:4] if isinstance(ref, str)] if isinstance(value.get('sourceIds'), list) else []
    result['sourceRefs'] = rows(value.get('sourceRefs'), 'name url', 4)
    result['scenarios'] = {}
    scenarios = value.get('scenarios') if isinstance(value.get('scenarios'), dict) else {}
    for asset in ('currency', 'XAUUSD', 'XAGUSD'):
        group = scenarios.get(asset)
        if not isinstance(group, dict):
            result['scenarios'][asset] = None
            continue
        projected = {}
        for case in ('below', 'inline', 'above'):
            row = scalar_fields(group.get(case), 'direction textTh')
            if row.get('direction') not in {'up', 'down', 'mixed', 'unknown'}:
                row['direction'] = 'unknown'
            projected[case] = row
        result['scenarios'][asset] = projected
    return result


def news_events(value):
    result = []
    for event in value[:5000] if isinstance(value, list) else []:
        if not isinstance(event, dict):
            continue
        row = scalar_fields(event, EVENT)
        analysis = event_ai(event.get('ai'))
        if analysis is not None:
            row['ai'] = analysis
        result.append(row)
    return result


COMMON = 'status source lastSuccessAt lastAttemptAt nextAttemptAt checkedAt errorCode reason'
EVENT = ('id sourceEventId idStability currency time dayThai timeLabel timeKind timePrecision sourceTime sourceTimeZone '
         'sourceDate originalTitle title titleLanguage metric summary summaryOrigin impact impactLabel kind numeric '
         'forecast previous actual forecastValue previousValue actualValue unit actualLabel actualStatus supportsActual '
         'sourceName sourceUrl mock aiStatus datePrecisionNote dayThaiEstimated')


def public_snapshot(snapshot, published_at):
    sentiment = snapshot.get('sentiment', {})
    correlations = snapshot.get('correlations', {})
    news = snapshot.get('news', {})
    s = scalar_fields(sentiment, COMMON + ' timestampBasis intervalSeconds requestsInLast24Hours requestLimit')
    s['items'] = []
    for item in sentiment.get('items', [])[:32]:
        row = scalar_fields(item, 'symbol sourceSymbol long short avgLong avgShort available asOf reason')
        for key in ('positions', 'volumes'):
            if isinstance(item, dict) and isinstance(item.get(key), dict):
                row[key] = scalar_fields(item[key], 'long short total')
        s['items'].append(row)
    c = scalar_fields(correlations, COMMON + ' sourceMode timeframe method lookback minSamples asOf marketStatus noteTh refreshErrorCode refreshIntervalSeconds')
    c['items'] = rows(correlations.get('items'), 'source target value status samples startAt endAt', 496)
    c['instruments'] = rows(correlations.get('instruments'), 'symbol brokerSymbol status samplesAvailable lastBarClosedAt lastReturnEndAt invalidBars errorCode', 32)
    c['coverage'] = scalar_fields(correlations.get('coverage'), 'available total')
    c['clock'] = scalar_fields(correlations.get('clock'), 'basis historicalClockApproximation')
    n = scalar_fields(news, COMMON + ' sourceUrl provider dayThai timeZone mock supportsActual snapshotOnly updatePolicy actualNotice aiStatus summaryOrigin migrationPending recoveredFromSavedExport warning error rightsNote')
    n['aiAnalysis'] = scalar_fields(news.get('aiAnalysis'), AI_METADATA)
    for key in ('events', 'calendarEvents'):
        n[key] = news_events(news.get(key))
    n['availableDays'] = rows(news.get('availableDays'), 'dayThai count fullyCovered', 100)
    n['attribution'] = scalar_fields(news.get('attribution'), 'text url')
    coverage = news.get('coverage', {})
    n['coverage'] = scalar_fields(coverage, 'from to weekStart sourceCount metadataIcsCount metadataXmlCount ambiguousTimeCount scope completeWorldCalendar dayFrom dayTo dayCount normalizedCount thaiDayFullyCovered cachedWeekCount cachedSourceCount fromThai toThai allImpacts')
    n['coverage']['intervals'] = rows(coverage.get('intervals') if isinstance(coverage, dict) else None, 'from to', 30)
    return {'schemaVersion': 1, 'mode': 'live', 'generatedAt': snapshot.get('generatedAt'),
            'mirror': {'publishedAt': published_at}, 'sentiment': s, 'correlations': c, 'news': n}
