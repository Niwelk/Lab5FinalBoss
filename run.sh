#!/bin/bash

source /home/niwelk/venv/bin/activate

uvicorn main:app --reload --port 8000 &

streamlit run app.py --server.headless=true &

wait
