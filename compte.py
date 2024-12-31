import pandas as pd
from date_utils import aligner_date
import logging


class compte:
    lignes = None
    extras = None

    def __init__(self):
        self.lignes = pd.DataFrame(columns=["date", "compte", "solde", "type_compte"])
        self.extras = pd.DataFrame(columns=["date", "compte", "solde", "type_compte"])

    def ajout_solde(self, date_solde, numero_compte: str, type_compte: str, solde: str, aligner_date: bool=True):
        if aligner_date:
            date_solde = aligner_date(date_solde)

        self.lignes.loc[len(self.lignes)] = [
            date_solde,
            numero_compte,
            solde,
            type_compte,
        ]

    def generate_insert(self, table):
        if len(self.lignes) > 0:
            self.lignes.drop_duplicates(inplace=True)
            with open(f"out/{table}.sql", "w", encoding="utf-8") as f:
                for index, row in self.lignes.iterrows():
                    date_solde = row["date"].strftime("%Y-%m-%d")
                    numero_compte = row["compte"]
                    solde = row["solde"]
                    type_compte = row["type_compte"]
                    f.writelines(
                        f"INSERT INTO {table} (date, compte, solde, type_compte) VALUES (TO_DATE('{date_solde}','YYYY-MM-DD'), '{numero_compte}', '{solde}', '{type_compte}');\n"
                    )

    def fill_missing_months(self):
        """Remplit les mois manquants avec le dernier solde connu."""
        count = 0
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

                    self.extras.loc[len(self.extras)] = [
                        date,
                        compte,
                        float(last_known["solde"]),
                        "ajout",
                    ]
                    count += 1

        logging.info(f"Lignés complétées: {count}")

        self.lignes = pd.concat([self.lignes, self.extras])
