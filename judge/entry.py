"""CodeRank judge: executa código Python de submissões dentro de um Python Worker.

Este Worker NÃO tem segredos nem bindings e não possui rota pública: só é
chamado pela API (coderank-api) via service binding. Cada submissão roda em
globals novos, com stdin/stdout substituídos, limite de tempo por teste e
limite de saída.
"""

import builtins
import io
import json
import sys
import time
import traceback

try:  # ambiente Cloudflare (Pyodide)
    from workers import WorkerEntrypoint
    from js import Response, Object
    from pyodide.ffi import to_js
except ImportError:  # testes locais
    WorkerEntrypoint = object
    Response = None
    Object = dict
    to_js = lambda x, **kwargs: x  # noqa: E731

MAX_SOURCE = 50_000
MAX_INPUT = 10_000
MAX_TESTS = 20
MAX_OUT = 50_000
PER_TEST_SECONDS = 2.0
TOTAL_SECONDS = 9.0

BLOCKED = {
    "js", "pyodide", "pyodide_js", "_pyodide", "_pyodide_core", "workers",
    "gc", "ctypes", "_ctypes", "subprocess", "socket", "ssl", "urllib",
    "http", "requests", "httpx", "aiohttp", "importlib", "webbrowser",
}


class TimeLimit(BaseException):
    pass


class OutputLimit(BaseException):
    pass


class _Out(io.StringIO):
    def write(self, s):
        if self.tell() + len(s) > MAX_OUT:
            raise OutputLimit()
        return super().write(s)


_real_import = builtins.__import__


def _guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name.split(".")[0] in BLOCKED:
        raise ImportError(f"O módulo '{name}' não é permitido no CodeRank.")
    return _real_import(name, globals, locals, fromlist, level)


def _make_builtins():
    b = dict(vars(builtins))
    b["__import__"] = _guarded_import
    for name in ("open", "breakpoint", "help"):
        b.pop(name, None)
    return b


def _where(tb):
    line = None
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<submission>":
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def run_single(code, stdin_text, limit, trace=True):
    out, err = _Out(), io.StringIO()
    deadline = time.monotonic() + limit
    counter = [0]

    def tracer(frame, event, arg):
        if frame.f_code.co_filename != "<submission>":
            return None

        def local(frame, event, arg):
            counter[0] += 1
            if counter[0] & 255 == 0 and time.monotonic() > deadline:
                raise TimeLimit()
            return local

        return local

    glb = {"__name__": "__main__", "__builtins__": _make_builtins()}
    old = (sys.stdin, sys.stdout, sys.stderr)
    sys.stdin, sys.stdout, sys.stderr = io.StringIO(stdin_text), out, err
    status = "ok"
    started = time.monotonic()
    if trace:
        sys.settrace(tracer)
    try:
        exec(code, glb)
    except TimeLimit:
        status = "timeout"
    except OutputLimit:
        status = "output_limit"
    except SystemExit as exc:
        if exc.code not in (None, 0):
            status = "runtime_error"
    except BaseException as exc:  # noqa: BLE001
        status = "runtime_error"
        line = _where(exc.__traceback__)
        where = f" (linha {line})" if line else ""
        err.write(f"{type(exc).__name__}: {exc}{where}\n")
    finally:
        sys.settrace(None)
        sys.stdin, sys.stdout, sys.stderr = old
    return {
        "status": status,
        "stdout": out.getvalue(),
        "stderr": err.getvalue()[:4000],
        "ms": int((time.monotonic() - started) * 1000),
    }


def run_all(source, inputs, trace=True):
    if not isinstance(source, str) or not source.strip():
        return {"error": "Código vazio."}, 400
    if len(source.encode("utf-8")) > MAX_SOURCE:
        return {"error": "O código ultrapassa o limite de 50 KB."}, 413
    if not isinstance(inputs, list) or not 1 <= len(inputs) <= MAX_TESTS:
        return {"error": "Entradas inválidas."}, 400
    if any(not isinstance(i, str) or len(i) > MAX_INPUT for i in inputs):
        return {"error": "Entrada inválida ou grande demais."}, 400

    try:
        code = compile(source, "<submission>", "exec")
    except SyntaxError as exc:
        msg = f"SyntaxError: {exc.msg} (linha {exc.lineno})"
        return {"results": [{"status": "compile_error", "stdout": "", "stderr": msg, "ms": 0}]}, 200

    results = []
    started = time.monotonic()
    for text in inputs:
        if time.monotonic() - started > TOTAL_SECONDS:
            results.append({"status": "timeout", "stdout": "", "stderr": "Tempo total excedido.", "ms": 0})
            continue
        results.append(run_single(code, text if text.endswith("\n") else text + "\n", PER_TEST_SECONDS, trace))
    return {"results": results}, 200


def _json(body, status=200):
    payload = json.dumps(body, ensure_ascii=False)
    if Response:
        opts = to_js(
            {"status": status, "headers": {"Content-Type": "application/json; charset=utf-8"}},
            dict_converter=Object.fromEntries,
        )
        return Response.new(payload, opts)
    return {"status": status, "body": body}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("?")[0].rstrip("/")
        if request.method == "GET" and path.endswith("/health"):
            return _json({"ok": True, "python": sys.version.split()[0]})
        if request.method != "POST" or not path.endswith("/run"):
            return _json({"error": "Não encontrado"}, 404)
        try:
            data = json.loads(await request.text())
        except Exception:  # noqa: BLE001
            return _json({"error": "JSON inválido"}, 400)
        # No plano Free o próprio Worker é cortado em 10 ms de CPU; o rastreio de
        # tempo (mais lento) só é ligado quando o binding TRACE=1 (plano pago).
        trace = str(getattr(self.env, "TRACE", "0")) == "1"
        body, status = run_all(data.get("source"), data.get("inputs"), trace)
        return _json(body, status)
