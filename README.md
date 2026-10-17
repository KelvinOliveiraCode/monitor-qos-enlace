# monitor-qos-enlace

## Descrição

monitor-qos-enlace é um monitor de enlace contínuo (área Redes) escrito em Python. Ele sonda um alvo com `ping` via subprocess, mede latência, jitter e perda de pacotes, e emite um alerta quando um limiar é excedido. Cada ciclo grava uma linha determinística em um log: mesma entrada, mesma saída.

MVP: latência, jitter, perda contínua, alerta. Não há dependências externas — apenas a biblioteca padrão do Python e o utilitário `ping` do sistema operacional.

## Como usar

Instale o Python (>= 3.10) e execute a partir da raiz do projeto, com o pacote de origem no caminho de importacao (o projeto nao e instalado):

```
PYTHONPATH=src python -m monitor_qos_enlace 10.0.0.1 --ciclos 10 --intervalo 1 --log enlace.log
```

No Windows (PowerShell):

```
$env:PYTHONPATH="src"; python -m monitor_qos_enlace 10.0.0.1 --ciclos 10 --intervalo 1 --log enlace.log
```

Opções da linha de comando:

- `target` — host ou IP a ser monitorado (obrigatório).
- `--ciclos N` — número de ciclos (0 = infinito; padrão 0).
- `--intervalo S` — segundos entre ciclos (padrão 1.0).
- `--contagem C` — ecos de ping por ciclo (padrão 4).
- `--log` — caminho do arquivo de log (padrão: apenas stdout).
- `--latencia-ms`, `--jitter-ms`, `--perda-pct` — limiares de alerta (padrões: 100 ms, 20 ms, 5%).

Exemplo de saída do console:

```
ciclo=1 alvo=10.0.0.1 latencia=11.000 ms jitter=0.816 ms perda=25.00% ALERTA: loss
```

Uma linha de log tem colunas fixas separadas por tabulação: sequencia, timestamp, alvo, latencia_ms, jitter_ms, perda_pct, status, alerta.

## Como funciona

- Latência: média dos RTT dos ecos que respondem no ciclo.
- Jitter: desvio padrão populacional das RTT acumuladas; é 0.0 com menos de duas amostras.
- Perda: (enviados menos respondidos) dividido pelos enviados, em porcentagem.
- Alerta: o primeiro limiar excedido, nesta ordem: latência, jitter, perda.

O sondador de ping é injetável pela interface `PingProbe`, então o monitor pode ser testado com um simulador, sem rede real.

## Testes

Execute a suíte pytest a partir da raiz do projeto:

```
python -m pytest -q
```

Resultado esperado: todos os testes passam (11 testes). Os testes usam um simulador de ping; nenhuma rede real é necessária.

## Licença

MIT License. Copyright (c) 2026 Kelvin Oliveira.

## Autor

Kelvin Oliveira.

---

# monitor-qos-enlace

## Description

monitor-qos-enlace is a continuous link monitor (Networking area) written in Python. It probes a target with `ping` via subprocess, measures latency, jitter, and packet loss, and emits an alert when a threshold is exceeded. Each cycle writes one deterministic line to a log: same input, same output.

MVP: latency, jitter, continuous loss, alert. No external dependencies — Python standard library only, plus the system `ping` utility.

## How to use

Install Python (>= 3.10) and run from the project root, with the source package on the import path (the project is not installed):

```
PYTHONPATH=src python -m monitor_qos_enlace 10.0.0.1 --ciclos 10 --intervalo 1 --log enlace.log
```

On Windows (PowerShell):

```
$env:PYTHONPATH="src"; python -m monitor_qos_enlace 10.0.0.1 --ciclos 10 --intervalo 1 --log enlace.log
```

Command-line options:

- `target` — host or IP to monitor (required).
- `--ciclos N` — number of cycles (0 = infinite; default 0).
- `--intervalo S` — seconds between cycles (default 1.0).
- `--contagem C` — ping echoes per cycle (default 4).
- `--log` — path to the log file (default: stdout only).
- `--latencia-ms`, `--jitter-ms`, `--perda-pct` — alert thresholds (defaults: 100 ms, 20 ms, 5%).

Example console output:

```
ciclo=1 alvo=10.0.0.1 latencia=11.000 ms jitter=0.816 ms perda=25.00% ALERTA: loss
```

Each log line has fixed tab-separated columns: sequence, timestamp, target, latency_ms, jitter_ms, loss_pct, status, alert.

## How it works

- Latency: mean RTT of the echoes that respond in the cycle.
- Jitter: population standard deviation of the accumulated RTTs; 0.0 with fewer than two samples.
- Loss: (sent minus responded) divided by sent, as a percentage.
- Alert: the first threshold exceeded, in this order: latency, jitter, loss.

The ping probe is injectable through the `PingProbe` interface, so the monitor can be tested with a simulator — no real network required.

## Tests

Run the pytest suite from the project root:

```
python -m pytest -q
```

Expected result: all tests pass (11 tests). Tests use a ping simulator; no real network required.

## License

MIT License. Copyright (c) 2026 Kelvin Oliveira.

## Author

Kelvin Oliveira.
