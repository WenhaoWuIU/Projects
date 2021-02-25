import numpy as np
from PIL import Image
import cv2 as cv
import math


transformation_matrix_original = np.array([
    [0.907, 0.258, -182],
    [-0.153, 1.44, 58],
    [-0.000306, 0.000731, 1],
])

def function1(path, transformation_matrix, outputName):
    image = Image.open(path)
    width, height = image.size
    new_img = Image.new('RGB', (width, height), color = 'black')
    for i in range(width):
        for j in range(height):
            color = image.getpixel((i, j))
            current_location = np.array([[i],[j],[1]])
            new_location = np.dot(transformation_matrix, current_location)
            new_x, new_y = new_location[0][0]/new_location[2][0], new_location[1][0]/new_location[2][0]
            if new_x > 0 and new_x < width-1 and new_y > 0 and new_y < height-1:
                new_img.putpixel((int(new_x), int(new_y)), color)
                new_img.putpixel((int(new_x), int(new_y-1)), color)
                new_img.putpixel((int(new_x-1), int(new_y)), color)
                new_img.putpixel((int(new_x-1), int(new_y-1)), color)

    new_img.save(outputName)


def translation(point1, point2):
    horizontal = point2[0] - point1[0]
    vertical = point2[1] - point1[1]

    matrix = np.array([
        [1, 0, horizontal],
        [0, 1, vertical],
        [0, 0, 1],
    ])
    return matrix


def rotation(group1, group2):

    radian1 = np.arctan2((group1[3] - group1[1]), (group1[2]-group1[0]))
    radian2 = np.arctan2((group2[3] - group2[1]), (group2[2]-group2[0]))
    m1 = (group1[3] - group1[1])/(group1[2]-group1[0])
    m2 = (group2[3] - group2[1])/(group2[2]-group2[0])

    theta = radian2 - radian1

    rigid_rotate_matrix = np.array([
        [math.cos(theta), -math.sin(theta), 0],
        [math.sin(theta), math.cos(theta), 0],
        [0, 0, 1],
    ])
    return rigid_rotate_matrix

def rigid(group1, group2):
    rotation_matrix = rotation(group1, group2)
    translation_matrix = translation((group1[0], group2[1]),(group2[0], group2[1]))
    rigid_matrix = np.dot(rotation_matrix, translation_matrix)
    return rigid_matrix
  
def shear(point1, point2):
    shx = (point2[0]-point1[0])/point1[1]
    shy = (point2[1]-point1[1])/point1[0]
    shear_matrix = np.array([
        [1, shx, 0],
        [shy, 1, 0],
        [0, 0, 1],
    ])
    return shear_matrix


def scale(point1, point2):
    sx = point2[0]/point1[0]
    sy = point2[1]/point1[1]
    scale_matrix = np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, 1],
    ])
    return scale_matrix


def affine(group1, group2):
    p1 = np.float32([
        [group1[0], group1[1]],
        [group1[2], group1[3]],
        [group1[4], group1[5]],
    ])
    p2 = np.float32([
        [group2[0], group2[1]],
        [group2[2], group2[3]],
        [group2[4], group2[5]],
    ])
    result = cv.getAffineTransform(p1,p2)
    affine_matrix = np.array(result)
    matrix3d = np.append(affine_matrix, [[0,0,1]], axis=0)
    return  matrix3d
def affine_b(group1, group2):
    p1 = np.float32([
        [group1[0], group1[1]],
        [group1[2], group1[3]],
        [group1[4], group1[5]],
    ])
    p2 = np.float32([
        [group2[0], group2[1]],
        [group2[2], group2[3]],
        [group2[4], group2[5]],
    ])
    translate_matrix = translation((group1[4], group1[5]), (group2[4], group2[5]))
    rotation_matrix = rotation((group1[0], group1[1], group1[2], group1[3]), (group2[0], group2[1], group2[2], group2[3]))
    shear_matrix = shear((group1[4], group1[5]), (group2[4], group2[5]))
    scale_matrix = scale((group1[4], group1[5]), (group2[4], group2[5]))
    affine_matrix = np.dot(translate_matrix, np.dot(shear_matrix, np.dot(rotation_matrix, scale_matrix)))
    return affine_matrix

def projective(group1, group2):
    p1 = np.float32([
        [group1[0], group1[1]],
        [group1[2], group1[3]],
        [group1[4], group1[5]],
        [group1[6], group1[7]],
    ])
    p2 = np.float32([
        [group2[0], group2[1]],
        [group2[2], group2[3]],
        [group2[4], group2[5]],
        [group2[6], group2[7]],
    ])
    result = cv.getPerspectiveTransform(p1,p2)
    projective_matrix = np.array(result)
    return  projective_matrix

