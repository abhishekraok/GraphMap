import copy
import os
import time
import unittest

import alpha_conversion
import constants
import imagetree
import imagetree_core.azure_image_tree
import imagetree_core.utilities
import imagevalue
import numpy as np
import serializer
import standard_nodes
import standard_pixel
import tile_disk_cache
import tileserver
import tree_creator
import tree_operator
import treegenerator
import utilities
from PIL import Image
from pixel_approximator import PixelApproximator, PixelApproximationMethod
from serialization import protbuf_serializer


class TestImageTree(unittest.TestCase):
    children_names = ['son', 'daughter', 'son2', 'daughter2']
    father_pixel = (77, 67, 77)
    son_pixel = (20, 52, 200)
    father_filename = 'test.tsv.gz'

    @staticmethod
    def create_one_high_tree(filename=father_filename):
        sample_serializer = serializer.Serializer()
        daughter_node = imagetree.ImageTree(name='daughter', children_links=[], input_image=(),
                                            serializer=sample_serializer, children=[], filename=filename)
        daughter_node2 = imagetree.ImageTree(name='daughter2', children_links=[], input_image=(10, 50, 100),
                                             serializer=sample_serializer, children=[], filename=filename)
        son_node = imagetree.ImageTree(name='son', children_links=[], input_image=TestImageTree.son_pixel, children=[],
                                       filename=filename, serializer=sample_serializer)
        son_node2 = imagetree.ImageTree(name='son2', children_links=[], input_image=(20, 52, 200), children=[],
                                        filename=filename, serializer=sample_serializer)
        father_node = imagetree.ImageTree(name='father', children_links=copy.deepcopy(TestImageTree.children_names),
                                          input_image=TestImageTree.father_pixel,
                                          children=[son_node, daughter_node, son_node2, daughter_node2],
                                          serializer=sample_serializer, filename=filename)
        return father_node

    def test_simple_approximator(self):
        pixels_list = [(0, 0, 10), (1, 10, 11), (2, 20, 12), (3, 30, 13)]
        approx = PixelApproximator.approximate(four_pixels_list=pixels_list, method=PixelApproximationMethod.simple_avg)
        expected = (1, 15, 11)
        self.assertEqual(expected, approx)

    def test_count_nodes(self):
        tree = TestImageTree.create_one_high_tree()
        self.assertEqual(5, tree.count_nodes())

    def test_height(self):
        tree = TestImageTree.create_one_high_tree()
        self.assertEqual(2, tree.height(max_height=77))

    def test_var_tree(self):
        tree = treegenerator.TreeGenerator.create_random_tree_var_child('test', height=6, pixel=(0, 0, 0), variance=2)
        self.assertEqual('test', tree.name)

    def test_get_descendant(self):
        height = 4
        main_tree = treegenerator.TreeGenerator.create_random_tree('test', height=height, pixel=(0, 0, 0), variance=2)
        quad_key = '312'
        sub_tree = main_tree.get_descendant(quad_key)
        self.assertEqual(height - len(quad_key), sub_tree.height(max_height=77))
        self.assertEqual('test312', sub_tree.name)

    def test_xyz_to_quadkey(self):
        self.assertEqual('0', utilities.xyz_to_quadkey(0, 0, 1))
        self.assertEqual('33', utilities.xyz_to_quadkey(3, 3, 2))
        self.assertEqual('330', utilities.xyz_to_quadkey(6, 6, 3))

    def test_quadkey_to_xyz(self):
        self.assertEqual((0, 0, 1), utilities.quadkey_to_xyz('0'))
        self.assertEqual((3, 3, 2), utilities.quadkey_to_xyz('33'))
        self.assertEqual((6, 6, 3), utilities.quadkey_to_xyz('330'))

    def test_get_path_zyx(self):
        self.assertEqual('5/6/7', utilities.get_path_zyx(7, 6, 5))

    def test_load_root_name(self):
        filename = 'test_load_root.tsv.gz'
        tree = TestImageTree.create_one_high_tree(filename=filename)
        serializer.save_tree(tree)
        loaded_tree = serializer.load_link_new_serializer(
            utilities.format_node_address(filename=filename, node_name='son'))
        self.assertEqual('son', loaded_tree.name)
        self.assertEqual(1, loaded_tree.height(max_height=7))
        os.remove(filename)

    def test_save_load_infinite(self):
        tree = TestImageTree.create_one_high_tree()
        tree.get_children()[0] = tree
        filename = 'test_infinite.tsv.gz'
        tree.set_filename(filename)
        serializer.save_tree(tree)
        new_tree = serializer.load_link_new_serializer(
            utilities.format_node_address(filename=filename, node_name='father'))
        self.assertEqual('father', new_tree.name)
        os.remove(filename)

    def test_multiple_file_link_load(self):
        tree = TestImageTree.create_one_high_tree()
        second_filename = 'second.tsv.gz'
        tree._children_links[2] = utilities.format_node_address(filename=second_filename,
                                                                node_name=tree.get_children()[2].name)
        tree.get_children()[2].filename = second_filename
        serializer.save_tree(tree)
        self.assertTrue(os.path.isfile(second_filename))
        link = tree.get_link()
        loaded_tree = serializer.load_link_new_serializer(link=link)
        self.assertEqual(loaded_tree, tree)
        os.remove(second_filename)

    def test_get_child_leaf(self):
        leaf = imagetree.ImageTree(children=[], name='test_leaf', input_image=(), children_links=[],
                                   serializer=serializer.Serializer(), filename='')
        self.assertTrue(leaf.is_leaf())
        self.assertEqual(1, leaf.height(max_height=999))
        self.assertEqual(1, leaf.count_nodes())

    def test_resolver(self):
        sample_links = ['haha', utilities.format_node_address(filename='somefile', node_name='second_node'),
                        utilities.format_node_address(filename='http://a.com/b', node_name='d')]
        resolved = [utilities.resolve_link(i) for i in sample_links]
        self.assertEqual(('haha', None), resolved[0])
        self.assertEqual(('second_node', 'somefile'), resolved[1])
        self.assertEqual(('d', 'http://a.com/b'), resolved[2])

    def test_save_load_compact(self):
        filename = 'test_compact.tsv.gzip'
        tree = TestImageTree.create_one_high_tree(filename)
        serializer.save_tree(tree)
        loaded_tree = serializer.load_link_new_serializer(utilities.format_node_address(filename, node_name=tree.name))
        self.assertEqual(tree, loaded_tree)
        os.remove(filename)

    def test_save_load_different_format(self):
        filename_extensions = ['.tsv', '.tsv.gz', '.itpb', '.itpb.gz']
        base_filename = 'sldf'
        for extension in filename_extensions:
            filename = base_filename + extension
            tree = TestImageTree.create_one_high_tree(filename)
            serializer.save_tree(tree)
            loaded_tree = serializer.load_link_new_serializer(
                utilities.format_node_address(filename, node_name=tree.name))
            self.assertEqual(tree.select(lambda x: x.name), loaded_tree.select(lambda x: x.name))
            os.remove(filename)

    def test_pixel_serialize_deserialize(self):
        sample_pixel = standard_pixel.Pixel((3, 0, 5))
        serialize_pixel = sample_pixel.serialize()
        self.assertEqual('3\t0\t5\t', serialize_pixel)
        self.assertEqual(sample_pixel, standard_pixel.deserialize(serialize_pixel))
        empty = standard_pixel.Pixel(())
        empty_serialize = empty.serialize()
        self.assertEqual('\t\t\t', empty_serialize)
        self.assertEqual(empty, standard_pixel.deserialize(empty_serialize))

    def test_equal(self):
        tree = TestImageTree.create_one_high_tree()
        same_value_tree = TestImageTree.create_one_high_tree()
        same_value_tree._children_links = copy.deepcopy(same_value_tree._children_links)
        self.assertTrue(tree, same_value_tree)
        same_value_tree._children_links[0] = 'haha'
        self.assertNotEqual(tree, same_value_tree)

    @unittest.skip("skip failing")
    def test_save_load_random(self):
        tree = treegenerator.TreeGenerator.create_random_tree('ra', 4, pixel=(0, 0, 0), variance=1)
        filename = 'rat.tsv.gz'
        tree.set_filename(filename)
        root_link = utilities.format_node_address(filename, node=tree.name)
        serializer.save_tree(tree)
        another_tree = serializer.load_link_new_serializer(link=root_link)
        self.assertEqual(tree, another_tree)
        os.remove(filename)

    def test_pixel_approximately_equal(self):
        test_pixel = standard_pixel.Pixel((55, 66, 77))
        similar = standard_pixel.Pixel((51, 68, 73))
        different = standard_pixel.Pixel((55, 66, 177))
        self.assertTrue(test_pixel.approximately_equal(similar))
        self.assertTrue(test_pixel.approximately_equal(test_pixel))
        self.assertFalse(test_pixel.approximately_equal(different))
        self.assertFalse(similar.approximately_equal(different))

    def test_blank_image_compress(self):
        blank_image = Image.new('RGB', size=(128, 128), color='blue')
        blank_tree = imagetree.ImageTree.from_image_array(array=np.array(blank_image), filename='test_compress.tsv.gz',
                                                          name='test_compress')
        original_count = blank_tree.count_nodes()
        blank_tree.compress()
        new_count = blank_tree.count_nodes()
        self.assertLess(new_count, original_count)

    @unittest.skip('obsolete')
    def test_save_compress(self):
        pic_file = '../data/beach.jpg'
        tree_filename = pic_file[:-4] + '.tsv.gz'
        self.assertTrue(os.path.isfile(pic_file), msg='Need any png file named ../data/beach.jpg file to run this test')
        tree = imagetree_core.utilities.from_imagefile(imagefilename=pic_file, name='test_save_compress',
                                                       tree_filename=tree_filename)
        serializer.compress_and_save(tree)
        self.assertTrue(os.path.isfile(tree_filename))
        os.remove(tree_filename)

    @unittest.skip('Requires Azure')
    def test_upload_to_azure(self):
        pic_file = '../data/beach.jpg'
        imagetree_core.azure_image_tree.upload_to_url(
            file_to_store=pic_file, url='https://artmapstore.blob.core.windows.net/firstnodes/test2/beach2.jpg')

    def test_insert_tree(self):
        first_tree = TestImageTree.create_one_high_tree()
        another_tree = imagetree.ImageTree(children=[], name='added', input_image=(), children_links=[],
                                           serializer=first_tree.serializer, filename='another.tsv.gz')
        quadkey_insert = '3333'
        first_tree.insert(another_tree, quadkey_insert)
        self.assertEqual(another_tree.name, first_tree.get_descendant(quadkey_insert).name)

    def test_stretch_keep_aspect(self):
        sample_pil = Image.new("RGB", size=(333, 222), color='white')
        max_resolution = 600
        resized_array = utilities.stretch_keep_aspect(sample_pil, max_resolution=max_resolution)
        self.assertEqual((600, 600, 3), resized_array.shape)

    def test_operator_separator(self):
        sample_name = 'rot90#benki@pinka.tsv'
        node_name, operation = tree_operator.extract_first_operator(sample_name)
        self.assertEqual(tree_operator.Operation.Rotate90, operation)
        self.assertEqual('benki@pinka.tsv', node_name)

    def test_rotate_90(self):
        sample_tree = TestImageTree.create_one_high_tree()
        self.assertEqual('son@test.tsv.gz', sample_tree.children_links[0])
        self.assertEqual('son', sample_tree.get_children()[0].name)
        operated_tree = tree_operator.operate_tree(sample_tree, tree_operator.Operation.Rotate90)
        self.assertEqual('son2@test.tsv.gz', operated_tree.children_links[0])
        self.assertEqual('son2', operated_tree.get_children()[0].name)
        self.assertEqual('son@test.tsv.gz', sample_tree.children_links[0])
        self.assertEqual('son', sample_tree.get_children()[0].name)
        self.assertEqual('rot90#father', operated_tree.name)

    def test_extract_nodename_and_operators_list(self):
        sample_name = 'rot90#rot90#rot180#jiji'
        nodename, operators_list = tree_operator.get_nodename_and_operators_list(sample_name)
        self.assertEqual('jiji', nodename)
        self.assertEqual(
            [tree_operator.Operation.Rotate90, tree_operator.Operation.Rotate90, tree_operator.Operation.Rotate180],
            operators_list)
        sample_2 = 'gaga'
        nodename2, operators_list2 = tree_operator.get_nodename_and_operators_list(sample_2)
        self.assertEqual('gaga', nodename2)
        self.assertEqual([], operators_list2)

    def test_rotate_90_180(self):
        sample_tree = TestImageTree.create_one_high_tree()
        operation_list = [tree_operator.Operation.Rotate90, tree_operator.Operation.Rotate90,
                          tree_operator.Operation.Rotate180]
        operated_tree = tree_operator.apply_operators(sample_tree, operation_list)
        self.assertEqual(operated_tree, sample_tree)

    def test_image_tree_args_to_path(self):
        sample_tree = TestImageTree.create_one_high_tree()
        cache_dir = 'test_args_cache_imagtree'
        cacher = tile_disk_cache.TileCache(cache_dir, size=10)
        save_path = cacher.image_tree_args_to_path(sample_tree, resolution=512)
        self.assertTrue(save_path.startswith(
            os.path.join(cache_dir, '512', tile_disk_cache.to_valid_filename(sample_tree.filename), sample_tree.name)))


class ImageTreeCacheTests(unittest.TestCase):
    def test_imagetree_with_cache_saves_file(self):
        test_tree = TestImageTree.create_one_high_tree()
        cache_dir = 'tiwc'
        cache_size = 8
        resolution = 64
        image_cache = tile_disk_cache.TileCache(cache_dir=cache_dir, size=cache_size)
        test_tree.serializer.image_cache = image_cache
        image_cache.cache_burst()
        self.assertEqual(image_cache.count_files_in_disk(), 0)
        self.assertFalse(image_cache.has_image(test_tree, resolution))
        pil_im = test_tree.get_pil_image(resolution=resolution)
        self.assertTrue(image_cache.has_image(test_tree, resolution))
        self.assertEqual(image_cache.count_files_in_disk(), 1)
        first_child_tree = test_tree.get_children()[0]
        self.assertFalse(image_cache.has_image(first_child_tree, resolution))
        pil_im2 = first_child_tree.get_pil_image(resolution=64)
        self.assertTrue(image_cache.has_image(first_child_tree, resolution))
        self.assertEqual(image_cache.count_files_in_disk(), 2)
        self.assertEqual(image_cache.cache_count, 2)
        image_cache.cache_burst()
        self.assertEqual(image_cache.count_files_in_disk(), 0)
        self.assertEqual(image_cache.cache_count, 0)

    # Requires internet
    def test_image_cache_populator(self):
        cache_dir = 'ticp'
        cache_size = 12
        image_cache = tile_disk_cache.TileCache(cache_dir=cache_dir, size=cache_size)
        multi_tile_server = tileserver.MultiRootTileServer(image_cache=image_cache)
        image_cache.cache_burst()
        self.assertEqual(image_cache.count_files_in_disk(), 0)
        root_link = constants.RED_GALLERY_LINK
        result = multi_tile_server.populate_cache(root_link=root_link, cache_limit=12)
        self.assertEqual(image_cache.count_files_in_disk(), cache_size)
        image_cache.cache_burst()


class ProtobufSerializationTest(unittest.TestCase):
    def test_visit(self):
        sample_tree = TestImageTree.create_one_high_tree()
        list_of_nodes = []

        def add_to_list(image_tree_node):
            if image_tree_node.name in list_of_nodes:
                return True
            list_of_nodes.append(image_tree_node.name)
            return False

        sample_tree.visit(add_to_list)
        self.assertEqual(5, len(list_of_nodes))

    def test_converts_list_of_imagetree_nodes_into_protbuf_forest(self):
        sample_tree = TestImageTree.create_one_high_tree()
        filename_to_node_map = sample_tree.create_node_dictionary()
        list_of_nodes = list(filename_to_node_map[sample_tree.filename].itervalues())

        protobuf_forest = protbuf_serializer.serialize_list_of_nodes_to_proto_forest(list_of_nodes)
        self.assertEqual(5, len(protobuf_forest.forest))
        self.assertIn(sample_tree.name, (i.name for i in protobuf_forest.forest))
        self.assertIn(sample_tree.get_children()[0].name, (i.name for i in protobuf_forest.forest))

    def test_serialize_deserialize_protobuf(self):
        sample_tree = TestImageTree.create_one_high_tree()
        serialized_string = protbuf_serializer.serialize_filename(sample_tree)
        deserialized_map = protbuf_serializer.deserialize_to_name_to_imagetree_node_map(serialized_string, '', None)
        self.assertEqual(sample_tree.count_nodes(), len(deserialized_map))
        self.assertEqual(sorted(sample_tree.select(lambda k: k.name)), sorted(deserialized_map.iterkeys()))

    def test_select(self):
        sample_tree = TestImageTree.create_one_high_tree()
        name_list = sample_tree.select(lambda x: x.name)
        self.assertEqual(sorted(name_list), sorted(['father'] + TestImageTree.children_names))

    def test_not_found_link(self):
        not_found_tree = serializer.load_link_new_serializer('bababaaskjfalj')
        self.assertEqual(not_found_tree.name, standard_nodes.not_found_node(None, None).name)


@unittest.skip('obsolete')
class InteGrationTest(unittest.TestCase):
    def test_imagetree_from_url(self):
        url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c4/Wikimedia_Foundation_RGB_logo_with_text.svg/240px-Wikimedia_Foundation_RGB_logo_with_text.svg.png'
        filename = 'wikimedia.tsv.gz'
        created_tree = utilities.create_tree_from_url(url=url, node_name='wikimedia', tree_filename=filename)
        self.assertGreater(created_tree.count_nodes(), 50)


class ImageTests(unittest.TestCase):
    wiki_image_url = 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Wikipedia%27s_W_%28Linux_Libertine%29.svg/128px-Wikipedia%27s_W_%28Linux_Libertine%29.svg.png'

    def test_jpg_image_url(self):
        jpg_image_from_url = imagevalue.JpgWebImage(ImageTests.wiki_image_url)
        rendered = jpg_image_from_url.get_pil_image(128)
        self.assertEqual(rendered.size, (128, 128))

    def test_standard_pixel_renders(self):
        pixel = standard_pixel.Pixel(input_pixel=(128, 129, 128))
        rendered = pixel.get_pil_image(128)
        self.assertEqual(rendered.size, (128, 128))

    def test_picture_in_picture_render(self):
        jpg_web_image = imagevalue.JpgWebImage(ImageTests.wiki_image_url)
        ser = serializer.Serializer()
        child_tree = imagetree.ImageTree(name='child_w', children_links=[], filename='', serializer=ser,
                                         input_image=jpg_web_image)

        children = [child_tree,
                    imagetree.empty_image_tree('1', ser, ''),
                    imagetree.empty_image_tree('2', ser, ''),
                    imagetree.empty_image_tree('3', ser, '')]
        top_tree = imagetree.ImageTree(name='father_w', children_links=[], filename='', serializer=ser,
                                       input_image=jpg_web_image, children=children)
        rendered = top_tree.get_pil_image(128)
        self.assertEqual(rendered.size, (128, 128))

    def create_image_url_tree(self):
        first_serialized_string = 'first\t\t\t\tchild0\tchild1\tchild2\tchild3\t' + ImageTests.wiki_image_url + '\n'
        child0_serialized_string = 'child0\t\t\t\t\t\t\t\t' + ImageTests.wiki_image_url + '\n'
        child1_serialized_string = 'child1\t\t\t\t\t\t\t\t' + '\n'
        child2_serialized_string = 'child2\t\t\t\t\t\t\t\t' + '\n'
        child3_serialized_string = 'child3\t\t\t\t\t\t\t\t' + '\n'
        full_serialized_string = first_serialized_string + child0_serialized_string + child1_serialized_string \
                                 + child2_serialized_string + child3_serialized_string
        filename = 'deserialize_image_url.tsv'
        test_serializer = serializer.Serializer()
        deserialized_tree = test_serializer.load_from_string(node_name='first', filename=filename,
                                                             serialized_string=full_serialized_string)
        return deserialized_tree

    def test_deserialize_tsv_image_url(self):
        deserialized_tree = self.create_image_url_tree()
        rendered = deserialized_tree.get_pil_image(128)
        self.assertEqual(rendered.size, (128, 128))
        rendered_array = np.array(rendered)
        self.assertNotEqual(np.sum(rendered_array), 0)

    def test_pil_image_at_quadkey(self):
        deserialized_tree = self.create_image_url_tree()
        rendered = deserialized_tree.get_pil_image_at_quadkey(64, '3')
        self.assertEqual(rendered.size, (64, 64))
        rendered_array = np.array(rendered)
        image_from_url = imagevalue.fetch_image_from_url(ImageTests.wiki_image_url)
        image_from_url = alpha_conversion.alpha_to_color(image_from_url)
        expected_array = np.array(image_from_url, dtype=np.uint8)[64:, 64:, :3]
        self.assertLess(utilities.mse(rendered_array, expected_array), 0.1)

    def test_fruits(self):
        fruit_filename = 'fruits.tsv'
        self.assertTrue(os.path.isfile(fruit_filename))
        link = utilities.format_node_address(node_name='fruits', filename=fruit_filename)
        fruit_tree = serializer.load_link_new_serializer(link=link)
        rendered = fruit_tree.get_np_array(128)
        self.assertEqual(rendered.shape[0], 128)

    def test_image_at_quadkey_resolution(self):
        fruits_link = constants.FRUITS_LINK
        fruit_tree = serializer.load_link_new_serializer(fruits_link)
        test_resolution = 256
        for quad_key in ['', '3', '33', '33313']:
            pil_image = fruit_tree.get_pil_image_at_quadkey(quad_key=quad_key, resolution=test_resolution)
            self.assertEqual((test_resolution, test_resolution), pil_image.size)

    def test_image_at_quadkey_child_same(self):
        fruits_link = constants.FRUITS_LINK
        fruit_tree = serializer.load_link_new_serializer(fruits_link)
        test_resolution = 256
        own_image = fruit_tree.get_np_array(test_resolution)
        child_pil_image = fruit_tree.get_pil_image_at_quadkey(resolution=test_resolution, quad_key='33')
        self.assertLess(utilities.mse(own_image, np.array(child_pil_image)), 0.1)

    def test_descendant_consistent_image_render_at_quadkey(self):
        fruits_link = constants.FRUITS_LINK
        fruit_tree = serializer.load_link_new_serializer(fruits_link)
        lowest_quad_keys = ['333133', '312312', '131231']
        for lowest_quad_key in lowest_quad_keys:
            start_resolution = 64
            expected_same_images = []
            for i in range(len(lowest_quad_key) + 1):
                node_quad_key = lowest_quad_key[:i]
                resolution = 2 ** (len(lowest_quad_key) - i) * 32
                node_image = fruit_tree.get_np_array_at_quad_key(quad_key=node_quad_key, resolution=resolution)
                image_quad_key = lowest_quad_key[i:]
                expected_same_image = imagetree.image_at_quad_key(node_image, resolution=start_resolution,
                                                                  quad_key=image_quad_key)
                expected_same_images.append(expected_same_image)
            for expected_same_image in expected_same_images:
                self.assertLess(utilities.mse(expected_same_image, expected_same_images[0]), 0.1)

    def test_descendant_consistent_image_pil_image(self):
        fruits_link = constants.FRUITS_LINK
        fruit_tree = serializer.load_link_new_serializer(fruits_link)
        lowest_quad_keys = ['333133', '312312', '131231']
        for lowest_quad_key in lowest_quad_keys:
            start_resolution = 64
            expected_same_images = []
            for i in range(len(lowest_quad_key) + 1):
                node_quad_key = lowest_quad_key[:i]
                resolution = 2 ** (len(lowest_quad_key) - i) * 32
                node_pil_image = fruit_tree.get_pil_image_at_quadkey(quad_key=node_quad_key, resolution=resolution)
                node_image = np.array(node_pil_image)
                image_quad_key = lowest_quad_key[i:]
                expected_same_image = imagetree.image_at_quad_key(node_image, resolution=start_resolution,
                                                                  quad_key=image_quad_key)
                expected_same_images.append(expected_same_image)
            for expected_same_image in expected_same_images:
                self.assertLess(utilities.mse(expected_same_image, expected_same_images[0]), 0.1)

    def test_sparse_link(self):
        node_link = 'start0010@https://artmapstore.blob.core.windows.net/firstnodes/user/abhishek/start.ver_10.tsv'
        sparse_tree = serializer.load_link_new_serializer(node_link)
        pil_image = sparse_tree.get_pil_image_at_quadkey(resolution=512, quad_key='1')
        self.assertEqual((512, 512), pil_image.size)


class CreationTests(unittest.TestCase):
    def test_insert_tree(self):
        ser = serializer.Serializer()
        first_tree = serializer.create_tree_from_jpg_url(ImageTests.wiki_image_url, name='test_insert',
                                                         filename='test_insert',
                                                         serializer=ser)
        second_tree = serializer.create_tree_from_jpg_url(ImageTests.wiki_image_url, name='child',
                                                          filename='test_insert',
                                                          serializer=ser)
        test_quadkey = '012'
        first_tree.insert(another_tree=second_tree, quad_key=test_quadkey)
        rendered = first_tree.get_np_array(128)
        self.assertEqual(rendered.shape[0], 128)

    def test_create_new_tree_from_old_jpg(self):
        first_tree = TestImageTree.create_one_high_tree()
        quad_key = '01'
        new_link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG/273px-Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG'
        new_tree = tree_creator.create_new_from_old_insert_jpg(old_tree=first_tree, link_to_insert=new_link,
                                                               quad_key=quad_key,
                                                               new_tree_name='hosa',
                                                               filename='newctfo.tsv').value
        self.assertEqual('hosa', new_tree.name)
        self.assertEqual(new_link, new_tree.get_descendant(quad_key)._image_value.url)
        self.assertEqual(TestImageTree.father_pixel, tuple(new_tree.get_np_array(1).flatten()))

    def test_create_new_tree_from_old_jpg_save(self):
        first_tree = TestImageTree.create_one_high_tree()
        quad_key = '012'
        new_link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG/273px-Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG'
        filename = 'hosafile.tsv'
        new_tree = tree_creator.create_new_from_old_insert_jpg(old_tree=first_tree, link_to_insert=new_link,
                                                               quad_key=quad_key,
                                                               new_tree_name='hosa',
                                                               filename=filename).value
        serializer.save_tree_only_filename(new_tree, filename)
        self.assertTrue(os.path.isfile(filename))
        os.remove(filename)

    def test_create_new_tree_from_old_jpg_save_load(self):
        if os.path.isfile(TestImageTree.father_filename):
            os.remove(TestImageTree.father_filename)
        first_tree = TestImageTree.create_one_high_tree()
        serializer.save_tree(first_tree)
        quad_key = '021'
        new_link = 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG/273px-Maquette_EDM_salon_du_Bourget_2013_DSC_0192.JPG'
        filename = 'saveload_jpg.tsv'
        new_tree = tree_creator.create_new_from_old_insert_jpg(old_tree=first_tree, link_to_insert=new_link,
                                                               quad_key=quad_key,
                                                               new_tree_name='slj',
                                                               filename=filename).value
        serializer.save_tree_only_filename(new_tree, new_tree.filename)
        self.assertTrue(os.path.isfile(filename))
        self.assertTrue(os.path.isfile(first_tree.filename))
        loaded_tree = serializer.load_link_new_serializer(new_tree.get_link())
        self.assertEqual(loaded_tree, new_tree)
        os.remove(filename)
        os.remove(first_tree.filename)

    def test_create_next_file_version_no_ver_tsv(self):
        first_filename = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.tsv'
        expected_next = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_1.tsv'
        self.assertEqual(expected_next, tree_creator.get_next_version_name(first_filename))

    def test_create_next_file_version_no_exist(self):
        first_filename = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_99.tsv'
        expected_next = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_100.tsv'
        self.assertEqual(expected_next, tree_creator.get_next_version_name(first_filename))

    def test_create_next_file_version_no_ver_tsv_gz(self):
        first_filename = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.tsv.gz'
        expected_next = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_1.tsv.gz'
        self.assertEqual(expected_next, tree_creator.get_next_version_name(first_filename))

    def test_create_next_file_version_no_exist_xyz(self):
        first_filename = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_99.xyz'
        expected_next = 'https://artmapstore.blob.core.windows.net/firstnodes/fruits.ver_100.xyz'
        self.assertEqual(expected_next, tree_creator.get_next_version_name(first_filename))

    def test_url_exists(self):
        self.assertTrue(utilities.url_exists('http://www.wikipedia.org'))
        self.assertFalse(utilities.url_exists('http://www.aljblabjl134141241tasfjalfjlajfala.com'))

    def test_create_new_tree_from_old_node_link(self):
        first_tree = TestImageTree.create_one_high_tree()
        first_tree_filename = 'tcntfonl0.tsv'
        if os.path.isfile(first_tree_filename):
            os.remove(first_tree_filename)
        first_tree.set_filename(first_tree_filename)
        serializer.save_tree(first_tree)
        quad_key = '01'
        new_link = first_tree.get_link()
        new_tree = tree_creator.create_new_from_old_insert_node_link(old_tree=first_tree, link_to_insert=new_link,
                                                                     quad_key=quad_key,
                                                                     new_tree_name='hosa',
                                                                     filename='newctfo.tsv').value
        self.assertEqual('hosa', new_tree.name)
        self.assertEqual(new_link, new_tree.get_descendant(quad_key).get_link())
        self.assertEqual(TestImageTree.father_pixel, tuple(new_tree.get_np_array(1).flatten()))
        self.assertEqual(TestImageTree.father_pixel, tuple(new_tree.get_descendant(quad_key).get_np_array(1).flatten()))
        os.remove(first_tree_filename)

    def test_create_new_tree_from_old_node_link_save_load(self):
        first_tree = TestImageTree.create_one_high_tree()
        first_tree_filename = 'tcntfonlsl.tsv'
        second_tree_filename = 'saveload_nl.tsv'
        if os.path.isfile(first_tree_filename):
            os.remove(first_tree_filename)
        if os.path.isfile(second_tree_filename):
            os.remove(second_tree_filename)
        first_tree.set_filename(first_tree_filename)
        serializer.save_tree(first_tree)
        quad_key = '321'
        new_link = first_tree.get_link()
        new_tree_result = tree_creator.create_new_from_old_insert_node_link(old_tree=first_tree,
                                                                            link_to_insert=new_link,
                                                                            quad_key=quad_key,
                                                                            new_tree_name='sln',
                                                                            filename=second_tree_filename)
        new_tree = new_tree_result.value
        serializer.save_tree_only_filename(new_tree, new_tree.filename)
        self.assertTrue(os.path.isfile(second_tree_filename))
        self.assertTrue(os.path.isfile(first_tree.filename))
        loaded_tree = serializer.load_link_new_serializer(new_tree.get_link())
        self.assertEqual(loaded_tree, new_tree)
        os.remove(second_tree_filename)
        os.remove(first_tree_filename)


class PerformanceTests(unittest.TestCase):
    def test_performance_deep_quad_key_500ms(self):
        quad_key = '001023020031110131'
        node_link = 'start@https://artmapstore.blob.core.windows.net/firstnodes/user/abhishek/start.ver_10.tsv'
        root_tree = serializer.load_link_new_serializer(node_link)
        pil_image0 = root_tree.get_pil_image_at_quadkey(resolution=256, quad_key=quad_key)  # warm it up
        start_time = time.time()
        pil_image1 = root_tree.get_pil_image_at_quadkey(resolution=256, quad_key=quad_key)
        end_time = time.time()
        duration_ms = 1000 * (end_time - start_time)
        time_limit_ms = 50
        self.assertLess(duration_ms, time_limit_ms, 'Time taken to create image ' + str(duration_ms) +
                        ' is not less than ' + str(time_limit_ms))

    def test_lowest_set_node(self):
        node_link = 'start@https://artmapstore.blob.core.windows.net/firstnodes/user/abhishek/start.ver_10.tsv'
        root_tree = serializer.load_link_new_serializer(node_link)
        quad_key = '001023020031111023210'
        lowest_set_node, relative_quad_key = root_tree.lowest_set_node(quad_key)
        self.assertEqual(relative_quad_key, '0')
        self.assertTrue(lowest_set_node.is_set())

    def test_pil_image_at_quad_key(self):
        seattle_skyline_pil_image = utilities.reshape_proper_pil_image(
            imagevalue.fetch_image_from_url(constants.seattle_skyline_url))
        start_resolution, _ = seattle_skyline_pil_image.size
        croped_image = imagetree.pil_image_at_quad_key(seattle_skyline_pil_image, quad_key='30')
        cropped_resolution, _ = croped_image.size
        self.assertEqual(start_resolution, cropped_resolution * 4)
        box = (start_resolution / 2, start_resolution / 2, start_resolution * 3 / 4, start_resolution * 3 / 4)
        self.assertEqual(seattle_skyline_pil_image.crop(box=box), croped_image)
