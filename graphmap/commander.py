from __future__ import print_function

import argparse
import ntpath
import time

import azure_image_tree
import imagetree
import tree_viewer
import matplotlib.pyplot as plt
import serializer
import utilities


def show(tree, resolution, quad_key=None):
    if quad_key is None:
        quad_key = ''
    plt.imshow(tree.get_pil_image_at_quadkey(resolution=resolution, quad_key=quad_key), interpolation='none')
    plt.draw()
    plt.pause(1)


def process_args(parser):
    arguments = parser.parse_args()

    if arguments.show:
        if not arguments.nodelink:
            print('Error! Need nodelink option')
            parser.print_help()
            exit()
        tree = serializer.load_link_new_serializer(arguments.nodelink)
        resolution = arguments.resolution if arguments.resolution is not None else 512
        show(tree, resolution, arguments.quad_key)
        time.sleep(10)
        exit()

    if arguments.create_tree:
        input_image = arguments.input_image
        nodelink = arguments.nodelink
        create_tree(input_image, nodelink)
        exit()

    if arguments.insert_tree_link:
        insert_tree_link(arguments.nodelink, arguments.child_nodelink, arguments.quad_key)
        exit()

    if arguments.tree_viewer:
        if not arguments.nodelink:
            print('Error! Need nodelink option')
            parser.print_help()
            exit()
        tree = serializer.load_link_new_serializer(arguments.nodelink)
        tree_viewer.tree_viewer(tree)
        exit()

    if arguments.upload_file:
        filename_without_path = ntpath.split(arguments.input_image)[-1]
        azure_image_tree.upload_to_blob_name(arguments.input_image, blob_name=filename_without_path)
        exit()

    parser.print_help()


def create_tree(input_image, node_link):
    if not input_image:
        print('Error! Need input image.', create_tree_help)
        parser.print_help()
        exit()
    if not node_link:
        print('Error! Need nodelink. e.g. -nl orange@orange.tsv.gz')
        parser.print_help()
        exit()
    node_name, filename = utilities.resolve_link(node_link)
    tree = utilities.from_imagefile(imagefilename=input_image, name=node_name, tree_filename=filename)
    serializer.compress_and_save(tree)
    show(tree, 512)


def insert_tree_link(root_link, child_link, quad_key):
    """
    Inserts a given child link into an existing tree whos link is root_link at the specified quad key.
    The root_link is loaded.

    :type root_link: str
    :type child_link: str
    :type quad_key: str
    :return: None
    """
    if not root_link:
        print('Error! Need parent nodelink.', insert_tree_help)
        parser.print_help()
        exit()
    if not child_link:
        print('Error! Need the nodelink of child ')
        parser.print_help()
        exit()
    if not quad_key:
        print('Error! Need the quad key of location to be inserted')
        parser.print_help()
        exit()
    root_tree = serializer.load_link_new_serializer(root_link)
    insert_tree_root(root_tree=root_tree, child_link=child_link, quad_key=quad_key)


def insert_tree_root(root_tree, child_link, quad_key, save=True):
    """
    Inserts a given child link to an existing root tree at the specified quad key.

    :type root_tree: imagetree.ImageTree
    :type child_link: str
    :type quad_key: str
    :return: None
    """
    insertion_tree = serializer.load_link_new_serializer(child_link)
    print('Inserting tree ', insertion_tree.name, ' into tree ', root_tree.name, ' at qk=', quad_key)
    root_tree.insert(insertion_tree, quad_key=quad_key)
    parent_tree = root_tree.get_descendant(quad_key[:-1])
    if save:
        serializer.save_tree(parent_tree)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    create_tree_help = "Creates tree from image. e.g. -ct -ii orange.jpg -nl orange@orange.tsv.gz"
    insert_tree_help = 'Insert one tree in another. Format.-it -nl <parent node link> -qk <quadkey where to insert> ' \
                       '-cl <node link of to be inserted tree>'
    # Main commands
    parser.add_argument("--show", help="Display a tree", action='store_true')
    parser.add_argument("-tv", "--tree_viewer", action='store_true')
    parser.add_argument("-it", "--insert_tree_link", action='store_true', help=insert_tree_help)
    parser.add_argument("-ct", "--create_tree", action='store_true', help=create_tree_help)
    # sub options
    parser.add_argument("-nl", "--nodelink", help="The link adress of the node")
    parser.add_argument("-cl", "--child_nodelink", help="The link adress of the child node")
    parser.add_argument("-res", "--resolution", type=int, help="The image resolution to display")
    parser.add_argument("-ii", "--input_image")
    parser.add_argument("-qk", "--quad_key", help="The quadkey. e.g 013001")
    parser.add_argument("-uf", "--upload_file", action='store_true',
                        help="Uploads a local file to azure e.g -uf -ii <source>")
    process_args(parser)
