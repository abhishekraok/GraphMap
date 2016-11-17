import random
import serializer
import imagetree
import constants


class TreeGenerator:
    @staticmethod
    def create_random_tree(name, height, pixel, variance):
        """

        :rtype: imagetree.ImageTree
        """
        child_pixel = TreeGenerator.create_similar_pixel(pixel, variance)
        if height > 1:
            children = [TreeGenerator.create_random_tree(name=name + str(i), height=height - 1, pixel=child_pixel,
                                                         variance=variance) for i in range(constants.children_per_node)]
        else:
            children = []
        return imagetree.ImageTree(children=children, name=name, input_image=child_pixel, children_links=[],
                                   serializer=serializer.Serializer(), filename='create_random_tree')

    @staticmethod
    def create_similar_pixel(pixel, variance, type='uniform'):
        if type == 'standard':
            return tuple((random.choice([0, 255]) for i in pixel))
        return tuple(((random.randint(-variance, variance) + i )% 256) for i in pixel)

    @staticmethod
    def create_random_tree_var_child(name, height, pixel, variance):
        child_pixel = TreeGenerator.create_similar_pixel(pixel, variance, type='uniform')
        have_child = random.randint(0, constants.children_per_node - 1) > 0
        if height > 1 and have_child:
            children = [
                TreeGenerator.create_random_tree_var_child(name=name + str(i), height=height - 1, pixel=child_pixel,
                                                           variance=variance) for i in
                range(constants.children_per_node)]
        else:
            children = []
        return imagetree.ImageTree(children=children, name=name, input_image=child_pixel, children_links=[i.name for i in children],
                                   serializer=serializer.Serializer(), filename='create_random_tree_var_child')

    @staticmethod
    def create_random_infinite(name, height, pixel, variance):
        # Todo modify this
        raise NotImplementedError()
        child_pixel = TreeGenerator.create_similar_pixel(pixel, variance, type='uniform')
        have_child = random.randint(0, constants.children_per_node - 1) > 0
        if height > 1 and have_child:
            children = [
                TreeGenerator.create_random_tree_var_child(name=name + str(i), height=height - 1, pixel=child_pixel,
                                                           variance=variance) for i in
                range(constants.children_per_node)]
        else:
            children = []
        return imagetree.ImageTree(children=children, name=name, input_image=child_pixel, children_links=[],
                                   serializer=serializer.Serializer(), filename='create_random_infinite')


if __name__ == '__main__':
    TreeGenerator.create_random_tree_var_child('main', height=10, pixel=(0, 0, 0), variance=2).show(resolution=1024)
