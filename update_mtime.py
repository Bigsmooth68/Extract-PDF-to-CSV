import os, datetime, time
from pathlib import Path

dir_path = Path('.\\pdf')
for file in sorted(dir_path.glob('*.pdf')):
    file_name = file.name
    date_string = file_name.rsplit(' ', 1)[1].replace('.pdf','')
    print(date_string)
    dt = datetime.datetime.strptime(date_string,'%Y-%m-%d')
    unix_time = time.mktime(dt.timetuple())
    os.utime(file, (unix_time, unix_time))