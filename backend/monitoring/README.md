# Monitoring Config

## Files
- `prometheus/prometheus.yml`: scrape config + alertmanager integration
- `prometheus/alerts.yml`: alert rules
- `alertmanager/alertmanager.yml`: warning/critical routing policy

## Notes
- Backend metrics endpoint is expected at `http://backend:8000/metrics`.
- MongoDB rules require `mongodb-exporter` at `mongodb-exporter:9216`.
- Replace webhook URLs in `alertmanager.yml` with your Slack/PagerDuty/webhook bridge.

## Quick validation
```powershell
promtool check rules backend/monitoring/prometheus/alerts.yml
promtool check config backend/monitoring/prometheus/prometheus.yml
amtool check-config backend/monitoring/alertmanager/alertmanager.yml
```
