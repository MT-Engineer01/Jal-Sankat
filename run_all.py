"""Run the whole pipeline with one command:  python run_all.py   (add --skip-tests to skip the checks)"""
import os, sys, subprocess, time
ROOT=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(ROOT,'data','raw','cgwb-changes-in-depth-to-water-level.csv')
if not os.path.exists(RAW):
    sys.exit('Raw data missing.\nSave the CGWB CSV as:\n  '+RAW+'\nthen run this command again.')
steps=['scripts/01_clean.py','scripts/02_stats.py','scripts/02b_rainfall_prep.py','scripts/02c_rain_analysis.py','scripts/03_models.py','sql/run_sql.py','scripts/04_build_dashboard.py','scripts/05_package_site.py']
if '--skip-tests' not in sys.argv: steps.append('-m unittest discover tests -v')
t0=time.time()
for s in steps:
    print(f'\n=== {s} ===',flush=True); t=time.time()
    cmd=[sys.executable]+(s.split() if s.startswith('-m') else [os.path.join(ROOT,s)])
    if subprocess.run(cmd,cwd=ROOT).returncode: sys.exit(f'FAILED at {s}')
    print(f'done in {time.time()-t:.0f}s')
print(f'\nAll steps finished in {time.time()-t0:.0f}s. Open docs/index.html in your browser.')
