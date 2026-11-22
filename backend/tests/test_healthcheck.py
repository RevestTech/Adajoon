"""Test health check endpoints."""

import httpx
import pytest
from httpx import AsyncClient

import app.services.healthcheck_service as healthcheck_service
from app.services.healthcheck_service import probe_stream


@pytest.fixture
def mock_transport(monkeypatch):
    """Patch the AsyncClient probe_stream builds so its requests are served
    by an in-process handler instead of going over the network.

    respx (already in requirements.txt) is incompatible with the installed
    httpx version in this environment - every request it's asked to mock
    comes back "not mocked" regardless of method/URL - so these tests use
    httpx's own MockTransport instead.
    """
    real_async_client = httpx.AsyncClient

    def _install(handler):
        transport = httpx.MockTransport(handler)

        class _PatchedClient(real_async_client):
            def __init__(self, *args, **kwargs):
                kwargs["transport"] = transport
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(healthcheck_service.httpx, "AsyncClient", _PatchedClient)

    return _install


@pytest.mark.unit
async def test_health_endpoint(client: AsyncClient):
    """Test basic health endpoint returns 200."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.unit
async def test_health_ready_endpoint(client: AsyncClient):
    """Test readiness endpoint checks database connectivity.

    Overall status is "degraded" rather than "ok" when Redis is unreachable
    (there's no Redis service in this test environment, same as CI) - that's
    the endpoint correctly reporting an optional dependency being down, not a
    failure. The database and query checks must still be "ok" regardless.
    """
    response = await client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["categories_query"]["status"] == "ok"


@pytest.mark.unit
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint.

    `/` deliberately returns a bare {"status": "ok"} health-check body (see
    PR #19) to avoid a proxy loop with the frontend - it's not meant to carry
    API info/a message/title.
    """
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.unit
async def test_probe_stream_online_via_head(mock_transport):
    """A normal server that honors HEAD and returns 200 is reported online."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "HEAD"
        return httpx.Response(200, headers={"content-type": "video/mp2t"})

    mock_transport(handler)
    result = await probe_stream("http://example.test/stream.ts")
    assert result["status"] == "online"


@pytest.mark.unit
async def test_probe_stream_get_fallback_on_405(mock_transport):
    """A server that rejects HEAD (405) falls back to a ranged GET."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "HEAD":
            return httpx.Response(405)
        assert request.method == "GET"
        assert request.headers.get("range") == "bytes=0-1024"
        return httpx.Response(206, content=b"some bytes")

    mock_transport(handler)
    result = await probe_stream("http://example.test/stream.ts")
    assert result["status"] == "online"
    assert "GET fallback" in result["detail"]


@pytest.mark.unit
async def test_probe_stream_valid_manifest(mock_transport):
    """A real HLS manifest is reported online."""
    manifest = b"#EXTM3U\n#EXTINF:-1,Channel\nhttp://example.test/seg.ts\n"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/vnd.apple.mpegurl"},
            content=manifest,
        )

    mock_transport(handler)
    result = await probe_stream("http://example.test/live.m3u8")
    assert result["status"] == "online"
    assert result["detail"] == "HLS manifest valid"


class _UnboundedStream(httpx.AsyncByteStream):
    """~500MB stream delivered in realistic 8KB chunks (matching the read
    granularity deep_validate_radio already assumes elsewhere in this
    codebase), yielded lazily so a test can tell how much of it a caller
    actually pulled before stopping."""

    def __init__(self, counter: dict):
        self._counter = counter

    async def __aiter__(self):
        chunk = b"x" * 8192  # 8 KB
        for _ in range(64000):  # ~500 MB if ever fully drained
            self._counter["total"] += len(chunk)
            yield chunk

    async def aclose(self):
        pass


@pytest.mark.unit
async def test_probe_stream_never_buffers_unbounded_body(mock_transport):
    """Regression test for the validator worker's intermittent crash-restarts.

    Root cause: httpx's non-streaming get()/head() fully buffer whatever
    body a server sends, regardless of request method or headers. A stream
    source that ignores HEAD/Range semantics and keeps pushing an unbounded
    live feed (common among the IPTV sources this validates) got read
    entirely into memory by every such probe - with enough concurrent
    pathological channels in a batch, that was enough to crash the worker
    before it ever logged a phase result. probe_stream must cap every read
    instead of trusting the server to respect HEAD/Range.
    """
    bytes_served = {"total": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        # Ignores the request method/headers entirely - always streams the
        # same unbounded body, exactly like a dumb live-TV relay would.
        return httpx.Response(
            200,
            headers={"content-type": "video/mp2t"},
            stream=_UnboundedStream(bytes_served),
        )

    mock_transport(handler)
    result = await probe_stream("http://example.test/misbehaving.ts")

    assert result["status"] == "online"
    assert bytes_served["total"] <= 16384, (
        f"probe_stream read {bytes_served['total']} bytes from an unbounded "
        "source - it must cap reads instead of buffering the full body"
    )


@pytest.mark.unit
async def test_probe_stream_manifest_path_never_buffers_unbounded_body(
    mock_transport,
):
    """Same regression as above, for the .m3u8 branch - reachable directly
    from the manual admin re-check endpoint (check_channel -> probe_stream)."""
    bytes_served = {"total": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/vnd.apple.mpegurl"},
            stream=_UnboundedStream(bytes_served),
        )

    mock_transport(handler)
    await probe_stream("http://example.test/misbehaving.m3u8")

    assert bytes_served["total"] <= 16384, (
        f"probe_stream read {bytes_served['total']} bytes from an unbounded "
        ".m3u8 source - it must cap reads instead of buffering the full body"
    )
