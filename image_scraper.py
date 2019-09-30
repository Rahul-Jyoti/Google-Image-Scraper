from bs4 import BeautifulSoup
import json
import re
import argparse
import itertools
import logging
import os
import uuid
import sys
from urllib.request import urlopen, Request

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s %(levelname)s %(module)s]: %(message)s'))
    logger.addHandler(handler)
    FileHandler = logging.FileHandler("log.txt")
    FileHandler.setFormatter(logging.Formatter('[%(asctime)s %(levelname)s %(module)s]: %(message)s'))
    logger.addHandler(FileHandler)
    return logger

logger = configure_logging()

request_header = {'User-Agent': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"}

def get_soup(url,header):
    response = urlopen(Request(url,headers=header))
    return BeautifulSoup(response,'html.parser')                        # Extracting HTML data 

def get_url(query):
    # returning the url as per the query of the user
    return "https://www.google.co.in/search?q=%s&source=lnms&tbm=isch" % query  

def extract_images_from_soup(soup):
    image_elements = soup.find_all("div",{"class":"rg_meta"})           # extracting the image elements
    metadata_dicts = (json.loads(e.text) for e in image_elements)
    link_type_records = ((d['ou'],d['ity']) for d in metadata_dicts)    # 'ou' -> link , 'ity' -> extension
    return link_type_records

def extract_images(query,num_images):
    url = get_url(query)
    logger.info("Souping")
    soup = get_soup(url,request_header)
    logger.info("Extracting image urls")
    link_type_records = extract_images_from_soup(soup)
    return itertools.islice(link_type_records,num_images)

def get_raw_image(url):
    req = Request(url,headers=request_header)
    resp = urlopen(req)
    return resp.read()

def save_image(raw_image, image_type, save_directory):
    extension = image_type if image_type else 'jpg'
    file_name = uuid.uuid4().hex + "." + extension         #uuid to generate unique names for downloaded images
    save_path = os.path.join(save_directory,file_name)
    with open(save_path,'wb') as f:                        #writing into a file in binary mode
        f.write(raw_image)

def download_images_to_dir(images, save_directory, num_images):
    for i , (url,image_type) in enumerate(images):
        try:
            logger.info("Making request (%d/%d): %s",i,num_images,url)
            raw_image = get_raw_image(url)
            save_image(raw_image, image_type, save_directory)
        except Exception as e:
            logger.exception(e)

def run(query, save_directory, num_images=5):
    query = '+'.join(query.split())
    logger.info("Extracting image links")
    images = extract_images(query,num_images)
    logger.info("Downlading images")
    download_images_to_dir(images, save_directory, num_images)
    logger.info("Finished")

def main():
    # For shell scripting
    parser = argparse.ArgumentParser(description='Scrape google images')
    parser.add_argument('-s', '--search', default='india', type=str, help='search term')
    parser.add_argument('-n', '--num_images', default=5, type=int, help='number of images to save')
    parser.add_argument('-d', '--directory', default="default_directory_to_save_images", type=str, help='save directory')
    args = parser.parse_args()
    run(args.search, args.directory, args.num_images)

if __name__ == '__main__':
    main()

