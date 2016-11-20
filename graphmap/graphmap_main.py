import custom_errors
import graph_helpers
import result_file
import tree_creator


class GraphMap:
    def __init__(self, persistence=None):
        """
        This class provides a simplified interface to create and modify Image Trees.
        Hides away the implementation of ImageTree and Serializer.

        :type persistence: PersistenceInterface
        """
        self.persistence = persistence

    def create_node(self, root_node_link, image_value_link=None, children_links=()):
        """
        Creates a node with given name.

        :type root_node_link: graph_helpers.NodeLink
        :type image_value_link: str
        :type children_links: tuple of str
        :return: Result whose value is the created node's name.
        :rtype: result_file.Result
        """
        if self.persistence.exists(root_node_link):
            return result_file.fail(result_file.NAME_ALREADY_EXISTS,
                                    'Node {0} is already present'.format(root_node_link))
        try:
            created_tree = tree_creator.create_tree(node_link=root_node_link, children_links=children_links,
                                                    persistence=self.persistence,
                                                    image_value_link=image_value_link)
            self.persistence.put_tree(created_tree)
            return result_file.good(created_tree.get_link())
        except custom_errors.CreationFailedError as e:
            return result_file.fail(result_file.WRONG_CHILDREN_COUNT, e.message)

    def connect_child(self, root_node_link, quad_key, child_node_link, new_root_name=None):
        """
        Adds a node with given name at given quad key.

        :type root_node_link: graph_helpers.NodeLink
        :type quad_key: str
        :type child_node_link: graph_helpers.NodeLink
        :type new_root_name: graph_helpers.NodeLink
        :return: Result whose value is the created root name.
        :rtype: result_file.Result
        """
        root_tree_result = self.persistence.get_tree(root_node_link)
        if not root_tree_result.is_success():
            return root_tree_result
        root_tree = root_tree_result.value
        if new_root_name is None:
            new_root_name = graph_helpers.random_node_link()
        create_tree_result = tree_creator.create_new_from_old_insert_node_link(old_tree=root_tree,
                                                                 link_to_insert=child_node_link.__str__(),
                                                                 quad_key=quad_key, filename=new_root_name.filename,
                                                                 new_tree_name=new_root_name.node_name)
        if create_tree_result.is_fail():
            return create_tree_result
        self.persistence.put_tree(create_tree_result.value)
        return result_file.good(create_tree_result.value.get_node_link())

    def node_exists(self, name):
        return self.persistence.exists(name)

    def get_child_name(self, root_node_link, quad_key):
        """
        Gets the name of the node at the location given by quad key wrt root.

        :type root_node_link: graph_helpers.NodeLink
        :type quad_key: str
        :return: Result whose value is a str name of node.
        :rtype: result_file.Result
        """
        image_tree_result = self.persistence.get_tree(root_node_link)
        if image_tree_result.is_fail():
            return image_tree_result
        image_tree = image_tree_result.value
        try:
            return result_file.good(image_tree.get_descendant(quad_key=quad_key))
        except custom_errors.NodeNotFoundException as e:
            return result_file.fail(message=e.message, code=result_file.NODE_LINK_NOT_FOUND_ERROR_CODE)

    def get_image_at_quad_key(self, root_node_link, resolution, quad_key):
        """
        Gets the pil image at quad key.

        :type root_node_link: graph_helpers.NodeLink
        :type resolution: int
        :type quad_key: str
        :return: Result whose value is a PIL Image.
        :rtype: result_file.Result
        """
        return result_file.combine((
            lambda prev_value: self.persistence.get_tree(root_node_link),
            lambda prev_value: result_file.good(prev_value.get_pil_image_at_quadkey(
                resolution=resolution, quad_key=quad_key))))

    def get_all_node_links(self):
        return self.persistence.get_all_node_links()
