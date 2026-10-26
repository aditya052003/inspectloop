"""Deterministic, evidence-driven inspection. No learned defect classifier."""
import base64
import time
import cv2
import numpy as np

cv2.setNumThreads(1)
if int(cv2.__version__.split('.')[0]) != 5:
    raise RuntimeError('InspectLoop requires OpenCV 5. Install requirements.txt.')


def png(image):
    ok, data = cv2.imencode('.png', image)
    if not ok:
        raise ValueError('Could not encode image')
    return 'data:image/png;base64,' + base64.b64encode(data).decode()


def decode(data):
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Upload a valid JPEG or PNG image.')
    if image.shape[0] * image.shape[1] > 12_000_000 or min(image.shape[:2]) < 128:
        raise ValueError('Images must be at least 128 pixels per side and at most 12 megapixels.')
    return image


def quality(gray):
    return {'brightness': round(float(gray.mean()), 2),
            'sharpness': round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 2),
            'clipped_fraction': round(float(np.mean((gray < 4) | (gray > 251))), 4)}


def inspect(reference, candidate):
    started = time.perf_counter()
    trace = []
    def step(tool, evidence, action):
        trace.append({'step': len(trace)+1, 'tool': tool, 'evidence': evidence, 'action': action})
    ref_ratio = reference.shape[1] / reference.shape[0]
    ratio = candidate.shape[1] / candidate.shape[0]
    size = (640, int(640/ref_ratio))
    if size[1] > 960 or size[1] < 240:
        raise ValueError('Use a landscape or square image with aspect ratio between 2:3 and 8:3.')
    ref = cv2.resize(reference, size)
    candidate = cv2.resize(candidate, size)
    before = candidate.copy()
    gray_ref = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
    q = quality(gray)
    ref_q = quality(gray_ref)
    result = {'opencv': cv2.__version__, 'trace': trace, 'quality': q, 'reference_quality': ref_q,
              'regions': [], 'changed_percent': 0, 'images': {'reference': png(ref), 'input': png(before)},
              'policy': 'Deterministic inspection policy v1; not a trained classifier or LLM.'}
    def finish(status, message):
        result.update(status=status, message=message, elapsed_ms=round((time.perf_counter()-started)*1000, 1))
        step('decision', {'status': status}, message)
        return result
    step('reference_quality', ref_q, 'Validate reference before comparison.')
    if ref_q['brightness'] < 40 or ref_q['sharpness'] < 45 or ref_q['clipped_fraction'] > .45:
        return finish('retake', 'Replace the reference with a sharp, evenly lit image.')
    step('capture_quality', q, 'Select recovery, alignment, or a new capture.')
    if abs(ratio-ref_ratio)/ref_ratio > .05:
        return finish('retake', 'Use the same framing and image aspect ratio as the reference.')
    if q['brightness'] < 22 or q['clipped_fraction'] > .45:
        return finish('retake', 'Capture again with even lighting; too much information is missing.')
    if q['brightness'] < ref_q['brightness'] * .6:
        gain = min(3.0, ref_q['brightness']/max(q['brightness'], 1))
        candidate = np.clip(candidate.astype(np.float32)*gain, 0, 255).astype(np.uint8)
        gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
        q = quality(gray)
        step('exposure_recovery', {'gain': round(gain, 2), 'recovered_quality': q}, 'Recheck sharpness after bounded exposure correction.')
    if q['sharpness'] < 45:
        return finish('retake', 'Capture again: hold the camera steady and focus on the product.')
    valid = np.ones(gray.shape, np.uint8)*255
    if np.mean(cv2.absdiff(gray_ref, gray)) < 1:
        step('alignment', {'method': 'already aligned', 'mean_difference': round(float(np.mean(cv2.absdiff(gray_ref, gray))), 3)}, 'Compare directly.')
    else:
        orb = cv2.ORB_create(nfeatures=1800)
        kr, dr = orb.detectAndCompute(gray_ref, None)
        kc, dc = orb.detectAndCompute(gray, None)
        if dr is None or dc is None:
            return finish('retake', 'Not enough visual features. Use a textured fixture and consistent framing.')
        pairs = cv2.BFMatcher(cv2.NORM_HAMMING).knnMatch(dc, dr, k=2)
        good = [p[0] for p in pairs if len(p)==2 and p[0].distance < .72*p[1].distance]
        if len(good) < 12:
            return finish('retake', 'Could not match the product reliably. Check reference and camera angle.')
        src = np.float32([kc[m.queryIdx].pt for m in good])
        dst = np.float32([kr[m.trainIdx].pt for m in good])
        matrix, inliers = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=2.5)
        count = int(inliers.sum()) if inliers is not None else 0
        if matrix is None or count < 12 or count/len(good) < .45:
            return finish('retake', 'Alignment is uncertain. Retake from the reference viewpoint.')
        scale = float(np.linalg.norm(matrix[:, 0]))
        # Normalize movement by frame diagonal so portrait captures are not
        # rejected by a landscape-specific 80-pixel cutoff.
        translation_fraction = float(np.linalg.norm(matrix[:, 2]) / np.hypot(*size))
        if not .85 <= scale <= 1.15 or translation_fraction > .10:
            return finish('retake', 'Camera movement is too large. Return to the reference framing.')
        warped_valid = cv2.warpAffine(valid, matrix, size, flags=cv2.INTER_NEAREST)
        overlap = float(np.mean(warped_valid > 0))
        if overlap < .75:
            return finish('retake', 'Too little shared image area. Return to the reference framing.')
        gray = cv2.warpAffine(gray, matrix, size)
        candidate = cv2.warpAffine(candidate, matrix, size)
        valid = warped_valid
        step('alignment', {'matches': len(good), 'inliers': count, 'scale': round(scale, 4), 'translation_fraction': round(translation_fraction, 4), 'overlap_fraction': round(overlap, 4)}, 'Warp candidate into reference coordinates.')
    valid = cv2.erode(valid, np.ones((9,9),np.uint8))
    valid[:6,:] = valid[-6:,:] = valid[:,:6] = valid[:,-6:] = 0
    offset = float(np.median(gray_ref[valid>0].astype(float)-gray[valid>0].astype(float)))
    corrected = np.clip(gray.astype(float)+offset,0,255).astype(np.uint8)
    diff = cv2.absdiff(cv2.GaussianBlur(gray_ref,(3,3),0),cv2.GaussianBlur(corrected,(3,3),0))
    mask = np.uint8((diff>35)&(valid>0))*255
    mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    contours,_ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    overlay = candidate.copy()
    for contour in contours:
        if cv2.contourArea(contour)<24:
            continue
        x,y,w,h = cv2.boundingRect(contour)
        # Second tool call zooms into a candidate region and measures evidence support.
        roi = diff[y:y+h,x:x+w]
        support = float(np.mean(roi>35))
        if support < .025:
            continue
        regions.append({'x':x,'y':y,'width':w,'height':h,'support':round(support,3),
                        'mean_difference':round(float(roi.mean()),2)})
        cv2.rectangle(overlay,(x,y),(x+w,y+h),(30,80,245),2)
    regions.sort(key=lambda r:r['width']*r['height'],reverse=True)
    result['regions'] = regions[:30]
    result['changed_percent'] = round(float(np.count_nonzero(mask)/np.count_nonzero(valid)*100),3)
    result['images'].update(overlay=png(overlay),mask=png(mask))
    step('difference_map', {'changed_percent':result['changed_percent'],'candidate_regions':len(regions),'threshold':35}, 'Inspect local regions if changes exist.')
    if regions:
        step('roi_refinement', {'regions':regions[:30],'min_support':.025}, 'Use local evidence to route to human review; never discard products automatically.')
    if result['changed_percent'] > 15:
        return finish('retake', 'Large mismatch: confirm the product, reference, viewpoint, and lighting.')
    if regions:
        return finish('review', 'Visible changes found. A person must confirm whether these are defects.')
    return finish('clear', 'No significant visual change detected at these thresholds. This is not a quality guarantee.')
