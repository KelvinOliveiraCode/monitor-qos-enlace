"""Interface de linha de comando do monitor-qos-enlace.

Uso:
    python -m monitor_qos_enlace <alvo> [--ciclos N] [--intervalo S]
                                     [--contagem C] [--log arquivo.log]
                                     [--latencia-ms MAX] [--jitter-ms MAX]
                                     [--perda-pct MAX]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from .log import Log
from .monitor import Monitor, Thresholds
from .probe import SubprocessPing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monitor-qos-enlace",
        description="Monitor de enlace: latencia, jitter, perda e alerta via ping.",
    )
    parser.add_argument("target", help="host ou IP a ser monitorado")
    parser.add_argument("--ciclos", type=int, default=0, help="numero de ciclos (0 = infinito)")
    parser.add_argument("--intervalo", type=float, default=1.0, help="segundos entre ciclos")
    parser.add_argument("--contagem", type=int, default=4, help="ecos de ping por ciclo")
    parser.add_argument("--log", default=None, help="caminho do arquivo de log")
    parser.add_argument("--latencia-ms", type=float, default=100.0, help="limiar de latencia (ms)")
    parser.add_argument("--jitter-ms", type=float, default=20.0, help="limiar de jitter (ms)")
    parser.add_argument("--perda-pct", type=float, default=5.0, help="limiar de perda (%%)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    thresholds = Thresholds(
        max_latency_ms=args.latencia_ms,
        max_jitter_ms=args.jitter_ms,
        max_loss_pct=args.perda_pct,
    )
    log = Log(path=Path(args.log)) if args.log else Log()

    def on_alert(alert) -> None:
        print(
            f"ALERTA [{alert.sequence}] {alert.kind}: {alert.value:.2f}{alert.metric.split('_')[1]} > "
            f"{alert.threshold:.2f}{alert.metric.split('_')[1]}",
            file=sys.stderr,
        )

    monitor = Monitor(
        target=args.target,
        thresholds=thresholds,
        probe=SubprocessPing(),
        clock=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        count=args.contagem,
        on_alert=on_alert,
        log=log,
    )

    ciclos = 0
    try:
        while args.ciclos == 0 or ciclos < args.ciclos:
            sample = monitor.run_once()
            unidade = "ms" if sample.latency_ms is not None else "perda"
            valor = (
                f"{sample.latency_ms:.3f} ms"
                if sample.latency_ms is not None
                else "perda total"
            )
            print(
                f"ciclo={sample.sequence} alvo={sample.target} "
                f"latencia={valor} jitter={sample.jitter_ms:.3f} ms "
                f"perda={sample.loss_pct:.2f}% "
                f"{'ALERTA: ' + sample.alert.kind if sample.alert else 'OK'}"
            )
            ciclos += 1
            if args.ciclos == 0 or ciclos < args.ciclos:
                time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
