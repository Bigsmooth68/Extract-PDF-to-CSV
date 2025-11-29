from compte import compte
import logging
import pdfplumber
import pandas as pd
import re


class compte_courant(compte):
    def analyse(self, fichier):
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        logging.info(fichier)
        pdf = pdfplumber.open(fichier)
        tableau_cc = []
        tableau_cb = []
        num_page = 1
        for page in pdf.pages:
            logging.debug(f"Traitement de la page {num_page}")
            tableaux = page.extract_tables()
            for tableau in tableaux:
                entete = tableau[0]
                if "Date valeur" in entete:
                    logging.debug("Ajout d'un tableau à CC")
                    if len(tableau_cc) > 0:  # ignorer l'entête si déjà présente
                        tableau = tableau[1:]
                    tableau_cc.extend(tableau)
                elif "Commerce" in entete:
                    logging.debug("Ajout d'un tableau à CB")
                    if len(tableau_cb) > 0:  # ignorer l'entête si déjà présente
                        tableau = tableau[1:]
                    tableau_cb.extend(tableau)
                else:
                    logging.debug(f"Tableau ignoré: {tableau[0]}")
            num_page += 1

        pdf.close()

        colonnes_cc = tableau_cc[0]
        colonnes_cb = tableau_cb[0]

        df_cb = pd.DataFrame(tableau_cb[1:], columns=colonnes_cb)
        df_cb["Opération"] = df_cb["Commerce"] + " - " + df_cb["Ville"]
        df_cb.drop(columns=["Ville", "Commerce", "Montant devises"], inplace=True)
        df_cb.rename(columns={"Montant euros": "Débit"}, inplace=True)

        for _col in ["Débit"]:
            df_cb[_col] = (
                df_cb[_col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
            )

        # df_cb = df_cb[:-1]
        df_cb = df_cb[~df_cb["Date"].str.contains("TOTAL", na=False)]

        df_cc = pd.DataFrame(tableau_cc[1:], columns=colonnes_cc)
        for _ligne in ["SOLDE CREDITEUR", "Date"]:
            _filtre = df_cc["Date"].str.contains(_ligne)
            df_cc = df_cc[~_filtre]

        df_cc.drop(columns="Date valeur", inplace=True)
        df_cc.rename(
            columns={"Débit EUROS": "Débit", "Crédit EUROS": "Crédit"}, inplace=True
        )
        for _col in ["Débit", "Crédit"]:
            df_cc[_col] = (
                df_cc[_col]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
            )
        df_cc = df_cc[df_cc["Date"] != ""]

        # df_cc_1.to_excel("out/cc.xlsx", index=False)

        logging.debug(
            f"Somme débit: {df_cc['Débit'].sum()}  crédit: {df_cc['Crédit'].sum()}"
        )
        logging.debug(f"Somme débit carte: {df_cb['Débit'].sum()}")

        df_all = pd.concat([df_cc, df_cb])

        # Changement Débit/Crédit en montant négatif/positif
        df_all["Montant"] = df_all["Crédit"].fillna(-df_all["Débit"])
        try:
            df_all["Date"] = pd.to_datetime(df_all["Date"], format="%d/%m/%Y")
        except:
            mask = pd.to_datetime(
                df_all["Date"], format="%d/%m/%Y", errors="coerce"
            ).isna()
            logging.info(df_all.loc[mask, "Date"])
            import sys

            sys.exit()

        df_all.dropna(inplace=True, subset=["Montant"])

        logging.info(f"Lignes ajoutées: {len(df_all)}")

        ## génération des entrées
        df_all.apply(
            lambda row: self.ajout_solde(
                row["Date"], 0, row["Opération"], row["Montant"], aligne_date=False
            ),
            axis=1,
        )

    def filtrer(self, filtre):
        # construction d'une regex OR
        pattern = "|".join(re.escape(m) for m in filtre)

        # filtrage en une seule passe
        self.lignes = self.lignes[
            ~self.lignes["type_compte"].str.contains(pattern, na=False)
        ]

    def factoriser(self, groupes):
        for g in groupes:
            mask = self.lignes["type_compte"].str.contains(g, na=False)
            self.lignes.loc[mask, "type_compte"] = g
