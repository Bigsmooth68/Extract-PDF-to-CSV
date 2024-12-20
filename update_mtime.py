import os, datetime, time
from pathlib import Path

dir_path = Path('.\\pdf')
count = 0
for file in sorted(dir_path.glob('*.pdf')):
    print('.', end='')
    date_string = file.name.rsplit(' ', 1)[1].replace('.pdf','')
    dt = datetime.datetime.strptime(date_string,'%Y-%m-%d')
    unix_time = time.mktime(dt.timetuple())
    os.utime(file, (unix_time, unix_time))
    count += 1

print(f'\nFiles processed: {count}')
