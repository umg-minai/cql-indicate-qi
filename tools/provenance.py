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


def generation_info():
    """How a generated file was made, as data."""
    directory, commit = data_dictionary.ensure_data_dictionary_clone()
    tool_commit = _git(TOOLS_DIRECTORY, "rev-parse", "HEAD")
    # Only the tool itself counts: the generated files in the other folders of the repository must not.
    changed = None if tool_commit is None else bool(
        _git(TOOLS_DIRECTORY, "status", "--porcelain", "--untracked-files=no", "--", "."))
    return {"tool_version": tool_commit,
            "tool_uncommitted_changes": changed,
            "generated_on": datetime.date.today(),
            "data_dictionary": {"repository": data_dictionary.REPOSITORY_URL,
                                "branch": data_dictionary.BRANCH,
                                "commit": commit,
                                "commit_date": _git(directory, "log", "-1", "--format=%cI", commit) or "unknown"}}


def generation_stamp():
    """Lines that say how a generated file was made (for the comment at the top of a CQL file)."""
    info = generation_info()
    dictionary = info["data_dictionary"]
    tool = info["tool_version"] or "unknown (not a git checkout)"
    if info["tool_uncommitted_changes"]:
        tool += " (with uncommitted changes)"
    return [f"Tool version:     {tool}",
            f"Generated on:     {info['generated_on'].isoformat()}",
            f"Data dictionary:  {dictionary['repository']}",
            f"  branch:         {dictionary['branch']}",
            f"  commit:         {dictionary['commit']}",
            f"  commit date:    {dictionary['commit_date']}"]
