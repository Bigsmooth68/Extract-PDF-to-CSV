import datetime

def parse_date_texte(str):
    date_obj = datetime.datetime.strptime(str, "%d %B %Y")
    return date_obj

def parse_date(str):
    if str[:4].isdigit():
        dt = datetime.datetime.strptime(str,'%Y-%m-%d')
    else:
        dt = datetime.datetime.strptime(str,'%d/%m/%Y')
    return dt

def aligner_date(dt):
    if dt.day > 25:
        new_date = (dt.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    else:
        new_date = dt.replace(day=1)

    return new_date