include "alldifferent.mzn";

% Parameters
int: n;                          % Number of teams (must be even)
int: W = n - 1;                  % Number of weeks
int: P = n div 2;                % Number of periods per week
set of int: TEAMS = 1..n;
set of int: WEEKS = 1..W;
set of int: PERIODS = 1..P;


% Decision Variables
array[WEEKS, PERIODS] of var TEAMS: home;  % Now [week,period]
array[WEEKS, PERIODS] of var TEAMS: away;

% --- Essential Constraints ---

% 1. No team plays itself
constraint forall(i in WEEKS, j in PERIODS)(
    home[i,j] != away[i,j]
);

% 2. Each team plays exactly once per week
constraint forall(i in WEEKS)(
    alldifferent([home[i,j] | j in PERIODS] ++ [away[i,j] | j in PERIODS])
);

% 3. Each pair of teams plays exactly once
constraint forall(a, b in TEAMS where a < b)(
    sum([(home[i,j] = a /\ away[i,j] = b) | i in WEEKS, j in PERIODS]) +
    sum([(home[i,j] = b /\ away[i,j] = a) | i in WEEKS, j in PERIODS]) = 1
);

% 4. No team plays more than twice in any period
constraint forall(a in TEAMS, j in PERIODS)(
    count([home[i,j] | i in WEEKS], a) + 
    count([away[i,j] | i in WEEKS], a) <= 2
);

% --- Symmetry Breaking ---

% 5. Fix initial pairing in week 1
constraint home[1,1] = 1;  
constraint away[1,1] = 2; 
constraint home[1,2] = 3;
constraint away[1,2] = 4; 


constraint forall(i in WEEKS , j in PERIODS)(
    away[i,j] > home[i,j]
);

% 7. Period ordering in Week 1 (home teams increase)
constraint  forall(j in 2..P)(home[1,j] > home[1,j-1]);
constraint  forall(i in 2..W)(home[i,1] >= home[i-1,1]);



% --- Implied Constraints ---
% 8. Balancing home and away games

%constraint implied_constraint( forall(t in TEAMS)(
%    sum([home[i,j] = t | i in WEEKS, j in PERIODS]) >= floor((n-1)/2) - 1 /\
%    sum([home[i,j] = t | i in WEEKS, j in PERIODS]) <= ceil((n-1)/2) + 1
%));
%solve satisfy;
solve :: int_search(
    [home[i,j] | i in WEEKS, j in PERIODS] ++ 
    [away[i,j] | i in WEEKS, j in PERIODS],
    input_order,  % Assign variables in the order they appear
    indomain_min
) satisfy;
% Output 
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
