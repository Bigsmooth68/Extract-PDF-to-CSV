class banque:
    def __init__(self_):
        self_.comptes = {}

    def ajouter(self_, compte):
        self_.comptes[compte.numero] = compte

    def get(self_, numero):
        return self_.comptes.get(numero)

    def generer_inserts(self_):
        inserts = []
        for compte in self_.comptes.values():
            inserts.extend(compte.generer_inserts())
        return inserts
