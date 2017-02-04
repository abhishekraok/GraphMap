import ctypes
import errno
import gzip
import os
import platform
import random
import string
import urllib2
from StringIO import StringIO

import alpha_conversion
import constants
import numpy as np
from PIL import Image

imagetreeprotbuf_file_extension = '.itpb'


def xyz_to_quadkey(x, y, z):
    quad_key = ''
    for i_z in range(z, 0, -1):
        quad_key += str(2 * (1 if y % 2 == 1 else 0) + (1 if x % 2 == 1 else 0))
        x /= 2
        y /= 2
    return quad_key[::-1]


def quadkey_to_xyz(quadkey):
    """

    :type quadkey: str
    """
    x, y, z = 0, 0, 0
    for ch in quadkey:
        z += 1
        x *= 2
        y *= 2
        if int(ch) > 1:
            y += 1
        if int(ch) % 2 == 1:
            x += 1
    return x, y, z


def get_path(x, y, z):
    return get_path_zyx(x, y, z)


def get_path_zyx(x, y, z):
    return str(z) + '/' + str(y) + '/' + str(x)


def is_power_of_2(num):
    return num == 2 ** np.floor(np.log2(num))


def resolve_link(link):
    """
    Separates a link into nodename and filename. If no filename given, returns nodename, None


    :rtype: str, str
    :type link: str
    """
    splitted = link.split(constants.separator_character)
    split_length = len(splitted)
    if split_length != 1 and split_length != 2:
        raise Exception('Invalid link ', link)
    nodename = splitted[0]
    if split_length == 1:
        return nodename, None
    return nodename, splitted[1]


def format_node_address(filename, node_name):
    return node_name + (constants.separator_character + filename if filename else '')


def get_contents_of_file(filename):
    print('Getting contents from ', filename)
    file_opener = gzip.open if is_gzip(filename) else open
    read_mode = 'rb' if is_protbuf_file(filename) else 'r'
    if os.path.isfile(filename):
        with file_opener(filename, read_mode) as f:
            return f.read()
    if not is_web_link(filename):
        raise Exception('Could not find file locally and it does not seem to be a url', filename)
    request = urllib2.Request(filename)
    request.add_header('Accept-encoding', 'gzip')
    response = urllib2.urlopen(request)
    buf = StringIO(response.read())
    if is_gzip(filename):
        f = gzip.GzipFile(fileobj=buf)
        return f.read()
    else:
        return buf.read()


def proper_shape(imarray):
    height = imarray.shape[0]
    width = imarray.shape[1]
    channel_count = imarray.shape[2]
    if height != width:
        return False
    if not channel_count == 3:
        return False
    return is_power_of_2(height)


def reshape_proper_pil_image(pil_image):
    return Image.fromarray(reshape_proper(np.array(pil_image)))


def reshape_proper(imarray, reshape_resolution=None):
    height = imarray.shape[0]
    width = imarray.shape[1]
    channel_count = imarray.shape[2]
    if channel_count == 4:
        pil_im = alpha_conversion.alpha_to_color(imarray)
    else:
        pil_im = Image.fromarray(imarray)
    if reshape_resolution is not None:
        pil_im.resize(size=(reshape_resolution, reshape_resolution))
        return np.array(pil_im, dtype=np.uint8)[:, :, :3]
    max_resolution = max(height, width)
    resolution_resized = 2 ** int(np.ceil(np.log2(max_resolution)))
    new_array = stretch_keep_aspect(pil_image=pil_im, max_resolution=resolution_resized)
    return new_array


def stretch_keep_aspect(pil_image, max_resolution):
    """
    Resize a given image so that the max resolution is equal to given max resolution and maintains aspec ratio.
    :type pil_image: Image.Image
    :rtype np.array:
    """
    width, height = pil_image.size
    if width > height:
        new_width = max_resolution
        new_height = int(float(height * max_resolution) / width)
    else:
        new_width = int(float(width * max_resolution) / height)
        new_height = max_resolution
    pil_image = pil_image.resize(size=(new_width, new_height))
    blank_array = np.zeros((max_resolution, max_resolution, 3), dtype=np.uint8)
    blank_array[:new_height, :new_width, :3] = np.array(pil_image, dtype=np.uint8)[:, :, :3]
    return blank_array


def is_valid_quadkey(quadkey):
    return all(ch in '0123' for ch in quadkey)


def mkdir_p(path):
    """
    Makes all the folder in the given path.
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_free_space_mb(dirname):
    """Return folder/drive free space (in megabytes).

    From http://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(dirname), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value / 1024 / 1024
    else:
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize / 1024 / 1024


def get_used_space_mb(start_path='.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / 1024 / 1024


def is_gzip(filename):
    """

    :type filename: str
    :rtype:bool
    """
    return filename.endswith('gz') or filename.endswith('gzip')


def put_contents(content, filename):
    print('Putting contents to', filename)
    if is_web_link(filename):
        write_filename = filename.rsplit('/', 1)[-1]
        print('Local write filename ', write_filename)
    else:
        write_filename = filename
    file_opener = gzip.open if is_gzip(filename) else open
    write_mode = 'wb' if is_protbuf_file(filename) else 'w'
    with file_opener(write_filename, write_mode) as f:
        f.writelines(content)
    if is_web_link(filename):
        import amazon_s3
        amazon_s3.upload_file(write_filename, remote_filename=filename)
        os.remove(write_filename)
    else:
        print('Saved as ', filename)


def is_image_file(link):
    """
    Checks whether given url or filename is an image link.
    :type link: str
    :rtype:bool
    """
    return link.lower().endswith('.jpg') or link.lower().endswith('.png')


def is_web_link(filename):
    """
    Determines if a given filename looks like a web url.

    :type filename: str
    :rtype: bool
    """
    return filename.startswith('http')


def url_exists(url):
    import urllib2
    try:
        urllib2.urlopen(url)
        return True
    except urllib2.HTTPError:
        return False
    except urllib2.URLError:
        return False


def file_exists(filename):
    if is_web_link(filename):
        return url_exists(filename)
    return os.path.isfile(filename)


def mse(imageA, imageB):
    # the 'Mean Squared Error' between the two images is the
    # sum of the squared difference between the two images;
    # NOTE: the two images must have the same dimension
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    # return the MSE, the lower the error, the more "similar"
    # the two images are
    return err


def pil_images_equal(first_pil_image, second_pil_image):
    return mse(np.array(first_pil_image), np.array(second_pil_image)) < 0.1


def is_protbuf_file(filename):
    if filename.endswith(imagetreeprotbuf_file_extension):
        return True
    if filename.endswith(imagetreeprotbuf_file_extension + '.gz'):
        return True
    return False


def generate_random_string(length):
    """
    Generates a random string of given length consisting of ASCII letters and numbers.

    :type length: int
    :rtype: str
    """
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))
