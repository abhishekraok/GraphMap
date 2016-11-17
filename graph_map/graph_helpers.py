import utilities


class NodeLink:
    def __init__(self, node_name, filename=None):
        """

        :type node_name: str
        """
        self.node_name = node_name
        self.filename = filename

    def get_node_name(self):
        return self.node_name

    def get_file_name(self):
        return self.filename

    def __str__(self):
        return utilities.format_node_address(filename=self.filename, node_name=self.node_name)

    def get_old_node_link_string(self):
        return self.__str__()

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __hash__(self):
        return hash((self.node_name, self.filename))


class QuadKey:
    def __init__(self, input_quad_key):
        self.quad_key = input_quad_key

    def head(self):
        return int(self.quad_key[0])

    def tail(self):
        return QuadKey(self.quad_key[1:])


def random_node_link():
    return NodeLink(node_name='root', filename=utilities.generate_random_string(length=20))
