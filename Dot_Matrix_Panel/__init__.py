import os
import sys

# Finde den Projektordner (eine Ebene über diesem Paket)
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Stelle sicher, dass Python ihn kennt
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)