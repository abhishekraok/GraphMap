import imagetree
import imagetree_core.constants
from imagetree_core import serializer
from imagetree_core.utilities import quadkey_to_xyz, xyz_to_quadkey, create_tree_from_url, is_valid_quadkey
import commander
import constants
import sys

valid_commands = ['+', '-', 'l', 'r', 'u', 'd', 's']


def tree_viewer_valid_input(input_command):
    return input_command in valid_commands or \
           is_valid_quadkey(input_command) or \
           input_command.startswith('c') or \
           input_command.startswith('http')


def tree_viewer(tree):
    """
    Interactively display the tree.

    :type tree: imagetree.ImageTree
    """
    import matplotlib.pyplot as plt
    x, y, z = 0, 0, 0
    im_array = tree.get_pil_image_at_xyz(x, y, z, constants.default_tile_resolution)
    plt.imshow(im_array)
    plt.draw()
    plt.pause(1)
    print('You can move around, connect to an existing image and insert image from url')
    print('To move around please enter one of' + str(valid_commands))
    print('To connect enter c <node_link> e.g. >c line@https://azurewebsite.line.tsv.gz')
    print('To insert another image please input this\n<image url> <jpg_link> e.g. >http://imgur.com/haha.jpg smile')
    input_command = raw_input('>')
    while tree_viewer_valid_input(input_command):
        if input_command == '+':
            x *= 2
            y *= 2
            z += 1
        if input_command == '-':
            x /= 2
            y /= 2
            z -= 1
        if input_command == 'l':
            x -= 1
        if input_command == 'r':
            x += 1
        if input_command == 'd':
            y += 1
        if input_command == 'u':
            y -= 1
        if input_command == 's':
            quad_key = xyz_to_quadkey(x, y, z)
            print('Saving at current location of ', quad_key, ' where filename is ', tree.filename)
            serializer.save_tree(tree)
        if is_valid_quadkey(input_command):
            x, y, z = quadkey_to_xyz(quadkey=input_command)
        current_quadkey = xyz_to_quadkey(x, y, z)
        if input_command.startswith('c'):
            _, node_link = input_command.split(' ')
            quad_key = current_quadkey
            print('connecting node link', node_link, ' at quadkey ', quad_key)
            commander.insert_tree_root(root_tree=tree, child_link=node_link, quad_key=quad_key, save=False)
        if input_command.startswith('http'):
            url, node_name = input_command.split(' ')
            blob_url = 'https://artmapstore.blob.core.windows.net/firstnodes/' + node_name + '.tsv.gz'
            quad_key = current_quadkey
            print('Inserting image ', url, ' at quadkey ', quad_key)
            another_tree = create_tree_from_url(url=url, node_name=tree.name, tree_filename=blob_url,
                                                max_resolution=1024)
            tree.insert(another_tree, quad_key)
        print(
        'xyz=', x, y, z, '. quadkey=', current_quadkey, 'node link=', tree.get_descendant(current_quadkey).get_link())
        im_array = tree.get_pil_image_at_xyz(x, y, z, constants.default_tile_resolution)
        plt.imshow(im_array)
        plt.draw()
        plt.pause(1)
        input_command = raw_input('>')


if __name__ == '__main__':
    print('Tree viewer with options ', sys.argv)
    if len(sys.argv) > 1:
        node_link = sys.argv[1]
    else:
        node_link = imagetree_core.constants.ROOT_LINK
    tree = serializer.load_link_new_serializer(node_link)
    tree_viewer(tree)
