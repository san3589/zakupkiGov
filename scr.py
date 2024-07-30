import requests
from bs4 import BeautifulSoup
import zipfile
import rarfile
from io import BytesIO
import os
import time
import hashlib
from options import cookies, headers
from tkinter import messagebox
from tkinter import ttk


def decode_filename(filename):
    try:
        return filename.encode('cp437').decode('utf-8').replace('/', '').replace('\\', '')
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return filename.encode('cp437').decode('cp866')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return filename.replace('/', '').replace('\\', '')


def ask_user_confirmation(auto_confirm, log_text, file_content=None):
    if auto_confirm:
        return True
    if file_content:
        log_text.insert('end', f"Archive contents:\n{file_content}\n")
        result = messagebox.askyesno("Download Confirmation", f"Do you want to download this archive?\n\nContents:\n{file_content}")
    else:
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


def hash_folder_name(name):
    return hashlib.md5(name.encode('utf-8')).hexdigest()


def find_files_on_page(url, auto_confirm, folder_path, log_text):
    response = requests.get(f"https://zakupki.gov.ru{url}", headers=headers, cookies=cookies)
    soup = BeautifulSoup(response.text, 'lxml')
    files = []
    multifiles = []
    try:
        page_name = soup.find('span', class_="cardMainInfo__content").text.strip().replace('/', '').replace('\\', '')[:100]
    except AttributeError:
        page_name = soup.find('div', class_="registry-entry__body-value").text.strip().replace('/', '').replace('\\', '')[:100]

    # Создаем папку с именем page_name
    page_folder = os.path.join(folder_path, page_name)
    os.makedirs(page_folder, exist_ok=True)

    try:
        files_block = soup.find('div', class_='blockFilesTabDocs').find_all('div', class_='col clipText')
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
                    if ask_user_confirmation(auto_confirm, log_text):
                        download_path = os.path.join(page_folder, page_name)
                        download_file(f"https://zakupki.gov.ru{file_link}", download_path, log_text)
                    else:
                        continue
    return files, multifiles, page_folder


def process_archive(content, archive_type, log_text, parent=""):
    contents_list = []
    if archive_type == "zip":
        with zipfile.ZipFile(content, 'r') as zip_ref:
            for member in zip_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                contents_list.append(full_path)
                nested_content = BytesIO(zip_ref.read(member))
                if zipfile.is_zipfile(nested_content):
                    log_text.insert('end', f"Found nested zip file: {full_path}\n")
                    contents_list.extend(process_archive(nested_content, "zip", log_text, full_path))
                elif rarfile.is_rarfile(nested_content):
                    log_text.insert('end', f"Found nested rar file: {full_path}\n")
                    contents_list.extend(process_archive(nested_content, "rar", log_text, full_path))
    elif archive_type == "rar":
        with rarfile.RarFile(content) as rar_ref:
            for member in rar_ref.infolist():
                decoded_name = decode_filename(member.filename)
                full_path = f"{parent}/{decoded_name}" if parent else decoded_name
                contents_list.append(full_path)
                nested_content = BytesIO(rar_ref.read(member))
                if zipfile.is_zipfile(nested_content):
                    log_text.insert('end', f"Found nested zip file: {full_path}\n")
                    contents_list.extend(process_archive(nested_content, "zip", log_text, full_path))
                elif rarfile.is_rarfile(nested_content):
                    log_text.insert('end', f"Found nested rar file: {full_path}\n")
                    contents_list.extend(process_archive(nested_content, "rar", log_text, full_path))
    return contents_list


def check_archive_contents_via_http(file_url, log_text):
    response = requests.get(file_url, headers=headers, cookies=cookies, stream=True)
    if response.status_code == 200:
        content = BytesIO(response.content)
        try:
            if zipfile.is_zipfile(content):
                log_text.insert('end', "Contents of the ZIP archive:\n")
                contents = process_archive(content, "zip", log_text)
                return True, contents
            content.seek(0)
            if rarfile.is_rarfile(content):
                log_text.insert('end', "Contents of the RAR archive:\n")
                contents = process_archive(content, "rar", log_text)
                return True, contents
        except Exception:
            log_text.insert('end', 'Unreadable format in archive\n')
    return False, []


def download_and_check_first_part(file_urls, download_dir, log_text):
    part_url = file_urls
    if download_file(part_url, download_dir, log_text):
        valid, contents = check_archive_contents_via_http(part_url, log_text)
        return download_dir, valid, contents
    return None, False, []


def download_file(file_url, download_path, log_text):
    response = requests.get(file_url, headers=headers, cookies=cookies, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        start_time = time.time()

        # Создаем прогресс-бар
        progress = ttk.Progressbar(log_text, orient='horizontal', length=400, mode='determinate', maximum=total_size)
        log_text.window_create('end', window=progress)
        log_text.insert('end', '\n')  # Добавляем перенос строки после прогресс-бара

        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
                downloaded_size += len(chunk)

                # Обновляем прогресс-бар и лог
                log_text.see('end')
                elapsed_time = time.time() - start_time
                speed = downloaded_size / elapsed_time if elapsed_time > 0 else 0
                percent = (downloaded_size / total_size) * 100

                log_text.delete('end-2l', 'end-1l')  # Удаляем предыдущую строку
                log_text.insert('end-1l', f"\rDownloading {download_path}: {percent:.2f}% at {speed / 1024:.2f} KB/s\n", 'log')
                log_text.see('end')  # Прокрутка к последней строке
                log_text.update_idletasks()  # Обновляем интерфейс

        log_text.insert('end', f"\nDownloaded file: {download_path}\n")
        log_text.see('end')  # Прокрутка к последней строке
        return True
    log_text.insert('end', f"Failed to download file: {file_url}\n")
    log_text.see('end')  # Прокрутка к последней строке
    return False


def download_multivolume_archive(file_urls, download_dir, log_text):
    for file_url, _ in file_urls:
        download_file(file_url, os.path.join(download_dir, os.path.basename(download_dir)), log_text)


def main(params, auto_confirm, folder_entry, log_text):
    links = get_links_from_search(params)
    for link in links:
        log_text.insert('end', f"Processing link: {link}\n")
        log_text.update_idletasks()  # Обновляем интерфейс
        files, multifiles, page_folder = find_files_on_page(link, auto_confirm, folder_entry, log_text)
        for file_url, file_name in files:
            log_text.insert('end', f"Checking contents of archive: {file_url}\n")
            log_text.update_idletasks()  # Обновляем интерфейс
            if check_archive_contents_via_http(file_url, log_text):
                if ask_user_confirmation(auto_confirm, log_text):
                    download_path = os.path.join(page_folder, file_name)
                    download_file(file_url, download_path, log_text)
        for file_url, file_name in multifiles:
            log_text.insert('end', f"Downloading first part of multivolume archive: {file_url}\n")
            log_text.update_idletasks()  # Обновляем интерфейс
            download_path = os.path.join(page_folder, file_name)
            first_part_path = download_and_check_first_part(file_url, download_path, log_text)
            if first_part_path and ask_user_confirmation(auto_confirm, log_text):
                log_text.insert('end', "Downloading full multivolume archive...\n")
                log_text.update_idletasks()  # Обновляем интерфейс
                download_multivolume_archive(files, download_path, log_text)
            else:
                log_text.insert('end', "Skipping multivolume archive.\n")
                log_text.update_idletasks()  # Обновляем интерфейс
                break
