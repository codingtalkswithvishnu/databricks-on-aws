"""Run from the companion root. --live is an explicit paid model request."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "shared"))
from healthcare import answer, chat

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    try:
        result = answer(args.question, model_call=chat if args.live else None)
    except OSError as error:
        print(json.dumps({"status": "failed", "error": "Local source files could not be read",
                          "error_type": type(error).__name__}))
        return 1
    except (ValueError, RuntimeError, KeyError, IndexError, TypeError) as error:
        print(json.dumps({"status": "failed", "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

