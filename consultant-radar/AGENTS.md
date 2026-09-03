# Consultant Radar

Python 3.11+, stdlib only. Work in this directory; do not mix with `cde-salesnav` or `prospeccion-consultoras`.

```bash
./run.sh companies
./run.sh scan --company deloitte-es
python3 -m unittest discover -s tests -v
```

- Config: `config/companies.json`, `config/filters.json`
- State: `data/radar.sqlite` (gitignored)
- Do not commit secrets. Public ATS endpoints need no keys today.
