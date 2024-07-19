import glob
import os.path

folder_path = os.path.expanduser(r"~/workspace/studypython")
file_type = r"/*.txt"
files = glob.glob(folder_path + file_type)
max_file = max(files, key=os.path.getctime)

print(max_file)
