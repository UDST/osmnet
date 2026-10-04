import datetime as dt

import pytest

import osmnet
import osmnet.load as load

# /api/status as served by overpass-api.de on 2026-10-04 (verbatim)
STATUS_LIVE_2026_10_04 = (
    'Connected as: 843828827\n'
    'Current time: 2026-10-04T12:18:14Z\n'
    'Announced endpoint: gall.openstreetmap.de/\n'
    'Rate limit: 2\n'
    '2 slots available now.\n'
    'Currently running queries (pid, space limit, time limit, start time):\n'
)

# older layout, where the slot line was at index 3
STATUS_OLD_LAYOUT = (
    'Connected as: 1234567890\n'
    'Current time: 2020-07-13T18:00:00Z\n'
    'Rate limit: 2\n'
    '1 slots available now.\n'
    'Currently running queries (pid, space limit, time limit, start time):\n'
)

STATUS_SLOT_TEMPLATE = (
    'Connected as: 843828827\n'
    'Current time: 2026-10-04T12:18:14Z\n'
    'Announced endpoint: gall.openstreetmap.de/\n'
    'Rate limit: 2\n'
    'Slot available after: {late}, in 120 seconds.\n'
    'Slot available after: {early}, in 30 seconds.\n'
    'Currently running queries (pid, space limit, time limit, start time):\n'
)

STATUS_BUSY = (
    'Connected as: 843828827\n'
    'Current time: 2026-10-04T12:18:14Z\n'
    'Announced endpoint: gall.openstreetmap.de/\n'
    'Rate limit: 2\n'
    'Currently running queries (pid, space limit, time limit, start time):\n'
    '12345\t536870912\t180\t2026-10-04T12:17:50Z\n'
    '12346\t536870912\t180\t2026-10-04T12:18:01Z\n'
)

STATUS_406_HTML = (
    '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n'
    '<html><head>\n'
    '<title>406 Not Acceptable</title>\n'
    '</head><body>\n'
    '<h1>Not Acceptable</h1>\n'
    '</body></html>\n'
)


def _utc_in(seconds):
    t = dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=seconds)
    return t.strftime('%Y-%m-%dT%H:%M:%SZ')


class FakeResponse(object):
    def __init__(self, status_code=200, text='', json_data=None):
        self.status_code = status_code
        self.text = text
        self.content = text.encode('utf-8')
        self.reason = 'reason'
        self._json_data = json_data

    def json(self):
        if self._json_data is None:
            raise ValueError('no JSON')
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception('HTTP {}'.format(self.status_code))


@pytest.fixture
def no_sleep(monkeypatch):
    sleeps = []
    monkeypatch.setattr(load.time, 'sleep', lambda s: sleeps.append(s))
    return sleeps


def test_user_agent():
    assert load.USER_AGENT == (
        'osmnet/{} (+https://github.com/UDST/osmnet)'
        .format(osmnet.__version__))


def test_parse_status_live_layout():
    assert load._parse_overpass_status(STATUS_LIVE_2026_10_04) == \
        ('available', 2)


def test_parse_status_old_layout():
    assert load._parse_overpass_status(STATUS_OLD_LAYOUT) == ('available', 1)


def test_parse_status_slot_available_after():
    text = STATUS_SLOT_TEMPLATE.format(late=_utc_in(120), early=_utc_in(30))
    kind, wait = load._parse_overpass_status(text)
    assert kind == 'slot'
    assert 25 <= wait <= 31


def test_parse_status_slot_in_past():
    text = STATUS_SLOT_TEMPLATE.format(late=_utc_in(-5), early=_utc_in(-10))
    assert load._parse_overpass_status(text) == ('slot', 1)


def test_parse_status_currently_running():
    assert load._parse_overpass_status(STATUS_BUSY) == ('busy', None)


def test_parse_status_unrecognized():
    assert load._parse_overpass_status(STATUS_406_HTML) == (None, None)
    assert load._parse_overpass_status('') == (None, None)


def test_get_pause_duration_sends_user_agent(monkeypatch, no_sleep):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse(text=STATUS_LIVE_2026_10_04)

    monkeypatch.setattr(load.requests, 'get', fake_get)
    assert load.get_pause_duration() == 0
    url, kwargs = calls[0]
    assert url == 'https://overpass-api.de/api/status'
    assert kwargs['headers']['User-Agent'] == load.USER_AGENT


def test_get_pause_duration_slot(monkeypatch, no_sleep):
    text = STATUS_SLOT_TEMPLATE.format(late=_utc_in(120), early=_utc_in(30))
    monkeypatch.setattr(load.requests, 'get',
                        lambda url, **kw: FakeResponse(text=text))
    assert 25 <= load.get_pause_duration() <= 31


def test_get_pause_duration_406_falls_back(monkeypatch, no_sleep):
    monkeypatch.setattr(
        load.requests, 'get',
        lambda url, **kw: FakeResponse(status_code=406, text=STATUS_406_HTML))
    assert load.get_pause_duration(default_duration=10) == 10


def test_get_pause_duration_busy_then_free(monkeypatch, no_sleep):
    pages = [STATUS_BUSY, STATUS_BUSY, STATUS_LIVE_2026_10_04]
    monkeypatch.setattr(load.requests, 'get',
                        lambda url, **kw: FakeResponse(text=pages.pop(0)))
    assert load.get_pause_duration(recursive_delay=5) == 0
    assert no_sleep == [5, 5]


def test_get_pause_duration_busy_is_bounded(monkeypatch, no_sleep):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResponse(text=STATUS_BUSY)

    monkeypatch.setattr(load.requests, 'get', fake_get)
    assert load.get_pause_duration(recursive_delay=5, default_duration=10,
                                   max_retries=3) == 10
    assert len(calls) == 4
    assert no_sleep == [5, 5, 5]


def test_overpass_request_sends_user_agent(monkeypatch, no_sleep):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        return FakeResponse(text='{}', json_data={'elements': []})

    monkeypatch.setattr(load.requests, 'post', fake_post)
    assert load.overpass_request(data={'data': 'q'}) == {'elements': []}
    assert calls[0]['headers']['User-Agent'] == load.USER_AGENT


def test_overpass_request_retries_then_succeeds(monkeypatch, no_sleep):
    responses = [FakeResponse(status_code=429), FakeResponse(status_code=504),
                 FakeResponse(text='{}', json_data={'elements': [1]})]
    monkeypatch.setattr(load.requests, 'post',
                        lambda url, **kw: responses.pop(0))
    result = load.overpass_request(data={'data': 'q'},
                                   error_pause_duration=2)
    assert result == {'elements': [1]}
    assert no_sleep == [2, 2]


def test_overpass_request_retry_exhaustion(monkeypatch, no_sleep):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse(status_code=429)

    monkeypatch.setattr(load.requests, 'post', fake_post)
    with pytest.raises(load.OverpassRetryError, match='429 after 3 retries'):
        load.overpass_request(data={'data': 'q'}, error_pause_duration=1,
                              max_retries=3)
    assert len(calls) == 4
    assert no_sleep == [1, 1, 1]


def test_overpass_request_default_max_retries(monkeypatch, no_sleep):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse(status_code=504)

    monkeypatch.setattr(load.requests, 'post', fake_post)
    monkeypatch.setattr(load.requests, 'get',
                        lambda url, **kw: FakeResponse(
                            text=STATUS_LIVE_2026_10_04))
    with pytest.raises(load.OverpassRetryError):
        load.overpass_request(data={'data': 'q'})
    assert len(calls) == 6


def test_overpass_request_other_status_raises(monkeypatch, no_sleep):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return FakeResponse(status_code=400, text='bad query')

    monkeypatch.setattr(load.requests, 'post', fake_post)
    with pytest.raises(Exception, match='Server returned no JSON data'):
        load.overpass_request(data={'data': 'q'})
    assert len(calls) == 1
