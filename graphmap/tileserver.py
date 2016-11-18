from Queue import Queue
from StringIO import StringIO

import constants
import decorators_library
import serializer
from flask import send_file
import imagetree


def pil_image_to_string_io(pil_img):
    """
    Converts a PIL Image into string io
    """
    img_io = StringIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/jpeg')


class MultiRootTileServer:
    """
    Contains a dictionary of TileServerSingleRoot. Each one contains an image tree. This is like a memory cache.

    :type root_link_tile_server_map : dict from str to  TileServerSingleRoot
    """
    def __init__(self, image_cache):
        self.root_link_tile_server_map = {}
        self.image_cache = image_cache

    def get_tile_image(self, root_link, x, y, z, resolution):
        if root_link not in self.root_link_tile_server_map:
            print('Root link ', root_link, ' not in dict, loading..')
            self.root_link_tile_server_map[root_link] = TileServerSingleRoot(root=root_link,
                                                                             image_cache=self.image_cache)
        return self.root_link_tile_server_map[root_link].get_tile_image(x, y, z, resolution=resolution)

    def get_node_link(self, root_link, x, y, z):
        if root_link not in self.root_link_tile_server_map:
            print('Root link ', root_link, ' not in dict, loading..')
            self.root_link_tile_server_map[root_link] = TileServerSingleRoot(root=root_link,
                                                                             image_cache=self.image_cache)
        return self.root_link_tile_server_map[root_link].get_node_link(x, y, z)

    def drop_root_link(self, root_link):
        if root_link in self.root_link_tile_server_map:
            del (self.root_link_tile_server_map[root_link])
            print ('Deleted root link ', root_link)
            return True
        else:
            print ('Given root link not present ')
            return False

    def get_tile_io(self, root_link, x, y, z, resolution):
        """
        Gets the tile image as string IO

        :type root_link: str
        :type x: int
        :type y: int
        :type z: int
        :type resolution: int
        """
        pil_im = self.get_tile_image(x=x, y=y, z=z, root_link=root_link, resolution=resolution)
        return pil_image_to_string_io(pil_img=pil_im)

    def cache_burst(self):
        cache_burst_message = 'MultiRootTileserver: Dropping {} tile servers'.format(
            len(self.root_link_tile_server_map))
        print(cache_burst_message)
        self.root_link_tile_server_map = {}
        return cache_burst_message + self.image_cache.cache_burst

    @decorators_library.asynchronous
    def populate_cache_async(self, root_link, cache_limit):
        self.populate_cache(root_link, cache_limit=cache_limit)

    def populate_cache(self, root_link, cache_limit):
        """
        Populates image cache by calling all the children in image tree.
        """
        resolution = constants.default_tile_resolution
        if root_link not in self.root_link_tile_server_map:
            self.root_link_tile_server_map[root_link] = TileServerSingleRoot(root=root_link,
                                                                             image_cache=self.image_cache)
        starting_image_tree = self.root_link_tile_server_map[root_link].tree
        cached_set = set()
        cached_set.add(starting_image_tree.name)
        cache_count = self.image_cache.count_files_in_disk()
        request_queue = Queue()
        request_queue.put(starting_image_tree)
        print('Starting tile cache populator with root link = {} starting number of files = {}. Limit = {}'
              .format(root_link, cache_count, cache_limit))
        while not request_queue.empty() and cache_count < cache_limit:
            current_tree = request_queue.get()
            cached_set.add(current_tree.name)
            pil_image = current_tree.get_pil_image(resolution=resolution)
            print('Requesting tile for ', current_tree.name)
            del (pil_image)
            cache_count += 1
            for child in current_tree.get_children():
                if child.name not in cached_set:
                    request_queue.put(child)

    def stats_dict(self):
        cache_stats = self.image_cache.stats_dict() if self.image_cache else {}
        cache_stats['node links loaded in multi root tile server '] = str(len(self.root_link_tile_server_map))
        return cache_stats


class TileServerSingleRoot:
    """
    Contains an ImageTree.

    :type tree: imagetree.ImageTree
    """
    def __init__(self, root, image_cache):
        self.root = root
        self.tree = serializer.load_link_new_serializer(self.root, image_cache=image_cache)
        print('Creating tile server for root ', self.root)

    def get_tile_image(self, x, y, z, resolution):
        return self.tree.get_pil_image_at_xyz(x, y, z, resolution=resolution)

    def get_node_link(self, x, y, z):
        return self.tree.get_node_link_from_xyz(x, y, z)
