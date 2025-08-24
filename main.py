# importing required classes
from pathlib import Path
import logging
import sys
import argparse
import os

from pea import pea
from livret import livret

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
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Augmenter le niveau de log"
    )
    args = parser.parse_args()

    flag_pea = True
    flag_livret = True
    if args.pea:
        flag_livret = False
    if args.livret:
        flag_pea = False

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Création des comptes
    epargne = livret()
    plan = pea()

    for dir in ["out", "cache"]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    dir_path = Path(".\\pdf")

    fichiers_cc = []
    fichiers_pea = []
    fichiers_livret = []

    # Selection des fichiers
    for file in sorted(dir_path.glob("*.pdf")):
        if "EUROCOMPTE" in file.name:
            fichiers_cc.append(file)
        if "Portefeuille valoris" in file.name and flag_pea:
            fichiers_pea.append(file)
        else:
            if flag_livret:
                fichiers_livret.append(file)

    logging.info(
        f"Fichiers sélectionnés: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)} - Compte Courant {len(fichiers_cc)}"
    )

    for fichier in fichiers_pea:
        plan.analyse(fichier)

    for fichier in fichiers_livret:
        epargne.analyse(fichier)

    logging.info(f"Lignes générées: {plan.nb_lignes() + epargne.nb_lignes()}")

    epargne.fill_missing_months()

    if args.out == "sql":
        epargne.generer_insert("epargne")
        plan.generer_insert("pea")
    else:
        epargne.generer_csv("epargne.csv")
        plan.generer_csv("pea.csv")


if __name__ == "__main__":
    main()
