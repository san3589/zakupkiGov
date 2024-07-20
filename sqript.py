import re

import requests
from bs4 import BeautifulSoup
import mimetypes
import zipfile
import rarfile
from tqdm import tqdm
from io import BytesIO
import os
from options import cookies, headers

def decode_filename(filename):
    try:
        return filename.encode('cp437').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return filename.encode('cp437').decode('cp866')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return filename

def ask_user_confirmation():
    while True:
        user_input = input("Do you want to download this archive? (yes/no): ").strip().lower()
        if user_input in ['yes', 'no']:
            return user_input == 'yes'
        print("Please answer 'yes' or 'no'.")

def search(params):
    response = requests.get(
        'https://zakupki.gov.ru/epz/order/extendedsearch/results.html',
        params=params,
        cookies=cookies,
        headers=headers,
    )
    soup = BeautifulSoup(response.text, 'lxml')
    links = soup.find('div', class_='search-registry-entrys-block').find_all('a')
    return links

def get_links_from_search(query):
    links = search(query)
    hrefs = []
    for link in links:
        try:
            href = link.get('href')
            if 'common-info.html' in href:
                hrefs.append(href)
        except (AttributeError, TypeError):
            continue
    print(len(hrefs))
    hrefs = [href.replace('common-info', 'documents') for href in hrefs]
    return hrefs

def find_files_on_page(url):
    response = requests.get(f"https://zakupki.gov.ru{url}", headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, 'lxml')
    files = []
    multifiles = []
    try:
        files_block =  soup.find('div', class_='blockFilesTabDocs').find_all('div', class_='col clipText')
        for file in files_block:
            file_text = file.find('img').get('alt')
            file_link = file.find('span', class_='section__value')
            file_name = file.find_all('a')[-1].text.strip('\n ')
            if file_text == 'Часть архива':
                 multifiles.append((file_link.find('a').get('href'), file_name))
            elif 'архив' in file_text:
                files.append((file_link.find('a').get('href'), file_name))
    except AttributeError:
        files_block = soup.find('section', class_="card-attachments").find('div', class_='col-12').find('div', class_='attachment__value').find_all('div', class_='')
        for file in files_block:
            info_file = file.find('img', class_='vAlignMiddle margRight5').get('alt')
            file_name = file.find_all('a')[-1].text.strip('\n ')

            if 'part' in file_name:
                file_link = file.find_all('a')[-1].get('href')
                endwish = file_name.split('.')[-1]
                if endwish == 'zip' or endwish == 'rar':
                    multifiles.append((f"https://zakupki.gov.ru{file_link}", file_name))
                    return files
                if endwish == 'z01':
                    print("Невозможно залянуть в архив")
                    if ask_user_confirmation():
                        download_path = os.path.join('/home/alex', file_name)
                        download_file(f"https://zakupki.gov.ru{file_link}", download_path)
    return files, multifiles



def process_archive(content, archive_type, parent=""):
    if archive_type == "zip":
        with zipfile.ZipFile(content, 'r') as zip_ref:
            for member in zip_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                print(full_path)
                if zipfile.is_zipfile(BytesIO(zip_ref.read(member))):
                    print(f"Found nested zip file: {full_path}")
                    nested_content = BytesIO(zip_ref.read(member))
                    process_archive(nested_content, "zip", full_path)
                elif rarfile.is_rarfile(BytesIO(zip_ref.read(member))):
                    print(f"Found nested rar file: {full_path}")
                    nested_content = BytesIO(zip_ref.read(member))
                    process_archive(nested_content, "rar", full_path)
    elif archive_type == "rar":
        with rarfile.RarFile(content) as rar_ref:
            for member in rar_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                print(full_path)
                if zipfile.is_zipfile(BytesIO(rar_ref.read(member))):
                    print(f"Found nested zip file: {full_path}")
                    nested_content = BytesIO(rar_ref.read(member))
                    process_archive(nested_content, "zip", full_path)
                elif rarfile.is_rarfile(BytesIO(rar_ref.read(member))):
                    print(f"Found nested rar file: {full_path}")
                    nested_content = BytesIO(rar_ref.read(member))
                    process_archive(nested_content, "rar", full_path)


# Функция для проверки содержимого архива через HTTP-заголовки

def check_archive_contents_via_http(file_url):
    response = requests.get(file_url, headers=headers, cookies=cookies, stream=True)
    if response.status_code == 200:
        content = BytesIO(response.content)
        try:
            if zipfile.is_zipfile(content):
                print("Contents of the ZIP archive:")
                process_archive(content, "zip")
                return True
            content.seek(0)
            if rarfile.is_rarfile(content):
                print("Contents of the RAR archive:")
                process_archive(content, "rar")
                return True
        except zipfile.BadZipFile:
            if zipfile.is_zipfile(content):
                with zipfile.ZipFile(content, 'r') as zip_ref:
                    print("Contents of the archive:")
                    for member in zip_ref.infolist():
                        decoded_name = decode_filename(member.filename)
                        print(decoded_name)
                    return True
            content.seek(0)
            if rarfile.is_rarfile(content):
                with rarfile.RarFile(content) as rar_ref:
                    print("Contents of the RAR archive:")
                    for member in rar_ref.infolist():
                        decoded_name = decode_filename(member.filename)
                        print(decoded_name)
                    return True
        except Exception:
            print('Unreaded format in archive')
            return True
    return False



def download_file(file_url, download_path):
    response = requests.get(file_url,headers=headers, cookies=cookies, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        with open(download_path, 'wb') as file, tqdm(
                desc=download_path,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                bar.update(len(chunk))
        return True
    return False

# Функция для скачивания многотомных архивов


# Функция для проверки содержимого архива
def check_archive_contents(file_paths):
    for file_path in file_paths:
        if zipfile.is_zipfile(file_path):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    try:
                        member.filename = member.filename.encode('cp437').decode('cp866')
                    except UnicodeDecodeError:
                        pass
                    print(member.filename)
        else:
            print("Unsupported archive format")
def download_and_check_first_part(file_urls, download_dir):
    part_url = file_urls[0][0]  # URL первого тома
    part_path = os.path.join(download_dir, os.path.basename(part_url))
    if download_file(part_url, part_path):
        check_archive_contents([part_path])
        return part_path
    return None

def download_file(file_url, download_path):
    response = requests.get(file_url,headers=headers, cookies=cookies, stream=True)
    if response.status_code == 200:
        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    return False

# Функция для скачивания многотомных архивов
def download_multivolume_archive(file_urls, download_dir):
    part_url = file_urls[0]  # URL первого тома
    part_path = os.path.join(download_dir, os.path.basename(part_url))
    download_file(part_url, part_path)
    return [part_path]

# Основная функция
def main(params):
    links = get_links_from_search(params)
    for link in links:
        print(link)
        files, multifiles = find_files_on_page(link)
        for file_url, file_name in files:
            print(f"Checking contents of volume archive: {file_url}")
            if check_archive_contents_via_http(file_url):
                if ask_user_confirmation():
                    file_name = os.path.basename(file_name)
                    download_path = os.path.join('/home/alex', file_name)
                    download_file(file_url, download_path)
        for file_url, file_name in multifiles:
            print(f"Downloading first part of multivolume archive: {file_url}")
            file_name = os.path.basename(file_name)
            download_path = os.path.join('/home/alex', file_name)
            first_part_path = download_and_check_first_part(files, download_path)
            if first_part_path and ask_user_confirmation():
                print("Downloading full multivolume archive...")

                download_multivolume_archive(files, download_path)
            else:
                print("Skipping multivolume archive.")
                break


# Пример использования:






