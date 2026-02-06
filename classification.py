from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os
import pandas as pd
import ollama
import logging
import sys
import yaml
import signal

class categories:
    categories = None
    inverted = {}

    def __init__(self_, file: str = "config.yml"):
        config = yaml.safe_load(open(file, encoding="utf-8"))

        self_.categories = [list(d.keys())[0] for d in config["categories"]]

        for item in config["categories"]:  # item = chaque dict dans la liste
            for category, merchants in item.items():
                for merchant in merchants:
                    self_.inverted[merchant] = category

        logging.info(f"{file} chargé")

    def classify_expense_manual(self_, row):
        label = row["type_compte"].strip()

        cat = self_.inverted.get(label, None)
        if cat:
            return cat
        # boucle sur les motifs partiels
        else:
            for pattern, category in self_.inverted.items():
                if pattern in label:
                    return category
        # return pd.NA

    def classify_expense_auto(self_, row):
        prompt = f"""
        Tu es un assistant qui classe les dépenses bancaires.
        Donne un mot et un seul parmis cette liste {self_.categories}
        pour la catégorie de cette opération.

        date: {row["date"]}
        compte: {row["compte"]}
        solde: {row["solde"]}
        opération: {row["type_compte"]}
        """
        logging.info("==============================================================")
        logging.info(f"prompt: {prompt}")
        logging.debug(f"classification {row['type_compte']}")
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        logging.info(f"reponse: {response}")
        cat = response["message"]["content"].strip()
        # on garde seulement le premier mot
        return cat.split()[0]


#### FIN CLASS
#### FIN FONCTIONS


def sigint_handler(signal, frame):
    print('Interrupted')
    sys.exit(0)
signal.signal(signal.SIGINT, sigint_handler)

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

lignes_totales = len(df)

df_manual = df[df["categorie"].notna()]
df_auto = df[df["categorie"].isna()]

logging.info(
    f"Mouvements catégorisé: {len(df_manual)} (restant { len(df_auto)})"
)

### test
# df_auto = df_auto.head(10)
# df_auto["categorie"] = df_auto.apply(categories_list.classify_expense_auto, axis=1)

# logging.info(f"\n{df_auto}")
# exit(0)

if len(df_manual) == 0:
    logging.warning("Rien à catégoriser")
    exit(1)

# Ecriture des résultats
with engine.begin() as conn:
    for _, row in df_manual.iterrows():
        conn.execute(
            text("""
                UPDATE cc
                SET categorie = :categorie
                WHERE id = :id
            """),
            {
                "categorie": row["categorie"],
                "id": row["id"],
            },
        )
