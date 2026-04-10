"""Convenience wrapper — run the pipeline directly from the project root.

    python run_pipeline.py --input-dir ./docs --search-fields title description --output qa_output.json

The installed CLI command ``qa-generate`` delegates to the same entry point.
"""
from src.pipeline import main  # noqa: F401

if __name__ == "__main__":
    main()
