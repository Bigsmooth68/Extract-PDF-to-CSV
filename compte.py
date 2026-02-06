import pandas as pd
from date_utils import aligner_date
import logging
from datetime import datetime


class compte:
    lignes = None
    colonne_valeur = None

    def __init__(self, colonne_valeur="solde"):
        # initialise un dataframe vide
        self.colonne_valeur = colonne_valeur
        self.lignes = pd.DataFrame(columns=["date", "compte", colonne_valeur, "type_compte"])

    def nb_lignes(self):
        len1 = len(self.lignes) if self.lignes is not None else 0
        return len1

    def ajout_solde(
        self,
        date_solde: datetime,
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
            type_compte.replace("'", "''"),
        ]

    def generer_insert(self, table):
        """
        Créer un fichier sql avec les INSERT correspondant aux lignes de solde
        """
        if len(self.lignes) > 0:
            self.lignes.drop_duplicates(inplace=True)
            with open(f"out/{table}.sql", "w", encoding="utf-8") as f:
                f.writelines(f"-- TRUNCATE TABLE {table};\n###\n")
                for index, row in self.lignes.iterrows():
                    date_solde = row["date"].strftime("%Y-%m-%d")
                    numero_compte = row["compte"]
                    solde = row[self.colonne_valeur]
                    type_compte = row["type_compte"]
                    f.writelines(
                        f"INSERT INTO {table} (date, compte, {self.colonne_valeur}, type_compte) VALUES (TO_DATE('{date_solde}','YYYY-MM-DD'), '{numero_compte}', '{solde}', '{type_compte}');\n"
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

    def analyse(self):
        pass
