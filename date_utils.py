import datetime


def parse_date_texte(str) -> datetime:
    """
    Créer un objet datetime à partir d'une chaîne date "JJ MOIS AAAA"
    Le mois est en toute lettre
    """
    date_obj = datetime.datetime.strptime(str, "%d %B %Y")
    return date_obj


def parse_date(date_str: str) -> datetime:
    """
    Analyse la chaine contenant une date.

    S'adapte au format (AAAA-MM-JJ ou JJ/MM/AAAA)
    """
    if date_str[:4].isdigit():
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.datetime.strptime(date_str, "%d/%m/%Y")
    return dt


def aligner_date(dt: datetime) -> datetime:
    """
    Retourne le premier jour du mois de la date fournie si le jour est inférieur à 25.

    Sinon, le premier jour du mois suivant la date.
    """
    if dt.day > 25:
        new_date = (dt.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    else:
        new_date = dt.replace(day=1)

    return new_date
