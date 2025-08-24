from compte import compte
import logging
import re
from date_utils import parse_date

from analyse import (
    extraire_section,
    convertir_pdf,
    formater_solde,
)


class pea(compte):
    def analyse(self, fichier):
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        compte_solde = 0
        logging.info(f"Analyse du fichier PEA: {fichier.name}")
        contenu = convertir_pdf(fichier)

        numero_compte = None

        match = re.search(r" (000\d+) \d\d au (.+).pdf", fichier.name)
        numero_compte = match[1]
        date_solde = parse_date(match[2])
        extract_fiscalite = extraire_section(
            contenu, "Valorisation titres (1)", "Plus/Moins value latente"
        )

        logging.debug(extract_fiscalite)
        valeurs_pea = [
            "Valorisation titre",
            "Solde espece",
            "Mouvements en cours",
            "Valorisation totale",
            "Cumul versements",
            "Cumul versements remboursés",
            "Plus/Moins value",
        ]
        if len(extract_fiscalite) > 7:
            midpoint = 3
            valeurs_pea = (
                valeurs_pea[0:midpoint] + ["Désinvestissement"] + valeurs_pea[midpoint:]
            )

        for index, type_compte in enumerate(valeurs_pea):
            match = re.search(
                r"\b(\d{1,3}(?:\s\d{3})*,\d{2})\b", extract_fiscalite[index]
            )
            valeur = formater_solde(match[1])
            self.ajout_solde(
                date_solde, numero_compte, type_compte, valeur, aligne_date=False
            )
            compte_solde += 1
        logging.info(f"Lignes PEA trouvées: {compte_solde}")
