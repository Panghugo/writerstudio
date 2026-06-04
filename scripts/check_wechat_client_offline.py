import os
import sys
import tempfile
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import requests

from writer_studio.wechat_client import WeChatClient
from writer_studio.wechat_publisher import (
    DEFAULT_PROXY_URL,
    PROXY_CONFIG,
    WeChatPublisher,
    _build_proxies,
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


class FakeResponse:
    def __init__(self, payload, raise_http=False):
        self._payload = payload
        self._raise_http = raise_http

    def raise_for_status(self):
        if self._raise_http:
            raise requests.HTTPError('fake http error')

    def json(self):
        return self._payload


def test_get_access_token_success():
    client = WeChatClient('app-id', 'app-secret')
    original = requests.get
    try:
        requests.get = lambda url, **kwargs: FakeResponse({'access_token': 'tok-123', 'expires_in': 7200})
        token = client.get_access_token()
    finally:
        requests.get = original

    assert_true(token == 'tok-123', f'expected token, got {token!r}')
    assert_true(client.token == 'tok-123', 'token should be stored on the client')
    assert_true(client.last_error == '', f'last_error should be cleared, got {client.last_error!r}')


def test_get_access_token_reports_api_error():
    client = WeChatClient('app-id', 'app-secret')
    original = requests.get
    try:
        requests.get = lambda url, **kwargs: FakeResponse({'errcode': 40013, 'errmsg': 'invalid appid'})
        token = client.get_access_token()
    finally:
        requests.get = original

    assert_true(token is None, 'API error should yield no token')
    assert_true('40013' in client.last_error, f'errcode should surface in last_error: {client.last_error!r}')


def test_get_access_token_retries_then_fails_on_network_error():
    client = WeChatClient('app-id', 'app-secret')
    calls = {'count': 0}

    def boom(url, **kwargs):
        calls['count'] += 1
        raise requests.ConnectionError('connection refused')

    original_get = requests.get
    original_sleep = time.sleep
    try:
        requests.get = boom
        time.sleep = lambda *a, **k: None
        token = client.get_access_token()
    finally:
        requests.get = original_get
        time.sleep = original_sleep

    assert_true(token is None, 'network failure should yield no token')
    assert_true(calls['count'] == 2, f'should attempt twice then give up, got {calls["count"]}')
    assert_true('连接微信 API 失败' in client.last_error, f'network failure reason missing: {client.last_error!r}')


def test_get_access_token_rejects_empty_credentials():
    client = WeChatClient('', '')
    token = client.get_access_token()
    assert_true(token is None, 'empty credentials should yield no token')
    assert_true('AppID 或 AppSecret 为空' in client.last_error, 'empty credentials reason missing')


def test_upload_image_missing_file_returns_none():
    client = WeChatClient('app-id', 'app-secret')
    client.token = 'tok'
    assert_true(client.upload_image('/no/such/file.png') is None, 'missing file should return None')


def test_upload_image_success_for_body_and_thumb():
    client = WeChatClient('app-id', 'app-secret')
    client.token = 'tok'
    tmp = tempfile.NamedTemporaryFile(prefix='ws-upload-', suffix='.png', delete=False)
    tmp.write(b'fake png bytes')
    tmp.close()

    def fake_post(url, **kwargs):
        if 'add_material' in url:
            return FakeResponse({'media_id': 'media-1'})
        return FakeResponse({'url': 'https://img.local/x.png'})

    original = requests.post
    try:
        requests.post = fake_post
        body_url = client.upload_image(tmp.name, is_thumb=False)
        thumb_id = client.upload_image(tmp.name, is_thumb=True)
    finally:
        requests.post = original
        os.unlink(tmp.name)

    assert_true(body_url == 'https://img.local/x.png', f'body image url mismatch: {body_url!r}')
    assert_true(thumb_id == 'media-1', f'thumb media id mismatch: {thumb_id!r}')


def test_build_proxies_resolution():
    assert_true(_build_proxies(None)['http'] == DEFAULT_PROXY_URL, 'None should fall back to default proxy')
    assert_true(_build_proxies('   ')['https'] == DEFAULT_PROXY_URL, 'blank should fall back to default proxy')
    custom = _build_proxies('socks5://10.0.0.1:1080')
    assert_true(custom['http'] == 'socks5://10.0.0.1:1080', 'custom proxy http mismatch')
    assert_true(custom['https'] == 'socks5://10.0.0.1:1080', 'custom proxy https mismatch')
    assert_true(PROXY_CONFIG['http'] == DEFAULT_PROXY_URL, 'compat PROXY_CONFIG should equal default proxy')


def test_publisher_proxy_toggle():
    on = WeChatPublisher('app-id', 'app-secret', use_proxy=True)
    off = WeChatPublisher('app-id', 'app-secret', use_proxy=False)

    assert_true(on.proxies is not None, 'use_proxy=True should set proxies')
    assert_true('http' in on.proxies and 'https' in on.proxies, 'proxies should contain http/https keys')
    assert_true(off.proxies is None, 'use_proxy=False should leave proxies unset')


def run_check():
    tests = [
        test_get_access_token_success,
        test_get_access_token_reports_api_error,
        test_get_access_token_retries_then_fails_on_network_error,
        test_get_access_token_rejects_empty_credentials,
        test_upload_image_missing_file_returns_none,
        test_upload_image_success_for_body_and_thumb,
        test_build_proxies_resolution,
        test_publisher_proxy_toggle,
    ]
    for test in tests:
        test()
    print('wechat-client-offline-ok')


if __name__ == '__main__':
    run_check()
