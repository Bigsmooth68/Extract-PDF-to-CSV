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
from compte_csv import compte_csv

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
        "-csv",
        action="store_true",
        help="Limite l'analyse aux relevés des comptes en csv",
    )
    parser.add_argument("-f", "--filtre", help="Filtre le nom des fichiers traités")
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
    flag_csv = False

    if args.cc:
        flag_livret = False
        flag_pea = False
    if args.pea:
        flag_livret = False
        flag_cc = False
    if args.livret:
        flag_cc = False
        flag_pea = False
    if args.csv:
        flag_cc = False
        flag_pea = False
        flag_livret = False
        flag_csv = True

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Création des comptes
    epargne = livret()
    plan = pea()
    cc = compte_courant()

    for dir in ["out", "cache"]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    dir_path = Path(".\\in")

    fichiers_cc = []
    fichiers_pea = []
    fichiers_livret = []

    if not flag_csv:
        pdf_files = dir_path.glob("*.pdf")

        filtre = args.filtre

        if filtre:
            filtered_pdf_files = [f for f in dir_path.glob("*.pdf") if filtre in f.name]
        else:
            filtered_pdf_files = pdf_files

        # Selection des fichiers
        for file in sorted(filtered_pdf_files):
            logging.debug(f"Fichier trouvé: {file.name}")
            if flag_cc and ("EUROCOMPTE" in file.name): # or "COMPTEDEDEPOTS" in file.name):
                fichiers_cc.append(file)
            elif flag_pea and "Portefeuille valoris" in file.name:
                fichiers_pea.append(file)
            elif flag_livret and (
                "LIVRET" in file.name or "COMPTE COURANT EN CHF" in file.name
            ):
                fichiers_livret.append(file)
        logging.info(
            f"Fichiers sélectionnés: PEA {len(fichiers_pea)} - Livrets {len(fichiers_livret)} - Compte Courant {len(fichiers_cc)}"
        )
        # Pause
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            input("Appuyez sur Entrée pour continuer...")
            
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

        if filtre:
            exit()

    else:
        csv_files = dir_path.glob("*.csv")

        # traitement des csv
        csv = compte_csv()
        for file in sorted(csv_files):
            csv.analyse(file)
            print(csv)
            csv.generer_insert(file.name[:-4])


    if args.out == "sql":

        load_dotenv()
        DB_URL = os.environ.get("DB_URL")
        engine = create_engine(url=DB_URL)
        logging.info("Connecté à la base de données")
        
        if flag_livret:
            epargne.generer_sql(engine, "epargne")
        if flag_pea:
            plan.generer_sql(engine, "pea")
        if flag_cc:
            cc.lignes["categorie"] = None
            cc.generer_sql(engine, "cc")
        if flag_csv:
            csv.generer_sql(engine, "csv")

    else:
        if flag_livret:
            epargne.generer_csv("epargne.csv")
        if flag_pea:
            plan.generer_csv("pea.csv")
        if flag_cc:
            cc.generer_csv("cc.csv")


if __name__ == "__main__":
    main()
