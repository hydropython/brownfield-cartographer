#!/usr/bin/env python3
"""
Brownfield Cartographer CLI

Entry point for codebase analysis.
Takes repo path (local path or GitHub URL), runs analysis.
"""

import argparse
import sys
import subprocess
import tempfile
from pathlib import Path
from .orchestrator import run_analysis
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clone_git_repo(git_url: str, temp_dir: Path) -> Path:
    """
    Clone Git repository to temporary directory.
    
    Args:
        git_url: GitHub or Git URL
        temp_dir: Temporary directory for clone
    
    Returns:
        Path to cloned repository
    
    Raises:
        Exception: If git clone fails
    """
    try:
        logger.info(f"Cloning repository: {git_url}")
        subprocess.run(
            ['git', 'clone', '--depth', '1', git_url, str(temp_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"   Repository cloned to {temp_dir}")
        return temp_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e.stderr}")
        raise Exception(f"Git clone failed: {e.stderr}")
    except FileNotFoundError:
        logger.error("Git not found. Please install git.")
        raise Exception("Git not found. Please install git.")


def is_git_url(path: str) -> bool:
    """Check if path is a Git URL."""
    return path.startswith('http://') or path.startswith('https://') or path.startswith('git@')


def main():
    parser = argparse.ArgumentParser(
        description="Brownfield Cartographer - Automated codebase intelligence"
    )
    parser.add_argument(
        "repo_path",
        type=str,
        help="Path to repository (local path or GitHub URL)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".cartography",
        help="Output directory for artifacts (default: .cartography)"
    )
    parser.add_argument(
        "--agents",
        type=str,
        nargs="+",
        default=["surveyor", "hydrologist"],
        choices=["surveyor", "hydrologist", "semanticist", "archivist"],
        help="Agents to run (default: surveyor hydrologist)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle Git URL vs local path
    temp_dir = None
    repo_path = Path(args.repo_path)
    
    try:
        if is_git_url(args.repo_path):
            # Clone Git repository
            temp_dir = Path(tempfile.mkdtemp(prefix="cartographer_"))
            repo_path = clone_git_repo(args.repo_path, temp_dir)
        elif not repo_path.exists():
            logger.error(f"Repository not found: {repo_path}")
            sys.exit(1)
        
        output_dir = Path(args.output)
        
        # Run analysis with progress reporting
        logger.info("=" * 60)
        logger.info("BROWNFIELD CARTOGRAPHER")
        logger.info("=" * 60)
        logger.info(f"Repository: {repo_path}")
        logger.info(f"Output: {output_dir}")
        logger.info(f"Agents: {', '.join(args.agents)}")
        logger.info()
        
        results = run_analysis(
            repo_path=repo_path,
            output_dir=output_dir,
            agents=args.agents,
            verbose=args.verbose
        )
        
        logger.info()
        logger.info("=" * 60)
        logger.info("ANALYSIS COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Module Graph: {output_dir / 'module_graph.json'}")
        logger.info(f"Lineage Graph: {output_dir / 'lineage_graph.json'}")
        
        if results.get("surveyor"):
            logger.info(f"Surveyor: {results['surveyor']['nodes']} nodes, {results['surveyor']['edges']} edges")
        if results.get("hydrologist"):
            logger.info(f"Hydrologist: {results['hydrologist']['nodes']} nodes, {results['hydrologist']['edges']} edges")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary directory
        if temp_dir and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()
