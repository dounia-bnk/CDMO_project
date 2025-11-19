import os, json

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def save_result_json(result, n: int, approach_name="cbc", base_dir="res/MIP", compact=False):
    ensure_dir(base_dir)
    out_path = os.path.join(base_dir, f"{n}.json")
    payload = {
        approach_name: {
            "time": result["time"],
            "optimal": result["optimal"],
            "obj": result["obj"],
            "sol": result["sol"],
        }
    }
    with open(out_path, "w") as f:
        if compact:
            json.dump(payload, f, separators=(",", ":"))
        else:
            json.dump(payload, f, indent=2)
    return out_path

def load_result_json(n, approach_name="cbc", base_dir="res/MIP"):
    path = os.path.join(base_dir, f"{n}.json")
    with open(path, "r") as f:
        data = json.load(f)
    return data.get(approach_name, {})
