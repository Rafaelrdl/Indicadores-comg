"""
Entry point for scripts module.

Usage:
    python -m scripts.backfill
    python -m scripts.delta
"""
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.backfill or python -m scripts.delta")
        sys.exit(1)

if __name__ == "__main__":
    main()
