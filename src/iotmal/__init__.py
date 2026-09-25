"""Cross-architecture IoT malware detection on the CIC-YNU-IoTMal 2026 dataset.

The package holds the code that turns the released parquet files into
hash-grouped, architecture-canonical features and trains the models the
paper reports. Scripts and job launchers import from here; nothing here
imports from them.
"""

__version__ = "0.1.0"
