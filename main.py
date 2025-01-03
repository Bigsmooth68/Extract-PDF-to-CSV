# importing required classes
from pathlib import Path
import logging
import sys
import argparse
import os

# extra modules
from compte import compte

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
    parser.add_argument(
        "-p",
        "--pea",
        action="store_true",
        help="Limite l'extraction aux relevés des PEA",
    )
    parser.add_argument(
        "-l", "--livret", action="store_true", help="Limite l'extraction aux livrets"
    )
    parser.add_argument(
        "-o",
        "--out",
        choices=["csv", "sql"],
        default="sql",
        help="Choix du format d'export",
    )
    args = parser.parse_args()

    flag_pea = True
    flag_livret = True
    if args.pea:
        flag_livret = False
    if args.livret:
        flag_pea = False

    epargne = compte()
    pea = compte()

    for dir in ["out", "cache"]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    dir_path = Path(".\\pdf")

    fichiers_pea = []
    fichiers_livret = []

    # Selection des fichiers
    for file in sorted(dir_path.glob("*.pdf")):
        if "EUROCOMPTE" in file.name:
            # convertir_pdf(file)
            # On ignore le compte courant pour l'instant
            continue
        if "Portefeuille valoris" in file.name and flag_pea:
            fichiers_pea.append(file)
        else:
            if flag_livret:
                fichiers_livret.append(file)

    logging.info(
        f"Fichiers sélectionnés: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)}"
    )

    for fichier in fichiers_pea:
        pea.analyse_pea(fichier)

    for fichier in fichiers_livret:
        epargne.analyse_livret(fichier)

    logging.info(f"Lignes générées: {pea.nb_lignes() + epargne.nb_lignes()}")

    epargne.fill_missing_months()

    if args.out == "sql":
        epargne.generer_insert("epargne")
        pea.generer_insert("pea")
    else:
        epargne.generer_csv("epargne.csv")
        pea.generer_csv("pea.csv")


if __name__ == "__main__":
    main()
