import numpy as np
import cv2

from app.video_operations import ClickAndDrop, VideoStabilizer


frame_size = (1280, 720)

# stabilize video
VideoStabilizer("../recordings", "recording1.mp4")

cap = cv2.VideoCapture('../recordings/stable-recording.avi')

# params for ShiTomasi corner detection, TODO improve tracking points
feature_params = dict(maxCorners=10,
                      qualityLevel=0.3,
                      minDistance=25,
                      blockSize=25)

# Parameters for lucas kanade optical flow
lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

# Create some random colors
color = np.random.randint(0, 255, (100, 3))

# Take first frame and find corners in it
ret, old_frame = cap.read()

cad = ClickAndDrop(old_frame)
reference_points = cad.get_reference_points()
old_frame = old_frame[reference_points[0][1]:reference_points[1][1], reference_points[0][0]:reference_points[1][0]]

old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
p0 = cv2.goodFeaturesToTrack(old_gray, mask=None, **feature_params)

# Create a mask image for drawing purposes
mask = np.zeros_like(old_frame)

while cap.isOpened():
    ret, frame = cap.read()

    if frame is None:  # break loop at the end of the clip
        break

    frame = frame[reference_points[0][1]:reference_points[1][1], reference_points[0][0]:reference_points[1][0]]
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # calculate optical flow
    p1, st, err = cv2.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)

    # Select good points
    good_new = p1[st == 1]
    good_old = p0[st == 1]

    # draw the tracks
    for i, (new, old) in enumerate(zip(good_new, good_old)):
        a, b = new.ravel()
        c, d = old.ravel()
        mask = cv2.line(mask, (a, b), (c, d), color[i].tolist(), 2)
        frame = cv2.circle(frame, (a, b), 5, color[i].tolist(), -1)
    img = cv2.add(frame, mask)

    resized_img = cv2.resize(img, frame_size, interpolation=cv2.INTER_AREA)
    cv2.imshow('frame', resized_img)

    # user exit on "q" or "Esc" key press
    k = cv2.waitKey(30) & 0xFF
    if k == 25 or k == 27:
        break

    # Now update the previous frame and previous points
    old_gray = frame_gray.copy()
    p0 = good_new.reshape(-1, 1, 2)

# tidying up
cv2.destroyAllWindows()
cap.release()
