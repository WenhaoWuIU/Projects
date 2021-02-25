#Take reference from scipy-cookbook.io and docs.opencv.org

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import cv2 as cv
import math
import scipy
import scipy.linalg


def ransacModel(data, model, n, k, t, d, debug=False, returnAll=False):
    bestFit = None
    bestErr = 100000
    best_consensus_set = None
    for i in range(k):
        possibile_x, possibile_y = randomPoints(n, data.shape[0])
        possibile_inliners = data[possibile_x,:]
        testPoints = data[possibile_y,:]
        possibile_model = model.fit(possibile_inliners)
        consensus_set = possibile_inliners
        testErr = model.error(testPoints, possibile_model)
        also_x = possibile_y[testErr < t]
        alsoInliners = data[also_x, :]
        if len(alsoInliners) > d:
            next_data = np.concatenate((possibile_inliners, alsoInliners))
            next_model = model.fit(next_data)
            next_error = model.error(next_data, next_model)
            current_error = np.mean(next_error)
            if current_error < bestErr:
                bestErr = current_error
                bestFit = next_model
                best_consensus_set = np.concatenate((possibile_x, also_x))
        if bestFit is None:
            print("best fit is none")
        return bestFit, {'inliners':best_consensus_set}


def randomPoints(n, data):
    datas = np.arange(data)
    np.random.shuffle(datas)
    x = datas[:n]
    y = datas[n:]
    return x, y


class theModel:
    def __init__(self, inputs, outputs, debug=False, returnAll=False):
        self.inputs = inputs
        self.outputs = outputs
        self.debug = debug

    def fit(self, data):
        fp = np.vstack([data[:,i] for i in self.inputs])
        fp = np.transpose(fp)
        tp = np.vstack([data[:,i] for i in self.outputs])
        tp = np.transpose(tp)
        fit, r, ra, s = scipy.linalg.lstsq(fp, tp)
        return fit
    
    def error(self, data, H):
        fp = np.vstack([data[:,i] for i in self.inputs])
        fp = np.transpose(fp)
        tp = np.vstack([data[:,i] for i in self.outputs])
        tp = np.transpose(tp)
        t_fit = np.dot(fp, H)
        error = np.sum((tp-t_fit)**2, axis=1)
        return error



def stiching(im1, im2, output):
    img_right = cv.imread(im2)
    img1 = cv.cvtColor(img_right,cv.COLOR_BGR2GRAY)
    img_left = cv.imread(im1)
    img2 = cv.cvtColor(img_left,cv.COLOR_BGR2GRAY)
    sift = cv.xfeatures2d.SIFT_create()

    k1, d1 = sift.detectAndCompute(img1,None)
    k2, d2 = sift.detectAndCompute(img2,None)
    bf = cv.BFMatcher()
    matches = bf.knnMatch(d1,d2, k=2)

    matches = np.asarray(matches)
    if len(matches[:,0]) >= 4:
        src = np.float32([k1[m.queryIdx].pt for m in matches[:,0]]).reshape(-1,1,2)
        dst = np.float32([k2[m.trainIdx].pt for m in matches[:,0]]).reshape(-1,1,2)
    H1, masked = cv.findHomography(src, dst, cv.RANSAC, 5.0)
    model = theModel(range(1), [1], debug=False)
    all_data = np.hstack( (src,dst) ).reshape(-1,2)
    H,mask = ransacModel(all_data, model, 50, 1000, 1000, 10, debug=False, returnAll=True)
    dst = cv.warpPerspective(img_right,H1,(img_left.shape[1] + img_right.shape[1], img_left.shape[0]+img_right.shape[0]))
    dst[0:img_left.shape[0], 0:img_left.shape[1]] = img_left
    cv.imwrite(output,dst)

