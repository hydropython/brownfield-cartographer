"""CLI entry point for brownfield-cartographer.

Usage:
    python -m src.cli analyze <repo_path> [--output <dir>]
    python -m src.cli query <cartography_dir>
"""
import argparse
import sys
from pathlib import Path

from orchestrator import run_pipeline
from agents.navigator import NavigatorAgent


def main():
    parser = argparse.ArgumentParser(description="Brownfield Cartographer  Static + Dynamic Code Analysis")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Run full analysis pipeline")
    analyze_parser.add_argument("repo_path", type=Path, help="Path to target repository (local or git URL)")
    analyze_parser.add_argument("--output", type=Path, default=Path(".cartography"), help="Output directory for artifacts")
    analyze_parser.add_argument("--incremental", action="store_true", help="Re-analyze only changed files via git diff")
    
    # query subcommand
    query_parser = subparsers.add_parser("query", help="Interactive Navigator query mode")
    query_parser.add_argument("cartography_dir", type=Path, help="Path to .cartography directory with existing artifacts")
    
    args = parser.parse_args()
    
    if args.command == "analyze":
        print(f"Running analysis on {args.repo_path}...")
        artifacts = run_pipeline(
            repo_path=args.repo_path,
            output_dir=args.output,
            incremental=args.incremental
        )
        print(f" Analysis complete. Artifacts saved to {args.output}")
        return 0
        
    elif args.command == "query":
        print(f"Starting Navigator query mode with {args.cartography_dir}...")
        navigator = NavigatorAgent(cartography_dir=args.cartography_dir)
        navigator.run_interactive()
        return 0
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
