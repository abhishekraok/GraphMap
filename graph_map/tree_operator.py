import constants
import imagetree
import transforms
from enum import Enum


class Operation(Enum):
    Rotate90 = 1
    Rotate180 = 2
    MirrorVertical = 3


operation_to_string_map = {
    Operation.Rotate90: 'rot90',
    Operation.Rotate180: 'rot180',
    Operation.MirrorVertical: 'mirrorv'
}

string_to_operator_map = dict((string, operator) for operator, string in operation_to_string_map.iteritems())

operator_to_transform_map = {
    Operation.Rotate90: transforms.rotate_90_transform,
    Operation.Rotate180: transforms.rotate_180_transform,
    Operation.MirrorVertical: transforms.mirror_vertical_transform
}


def apply_transform(input_list, transform_to_apply):
    return [input_list[i] for i in transform_to_apply]


def rotate_90(input_list):
    """
    Rotates the input list in clockwise direction once.

    :type input_list: list
    :rtype: list
    """
    return apply_transform(input_list, transforms.rotate_90_transform)


def rotate_180(input_list):
    """
    Rotates the input list in clockwise direction twice.

    :type input_list: list
    :rtype: list
    """
    return apply_transform(input_list, transforms.rotate_180_transform)


def mirror_vertical(input_list):
    """
    Reflects along the y axis.

    :type input_list: list
    :rtype: list
    """
    return apply_transform(input_list, transforms.mirror_vertical_transform)


operator_to_function_map = {
    Operation.Rotate90: rotate_90,
    Operation.Rotate180: rotate_180,
    Operation.MirrorVertical: mirror_vertical
}


def format_name(original_node_name, operation):
    """
    Returns the jpg_link with operator

    :type original_node_name: str
    :type operation: Operation
    :rtype: str
    """
    return operator_to_string(operation) + constants.operator_separator + original_node_name


def extract_first_operator(node_name_with_operator):
    """
    Returns the nodename + the operator if present else None.

    :param node_name_with_operator:
    :return: str,Operation
    """
    if not constants.operator_separator in node_name_with_operator:
        return node_name_with_operator, None
    operator_string, node_name = node_name_with_operator.split(constants.operator_separator, 1)
    return node_name, string_to_operator(operator_string)


def operate_tree(input_tree, operation):
    """
    Operates on the tree according to the given operation

    :type input_tree: imagetree.ImageTree
    :type operation:Operation
    :rtype: imagetree.ImageTree
    """
    transform = operator_to_transform_map[operation]
    transform_name = format_name(original_node_name=input_tree.name, operation=operation)

    return transform_tree(input_tree, transform, transform_name)


def transform_tree(input_tree, transform, transform_name):
    """
    Transform the given tree according to the transform list and creates a new tree with a new name based
    on transform_name

    :type input_tree: imagetree.ImageTree
    :type transform: list of int
    :type transform_name: str
    :rtype : imagetree.ImageTree
    """
    if input_tree.is_leaf():
        return input_tree
    if input_tree._children and len(input_tree._children) > 0:
        operated_children = apply_transform(input_tree._children, transform)
    else:
        operated_children = input_tree._children
    operated_children_links = apply_transform(input_tree._children_links, transform)
    return imagetree.ImageTree(
        name=transform_name,
        children=operated_children,
        children_links=operated_children_links,
        input_image=input_tree._image_value,
        serializer=input_tree.serializer,
        filename=input_tree.filename
    )


def operator_to_string(operation):
    """
    Gives the standard string for operation
    :type operation: Operation
    :return: str
    """
    return operation_to_string_map[operation]


def string_to_operator(operator_string):
    """
    Converts string representation of operator to an type Operation

    :type operator_string:str
    :rtype:Operation
    """
    return string_to_operator_map[operator_string]


def get_nodename_and_operators_list(nodename_with_operator):
    """
    Gets the node name and list of operators.
    :type nodename_with_operator: str
    :rtype:str, list of Operation
    """
    if not constants.operator_separator in nodename_with_operator:
        return nodename_with_operator, []
    extracted_operator = Operation.Rotate90
    operations_list = []
    nodename = nodename_with_operator
    while extracted_operator is not None:
        nodename, extracted_operator = extract_first_operator(nodename)
        if extracted_operator is not None:
            operations_list.append(extracted_operator)
    return nodename, operations_list


def apply_operators(unoperated_tree, operators_list):
    """
    Applies list of operater on the tree, from backwards to forward.

    :type unoperated_tree: imagetree.ImageTree
    :type operators_list: list of Operation
    :rtype: imagTree.ImageTree
    """
    transforms_list = [operator_to_transform_map[i] for i in operators_list]
    final_transform = transforms.identity_transform[:]
    for transform in transforms_list[::-1]:
        final_transform = apply_transform(final_transform, transform)
    if final_transform == transforms.identity_transform:
        return unoperated_tree
    return transform_tree(unoperated_tree, final_transform,
                          str(final_transform) + constants.operator_separator + unoperated_tree.name)
