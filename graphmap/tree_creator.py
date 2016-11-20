import constants
import custom_errors
import imagetree
import serializer
import utilities
import imagevalue
from graph_helpers import NodeLink
import result


def create_new_from_old_and_save(old_root_link, quad_key, image_link, name, filename):
    """
    Creates a new tree by inserting given link to at quadkey and saving it in specified filename.

    Returns the new node link.

    :type old_root_link: str
    :type quad_key: str
    :type image_link:str
    :type name: str
    :type filename: str
    :rtype : str
    """
    filetype = serializer.get_filetype(filename)
    if filetype == serializer.FileType.unknown:
        filename = filename + '.tsv'
    new_tree = create_tree_from_old(filename, image_link, name, old_root_link, quad_key)
    serializer.save_tree_only_filename(new_tree, filename)
    return new_tree.get_link()


def create_tree_from_old(filename, image_link, name, old_root_link, quad_key):
    """
    Creates a new tree by inserting given link to at quadkey.

    Returns the new tree.

    :type old_root_link: str
    :type quad_key: str
    :type image_link:str
    :type name: str
    :type filename: str
    :rtype : imagetree.ImageTree
    """
    print('Inserting {} with name {}@{} into root node {}'.format(image_link, name, filename, old_root_link))
    old_tree = serializer.load_link_new_serializer(old_root_link)
    new_tree_creator = create_new_from_old_insert_jpg \
        if utilities.is_image_file(image_link) \
        else create_new_from_old_insert_node_link
    new_tree = new_tree_creator(old_tree=old_tree, link_to_insert=image_link, quad_key=quad_key,
                                filename=filename, new_tree_name=name).value
    return new_tree


def create_new_from_old_insert_node_link(old_tree, link_to_insert, quad_key, filename, new_tree_name):
    """
    Creates a new tree, given an old tree, by inserting node_link at given quadkey. New tree will have name = given
    name.

    :type old_tree: imagetree.ImageTree
    :type link_to_insert: str
    :type quad_key: str
    :type filename: str
    :type new_tree_name: str
    :return: imagetree.ImageTree
    :rtype: result.Result
    """
    if len(quad_key) == 0:
        raise Exception('Quadkey for insert node link should have > 1 length')

    if old_tree.is_leaf():
        new_tree = imagetree.ImageTree(name=new_tree_name, filename=filename, children_links=[],
                                       input_image=old_tree.get_image_value(), children=[],
                                       serializer=old_tree.serializer)
        another_tree_result = old_tree.serializer.get_tree(NodeLink(link_to_insert))
        if another_tree_result.is_fail():
            return another_tree_result
        another_tree = another_tree_result.value
        try:
            new_tree.insert(another_tree=another_tree, quad_key=quad_key)
        except custom_errors.CreationFailedError as e:
            return result.fail(result.NODE_LINK_NOT_FOUND_ERROR_CODE, e.message)
        return result.good(new_tree)

    children = old_tree.get_children()[:]  # deep copy
    children_links = old_tree.children_links[:]
    child_index = int(quad_key[0])

    if len(quad_key) == 1:
        children_links[child_index] = link_to_insert
        children = []
        new_tree = imagetree.ImageTree(name=new_tree_name, filename=filename, children_links=children_links,
                                       input_image=old_tree.get_image_value(), children=children,
                                       serializer=old_tree.serializer)
        return result.good(new_tree)

    new_child_result = create_new_from_old_insert_node_link(old_tree=old_tree.get_children()[child_index],
                                                            link_to_insert=link_to_insert,
                                                            quad_key=quad_key[1:],
                                                            new_tree_name=new_tree_name + quad_key[0],
                                                            filename=filename)
    if new_child_result.is_fail():
        return new_child_result
    new_child = new_child_result.value
    children[child_index] = new_child
    children_links[child_index] = new_child.get_link()
    new_tree = imagetree.ImageTree(name=new_tree_name, filename=filename, children_links=children_links,
                                   input_image=old_tree.get_image_value(), children=children,
                                   serializer=old_tree.serializer)
    return result.good(new_tree)


def create_new_from_old_insert_jpg(old_tree, link_to_insert, quad_key, filename, new_tree_name):
    """
    Creates a new tree, given an old tree, by inserting jpg image at given quadkey. New tree will have name = given
    name.

    :type old_tree: imagetree.ImageTree
    :type link_to_insert: str
    :type quad_key: str
    :type filename: str
    :type new_tree_name: str
    :returns: Result wrapping imagetree.ImageTre
    :rtype : result.Result
    """
    if quad_key == '':
        new_tree = serializer.create_tree_from_jpg_url(url=link_to_insert, serializer=old_tree.serializer,
                                                       name=new_tree_name,
                                                       filename=filename)
        return result.good(new_tree)
    if old_tree.is_leaf():
        new_tree = imagetree.ImageTree(name=new_tree_name, filename=filename, children_links=[],
                                       input_image=old_tree.get_image_value(),
                                       children=[], serializer=old_tree.serializer)
        new_tree.insert_jpg_at_quadkey(jpg_link=link_to_insert, quad_key=quad_key)
        return result.good(new_tree)
    children = old_tree.get_children()[:]  # deep copy
    children_links = old_tree.children_links[:]
    child_index = int(quad_key[0])
    new_child = create_new_from_old_insert_jpg(old_tree=old_tree.get_children()[child_index],
                                               link_to_insert=link_to_insert,
                                               quad_key=quad_key[1:], new_tree_name=new_tree_name + quad_key[0],
                                               filename=filename).value
    children[child_index] = new_child
    children_links[child_index] = new_child.get_link()
    new_tree = imagetree.ImageTree(name=new_tree_name, filename=filename, children_links=children_links,
                                   input_image=old_tree.get_image_value(), children=children,
                                   serializer=old_tree.serializer)
    return result.good(new_tree)


def get_next_version_name(current_version_filename):
    components = current_version_filename.split('.')
    all_components_version_index = [i for i, comp in enumerate(components) if constants.version_string in comp]
    if len(all_components_version_index) > 0:
        # version found
        last_components_version_index = all_components_version_index[-1]
        current_version_string = components[last_components_version_index]
        current_version = int(current_version_string.split(constants.version_string)[-1])
        new_version_string = constants.version_string + str(current_version + 1)
        return '.'.join(components[:last_components_version_index] + [new_version_string] + \
                        components[last_components_version_index + 1:])
    # no version found
    if utilities.is_gzip(current_version_filename):
        insertion_point = -2
    else:
        insertion_point = -1
    return '.'.join(components[:insertion_point] + [constants.version_string + '1'] + \
                    components[insertion_point:])


def create_node_link_for_new_user(username):
    filename = 'https://artmapstore.blob.core.windows.net/firstnodes/user/' + username + '/start.ver_0.tsv'
    ser = serializer.Serializer()
    first_tree = serializer.create_tree_from_jpg_url(url=constants.WELCOME_IMAGE, name='start', filename=filename,
                                                     serializer=ser)
    try:
        serializer.save_tree_only_filename(first_tree, filename)
    except custom_errors.CreationFailedError:
        pass
    return first_tree.get_link()


def create_tree(node_link, children_links, persistence, image_value_link):
    """
    Creates a new ImageTree

    :type node_link: graph_helpers.NodeLink
    :param children_links:
    :param persistence:
    :param image_value_link:
    :rtype: imagetree.ImageTree
    """
    jpge_image_value = imagevalue.JpgWebImage(image_value_link)
    created_tree = imagetree.ImageTree(name=node_link.node_name, filename=node_link.filename,
                                       children_links=children_links, input_image=jpge_image_value,
                                       serializer=persistence)
    return created_tree
