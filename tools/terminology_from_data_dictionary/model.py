from abc import ABC
from dataclasses import dataclass
from typing import List, Optional, Dict

from pydantic import BaseModel, Field


# Configuration

class OMOPConceptReference(BaseModel):
    concept_id: int
    name: str
    descendants: bool = Field(default=False)


class PriorityEntry(BaseModel):
    concept_id: int
    name: str
    priority: int


class Mapping(BaseModel, ABC):
    name: str
    cql_definition: Optional[str] = None
    # TODO: allow include/exclude with descendants
    exclude: List[OMOPConceptReference] = Field(default=[])
    include: List[OMOPConceptReference] = Field(default=[])


class ConceptSetMapping(Mapping):
    concept_sets: List[str]
    priorities: List[PriorityEntry] = Field(default=[])


class CategoryMapping(Mapping):
    category: str
    subcategory: str


class Configuration(BaseModel):
    mappings: List[ConceptSetMapping | CategoryMapping]


# Output

@dataclass
class ConceptSetInfo:
    concept_set: Dict
    resolved_concept_set: Dict

    @property
    def concept_set_id(self):
        return self.concept_set.get("id")

    @property
    def name(self):
        return self.concept_set.get("name")

    @property
    def expression(self):
        return self.concept_set.get("expression").get("items")

    @property
    def resolved_concepts(self):
        return self.resolved_concept_set.get("resolvedConcepts")


@dataclass
class ConceptOutput:
    concept_set: Optional[ConceptSetInfo]
    concept_id: int
    name: str
    descendants: bool = False
    vocabulary: str = ""
    concept_code: str = ""
    priority: Optional[int] = None


@dataclass
class Output:
    concept_sets: List[ConceptSetInfo]
    concepts: List[ConceptOutput]
    repository_url: str
    commit: str
