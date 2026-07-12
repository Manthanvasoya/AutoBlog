#!/usr/bin/env python3
"""
Entry point for AutoBlog application.
Runs the Streamlit frontend.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run Streamlit app"""
    app_path = Path(__file__).parent.parent / "frontend" / "app.py"

    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", str(app_path)
        ], check=True)
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error running application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
