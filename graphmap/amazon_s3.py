import os
import tinys3
import constants

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
    if remote_filename.startswith(constants.amazon_s3_base_filename):
        final_remote_filename = constants.amazon_s3_folder + '/'  + remote_filename[len(constants.amazon_s3_base_filename):]
    else:
        final_remote_filename = remote_filename
    with open(filename, 'rb') as f:
        conn.upload(final_remote_filename, f, constants.amazon_s3_bucket)


if __name__ == '__main__':
    upload_file('constants.py', 'first/constants2.py')
