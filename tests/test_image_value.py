import unittest
from graphmap import imagevalue
from graphmap import utilities

test_url = 'https://en.wikipedia.org/wiki/Impression,_Sunrise'

class CreateNodeTests(unittest.TestCase):
  def test_url_is_converted_to_image(self):
    url_imager = imagevalue.UrlWebImage(test_url)
    jpeg_image = url_imager.get_pil_image(256)
    self.assertEqual(jpeg_image.size, 256)
