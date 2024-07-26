import os
import logging
import requests
from math import ceil
from file_utils import get_size_format
from config import BASE_URL, CHANNEL_ID, headers, CHUNK_SIZE
from config import MAX_TERMINAL_WIDTH, PADDING, SIZE_COLUMN_WIDTH, ID_COLUMN_WIDTH

logging.basicConfig(level=logging.INFO)




def print_table_header():
    """
    Prints the table header for a list of files including their filename, size, and ID.
    Adjusts the column width based on the terminal size.

    Returns:
        tuple: A tuple containing the formatting string and the maximum width for the filename column.
    """
    # Constants for configuration

    terminal_width = os.get_terminal_size().columns
    max_width = min(MAX_TERMINAL_WIDTH, terminal_width) - PADDING
    filename_column_width = max_width - SIZE_COLUMN_WIDTH - ID_COLUMN_WIDTH - 6  # Adjust for spacing

    # Advanced string formatting for cleaner code
    header_format = f"{{:<{filename_column_width}}}   {{:<{SIZE_COLUMN_WIDTH}}}   {{:<{ID_COLUMN_WIDTH}}}"
    separator = f"{'-' * filename_column_width}   {'-' * SIZE_COLUMN_WIDTH}   {'-' * ID_COLUMN_WIDTH}"

    print(header_format.format("Filename", "Size", "ID"))
    print(separator)

    return header_format, filename_column_width

def print_table_row(number, filename, size, formatting, maxwidth):
    # Dynamically adjust the formatting string to include maxwidth for the filename
    dynamic_formatting = f"%-{maxwidth}s   %-10s   %-5s"
    # Ensure filename is truncated or padded to fit maxwidth
    formatted_filename = filename[:maxwidth]
    # Format the size using a helper function (assuming getSizeFormat exists)
    formatted_size = get_size_format(size)
    # Format the row number as a string with a hash prefix
    formatted_number = "#" + str(number)
    # Print the row using the dynamically adjusted formatting string
    print(dynamic_formatting % (formatted_filename, formatted_size, formatted_number))

def print_summary_line(max_width):
    """
    Prints a summary line based on the maximum width.

    Args:
        max_width (int): The maximum width for the summary line.
    """
    terminal_size = os.get_terminal_size()
    adjusted_width = min(max_width, terminal_size[0])
    print("-" * adjusted_width)

def get_total_chunks(size):
    """
    Calculates the total number of chunks needed for a given size.

    Args:
        size (int): The size of the file or data.

    Returns:
        int: The total number of chunks.
    """
    return ceil(size / CHUNK_SIZE)

def show_progress_bar(iteration, total):
    decimals = 2
    length = min(120, os.get_terminal_size()[0]) - 40
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * (iteration) // total)
    bar = f"{'#' * filled_length}{'-' * (length-filled_length - 1)}"
    print(f"\rProgress: {bar} {iteration}/{total} ({percent}%) Complete", end="")
    if iteration == total:
        print()

def fetch_message(message_id):
    """
    Fetches a message by its ID from a specified channel.

    Parameters:
        message_id (str): The ID of the message to fetch.

    Returns:
        dict: The message data as a dictionary if successful, None otherwise.
    """
    try:
        response = requests.get(f"{BASE_URL}{CHANNEL_ID}/messages/{message_id}", headers=headers)
        response.raise_for_status()  # This will raise an exception for 4XX/5XX responses
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while loading message {message_id}: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred while loading message {message_id}: {req_err}")
    return None

def download_content(download_url, file_handle, current_chunk, total_chunks):
    try:
        with requests.get(download_url, stream=True) as cdnResponse:
            cdnResponse.raise_for_status()  # Automatically handles bad responses

            for chunk in cdnResponse.iter_content(chunk_size=26214400): 
                if chunk:  # filter out keep-alive new chunks
                    file_handle.write(chunk)
                    show_progress_bar(current_chunk + 1, total_chunks)
                    
        print("Download complete.")
        return True
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred while downloading the file: {http_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred while downloading the file: {req_err}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return False