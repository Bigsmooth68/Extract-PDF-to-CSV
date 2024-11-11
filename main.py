# importing required classes
from pypdf import PdfReader
from pathlib import Path
import re
import matplotlib.pyplot as plt

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
            # print(f'{numero_compte},{date_solde},{solde}')
            return [date_solde, numero_compte, solde]    

def analyse_autres_comptes(date_solde, text):
    for line in text:
        print(line)
        if 'LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE' in line:
            match = re.search(r'(\d.+\d) .+EUR .(\d{1,3}(\.?\d{3})*,\d+)', line)
            if match:
                numero_compte = match[1]
                solde = match[2]
                solde = solde.replace('.','').replace(',','.').replace('+','')
                solde = float(solde)
                return [date_solde, numero_compte, solde]    

############## 

def main():
    
    # print('date,solde')
    tab_date = []
    tab_solde = []
    lines_found = 0
    result_file = open("out\insert.sql", "w")
    dir_path = Path('.\\pdf')
    for file in sorted(dir_path.glob('*.pdf')):
        print(f'Processing {file} ')
        reader = PdfReader(file)

        for page in reader.pages:

            content = page.extract_text(extraction_mode='plain')
            livret = extract_sections(content, 'LIVRET BLEU', 'Réf')
            ldd = extract_sections(content, 'SITUATION DE VOS AUTRES COMPTES', 'Sous réserve des extournes ou annulations éventuelles')

            solde = analyse_livret(livret)
            if solde:
                tab_date.append(solde[0])
                tab_solde.append(solde[2])
                # result_file.writelines(f"INSERT INTO epargne (date, compte, solde) VALUES (TO_DATE('{solde[0]}','DD/MM/YYYY'), '{solde[1]}', '{solde[2]}');\n")
                lines_found += 1
                solde_ldd = analyse_autres_comptes(solde[0], ldd)
                if solde_ldd:
                    tab_date.append(solde_ldd[0])
                    tab_solde.append(solde_ldd[2])
                    result_file.writelines(f"INSERT INTO epargne (date, compte, solde) VALUES (TO_DATE('{solde_ldd[0]}','DD/MM/YYYY'), '{solde_ldd[1]}', '{solde_ldd[2]}');\n")
                    lines_found += 1


    result_file.close()

    print(f'{lines_found} lines found.')
    # # Plotting
    # plt.plot(tab_date,tab_solde)
    # plt.xlabel('Date')
    # plt.ylabel('Solde')
    # plt.title(f'Epargne')

    # # function to show the plot
    # plt.show()


if __name__ == "__main__":
    main()
