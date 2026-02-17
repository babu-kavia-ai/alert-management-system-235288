#!/bin/bash
cd /tmp/kavia/workspace/code-generation/alert-management-system-235288/alert_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

