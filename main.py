import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from scientific_time_machine.main import main
if __name__ == "__main__":
    main()
