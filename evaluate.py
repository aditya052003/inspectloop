"""Reproducible synthetic smoke benchmark; NOT production accuracy evidence."""
import csv
import json
import platform
import statistics
from pathlib import Path
import cv2
from demo import pair
from vision import inspect

EXPECTED={'clean':'clear','missing':'review','scratch':'review','shifted':'clear','dim':'review','blur':'retake','dark':'retake','wrong':'retake'}

def main():
    from generate_samples import generate
    generate()
    out=Path('evaluation');out.mkdir(exist_ok=True)
    rows=[]
    for seed in range(10):
        for scenario,expected in EXPECTED.items():
            result=inspect(*pair(scenario,seed))
            rows.append({'seed':seed,'scenario':scenario,'expected':expected,'actual':result['status'],'correct':result['status']==expected,'regions':len(result['regions']),'elapsed_ms':result['elapsed_ms']})
            if seed==0:
                (out/(scenario+'-trace.json')).write_text(json.dumps({k:v for k,v in result.items() if k!='images'},indent=2))
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    times=sorted(r['elapsed_ms'] for r in rows)
    summary={'dataset':'80 procedural synthetic cases; 8 scenarios × 10 texture seeds. Correlated fixtures, not independent field data.','opencv':cv2.__version__,'python':platform.python_version(),'platform':platform.platform(),'cases':len(rows),'correct_routes':sum(r['correct'] for r in rows),'median_ms':round(statistics.median(times),2),'p95_ms':times[int(len(times)*.95)-1],'measurement':'Local vision engine only, including PNG encoding. Excludes HTTP, storage, Lambda cold starts and network.','limitations':['Fixed thresholds tuned on these synthetic fixture families.','No real-world accuracy, defect classification, or AWS benchmark claimed.','Low-contrast and tiny defects may be missed; lighting and viewpoint changes may cause false alarms.']}
    (out/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
    return rows

if __name__=='__main__':main()
