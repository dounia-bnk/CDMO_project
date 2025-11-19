% phase2_optimize.mzn
% Ultra-fast home/away balancing

% Parameters
int: n;                          
int: W = n - 1;                  % Number of weeks
int: P = n div 2;                % Number of periods per week
set of int: TEAMS = 1..n;
set of int: WEEKS = 1..W;
set of int: PERIODS = 1..P;

% Input solution from phase 1 - format: [periods][weeks][home,away]
array[PERIODS, WEEKS, 1..2] of int: initial_solution;

% Decision Variables: Simple swap flags
array[WEEKS, PERIODS] of var 0..1: swap;

% Derived home and away arrays based on swap decisions
array[WEEKS, PERIODS] of var TEAMS: home;
array[WEEKS, PERIODS] of var TEAMS: away;

constraint forall(i in WEEKS, j in PERIODS)(
    home[i,j] = if swap[i,j] = 0 then initial_solution[j,i,1] else initial_solution[j,i,2] endif
);

constraint forall(i in WEEKS, j in PERIODS)(
    away[i,j] = if swap[i,j] = 0 then initial_solution[j,i,2] else initial_solution[j,i,1] endif
);

% Precompute initial home/away counts for each team
array[TEAMS] of int: init_home_count = [
    sum([1 | i in WEEKS, j in PERIODS where initial_solution[j,i,1] = t]) | t in TEAMS
];

array[TEAMS] of int: init_away_count = [
    sum([1 | i in WEEKS, j in PERIODS where initial_solution[j,i,2] = t]) | t in TEAMS
];

% Correct imbalance calculation
var int: total_imbalance = 
    sum(t in TEAMS)(
        abs(
            (init_home_count[t] + 
             sum([swap[i,j] | i in WEEKS, j in PERIODS where initial_solution[j,i,2] = t]) - 
             sum([swap[i,j] | i in WEEKS, j in PERIODS where initial_solution[j,i,1] = t]))
            - 
            (init_away_count[t] + 
             sum([swap[i,j] | i in WEEKS, j in PERIODS where initial_solution[j,i,1] = t]) - 
             sum([swap[i,j] | i in WEEKS, j in PERIODS where initial_solution[j,i,2] = t]))
        )
    );

% --- OPTIMIZED SEARCH STRATEGY ---
solve :: int_search(
    [swap[i,j] | i in WEEKS, j in PERIODS],
    dom_w_deg,
    indomain_min,
    complete
) minimize total_imbalance;

% Output - same format as phase 1: [periods][weeks][home,away]
output [
  "[" ++ 
  join(", ", [
    "[" ++ join(", ", [
      "[" ++ show(home[w,p]) ++ "," ++ show(away[w,p]) ++ "]" 
      | w in WEEKS
    ]) ++ "]"
    | p in PERIODS
  ]) ++ "]"
];