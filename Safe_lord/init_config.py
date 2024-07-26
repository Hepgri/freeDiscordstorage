import os
import sys
from file_operations import list_files, upload_file, download_file, delete_file, find_file

def init():
    commands = [
        {
            "alias": ["-l", "-list"],
            "function": list_files,
            "minArgs": 0,
            "syntax": "-l",
            "desc": "Lists all the file information that has been uploaded to the server.",
        },
        {
            "alias": ["-u", "-upload"],
            "function": upload_file,
            "minArgs": 1,
            "syntax": "-u path/to/file",
            "desc": "Uploads a file to the server. The full file directory is taken in for the argument.",
        },
        {
            "alias": ["-d", "-download"],
            "function": download_file,
            "minArgs": 1,
            "syntax": "-d #ID",
            "desc": "Downloads a file from the server. An #ID is taken in as the file identifier. Provide multiple ids separated by space to download multiple files",
        },
        {
            "alias": ["-del", "-delete"],
            "function": delete_file,
            "minArgs": 1,
            "syntax": "-del #ID",
            "desc": "Deletes a file from the server. An #ID is taken in as the file identifier",
        },
        {
            "alias": ["-f", "-find"],
            "function": find_file,
            "minArgs": 1,
            "syntax": "-f text_to_search",
            "desc": "Finds files with matching text",
        },
    ]


    try:
        f = open(".env", "r")
        TOKEN = f.readline().split("=")[1].strip()  # This now correctly updates the global variable
        CHANNEL_ID = f.readline().split("=")[1].strip()  
        f.close()
    except FileNotFoundError or IndexError:
        TOKEN = input("Enter bot token to be used: ")  
        CHANNEL_ID = input("Enter discord channel id to be used to store files: ")  
        f = open(".env", "w")
        f.write(f"TOKEN={TOKEN}\nCHANNEL_ID={CHANNEL_ID}")
        f.close()


    args = sys.argv
    if len(args) == 1:
        print(f"Usage: python {os.path.basename(__file__)} [command] (target)")
        print("COMMANDS:")
        for cmd in commands:
            print("[%s] :: %s" % (", ".join(cmd["alias"]), cmd["desc"]))
        sys.exit()
    else:
        if not TOKEN:
            print("No token provided")
            sys.exit()
        if not CHANNEL_ID:
            print("Not channel id provided")
            sys.exit()

    for cmd in commands:
        if args[1] in cmd["alias"]:
            if len(args) < cmd["minArgs"] + 2:
                print("Description: ", cmd["desc"])
                print("Syntax: python", sys.argv[0], cmd["syntax"])
                sys.exit()
            else:
                cmd["function"](args[2:])
            break


init()
