import os

import custom_errors
import utilities

first_container = 'firstnodes'
first_storage_account = 'artmapstore'
base_azure_blob = 'https://{0}.blob.core.windows.net/{1}/{2}.tsv.gz'
read_key = None


def create_first_node_link(label):
    return utilities.format_node_address(filename=create_first_blob_name(label), node_name=label)


def create_blob_name_from_base(blob_name, container_name, account_name):
    return base_azure_blob.format(account_name, container_name, blob_name)


def create_first_blob_name(blob_name):
    return create_blob_name_from_base(blob_name, container_name=first_container, account_name=first_storage_account)


def get_blob_name_from(url):
    blob_start_index = len('https://{0}.blob.core.windows.net/{1}/'.format(first_storage_account, first_container))
    return url[blob_start_index:]


def upload_to_url(file_to_store, url):
    blob_name = get_blob_name_from(url)
    upload_to_blob_name(file_to_store, blob_name)


def upload_to_blob_name(file_to_store, blob_name):
    from azure.storage.blob import BlockBlobService
    global read_key
    if read_key is None:
        keys_filename = 'keys.txt'
        if not os.path.isfile(keys_filename):
            basedir = os.path.abspath(os.path.dirname(__file__))
            raise custom_errors.CreationFailedError('Keys file not found for azure storage. Need a file named '
                                                    + basedir + '/' + keys_filename)
        with open(keys_filename) as f:
            read_key = f.read()
    block_blob_service = BlockBlobService(account_name=first_storage_account, account_key=read_key)
    block_blob_service.create_blob_from_path(container_name=first_container,
                                             blob_name=blob_name, file_path=file_to_store)
    print('Saved to azure the file ', file_to_store, '. Remote path = ', blob_name)

if __name__ == '__main__':
    import requests
    data = {'Authorization':'SharedKey artmapstore:',
            'x-ms-date':'Fri, 26 Jun 2015 23:39:12 GMT'}
    url = 'https://artmapstore.blob.core.windows.net/?comp=list'
    r = requests.get(url, data=data)
    print(r.status_code, r.text)