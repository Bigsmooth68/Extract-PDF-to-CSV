from date_utils import parse_date_texte, parse_date
import logging
import re
import os
from pypdf import PdfReader


def convertir_pdf(file) -> list[str]:
    """
    Conversion du pdf avec gestion du cache
    """
    fichier_text = "cache/" + file.name.replace(".pdf", ".txt")

    if os.path.isfile(fichier_text):
        with open(fichier_text, "r", encoding="utf-8") as f:
            contenu = f.read()

    else:
        reader = PdfReader(file)
        contenu = ""
        for page in reader.pages:
            contenu += page.extract_text(extraction_mode="plain")

        with open(fichier_text, "w", encoding="utf-8") as f:
            f.writelines(contenu)

    return contenu


def extraire_section(text, start_pattern: str, end_pattern: str):
    """
    Selection des lignes entre start_pattern et end_pattern
    """
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
    """
    Analyse des lignes correspondant au livret Bleu
    """
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
    """
    Analyse des lignes correspondant aux livrets Bleu, LDD dans la section "autres comptes"
    """
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


def formater_solde(str):
    """
    Conversion d'une chaine contenant un solde (1 433,21) vers une chaine nombre (1433.21)
    """
    return str.replace(" ", "").replace(",", ".")
