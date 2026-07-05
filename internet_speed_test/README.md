# Internet Speed Test GUI

A Windows Tkinter desktop app for measuring download speed, upload speed,
latency, and jitter. The current version uses Cloudflare endpoints, records
results, draws historical graphs, and can run network diagnostics.

## Versions

- `speedtest_chatgpt.py`: original prototype.
- `speedtest_gui_v1.00.py` through `speedtest_gui_v1.04.py`: early GUI and
  Speedtest-based releases.
- `speedtest_gui_v1.05.py`: switches speed testing to Cloudflare endpoints.
- `speedtest_gui_v1.06.py`: adds historical result graphs.
- `speedtest_gui_v1.07.py`: adds manual and automatic network diagnostics.

Run the current version from this folder:

```powershell
python speedtest_gui_v1.07.py
```

`openpyxl` is optional and enables formatted Excel log output. The Tkinter
interface and CSV output work without it.

## Runtime files

- `internet_speed_log.csv`: portable speed-test history used by the graph.
- `internet_speed_log.xlsx`: formatted Excel copy of the history.
- `internet_speed_diagnostics.log`: results from the most recent diagnostic run.

These files remain beside the scripts because the application resolves them
relative to its own location.
