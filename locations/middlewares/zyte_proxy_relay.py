"""
A tiny local HTTP CONNECT proxy that relays traffic to Zyte API's
proxy-mode endpoint, injecting the required Basic auth itself.

Why this indirection exists (and isn't just "put Zyte's proxy in
PLAYWRIGHT_LAUNCH_OPTIONS/CAMOUFOX_LAUNCH_OPTIONS['proxy']"):

Firefox has a confirmed bug where combining an *authenticated* HTTP proxy
(a `proxy` launch option with `username`/`password`, or credentials
embedded in the proxy URL) with `route.continue_(headers=...)` reliably
breaks every navigation with `NS_ERROR_PROXY_CONNECTION_REFUSED`. This
isn't a theoretical concern: scrapy_playwright and scrapy_camoufox call
`route.continue_(headers=...)` unconditionally on *every* request (see
`ScrapyPlaywrightDownloadHandler._make_request_handler` /
`ScrapyCamoufoxDownloadHandler`), to keep the browser request in sync with
the original Scrapy Request. It was reproduced locally (no Zyte account
involved -- just a throwaway authenticated CONNECT proxy and
`page.route("**", lambda route: route.continue_(headers=...))`) while
building this module: an unauthenticated proxy + header override works;
the same proxy with credentials attached, whether via the `username`/
`password` fields or embedded in the proxy URL, fails every time.

The one configuration that reliably works is a proxy the browser itself
doesn't have to authenticate to. This module provides exactly that: the
browser is pointed at `127.0.0.1:<ephemeral port>` with no credentials,
and this relay performs the real (authenticated) CONNECT handshake to
Zyte on the browser's behalf, then pipes bytes through unmodified. Zyte's
own TLS interception (used for proxy-mode HTTPS decryption and to honour
Zyte-* request headers such as Zyte-Geolocation) still happens on the far
side of the relay, untouched -- this relay only solves the outer,
browser-to-proxy authentication step.

Related: because Zyte's proxy-mode terminates HTTPS itself and presents a
certificate signed by its own CA (not the destination site's real
certificate), the browser context also needs `ignore_https_errors=True`
-- see `PlaywrightMiddleware._apply_zyte_proxy_context_options` in
`playwright_middleware.py`.
"""

import asyncio
import base64
import logging
import ssl
import threading
from contextlib import suppress

logger = logging.getLogger(__name__)

# Zyte API's TLS-wrapped proxy-mode endpoint (the "HTTPS proxy interface").
# See https://docs.zyte.com/zyte-api/usage/proxy-mode.html. Deliberately not
# the plaintext :8011 endpoint: this relay's Proxy-Authorization header
# carries the Zyte API key, and :8011 would send it in cleartext over the
# public internet. :8014 presents a normal, publicly-trusted (Let's
# Encrypt) certificate for the proxy connection itself -- confirmed with
# `openssl s_client -connect api.zyte.com:8014` returning "Verify return
# code: 0 (ok)" against the system trust store -- so no special CA handling
# is needed here (this is unrelated to the Zyte-CA-signed certificates Zyte
# presents for *tunnelled* HTTPS traffic once a CONNECT succeeds, which is
# what ignore_https_errors in playwright_middleware.py deals with).
ZYTE_API_PROXY_HOST = "api.zyte.com"
ZYTE_API_PROXY_PORT = 8014

_RELAY_START_TIMEOUT = 10

_relays_lock = threading.Lock()
_relays: dict[str, "_ZyteProxyRelay"] = {}


def ensure_relay_running(api_key: str) -> tuple[str, int]:
    """
    Idempotently start (or reuse, if already running for this API key) a
    local relay proxy for the given Zyte API key, and return the
    (host, port) the browser should be pointed at.
    """
    with _relays_lock:
        relay = _relays.get(api_key)
        if relay is None:
            relay = _ZyteProxyRelay(api_key)
            relay.start()
            _relays[api_key] = relay
        port = relay.port
    if port is None:
        raise RuntimeError("Local Zyte proxy relay has no listening port")
    return "127.0.0.1", port


class _ZyteProxyRelay:
    """
    Runs an asyncio CONNECT-forwarding proxy on a dedicated background
    thread with its own event loop, independent of Scrapy's Twisted (or
    asyncio) reactor. It's started synchronously from
    `PlaywrightSpider.update_settings()`, which runs before Scrapy's
    reactor exists, so it can't simply be scheduled on Scrapy's own loop.
    """

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._proxy_authorization = "Basic " + base64.b64encode(f"{api_key}:".encode()).decode()
        self.port: int | None = None
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, name="zyte-proxy-relay", daemon=True)

    def start(self) -> None:
        self._thread.start()
        if not self._ready.wait(timeout=_RELAY_START_TIMEOUT):
            raise RuntimeError("Timed out starting the local Zyte proxy relay")
        if self.port is None:
            raise RuntimeError("Local Zyte proxy relay failed to start")

    def _run(self) -> None:
        asyncio.run(self._serve())

    async def _serve(self) -> None:
        server = await asyncio.start_server(self._handle_client, "127.0.0.1", 0)
        self.port = server.sockets[0].getsockname()[1]
        logger.debug("Local Zyte proxy relay listening on 127.0.0.1:%s", self.port)
        self._ready.set()
        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await self._proxy_one_connection(reader, writer)
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            pass
        except Exception:
            logger.debug("Local Zyte proxy relay: error handling client connection", exc_info=True)
        finally:
            with suppress(OSError, RuntimeError):
                writer.close()

    async def _proxy_one_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request_line = await reader.readline()
        if not request_line:
            return

        header_lines = []
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b""):
                break
            # Never forward the client's own Proxy-Authorization (there
            # shouldn't be one, since the browser isn't given credentials
            # for this relay) -- we always inject our own below.
            if not line.lower().startswith(b"proxy-authorization:"):
                header_lines.append(line)

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                ZYTE_API_PROXY_HOST, ZYTE_API_PROXY_PORT, ssl=ssl.create_default_context()
            )
        except (OSError, ssl.SSLError) as e:
            logger.warning("Local Zyte proxy relay: failed to reach %s: %s", ZYTE_API_PROXY_HOST, e)
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            await writer.drain()
            return

        try:
            upstream_writer.write(request_line)
            for line in header_lines:
                upstream_writer.write(line)
            upstream_writer.write(f"Proxy-Authorization: {self._proxy_authorization}\r\n".encode())
            upstream_writer.write(b"\r\n")
            await upstream_writer.drain()

            method = request_line.split(b" ", 1)[0].upper()
            if method == b"CONNECT":
                status_line = await upstream_reader.readline()
                response_header_lines = []
                while True:
                    line = await upstream_reader.readline()
                    response_header_lines.append(line)
                    if line in (b"\r\n", b""):
                        break

                if b" 200 " not in status_line and not status_line.startswith(b"HTTP/1.1 200"):
                    # Surface whatever Zyte returned (e.g. an
                    # account-suspended error) to the browser instead of
                    # hanging. Note this is *not* the same as it reaching the
                    # browser in any diagnosable form: Firefox collapses any
                    # failed CONNECT -- for any reason -- into a generic,
                    # non-specific NS_ERROR_PROXY_CONNECTION_REFUSED, with no
                    # visibility into the underlying status/headers. This log
                    # line is the only place the real reason (e.g. an
                    # invalid/suspended API key or an out-of-credits account)
                    # is ever observable, so log it before returning.
                    zyte_error_headers = "".join(
                        line.decode(errors="replace")
                        for line in response_header_lines
                        if line.lower().startswith(b"zyte-")
                    )
                    logger.warning(
                        "Local Zyte proxy relay: upstream CONNECT to %s failed: %s%s",
                        ZYTE_API_PROXY_HOST,
                        status_line.decode(errors="replace").strip(),
                        (" | " + zyte_error_headers.strip()) if zyte_error_headers else "",
                    )
                    writer.write(status_line)
                    for line in response_header_lines:
                        writer.write(line)
                    await writer.drain()
                    return

                writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await writer.drain()

            # Stop the peer pipe as soon as either direction finishes,
            # rather than waiting for asyncio.gather() to let both run to
            # completion -- if the browser closes its end first, the
            # upstream->browser pipe would otherwise block on
            # upstream_reader.read() until Zyte itself closes the
            # connection, leaking a relay task/socket per cancelled
            # navigation until then.
            pipes = (
                asyncio.ensure_future(self._pipe(reader, upstream_writer)),
                asyncio.ensure_future(self._pipe(upstream_reader, writer)),
            )
            try:
                await asyncio.wait(pipes, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for pipe in pipes:
                    pipe.cancel()
                await asyncio.gather(*pipes, return_exceptions=True)
        finally:
            with suppress(OSError, RuntimeError):
                upstream_writer.close()

    @staticmethod
    async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                data = await reader.read(65536)
                if not data:
                    break
                writer.write(data)
                await writer.drain()
        except (ConnectionResetError, BrokenPipeError):
            pass
