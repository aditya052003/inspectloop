"""Regenerate original synthetic upload fixtures and explicit failure evidence."""
import json
from pathlib import Path
import cv2
from demo import pair,SCENARIOS
from vision import inspect


def generate():
    Path('samples').mkdir(exist_ok=True)
    Path('evaluation').mkdir(exist_ok=True)
    for scenario in SCENARIOS:
        ref,test=pair(scenario)
        cv2.imwrite('samples/'+scenario+'.png',test)
    cv2.imwrite('samples/reference.png',pair('clean')[0])
    ref,_=pair('clean')
    cases=[]
    for name in ('tiny_defect','low_contrast_change'):
        test=ref.copy()
        if name=='tiny_defect':
            cv2.circle(test,(220,190),1,(240,240,240),-1)
        else:
            cv2.rectangle(test,(210,170),(250,190),(83,109,85),-1)
        result=inspect(ref,test)
        cases.append({'case':name,'known_change':True,'actual_status':result['status'],'regions':len(result['regions']),'limitation':'Change is below configured spatial or contrast thresholds.'})
        cv2.imwrite('samples/failure-'+name+'.png',test)
    Path('evaluation/failure-cases.json').write_text(json.dumps(cases,indent=2))

if __name__=='__main__':generate()
