import imagetree

node_not_found_name = 'standard_nodes.not_found_node'
default_grey_pixel = (128, 128, 128)


def not_found_node(serializer, filename):
    return imagetree.ImageTree(
        name= node_not_found_name,
        input_image=default_grey_pixel,
        children=[],
        children_links=[],
        serializer=serializer,
        filename=filename)
