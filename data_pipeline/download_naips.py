'''
    a class to download NAIP imagery from 
    the s3://aws-naip RequesterPays bucket
'''

import boto3
from random import shuffle
import sys, os, subprocess

GEO_DATA_DIR = os.environ.get("GEO_DATA_DIR") # set in Dockerfile as env variable
NAIP_DATA_DIR = os.path.join(GEO_DATA_DIR, "naip")

class NAIPDownloader:

  def __init__(self):
    '''
        download some arbitrary NAIP images from the aws-naip S3 bucket
    '''

    self.number_of_naips = 1

    self.state = 'md'
    self.year = '2013'
    self.resolution = '1m'
    self.spectrum = 'rgbir' 
    self.grid = '38077'
    self.bucket_url = 's3://aws-naip/'
    self.url_base = '{}{}/{}/{}/{}/{}/'.format(self.bucket_url, self.state,self.year,self.resolution,self.spectrum,self.grid)

    self.make_directory(NAIP_DATA_DIR, full_path=True)

  def make_directory(self, new_dir, full_path=False):
    '''
       make a new directory tree if it doesn't already exist
    '''
    if full_path:
      path = ''
      for token in new_dir.split('/'):
        path += token + '/'
        try:
          os.mkdir(path);
        except:
          pass
      return path

    try:
      os.mkdir(new_dir);
    except:
      pass
    return new_dir

  def download_naips(self):
    '''
        download self.number_of_naips randomish NAIPs from aws-naip bucket
    '''

    self.configure_s3cmd()
    naip_filenames = self.list_naips()
    shuffle(naip_filenames)
    naip_local_paths = self.download_from_s3(naip_filenames)
    return naip_local_paths

  def configure_s3cmd(self):
    ''' 
        configure s3cmd with AWS credentials
    '''
    file_path = '/' + os.environ.get("HOME")+'/.s3cfg'
    f = open(file_path,'r')
    filedata = f.read()
    f.close()
    newdata = filedata.replace("AWS_ACCESS_KEY",os.environ.get("AWS_ACCESS_KEY_ID"))
    newdata = newdata.replace("AWS_SECRET_KEY",os.environ.get("AWS_SECRET_ACCESS_KEY"))
    f = open(file_path,'w')
    f.write(newdata)
    f.close()

  def list_naips(self):
    '''
        make a list of NAIPs based on the init parameters for the class
    '''

    # list the contents of the bucket directory
    bash_command = "s3cmd ls --recursive --skip-existing {} --requester-pays".format(self.url_base)
    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    naip_filenames = []
    for line in output.split('\n'):
      parts = line.split(self.url_base)
      if len(parts) == 2:
        naip_filenames.append(parts[1])
      else:
        pass
        # skip non filename lines from response
    return naip_filenames

  def download_from_s3(self, naip_filenames):
    '''
        download the NAIPs and return a list of the file paths
    '''

    s3_client = boto3.client('s3')
    naip_local_paths = []
    max_range = self.number_of_naips
    if max_range == -1:
      max_range = len(naip_filenames)
    for filename in naip_filenames[0:max_range]:
      full_path = os.path.join(NAIP_DATA_DIR, filename)
      if os.path.exists(full_path):
        print("NAIP {} already downloaded".format(full_path))
      else:
        url_without_prefix = self.url_base.split(self.bucket_url)[1]
        s3_url = '{}{}'.format(url_without_prefix, filename)
        s3_client.download_file('aws-naip', s3_url, full_path, {'RequestPayer':'requester'})
      naip_local_paths.append(full_path)
    return naip_local_paths


if __name__ == '__main__':
  parameters_message = "parameters are: download"
  if len(sys.argv) == 1:
    print(parameters_message)
  elif sys.argv[1] == 'download':
  	naiper = NAIPDownloader()
  	naiper.download_naips()
  else:
    print(parameters_message)