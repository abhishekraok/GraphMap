import unittest
from .context import graphmap

from graphmap import constants
from graphmap import graph_map
from graphmap import imagetree
from graphmap import imagevalue
from graphmap import memory_persistence
from graphmap import result_file
from graphmap import serializer
from graphmap import utilities
from graphmap.constants import seattle_skyline_url
from graphmap.graph_helpers import NodeLink

wiki_image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Wikimedia_Foundation_RGB_logo_with_text.svg/240px-Wikimedia_Foundation_RGB_logo_with_text.svg.png'
wiki_pil_image = utilities.reshape_proper_pil_image(imagevalue.fetch_image_from_url(wiki_image_url))
seattle_skyline_pil_image = utilities.reshape_proper_pil_image(imagevalue.fetch_image_from_url(seattle_skyline_url))


class CreateNodeTests(unittest.TestCase):
    def test_valid_jpg_link(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        node_name = NodeLink('tvjl', None)
        self.assertFalse(gm.node_exists(node_name))
        create_result = gm.create_node(root_node_link=node_name, image_value_link=wiki_image_url)
        self.assertEqual(create_result.code, result_file.SUCCESS_CODE)
        self.assertTrue(gm.node_exists(node_name))
        self.assertEqual(create_result.value, node_name)

    def test_valid_node_link_same_image(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('tvnl_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('tvnl_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=wiki_image_url)
        first_image_result = gm.get_image_at_quad_key(first_node_name, resolution=256, quad_key='')
        second_image_result = gm.get_image_at_quad_key(second_node_name, resolution=256, quad_key='')
        self.assertEqual(first_image_result.code, result_file.SUCCESS_CODE)
        self.assertEqual(second_image_result.code, result_file.SUCCESS_CODE)
        self.assertTrue(utilities.pil_images_equal(first_image_result.value, second_image_result.value))

    def test_invalid_already_exists(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('tiae')
        create_result = gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        self.assertEqual(create_result.code, result_file.SUCCESS_CODE)
        repeat_create_result = gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        self.assertNotEqual(repeat_create_result.code, result_file.SUCCESS_CODE)
        self.assertEqual(repeat_create_result.code, result_file.NAME_ALREADY_EXISTS)

    def test_invalid_wrong_children_count(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        children_names = ('a', 'b', 'c', 'd')
        good_result = gm.create_node(root_node_link=NodeLink('tiwccg'), children_links=children_names)
        self.assertEqual(good_result.code, result_file.SUCCESS_CODE)
        wrong_children_names = ('e', 'f', 'g')
        bad_result = gm.create_node(root_node_link=NodeLink('tiwccb'), children_links=wrong_children_names)
        self.assertNotEqual(bad_result.code, result_file.SUCCESS_CODE)
        self.assertEqual(bad_result.code, result_file.WRONG_CHILDREN_COUNT)


class ConnectChildTests(unittest.TestCase):
    def test_valid_simple(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('anttvs')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('tvnl_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '333'
        new_root_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                           child_node_link=second_node_name)
        new_root = new_root_result.value
        self.assertTrue(gm.node_exists(new_root), new_root_result.message)
        self.assertEqual(second_node_name, gm.get_child_name(new_root, quad_key=quad_key).value)

    @unittest.skip("Currently blank quad key is not supported")
    def test_valid_quad_key_blank(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('anttvb_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('anttvb_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = ''
        first_image = gm.get_image_at_quad_key(first_node_name, 256, quad_key=quad_key)
        self.assertTrue(utilities.pil_images_equal(first_image.value, wiki_pil_image))
        new_root_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                           child_node_link=second_node_name)
        self.assertTrue(new_root_result.is_success())
        new_root = new_root_result.value
        self.assertEqual(second_node_name, gm.get_child_name(new_root, quad_key=quad_key))
        self.assertEqual(second_node_name, new_root)
        second_image_result = gm.get_image_at_quad_key(new_root, 256, quad_key=quad_key)
        self.assertTrue(second_image_result.is_success())
        self.assertTrue(utilities.pil_images_equal(second_image_result.value, seattle_skyline_pil_image))

    @unittest.skip("will make quad key a class and check there")
    def test_invalid_quad_key(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('ant_iqk_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('ant_iqk_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '512'
        new_root_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                           child_node_link=second_node_name)
        self.assertFalse(new_root_result.is_success())

    def test_valid_new_root_name(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('ant_vnr_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('ant_vnr_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '123'
        input_new_root = NodeLink('ant_vnr_nr')
        new_root_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                           child_node_link=second_node_name,
                                           new_root_name=input_new_root)
        self.assertTrue(new_root_result.is_success())
        self.assertEqual(new_root_result.value, input_new_root)

    def test_invalid_add_non_existent_insert_node_name(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('ant_nen_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('ant_nen_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '512'
        new_root_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                           child_node_link=NodeLink('dalja'))
        self.assertFalse(new_root_result.is_success())
        self.assertEqual(result_file.NODE_LINK_NOT_FOUND_ERROR_CODE, new_root_result.code)

    def test_invalid_add_non_existent_root_name(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('ant_ner_first')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('ant_ner_second')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '512'
        new_root_result = gm.connect_child(root_node_link=NodeLink('galall'), quad_key=quad_key,
                                           child_node_link=second_node_name)
        self.assertFalse(new_root_result.is_success())
        self.assertEqual(result_file.NODE_LINK_NOT_FOUND_ERROR_CODE, new_root_result.code)


class NodeExistsTest(unittest.TestCase):
    def test_exists_true(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('ne0')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        self.assertTrue(gm.node_exists(first_node_name))

    def test_exists_false(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        gm.create_node(root_node_link=NodeLink('lajaflaga'), image_value_link=wiki_image_url)
        self.assertFalse(gm.node_exists('agaljvalbla'))


class GetChildName(unittest.TestCase):
    def test_valid_quad_key(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_link = NodeLink('gcn_vq')
        gm.create_node(root_node_link=first_node_link, image_value_link=wiki_image_url)
        second_node_link = NodeLink('gcn_vq2')
        gm.create_node(root_node_link=second_node_link, image_value_link=seattle_skyline_url)
        quad_key = '01333'
        third_node_link_result = gm.connect_child(root_node_link=first_node_link, quad_key=quad_key,
                                                  child_node_link=second_node_link)
        self.assertTrue(third_node_link_result.is_success())
        child_name_result = gm.get_child_name(root_node_link=third_node_link_result.value, quad_key=quad_key)
        self.assertTrue(child_name_result.is_success())
        self.assertEqual(second_node_link, child_name_result.value)

    def test_invalid_child_not_exists(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('gcn_cne')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('gcn_cne')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        add_result = gm.connect_child(root_node_link=first_node_name, quad_key='01312',
                                      child_node_link=second_node_name)
        self.assertTrue(add_result.is_success())
        child_name_result = gm.get_child_name(root_node_link=first_node_name, quad_key='111')
        self.assertFalse(child_name_result.is_success())
        self.assertEqual(result_file.NODE_LINK_NOT_FOUND_ERROR_CODE, child_name_result.code)

    def test_invalid_root_does_not_exists(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('gcn_ner')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        second_node_name = NodeLink('gcn_ner2')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        quad_key = '01333'
        add_result = gm.connect_child(root_node_link=first_node_name, quad_key=quad_key,
                                      child_node_link=second_node_name)
        self.assertTrue(add_result.is_success())
        child_name_result = gm.get_child_name(root_node_link=NodeLink('invalid'), quad_key=quad_key)
        self.assertFalse(child_name_result.is_success())
        self.assertEqual(result_file.NODE_LINK_NOT_FOUND_ERROR_CODE, child_name_result.code)


class GetImageAtQuadKey(unittest.TestCase):
    def test_valid_image_match_resolution(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('tvimr')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        test_resolution = 256
        pil_image_result = gm.get_image_at_quad_key(first_node_name, resolution=test_resolution, quad_key='')
        self.assertTrue(pil_image_result.is_success())
        pil_image = pil_image_result.value
        self.assertEqual(pil_image.size, (test_resolution, test_resolution))

    # def test_invalid_root_does_not_exist(self):
    #     raise NotImplementedError
    #
    # def test_invalid_child_does_not_exist_at_quad_key(self):
    #     raise NotImplementedError

    def test_no_change_after_adding_node(self):
        gm = graph_map.GraphMap(memory_persistence.MemoryPersistence())
        first_node_name = NodeLink('nocan0')
        gm.create_node(root_node_link=first_node_name, image_value_link=wiki_image_url)
        test_resolution = 256
        first_image_before_add_result = gm.get_image_at_quad_key(first_node_name, resolution=test_resolution,
                                                                 quad_key='')
        self.assertTrue(first_image_before_add_result.is_success())
        second_node_name = NodeLink('nocan1')
        gm.create_node(root_node_link=second_node_name, image_value_link=seattle_skyline_url)
        first_image_after_add_result = gm.get_image_at_quad_key(first_node_name, resolution=test_resolution,
                                                                quad_key='')
        self.assertTrue(first_image_after_add_result.is_success())
        self.assertTrue(utilities.pil_images_equal(first_image_before_add_result.value,
                                                   first_image_after_add_result.value))

    def test_consistent_image_as_you_zoom(self):
        gm = graph_map.GraphMap(serializer.Serializer())
        fruits_node_link = NodeLink(constants.FRUITS_LINK)
        lowest_quad_keys = ['333133', '312312', '131231']
        for lowest_quad_key in lowest_quad_keys:
            expected_same_images = []
            for i in range(len(lowest_quad_key) + 1):
                node_quad_key = lowest_quad_key[:i]
                resolution = 2 ** (len(lowest_quad_key) - i) * 32
                node_pil_image_result = gm.get_image_at_quad_key(root_node_link=fruits_node_link, resolution=resolution,
                                                                 quad_key=node_quad_key)
                self.assertTrue(node_pil_image_result.is_success())
                node_pil_image = node_pil_image_result.value
                image_quad_key = lowest_quad_key[i:]
                expected_same_image = imagetree.pil_image_at_quad_key(node_pil_image, quad_key=image_quad_key)
                expected_same_images.append(expected_same_image)
            for expected_same_image in expected_same_images[1:]:
                self.assertTrue(utilities.pil_images_equal(expected_same_image, expected_same_images[0]))

# class IntegrationTests(unittest.TestCase):
#     def test_build_sample_and_compare(self):
#         raise NotImplementedError
#
#     def test_build_another_sample_and_compare(self):
#         raise NotImplementedError
