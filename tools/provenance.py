"""Information about how a generated file was made (tool version, date, data dictionary)."""

import datetime
import pathlib
import subprocess

import data_dictionary


TOOLS_DIRECTORY = pathlib.Path(__file__).parent


def _git(directory, *args):
    try:
        process = subprocess.run(["git", *args], cwd=directory, capture_output=True, check=True, timeout=30)
        return process.stdout.decode().strip()
    except (subprocess.SubprocessError, OSError):
        return None


def tool_version():
    """Commit hash of the repository this tool is in, with a note if there are uncommitted changes."""
    commit = _git(TOOLS_DIRECTORY, "rev-parse", "HEAD")
    if commit is None:
        return "unknown (not a git checkout)"
    if _git(TOOLS_DIRECTORY, "status", "--porcelain", "--untracked-files=no"):
        commit += " (with uncommitted changes)"
    return commit


def generation_stamp():
    """Lines that say how a generated file was made."""
    directory, commit = data_dictionary.ensure_data_dictionary_clone()
    commit_date = _git(directory, "log", "-1", "--format=%cI", commit) or "unknown"
    return [f"Tool version:     {tool_version()}",
            f"Generated on:     {datetime.date.today().isoformat()}",
            f"Data dictionary:  {data_dictionary.REPOSITORY_URL}",
            f"  branch:         {data_dictionary.BRANCH}",
            f"  commit:         {commit}",
            f"  commit date:    {commit_date}"]
