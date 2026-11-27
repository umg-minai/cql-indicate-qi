import json
import subprocess
from dataclasses import dataclass
from typing import Dict, List

from data_dictionary import clone_directory, load_project, load_concept_set_versions
from terminology_from_data_dictionary.model import ConceptSetInfo


@dataclass
class ProjectConceptSet:
    group: str            # id of the group in the project file, e.g. "group-default"
    version: str          # version pinned in the project file
    info: ConceptSetInfo
    from_history: bool    # True if loaded from an older commit because the current version differs


def read_json_at_commit(path: str, commit: str):
    try:
        process = subprocess.run(["git", "show", f"{commit}:{path}"],
                                 cwd=clone_directory(),
                                 capture_output=True,
                                 check=True,
                                 timeout=60)
    except subprocess.CalledProcessError as e:
        error = e.stderr.decode(errors="replace")
        raise RuntimeError(f"Could not read {path} at commit {commit}: {error}") from None
    return json.loads(process.stdout)


def load_project_concept_sets(project_id: int,
                              concept_sets: Dict[int, Dict],
                              resolved_concept_sets: Dict[int, Dict]) -> List[ProjectConceptSet]:
    """Return the concept sets listed in the project, each in the version pinned there.

    If the pinned version is the current one, the current files are used. Otherwise the
    concept set is read from the data dictionary commit that belongs to the pinned version."""
    project = load_project(project_id)
    versions = None
    result = []
    for group in project["groups"]:
        for entry in group["conceptSets"]:
            concept_set_id, version = entry["id"], entry["version"]
            current = concept_sets.get(concept_set_id)
            if current is None:
                raise RuntimeError(f"Project {project_id} lists concept set {concept_set_id}, "
                                   f"which does not exist in the data dictionary")
            if current.get("version") == version:
                info = ConceptSetInfo(current, resolved_concept_sets[concept_set_id])
                from_history = False
            else:
                if versions is None:
                    versions = load_concept_set_versions()
                commit = versions.get(str(concept_set_id), {}).get(version)
                if commit is None:
                    raise RuntimeError(f"Project {project_id} pins version {version} of concept set "
                                       f"{concept_set_id}, which is not listed in concept_sets_versions.json")
                concept_set = read_json_at_commit(f"concept_sets/{concept_set_id}.json", commit)
                resolved = read_json_at_commit(f"concept_sets_resolved/{concept_set_id}.json", commit)
                if concept_set.get("version") != version:
                    raise RuntimeError(f"Concept set {concept_set_id} at commit {commit} has version "
                                       f"{concept_set.get('version')}, not the pinned version {version}")
                info = ConceptSetInfo(concept_set, resolved)
                from_history = True
            result.append(ProjectConceptSet(group["id"], version, info, from_history))
    return result
