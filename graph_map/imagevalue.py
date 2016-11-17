import cStringIO
import urllib

import numpy as np
import pylru
import utilities
from PIL import Image


def fetch_image_from_url(url):
    """
    Returns a pil image from given url
    :rtype Image.Image:
    """
    if utilities.url_exists(url):
        img_stream = cStringIO.StringIO(urllib.urlopen(url).read())
        pil_image = Image.open(img_stream)
        return pil_image
    return Image.new("RGB", size=(256, 266), color='black')


class ImageValue:
    """
    An image class that has the ability to provide raster image at any resolution. In either array or pil Image format.
    """

    def get_pil_image(self, resolution):
        """
        Returns a pil Image at requested resolution.

        :rtype:  Image.Image
        """
        raise NotImplementedError('This is an interface')

    def get_np_array(self, resolution):
        raise NotImplementedError('This is an interface')

    def is_set(self):
        raise NotImplementedError('This is an interface')

    def get_pil_image_at_full_resolution(self):
        raise NotImplementedError('This is an interface')

    def get_pil_image_at_full_resolution_proper_shape(self):
        pass


image_cache_size = 1000
pil_image_cache = pylru.lrucache(image_cache_size)
proper_shape_image_cache = pylru.lrucache(image_cache_size)


class JpgWebImage(ImageValue):
    """
    A lazily fetched web image.
    """

    def __init__(self, url):
        """
        Given url is stored. When asked to render it fetches the image.

        :type _pil_image: Image.Image
        """
        self.url = url
        if url in pil_image_cache:
            self._pil_image = pil_image_cache[url]
        else:
            self._pil_image = None
        if url in proper_shape_image_cache:
            self._proper_shape_image = proper_shape_image_cache[url]
        else:
            self._proper_shape_image = None
        self.cache = pylru.lrucache(10)

    @property
    def pil_image(self):
        if self._pil_image is None:
            self._pil_image = fetch_image_from_url(self.url)
            pil_image_cache[self.url] = self._pil_image
        return self._pil_image

    def get_pil_image_at_full_resolution(self):
        return self.pil_image

    def get_pil_image_at_full_resolution_proper_shape(self):
        if self._proper_shape_image is None:
            self._proper_shape_image = utilities.reshape_proper_pil_image(self.get_pil_image_at_full_resolution())
            proper_shape_image_cache[self.url] = self._proper_shape_image
        return self._proper_shape_image

    def get_pil_image(self, resolution):
        """
        Returns a pil Image at requested resolution.

        :rtype:  Image.Image
        """
        return self.pil_image.resize((resolution, resolution))

    def get_np_array(self, resolution):
        """Convert to numpy array.

        Drop alpha"""
        cache_key = str(resolution)
        if cache_key in self.cache:
            return self.cache[cache_key]
        pil_image = self.get_pil_image_at_full_resolution()
        im_array = np.array(pil_image, dtype=np.uint8)
        square_image = utilities.reshape_proper(im_array)
        return_value = np.array(Image.fromarray(square_image).resize((resolution, resolution)), dtype=np.uint8)
        self.cache[cache_key] = return_value
        return return_value

    def is_set(self):
        return True

    def __eq__(self, other):
        return self.url == other.url

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return 'JpegWebImage({})'.format(self.url)
