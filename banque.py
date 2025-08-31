class banque:
    def __init__(self):
        self.comptes = {}

    def ajouter(self, compte):
        self.comptes[compte.numero] = compte

    def get(self, numero):
        return self.comptes.get(numero)

    def generer_inserts(self):
        inserts = []
        for compte in self.comptes.values():
            inserts.extend(compte.generer_inserts())
        return inserts
