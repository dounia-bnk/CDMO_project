import minizinc
import json
import time
from datetime import timedelta
from pathlib import Path

def run_solver(model_file: str, n: int, solver_name: str, time_limit: int = 300) -> dict:
    """Run MiniZinc model using the specified solver and return results."""
    
    # Load the model
    model = minizinc.Model(model_file)
    
    # Configure solver
    solver = minizinc.Solver.lookup(solver_name)
    instance = minizinc.Instance(solver, model)
    
    # Set parameters
    instance["n"] = n  # Pass parameter 'n' to the model
    
    try:
        # Solve with a time limit 
        start_time = time.time()
        result = instance.solve(timeout=timedelta(seconds=time_limit))
        elapsed = time.time() - start_time
        
        # Check solution status
        if result.status == minizinc.Status.UNSATISFIABLE:
            status = "unsatisfiable"
            optimal = True
            obj = None
            sol = None
        elif result.status == minizinc.Status.UNKNOWN:
            status = "unknown"
            optimal = False
            obj = None
            sol = None
        elif result.status == minizinc.Status.OPTIMAL_SOLUTION:
            status = "optimal"
            optimal = True
            obj = result.objective if hasattr(result, "objective") else None
            sol_str = str(result.solution) if hasattr(result, "solution") else None
            sol = eval(sol_str) if sol_str else None  # Simple conversion from string to list
        else:  # SATISFIED or other status
            status = "satisfiable"
            optimal = False  # Not necessarily optimal
            obj = result.objective if hasattr(result, "objective") else None
            sol_str = str(result.solution) if hasattr(result, "solution") else None
            sol = eval(sol_str) if sol_str else None  # Simple conversion from string to list
        
        return {
            "time": int(min(elapsed, time_limit)),
            "optimal": optimal,
            "obj": obj,
            "sol": sol,  # Now properly formatted as list
        }
    
    except minizinc.MiniZincError as e:
        return {
            "solver": solver_name,
            "n": n,
            "status": "error",
            "time": int(min(elapsed, time_limit)),
            "optimal": False,
            "obj": None,
            "sol": None,
            "error": str(e),
        }

def main():
    # Test n values from 6 to 16 (inclusive)
    n_values = [6 ,8 ,10, 12, 14]
    
    solvers = ['gecode', 'chuffed', 'coin-bc', 'cp-sat', 'highs']
    
    # Create output directory
    output_dir = Path("res/CP")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run for each n value
    for n in n_values:
        print(f"\n=== Testing n = {n} ===")
        results = {}
        
        for solver in solvers:
            print(f"Running with {solver}...")
            result = run_solver("source/CP/simple_CP.mzn", n, solver)
            
            # Filter out results with sol=null or time > 300
            if result["sol"] is not None and result["time"] <= 300:
                results[solver] = result
            else:
                print(f"  Skipping {solver} - no solution found or timeout exceeded")
        
        # Only save if there are valid results
        if results:
            # Save to JSON file for this n value
            output_file = output_dir / f"{n}.json"
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"Results for n={n} saved to {output_file}")
        else:
            print(f"No valid results for n={n}, skipping file creation")

if __name__ == "__main__":
    main()