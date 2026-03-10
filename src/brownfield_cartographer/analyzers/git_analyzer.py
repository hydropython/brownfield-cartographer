"""Git-based change velocity analysis for Surveyor Agent.

Uses git log --follow to track file history across renames.
Implements Pareto analysis (20/80 rule) for high-velocity core detection.
"""
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta


class GitVelocityAnalyzer:
    """Analyzes git history to compute change velocity metrics."""
    
    def __init__(self, repo_path: Path, days_lookback: int = 30):
        self.repo_path = repo_path
        self.days_lookback = days_lookback
        self._commit_cache: dict[str, int] = {}
    
    def get_change_velocity(self, file_path: str) -> int:
        """Get commit count for a file in the last N days (with --follow for renames).
        
        Returns:
            Number of commits affecting this file
        """
        if file_path in self._commit_cache:
            return self._commit_cache[file_path]
        
        try:
            # Use git log --follow to track across renames
            since_date = (datetime.utcnow() - timedelta(days=self.days_lookback)).strftime("%Y-%m-%d")
            
            result = subprocess.run(
                [
                    "git", "-C", str(self.repo_path),
                    "log", "--follow", "--since", since_date,
                    "--pretty=format:%H", "--", file_path
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            
            # Count unique commits
            commits = [line for line in result.stdout.strip().split("\n") if line]
            count = len(set(commits))
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            # Fail-open: return 0 if git unavailable or file not tracked
            count = 0
        
        self._commit_cache[file_path] = count
        return count
    
    def get_pareto_core(self, file_paths: list[str], threshold: float = 0.2) -> list[str]:
        """Identify the "high-velocity core" using Pareto (20/80) analysis.
        
        Args:
            file_paths: List of file paths to analyze
            threshold: Fraction of files that constitute the "core" (default: 20%)
        
        Returns:
            List of file paths in the high-velocity core (top 20% by commit count)
        """
        # Compute velocity for each file
        velocities = [(fp, self.get_change_velocity(fp)) for fp in file_paths]
        
        # Sort by velocity descending
        velocities.sort(key=lambda x: x[1], reverse=True)
        
        # Take top threshold% as "core"
        core_count = max(1, int(len(velocities) * threshold))
        core_files = [fp for fp, _ in velocities[:core_count]]
        
        return core_files
    
    def get_file_last_modified(self, file_path: str) -> Optional[datetime]:
        """Get the last commit timestamp for a file."""
        try:
            result = subprocess.run(
                [
                    "git", "-C", str(self.repo_path),
                    "log", "-1", "--pretty=format:%cI", "--", file_path
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            if result.stdout.strip():
                return datetime.fromisoformat(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
            pass
        return None