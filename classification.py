from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
import pandas as pd
import ollama
import logging
import sys
import yaml

class categories:
    inverted = {}

    def __init__(self, file: str = "config.yml"):
        config = yaml.safe_load(open(file, encoding="utf-8"))

        categories = config["categories"]

        for item in categories:  # item = chaque dict dans la liste
            for category, merchants in item.items():
                for merchant in merchants:
                    self.inverted[merchant] = category

        logging.info(f"{file} chargé")


    def classify_expense_manual(self, row):
        label = row["type_compte"].strip()

        cat = self.inverted.get(label, None)
        if cat:
            return cat
        # boucle sur les motifs partiels
        else:
            for pattern, category in self.inverted.items():
                if pattern in label:
                    return category
        # return pd.NA

    @staticmethod
    def classify_expense_auto(self, row):
        prompt = f"""
        Tu es un assistant qui classe les dépenses bancaires.
        Donne un seul mot (ex: 'loyer', 'courses', 'salaire', 'loisirs', 'transport', etc.)
        pour la catégorie de cette opération.

        date: {row["date"]}
        compte: {row["compte"]}
        solde: {row["solde"]}
        type_compte: {row["type_compte"]}
        """
        logging.debug(f"classification {row['type_compte']}")
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        cat = response["message"]["content"].strip()
        # on garde seulement le premier mot
        return cat.split()[0]

#### FIN CLASS
#### FIN FONCTIONS

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

load_dotenv()
DB_URL = os.environ.get("DB_URL")
MODEL = os.environ.get("MODEL")
engine = create_engine(url=DB_URL)

try:
    df = pd.read_sql("select * from cc where categorie is null", con=engine)
    logging.info("Connecté à la base")
except Exception as X:
    logging.error(X)
    exit(1)

# df = df.head(100)

categories_list = categories()

df["categorie"] = df.apply(categories_list.classify_expense_manual, axis=1)

lignes_sans_categorie = len(df)

df = df[df["categorie"].notna()]

logging.info(f"Mouvements catégorisé: {len(df)} (restant {lignes_sans_categorie-len(df)})")

if len(df) == 0:
    logging.warning("Rien à catégoriser")
    exit(1)

# Ecriture des résultats
with engine.begin() as conn:
    for _, row in df.iterrows():
        conn.execute(
            text("""
                UPDATE cc
                SET categorie = :categorie
                WHERE id = :id
            """),
            {
                "categorie": row["categorie"],
                "id": row["id"],
            }
        )