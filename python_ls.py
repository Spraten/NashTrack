#
import os 
import datetime

GREEN = "\033[32m"
CYAN = "\033[36m"
RESET = "\033[0m"

dir_items = os.listdir(path='.')
users_path = "."
today = datetime.datetime.now().date()


def color_time(date_obj, text):
    now = datetime.datetime.now()

    if date_obj.date() == today and date_obj.hour == now.hour:
        return f"{CYAN}{text}{RESET}"

    if date_obj.date() == today:
        return f"{GREEN}{text}{RESET}"

    return text

print("----------------------------")
print(datetime.datetime.now())
print(os.getcwd())

print("----------------------------")
# Path logic 
if users_path:
    working_path = users_path
else:
    working_path = "."
print(f"Working with path: {working_path}")
for item in dir_items:
    filestats = statinfo = os.stat(item)
    #atime= filestats.st_atime
    #mtime= filestats.st_mtime
    #ctime= filestats.st_ctime
    # Convert timestamps to human-readable format
    atime_obj = datetime.datetime.fromtimestamp(filestats.st_atime)
    mtime_obj = datetime.datetime.fromtimestamp(filestats.st_mtime)
    ctime_obj = datetime.datetime.fromtimestamp(filestats.st_ctime)

    atime = atime_obj.strftime('%Y-%m-%d %H:%M:%S')
    mtime = mtime_obj.strftime('%Y-%m-%d %H:%M:%S')
    ctime = ctime_obj.strftime('%Y-%m-%d %H:%M:%S')

    atime_column = color_time(atime_obj, f"{atime:25}")
    mtime_column = color_time(mtime_obj, f"{mtime:25}")
    ctime_column = color_time(ctime_obj, f"{ctime:25}")

    print(f"{item:30} atime: {atime_column} mtime: {mtime_column} ctime: {ctime_column}")



print("----------------------------")



