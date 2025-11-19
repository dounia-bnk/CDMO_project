import time, math, os, json
import pulp
from pulp import PulpSolverError
from utils.symmetry import round_robin_weeks

def get_solver(name: str, msg: bool):
    s = name.lower()
    if s == "highs":
        return pulp.HiGHS_CMD(timeLimit=300, msg=msg, threads=1)
    if s == "cbc":
        return pulp.PULP_CBC_CMD(timeLimit=300, msg=msg)
    raise ValueError("solver must be 'highs' or 'cbc'")

def solve_tournament(n: int, verbose: bool = False, solver_name: str = "highs"):
    teams = list(range(1, n + 1))
    weeks = list(range(1, n))
    periods = list(range(1, n // 2 + 1))
    week_pairs = round_robin_weeks(n)
    prob = pulp.LpProblem("STS", pulp.LpMinimize)
    week_of, matches = {}, []
    for w_idx, pairs in enumerate(week_pairs, start=1):
        for ij in pairs:
            i, j = ij
            week_of[(i, j)] = w_idx
            matches.append((i, j))
    y = pulp.LpVariable.dicts("y", [(i, j, p) for (i, j) in matches for p in periods], 0, 1, cat="Binary")
    h = pulp.LpVariable.dicts("h", matches, 0, 1, cat="Binary")
    home_count = pulp.LpVariable.dicts("home_count", teams, lowBound=0, upBound=len(weeks), cat="Continuous")
    z_min = pulp.LpVariable("z_min", lowBound=0, cat="Continuous")
    z_max = pulp.LpVariable("z_max", lowBound=0, upBound=len(weeks), cat="Continuous")
    for ij in matches:
        i, j = ij
        prob += pulp.lpSum(y[(i, j, p)] for p in periods) == 1
    for w in weeks:
        for p in periods:
            prob += pulp.lpSum(y[(i, j, p)] for (i, j) in week_pairs[w - 1]) == 1
    for t in teams:
        for p in periods:
            prob += pulp.lpSum(y[(i, j, p)] for (i, j) in matches if i == t or j == t) <= 2
    for i in teams:
        left = pulp.lpSum(h[(i, j)] for (a, j) in matches if a == i)
        right = pulp.lpSum(1 - h[(k, i)] for (k, b) in matches if b == i)
        prob += home_count[i] == left + right
        prob += z_max >= home_count[i]
        prob += z_min <= home_count[i]
    for ij in week_pairs[0]:
        i, j = ij
        if 1 in (i, j):
            a, b = (i, j) if i < j else (j, i)
            prob += y[(a, b, 1)] == 1
            break
    target = (n - 1) / 2.0
    d_plus = pulp.LpVariable.dicts("d_plus", teams, lowBound=0, cat="Continuous")
    d_minus = pulp.LpVariable.dicts("d_minus", teams, lowBound=0, cat="Continuous")
    for i in teams:
        prob += home_count[i] - target == d_plus[i] - d_minus[i]
    prob += pulp.lpSum(d_plus[i] + d_minus[i] for i in teams)
    start = time.time()
    try:
        solver = get_solver(solver_name, verbose)
        prob.solve(solver)
    except PulpSolverError:
        solver = get_solver("cbc", verbose)
        prob.solve(solver)
        solver_name = "cbc"
    wall = int(math.floor(time.time() - start))
    status = pulp.LpStatus[prob.status]
    optimal = prob.status == pulp.LpStatusOptimal
    if not optimal:
        wall = 300
    feasible = any((pulp.value(y[(i, j, p)]) or 0) > 0.5 for (i, j) in matches for p in periods)
    obj_val = int(round(pulp.value(prob.objective))) if pulp.value(prob.objective) is not None else None
    solution = []
    if feasible:
        solution = [[None for x in weeks] for q in periods]
        for ij in matches:
            i, j = ij
            w = week_of[(i, j)]
            chosen = None
            for p in periods:
                val = pulp.value(y[(i, j, p)]) or 0
                if val > 0.5:
                    chosen = p
                    break
            hij = int(round(pulp.value(h[(i, j)]) or 0))
            home, away = (i, j) if hij == 1 else (j, i)
            solution[chosen - 1][w - 1] = [home, away]
    return {"time": wall, "optimal": optimal, "obj": obj_val, "sol": solution, "solver": solver_name, "status": status}

def save_merge_json(n: int, key: str, payload: dict, base_dir: str = "res/MIP"):
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"{n}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
    data[key] = {"time": payload["time"], "optimal": bool(payload["optimal"]), "obj": payload["obj"], "sol": payload["sol"], "solver": payload["solver"], "status": payload["status"]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    return path

def main():
    ns = [6, 8, 10, 12, 14]
    solvers = ["highs", "cbc"]
    for n in ns:
        for name in solvers:
            print(f"start n={n} solver={name}")
            res = solve_tournament(n, verbose=False, solver_name=name)
            key = f"{res['solver']}_dev"
            out_path = save_merge_json(n, key, res, base_dir="res/MIP")
            print(f"saved {out_path} key={key}")

if __name__ == "__main__":
    main()