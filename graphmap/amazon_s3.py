import os
import tinys3

bucket_name = 'graphnodes'
key_filename = 'rootkey.csv'
if os.path.isfile(key_filename):
    with open(key_filename, 'r') as f:
        key_file_content = f.readlines()
else:
    raise IOError('Need a rootkey.csv file containing S3 credentials')
access_key_id = key_file_content[0].strip().split('=')[-1]
secret_key = key_file_content[1].strip().split('=')[-1]


def upload_file(filename, remote_filename):
    conn = tinys3.Connection(access_key_id, secret_key, tls=True)
    with open(filename, 'rb') as f:
        conn.upload(remote_filename, f, bucket_name)


if __name__ == '__main__':
    upload_file('constants.py', 'first/constants2.py')
