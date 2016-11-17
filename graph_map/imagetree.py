from __future__ import print_function

import imagevalue
import numpy as np
import pixel_approximator
import serializer
import standard_pixel
import utilities
from PIL import Image
from custom_errors import NodeNotFoundException
import constants
import custom_errors
from graph_helpers import NodeLink, QuadKey


def empty_image_tree(name, serializer, filename):
    return ImageTree(children=[], children_links=[], name=name, serializer=serializer, filename=filename,
                     input_image=())


def get_child_array(im_array, child_index):
    """
    Given an image array, gets the image array corresponding the the child.
    :type im_array: np.array
    :type child_index: int
    :rtype:np.array
    """
    resolution = im_array.shape[0]
    if im_array.shape[0] != im_array.shape[1]:
        raise ValueError('Expected square image, it is ' + str(im_array.shape))
    if resolution <= 1:
        return im_array
    if child_index == 0:
        return im_array[:resolution / 2, :resolution / 2, :]
    if child_index == 1:
        return im_array[:resolution / 2, resolution / 2:, :]
    if child_index == 2:
        return im_array[resolution / 2:, :resolution / 2, :]
    if child_index == 3:
        return im_array[resolution / 2:, resolution / 2:, :]
    raise ('Invalid index for child ' + str(child_index))


def image_at_quad_key(input_image, resolution, quad_key):
    """
    Renders input image at given quadkey at given resolution.

    Expects a square image as input.
    :type input_image: np.array
    :type resolution: int
    :type quad_key: str
    :rtype: np.array
    """
    if input_image.shape[0] != input_image.shape[1]:
        raise ValueError('Expected square image, it is ' + str(input_image.shape))
    if quad_key == '':
        return np.array(Image.fromarray(input_image).resize((resolution, resolution)))
    return image_at_quad_key(get_child_array(input_image, int(quad_key[0])), resolution=resolution,
                             quad_key=quad_key[1:])


def child_image(input_pil_image, child_index):
    """
    Returns the sub image given by child index

    Expects a square image as input.
    :type input_image: Image.Image
    :type child_index: int
    :rtype: Image.Image
    """


def pil_image_at_quad_key(input_pil_image, quad_key):
    """
    Renders input PIL image at given quadkey.

    Expects a square image as input.
    :type input_image: Image.Image
    :type quad_key: str
    :rtype: Image.Image
    """
    input_resolution, _ = input_pil_image.size
    start_x = 0
    start_y = 0
    end_x = input_resolution
    end_y = input_resolution
    for quad_key_char in quad_key:
        if start_x >= end_x + 1 or start_y >= end_y + 1:
            break
        child_index = int(quad_key_char)
        if child_index == 0:
            end_x -= (end_x - start_x) / 2
            end_y -= (end_y - start_y) / 2
        elif child_index == 1:
            start_x += (end_x - start_x) / 2
            end_y -= (end_y - start_y) / 2
        elif child_index == 2:
            end_x -= (end_x - start_x) / 2
            start_y += (end_y - start_y) / 2
        elif child_index == 3:
            start_x += (end_x - start_x) / 2
            start_y += (end_y - start_y) / 2
        else:
            raise ValueError('quadkey is invalid ' + quad_key)
    box = (start_x, start_y, end_x, end_y)
    return input_pil_image.crop(box=box)


class ImageTree:
    """
    Represents an image as a tree.

    Each node is a pixel. This is a quad tree. Each node has 0 or 4 child.
    Children can be active (self.children_private) or a link (self.children_links)
    """

    def __init__(self, name, input_image, children_links, serializer, filename, children=None):
        """

        :type input_image: tuple of int or link to image.
        :type children: list of ImageTree
        :type children_links: list of str
        :type filename: str
        :type serializer: serializer.Serializer
        """
        self.name = name
        self.serializer = serializer
        self._children_links = children_links  # The locations of children, to load lazily
        self.filename = filename
        # Process children
        if children is None:
            children = []
        children_count = len(children)
        if children_count is not 4 and children_count is not 0:
            raise custom_errors.CreationFailedError('Children count is not 4 or 0')
        if len(children_links) is not 4 and len(children_links) is not 0:
            raise custom_errors.CreationFailedError(
                'Children links count is not 4 or 0. They are ' + ' '.join(children_links))
        self._children = children
        # Set image value
        if isinstance(input_image, (list, tuple)):
            if len(input_image) != 3 and len(input_image) != 0:
                raise custom_errors.CreationFailedError(str(input_image) + ' is incorrect format for pixel')
            self._image_value = standard_pixel.Pixel(input_image)
        elif isinstance(input_image, imagevalue.ImageValue):
            self._image_value = input_image
        else:
            raise custom_errors.CreationFailedError('Input pixel is not correct type' + str(input_image))

    def get_image_value(self):
        if self._image_value:
            return self._image_value
        return ()

    @property
    def children_links(self):
        return [child_link
                if (constants.separator_character in child_link)
                else utilities.format_node_address(self.filename, child_link)
                for child_link in self._children_links]

    def get_children(self):
        """
        Lazily gets the children. If loaded returns them, else loads and returns them.

        :rtype: list of ImageTree
        :return: list of children nodes
        """
        if self._children is None or self._children == []:
            self._children = [self.serializer.load_node(child_link) for child_link in self.children_links]
        return self._children

    def info(self):
        """

        :rtype: str
        """
        return self.name + ' is the imagetree_core with child count = ' + str(self.count_nodes()) + \
               ' and height =' + str(self.height(max_height=1000))

    def count_nodes(self, unique_map=None):
        if unique_map is None:
            unique_map = {}
        if self.name in unique_map:
            return 0
        unique_map[self.name] = self.name
        return 1 + sum(i.count_nodes(unique_map=unique_map) for i in self.get_children())

    def height(self, max_height):
        if self.is_leaf():
            return 1
        return 1 + max(i.height(max_height=max_height - 1) for i in self.get_children())

    def is_leaf(self):
        if len(self._children_links) is not 0:
            return False
        return len(self._children) is 0

    def get_pil_image(self, resolution):
        if self.serializer.image_cache is not None:
            if self.serializer.image_cache.has_image(image_tree=self, resolution=resolution):
                return self.serializer.image_cache.get_image(image_tree=self, resolution=resolution)
            else:
                pil_image = Image.fromarray(self.get_np_array(resolution))
                self.serializer.image_cache.put_image(pil_image=pil_image, image_tree=self, resolution=resolution)
                return pil_image
        return Image.fromarray(self.get_np_array(resolution))

    def get_np_array(self, resolution):
        im = np.zeros((resolution, resolution, 3), dtype=np.uint8)
        return self.render(resolution, im_array=im)

    def render(self, resolution, im_array):
        if im_array is None:
            raise ValueError('input im array is None')
        if im_array.shape[0:2] != (resolution, resolution):
            raise ValueError('Input image array is of shape {} but asked for resolution {}'
                             .format(im_array.shape, resolution))
        # Render ancestors
        if self._image_value and self._image_value.is_set():
            im_array = self._image_value.get_np_array(resolution=resolution)
        # Render children
        if self.is_leaf() or resolution <= 1 or im_array.shape[0] <= 1:
            return im_array
        im_array[:resolution / 2, :resolution / 2, :] = self.get_children()[0] \
            .render(resolution / 2, get_child_array(im_array, 0))
        im_array[:resolution / 2, resolution / 2:, :] = self.get_children()[1] \
            .render(resolution / 2, get_child_array(im_array, 1))
        im_array[resolution / 2:, :resolution / 2, :] = self.get_children()[2] \
            .render(resolution / 2, get_child_array(im_array, 2))
        im_array[resolution / 2:, resolution / 2:, :] = self.get_children()[3] \
            .render(resolution / 2, get_child_array(im_array, 3))
        return im_array

    def save_image(self, filename, resolution):
        imarray = self.get_np_array(resolution)
        pil_img = Image.fromarray(imarray, 'RGB')
        print('Saving ', filename)
        pil_img.save(filename)
        return filename

    @staticmethod
    def from_image_array(array, name, filename):
        if len(array.shape) != 3 or any(i == 0 for i in array.shape) or array.shape[2] != 3:
            raise Exception('improper imarray dimension', array.shape)
        if array.shape[0] == 1 or array.shape[1] == 1:
            imtree = ImageTree(children=[], name=name,
                               input_image=tuple((int(i) for i in array[0, 0, :].flatten())),
                               children_links=[], serializer=serializer.Serializer(), filename=filename)
            return imtree
        resolution = array.shape[0]
        children_0 = ImageTree.from_image_array(array[:resolution / 2, :resolution / 2, :], name=name + '0',
                                                filename=filename)
        children_1 = ImageTree.from_image_array(array[:resolution / 2, resolution / 2:, :], name=name + '1',
                                                filename=filename)
        children_2 = ImageTree.from_image_array(array[resolution / 2:, :resolution / 2, :], name=name + '2',
                                                filename=filename)
        children_3 = ImageTree.from_image_array(array[resolution / 2:, resolution / 2:, :], name=name + '3',
                                                filename=filename)
        return ImageTree(children=[children_0, children_1, children_2, children_3], name=name, input_image=(),
                         children_links=[children_0.name, children_1.name, children_2.name, children_3.name],
                         serializer=serializer.Serializer(), filename=filename)

    def get_descendant(self, quad_key):
        """
        Gets the child node corresponding the the quad_key.

        quad_key is a string, e.g '032' => first child's 4th's child's 3rd child.
        If not found raises NodeNotFoundException
        :rtype: ImageTree
        """
        if quad_key == '':
            return self
        index_child = int(quad_key[0])
        if index_child >= len(self.get_children()):
            raise NodeNotFoundException('The child index is out of range ' + quad_key + ' in ' + self.name)
        return self.get_children()[index_child].get_descendant(quad_key[1:])

    def get_node_link_from_xyz(self, x, y, z):
        quad_key = utilities.xyz_to_quadkey(x, y, z)
        return self.get_descendant(quad_key=quad_key).get_link()

    def __eq__(self, other):
        """
        Checks if this tree is equal to the other tree

        :type other: ImageTree
        """
        if other is None:
            return False
        if self.name != other.name:
            return False
        if self._children_links != other._children_links:
            return False
        if self._image_value != other._image_value:
            return False
        if len(self.get_children()) != len(other.get_children()):
            return False
        for child, other_child in zip(self.get_children(), other.get_children()):
            if child != other_child:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.get_link()

    def __repr__(self):
        return self.serialize_node()

    def serialize_node(self):
        if isinstance(self._image_value, imagevalue.JpgWebImage):
            if self.is_leaf():
                return self.name + '\t\t\t\t' + '\t'.join(['' for _ in range(4)]) + '\t' + self._image_value.url + '\n'
            return self.name + '\t\t\t\t' + '\t'.join(self._children_links) + '\t' + self._image_value.url + '\n'
        if isinstance(self._image_value, standard_pixel.Pixel):
            return self.name + '\t' + self._image_value.serialize() + '\t'.join(self._children_links) + '\n'
        if isinstance(self._image_value, ImageTree):
            if self.is_leaf():
                return self.name + '\t\t\t\t' + '\t'.join(
                    ['' for _ in range(4)]) + '\t' + self._image_value.get_link() + '\n'
            return self.name + '\t\t\t\t' + '\t'.join(self._children_links) + '\t' + self._image_value.get_link() + '\n'
        raise Exception('Unknown type of _image_value ' + str(self._image_value))

    def remove_similar_children(self):
        if self.is_leaf():
            return
        if not isinstance(self._image_value, standard_pixel.Pixel):
            return
        if not self._image_value.is_set():
            self._image_value = pixel_approximator.simple_average_pixels(list(i._image_value for i in self._children))
        for child in self._children:
            if not self._image_value.approximately_equal(child._image_value):
                return
        self._children = []
        self._children_links = []

    def compress(self):
        for child in self.get_children():
            child.compress()
        self.remove_similar_children()

    def replace_child(self, another_tree, index):
        """
        Places given another_tree at the specified index child.

        If no children then throws error.
        :type another_tree: ImageTree
        :type index: int
        """
        if self.is_leaf():
            raise Exception('Tree ' + self.name + ' cannot replace with ' + another_tree.name + ' as it is a leaf')
        self._children[index] = another_tree
        self._children_links[index] = another_tree.get_link()

    def insert(self, another_tree, quad_key):
        """
        Inserts another tree into the existing tree at the specified quadkey.

        Deletes existing node if at the quadkey if present. Else creates all the required empty children.
        :type another_tree:ImageTree
        :type quad_key: string
        :rtype: None
        """
        if len(quad_key) <= 0:
            raise Exception('Quadkey cannot be blank. Cannot replace self with another tree.')
        if not utilities.is_valid_quadkey(quad_key):
            raise Exception('Given quadkey is not valid ' + quad_key)
        replace_index = int(quad_key[0])
        if self.is_leaf():
            self.grow_empty()
        if len(quad_key) == 1:
            self.replace_child(another_tree, replace_index)
        else:
            self.get_children()[replace_index].insert(another_tree, quad_key[1:])

    def get_link(self):
        return utilities.format_node_address(filename=self.filename, node_name=self.name)

    def get_node_link(self):
        return NodeLink(node_name=self.name, filename=self.filename)

    def grow_empty(self):
        """
        Creates empty children for self.
        """
        self._children = [empty_image_tree(name=self.name + str(i), serializer=self.serializer, filename=self.filename)
                          for i in range(4)]
        self._children_links = [i.get_link() for i in self._children]

    def create_node_dictionary(self):
        """
        Creates a dictionary with key node name and value the ImageTree Node.

        :rtype: dict from str to ImageTreeNode
        """
        filename_nodename_node_map = {}
        self.add_to_node_dictionary(filename_nodename_node_map)
        return filename_nodename_node_map

    def add_to_node_dictionary(self, filename_nodename_node_map):
        """
        Adds all the nodes of this tree to the filename_nodename_node_map.

        :type filename_nodename_node_map: dict of str and ImageTree
        :rtype: None
        """
        if not self.filename in filename_nodename_node_map:
            filename_nodename_node_map[self.filename] = {}
        if self.filename in filename_nodename_node_map:
            if self.name in filename_nodename_node_map[self.filename]:
                return
        filename_nodename_node_map[self.filename][self.name] = self
        for child in self.get_children():
            child.add_to_node_dictionary(filename_nodename_node_map)

    def set_filename(self, filename):
        old_filename = self.filename
        self.filename = filename
        for child in self.get_children():
            if child.filename == old_filename:
                child.set_filename(filename)

    def visit(self, action):
        """
        Applies the function action to self and all the children.
        :param action: Any function that takes input the ImageTree and returns a boolean that indicates stop.
        Stop at true
        :return: None
        """
        stop_processing = action(self)
        if not stop_processing:
            for child in self.get_children():
                child.visit(action)

    def add_to_dictionary_function(self, function, nodename_to_output_map=None):
        """
        Similar to LINQ ToDictionary.

        :param function: Function that will transform each node
        :rtype: list
        """
        if nodename_to_output_map is None:
            nodename_to_output_map = {}
        if self.name in nodename_to_output_map:
            return
        nodename_to_output_map[self.name] = function(self)
        for child in self.get_children():
            child.add_to_dictionary_function(function, nodename_to_output_map)

    def select(self, function):
        """
        Similar to LINQ select function
        :param function: function that transforms each node.
        :return: list of function(node)
        """
        nodename_to_output_map = {}
        self.add_to_dictionary_function(function, nodename_to_output_map=nodename_to_output_map)
        return list(nodename_to_output_map.itervalues())

    def get_pil_image_at_xyz(self, x, y, z, resolution):
        """
        Gets the tile image at x, y, z. If tile is not found raises NodeNotFoundException
        :rtype: Image.Image
        """
        print('Getting pil image for node', self.name, ' xyz=', x, y, z, ' at resolution of ', resolution)
        quad_key = utilities.xyz_to_quadkey(x, y, z)
        return self.get_pil_image_at_quadkey(resolution=resolution, quad_key=quad_key)

    def get_pil_image_at_quadkey(self, resolution, quad_key):
        return Image.fromarray(self.get_np_array_at_quad_key(resolution=resolution, quad_key=quad_key))

    def get_np_array_at_quad_key(self, resolution, quad_key, input_im_array=None):
        if len(quad_key) <= 0:
            if input_im_array is None:
                return self.get_np_array(resolution=resolution)
            return self.render(resolution=resolution, im_array=input_im_array)
        child_index = int(quad_key[0])
        if self.is_set():
            current_full_pil_image = self._image_value.get_pil_image_at_full_resolution_proper_shape()
            im_array = np.array(current_full_pil_image)
            current_im_array = image_at_quad_key(im_array, resolution=resolution,
                                                 quad_key=quad_key)
        else:
            current_im_array = input_im_array
        if self.is_leaf():
            return current_im_array
        return self.get_children()[child_index].get_np_array_at_quad_key(resolution=resolution, quad_key=quad_key[1:],
                                                                         input_im_array=current_im_array)

    def is_set(self):
        if not self._image_value:
            return False
        return self._image_value.is_set()

    def insert_jpg_at_quadkey(self, jpg_link, quad_key):
        tree_to_be_inserted = serializer.create_tree_from_jpg_url(url=jpg_link, name=self.name + quad_key,
                                                                  serializer=self.serializer, filename=self.filename)
        self.insert(another_tree=tree_to_be_inserted, quad_key=quad_key)

    def get_pil_image_at_full_resolution(self):
        return self.get_pil_image(resolution=256)
