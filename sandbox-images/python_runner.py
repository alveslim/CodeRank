"""Entrypoint mínimo da imagem usada para executar submissões Python."""

import sys


source = sys.stdin.read()
code = compile(source, "<submission>", "exec")
namespace = {"__name__": "__main__", "__file__": "<submission>"}
exec(code, namespace, namespace)
