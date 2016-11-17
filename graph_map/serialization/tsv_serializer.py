"""
The schema for tsv serialization is without the spaces
        name \t pixel0 \t pixel1 \t pixel2 \t pixel3 \t child_link0 \t
        child_link1 \t child_link2 \t child_link3 \t image url \n
"""
import imagetree_core.imagetree
import imagetree_core.standard_pixel
import imagetree_core.treemap
import imagetree_core.utilities
import imagetree_core.imagevalue
import imagetree_core.utilities


def deserialize_to_imagetree_node(line, filename, serializer):
    """
    Deserialize a line of compact TSV encoded string into ImageTree Node

    :type line: str
    :rtype: imagetree_core.imagetree.ImageTree
    """
    split_line = line.strip().split('\t')
    name = split_line[0]
    image_value = imagetree_core.standard_pixel.deserialize_from_list_of_strings(split_line[1:4])
    children_names = [i for i in split_line[4:8] if i is not '']
    if len(split_line) > 8:
        image_url = split_line[8]
        # image url can be a jpg/png image or a node link.
        if imagetree_core.utilities.is_image_file(image_url):
            image_value = imagetree_core.imagevalue.JpgWebImage(image_url)
        else:
            image_value = serializer.load_node(link=image_url)
    return imagetree_core.imagetree.ImageTree(name=name, input_image=image_value, children_links=children_names, children=[],
                                              serializer=serializer, filename=filename)


def deserialize_to_treemap(serialized_string, filename, serializer):
    all_nodes = (deserialize_to_imagetree_node(line=line, filename=filename, serializer=serializer)
                 for line in serialized_string.split('\n'))
    name_to_image_tree_node_map = dict((node.name, node) for node in all_nodes)
    return imagetree_core.treemap.TreeMap(name_to_image_tree_node_map=name_to_image_tree_node_map)


def convert_imagetree_to_tsv_string_dictionary(input_imagetree):
    """
    Converts given input ImageTree to a tsv compressed file.

    :type input_imagetree: imagetree_core.imagetree.ImageTree
    :rtype:dict from str to str
    """
    filename_nodename_node_dictionary = input_imagetree.create_node_dictionary()
    filename_tsvencoded_string_map = {}
    for filename in filename_nodename_node_dictionary.iterkeys():
        list_of_nodes = filename_nodename_node_dictionary[filename].itervalues()
        serialized_string = serialize_list_of_nodes(list_of_nodes)
        filename_tsvencoded_string_map[filename] = serialized_string
    return filename_tsvencoded_string_map


def serialize_list_of_nodes(list_of_nodes):
    # \n is included in the serialize_node function
    return ''.join(i.serialize_node() for i in list_of_nodes)


def save_tree(input_imagetree):
    """
    Saves all the files in the given tree as tsv encoded format.
    :type input_imagetree: imagetree_core.imagetree.ImageTree
    """
    filename_tsvencoded_string_map = convert_imagetree_to_tsv_string_dictionary(input_imagetree)
    for filename, serialized_sring in filename_tsvencoded_string_map.iteritems():
        imagetree_core.utilities.put_contents(serialized_sring, filename)


def is_tsv_file(filename):
    return 'tsv' in filename.split('.')[1:]
