# Analyses d'extrait de compte Crédit Mutuel

Pour l'instant, cela produit un graphique montant l'évolution du solde avec une ligne par compte.

Les différents pdf doivent être stocké dans le répertoire pdf.

# Utilisation

## Aide

```bash
$ python main.py -h
usage: Analyse des extraits de comptes Crédit Mutuel [-h] [-p] [-l] [-o {csv,sql}]

options:
  -h, --help            show this help message and exit
  -p, --pea             Limite l'extraction aux relevés des PEA
  -l, --livret          Limite l'extraction aux livrets
  -o {csv,sql}, --out {csv,sql}
                        Choix du format d'export
```
