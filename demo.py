"""Original procedural fixtures; synthetic test data, not field evidence."""
import cv2
import numpy as np

SCENARIOS = {'clean':'Matching assembly', 'missing':'Missing component', 'scratch':'Surface scratch',
             'shifted':'Camera shifted', 'dim':'Dim capture + defect', 'blur':'Out of focus',
             'dark':'Unusable exposure', 'wrong':'Wrong reference'}


def pair(scenario='missing', seed=0):
    if scenario not in SCENARIOS:
        raise ValueError('Unknown demo scenario.')
    rng = np.random.default_rng(seed)
    ref = np.full((480,640,3),195,np.uint8)
    cv2.rectangle(ref,(65,55),(575,425),(76,102,78),-1)
    for _ in range(100):
        x,y = rng.integers([85,75],[550,400])
        cv2.circle(ref,(int(x),int(y)),2,(140,165,128),-1)
    for y in (115,215,315):
        for x in (135,265,395):
            cv2.line(ref,(x-25,y+35),(x+105,y+35),(100,170,180),2)
            cv2.rectangle(ref,(x,y),(x+65,y+38),(32,35,40),-1)
            for dx in range(5,65,10):
                cv2.line(ref,(x+dx,y-6),(x+dx,y),(170,180,190),3)
            cv2.putText(ref,str(x+y),(x+8,y+25),cv2.FONT_HERSHEY_SIMPLEX,.4,(185,190,195),1)
    for x,y in ((80,70),(560,70),(80,410),(560,410)):
        cv2.circle(ref,(x,y),7,(200,205,210),-1)
        cv2.circle(ref,(x,y),3,(45,50,50),-1)
    cv2.putText(ref,'INSPECTLOOP / A01',(160,395),cv2.FONT_HERSHEY_SIMPLEX,.5,(195,205,190),1)
    test = ref.copy()
    if scenario in ('missing','dim'):
        cv2.rectangle(test,(265,215),(330,253),(76,102,78),-1)
    if scenario=='scratch':
        cv2.line(test,(350,180),(450,280),(225,230,235),4)
    if scenario=='shifted':
        test = cv2.warpAffine(test,np.float32([[1,0,9],[0,1,-6]]),(640,480),borderValue=(195,195,195))
    if scenario=='dim':
        test = (test.astype(float)*.4).astype(np.uint8)
    if scenario=='blur':
        test = cv2.GaussianBlur(test,(25,25),7)
    if scenario=='dark':
        test = (test.astype(float)*.06).astype(np.uint8)
    if scenario=='wrong':
        test = rng.integers(20,220,(480,640,3),dtype=np.uint8)
    return ref,test
