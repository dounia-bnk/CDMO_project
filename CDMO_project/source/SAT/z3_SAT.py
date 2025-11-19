from z3 import *
import os
import json

# I will use sequential encoding from the labs because it is more
# efficient compared to naive pairwise encoding for constraints

def at_least_one_seq(bool_vars):
  return Or(bool_vars)

def at_most_one_seq(bool_vars, name):
  constraints = []
  n = len(bool_vars)
  s = [Bool(f"s_{name}_{i}") for i in range(n - 1)]

  constraints.append(Or(Not(bool_vars[0]), s[0]))
  constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
  for i in range(1, n - 1):
      constraints.append(Or(Not(bool_vars[i]), s[i]))
      constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
      constraints.append(Or(Not(s[i-1]), s[i]))

  return And(constraints)

def exactly_one_seq(bool_vars, name):
  return And(at_least_one_seq(bool_vars), at_most_one_seq(bool_vars, name))

def at_least_k_seq(bool_vars, k, name):
  return at_most_k_seq([Not(var) for var in bool_vars], len(bool_vars)-k, name)

def at_most_k_seq(bool_vars, k, name):
  constraints = []
  n = len(bool_vars)
  s = [[Bool(f"s_{name}_{i}_{j}") for j in range(k)] for i in range(n - 1)]

  constraints.append(Or(Not(bool_vars[0]), s[0][0]))
  constraints += [Not(s[0][j]) for j in range(1, k)]

  for i in range(1, n-1):
    constraints.append(Or(Not(bool_vars[i]), s[i][0]))
    constraints.append(Or(Not(s[i-1][0]), s[i][0]))
    constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][k-1])))

    for j in range(1, k):
      constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][j-1]), s[i][j]))
      constraints.append(Or(Not(s[i-1][j]), s[i][j]))

  constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2][k-1])))

  return And(constraints)

def exactly_k_seq(bool_vars, k, name):
  return And(at_most_k_seq(bool_vars, k, name), at_least_k_seq(bool_vars, k, name))

########################################

def validate_solution(solution, n):
    """
    Validate that a generated tournament schedule meets all constraints.
    Args:
        solution: The schedule to validate, as a periods × weeks matrix of [home, away] pairs
        n: Number of teams in the tournament
    Returns:
        bool: True if solution is valid, False otherwise with explanation printed
    """
    weeks = n - 1
    periods = n // 2

    # 1. Check solution structure - must have correct number of periods and weeks
    if len(solution) != periods:
        return False

    # 2. Check every team plays every other team exactly once
    all_games = []
    for period in solution:
        # Each period should have one game per week
        if len(period) != weeks:
            return False
        for week_games in period:
            home, away = week_games
            # A team can't play itself
            if home == away:
                print(f"Invalid game: team {home} plays itself")
                return False
            # Store game as sorted tuple to check uniqueness
            all_games.append((min(home, away), max(home, away)))

    # Generate all possible unique pairings we expect to see
    expected_games = set()
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            expected_games.add((i, j))

    # Check if we have exactly the expected games, no more no less
    if set(all_games) != expected_games:
        print("Teams got paired more than one time")
        return False

    # 3. Check every team plays exactly once per week
    for w in range(weeks):
        weekly_teams = set()
        for p in range(periods):
            game = solution[p][w]
            home, away = game
            # Check if either team already played this week
            if home in weekly_teams:
                print(f"Team {home} plays multiple times in week {w+1}")
                return False
            if away in weekly_teams:
                print(f"Team {away} plays multiple times in week {w+1}")
                return False
            weekly_teams.add(home)
            weekly_teams.add(away)

        # Check all teams played this week
        if len(weekly_teams) != n:
            print(f"Not all teams played in week {w+1}")
            return False

    # 4. Check no team plays more than twice in any period across tournament
    for t in range(1, n+1):
        for p in range(periods):
            appearances = 0
            for w in range(weeks):
                game = solution[p][w]
                if t in game:
                    appearances += 1
            if appearances > 2:
                print(f"Team {t} appears {appearances} times in period {p+1}")
                return False

    return True

####################################

def Sat_solution(n,sb):
  # n: Number of teams (must be even)

  # Initialize Z3 solver
  solver = Solver()
  # Set timeout
  solver.set("timeout", 300 * 1000)

  # Set number of weeks and periods
  weeks = n - 1
  periods = n // 2

  # x[w][p][t1][t2] week, period, team 1 vs team 2"
  x = [[[[Bool(f"x_{w}_{p}_{t1}_{t2}") for t2 in range(n)] for t1 in range(n)] for p in range(periods)] for w in range(weeks)]

  # Every pair of teams plays exactly once
  for t1 in range(n):
    for t2 in range(t1 + 1, n):
      games = []
      for w in range(weeks):
        for p in range(periods):
          games.append(x[w][p][t1][t2])  # t1 vs t2
          games.append(x[w][p][t2][t1])  # t2 vs t1
      # add exactly one
      solver.add(exactly_one_seq(games, f"pair_{t1}_{t2}"))

  # Every team plays exactly once per week
  for t1 in range(n):
    for w in range(weeks):
      games_in_week = []
      for p in range(periods):
        for t2 in range(n):
          if t2 != t1:
            games_in_week.append(x[w][p][t1][t2])  # t1 vs t2
            games_in_week.append(x[w][p][t2][t1])  # t2 vs t1
      # add exactly one
      solver.add(exactly_one_seq(games_in_week, f"team_{t1}_week_{w}"))

  # Each period in each week has exactly one game
  for w in range(weeks):
    for p in range(periods):
      games_in_slot = []
      for t1 in range(n):
        for t2 in range(n):
          if t1 != t2:
            games_in_slot.append(x[w][p][t1][t2])
      # add exactly one
      solver.add(exactly_one_seq(games_in_slot, f"week_{w}_period_{p}"))

  # Every team plays at most twice in the same period across all weeks
  for t1 in range(n):
    for p in range(periods):
      games_in_period = []
      for w in range(weeks):
        for t2 in range(n):
          if t2 != t1:
            games_in_period.append(x[w][p][t1][t2])  # t1 vs t2
            games_in_period.append(x[w][p][t2][t1])  # t2 vs t1
      # At most two appearances per period across weeks
      solver.add(at_most_k_seq(games_in_period, 2, f"team_{t1}_period_{p}"))

  # No team plays against itself
  for w in range(weeks):
    for p in range(periods):
      for t in range(n):
        solver.add(Not(x[w][p][t][t]))

  import time
  start_time = time.time()
  # Reduce search space by Symmetry Breaking
  if sb == True:
    # 1. Fix first week assignments
    for p in range(n // 2):
      t1 = 2 * p
      t2 = 2 * p + 1
      solver.add(x[0][p][t1][t2])

    # 2. In all periods of all weeks, enforce home team has smaller index than away team
    for w in range(weeks):
      for p in range(periods):
        for t1 in range(n):
          for t2 in range(n):
            if t1 >= t2:
              solver.add(Not(x[w][p][t1][t2]))

  # Solve
  result = solver.check()
  end_time = time.time()

  time_spent = float(end_time - start_time)

  # Handle results
  if result == sat:
    model = solver.model()
    weeks = n - 1
    periods = n // 2

    # Initialize empty schedule structure
    schedule = []
    for p in range(periods):
      period_schedule = []
      for w in range(weeks):
        # Find which game is assigned to this period and week
        game_found = False
        for t1 in range(n):
          for t2 in range(n):
            var_val = model.eval(x[w][p][t1][t2])
            if is_true(var_val):
              # Convert from 0-based to 1-based team numbering
              period_schedule.append([t1 + 1, t2 + 1])
              game_found = True
              break
          if game_found:
              break
      schedule.append(period_schedule)
    print(f"Solution found in {time_spent:.3f} seconds")
    return {
      "time": time_spent,
      "optimal": True,
      "obj": None,
      "sol": schedule}

  elif result == unsat:
    print(f"After checking for {time_spent:.3f} seconds")
    print("No solution exists")
    print(f"{'-'*50}")
    return {
      "time": time_spent,
      "optimal": True,
      "obj": None,
      "sol": None}

  else:
    print(f"No solution found within time limit (300 seconds)")
    return {
      "time": 300,
      "optimal": False,
      "obj": None,
      "sol": None}

##################################

def save_solution(results, n, sb):
  """Save solution in the required JSON format, appending if file exists"""
  os.makedirs("res/SAT", exist_ok=True)

  if results["sol"] is not None:
    approach = "Z3 + SB" if sb else "Z3 w/out SB"
    new_entry = {
      "time": int(results["time"]),
      "optimal": results["optimal"],
      "obj": None,
      "sol": results["sol"]
    }

    filename = f"res/SAT/{n}.json"

    # Load existing data if file exists
    if os.path.exists(filename):
      with open(filename, "r") as f:
        data = json.load(f)
    else:
      data = {}

    # Add or update the approach
    data[approach] = new_entry

    # Custom formatting
    with open(filename, "w") as f:
      f.write("{\n")
      for i, (key, value) in enumerate(data.items()):
        comma = "," if i < len(data) - 1 else ""
        f.write(f'  "{key}": {{\n')
        f.write(f'    "time": {value["time"]},\n')
        f.write(f'    "optimal": {str(value["optimal"]).lower()},\n')
        f.write(f'    "obj": "None",\n')
        sol_str = json.dumps(value["sol"], separators=(",", ":"))
        f.write(f'    "sol": {sol_str}\n')
        f.write(f'  }}{comma}\n')
      f.write("}\n")

      print(f"Solution saved to {filename} under approach '{approach}'")

#################################


# Number of teams
team_n = [6,8,10,12,14,16,18,20]
#team_n = [2,4,6]

Z3SB = []
Z3WOSB = []

symmetry_breaking = [False, True]
for sb in symmetry_breaking:
  for n in team_n:
    if sb == True:
      print("Z3 + SB")
    else:
      print("Z3 w/out SB")
    output = Sat_solution(n,sb)
    solution = output["sol"]
    if solution == None and output["optimal"] == True:
      if sb == True:
        Z3SB.append("UNSAT")
      else:
        Z3WOSB.append("UNSAT")
    # if solution excit print it
    if output["time"] == 300:
      if sb == True:
        Z3SB.append("N/A")
      else:
        Z3WOSB.append("N/A")
      print("N/A")
      print("-------------------------------")
      break
    if solution != None:
        if sb == True:
          Z3SB.append(int(output["time"]))
        else:
          Z3WOSB.append(int(output["time"]))
        print()
        print("          ", end="")
        for week in range(len(solution[0])):
            print(f"Week{week+1:<5}", end="  ")
        print()

        for period_idx in range(len(solution)):

          print(f"Period {period_idx+1}:", end=" ")

          for week_idx in range(len(solution[period_idx])):
              home = solution[period_idx][week_idx][0]
              away = solution[period_idx][week_idx][1]
              print(f"{home} vs {away:<4}", end="  ")
          print()
        print()
        if validate_solution(solution, n):
          print("Solution passed the validation test")
        else:
          print("Solution failed the validation test")
        save_solution(output, n, sb)
        print("-------------------------------")
print("Table 1: Results using Z3 + SB and Z3 w/out SB")
print()
print(f"# teams    ", end="")
print("Z3 + SB    ", end="")
print("Z3 w/out SB    ", end="")
print()
for i in range(2, n+1, 2):
  print(f"   {i:<8}", end="")
  try:
    print(f"   {Z3SB[int(i/2-1)]:<8}", end="")
  except:
    print(f"   {'N/A':<3}", end="")
  try:
    print(f"   {Z3WOSB[int(i/2-1)]:<7}", end="")
  except:
    print(f"   {'N/A':<3}", end="")
  print()

