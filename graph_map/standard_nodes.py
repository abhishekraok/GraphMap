import imagetree

default_grey_pixel = (128, 128, 128)


def not_found_node(serializer, filename):
    return imagetree.ImageTree(
        name='standard_nodes.not_found_node',
        input_image=default_grey_pixel,
        children=[],
        children_links=[],
        serializer=serializer,
        filename=filename)
