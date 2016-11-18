"""
Contains all the standard transforms.
"""

"""
Shift clockwise 90 degree
01 => 20
23    31
"""
rotate_90_transform = [2, 0, 3, 1]

"""
Shift clockwise 180 degree
01 => 32
23    10
"""
rotate_180_transform = [3, 2, 1, 0]

"""
Shift clockwise 180 degree
01 => 10
23    32
"""
mirror_vertical_transform = [1, 0, 3, 2]

identity_transform = [0, 1, 2, 3]
