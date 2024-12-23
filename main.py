# importing required classes
from pypdf import PdfReader
from pathlib import Path
import re
import matplotlib.pyplot as plt
import pandas as pd
from compte import compte

def extract_sections(text, start_pattern: str, end_pattern: str):
    section = []
    inside_section = False
    for line in text.splitlines():
        if start_pattern in line:
            inside_section = True
        if inside_section and end_pattern in line:
            section.append(line)
            return section
        if inside_section:
            section.append(line)
    return section

def analyse_livret(text):
    try:
        for line in text:
            match = re.search(r' (\d{7,}) ', line) # au moins 7 chiffres
            if match:
                numero_compte = match[1]
                # print(f'Nouveau compte trouvé: {numero_compte}')
            if ' SOLDE' in line and 'Réf' in line:
                match = re.search(r'AU (\d.+\d) (\d{1,3}(\.?\d{3})*,\d+)', line)
                date_solde = match[1]
                solde = match[2]
                solde = solde.replace('.','').replace(',','.')
                solde = float(solde)
                return {
                    'date': date_solde,
                    'compte': numero_compte,
                    'solde': solde
                }
    except:
        print(text)

def analyse_autres_comptes(date_solde, text):
    for line in text:
        if 'LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE' in line:
            match = re.search(r'(\d.+\d) .+EUR .(\d{1,3}(\.?\d{3})*,\d+)', line)
            if match:
                numero_compte = match[1]
                solde = match[2]
                solde = solde.replace('.','').replace(',','.').replace('+','')
                solde = float(solde)
                return {
                    'date': date_solde,
                    'compte': numero_compte,
                    'solde': solde
                }


############## 
epargne = compte()
pea = compte()

def main():

    lines_found = 0
    dir_path = Path('.\\pdf')
    for file in sorted(dir_path.glob('*.pdf')):
        print(f'Processing {file} ')
        reader = PdfReader(file)

        numero_compte = None

        for page in reader.pages:

            if ('EUROCOMPTE' in file.name) or ('COMPTE COURANT EN CHF' in file.name):
                # On ignore le compte courant pour l'instant
                continue

            content = page.extract_text(extraction_mode='plain')

            if 'Portefeuille valoris' in file.name:
                match = re.search(r' au (.+).pdf', file.name)
                date_solde = match[1]
                for line in content.splitlines():
                    if numero_compte is None and ' 000' in line:
                        match = re.search(r' (000\d+)$', line)
                        if match:
                            numero_compte = match[1]
                    if 'TOTAL DU COMPTE TITRES' in line:
                        match = re.search(r'TOTAL DU COMPTE TITRES (\d{1,3}( ?\d{3})*,\d+)', line)
                        if match:
                            solde = match[1].replace(' ','').replace(',','.')
                            pea.ajout_solde(date_solde, numero_compte, 'PEA', solde)
                            lines_found += 1
            else:
                livret = extract_sections(content, 'LIVRET BLEU', 'Réf')
                ldd = extract_sections(content, 'SITUATION DE VOS AUTRES COMPTES', 'Sous réserve des extournes ou annulations éventuelles')

                solde = analyse_livret(livret)
                if solde:
                    epargne.ajout_solde(solde['date'], solde['compte'], 'LIVRET', solde['solde'])
                    lines_found += 1
                    solde_ldd = analyse_autres_comptes(solde['date'], ldd)
                    if solde_ldd:
                        epargne.ajout_solde(solde_ldd['date'], solde_ldd['compte'], 'LDD', solde_ldd['solde'])
                        lines_found += 1

    print(f'Lignes générées: {lines_found}')

    epargne.fill_missing_months()

    epargne.generate_insert('epargne')

if __name__ == "__main__":
    main()
