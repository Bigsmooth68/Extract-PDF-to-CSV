# importing required classes
from pypdf import PdfReader
from pathlib import Path
import re
from compte import compte
from date_utils import parse_date_texte, parse_date
import logging
import sys
import argparse

import locale

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")


def extract_sections(text, start_pattern: str, end_pattern: str):
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


##############


def main():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(prog="Analyse des extraits de comptes Crédit Mutuel")
    parser.add_argument('-p', '--pea', action='store_true')
    args = parser.parse_args()

    flag_pea = True
    flag_livret = True
    if args.pea:
        flag_livret = False

    epargne = compte()
    pea = compte()
    lines_found = 0

    dir_path = Path(".\\pdf")

    fichiers_pea = []
    fichiers_livret = []

    # Selection des fichiers
    for file in sorted(dir_path.glob("*.pdf")):
        if "Portefeuille valoris" in file.name:
            if flag_pea:
                fichiers_pea.append(file)
        else:
            if flag_livret:
                fichiers_livret.append(file)

    logging.info(f"Fichiers sélectionnées: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)}")

    for file in fichiers_pea:
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        logging.info(f"Analyse du fichier {file.name}")
        reader = PdfReader(file)

        numero_compte = None
        count_page = 1

        for page in reader.pages:
            logging.debug(
                f"****************** NEW PAGE {count_page} ******************"
            )
            lines_found_in_page = 0
            if "EUROCOMPTE" in file.name:
                # On ignore le compte courant pour l'instant
                continue

            content = page.extract_text(extraction_mode="plain")

            match = re.search(r" (000\d+) \d\d au (.+).pdf", file.name)
            numero_compte = match[1]
            date_solde = parse_date(match[2])
            texte_pea = extract_sections(content, "FISCALITE DU PEA OUVERT", "Plus/Moins value latente")
            print(texte_pea)
            exit(0)
            for line in content.splitlines():
                match = re.search(
                    r"Valorisation titres (\d{1,3}( ?\d{3})*,\d+)", line
                )
                if match:
                    solde = match[1].replace(" ", "").replace(",", ".")
                    pea.ajout_solde(date_solde, numero_compte, "PEA", solde)
                    lines_found += 1
                    lines_found_in_page += 1

        for file in fichiers_livret:
            logging.debug(
            "*************************** NEW FILE ***************************"
            )
            logging.info(f"Analyse du fichier {file.name}")
            reader = PdfReader(file)

            numero_compte = None
            count_page = 1

            for page in reader.pages:

                livret = extract_sections(content, "LIVRET BLEU", "Réf")
                ldd = extract_sections(
                    content, "SITUATION DE VOS AUTRES COMPTES", "Sous "
                )

                solde = analyse_livret(livret)
                if solde:
                    epargne.ajout_solde(
                        solde["date"], solde["compte"], "LIVRET", solde["solde"]
                    )
                    lines_found += 1
                    lines_found_in_page += 1
                solde_ldd = analyse_autres_comptes(ldd)
                if solde_ldd:
                    epargne.ajout_solde(
                        solde_ldd["date"],
                        solde_ldd["compte"],
                        "LDD",
                        solde_ldd["solde"],
                    )
                    lines_found += 1
                    lines_found_in_page += 1
            logging.debug(
                f"Processing {file} - page {count_page} - count {lines_found_in_page}"
            )
            count_page += 1

    logging.info(f"Lignes générées: {lines_found}")

    epargne.fill_missing_months()

    epargne.generate_insert("epargne")

    pea.generate_insert("pea")


if __name__ == "__main__":
    main()
