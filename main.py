"""
YouTube Livestream Planner
Hoofdapplicatie - startpunt
"""

import sys
import os

# Zorg dat src in het pad zit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import App

if __name__ == "__main__":
    app = App()
    app.run()
