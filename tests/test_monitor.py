"""Suite de testes do monitor-qos-enlace.

Todos os testes usam um simulador de ping: nenhuma rede real é acionada,
garantindo determinismo e execução off-line.
"""

from __future__ import annotations

from monitor_qos_enlace.log import Log
from monitor_qos_enlace.monitor import Alert, Monitor, Sample, Thresholds
from monitor_qos_enlace.probe import PingProbe, PingResult, SubprocessPing


class SimulatedProbe:
    """Simulador de ping: devolge os resultados programados, um lote por sonda."""

    def __init__(self, outcomes: list[float | None]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[tuple[str, int]] = []

    def probe(self, target: str, count: int) -> list[PingResult]:
        self.calls.append((target, count))
        batch = self.outcomes[:count]
        self.outcomes = self.outcomes[count:]
        return [PingResult(latency_ms) for latency_ms in batch]


def fixed_clock() -> str:
    return "2026-10-16T12:00:00Z"


def default_thresholds() -> Thresholds:
    return Thresholds(max_latency_ms=100.0, max_jitter_ms=20.0, max_loss_pct=5.0)


def make_monitor(outcomes: list[float | None], **overrides) -> Monitor:
    kwargs = dict(
        target="10.0.0.1",
        thresholds=default_thresholds(),
        probe=SimulatedProbe(list(outcomes)),
        clock=fixed_clock,
        count=4,
    )
    kwargs.update(overrides)
    return Monitor(**kwargs)


def test_sample_computa_latencia_jitter_perda() -> None:
    """Uma sonda com 3 respostas e 1 perda gera média, jitter e perda corretos."""
    monitor = make_monitor(
        [10.0, 12.0, 11.0, None], thresholds=Thresholds(1000.0, 100.0, 50.0)
    )
    sample = monitor.run_once()

    assert sample.sequence == 1
    assert sample.target == "10.0.0.1"
    assert sample.timestamp == "2026-10-16T12:00:00Z"
    assert sample.latency_ms == 11.0  # media de 10, 12, 11
    assert sample.loss_pct == 25.0  # 1 perda de 4 enviados
    # desvio padrao populacional de [10, 12, 11] = sqrt(2/3)
    assert abs(sample.jitter_ms - 0.816496580927726) < 1e-9
    assert sample.alert is None


def test_primeira_sonda_tem_jitter_zero() -> None:
    """Com apenas um RTT historico, jitter eh 0 (necessario pelo menos 2 amostras)."""
    monitor = make_monitor(
        [10.0, None, None, None], thresholds=Thresholds(1000.0, 100.0, 100.0)
    )
    sample = monitor.run_once()

    assert sample.latency_ms == 10.0
    assert sample.jitter_ms == 0.0
    assert sample.alert is None


def test_alerta_latencia_acima_do_limiar() -> None:
    """Latencia media acima do limiar dispara alerta de latencia."""
    monitor = make_monitor([200.0, None, None, None])
    sample = monitor.run_once()

    assert sample.alert is not None
    assert sample.alert.kind == "latency"
    assert sample.alert.metric == "latency_ms"
    assert sample.alert.value == 200.0
    assert sample.alert.threshold == 100.0
    assert sample.alert.sequence == 1
    assert monitor.alerts == [sample.alert]


def test_alerta_jitter_acima_do_limiar() -> None:
    """Jitter acima do limiar dispara alerta de jitter (sem disparar latencia)."""
    monitor = make_monitor(
        [10.0, 55.0],
        count=2,
        thresholds=Thresholds(1000.0, 20.0, 100.0),
    )
    sample = monitor.run_once()

    assert sample.alert is not None
    assert sample.alert.kind == "jitter"
    assert sample.alert.metric == "jitter_ms"
    assert abs(sample.alert.value - 22.5) < 1e-9  # pstdev de [10, 55]
    assert sample.alert.threshold == 20.0


def test_alerta_perda_acima_do_limiar() -> None:
    """Perca de pacotes acima do limiar dispara alerta de perda."""
    monitor = make_monitor([None, None, None, None])
    sample = monitor.run_once()

    assert sample.alert is not None
    assert sample.alert.kind == "loss"
    assert sample.alert.metric == "loss_pct"
    assert sample.alert.value == 100.0
    assert sample.alert.threshold == 5.0
    assert sample.latency_ms is None


def test_sem_alerta_abaixo_dos_limiares() -> None:
    """Valores dentro dos limiares nao geram alerta."""
    monitor = make_monitor([10.0, 12.0, 11.0, 13.0], thresholds=Thresholds(1000.0, 100.0, 50.0))
    sample = monitor.run_once()

    assert sample.alert is None
    assert monitor.alerts == []


def test_log_eh_deterministico() -> None:
    """Mesmas entradas produzem exatamente as mesmas linhas de log."""
    outcomes = [10.0, 12.0, 11.0, None, 15.0, None, None, None]

    log_a = Log()
    monitor_a = make_monitor(outcomes, log=log_a)
    monitor_a.run_once()
    monitor_a.run_once()

    log_b = Log()
    monitor_b = make_monitor(outcomes, log=log_b)
    monitor_b.run_once()
    monitor_b.run_once()

    assert log_a.lines == log_b.lines
    assert len(log_a.lines) == 2
    # cabecalho de colunas: sequencia, timestamp, alvo, latencia, jitter, perda, status, alerta
    assert log_a.lines[0].startswith("1\t2026-10-16T12:00:00Z\t10.0.0.1\t11.000\t")
    assert "\tOK\t" in log_a.lines[0] or "\tALERT\t" in log_a.lines[0]


def test_acumula_historico_em_ciclos_sucessivos() -> None:
    """run(limit) executa ciclos sucessivos e o jitter cresce com o historico."""
    monitor = make_monitor([10.0, 12.0, 11.0, None, 10.0, 12.0, 11.0, None])
    samples = monitor.run(limit=2)

    assert len(samples) == 2
    assert samples[0].sequence == 1
    assert samples[1].sequence == 2
    assert samples[1].jitter_ms >= samples[0].jitter_ms
    assert samples[1].loss_pct == 25.0


def test_parse_extrai_latencias_e_marca_perdas() -> None:
    """Analisador de saida do ping extrai tempos e marca pacotes perdados."""
    saida = (
        "Resposta de 10.0.0.1: bytes=32 tempo=10ms TTL=64\r\n"
        "Resposta de 10.0.0.1: bytes=32 tempo=12ms TTL=64\r\n"
        "Resposta de 10.0.0.1: bytes=32 tempo=11ms TTL=64\r\n"
        "Resposta de 10.0.0.1: bytes=32 tempo=13ms TTL=64\r\n"
    )
    resultados = SubprocessPing._parse(saida, 4)  # noqa: SLF001 - teste unitario direto

    assert [r.latency_ms for r in resultados] == [10.0, 12.0, 11.0, 13.0]

    saida_perda = (
        "Resposta de 10.0.0.1: bytes=32 tempo=10ms TTL=64\r\n"
        "Pedido esgotado.\r\n"
    )
    resultados = SubprocessPing._parse(saida_perda, 2)
    assert resultados[0].latency_ms == 10.0
    assert resultados[1].latency_ms is None


def test_sonda_é_protocolo_substituivel() -> None:
    """Monitor aceita qualquer objeto que implemente PingProbe (injecao de dependencia)."""

    class FalsaSonda:
        def probe(self, target: str, count: int) -> list[PingResult]:
            return [PingResult(7.0)] * count

    monitor = Monitor(
        target="alvo",
        thresholds=default_thresholds(),
        probe=FalsaSonda(),
        clock=fixed_clock,
        count=2,
    )
    sample = monitor.run_once()
    assert sample.latency_ms == 7.0
    assert isinstance(monitor.probe, PingProbe) is True  # protocolo estrutural


def test_log_arquivo_acrescenta_linhas_idênticas() -> None:
    """Log gravado em arquivo eh deterministico: mesma entrada, mesmo conteudo."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "monitor.log"
        log = Log(caminho)
        monitor = make_monitor([10.0, 12.0], log=log)
        monitor.run_once()
        primeiro = caminho.read_text(encoding="utf-8")

        log2 = Log(caminho)
        monitor2 = make_monitor([10.0, 12.0], log=log2)
        monitor2.run_once()
        segundo = caminho.read_text(encoding="utf-8")

        assert segundo == primeiro + primeiro
        assert primeiro.count("\n") == 1
