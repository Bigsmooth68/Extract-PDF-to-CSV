from compte import compte
import logging

from analyse import (
    extraire_section,
    analyse_livret,
    analyse_autres_comptes,
    convertir_pdf,
)


class livret(compte):
    def analyse(self, fichier):
        logging.debug(
            "*************************** NEW FILE ***************************"
        )
        compte_solde = 0
        logging.info(f"Analyse du fichier livrets: {fichier.name}")

        contenu = convertir_pdf(fichier)

        livret = extraire_section(contenu, "LIVRET BLEU", "Réf")
        solde = analyse_livret(livret)
        if solde:
            self.ajout_solde(solde["date"], solde["compte"], "LIVRET", solde["solde"])
            compte_solde += 1

        livret = extraire_section(
            contenu, "LIVRET DE DEVELOPPEMENT DURABLE SOLIDAIRE", "Réf"
        )
        solde = analyse_livret(livret)
        if solde:
            self.ajout_solde(solde["date"], solde["compte"], "LDD", solde["solde"])
            compte_solde += 1

        # dans le cas ou il n'y a pas de mouvement, le compte est dans la section autres comptes
        livret = extraire_section(contenu, "SITUATION DE VOS AUTRES COMPTES", "Réf :")
        solde = analyse_autres_comptes(livret)
        if solde:
            self.ajout_solde(
                solde["date"],
                solde["compte"],
                "LDD",
                solde["solde"],
            )
        logging.info(f"Ligne livrets trouvées: {compte_solde}")
