#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Wizard..."
streamlit run Wizard.py
read -p "Press Enter to close..."