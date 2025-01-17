from timefold.solver.domain import planning_entity, planning_solution, PlanningId, PlanningVariable
from timefold.solver.domain import PlanningEntityCollectionProperty, ProblemFactCollectionProperty, ValueRangeProvider
from timefold.solver.domain import PlanningScore
from timefold.solver.score import HardSoftScore
from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, List, Optional


class BuildingType(Enum):
    HOUSE = "HOUSE"
    SCHOOL = "SCHOOL"
    PHARMACY = "PHARMACY"
    HOSPITAL = "HOSPITAL"
    SHOP = "SHOP"
    OFFICE = "OFFICE"


class ZoneType(Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    MIXED = "MIXED"
    INDUSTRIAL = "INDUSTRIAL"
    RESTRICTED = "RESTRICTED"


@dataclass
class Location:
    """
    Problem Fact:
      - 'zone': which zone this location is in (RESIDENTIAL, COMMERCIAL, etc.)
      - 'cost_factor': an arbitrary numeric cost for building on this location.
      - 'allowed_building_types': which building types are definitely allowed here
        (used by the 'disallowed_location' constraint).
    """
    id: int
    name: str
    x: float
    y: float
    zone: ZoneType
    cost_factor: float = 1.0
    allowed_building_types: List[BuildingType] = field(default_factory=list)


@planning_entity
@dataclass
class BuildingPlacement:
    id: Annotated[int, PlanningId]
    building_type: BuildingType
    location: Annotated[
        Optional[Location],
        PlanningVariable(value_range_provider_refs=["locationRange"])
    ] = None


@planning_solution
@dataclass
class CityPlanSolution:
    id: str
    location_list: Annotated[
        List[Location],
        ProblemFactCollectionProperty,
        ValueRangeProvider(id="locationRange")
    ]
    building_placement_list: Annotated[
        List[BuildingPlacement],
        PlanningEntityCollectionProperty
    ]
    score: Annotated[HardSoftScore, PlanningScore] = field(default=None)
