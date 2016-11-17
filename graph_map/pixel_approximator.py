from enum import Enum
import standard_pixel


def simple_average_pixels(pixels_list):
    """
    Does a simple arithmetic mean averaging of rgb.

    :param pixels_list: 4 pixels to be approximated.
    :type pixels_list: list of standard_pixel.Pixel
    :return: Averaged pixel
    :rtype: standard_pixel.Pixel
    """
    input_pixel = tuple(int(float(sum([pix.get_rgb()[i] for pix in pixels_list])) / 4) for i in range(3))
    return standard_pixel.Pixel(input_pixel=input_pixel)


class PixelApproximator:
    @staticmethod
    def approximate(four_pixels_list, method):
        if method == PixelApproximationMethod.simple_avg:
            return PixelApproximator.simple_average(four_pixels_list)
        raise Exception('Unknown method of pixel approximation ', method)

    @staticmethod
    def simple_average(four_pixels_list):
        return tuple(int(float(sum([pix[i] for pix in four_pixels_list])) / 4) for i in range(3))


class PixelApproximationMethod(Enum):
    simple_avg = 1
