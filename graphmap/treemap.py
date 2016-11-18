import time

import serializer
import utilities
import serialization.protbuf_serializer


class TreeMap:
    def __init__(self, name_to_image_tree_node_map):
        """
        A mapping of names to ImageTree, no active links

        :type name_to_image_tree_node_map: dict of str and ImageTree.ImageTree
        """
        self.name_to_image_tree_node_map = name_to_image_tree_node_map if name_to_image_tree_node_map is not None else {}
        self.is_child_map = {}

    def has_node(self, node_name):
        return node_name in self.name_to_image_tree_node_map

    def get_node(self, node_name):
        """
        Gets the ImageTree node with specified name. If not found returns a not found node.
        :param node_name:
        :return:
        """
        return self.name_to_image_tree_node_map[node_name]

    @classmethod
    def create_from_file(cls, filename, serializer):
        """
        Creates a TreeMap from given file

        :type serializer: serializer.Serializer
        :rtype: TreeMap
        """
        start_time = time.time()
        serialized_string = utilities.get_contents_of_file(filename)
        print('Deserializing string with lenght ', len(serialized_string))
        name_to_image_tree_node_map = serialization.protbuf_serializer.deserialize_to_name_to_imagetree_node_map(serialized_string,
                                                                                                                 serializer)
        deserialization_time_sec = time.time() - start_time
        if deserialization_time_sec > 0:
            print('Total time taken to deserialize ', filename, ' is ', round((deserialization_time_sec), ndigits=4), ' seconds')
            print('Rate of deserialization is ', round(len(name_to_image_tree_node_map)/deserialization_time_sec, ndigits=4),' lines/sec')
        return TreeMap(name_to_image_tree_node_map=name_to_image_tree_node_map)
