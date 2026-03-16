import os
import subprocess
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_script(script_name: str, args: list):
    """Utility to run a python script as a subprocess."""
    cmd = ["python", script_name] + args
    logging.info(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Pipeline failed at {script_name} with error code {e.returncode}")
        exit(1)
    except FileNotFoundError:
         logging.error("Python command not found. Ensure Python is in your PATH.")
         exit(1)

def main():
    parser = argparse.ArgumentParser(description="Agentic AI Knowledge Base Pipeline Orchestrator")
    parser.add_argument("--src-vault", default="source_knowledge_base", help="Path to raw Obsidian vault")
    parser.add_argument("--normalized-vault", default="normalized_knowledge_base", help="Path for the flat, normalized markdown files")
    parser.add_argument("--hugo-content", default="frontend/content/posts", help="Path to Hugo content dir (posts)")
    parser.add_argument("--hugo-static", default="frontend/static/images", help="Path to Hugo static images dir")
    parser.add_argument("--db-path", default="knowledge_rag.sqlite", help="Path for the generated sqlite-vec RAG database")
    
    args = parser.parse_args()

    # Step 1: Normalize Directory (Nested -> Flat prefix)
    logging.info("--- STEP 1: Directory Normalization ---")
    run_script(os.path.join("backend", "normalize_directory.py"), [
        "--src-dir", args.src_vault,
        "--dest-dir", args.normalized_vault
    ])

    # Step 2: Build RAG DB (Chunk & Embed)
    logging.info("--- STEP 2: SQLite-vec RAG Construction ---")
    run_script(os.path.join("backend", "build_rag_db.py"), [
        "--src-dir", args.normalized_vault,
        "--db-path", args.db_path
    ])

    # Step 3: Preprocess for Hugo Publishing
    logging.info("--- STEP 3: Hugo Preprocessing ---")
    run_script(os.path.join("frontend", "preprocess_obsidian_to_hugo.py"), [
        "--src-dir", args.normalized_vault,
        "--dest-dir", args.hugo_content,
        "--assets-src", os.path.join(args.normalized_vault, "images") if os.path.isdir(os.path.join(args.normalized_vault, "images")) else args.normalized_vault,
        "--assets-dest", args.hugo_static
    ])

    logging.info("=== Pipeline Execution Complete ===")
    logging.info("The knowledge base has been normalized, embedded in RAG, and prepared for Hugo publishing.")

if __name__ == "__main__":
    main()
