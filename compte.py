import pandas as pd
from date_utils import aligner_date
import logging
import re
from date_utils import parse_date
from analyse import (
    extraire_section,
    analyse_livret,
    analyse_autres_comptes,
    convertir_pdf,
    formater_solde,
)


class compte:
    lignes = None

    def __init__(self):
        self.lignes = pd.DataFrame(columns=["date", "compte", "solde", "type_compte"])

    def nb_lignes(self):
        len1 = len(self.lignes) if self.lignes is not None else 0
        return len1

    def ajout_solde(
        self,
        date_solde,
        numero_compte: str,
        type_compte: str,
        solde: str,
        aligne_date: bool = True,
    ):
        """
        Ajout d'une ligne solde
        """
        if aligne_date:
            date_solde = aligner_date(date_solde)

        self.lignes.loc[len(self.lignes)] = [
            date_solde,
            numero_compte,
            solde,
            type_compte,
        ]

    def generer_insert(self, table):
        """
        Créer un fichier sql avec les INSERT correspondant aux lignes de solde
        """
        if len(self.lignes) > 0:
            self.lignes.drop_duplicates(inplace=True)
            with open(f"out/{table}.sql", "w", encoding="utf-8") as f:
                f.writelines(f"TRUNCATE TABLE {table};\n###\n")
                for index, row in self.lignes.iterrows():
                    date_solde = row["date"].strftime("%Y-%m-%d")
                    numero_compte = row["compte"]
                    solde = row["solde"]
                    type_compte = row["type_compte"]
                    f.writelines(
                        f"INSERT INTO {table} (date, compte, solde, type_compte) VALUES (TO_DATE('{date_solde}','YYYY-MM-DD'), '{numero_compte}', '{solde}', '{type_compte}');\n"
                    )

    def generer_csv(self, fichier):
        """
        Créer un fichier csv avec les lignes de solde
        """
        if len(self.lignes) > 0:
            logging.debug(self.lignes)
            self.lignes.to_csv(f"out/{fichier}", index=False)

    def fill_missing_months(self):
        """
        Remplit les mois manquants avec le dernier solde connu.
        """
        count = 0
        extras = self.lignes.drop(self.lignes.index)
        # Récupère tous les comptes
        self.lignes.sort_values(["date", "compte"], ascending=True, inplace=True)

        comptes = self.lignes["compte"].unique()

        for compte in comptes:
            soldes = self.lignes[self.lignes["compte"] == compte]

            date_range = pd.date_range(
                start=soldes["date"].min(), end=soldes["date"].max(), freq="MS"
            )
            # Pour chaque date manquante, trouve le dernier solde connu
            for date in date_range:
                if date not in soldes["date"].values:
                    # Trouve le dernier solde connu avant cette date
                    last_known = soldes[soldes["date"] < date].iloc[-1]

                    extras.loc[len(extras)] = [
                        date,
                        compte,
                        float(last_known["solde"]),
                        "ajout",
                    ]
                    count += 1

        logging.info(f"Lignés complétées: {count}")

        self.lignes = pd.concat([self.lignes, extras])

        self.lignes.sort_values(["date", "compte"], ascending=True, inplace=True)

    def analyse_pea(self, fichier):
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

    def analyse_livret(self, fichier):
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        compte_solde = 0
        logging.info(f"Analyse du fichier livrets: {fichier.name}")

        contenu = convertir_pdf(fichier)

        livret = extraire_section(contenu, "LIVRET BLEU", "Réf")
        solde = analyse_livret(livret)
        if solde:
            self.ajout_solde(solde["date"], solde["compte"], "LIVRET", solde["solde"])
            compte_solde += 1

        livret = extraire_section(
            contenu, "LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE", "Réf"
        )
        solde = analyse_livret(livret)
        if solde:
            self.ajout_solde(solde["date"], solde["compte"], "LDD", solde["solde"])
            compte_solde += 1

        # dans le cas ou il n'y a pas de mouvement, le compte est dans la section autres comptes
        livret = extraire_section(contenu, "SITUATION DE VOS AUTRES COMPTES", "Réf :")
        solde = analyse_autres_comptes(livret)
        if solde:
            self.ajout_solde(
                solde["date"],
                solde["compte"],
                "LDD",
                solde["solde"],
            )
        logging.info(f"Ligne livrets trouvées: {compte_solde}")
