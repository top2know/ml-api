#!/bin/bash
cd api_app
pip install -r requirements.txt
python -m unittest test.py
