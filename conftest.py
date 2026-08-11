"""pytest configuration file to set pythonpath automatically."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
