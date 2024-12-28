# importing required classes
from pathlib import Path
import re
import logging
import sys
import argparse
import os

# extra modules
from compte import compte
from date_utils import parse_date
from analyse import (
    extraire_section,
    analyse_livret,
    analyse_autres_comptes,
    convertir_pdf,
)

import locale

locale.setlocale(locale.LC_ALL, "fr_FR.UTF-8")


def main():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        prog="Analyse des extraits de comptes Crédit Mutuel"
    )
    parser.add_argument("-p", "--pea", action="store_true")
    parser.add_argument("-l", "--livret", action="store_true")
    args = parser.parse_args()

    flag_pea = True
    flag_livret = True
    if args.pea:
        flag_livret = False
    if args.livret:
        flag_pea = False

    epargne = compte()
    pea = compte()
    lines_found = 0

    for dir in ["out", "cache"]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    dir_path = Path(".\\pdf")

    fichiers_pea = []
    fichiers_livret = []

    # Selection des fichiers
    for file in sorted(dir_path.glob("*.pdf")):
        if "EUROCOMPTE" in file.name:
            # On ignore le compte courant pour l'instant
            continue
        if "Portefeuille valoris" in file.name:
            if flag_pea:
                fichiers_pea.append(file)
        else:
            if flag_livret:
                fichiers_livret.append(file)

    logging.info(
        f"Fichiers sélectionnés: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)}"
    )

    for file in fichiers_pea:
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        logging.info(f"Analyse du fichier {file.name}")
        contenu = convertir_pdf(file)

        numero_compte = None

        match = re.search(r" (000\d+) \d\d au (.+).pdf", file.name)
        numero_compte = match[1]
        date_solde = parse_date(match[2])
        texte_pea = extraire_section(
            contenu, "FISCALITE DU PEA OUVERT", "Plus/Moins value latente"
        )

        for line in contenu.splitlines():
            match = re.search(r"Valorisation titres (\d{1,3}( ?\d{3})*,\d+)", line)
            if match:
                solde = match[1].replace(" ", "").replace(",", ".")
                pea.ajout_solde(date_solde, numero_compte, "PEA", solde)
                lines_found += 1

    for file in fichiers_livret:
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        logging.info(f"Analyse du fichier {file.name}")

        contenu = convertir_pdf(file)
        numero_compte = None

        livret = extraire_section(contenu, "LIVRET BLEU", "Réf")
        ldd = extraire_section(contenu, "SITUATION DE VOS AUTRES COMPTES", "Sous ")

        solde = analyse_livret(livret)
        if solde:
            epargne.ajout_solde(
                solde["date"], solde["compte"], "LIVRET", solde["solde"]
            )
            lines_found += 1
        solde_ldd = analyse_autres_comptes(ldd)
        if solde_ldd:
            epargne.ajout_solde(
                solde_ldd["date"],
                solde_ldd["compte"],
                "LDD",
                solde_ldd["solde"],
            )
            lines_found += 1

    logging.info(f"Lignes générées: {lines_found}")

    epargne.fill_missing_months()

    epargne.generate_insert("epargne")

    pea.generate_insert("pea")


if __name__ == "__main__":
    main()
