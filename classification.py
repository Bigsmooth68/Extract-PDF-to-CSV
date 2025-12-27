from dotenv import load_dotenv
from sqlalchemy import create_engine
import os
import pandas as pd
import ollama
import logging
import sys


def classify_expense(row):
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


def post_process_type_depense(row):
    lib = row["type_compte"].upper()
    cat = row["type_depense"]

    # 1. Règles de surclassement par mot-clé
    if "RETRAIT DAB" in lib:
        return "Cash"
    if "FREE MOBILE" in lib:
        return "Téléphone"
    if "CAF" in lib:
        return "Allocations"
    if "EKWATEUR" in lib:
        return "Énergie"

    # 2. Nettoyage de la réponse LLM
    cat = cat.strip(" '\"").capitalize()

    return cat


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
    df = pd.read_sql("select * from cc", con=engine)
    print("Connecté à la base")
except Exception as X:
    print(X)

df = df.head(20)

logging.info(f"En cours d'analyse avec le model {MODEL} ...")
df["type_depense"] = df.apply(classify_expense, axis=1)

logging.info("Normalisation des catégories")
df["type_depense_corrige"] = df.apply(post_process_type_depense, axis=1)

logging.info(df)
