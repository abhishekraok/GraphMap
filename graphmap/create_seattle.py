import commander
import azure_image_tree
import serializer

input_image_list = ['../data/worldmapStretch.jpg',
                    'http://alltaskstraducoes.com.br/vdisk/27/united-states-flag-map-i6.jpg',
                    'https://c1.staticflickr.com/5/4091/5001052425_e67c39a89b.jpg',
                    'https://upload.wikimedia.org/wikipedia/commons/b/b7/Seattle_Skyline_tiny.jpg',
                    'https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Seattle_07752.JPG/640px-Seattle_07752.JPG',
                    'https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Mount_Rainier_over_Tacoma.jpg/320px-Mount_Rainier_over_Tacoma.jpg'
                    ]
labels = ['worldmap', 'usaflags', 'washingtoni', 'seattleskyline', 'seattledowntown', 'rainier_tacoma']
seattle_node_link = [azure_image_tree.create_first_node_link(label) for label in labels]
quad_keys_to_link = ['003', '00300', '00300012']


def create_seattle():
    # Create images
    for image_link, label in zip(input_image_list, labels):
        node_link = azure_image_tree.create_first_node_link(label)
        commander.create_tree(image_link, node_link=node_link)
    # Link them
    root_tree = serializer.load_link_new_serializer(seattle_node_link[0])
    for i, quad_key in enumerate(quad_keys_to_link):
        commander.insert_tree_root(root_tree, seattle_node_link[i + 1], quad_key)


if __name__ == '__main__':
    create_seattle()
