# Sports Tournament Scheduling (STS) Project

This project models and solves the **Sports Tournament Scheduling (STS)** problem using combinatorial optimization techniques. We developed three different approaches to schedule a round-robin tournament for `n` teams over `n-1` weeks.

## Approaches Implemented

### 1. Constraint Programming (CP)
- **Language**: MiniZinc
- **Versions**: Base model and optimized model with symmetry-breaking constraints
- **Solvers**: Gecode, Chuffed, COIN-BC, CP-SAT, HiGHS
- **Features**:  non-optimal version of CP

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

run_all.py              # Main script to run solvers
solution_checker.py     # Validates generated solutions
Dockerfile             # Docker container configuration
environment.yml        # Conda environment specification
```

## Running the Project
All the the next instructions must be executed inside of the CDMO_project directory, you can do that by :
```bash
cd CDMO_project
```

### Using Docker 

Build the Docker image:
```bash
docker build -t cdmo .
```

### Run the image and open the bash
```bash
docker run -it cdmo bash
```
This will allow to run the source code, generate the files and verify them inside of the container created
### Inside the bash : checking solutions
Before or after executing any of the code you can check the solutions
```bash
python solution_checker.py res/CP
python solution_checker.py res/SAT
python solution_checker.py res/MIP
```

#### Inside  the bash : testing the code
You can run all the models toguether (you must be inside the bash)
```bash
# Run all solvers
python run_all.py
```
Or choose to run them individually
# Run individual solvers
```bash
python run_all.py CP
python run_all.py SAT
python run_all.py MIP
```


## Output Format

Results are stored in JSON format in the `res/` directory, organized by approach (CP, SAT, MIP). Each solution file contains:
- Instance parameters (number of teams, weeks)
- Schedule assignments
- Solver statistics (time, optimality status)
