#!/usr/bin/env python3
"""Mix voice + music into vertical videos: python3 vertical/mix.py [--lang en] [--id 17-18]"""
import runpy, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import render_vertical  # noqa: F401  (sets the vertical intro length used for voice offsets)
sys.argv = ["add_music.py", "--vertical"] + sys.argv[1:]
runpy.run_path(str(HERE.parent / "add_music.py"), run_name="__main__")
