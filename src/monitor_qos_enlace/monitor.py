"""Monitor de enlace continuo: latencia, jitter, perda e alerta.

Mede latencia via ``ping`` (subprocess), calcula jitter e perda, emite
alerta quando um limiar e excedido e grava um log deterministico.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Callable, Optional

from .log import Log
from .probe import PingProbe, PingResult


@dataclass(frozen=True)
class Thresholds:
    """Limiares que disparam alerta.

    Latencia e jitter em milissegundos; perda em porcentagem (0-100).
    """

    max_latency_ms: float
    max_jitter_ms: float
    max_loss_pct: float


@dataclass(frozen=True)
class Alert:
    """Alerta emitido quando um limiar e excedido por uma amostra."""

    kind: str  # "latency" | "jitter" | "loss"
    metric: str
    value: float
    threshold: float
    sequence: int
    timestamp: str


@dataclass(frozen=True)
class Sample:
    """Resultado de um ciclo de medição."""

    sequence: int
    timestamp: str
    target: str
    latency_ms: Optional[float]
    jitter_ms: float
    loss_pct: float
    alert: Optional[Alert]


class Monitor:
    """Mede latencia/jitter/perda de um alvo e alerta quando limiar excede.

    Determinismo: o relogio e o sondador de ping sao injetaveis, de modo
    que a mesma sequencia de entradas produz a mesma saida (util em testes
    sem rede real).

    Args:
        target: host ou IP a ser sondado.
        thresholds: limiares de alerta.
        probe: objeto que implementa :class:`PingProbe` (injetavel).
        clock: funcao sem argumentos que retorna um timestamp (injetavel).
        count: quantidade de ecos por ciclo (default 4).
        on_alert: callback disparado a cada alerta (opcional).
        log: instancia de :class:`Log` (default novo log em memoria).
    """

    def __init__(
        self,
        *,
        target: str,
        thresholds: Thresholds,
        probe: PingProbe,
        clock: Callable[[], str],
        count: int = 4,
        on_alert: Optional[Callable[[Alert], None]] = None,
        log: Optional[Log] = None,
    ) -> None:
        self.target = target
        self.thresholds = thresholds
        self.probe = probe
        self.clock = clock
        self.count = count
        self.on_alert = on_alert
        self.log = log or Log()
        self._rtts: list[float] = []
        self._sent = 0
        self._received = 0
        self._sequence = 0
        self.alerts: list[Alert] = []
        self.samples: list[Sample] = []

    @property
    def loss_pct(self) -> float:
        """Perda de pacotes acumulada em porcentagem."""
        if self._sent == 0:
            return 0.0
        return (self._sent - self._received) / self._sent * 100.0

    @property
    def jitter_ms(self) -> float:
        """Jitter acumulado: desvio padrao populacional das RTTs coletadas.

        Retorna 0.0 enquanto houver menos de duas amostras de RTT.
        """
        if len(self._rtts) < 2:
            return 0.0
        return statistics.pstdev(self._rtts)

    def _alert_for(self, sequence: int, timestamp: str, latency: Optional[float]) -> Optional[Alert]:
        """Retorna o primeiro limiar excedido, na ordem: latencia, jitter, perda."""
        if latency is not None and latency > self.thresholds.max_latency_ms:
            return Alert(
                "latency", "latency_ms", latency, self.thresholds.max_latency_ms,
                sequence, timestamp,
            )
        if (
            self.jitter_ms > self.thresholds.max_jitter_ms
            and len(self._rtts) >= 2
        ):
            return Alert(
                "jitter", "jitter_ms", self.jitter_ms, self.thresholds.max_jitter_ms,
                sequence, timestamp,
            )
        if (
            self._sent > 0
            and self.loss_pct > self.thresholds.max_loss_pct
        ):
            return Alert(
                "loss", "loss_pct", self.loss_pct, self.thresholds.max_loss_pct,
                sequence, timestamp,
            )
        return None

    def run_once(self) -> Sample:
        """Executa um ciclo de medição e grava a linha de log correspondente."""
        self._sequence += 1
        timestamp = self.clock()
        results = self.probe.probe(self.target, self.count)

        rtts = [result.latency_ms for result in results if result.latency_ms is not None]
        self._sent += len(results)
        self._received += len(rtts)
        self._rtts.extend(rtts)

        latency = statistics.mean(rtts) if rtts else None
        alert = self._alert_for(self._sequence, timestamp, latency)

        sample = Sample(
            sequence=self._sequence,
            timestamp=timestamp,
            target=self.target,
            latency_ms=latency,
            jitter_ms=self.jitter_ms,
            loss_pct=self.loss_pct,
            alert=alert,
        )
        self.samples.append(sample)
        self.log.write(sample)
        if alert is not None and self.on_alert is not None:
            self.on_alert(alert)
        if alert is not None:
            self.alerts.append(alert)
        return sample

    def run(self, limit: Optional[int] = None) -> list[Sample]:
        """Executa ciclos sucessivos; se ``limit`` for dado, para após N ciclos."""
        collected: list[Sample] = []
        while limit is None or len(collected) < limit:
            collected.append(self.run_once())
        return collected
