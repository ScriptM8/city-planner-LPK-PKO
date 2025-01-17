# solve.py

from timefold.solver import SolverFactory
from timefold.solver.config import (
    SolverConfig,
    ScoreDirectorFactoryConfig,
    TerminationConfig,
    Duration
)
import logging

from domain import (
    CityPlanSolution,
    BuildingPlacement,
    Location,
    BuildingType,
    ZoneType
)
from constraints import define_constraints

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("city-planner")


def create_initial_solution() -> CityPlanSolution:
    """
    Demo dataset including:
      - 4 Locations with different zones and cost_factors
      - 4 BuildingPlacements of different types
      - We'll let the solver assign each building to a location
    """
    # Define locations
    loc1 = Location(
        id=1,
        name="Loc1",
        x=0.0,
        y=0.0,
        zone=ZoneType.RESIDENTIAL,
        cost_factor=3.0,
        allowed_building_types=[BuildingType.HOUSE, BuildingType.SCHOOL, BuildingType.HOSPITAL]
    )
    loc2 = Location(
        id=2,
        name="Loc2",
        x=10.0,
        y=0.0,
        zone=ZoneType.COMMERCIAL,
        cost_factor=7.0,
        allowed_building_types=[BuildingType.OFFICE, BuildingType.SHOP, BuildingType.PHARMACY]
    )
    loc3 = Location(
        id=3,
        name="Loc3",
        x=5.0,
        y=5.0,
        zone=ZoneType.MIXED,
        cost_factor=10.0,
        allowed_building_types=[BuildingType.HOUSE, BuildingType.OFFICE, BuildingType.SCHOOL, BuildingType.SHOP]
    )
    loc4 = Location(
        id=4,
        name="Loc4",
        x=20.0,
        y=5.0,
        zone=ZoneType.RESTRICTED,
        cost_factor=1.0,  # Cheap, but restricted
        allowed_building_types=[]
    )

    # Building placements
    bp1 = BuildingPlacement(
        id=101,
        building_type=BuildingType.HOUSE
    )
    bp2 = BuildingPlacement(
        id=102,
        building_type=BuildingType.SCHOOL
    )
    bp3 = BuildingPlacement(
        id=103,
        building_type=BuildingType.OFFICE
    )
    bp4 = BuildingPlacement(
        id=104,
        building_type=BuildingType.SHOP
    )

    return CityPlanSolution(
        id="Demo",
        building_placement_list=[bp1, bp2, bp3, bp4],
        location_list=[loc1, loc2, loc3, loc4]
    )


def solve_city_plan(problem: CityPlanSolution) -> CityPlanSolution:
    solver_factory = SolverFactory.create(
        SolverConfig(
            solution_class=CityPlanSolution,
            entity_class_list=[BuildingPlacement],
            score_director_factory_config=ScoreDirectorFactoryConfig(
                constraint_provider_function=define_constraints
            ),
            termination_config=TerminationConfig(
                spent_limit=Duration(seconds=5)
            ),
        )
    )
    solver_factory.construction_heuristic_type = "FIRST_FIT"
    solver_factory.local_search_type = "TABU_SEARCH"
    solver = solver_factory.build_solver()

    best_solution = solver.solve(problem)
    return best_solution


def main():
    solution = solve_city_plan()
    LOGGER.info("=== BEST SOLUTION FOUND ===")
    for bp in solution.building_placement_list:
        loc_name = bp.location.name if bp.location else "None"
        LOGGER.info(f"BuildingPlacement {bp.id} ({bp.building_type.value}) => {loc_name}")
    LOGGER.info(f"Score = {solution.score}")


if __name__ == "__main__":
    main()
