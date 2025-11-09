import logging

debug_log_file = "debug.log"

# Eigenen Logger erstellen
logger = logging.getLogger("debug_logger")
logger.setLevel(logging.INFO)

# File Handler für Datei-Ausgabe konfigurieren
file_handler = logging.FileHandler(debug_log_file)
file_handler.setLevel(logging.INFO)

# Format für Logs definieren
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(formatter)

# Handler dem Logger hinzufügen
logger.addHandler(file_handler)

