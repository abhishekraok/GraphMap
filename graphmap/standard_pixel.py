import imagevalue
from PIL import Image
from serialization import imagetree_pb2
import numpy as np
import constants


class Pixel(imagevalue.ImageValue):
    SIMILARITY_THRESHOLD = 5

    def __init__(self, input_pixel):
        """
        The pixel of an image.

        :rtype: Pixel
        :type input_pixel: tuple of int
        """
        self.r = None
        self.g = None
        self.b = None
        if input_pixel and len(input_pixel) == 3:
            if max(input_pixel) > 255:
                raise Exception('Invalid pixel ' + str(input_pixel))
            if min(input_pixel) < 0:
                raise Exception('Invalid pixel ' + str(input_pixel))
            self.r, self.g, self.b = input_pixel

    def is_set(self):
        return self.r is not None and self.g is not None and self.b is not None

    def get_rgb(self):
        if self.is_set():
            return (self.r, self.g, self.b)
        return ()

    def get_np_array_1D(self):
        if self.is_set():
            return np.array([self.r, self.g, self.b], dtype=np.uint8)
        raise ValueError('Pixel is not set, but was asked for np array')

    def serialize(self):
        if self.is_set():
            return str(self.r) + '\t' + str(self.g) + '\t' + str(self.b) + '\t'
        return '\t\t\t'

    def __str__(self):
        return self.serialize()

    def __eq__(self, other):
        """

        :type other: Pixel
        """
        if not self.is_set() and not other.is_set():
            return True
        return self.r == other.r and self.g == other.g and self.b == other.b

    def __ne__(self, other):
        return not self == other

    def approximately_equal(self, other):
        return abs(self.r - other.r) < Pixel.SIMILARITY_THRESHOLD and \
               abs(self.g - other.g) < Pixel.SIMILARITY_THRESHOLD and \
               abs(self.b - other.b) < Pixel.SIMILARITY_THRESHOLD

    def to_protobuf(self):
        proto_pixel = imagetree_pb2.Pixel()
        if self.is_set():
            proto_pixel.r = self.r
            proto_pixel.g = self.g
            proto_pixel.b = self.b
        return proto_pixel

    def get_pil_image(self, resolution):
        """
        Returns a pil Image at requested resolution.

        :rtype:  Image.Image
        """
        return Image.new("RGB", (resolution, resolution), color=self.get_rgb())

    def get_np_array(self, resolution):
        if self.is_set():
            return np.tile(self.get_np_array_1D(), (resolution, resolution,1))
        return np.zeros((resolution, resolution, constants.color_channels_used), dtype=np.uint8)

    def get_pil_image_at_full_resolution(self):
        return self.get_pil_image(resolution=1)

    def get_pil_image_at_full_resolution_proper_shape(self):
        return self.get_pil_image(resolution=1)

def deserialize(serialized_pixel):
    """
    Converts a serialized string to a Pixel class

    :type serialized_pixel: str
    """
    split_line = serialized_pixel.split('\t')
    return deserialize_from_list_of_strings(split_line)


def deserialize_from_list_of_strings(list_of_strings):
    result_deserialize = tuple(int(i) for i in list_of_strings if i is not '')
    return Pixel(result_deserialize)
