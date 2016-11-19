import imagetree
import result_file
import persistence_interface
import result_file
from graph_helpers import NodeLink
import serializer
import custom_errors


class MemoryPersistence(persistence_interface.PersistenceInterface):
    def __init__(self):
        self.tree_dictionary = {}

    def put_tree(self, input_tree):
        """

        :type input_tree: imagetree.ImageTree
        :return:
        """
        self.tree_dictionary[input_tree.get_link()] = input_tree

    def exists(self, node_link):
        """
        Checks if given node link is stored.

        :type node_link: NodeLink
        :return:
        """
        if isinstance(node_link, NodeLink):
            key = node_link.get_old_node_link_string()
        else:
            key = node_link
        return key in self.tree_dictionary

    def get_tree(self, requested_node_link):
        if isinstance(requested_node_link, NodeLink):
            key = requested_node_link.get_old_node_link_string()
        else:
            key = requested_node_link
        if key in self.tree_dictionary:
            return result_file.good(self.tree_dictionary[key])
        # If not found in memory try disk
        try:
            image_tree = serializer.load_link_new_serializer(requested_node_link.get_old_node_link_string())
            self.put_tree(image_tree)
            return result_file.good(image_tree)
        except custom_errors.NodeNotFoundException as e:
            pass
        return result_file.fail(code=result_file.NODE_LINK_NOT_FOUND_ERROR_CODE,
                                message=str(requested_node_link) + ' not found in Memory Persistence')
