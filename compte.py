import pandas as pd
from date_utils import *

class compte:
    lignes = None
    extras = None

    def __init__(self):
        self.lignes = pd.DataFrame(columns=['date', 'compte', 'solde', 'type_compte'])
        self.extras = pd.DataFrame(columns=['date', 'compte', 'solde', 'type_compte'])

    def ajout_solde(self, date_solde: str, numero_compte: str, type_compte: str, solde: str):
        date_solde = aligner_date(parse_date(date_solde))
        self.lignes.loc[len(self.lignes)] = [date_solde, numero_compte, solde, type_compte]

    def generate_insert(self, table):
        with open(f'out/{table}.sql', 'w') as f:
            for index, row in self.lignes.iterrows():
                date_solde = aligner_date(row['date']).strftime('%Y-%m-%d')
                numero_compte = row['compte']
                solde = row['solde']
                type_compte = row['type_compte']
                f.writelines(f"INSERT INTO epargne (date, compte, solde, type_compte) VALUES (TO_DATE('{date_solde}','YYYY-MM-DD'), '{numero_compte}', '{solde}', '{type_compte}');\n")

    def fill_missing_months(self):
        """Remplit les mois manquants avec le dernier solde connu."""
        count = 0
        # Récupère tous les comptes
        self.lignes.sort_values(['date','compte'], ascending=True, inplace=True)

        comptes = self.lignes['compte'].unique()

        for (compte) in comptes:
            
            soldes = self.lignes[self.lignes['compte'] == compte]

            date_range = pd.date_range(
                start=soldes['date'].min(),
                end=soldes['date'].max(),
                freq='MS'
            )
            # Pour chaque date manquante, trouve le dernier solde connu
            for date in date_range:
                if date not in soldes['date'].values:
                    # Trouve le dernier solde connu avant cette date
                    last_known = soldes[soldes['date'] < date].iloc[-1]

                    self.extras.loc[len(self.extras)] = [date, compte, float(last_known['solde']), 'ajout']
                    count += 1

        print(f'Ajout de lignes manquantes: {count}')

        self.lignes = pd.concat([self.lignes, self.extras])