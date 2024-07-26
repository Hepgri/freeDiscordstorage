def get_size_format(size):
    """
    Converts a file size in bytes to a human-readable format.

    Parameters:
    size (int): The size in bytes.

    Returns:
    str: The size in a human-readable format (e.g., "1.00 MB").
    """
    if size < 0:
        return "Size must be non-negative"

    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024.0:
            return "{:.2f} {}".format(size, unit)
        size /= 1024.0

    return "{:.2f} {}".format(size, "PB")  # Handle sizes in petabytes

def encode(string):
    """
    Encodes a string using the ROT13 cipher.

    Parameters:
    string (str): The input string to encode.

    Returns:
    str: The encoded string.
    """
    encoded = ""
    for char in string:
        if char.isalpha():  # Check if the character is a letter
            # Determine the start based on the case (upper or lower)
            start = ord('a') if char.islower() else ord('A')
            # Apply ROT13 by shifting 13 places and use modulo to wrap around
            offset = (ord(char) - start + 13) % 26
            encoded += chr(start + offset)
        else:
            # Non-alphabetic characters are added unchanged
            encoded += char
    return encoded

def decode(encoded):
    """
    Decodes a string encoded with the ROT13 cipher.

    Parameters:
    encoded (str): The encoded string to decode.

    Returns:
    str: The decoded string.
    """
    decoded = ""
    for char in encoded:
        if char.isalpha():  # Check if the character is a letter
            # Determine the start based on the case (upper or lower)
            start = ord('a') if char.islower() else ord('A')
            # Apply ROT13 by shifting 13 places back and use modulo to wrap around
            offset = (ord(char) - start - 13) % 26
            decoded += chr(start + offset)
        else:
            # Non-alphabetic characters are added unchanged
            decoded += char
    return decoded