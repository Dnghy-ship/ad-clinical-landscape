import argparse, importlib, json
from pathlib import Path
import subprocess, sys
from .client import CTGovClient
from .config import load_config
from .pipeline import collect
from .report import build_report

REQUIRED = {"requests":"requests","pandas":"pandas","plotly":"plotly","openpyxl":"openpyxl","yaml":"PyYAML","streamlit":"streamlit","pycountry":"pycountry"}

def doctor(config_path):
    print("=== Python ===")
    print(sys.version); print("Executable:",sys.executable); print()
    ok = True
    print("=== Packages ===")
    for mod,pkg in REQUIRED.items():
        try:
            m=importlib.import_module(mod); print(f"[OK] {pkg}: {getattr(m,'__version__','unknown')}")
        except Exception as e:
            ok=False; print(f"[MISSING] {pkg}: {e}")
    print("\n=== ClinicalTrials.gov API ===")
    try:
        cfg=load_config(config_path)
        v=CTGovClient(cfg["api"]["base_url"],int(cfg["api"]["timeout_seconds"]),cfg["api"]["user_agent"]).get_version()
        print("[OK] API reachable"); print(json.dumps(v,ensure_ascii=False,indent=2))
    except Exception as e:
        ok=False; print("[FAILED]",repr(e))
    print("\nEnvironment check passed." if ok else "\nEnvironment check found issues.")
    return 0 if ok else 1

def launch_dashboard():
    p=Path(__file__).with_name("dashboard.py")
    return subprocess.call([sys.executable,"-m","streamlit","run",str(p)])

def main():
    parser=argparse.ArgumentParser(prog="adtrial")
    parser.add_argument("--config",default="config/alzheimer.yml")
    sub=parser.add_subparsers(dest="command",required=True)
    sub.add_parser("doctor")
    c=sub.add_parser("collect"); c.add_argument("--max-studies",type=int,default=None)
    sub.add_parser("report")
    a=sub.add_parser("all"); a.add_argument("--max-studies",type=int,default=None)
    sub.add_parser("dashboard")
    args=parser.parse_args()
    if args.command=="doctor": raise SystemExit(doctor(args.config))
    if args.command=="collect": print(json.dumps(collect(args.config,args.max_studies),ensure_ascii=False,indent=2)); return
    if args.command=="report": print("Report:",build_report(args.config)); return
    if args.command=="all":
        print(json.dumps(collect(args.config,args.max_studies),ensure_ascii=False,indent=2))
        print("Report:",build_report(args.config)); return
    if args.command=="dashboard": raise SystemExit(launch_dashboard())

if __name__=="__main__": main()
