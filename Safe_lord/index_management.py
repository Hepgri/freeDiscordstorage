import json
import logging
import requests
import sys
from config import BASE_URL, CHANNEL_ID, INDEX_FILE, headers

def load_file_index():
    """
    Loads the index file from a specified channel and writes it to a local file.
    
    Returns:
        The ID of the last message if successful, None otherwise.
    """
    try:
        response = requests.get(f"{BASE_URL}{CHANNEL_ID}/messages?limit=1", headers=headers)
        response.raise_for_status()  # Raises an HTTPError if the response was an error
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred while loading index: {e}")
        sys.exit()

    messages = response.json()
    if not messages:
        logging.info("No messages found in the channel.")
        return None

    last_message = messages[0]
    if not last_message.get("attachments"):
        logging.info("No attachments found in the last message.")
        return None

    file = last_message["attachments"][0]
    filename = file["filename"]
    url = file["url"]

    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(filename, "w") as f:  # Use the actual filename from the attachment
            f.write(response.text)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download the index file: {e}")
        return None

    return last_message["id"]

def get_file_index():
    """
    Reads the index file and returns its content as a dictionary.

    Returns:
        dict: The content of the index file if it exists and is valid JSON, otherwise an empty dictionary.
    """
    try:
        with open(INDEX_FILE, "r") as f:
            data = f.read()
            return json.loads(data)
    except FileNotFoundError as e:
        logging.warning(f"File not found: {e}")
        return {}
    except json.JSONDecodeError as e:
        logging.warning(f"JSON decode error: {e}")
    return {}
    
def update_file_index(index_id, file_index):
    try:
        # Using context manager for file operations
        with open(INDEX_FILE, "w") as f:
            json.dump(file_index, f)

        # Ensure the file is closed after its content is read
        with open(INDEX_FILE, "rb") as file_content:
            files = {"": ("", file_content)}

            # Deleting existing index file on the channel
            if index_id:
                logging.info("Deleting old index file")
                response = requests.delete(f"{BASE_URL}{CHANNEL_ID}/messages/{index_id}", headers=headers)
                if response.status_code != 204:
                    logging.error(f"An error occurred while deleting old index file: {response.status_code} {response.text}")

            # Uploading new updated index file
            logging.info("Uploading new updated index file")
            response = requests.post(f"{BASE_URL}{CHANNEL_ID}/messages", headers=headers, files=files)
            if response.status_code != 200:
                logging.error(f"An error occurred while updating index: {response.text}")

            logging.info("Done.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")