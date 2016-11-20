import imagetree
from result import Result


class PersistenceInterface:
    """
    This class is responsible for storing and retrieving the image tree.
    """

    def exists(self, name):
        raise NotImplementedError('This is an interface, subclass this')

    def get_tree(self, root):
        """
        Gets the tree and puts it into result whose value is the image tree.

        :type root:str
        :rtype: Result
        """
        raise NotImplementedError('This is an interface, subclass this')

    def put_tree(self, image_tree):
        """

        :type image_tree:imagetree.ImageTree
        :rtype: Result
        """
        raise NotImplementedError('This is an interface, subclass this')

    def get_all_node_links(self):
        """
        Gets the names of all the nodes.
        """
        raise NotImplementedError('This is an interface, subclass this')

