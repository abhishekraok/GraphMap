import imagetree_core.imagetree
import imagetree_core.treemap
import imagetree_pb2


def serialize_list_of_nodes_to_proto_forest(list_of_imagetree_nodes):
    """
    Converts a list of ImageTree Nodes into a list of protbuf image tree nodes.

    :type list_of_imagetree_nodes: list of imagetree_core.imagetree.ImageTree
    :rtype: imagetree_pb2.ImageForest
    """
    proto_forest = imagetree_pb2.ImageForest()
    for node in list_of_imagetree_nodes:
        proto_node = proto_forest.forest.add()
        proto_node.name = node.name
        for child in node.children_links:
            proto_node.children.name.append(child)
        if node._image_value.is_set():
            proto_node.pixel.r, \
            proto_node.pixel.g, \
            proto_node.pixel.b = node._image_value.get_rgb()
    return proto_forest

def serialize_list_of_nodes_to_string(list_of_imagetree_nodes):
    """
    Converts a list of ImageTree Nodes into a protbuf string.

    :type list_of_imagetree_nodes: list of imagetree_core.imagetree.ImageTree
    :rtype: str
    """
    return serialize_list_of_nodes_to_proto_forest(list_of_imagetree_nodes).SerializeToString()

def convert_imagetree_to_protobuf_strings(input_imagetree):
    """
    Converts given input ImageTree to a dictionary of filename, protobuf string.
    :type input_imagetree: imagetree_core.imagetree.ImageTree
    :rtype:dict from str to str
    """
    filename_nodename_node_dictionary = input_imagetree.create_node_dictionary()
    filename_protobuf_string_map = {}
    for filename in filename_nodename_node_dictionary.iterkeys():
        list_of_nodes = list(filename_nodename_node_dictionary[filename].itervalues())
        proto_forest = serialize_list_of_nodes_to_proto_forest(list_of_nodes)
        filename_protobuf_string_map[filename] = proto_forest.SerializeToString()
    return filename_protobuf_string_map


def serialize_filename(input_imagetree):
    """
    Serializes all the nodes that have same filename as given tree node.
    Todo: Optimize this, currently goes through all the nodes, including different filenames.

    :type input_imagetree: imagetree_core.imagetree.ImageTree
    :rtype:str
    """
    return convert_imagetree_to_protobuf_strings(input_imagetree)[input_imagetree.filename]


def deserialize_to_name_to_imagetree_node_map(serialized_string, filename, serializer):
    """
    Deserializes a protbuf encoded string into a dict.

    :type serialized_string: str
    :rtype:dict from str to imagetree_core.imagetree.ImageTree
    """
    name_to_image_tree_node_map = {}
    protbuf_forest = imagetree_pb2.ImageForest()
    protbuf_forest.ParseFromString(serialized_string)
    for proto_node in protbuf_forest.forest:
        children_lins = [i for i in proto_node.children.name]
        pixel_value = (proto_node.pixel.r, proto_node.pixel.g, proto_node.pixel.b)
        imagetree_node = imagetree_core.imagetree.ImageTree(children=[], name=proto_node.name, input_image=pixel_value,
                                                            children_links=children_lins, filename=filename,
                                                            serializer=serializer)
        name_to_image_tree_node_map[imagetree_node.name] = imagetree_node
    return name_to_image_tree_node_map


def deserialize_to_tree_map(serialized_string, filename, serializer):
    """
    Given a protobuf serialized string converts it into TreeMap

    :type serialized_string: str
    :rtype: imagetree_core.treemap.TreeMap
    """
    return imagetree_core.treemap.TreeMap(
        deserialize_to_name_to_imagetree_node_map(serialized_string=serialized_string, filename=filename,
                                                  serializer=serializer))
