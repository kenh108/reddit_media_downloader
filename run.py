import argparse
import logging
import sys
from app import create_app

parser = argparse.ArgumentParser(description="Run the Flask app.")
parser.add_argument("--production", action="store_true", help="Run in production mode")
args = parser.parse_args()

logging.basicConfig(
    level=logging.INFO if args.production else logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)

app = create_app()

if __name__ == "__main__":
    app.run(debug=not args.production)
