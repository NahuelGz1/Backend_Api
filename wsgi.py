from pathlib import Path
from runpy import run_path


app = run_path(str(Path(__file__).with_name("app.py")))["app"]
