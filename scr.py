import requests
from bs4 import BeautifulSoup
import zipfile
import rarfile
from tqdm import tqdm
from io import BytesIO
import os
from options import cookies, headers
from tkinter import messagebox


def decode_filename(filename):
    try:
        return filename.encode('cp437').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return filename.encode('cp437').decode('cp866')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return filename


def ask_user_confirmation(auto_confirm):
    if auto_confirm:
        return True
    result = messagebox.askyesno("Download Confirmation", "Do you want to download this archive?")
    return result


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
        href = link.get('href')
        if href and 'common-info.html' in href:
            hrefs.append(href.replace('common-info', 'documents'))
    return hrefs


def find_files_on_page(url, auto_confirm, folder_path):
    response = requests.get(f"https://zakupki.gov.ru{url}", headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, 'lxml')
    files = []
    multifiles = []
    page_name = soup.find('span', class_="cardMainInfo__content").text
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
                if endwish == 'z01':
                    print("Невозможно залянуть в архив")
                    if ask_user_confirmation(auto_confirm):
                        download_path = os.path.join(folder_path, page_name)
                        download_file(f"https://zakupki.gov.ru{file_link}", download_path)
                    else:
                        continue
    return files, multifiles


def process_archive(content, archive_type, parent=""):
    if archive_type == "zip":
        with zipfile.ZipFile(content, 'r') as zip_ref:
            for member in zip_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                print(full_path)
                nested_content = BytesIO(zip_ref.read(member))
                if zipfile.is_zipfile(nested_content):
                    print(f"Found nested zip file: {full_path}")
                    process_archive(nested_content, "zip", full_path)
                elif rarfile.is_rarfile(nested_content):
                    print(f"Found nested rar file: {full_path}")
                    process_archive(nested_content, "rar", full_path)
    elif archive_type == "rar":
        with rarfile.RarFile(content) as rar_ref:
            for member in rar_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                print(full_path)
                nested_content = BytesIO(rar_ref.read(member))
                if zipfile.is_zipfile(nested_content):
                    print(f"Found nested zip file: {full_path}")
                    process_archive(nested_content, "zip", full_path)
                elif rarfile.is_rarfile(nested_content):
                    print(f"Found nested rar file: {full_path}")
                    process_archive(nested_content, "rar", full_path)


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
        except Exception:
            print('Unreadable format in archive')
    return False


def download_and_check_first_part(file_urls, download_dir):
    part_url = file_urls
    # part_path = os.path.join(download_dir, os.path.basename(part_url))
    if download_file(part_url, download_dir):
        check_archive_contents_via_http(part_url)
        return download_dir
    return None


def download_file(file_url, download_path):
    response = requests.get(file_url, headers=headers, cookies=cookies, stream=True)
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


def download_multivolume_archive(file_urls, download_dir):
    for file_url, _, _ in file_urls:
        download_file(file_url, os.path.join(download_dir, os.path.basename(download_dir)))



def main(params, auto_confirm, folder_entry):
    links = get_links_from_search(params)
    for link in links:
        print(link)
        files, multifiles = find_files_on_page(link, auto_confirm, folder_entry)
        for file_url, file_name in files:
            print(f"Checking contents of archive: {file_url}")
            if check_archive_contents_via_http(file_url):
                if ask_user_confirmation(auto_confirm):
                    download_path = os.path.join(folder_entry, os.path.basename(file_name))
                    download_file(file_url, download_path)
        for file_url, file_name in multifiles:
            print(f"Downloading first part of multivolume archive: {file_url}")
            download_path = os.path.join(folder_entry, os.path.basename(file_name))
            first_part_path = download_and_check_first_part(file_url, download_path)
            if first_part_path and ask_user_confirmation(auto_confirm):
                print("Downloading full multivolume archive...")
                download_multivolume_archive(files, download_path)
            else:
                print("Skipping multivolume archive.")
                break