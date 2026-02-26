#!/bin/bash
cd /opt/aishield
source venv/bin/activate

case "$1" in
  orchestrator)
    python -m backend.orchestrator.main 2>&1 | tail -5
    ;;
  monitoring)
    python -m backend.monitoring.scheduler 2>&1 | tail -5
    ;;
  lead_scoring)
    python -m backend.prospecting.lead_scoring 2>&1 | tail -5
    ;;
esac
