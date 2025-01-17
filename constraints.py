# constraints.py

from math import dist
from timefold.solver.score import (
    ConstraintFactory, Constraint, constraint_provider, HardSoftScore
)
from domain import (
    BuildingPlacement, Location, BuildingType, ZoneType
)


@constraint_provider
def define_constraints(constraint_factory: ConstraintFactory):
    """
    Return a list of constraints (Hard/Soft).
    """
    return [
        build_disallowed_location_constraint(constraint_factory),
        build_house_school_distance_constraint(constraint_factory),
        build_house_office_distance_constraint(constraint_factory),
        build_zoning_mismatch_constraint(constraint_factory),
        build_location_uniqueness_constraint(constraint_factory),
        build_cost_constraint(constraint_factory),
    ]


def build_disallowed_location_constraint(cf: ConstraintFactory) -> Constraint:
    """
    HARD constraint:
    If a BuildingPlacement is placed in a Location that doesn't allow that building type,
    penalize with 1 Hard point.
    """
    return (
        cf.for_each(BuildingPlacement)
        .filter(lambda bp: bp.location is not None
                           and bp.building_type not in bp.location.allowed_building_types)
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Building in disallowed location (HARD)")
    )


def build_house_school_distance_constraint(cf: ConstraintFactory) -> Constraint:
    """
    SOFT constraint:
    Penalize distance between House and School, to keep them close.
    """
    return (
        cf.for_each_unique_pair(BuildingPlacement)
        # Filter for House vs School
        .filter(lambda bp1, bp2:
                ((bp1.building_type == BuildingType.HOUSE and bp2.building_type == BuildingType.SCHOOL) or
                 (bp1.building_type == BuildingType.SCHOOL and bp2.building_type == BuildingType.HOUSE))
                and bp1.location is not None and bp2.location is not None)
        # Penalize the Euclidean distance
        .penalize(HardSoftScore.ONE_SOFT, lambda bp1, bp2: calc_distance(bp1, bp2))
        .as_constraint("Distance between HOUSE and SCHOOL (SOFT)")
    )


def build_house_office_distance_constraint(cf: ConstraintFactory) -> Constraint:
    """
    SOFT constraint:
    Penalize distance between House and Office, to reduce commutes.
    """
    return (
        cf.for_each_unique_pair(BuildingPlacement)
        .filter(lambda bp1, bp2:
                ((bp1.building_type == BuildingType.HOUSE and bp2.building_type == BuildingType.OFFICE) or
                 (bp1.building_type == BuildingType.OFFICE and bp2.building_type == BuildingType.HOUSE))
                and bp1.location is not None and bp2.location is not None)
        .penalize(HardSoftScore.ONE_SOFT, lambda bp1, bp2: calc_distance(bp1, bp2))
        .as_constraint("Distance between HOUSE and OFFICE (SOFT)")
    )


def build_location_uniqueness_constraint(cf: ConstraintFactory) -> Constraint:
    """
    HARD constraint:
    Ensure that each Location can only have one BuildingPlacement.
    """
    return (
        cf.for_each_unique_pair(BuildingPlacement)
        .filter(lambda bp1, bp2: bp1.location is not None and bp1.location == bp2.location)
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Location uniqueness (HARD)")
    )


def build_zoning_mismatch_constraint(cf: ConstraintFactory) -> Constraint:
    """
    HARD constraint:
    If a building type is not allowed in a certain zone, penalize Hard.
    Example logic: if zone is RESTRICTED, no buildings allowed (except if you want some exceptions).
                  If zone is INDUSTRIAL, you might not want houses, etc.
    """
    return (
        cf.for_each(BuildingPlacement)
        .filter(lambda bp: bp.location is not None
                           and not is_building_type_allowed_in_zone(bp.building_type, bp.location.zone))
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Zoning mismatch (HARD)")
    )


def build_cost_constraint(cf: ConstraintFactory) -> Constraint:
    """
    SOFT constraint:
    Penalize building in high-cost locations.
    The higher the location cost factor, the bigger the penalty.
    """
    return (
        cf.for_each(BuildingPlacement)
        .filter(lambda bp: bp.location is not None)
        .penalize(
            HardSoftScore.ONE_SOFT,
            lambda bp: bp.location.cost_factor
        )
        .as_constraint("Building cost minimization (SOFT)")
    )


def calc_distance(bp1: BuildingPlacement, bp2: BuildingPlacement) -> float:
    p1 = (bp1.location.x, bp1.location.y)
    p2 = (bp2.location.x, bp2.location.y)
    return dist(p1, p2)


def is_building_type_allowed_in_zone(building_type: BuildingType, zone: ZoneType) -> bool:
    """
    Example logic:
      - No building in RESTRICTED
      - Houses allowed in RESIDENTIAL, MIXED, COMMERCIAL
      - Offices allowed in COMMERCIAL, MIXED
      - Shops in COMMERCIAL, MIXED
      - Industry in INDUSTRIAL, maybe also MIXED
    """
    if zone == ZoneType.RESTRICTED:
        return False

    if building_type == BuildingType.HOUSE and zone in [ZoneType.RESIDENTIAL, ZoneType.MIXED, ZoneType.COMMERCIAL]:
        return True
    if building_type == BuildingType.OFFICE and zone in [ZoneType.COMMERCIAL, ZoneType.MIXED]:
        return True
    if building_type == BuildingType.SHOP and zone in [ZoneType.COMMERCIAL, ZoneType.MIXED]:
        return True
    if building_type == BuildingType.SCHOOL and zone in [ZoneType.RESIDENTIAL, ZoneType.MIXED]:
        return True
    if building_type == BuildingType.HOSPITAL and zone in [ZoneType.RESIDENTIAL, ZoneType.MIXED]:
        return True
    if building_type == BuildingType.PHARMACY and zone in [ZoneType.RESIDENTIAL, ZoneType.MIXED, ZoneType.COMMERCIAL]:
        return True

    # If not matched, return False
    return False
