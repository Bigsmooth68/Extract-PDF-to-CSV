# importing required classes
from pathlib import Path
import logging
import sys
import argparse
import os
import tomllib
from dotenv import load_dotenv
from sqlalchemy import create_engine
from pea import pea
from livret import livret
from compte_courant import compte_courant

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
        "-cc",
        action="store_true",
        default=False,
        help="Limite l'extraction aux relevés des comptes courants",
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
    parser.add_argument(
        "-un", action="store_true", help="Traite le premier fichier uniquement"
    )
    parser.add_argument(
        "-nf",
        action="store_true",
        help="Désactive le filtrage des mouvements internes à la banque",
    )
    args = parser.parse_args()

    flag_cc = True
    flag_pea = True
    flag_livret = True

    if args.cc:
        flag_livret = False
        flag_pea = False
    if args.pea:
        flag_livret = False
        flag_cc = False
    if args.livret:
        flag_cc = False
        flag_pea = False

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Création des comptes
    epargne = livret()
    plan = pea()
    cc = compte_courant()

    for dir in ["out", "cache"]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    dir_path = Path(".\\pdf")

    fichiers_cc = []
    fichiers_pea = []
    fichiers_livret = []

    files = dir_path.glob("*.pdf")

    # Selection des fichiers
    for file in sorted(files):
        if flag_cc and "EUROCOMPTE" in file.name:
            fichiers_cc.append(file)
        elif flag_pea and "Portefeuille valoris" in file.name:
            fichiers_pea.append(file)
        elif flag_livret and ("LIVRET" in file.name or "COMPTE COURANT EN CHF" in file.name):
            fichiers_livret.append(file)

    logging.info(
        f"Fichiers sélectionnés: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)} - Compte Courant {len(fichiers_cc)}"
    )
    if args.un:
        if flag_cc:
            fichiers_cc = [fichiers_cc[0]]
        if flag_livret:
            fichiers_livret = [fichiers_livret[0]]
        if flag_pea:
            fichiers_pea = [fichiers_pea[0]]

    if flag_cc:
        for fichier in fichiers_cc:
            cc.analyse(fichier)

    if not args.nf:
        with open("config.toml", "rb") as cf:
            config = tomllib.load(cf)
            cc.filtrer(config["filtre"])

    cc.factoriser(config["groupement"])

    if flag_pea:
        for fichier in fichiers_pea:
            plan.analyse(fichier)

    if flag_livret:
        for fichier in fichiers_livret:
            epargne.analyse(fichier)

    logging.info(
        f"Lignes générées: {plan.nb_lignes() + epargne.nb_lignes() + cc.nb_lignes()}"
    )

    epargne.fill_missing_months()

    load_dotenv()
    DB_URL = os.environ.get("DB_URL")
    engine = create_engine(url=DB_URL)

    if args.out == "sql":
        epargne.generer_sql(engine, "epargne")
        plan.generer_sql(engine, "pea")
        cc.generer_sql(engine, "cc")
    else:
        epargne.generer_csv("epargne.csv")
        plan.generer_csv("pea.csv")
        cc.generer_csv("cc.csv")


if __name__ == "__main__":
    main()
