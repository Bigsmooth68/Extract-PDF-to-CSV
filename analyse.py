from date_utils import parse_date_texte, parse_date
import logging
import re


def extraire_section(text, start_pattern: str, end_pattern: str):
    section = []
    inside_section = False
    for line in text.splitlines():
        if start_pattern in line:
            inside_section = True
        if inside_section and end_pattern in line:
            section.append(line)
            return section
        if inside_section:
            section.append(line)
    return section


def analyse_livret(text):
    try:
        for line in text:
            match = re.search(r" (\d{7,}) ", line)  # au moins 7 chiffres
            if match:
                numero_compte = match[1]
                logging.debug(f"Nouveau compte trouvé: {numero_compte}")
            if " SOLDE" in line and "Réf" in line:
                match = re.search(r"AU (\d.+\d) (\d{1,3}(\.?\d{3})*,\d+)", line)
                date_solde = parse_date(match[1])
                solde = match[2]
                solde = solde.replace(".", "").replace(",", ".")
                solde = float(solde)
                return {"date": date_solde, "compte": numero_compte, "solde": solde}
    except Exception:
        logging.info(text)


def analyse_autres_comptes(text):
    for line in text:
        if "SITUATION DE VOS AUTRES COMPTES" in line:
            pattern = r"au (\d{1,2} \w+ \d{4})"
            date_str = re.search(pattern, line).group(1)
            date_solde = parse_date_texte(date_str)
        elif "LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE" in line:
            match = re.search(r"(\d.+\d) .+EUR .(\d{1,3}(\.?\d{3})*,\d+)", line)
            if match:
                numero_compte = match[1]
                solde = match[2]
                solde = solde.replace(".", "").replace(",", ".").replace("+", "")
                solde = float(solde)
                return {"date": date_solde, "compte": numero_compte, "solde": solde}
