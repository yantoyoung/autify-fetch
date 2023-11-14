#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import re
import sys
from datetime import datetime, timezone
from typing import List, Optional, TypedDict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, ResultSet


class Metadata(TypedDict):
    site: str
    num_links: int
    images: int
    last_fetch: str


def download_assets_and_normalize_paths(
    base_url: str,
    base_local_path: str,
    assets: ResultSet,
    path_attr: str,
) -> ResultSet:
    """
    - Download images, scripts and stylesheets contained in parsed web page.
    - Normalize the asset path by removing the front slashes (if any) so that
      they become relative paths and can be accessed when opening saved
      web pages locally.
    - Some assets can be taken from other sources e.g. a CDN. In that case,
      remove the site name and use the path following the site name as the local
      path to store the downloaded files.
      E.g. File from https://cdnjs.cloudflare.com/ajax/libs/jquery/jquery.min.js
           will be saved locally in ./ajax/libs/jquery/jquery.min.js
    :return input ResultSet with the paths normalized
    """
    for asset in assets:
        asset_path = asset.attrs.get(path_attr)

        # Skip for embedded Javascript.
        if not asset_path:
            continue

        if asset_path.startswith('http'):
            asset_url = asset_path
            parsed_path = urlparse(asset_path)
            asset_path = parsed_path.path.lstrip('/')
        else:
            asset_url = urljoin(base_url, asset_path)
            asset_path = asset_path.lstrip('/')

        try:
            response = requests.get(asset_url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(http_err, file=sys.stderr)
        except requests.exceptions.RequestException as req_exc:
            print(req_exc, file=sys.stderr)
        else:
            asset[path_attr] = asset_path

            local_path = os.path.join(
                base_local_path,
                os.path.dirname(asset_path)
            )
            if not os.path.exists(local_path):
                os.makedirs(local_path)

            with open(
                os.path.join(local_path, os.path.basename(asset_path)), 'wb'
            ) as f:
                f.write(response.content)

    return assets


def save_webpage(base_local_path: str, content: str):
    file_name = base_local_path.split('/')[-1]
    save_path = os.path.join(base_local_path, f'{file_name}.html')
    with open(save_path, 'w') as f:
        f.write(content)


def print_metadata(metadata: Metadata):
    for key, value in metadata.items():
        print(f'{key}: {value}')


def fetch_webpages(urls: List[str], record_metadata: Optional[bool] = False):
    for url in urls:
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(http_err, file=sys.stderr)
        except requests.exceptions.RequestException as req_exc:
            print(req_exc, file=sys.stderr)
        else:
            # Create a local directory with the site as the directory name.
            # All downloaded files will be saved there.
            remove_https_regex = re.compile(r'https?://')
            site_name = remove_https_regex.sub('', url).strip().strip('/')
            base_local_path = os.path.join(os.getcwd(), site_name)
            if not os.path.exists(base_local_path):
                os.makedirs(base_local_path)

            now = datetime.now(timezone.utc)
            soup = BeautifulSoup(response.content, 'html.parser')

            images = soup.find_all('img')
            images_with_normalized_paths = download_assets_and_normalize_paths(
                url, base_local_path, images, 'src'
            )
            for image, image_with_normalized_path in zip(images, images_with_normalized_paths):
                image['src'] = image_with_normalized_path['src']

            stylesheets = soup.find_all('link', rel='stylesheet')
            stylesheets_with_normalized_paths = download_assets_and_normalize_paths(
                url, base_local_path, stylesheets, 'href'
            )
            for stylesheet, stylesheet_with_normalized_path in zip(stylesheets, stylesheets_with_normalized_paths):
                stylesheet['href'] = stylesheet_with_normalized_path['href']

            scripts = soup.find_all('script')
            scripts_with_normalized_paths = download_assets_and_normalize_paths(
                url, base_local_path, scripts, 'src'
            )
            for script, script_with_normalized_path in zip(scripts, scripts_with_normalized_paths):
                if script.has_attr('src'):
                    script['src'] = script_with_normalized_path['src']

            save_webpage(base_local_path, str(soup))

            if record_metadata:
                links = soup.find_all('a')

                metadata = Metadata(
                    site=site_name,
                    num_links=len(links),
                    images=len(images),
                    last_fetch=now.strftime('%a %b %d %Y %H:%M %Z')
                )
                print_metadata(metadata)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('urls', type=str, nargs='+', help='list of urls to fetch')
    parser.add_argument('--metadata', action='store_true', help='show metadata on console')

    args = parser.parse_args()

    fetch_webpages(args.urls, args.metadata)
