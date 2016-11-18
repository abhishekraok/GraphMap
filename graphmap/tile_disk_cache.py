"""
Disk caching ImageTree get pil image function
"""
import ntpath
import os
import random
import shutil
import string

import imagetree
import utilities
from PIL import Image


class CacheStats:
    def __init__(self, cache_count, cache_dir, used_space, free_space):
        self.cache_count = cache_count
        self.cache_dir = cache_dir
        self.used_space = used_space
        self.free_space = free_space

    def __str__(self):
        return 'Cache disk usage. Count {} Dir {}. Used space {}MB. Free space {}MB' \
            .format(self.cache_count, self.cache_dir, self.used_space, self.free_space)

    @classmethod
    def empty_cache(cls):
        return CacheStats(0, '.', 0, 0)


def save_image_to_disk(file_path, pil_image):
    directory_to_save = os.path.dirname(file_path)
    if not os.path.isdir(directory_to_save):
        utilities.mkdir_p(directory_to_save)
    pil_image.save(file_path, "JPEG")
    print('Saved image to file ', file_path)


def to_valid_filename(link):
    """
    Convert a unique root link to unique filename. Should not have non approved characters, but should
    not map to same name, so hashing.
    """
    link_hash = str(hash(link))[1:10]  # skipping 1 to ignore negative sign
    valid_chars = "%s%s" % (string.ascii_letters, string.digits)
    valid_filename = ''.join(i for i in (link + link_hash) if i in valid_chars)
    return valid_filename


class TileCache:
    def __init__(self, cache_dir, size, verbose=False):
        self.cache_dir = cache_dir
        self.size = size
        self.cache_count = 0
        self.verbose = verbose
        if not os.path.isdir(self.cache_dir):
            os.mkdir(self.cache_dir)
            print 'Created cache directory %s' \
                  % os.path.join(os.path.abspath(__file__), self.cache_dir)
        else:
            self.cache_count = self.count_files_in_disk()
            print('Cache dir ', self.cache_dir, ' already exists, current no. of files ', self.cache_count)

    def cache_burst(self):
        print('Cache burst')
        current_count = self.cache_count
        free_space = self.disk_stats()
        shutil.rmtree(self.cache_dir, ignore_errors=True)
        now_space = self.disk_stats()
        self.cache_count = 0
        return 'Had ' + str(current_count) + ' images in disk cache.' + 'Previously ' + free_space + '\n' + now_space

    def image_tree_args_to_path(self, image_tree, resolution):
        """

        :type image_tree:imagetree.ImageTree
        :type resolution: int
        :rtype:str
        """
        return ntpath.join(self.cache_dir, str(resolution),
                           to_valid_filename(image_tree.filename), to_valid_filename(image_tree.name) + '.jpg')

    def count_files_in_disk(self):
        return sum(len(files) for r, d, files in os.walk(self.cache_dir))

    def remove_random(self):
        path, dirs, files = os.walk(self.cache_dir).next()
        chosen_file = random.choice(files)
        if self.verbose:
            print('Removing file randomly ', chosen_file)
        os.remove(chosen_file)
        self.cache_count -= 1

    def disk_stats(self):
        """ Gets the size of cache and free space left"""
        return self.stats().__str__()

    def stats(self):
        return CacheStats(cache_count=self.cache_count, cache_dir=self.cache_dir,
                          used_space=utilities.get_used_space_mb(self.cache_dir),
                          free_space=utilities.get_free_space_mb(self.cache_dir))

    def stats_dict(self):
        cache_stats = self.stats()
        return {'cache count': str(self.cache_count),
                'cache dir': self.cache_dir,
                'used space': str(cache_stats.used_space) + ' MB',
                'free space': str(cache_stats.free_space) + ' MB'}

    def has_image(self, image_tree, resolution):
        """
        Determines whether the cache has image for given tree or not.
        :type image_tree: imagetree.ImageTree
        :type resolution: int
        :rtype : bool
        """
        file_path = self.image_tree_args_to_path(image_tree, resolution)
        if self.verbose:
            print('file path is ', file_path, ' count is ', self.cache_count)
        return os.path.isfile(file_path)

    def get_image(self, image_tree, resolution):
        """
        Gets the image already present in cache.

        :type image_tree: imagetree.ImageTree
        :type resolution: int
        :rtype : bool
        """
        file_path = self.image_tree_args_to_path(image_tree, resolution)
        pil_image = Image.open(file_path)
        pil_image.load()
        return pil_image

    def put_image(self, pil_image, image_tree, resolution):
        """
        Determines whether the cache has image for given tree or not.
        :type  pil_image: Image.Image
        :type image_tree: imagetree.ImageTree
        :type resolution: int
        :rtype : bool
        """
        file_path = self.image_tree_args_to_path(image_tree, resolution)
        save_image_to_disk(file_path, pil_image)
        self.cache_count += 1
        if self.cache_count > self.size:
            self.remove_random()
        return pil_image

    def __repr__(self):
        return 'TileCache(cache_dir={}, size={}, verbose={}). Cache Count is {}' \
            .format(self.cache_dir, self.size, self.verbose, self.cache_count)
