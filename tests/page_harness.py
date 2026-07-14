"""Internal Streamlit AppTest harness for callable page modules."""

from __future__ import annotations

import importlib
import os


module = importlib.import_module(os.environ["FITJOURNEY_TEST_PAGE"])
module.render()
