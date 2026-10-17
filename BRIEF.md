# BRIEF — monitor-qos-enlace (área Redes)

## Entregas

Projeto completo de monitor de enlace com latência, jitter, perda contínua e alerta.

Arquivos criados (raiz: `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\monitor-qos-enlace\`):

| Caminho | Conteúdo |
|---|---|
| `pyproject.toml` | Metadados do projeto, entry point CLI e configuração do pytest (`pythonpath = ["src"]`). |
| `src/monitor_qos_enlace/__init__.py` | Exportação pública do pacote e versão. |
| `src/monitor_qos_enlace/probe.py` | `PingResult`, interface `PingProbe` e `SubprocessPing` (executa `ping` do SO via subprocess e analisa a saída). |
| `src/monitor_qos_enlace/log.py` | `Log`: gravação determinística em colunas fixas separadas por tabulação (opcionalmente em arquivo). |
| `src/monitor_qos_enlace/monitor.py` | `Monitor`: latência (média de RTT), jitter (desvio padrão populacional), perda (%), alerta no primeiro limiar excedido, log de cada ciclo. Relógio e sondador injetáveis. |
| `src/monitor_qos_enlace/__main__.py` | CLI: `python -m monitor_qos_enlace <alvo> [--ciclos] [--intervalo] [--contagem] [--log] [--latencia-ms] [--jitter-ms] [--perda-pct]`. |
| `tests/test_monitor.py` | Suíte pytest com simulador de ping (sem rede real): 11 testes. |
| `README.md` | Documentação bilíngue PT-BR + EN: descrição, como usar, como funciona, testes, licença MIT, autor. |
| `LICENSE` | Texto da licença MIT (Kelvin Oliveira, 2026). |
| `BRIEF.md` | Este resumo. |

## Stack

Python (stdlib apenas) + `ping`/`subprocess`. Nenhuma dependência externa.

## Critérios de aceitação

- [x] Log determinístico (mesma entrada produz mesma saída) com colunas fixas.
- [x] Alerta emitido quando limiar de latência, jitter ou perda é excedido.
- [x] Testes que passam (ver abaixo).
- [x] README PT-BR + EN completo.
- [x] Código tipado, com docstrings, sem dependências externas.

## Como verificar

1. Entre na raiz do projeto:
   ```
   cd C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\monitor-qos-enlace
   ```
2. Rode a suíte de testes:
   ```
   python -m pytest -q
   ```
   Resultado esperado: `11 passed`.
3. (Opcional) Execute o CLI contra um alvo local:
   ```
   PYTHONPATH=src python -m monitor_qos_enlace 127.0.0.1 --ciclos 3 --intervalo 1 --log teste.log
   ```

## Resultado da verificação (esta sessão)

Comando usado: `python -m pytest -q`
Resultado: `11 passed in 0.13s` — todos os testes aprovados.

## Autor

Kelvin Oliveira.

---

# BRIEF — monitor-qos-enlace (Networking area)

## Deliverables

Complete link monitor project with latency, jitter, continuous loss, and alert.

Files created (root: `C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\monitor-qos-enlace\`):

| Path | Content |
|---|---|
| `pyproject.toml` | Project metadata, CLI entry point, and pytest config (`pythonpath = ["src"]`). |
| `src/monitor_qos_enlace/__init__.py` | Public package exports and version. |
| `src/monitor_qos_enlace/probe.py` | `PingResult`, `PingProbe` interface, and `SubprocessPing` (runs the OS `ping` via subprocess and parses output). |
| `src/monitor_qos_enlace/log.py` | `Log`: deterministic writing in fixed tab-separated columns (optionally to a file). |
| `src/monitor_qos_enlace/monitor.py` | `Monitor`: latency (mean RTT), jitter (population standard deviation), loss (%), alert on first exceeded threshold, one log line per cycle. Clock and probe are injectable. |
| `src/monitor_qos_enlace/__main__.py` | CLI: `python -m monitor_qos_enlace <target> [--ciclos] [--intervalo] [--contagem] [--log] [--latencia-ms] [--jitter-ms] [--perda-pct]`. |
| `tests/test_monitor.py` | pytest suite with a ping simulator (no real network): 11 tests. |
| `README.md` | Bilingual PT-BR + EN documentation: description, usage, how it works, tests, MIT license, author. |
| `LICENSE` | MIT license text (Kelvin Oliveira, 2026). |
| `BRIEF.md` | This summary. |

## Stack

Python (standard library only) + `ping`/`subprocess`. No external dependencies.

## Acceptance criteria

- [x] Deterministic log (same input produces same output) with fixed columns.
- [x] Alert emitted when latency, jitter, or loss threshold is exceeded.
- [x] Passing tests (see below).
- [x] Complete bilingual PT-BR + EN README.
- [x] Typed code with docstrings, no external dependencies.

## How to verify

1. Go to the project root:
   ```
   cd C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\monitor-qos-enlace
   ```
2. Run the test suite:
   ```
   python -m pytest -q
   ```
   Expected result: `11 passed`.
3. (Optional) Run the CLI against a local target:
   ```
   PYTHONPATH=src python -m monitor_qos_enlace 127.0.0.1 --ciclos 3 --intervalo 1 --log teste.log
   ```

## Verification result (this session)

Command used: `python -m pytest -q`
Result: `11 passed in 0.13s` — all tests approved.

## Author

Kelvin Oliveira.
