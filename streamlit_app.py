"""
Streamlit Community Cloud Entrypoint (streamlit_app.py).
Delegates directly to dashboard/app.py.
"""
import os
import sys
import runpy

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

dashboard_app = os.path.join(root_dir, "dashboard", "app.py")
runpy.run_path(dashboard_app, run_name="__main__")
