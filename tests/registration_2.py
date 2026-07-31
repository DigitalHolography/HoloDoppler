import cv2
import matplotlib.pyplot as plt
import numpy as np

# -------------------------------------------------------
# Load
# -------------------------------------------------------

fixed = plt.imread("debug_outputs/debug_M0ff.png").astype(np.float32)
moving = plt.imread("debug_outputs/debug_M0ff2.png").astype(np.float32)

if fixed.ndim == 3:
    fixed = fixed[...,0]
if moving.ndim == 3:
    moving = moving[...,0]

fixed /= fixed.max()
moving /= moving.max()

h,w = fixed.shape

# -------------------------------------------------------
# 1) Rigid registration (ECC)
# -------------------------------------------------------

warp = np.eye(2,3,dtype=np.float32)

criteria = (
    cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
    200,
    1e-8,
)

_, warp = cv2.findTransformECC(
    fixed,
    moving,
    warp,
    cv2.MOTION_EUCLIDEAN,
    criteria,
)

rigid = cv2.warpAffine(
    moving,
    warp,
    (w,h),
    flags=cv2.INTER_CUBIC | cv2.WARP_INVERSE_MAP,
)

# -------------------------------------------------------
# 2) Piecewise affine (feature based)
# -------------------------------------------------------

orb = cv2.ORB_create(3000)

kp1,des1 = orb.detectAndCompute((255*fixed).astype(np.uint8),None)
kp2,des2 = orb.detectAndCompute((255*moving).astype(np.uint8),None)

bf = cv2.BFMatcher(cv2.NORM_HAMMING)

matches = bf.match(des1,des2)
matches = sorted(matches,key=lambda x:x.distance)

pts1 = np.float32([kp1[m.queryIdx].pt for m in matches])
pts2 = np.float32([kp2[m.trainIdx].pt for m in matches])

M,inliers = cv2.estimateAffinePartial2D(
    pts2,
    pts1,
    method=cv2.RANSAC,
)

piecewise = cv2.warpAffine(
    moving,
    M,
    (w,h),
)

# -------------------------------------------------------
# 3) Dense optical flow
# -------------------------------------------------------

flow = cv2.calcOpticalFlowFarneback(
    moving,
    fixed,
    None,
    pyr_scale=0.5,
    levels=4,
    winsize=51,
    iterations=5,
    poly_n=7,
    poly_sigma=1.5,
    flags=0,
)

# -------------------------------------------------------
# Quiver
# -------------------------------------------------------

step = 20

Y,X = np.mgrid[
    step//2:h:step,
    step//2:w:step
]

Fx = flow[Y,X,0]
Fy = flow[Y,X,1]

# rigid displacement field

XX,YY = np.meshgrid(np.arange(w),np.arange(h))

XY = np.stack([XX.ravel(),YY.ravel(),np.ones(h*w)])

rig = warp@XY

Ux = (rig[0]-XX.ravel()).reshape(h,w)
Uy = (rig[1]-YY.ravel()).reshape(h,w)

Ux = Ux[Y,X]
Uy = Uy[Y,X]

# -------------------------------------------------------
# display
# -------------------------------------------------------

fig,ax = plt.subplots(2,3,figsize=(15,10))

ax[0,0].imshow(fixed,cmap='gray')
ax[0,0].set_title("Fixed")

ax[0,1].imshow(moving,cmap='gray')
ax[0,1].set_title("Moving")

ax[0,2].imshow(rigid,cmap='gray')
ax[0,2].set_title("Rigid ECC")

ax[1,0].imshow(fixed,cmap='gray')
ax[1,0].quiver(X,Y,Ux,-Uy,color='r')
ax[1,0].set_title("Rigid field")

ax[1,1].imshow(fixed,cmap='gray')
ax[1,1].quiver(X,Y,Fx,-Fy,color='lime')
ax[1,1].set_title("Dense optical flow")

ax[1,2].imshow(fixed-moving,cmap='seismic')
ax[1,2].set_title("Difference")

for a in ax.ravel():
    a.axis('off')

plt.tight_layout()
plt.show()