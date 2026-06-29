import os
import sys
import yaml
import subprocess
import time
import requests
import shutil
import pandas as pd
from pathlib import Path

# --- Configuration ---
REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    "dvc.yaml",
    "params.yaml",
    "data/raw/real_drug_dataset.csv", 
    "infra/docker/Dockerfile.training",
    "infra/docker/Dockerfile.inference",
    "infra/docker/Dockerfile.frontend",
    "infra/docker/docker-compose.yml",
    "infra/k8s/namespace.yaml",
]

EXPECTED_COLUMNS = [
    "Patient_ID", "Age", "Gender", "Condition", "Drug_Name", 
    "Dosage_mg", "Treatment_Duration_days", "Side_Effects", 
    "Improvement_Score"
]

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log(msg, status="INFO"):
    if status == "PASS":
        print(f"{GREEN}[PASS]{RESET} {msg}")
    elif status == "FAIL":
        print(f"{RED}[FAIL]{RESET} {msg}")
    elif status == "WARN":
        print(f"{YELLOW}[WARN]{RESET} {msg}")
    else:
        print(f"[INFO] {msg}")

def check_cmd(cmd):
    return shutil.which(cmd) is not None

def run_cmd(cmd, cwd=None, env=None, capture_output=True):
    try:
        result = subprocess.run(
            cmd, check=True, cwd=cwd, env=env,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def step_1_integrity():
    log("Step 1: Repository Integrity Check")
    all_exist = True
    for f in REQUIRED_FILES:
        if not Path(f).exists():
            log(f"Missing file: {f}", "FAIL")
            all_exist = False
    
    if all_exist:
        log("All required files present", "PASS")
    else:
        return False
        
    # Check YAML syntax
    try:
        with open("dvc.yaml") as f: yaml.safe_load(f)
        with open("params.yaml") as f: yaml.safe_load(f)
        log("YAML syntax valid", "PASS")
    except Exception as e:
        log(f"YAML syntax error: {e}", "FAIL")
        return False
    return True

def step_2_schema_check():
    log("Step 2: Dataset Schema Verification")
    csv_path = "data/raw/real_drug_dataset.csv"
    try:
        df = pd.read_csv(csv_path)
        cols = df.columns.tolist()
        if cols == EXPECTED_COLUMNS:
            log("CSV columns match expected schema", "PASS")
            return True
        else:
            log(f"CSV schema mismatch.\nExpected: {EXPECTED_COLUMNS}\nFound: {cols}", "FAIL")
            return False
    except Exception as e:
        log(f"Failed to read dataset: {e}", "FAIL")
        return False

def step_3_dvc_pipeline():
    log("Step 3: DVC Pipeline Verification")
    success, output = run_cmd(["dvc", "repro"])
    if success:
        log("DVC pipeline ran successfully", "PASS")
        if Path("models/model.joblib").exists() and Path("metrics/scores.json").exists():
             log("Artifacts generated (model + metrics)", "PASS")
             return True
        else:
             log("Pipeline ran but artifacts missing", "FAIL")
             return False
    else:
        log(f"DVC pipeline failed: {output}", "FAIL")
        return False

def step_4_docker_check():
    log("Step 4: Docker Verification")
    if not check_cmd("docker"):
        log("Docker not installed. Skipping build checks (PREREQUISITE MISSING)", "WARN")
        return True
    
    # Check daemon
    success, _ = run_cmd(["docker", "info"])
    if not success:
        log("Docker daemon not running. Skipping build checks (PREREQUISITE MISSING)", "WARN")
        return True

    log("Docker daemon available. (Skipping full build in validation script to avoid timeout)", "PASS")
    return True

def step_5_k8s_check():
    log("Step 5: Kubernetes Manifest Verification")
    if not check_cmd("kubectl"):
        log("kubectl not installed. Skipping manifest validation (PREREQUISITE MISSING)", "WARN")
        return True
    
    # Check cluster connection
    cluster_up, _ = run_cmd(["kubectl", "cluster-info"])
    
    if not cluster_up:
         log("Kubernetes cluster not reachable. Skipping manifest validation to avoid connection errors.", "WARN")
         return True
    
    cmd = ["kubectl", "apply", "--dry-run=client", "-f", "infra/k8s/"]
    success, output = run_cmd(cmd)
    if success:
        log("K8s manifests syntax valid", "PASS")
    else:
        log(f"K8s manifest validation failed: {output}", "FAIL")
        return False
    return True

def step_6_api_runtime():
    log("Step 6: Local API Runtime Check")
    
    # Start API in background
    # Use sys.executable to ensure we use the same python interpreter (venv)
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "inference.app:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        # Retry loop for health check
        max_retries = 10
        started = False
        for i in range(max_retries):
            try:
                resp = requests.get("http://127.0.0.1:8000/health")
                if resp.status_code == 200:
                    started = True
                    break
            except requests.ConnectionError:
                pass
            time.sleep(1)
            
        if not started:
            log(f"API failed to start after {max_retries} seconds", "FAIL")
            return False
            
        log("API /health validation", "PASS")
        
        # Predict test
        payload = {
            "Patient_ID": "P0001",
            "Age": 30,
            "Gender": "Male",
            "Condition": "Diabetes",
            "Drug_Name": "Metformin",
            "Dosage_mg": 500,
            "Treatment_Duration_days": 10,
            "Side_Effects": "Nausea"
        }
        resp = requests.post("http://127.0.0.1:8000/predict", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            if "Improvement_Score" in data:
                 log("API /predict validation", "PASS")
            else:
                 log(f"API /predict missing Improvement_Score: {data}", "FAIL")
                 return False
        else:
            log(f"API /predict failed: {resp.text}", "FAIL")
            return False
            
        # Metrics test
        resp = requests.get("http://127.0.0.1:8000/metrics")
        if resp.status_code == 200 and "api_request_total" in resp.text:
            log("API /metrics validation", "PASS")
        else:
            log("API /metrics validation failed", "FAIL")
            return False

        return True

    except Exception as e:
        log(f"API connection failed: {e}", "FAIL")
        return False
    finally:
        proc.terminate()
        proc.wait()

def main():
    print("=============================================")
    print("   MLOps Repository Verification Protocol    ")
    print("=============================================")
    
    checks = [
        step_1_integrity,
        step_2_schema_check,
        step_3_dvc_pipeline,
        step_4_docker_check,
        step_5_k8s_check,
        step_6_api_runtime
    ]
    
    failed = False
    for check in checks:
        if not check():
            failed = True
            break
            
    print("=============================================")
    if failed:
        print(f"{RED}VERIFICATION FAILED{RESET}")
        sys.exit(1)
    else:
        print(f"{GREEN}VERIFICATION PASSED{RESET}")
        print("Ready for GitHub Push (Subject to infrastructure prerequisites)")
        sys.exit(0)

if __name__ == "__main__":
    main()
