"""Gravacao deterministica de amostras em log."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitor import Sample


SEPARATOR = "\t"


@dataclass
class Log:
    """Escreve linhas de log determinísticas (mesma entrada, mesma saída).

    Cada linha tem colunas fixas, separadas por tabulação:
    sequencia, timestamp, alvo, latencia_ms, jitter_ms, perda_pct, status, alerta.
    Opcionalmente espelha as linhas num arquivo em disco.
    """

    path: Path | None = None
    lines: list[str] = field(default_factory=list)

    def write(self, sample: "Sample") -> None:
        """Acrescenta uma linha formatada a partir de uma amostra."""
        latency = (
            f"{sample.latency_ms:.3f}" if sample.latency_ms is not None else ""
        )
        fields = [
            str(sample.sequence),
            sample.timestamp,
            sample.target,
            latency,
            f"{sample.jitter_ms:.3f}",
            f"{sample.loss_pct:.2f}",
            "ALERT" if sample.alert is not None else "OK",
            sample.alert.kind if sample.alert is not None else "",
        ]
        line = SEPARATOR.join(fields)
        self.lines.append(line)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
