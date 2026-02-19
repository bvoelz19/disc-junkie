#!/bin/bash

# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the required packages
pip install discord.py yt-dlp

# Install the required libraries
pip install -r requirements.txt
