# importing required classes
from pypdf import PdfReader
from pathlib import Path
import re, locale
import matplotlib.pyplot as plt

print(locale.getlocale())


# creating a pdf reader object

dir_path = Path('.\\pdf')

# print('date,solde')
tab_date = []
tab_solde = []

for file in sorted(dir_path.glob('*.pdf')):
    reader = PdfReader(file)

    # printing number of pages in pdf file
    # print(f'Number of pages: {len(reader.pages)}')

    # creating a page object
    page = reader.pages[0]

    for line in page.extract_text(extraction_mode='plain').splitlines():

        if ' SOLDE' in line:
            # print(line)
            match = re.search(r'AU (\d.+\d) (\d{1,3}(\.?\d{3})*,\d+)', line)
            date_solde = match[1]
            solde = match[2]
            solde = solde.replace('.','').replace(',','.')
            solde = float(solde)
            # print(f'{date_solde},{solde}')
            tab_date.append(date_solde)
            tab_solde.append(solde)
        elif 'TITULAIRE' in line:
            print(line)

# Plotting
plt.plot(tab_date,tab_solde)
plt.xlabel('Date')
plt.ylabel('Solde')
plt.title('Epargne')

# function to show the plot
plt.show()