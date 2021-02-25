import sys
import part2
import numpy as np
import part3
from part1 import*
import cv2
import numpy as np
import itertools
import matplotlib.pyplot as plt
import os, shutil, glob, os.path
from sklearn import manifold
from sklearn import cluster
from mpl_toolkits.mplot3d import Axes3D 
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler


transformation_matrix_original = np.array([
    [0.907, 0.258, -182],
    [-0.153, 1.44, 58],
    [-0.000306, 0.000731, 1],
])

part = sys.argv[1]

if part == 'part1':
    k = int(sys.argv[2])
    narg = len(sys.argv)

    filelist_short = np.array(sys.argv[3:narg-1])
    filelist = get_dirs_true(filelist_short)

    X_n0, X_mean0 = get_config(filelist, n_dim = 3,matchmethod=1,showmatch=0)
    label_list = get_cluster(X_mean0,method="spectral",k=k)
    result_dict_byimg,result_dict_bycat = get_result_cat(filelist_short,label_list)

    outputfile_name = sys.argv[narg-1]
    write_file(result_dict_bycat,outputfile_name)
    print("the correction rate is: %s " %(get_correct_rate(filelist_short,label_list)),end="\n")
    
elif part == 'part2':
    n = sys.argv[2]
    if n == "function1":
        path = sys.argv[3]
        part2.function1(path, transformation_matrix_original, "function1-output.png")
    else:
        n = int(n)
        im1 = sys.argv[3]
        im2 = sys.argv[4]
        imOut = sys.argv[5]
        if n == 1:
            p1 = (int(sys.argv[6]), int(sys.argv[7]))
            p2 = (int(sys.argv[8]), int(sys.argv[9]))
            translate_matrix = part2.translation(p1,p2)
            print("Translation Matrix: \n", translate_matrix)
            part2.function1(im1, translate_matrix, imOut)
        elif n == 2:
            p1 = (int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[10]), int(sys.argv[11]))
            p2 = (int(sys.argv[8]), int(sys.argv[9]), int(sys.argv[12]), int(sys.argv[13]))
            rigid_matrix = part2.rigid(p1,p2)
            print("Rigid Matrix: \n", rigid_matrix)
            part2.function1(im1, rigid_matrix, imOut)
        elif n == 3:
            p1 = (int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[10]), int(sys.argv[11]), int(sys.argv[14]), int(sys.argv[15]))
            p2 = (int(sys.argv[8]), int(sys.argv[9]), int(sys.argv[12]), int(sys.argv[13]),int(sys.argv[16]), int(sys.argv[17]))
            affine_matrix = part2.affine(p1,p2)
            print("Affine Matrix: \n", affine_matrix)
            part2.function1(im1, affine_matrix, imOut)
        else:
            p1 = (int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[10]), int(sys.argv[11]), int(sys.argv[14]), int(sys.argv[15]), int(sys.argv[18]), int(sys.argv[19]))
            p2 = (int(sys.argv[8]), int(sys.argv[9]), int(sys.argv[12]), int(sys.argv[13]),int(sys.argv[16]), int(sys.argv[17]), int(sys.argv[20]), int(sys.argv[21]))                     
            projective_matrix = part2.projective(p1,p2)
            print("Projective Matrix: \n", projective_matrix)
            part2.function1(im1, projective_matrix, imOut)
else:
    im1 = sys.argv[2]
    im2 = sys.argv[3]
    result = sys.argv[4]
    part3.stiching(im1, im2, result)

