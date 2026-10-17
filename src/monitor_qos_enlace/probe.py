"""Sondagem de ping: protocolo substituivel e implementacao real via subprocess."""

from __future__ import annotations

import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class PingResult:
    """Resultado de um único eco de ping.

    Attributes:
        latency_ms: latencia de ida e volta em milissegundos, ou None quando
            o pacote se perde.
    """

    latency_ms: float | None


@runtime_checkable
class PingProbe(Protocol):
    """Sonda um alvo de rede e retorna os resultados de eco."""

    def probe(self, target: str, count: int) -> list[PingResult]:
        """Executa `count` ecos contra `target` e retorna um resultado por eco."""


class SubprocessPing:
    """Executa o utilitario `ping` do sistema operacional via subprocess.

    A saida e analisada com expressao regular; pacotes sem resposta viram
    ``PingResult(latency_ms=None)``.
    """

    def probe(self, target: str, count: int) -> list[PingResult]:
        system = platform.system().lower()
        if system == "windows":
            cmd = ["ping", "-n", str(max(1, count)), "-w", "1000", target]
        else:
            cmd = ["ping", "-c", str(max(1, count)), "-W", "1", target]
        try:
            completed = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
        except (OSError, subprocess.SubprocessError):
            return [PingResult(None) for _ in range(max(1, count))]
        return self._parse(completed.stdout, count)

    @staticmethod
    def _parse(output: str, count: int) -> list[PingResult]:
        """Extrai tempos de resposta da saida textual do `ping`."""
        times = re.findall(
            r"(?:tempo|time)[=<]([\d.]+)\s*ms", output, flags=re.IGNORECASE
        )
        latencies = [float(value) for value in times]
        results: list[PingResult] = []
        for index in range(max(1, count)):
            results.append(
                PingResult(latencies[index] if index < len(latencies) else None)
            )
        return results
