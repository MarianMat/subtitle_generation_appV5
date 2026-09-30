import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).parent / "v5" / "app.py"), run_name="__main__")
