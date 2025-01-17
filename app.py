# app.py

import logging
import os
from flask import Flask, request, jsonify, send_from_directory
from typing import Any, Dict

from domain import (
    CityPlanSolution, BuildingPlacement, Location,
    BuildingType, ZoneType
)
from constraints import define_constraints, is_building_type_allowed_in_zone, calc_distance
from solve import solve_city_plan
import json

app = Flask(__name__, static_folder="static")
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

TEST_DATA_DIR = "test_data"  # mapīte, kur saglabāti PlanSmall/PlanMedium/PlanLarge JSON

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/solve", methods=["GET", "POST"])
def solve_endpoint():
    """
    GET -> ielasa default "PlanSmall"
    POST -> sagaida custom JSON
    """
    if request.method == "GET":
        small_file = os.path.join(TEST_DATA_DIR, "PlanSmall.json")
        problem = load_solution_from_json(small_file)
        best_solution = solve_city_plan(problem)
        breakdown = get_score_breakdown(best_solution)
        return jsonify(solution_to_dict(best_solution, breakdown))

    if request.method == "POST":
        data = request.get_json() or {}
        LOGGER.info(f"POST /solve with data: {data}")

        problem = build_solution_from_data(data)
        best_solution = solve_city_plan(problem)
        breakdown = get_score_breakdown(best_solution)
        return jsonify(solution_to_dict(best_solution, breakdown))

@app.route("/solve/<plan_name>", methods=["GET"])
def solve_with_plan(plan_name):
    """
    GET /solve/PlanMedium  -> ielasīs test_data/PlanMedium.json
    GET /solve/PlanLarge   -> ielasīs test_data/PlanLarge.json
    """
    file_name = f"{plan_name}.json"
    path = os.path.join(TEST_DATA_DIR, file_name)
    if not os.path.exists(path):
        return jsonify({"error": f"No such plan file: {file_name}"}), 404

    problem = load_solution_from_json(path)
    best_solution = solve_city_plan(problem)
    breakdown = get_score_breakdown(best_solution)
    return jsonify(solution_to_dict(best_solution, breakdown))

def load_solution_from_json(path: str) -> CityPlanSolution:
    """
    Ielasa no faila
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return build_solution_from_data(data)

def build_solution_from_data(data: Dict[str, Any]) -> CityPlanSolution:
    sol_id = data.get("id", "NoNamePlan")
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
        building_list.append(BuildingPlacement(
            id=int(b["id"]),
            building_type=BuildingType(b["building_type"]),
            location=None
        ))

    return CityPlanSolution(
        id=sol_id,
        location_list=location_list,
        building_placement_list=building_list
    )

def get_score_breakdown(solution: CityPlanSolution):
    """
    Manuāla "constraint breakdown" atkārtota no constraints.py
    """
    placements = solution.building_placement_list
    breakdown = []

    # Disallowed (HARD)
    name = "Building in disallowed location (HARD)"
    disallowed_count = 0
    for bp in placements:
        if bp.location and bp.building_type not in bp.location.allowed_building_types:
            disallowed_count += 1
    breakdown.append({
        "constraintName": name,
        "hardPenalty": -disallowed_count,
        "softPenalty": 0
    })

    # Zoning mismatch (HARD)
    name = "Zoning mismatch (HARD)"
    zoning_count = 0
    for bp in placements:
        if bp.location and not is_building_type_allowed_in_zone(bp.building_type, bp.location.zone):
            zoning_count += 1
    breakdown.append({
        "constraintName": name,
        "hardPenalty": -zoning_count,
        "softPenalty": 0
    })

    # Location uniqueness (HARD)
    name = "Location uniqueness (HARD)"
    uniq_count = 0
    n = len(placements)
    for i in range(n):
        for j in range(i+1, n):
            bp1 = placements[i]
            bp2 = placements[j]
            if bp1.location and bp2.location and bp1.location == bp2.location:
                uniq_count += 1
    breakdown.append({
        "constraintName": name,
        "hardPenalty": -uniq_count,
        "softPenalty": 0
    })

    # House-School distance (SOFT)
    name = "Distance between HOUSE and SCHOOL (SOFT)"
    hs_sum = 0.0
    for i in range(n):
        for j in range(i+1, n):
            bp1 = placements[i]
            bp2 = placements[j]
            if bp1.location and bp2.location:
                if ((bp1.building_type == BuildingType.HOUSE and bp2.building_type == BuildingType.SCHOOL)
                   or (bp1.building_type == BuildingType.SCHOOL and bp2.building_type == BuildingType.HOUSE)):
                    hs_sum += calc_distance(bp1, bp2)
    breakdown.append({
        "constraintName": name,
        "hardPenalty": 0,
        "softPenalty": -hs_sum
    })

    # House-Office distance (SOFT)
    name = "Distance between HOUSE and OFFICE (SOFT)"
    ho_sum = 0.0
    for i in range(n):
        for j in range(i+1, n):
            bp1 = placements[i]
            bp2 = placements[j]
            if bp1.location and bp2.location:
                if ((bp1.building_type == BuildingType.HOUSE and bp2.building_type == BuildingType.OFFICE)
                   or (bp1.building_type == BuildingType.OFFICE and bp2.building_type == BuildingType.HOUSE)):
                    ho_sum += calc_distance(bp1, bp2)
    breakdown.append({
        "constraintName": name,
        "hardPenalty": 0,
        "softPenalty": -ho_sum
    })

    # Building cost (SOFT)
    name = "Building cost minimization (SOFT)"
    cost_sum = 0.0
    for bp in placements:
        if bp.location:
            cost_sum += bp.location.cost_factor
    breakdown.append({
        "constraintName": name,
        "hardPenalty": 0,
        "softPenalty": -cost_sum
    })

    return breakdown

def solution_to_dict(solution: CityPlanSolution, breakdown):
    placements_out = []
    for bp in solution.building_placement_list:
        loc_data = None
        if bp.location:
            loc_data = {
                "id": bp.location.id,
                "name": bp.location.name,
                "x": bp.location.x,
                "y": bp.location.y,
                "zone": bp.location.zone.value,
                "cost_factor": bp.location.cost_factor
            }
        placements_out.append({
            "id": bp.id,
            "building_type": bp.building_type.value,
            "location": loc_data
        })

    return {
        "solution_id": solution.id,
        "score": str(solution.score) if solution.score else "None",
        "placements": placements_out,
        "constraintBreakdown": breakdown
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
