from urllib2 import HTTPError

from enum import Enum

import custom_errors
import imagetree
import imagevalue
import result
import serialization.protbuf_serializer
import serialization.tsv_serializer
import standard_nodes
import tile_disk_cache
import tree_operator
import treemap
import utilities
from graph_helpers import NodeLink
from persistence_interface import PersistenceInterface


class FileType(Enum):
    tsv = 0,
    protbuf = 1
    unknown = 3


def compress_and_save(tree):
    """

    :type tree: imagetree.ImageTree
    :param tree_filename: Can be a local filename to be saved or azure blob url
    :return:
    """
    original_node_count = tree.count_nodes()
    print('Compressing tree, original number of nodes is ', original_node_count)
    tree.compress()
    final_node_count = tree.count_nodes()
    print('Node count after compression is ', final_node_count, ' compression ratio is ',
          float(final_node_count) / original_node_count)
    save_tree(tree)


def save_tree(tree):
    """
    Saves a tree, saves all the nodes.

    :type tree: imagetree.ImageTree
    :rtype: None
    """
    print('Saving tree ', tree.name)
    filename_nodename_node_dictionary = tree.create_node_dictionary()
    for filename in filename_nodename_node_dictionary.iterkeys():
        list_of_nodes = filename_nodename_node_dictionary[filename].itervalues()
        save_tree_given_node_dictionary(filename, list_of_nodes)


def save_tree_given_node_dictionary(filename, list_of_nodes):
    """
    Saves a tree given a list of nodes.

    :type filename: str
    :type list_of_nodes: list of imagetree.ImageTree
    :rtype: None
    """
    if utilities.file_exists(filename):
        raise custom_errors.CreationFailedError('filename ' + filename + ' already exists.')
    filetype = get_filetype(filename)
    if filetype == FileType.protbuf:
        serialized_string = serialization.protbuf_serializer.serialize_list_of_nodes_to_string(list_of_nodes)
    elif filetype == FileType.tsv:
        serialized_string = serialization.tsv_serializer.serialize_list_of_nodes(list_of_nodes)
    else:
        raise custom_errors.CreationFailedError('Unknown filetype ' + filename)
    utilities.put_contents(serialized_string, filename)


def save_tree_only_filename(tree, filename):
    """
    Saves a tree, saves only nodes that have given filename.

    :type tree: imagetree.ImageTree
    :type filename: str
    :rtype: None
    """
    print('Saving tree ', tree.name, ' whose nodes belong to filename ', filename)
    filename_nodename_node_dictionary = tree.create_node_dictionary()
    list_of_nodes = filename_nodename_node_dictionary[filename].itervalues()
    save_tree_given_node_dictionary(filename, list_of_nodes)


def get_filetype(filename):
    if utilities.is_protbuf_file(filename):
        return FileType.protbuf
    if serialization.tsv_serializer.is_tsv_file(filename):
        return FileType.tsv
    return FileType.unknown


def load_link_new_serializer(link, image_cache=None):
    """
    Loads a link by creating a new Serializer.

    :param link: a link to ImageTree file. e.g. orange@orange.tsv.gz
    :type link:str
    :return: Loaded ImageTree object.
    :rtype: imagetree.ImageTree
    """
    return Serializer(image_cache=image_cache).load_node(link=link)


class Serializer(PersistenceInterface):
    def __init__(self, image_cache=None):
        """

        :type tree: imagetree.ImageTree
        :type image_cache: tile_disk_cache.TileCache
        """
        self.filename_treemap_map = {}
        self.image_cache = image_cache

    def load_from_string(self, node_name, filename, serialized_string):
        return self.load_node(link=utilities.format_node_address(filename=filename, node_name=node_name),
                              serialized_string=serialized_string)

    def load_node(self, link, serialized_string=None):
        """
        Loads a single node from given link. Does not load the children

        :type link: str
        :rtype: imagetree.ImageTree
        """
        nodename_with_operator, filename = utilities.resolve_link(link)
        if filename is None:
            return standard_nodes.not_found_node(self, filename='')
        if not filename in self.filename_treemap_map:
            print('Loading node ', nodename_with_operator, ' from file ', filename)
            if serialized_string is None:
                try:
                    serialized_string = utilities.get_contents_of_file(filename)
                except HTTPError:
                    return standard_nodes.not_found_node(self, filename='')
            self.filename_treemap_map[filename] = self.deserialize_string_to_tree_map(filename,
                                                                                      serialized_string=serialized_string)
        nodename, operators_list = tree_operator.get_nodename_and_operators_list(nodename_with_operator)
        if self.filename_treemap_map[filename].has_node(nodename):
            unoperated_node = self.filename_treemap_map[filename].get_node(nodename)
            return tree_operator.apply_operators(unoperated_node, operators_list)
        else:
            print('Node ', nodename, ' not found in file ', filename, ' returning not found blank node.')
            return standard_nodes.not_found_node(serializer=self, filename=filename)

    def deserialize_string_to_tree_map(self, filename, serialized_string):
        """
        Given a serialized string and a filename from which it was created,
        determines what type of file it is and calls appropriate deserializer.

        :param filename: A valid local filename or web link
        :type filename: str
        :type serialized_string: str
        :rtype: treemap.TreeMap
        """
        file_type = get_filetype(filename=filename)
        if file_type == FileType.protbuf:
            return serialization.protbuf_serializer.deserialize_to_tree_map(serialized_string, filename=filename,
                                                                            serializer=self)
        elif file_type == FileType.tsv:
            return serialization.tsv_serializer.deserialize_to_treemap(serialized_string=serialized_string,
                                                                       filename=filename,
                                                                       serializer=self)
        else:
            raise Exception('Unknown filetype ' + filename)

    def put_tree(self, image_tree):
        save_tree(image_tree)

    def get_tree(self, node_link):
        """
        Gets tree for the given node_link
        :type node_link: NodeLink
        :returns: Result wrapping imagetree.ImageTree
        :rtype: result.Result
        """
        try:
            return result.good(self.load_node(node_link.get_old_node_link_string()))
        except custom_errors.NodeNotFoundException as e:
            return result.fail(result.NODE_LINK_NOT_FOUND_ERROR_CODE, e.message)

    def get_all_node_links(self):
        return (node_name for filename in self.filename_treemap_map for node_name in filename)


def create_tree_from_jpg_url(url, name, serializer, filename='create_tree_from_jpg_url'):
    """
    Creates an ImageTree node with no children and image value equal to given jpg url.

    :rtype: imagetree.ImageTree
    """
    jpg_web_image = imagevalue.JpgWebImage(url)
    return imagetree.ImageTree(name=name, children=[], children_links=[], serializer=serializer, filename=filename,
                               input_image=jpg_web_image)
