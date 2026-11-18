"""HTTP assíncrono que funciona no navegador (Pyodide) e no Python local."""

from __future__ import annotations

import asyncio
import json
import sys
import urllib.error
import urllib.request

IS_WEB = sys.platform == "emscripten"


async def fetch_json(
    method: str,
    url: str,
    body: dict | None = None,
    headers: dict | None = None,
    timeout: float = 25.0,
) -> tuple[int, object]:
    """Executa a requisição e devolve (status, json|texto). Status 0 = sem conexão."""

    hdrs = {"Accept": "application/json", **(headers or {})}
    payload = None
    if body is not None:
        payload = json.dumps(body)
        hdrs["Content-Type"] = "application/json"

    if IS_WEB:
        try:
            from pyodide.http import pyfetch  # type: ignore

            kwargs = {"method": method, "headers": hdrs}
            if payload is not None:
                kwargs["body"] = payload
            resp = await asyncio.wait_for(pyfetch(url, **kwargs), timeout=timeout)
            text = await resp.string()
            status = resp.status
        except Exception:  # noqa: BLE001
            return 0, None
    else:
        def _blocking() -> tuple[int, str]:
            req = urllib.request.Request(
                url,
                data=payload.encode("utf-8") if payload is not None else None,
                headers=hdrs,
                method=method,
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
                    return r.status, r.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as exc:
                return exc.code, exc.read().decode("utf-8", "replace")

        try:
            status, text = await asyncio.to_thread(_blocking)
        except Exception:  # noqa: BLE001
            return 0, None

    try:
        return status, json.loads(text) if text else None
    except ValueError:
        return status, text
