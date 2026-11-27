from abc import ABC
from dataclasses import dataclass
from typing import List, Optional, Dict

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


# Configuration

class OMOPConceptReference(BaseModel):
    concept_id: int
    name: str
    # only needed for concepts that are in no concept set (no domain known)
    omop_record: Optional[str] = None
    # also only needed for concepts that are in no concept set: the vocabulary is part of the code names in CQL
    vocabulary: Optional[str] = None
    descendants: bool = Field(default=False,
                              validation_alias=AliasChoices("with_descendants", "descendants"))


class PriorityEntry(BaseModel):
    """Settings of one concept of a concept set."""
    concept_id: int
    name: str
    priority: Optional[int] = None
    redundancy_group: Optional[str] = None
    is_preferred: Optional[bool] = None

    @model_validator(mode="after")
    def check_redundancy_fields(self):
        if (self.redundancy_group is None) != (self.is_preferred is None):
            raise ValueError(f"Concept {self.concept_id}: redundancy_group and is_preferred must be given together")
        return self


class Mapping(BaseModel, ABC):
    model_config = ConfigDict(extra="forbid")
    # Concept set entries: the exact name of the concept set in the data dictionary.
    # Category entries: a label that can be used in inject comments.
    name: str
    cql_definition: Optional[str] = None
    # TODO: allow include/exclude with descendants
    exclude: List[OMOPConceptReference] = Field(default=[])
    include: List[OMOPConceptReference] = Field(default=[])


class ConceptSetMapping(Mapping):
    priorities: List[PriorityEntry] = Field(default=[], validation_alias=AliasChoices("concepts", "priorities"))
    # If given, only these concepts of the concept set(s) are used
    only: List[OMOPConceptReference] = Field(default=[])
    # False: generate-cql writes no CQL library for this concept set
    cql: bool = True
    # False: the QIs do not use this concept set of the project. It is in no output.
    used: bool = True

    @model_validator(mode="after")
    def check_unused_has_no_settings(self):
        if not self.used and (self.include or self.exclude or self.only or self.priorities):
            raise ValueError(f"Concept set '{self.name}': used: false cannot be combined with settings for its concepts")
        return self


class CategoryMapping(Mapping):
    category: str
    subcategory: str


class AdditionalConceptSet(BaseModel):
    """A set of concepts that is not a concept set of the data dictionary."""
    model_config = ConfigDict(extra="forbid")
    name: str
    omop_record: str
    # If given, the CQL library also has a definition of this name that lists the concepts of the
    # set as OMOP concepts (the QI code needs that for the ingredients of the insulin drugs)
    concepts_define: Optional[str] = None
    concepts: List[OMOPConceptReference]


class Configuration(BaseModel):
    mappings: List[ConceptSetMapping | CategoryMapping]
    additional_concept_sets: List[AdditionalConceptSet] = Field(default=[])


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
    redundancy_group: Optional[str] = None
    is_preferred: Optional[bool] = None


@dataclass
class Output:
    concept_sets: List[ConceptSetInfo]
    concepts: List[ConceptOutput]
    repository_url: str
    commit: str
