import constants
import imagetree
import tree_operator
import serializer


def red_pixel_tree(filename, serializer):
    return imagetree.ImageTree(children=[], children_links=[], name='red_pixel_tree',
                               input_image=constants.red_rgb_tuple, filename=filename,
                               serializer=serializer)


def green_pixel_tree(filename, serializer):
    return imagetree.ImageTree(children=[], children_links=[], name='green_pixel_tree',
                               input_image=constants.green_rgb_tuple, filename=filename,
                               serializer=serializer)


def blue_pixel_tree(filename, serializer):
    return imagetree.ImageTree(children=[], children_links=[], name='blue_pixel_tree',
                               input_image=constants.blue_rgb_tuple, filename=filename,
                               serializer=serializer)


if __name__ == '__main__':
    rotating_tree = serializer.load_link_new_serializer('rotating_rgb@../data/rotating_pixels.tsv.gz')
    rotating_tree.show(resolution=512)
