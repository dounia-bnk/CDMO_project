# run_2phase_solver.py
import minizinc
import json
import time
from datetime import timedelta
from pathlib import Path

class STSTwoPhaseSolver:
    def __init__(self, n_teams, solver_name="gecode", timeout=300):
        self.n_teams = n_teams
        self.solver_name = solver_name
        self.timeout = timeout
        self.phase1_solution = None
        self.phase2_solution = None
        self.phase1_time = 0
        self.phase2_time = 0
    
    def run_minizinc_model(self, model_file, data_dict=None):
        """Run MiniZinc model and return results"""
        try:
            # Load the model
            model = minizinc.Model(model_file)
            
            # Configure solver
            solver = minizinc.Solver.lookup(self.solver_name)
            instance = minizinc.Instance(solver, model)
            
            # Set parameters
            if data_dict:
                for key, value in data_dict.items():
                    instance[key] = value
            
            # Solve with time limit
            start_time = time.time()
            result = instance.solve(timeout=timedelta(seconds=self.timeout))
            elapsed = time.time() - start_time
            
            return {
                "result": result,
                "elapsed": min(elapsed, self.timeout),
                "status": result.status,
                "solver": self.solver_name
            }
            
        except Exception as e:
            print(f"Error running MiniZinc model {model_file} with {self.solver_name}: {e}")
            return {
                "result": None,
                "elapsed": self.timeout,
                "status": minizinc.Status.ERROR,
                "error": str(e),
                "solver": self.solver_name
            }
    
    def parse_phase1_solution(self, result):
        """Parse phase 1 solution from MiniZinc result - format: [weeks][periods][home,away]"""
        try:
            # Parse from solution string
            sol_str = str(result.solution) if hasattr(result, "solution") else str(result)
            if '[' in sol_str and ']' in sol_str:
                # Extract the solution array
                start_idx = sol_str.find('[')
                end_idx = sol_str.rfind(']') + 1
                solution_str = sol_str[start_idx:end_idx]
                solution = eval(solution_str)
                
                # The solution format is: [weeks][periods][home,away]
                # Convert to 3D array for phase 2 input
                weeks = len(solution)
                periods = len(solution[0]) if weeks > 0 else 0
                
                # Create 3D array: [week][period][home/away]
                solution_3d = []
                for week_idx in range(weeks):
                    week_solution = []
                    for period_idx in range(periods):
                        if period_idx < len(solution[week_idx]):
                            match_pair = solution[week_idx][period_idx]
                            week_solution.append([match_pair[0], match_pair[1]])
                    solution_3d.append(week_solution)
                
                print(f"Phase 1 solution parsed: {weeks} weeks, {periods} periods")
                return solution_3d
            else:
                print(f"No solution found in output with {self.solver_name}")
                return None
            
        except Exception as e:
            print(f"Failed to parse phase 1 solution with {self.solver_name}: {e}")
            return None
    
    def parse_phase2_solution(self, result):
        """Parse phase 2 solution from MiniZinc result"""
        try:
            # Parse from solution string
            sol_str = str(result.solution) if hasattr(result, "solution") else str(result)
            if '[' in sol_str and ']' in sol_str:
                start_idx = sol_str.find('[')
                end_idx = sol_str.rfind(']') + 1
                solution_str = sol_str[start_idx:end_idx]
                solution = eval(solution_str)
                
                # The solution format is: [weeks][periods][home,away]
                return solution
            
        except Exception as e:
            print(f"Failed to parse phase 2 solution with {self.solver_name}: {e}")
            return None
    
    def calculate_imbalance(self, solution):
        """Calculate home/away imbalance from a solution"""
        if not solution:
            return float('inf')
        
        home_games = {}
        away_games = {}
        
        for week in solution:
            for period in week:
                home_team = period[0]
                away_team = period[1]
                home_games[home_team] = home_games.get(home_team, 0) + 1
                away_games[away_team] = away_games.get(away_team, 0) + 1
        
        total_imbalance = 0
        for team in range(1, self.n_teams + 1):
            h = home_games.get(team, 0)
            a = away_games.get(team, 0)
            total_imbalance += abs(h - a)
        
        return total_imbalance
    
    def run_phase1(self):
        """Run phase 1 to find a feasible solution"""
        print(f"Running phase 1 for n={self.n_teams} with {self.solver_name}...")
        phase1_start = time.time()
        
        data = {"n": self.n_teams}
        result_info = self.run_minizinc_model("simple_CP.mzn", data)
        
        self.phase1_time = time.time() - phase1_start
        
        if result_info["result"] and result_info["status"] in [
            minizinc.Status.SATISFIED, 
            minizinc.Status.OPTIMAL_SOLUTION,
            minizinc.Status.ALL_SOLUTIONS
        ]:
            solution = self.parse_phase1_solution(result_info["result"])
            if solution is not None:
                self.phase1_solution = {
                    "solution": solution,
                    "elapsed": self.phase1_time,
                    "solver": self.solver_name,
                    "imbalance": self.calculate_imbalance(solution)
                }
                print(f"Phase 1 completed successfully in {self.phase1_time:.3f} seconds with {self.solver_name}!")
                print(f"Initial imbalance: {self.phase1_solution['imbalance']}")
                return True
        
        print(f"Phase 1 failed with {self.solver_name}")
        return False
    
    def run_phase2(self):
        """Run phase 2 to optimize the solution"""
        if not self.phase1_solution:
            print("Run phase 1 first!")
            return False
        
        print(f"Running phase 2 optimization for n={self.n_teams} with {self.solver_name}...")
        phase2_start = time.time()
        
        # Prepare data for phase 2 - use the 3D array format
        data = {
            "n": self.n_teams,
            "initial_solution": self.phase1_solution["solution"]
        }
        
        result_info = self.run_minizinc_model("phase2_optimize.mzn", data)
        
        self.phase2_time = time.time() - phase2_start
        
        if result_info["result"] and result_info["status"] in [
            minizinc.Status.SATISFIED, 
            minizinc.Status.OPTIMAL_SOLUTION,
            minizinc.Status.ALL_SOLUTIONS
        ]:
            solution = self.parse_phase2_solution(result_info["result"])
            if solution:
                imbalance = self.calculate_imbalance(solution)
                self.phase2_solution = {
                    "solution": solution,
                    "elapsed": self.phase2_time,
                    "solver": self.solver_name,
                    "imbalance": imbalance
                }
                print(f"Phase 2 completed in {self.phase2_time:.3f} seconds with {self.solver_name}! Final imbalance: {imbalance}")
                return True
        
        print(f"Phase 2 failed with {self.solver_name}")
        return False
    
    def get_total_time(self):
        """Get the total time for both phases"""
        return self.phase1_time + self.phase2_time
    
    def get_result_dict(self):
        """Get the result in the required JSON format"""
        if not self.phase2_solution:
            return None

        # Get solution data
        solution_data = self.phase2_solution["solution"]

        # Calculate total runtime (both phases)
        total_time = self.get_total_time()
        runtime = float("{:.3f}".format(min(total_time, self.timeout)))


        # Create the result entry
        result_dict = {
            "time": runtime,
            "optimal": True,
            "obj": int(self.phase2_solution["imbalance"]),
            "sol": solution_data
        }

        return result_dict

def run_solver(model_file: str, n: int, solver_name: str, time_limit: int = 300) -> dict:
    """Run two-phase solver and return results in the same format as the first code"""
    print(f"Running two-phase solver for n={n} with {solver_name}...")
    
    solver = STSTwoPhaseSolver(n, solver_name, time_limit)
    
    # Run both phases
    success = solver.run_phase1() and solver.run_phase2()
    
    if success:
        result_dict = solver.get_result_dict()
        if result_dict and result_dict["sol"] is not None and result_dict["time"] <= time_limit:
            return result_dict
    
    # Return empty result if failed or filtered out
    return {
        "time": float("{:.3f}".format(time_limit)),
        "optimal": True,
        "obj": None,
        "sol": None
    }

def main():
    """Main function to run the two-phase solver"""
    # Test n values from 6 to 16 (inclusive)
    n_values = [6, 8, 10, 12, 14]
    
    solvers = ['gecode', 'chuffed', 'coin-bc', 'cp-sat', 'highs']
    
    # Create output directory
    output_dir = Path("res/CP")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run for each n value
    for n in n_values:
        print(f"\n=== Testing n = {n} ===")
        results = {}
        
        # Load existing results if file exists
        output_file = output_dir / f"{n}.json"
        if output_file.exists():
            with open(output_file, "r") as f:
                results = json.load(f)
        
        for solver in solvers:
            
                
            print(f"Running with {solver}...")
            result = run_solver("simple_CP.mzn", n, solver)
            
            # Filter out results with sol=null or time > 300
            if result["sol"] is not None and result["time"] <= 300:
                results[solver] = result
            else:
                print(f"  Skipping {solver} - no solution found or timeout exceeded")
        
        # Save to JSON file for this n value (append to existing)
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Results for n={n} saved to {output_file}")

if __name__ == "__main__":
    main()