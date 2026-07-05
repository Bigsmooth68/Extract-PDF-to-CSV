from compte import compte
import logging
import re
from date_utils import parse_date
import pandas as pd

from analyse import (
    extraire_section,
    convertir_pdf,
    formater_solde,
)


class compte_csv(compte):
    def analyse(self_, fichier):
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        compte_solde = 0
        logging.info(f"Analyse du fichier CSV: {fichier.name}")

        numero_compte = fichier.name[:-4]

        # Lecture du fichier csv
        df = pd.read_csv(fichier, sep=",", encoding="utf-8")

        for line in df.itertuples(index=False):
            logging.info(f"Analyse de la ligne: {line}")

            date_solde = pd.Timestamp(line.date)

            self_.ajout_solde(
                date_solde, numero_compte, "AV", line.solde, aligne_date=False
            )
            compte_solde += 1
        logging.info(f"Lignes CSV trouvées: {compte_solde}")

        self_.analyse_finie(fichier)

    def __repr__(self):
        return f"{self.lignes}"
