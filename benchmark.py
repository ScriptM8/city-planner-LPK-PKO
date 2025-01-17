import json, time
from timefold.solver import SolverFactory
from timefold.solver.config import (
    SolverConfig, ScoreDirectorFactoryConfig, TerminationConfig, Duration
)
from domain import CityPlanSolution, Location, BuildingPlacement, BuildingType, ZoneType
from constraints import define_constraints


def load_solution_from_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Atkārto build_solution_from_json loģiku
    sol_id = data.get("id", "PlanX")
    locs_raw = data.get("locations", [])
    bld_raw = data.get("buildings", [])

    location_list = []
    for loc in locs_raw:
        location_list.append(Location(
            id=int(loc["id"]),
            name=loc["name"],
            x=float(loc["x"]),
            y=float(loc["y"]),
            zone=ZoneType(loc["zone"]),
            cost_factor=float(loc.get("cost_factor", 1.0)),
            allowed_building_types=[
                BuildingType(bt) for bt in loc.get("allowed_building_types", [])
            ]
        ))

    building_list = []
    for b in bld_raw:
        building_list.append(
            BuildingPlacement(
                id=int(b["id"]),
                building_type=BuildingType(b["building_type"]),
                location=None
            )
        )

    return CityPlanSolution(
        id=sol_id,
        location_list=location_list,
        building_placement_list=building_list
    )


def run_solver(solution, local_search_type=None, time_limit_s=5):
    # Izveido config ar norādītu local_search
    solver_config = SolverConfig(
        solution_class=CityPlanSolution,
        entity_class_list=[BuildingPlacement],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=define_constraints
        ),
        termination_config=TerminationConfig(
            spent_limit=Duration(seconds=time_limit_s)
        )
    )
    # Ja local_search_type ir norādīts, pieseti
    if local_search_type:
        solver_config.local_search_type = local_search_type

    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    start = time.time()
    best_solution = solver.solve(solution)
    end = time.time()

    elapsed = end - start
    return best_solution.score, elapsed


def main():
    # Dažādi testa faili
    test_files = ["test_data/PlanSmall.json", "test_data/PlanMedium.json", "test_data/PlanLarge.json"]

    # Dažādas konfigurācijas
    configs = [
        {"name": "DefaultLS", "lsType": None},
        {"name": "LateAcceptance", "lsType": "LATE_ACCEPTANCE"},
        {"name": "TabuSearch", "lsType": "TABU_SEARCH"},
    ]

    # Tabulu ar rezultātiem
    print("TestFile, ConfigName, Score, TimeSec")

    for f in test_files:
        # Ielādē izejas risinājumu
        solution = load_solution_from_json(f)
        for cfg in configs:
            score, duration = run_solver(solution, local_search_type=cfg["lsType"], time_limit_s=5)
            print(f"{f}, {cfg['name']}, {score}, {duration:.3f}")


if __name__ == "__main__":
    main()
