import os
from screeninfo import get_monitors
import re
import requests

# strip html from string
def striphtml(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

# get the correct path to be given
# to pywebview.load_url()
def get_full_path(filename):
    return 'file://' + os.path.abspath(filename)

# get monitor width and height
def get_monitor_size():
    monitor = get_monitors()[0]
    return (monitor.width, monitor.height)

# store content inside a file in
# the static folder
def store_static(filename, content):
    with open("static/" + filename, 'w') as file:
        file.write(content)

# download a file to a specific path
def download_file(url, path_to_save):
    response = requests.head(url)

    if "Content-Disposition" in response.headers:
        content_disposition = response.headers["Content-Disposition"]
        filename_index = content_disposition.find("filename=")
        filename = content_disposition[filename_index + len("filename="):]
        filename = filename.strip('"')
    else:
        filename = url.split("/")[-1]
                        
    response = requests.get(url)
    with open(os.path.join(path_to_save, filename), "wb") as file:
        file.write(response.content)