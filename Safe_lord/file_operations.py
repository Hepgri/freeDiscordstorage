import os
import sys
import io
import logging
import requests
import zipfile
import time
from time import sleep
from index_management import load_file_index, get_file_index, update_file_index
from utils import show_progress_bar, print_table_header, print_table_row, print_summary_line, get_total_chunks, fetch_message
from file_utils import encode, decode, get_size_format
from config import MAX_TERMINAL_WIDTH, CHANNEL_ID, BASE_URL, headers, CHUNK_SIZE


def list_files(args):
    """
    Lists files stored in the file index, displaying their name, size, and total storage used.

    Args:
        args (list): Arguments passed to the function.
    """
    try:
        load_file_index()
        file_index = get_file_index()
    except Exception as e:
        print(f"Error loading file index: {e}")
        return

    formatting, maxwidth = print_table_header()
    total_size = 0

    for i, values in enumerate(file_index.values()):
        try:
            filename = decode(values["filename"])
        except Exception as e:
            print(f"Error decoding filename: {e}")
            continue

        size = values.get("size", 0)
        total_size += size
        print_table_row(i + 1, filename, size, formatting, maxwidth)

    print_summary_line(max_width=MAX_TERMINAL_WIDTH)
    print(f"Total storage used: {get_size_format(total_size)}")

def find_file(args):
    """
    Searches for files in the file index that match the given search terms.

    Args:
        args (list): The search terms as a list of strings.
    """
    try:
        load_file_index()
        file_index = get_file_index()
    except Exception as e:
        print(f"Error accessing file index: {e}")
        return

    search_term = " ".join(args).lower()
    results = [
        (i + 1, decode(values["filename"]).lower(), values["size"])
        for i, values in enumerate(file_index.values())
        if search_term in decode(values["filename"]).lower()
    ]

    if results:
        formatting, maxwidth = print_table_header()
        for result_num, result_filename, result_size in results:
            print_table_row(result_num, result_filename, result_size, formatting, maxwidth)
    else:
        print("No matching files found in the server.")

def upload_file(args):
    path = args[0]
    message_id = load_file_index()
    file_index = get_file_index()

    def upload_single_file(file_path, message_id, file_index):
        size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        total_chunks = get_total_chunks(size)

        if encode(filename) in file_index:
            logging.info("File already uploaded.")
            return

        logging.info(f"File Name: {filename}")
        logging.info(f"File Size: {get_size_format(size)}")
        logging.info(f"Chunks to be created: {total_chunks}")
        logging.info("Uploading...")

        # Assume upload_chunks is a function that handles the upload
        urls = upload_chunks(f, filename, total_chunks)

        logging.info("File uploaded")

        file_index[encode(filename)] = {
            "filename": encode(filename),
            "size": size,
            "urls": urls,
        }
        update_file_index(message_id, file_index)

    if os.path.isfile(path):
        with open(path, "rb") as f:
            upload_single_file(path, message_id, file_index)
    elif os.path.isdir(path):
        compressed_file_path = compress_directory(path)
        with open(compressed_file_path, "rb") as f:
            upload_single_file(compressed_file_path, message_id, file_index)
    else:
        logging.error("Invalid path. Please provide a valid file or directory path.")
        sys.exit()

def compress_directory(directory_path):
    try:
        if not os.path.isdir(directory_path):
            logging.error(f"Directory does not exist: {directory_path}")
            return None

        output_filename = os.path.basename(directory_path) + '.zip'
        archive_path = os.path.join(os.getcwd(), output_filename)

        # Get a list of all files to be compressed
        file_paths = []
        for root, directories, files in os.walk(directory_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)

        total_files = len(file_paths)
        logging.info(f"Starting compression of directory: {directory_path}")

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for i, file in enumerate(file_paths, 1):
                # Add file to zip
                zipf.write(file, os.path.relpath(file, directory_path))
                # Update progress bar
                show_progress_bar(i, total_files)

        logging.info(f"Directory compressed successfully: {archive_path}")
        return archive_path
    except Exception as e:
        logging.error(f"Error compressing directory: {e}")
        return None

def upload_chunks(file_handle, filename, total_chunks):
    """
    Uploads file in chunks to a specified channel.

    :param file_handle: File handle for the file to be uploaded.
    :param filename: Name of the file to be uploaded.
    :param total_chunks: Total number of chunks to divide the file into.
    :return: List of tuples containing message_id and attachment_id for each uploaded chunk.
    """
    urls = []
    for i in range(total_chunks):
        show_progress_bar(i + 1, total_chunks)
        chunk_data = file_handle.read(CHUNK_SIZE)
        if not chunk_data:
            break  # Stop if there's no more data to read

        chunk = io.BytesIO(chunk_data)
        files = {"file": (encode(filename) + "." + str(i), chunk)}

        try:
            response = requests.post(f"{BASE_URL}{CHANNEL_ID}/messages", headers=headers, files=files)
            response.raise_for_status()  # Raise an exception for HTTP error responses

            message = response.json()
            urls.append((message["id"], message["attachments"][0]["id"]))  # message_id, attachment_id pair
        except requests.RequestException as e:
            logging.error(f"Failed to upload chunk {i+1}/{total_chunks}: {e}")
            raise  # Reraise the exception to allow caller to handle

    return urls

def download_file(args):
    indices = [int(arg[1:]) if arg[0] == "#" else int(arg) - 1 for arg in args]

    load_file_index()
    file_index = get_file_index()
    filelist = list(file_index.items())

    for index in indices:
        if index >= len(filelist):
            logging.error(f"Invalid ID provided: {index}")
            sys.exit()

        logging.info("Downloading...")

        og_name, file = filelist[index]
        filename = decode(file["filename"])
        os.makedirs(os.path.dirname(f"downloads/{filename}"), exist_ok=True)

        with open(f"downloads/{filename}", "wb") as f:
            for i, values in enumerate(file["urls"]):
                message_id, _ = values  # Assuming attachment_id is no longer needed

                response = fetch_message(message_id)
                if not response:
                    continue  # Skip this file or handle error as needed

                download_url = response['attachments'][0]['url']
                if not download_content(download_url, f, i, len(file["urls"])):
                    continue  # Skip this file or handle error as needed

    logging.info("Download complete.")

def download_content(download_url, file_handle, current_chunk, total_chunks):
    MAX_RETRIES = 5
    RETRY_DELAY = 2  # seconds
    CHUNK_SIZE = 24 * 1024**3  # Adjust based on server capability

    try:
        with requests.get(download_url, stream=True) as cdnResponse:
            cdnResponse.raise_for_status()  # Check for HTTP errors

            for chunk in cdnResponse.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue  # Skip keep-alive chunks

                retry_count = 0
                while retry_count < MAX_RETRIES:
                    try:
                        file_handle.write(chunk)
                        show_progress_bar(current_chunk + 1, total_chunks)
                        break  # Successfully written chunk
                    except Exception as write_error:
                        logging.error(f"Error writing chunk: {write_error}")
                        retry_count += 1
                        time.sleep(RETRY_DELAY)

                if retry_count == MAX_RETRIES:
                    logging.error("Max retries reached for writing chunk.")
                    return False

        print("Download complete.")
        return True
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error: {req_err}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    return False

def delete_file(args):
    index = (int(args[0][1:]) if args[0][0] == "#" else int(args[0])) - 1
    index_message_id = load_file_index()

    file_index = get_file_index()
    file_list = list(file_index.values())
    if index >= len(file_list):
        print("Invalid ID provided")
        return  # Exit if index is out of range

    file = file_list[index]
    message_ids = [i[0] for i in file["urls"]]
    print("Deleting...")

    # Initialize a flag to track deletion success
    all_deleted_successfully = True

    for i, message_id in enumerate(message_ids):
        try:
            response = requests.delete(
                f"{BASE_URL}{CHANNEL_ID}/messages/{message_id}", headers=headers
            )
            if response.status_code == 204:
                print(f"Message {message_id} deleted successfully.")
            else:
                print(f"Failed to delete message {message_id}: {response.status_code} {response.text}")
                all_deleted_successfully = False  # Update flag if any deletion fails
        except Exception as e:
            print(f"An error occurred while deleting message {message_id}: {e}")
            all_deleted_successfully = False  # Update flag for exceptions

        show_progress_bar(i + 1, len(message_ids))
        sleep(1)

    # Proceed with index update only if all deletions were successful
    if all_deleted_successfully:
        filename_to_delete = file["filename"].strip()
        if filename_to_delete in file_index:
            del file_index[filename_to_delete]
            update_file_index(index_message_id, file_index)
            print(f"Deleted {decode(filename_to_delete)}.")
        else:
            print(f"File {decode(filename_to_delete)} not found in index.")
    else:
        print("Not all messages were deleted successfully. Aborting index update.")