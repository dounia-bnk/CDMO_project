# Sports Tournament Scheduling (STS) Project

This project models and solves the **Sports Tournament Scheduling (STS)** problem using combinatorial optimization techniques. We developed three different approaches to schedule a round-robin tournament for `n` teams over `n-1` weeks.

## Approaches Implemented

### 1. Constraint Programming (CP)
- **Language**: MiniZinc
- **Versions**: Base model and optimized model with symmetry-breaking constraints
- **Solvers**: Gecode, Chuffed, COIN-BC, CP-SAT, HiGHS
- **Solvers**: Optimal solution, we tested both optimal and non-optimal version of CP

### 2. Propositional Satisfiability (SAT)
- **Language**: Python with Z3 solver
- **Features**: Sequential encoding for cardinality constraints, symmetry-breaking

### 3. Mixed-Integer Programming (MIP)
- **Language**: Python with PuLP
- **Focus**: Fairness optimization by balancing home/away games
- **Solvers**: CBC, HiGHS

## Project Structure
```
source/          # Source code for all models
├── CP/         # MiniZinc models
├── SAT/        # Python Z3 scripts
└── MIP/        # Python PuLP scripts

res/            # Results in JSON format
├── CP/
├── SAT/
└── MIP/
```

## Running the Project

To execute all solvers and generate results:

```bash
python run_all.py
```

This will run all CP, SAT, and MIP models with a 300-second time limit per instance and store results in the `res/` folder.

Individual models can also be run from their respective subdirectories in `source/`.
