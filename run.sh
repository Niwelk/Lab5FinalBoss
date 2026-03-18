#!/bin/bash

source /home/niwelk/venv/bin/activate

echo "1) Запуск FastAPI main.py"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "2) Запуск монитора ресурсов monitoring.py"
python monitoring.py &
MONITOR_PID=$!

echo "3) Запуск streamlit интерфейса app.py"
streamlit run app.py --server.headless=true &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $MONITOR_PID $FRONTEND_PID" INT TERM
wait
