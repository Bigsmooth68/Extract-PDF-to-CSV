# importing required classes
from pypdf import PdfReader
from pathlib import Path
import re, datetime
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
            return [date_solde, numero_compte, solde]    

def analyse_autres_comptes(date_solde, text):
    for line in text:
        if 'LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE' in line:
            match = re.search(r'(\d.+\d) .+EUR .(\d{1,3}(\.?\d{3})*,\d+)', line)
            if match:
                numero_compte = match[1]
                solde = match[2]
                solde = solde.replace('.','').replace(',','.').replace('+','')
                solde = float(solde)
                return [date_solde, numero_compte, solde]    

def align_date(str):
    dt = datetime.datetime.strptime(str,'%Y-%m-%d')
    if dt.day > 25:
        new_date = (dt.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
    else:
        new_date = dt.replace(day=1)
    new_str = new_date.strftime('%Y-%m-%d')
    return (f'{str} => {new_str}')

def generate_insert(table: str, date_solde: str, numero_compte: str, solde: str, type_compte: str):

    # Detect date format
    date_format = ""
    if date_solde[:4].isdigit():
        date_format = "YYYY-MM-DD"
    else:
        date_format = "DD/MM/YYYY"

    return f"INSERT INTO {table} (date, compte, solde, type_compte) VALUES (TO_DATE('{date_solde}','{date_format}'), '{numero_compte}', '{solde}', '{type_compte}');\n"

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

        numero_compte = None

        for page in reader.pages:

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
                            result_file.writelines(generate_insert('epargne',date_solde, numero_compte, solde, 'PEA'))
                            lines_found += 1
            else:
                livret = extract_sections(content, 'LIVRET BLEU', 'Réf')
                ldd = extract_sections(content, 'SITUATION DE VOS AUTRES COMPTES', 'Sous réserve des extournes ou annulations éventuelles')

                solde = analyse_livret(livret)
                if solde:
                    tab_date.append(solde[0])
                    tab_solde.append(solde[2])
                    result_file.writelines(generate_insert('epargne', solde[0], solde[1], solde[2], 'LIVRET'))
                    lines_found += 1
                    solde_ldd = analyse_autres_comptes(solde[0], ldd)
                    if solde_ldd:
                        tab_date.append(solde_ldd[0])
                        tab_solde.append(solde_ldd[2])
                        result_file.writelines(generate_insert('epargne', solde_ldd[0], solde_ldd[1], solde_ldd[2], 'LDD'))
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
