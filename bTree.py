import bisect

class _NoB(object):
    __slots__ = ["arvore", "chaves", "filhos"]

    def __init__(self, arvore, chaves=None, filhos=None):
        self.arvore = arvore
        self.chaves = chaves or []
        self.filhos = filhos or []

    def __repr__(self):
        name = getattr(self, "filhos", 0) and "Ramo" or "Folha"
        return "<%s %s>" % (name, ", ".join(map(str, self.chaves)))

    def lateral(self, pai, pai_index, dest, dest_index):
        if pai_index > dest_index:
            dest.chaves.append(pai.chaves[dest_index])
            pai.chaves[dest_index] = self.chaves.pop(0)
            if self.filhos:
                dest.filhos.append(self.filhos.pop(0))
        else:
            dest.chaves.insert(0, pai.chaves[pai_index])
            pai.chaves[pai_index] = self.chaves.pop()
            if self.filhos:
                dest.filhos.insert(0, self.filhos.pop())

    def encolher(self, ancestrais):
        pai = None

        if ancestrais:
            pai, pai_index = ancestrais.pop()
            if pai_index:
                irmao_esquerda = pai.filhos[pai_index - 1]
                if len(irmao_esquerda.chaves) < self.arvore.ordem:
                    self.lateral(pai, pai_index, irmao_esquerda, pai_index - 1)
                    return
            if pai_index + 1 < len(pai.filhos):
                irmao_direita = pai.filhos[pai_index + 1]
                if len(irmao_direita.chaves) < self.arvore.ordem:
                    self.lateral(pai, pai_index, irmao_direita, pai_index + 1)
                    return

        irmao, push = self.dividir()

        if not pai:
            pai, pai_index = self.arvore.RAMO(
                    self.arvore, filhos=[self]), 0
            self.arvore._raiz = pai
        pai.chaves.insert(pai_index, push)
        pai.filhos.insert(pai_index + 1, irmao)
        if len(pai.chaves) > pai.arvore.ordem:
            pai.encolher(ancestrais)

    def crescer(self, ancestrais):
        pai, pai_index = ancestrais.pop()

        minimo = self.arvore.ordem // 2
        irmao_esquerda = irmao_direita = None

        if pai_index + 1 < len(pai.filhos):
            irmao_direita = pai.filhos[pai_index + 1]
            if len(irmao_direita.chaves) > minimo:
                irmao_direita.lateral(pai, pai_index + 1, self, pai_index)
                return

        if pai_index:
            irmao_esquerda = pai.filhos[pai_index - 1]
            if len(irmao_esquerda.chaves) > minimo:
                irmao_esquerda.lateral(pai, pai_index - 1, self, pai_index)
                return

        if irmao_esquerda:
            irmao_esquerda.chaves.append(pai.chaves[pai_index - 1])
            irmao_esquerda.chaves.extend(self.chaves)
            if self.filhos:
                irmao_esquerda.filhos.extend(self.filhos)
            pai.chaves.pop(pai_index - 1)
            pai.filhos.pop(pai_index)
        else:
            self.chaves.append(pai.chaves[pai_index])
            self.chaves.extend(irmao_direita.chaves)
            if self.filhos:
                self.filhos.extend(irmao_direita.filhos)
            pai.chaves.pop(pai_index)
            pai.filhos.pop(pai_index + 1)

        if len(pai.chaves) < minimo:
            if ancestrais:
                pai.crescer(ancestrais)
            elif not pai.chaves:
                self.arvore._raiz = irmao_esquerda or self

    def dividir(self):
        center = len(self.chaves) // 2
        median = self.chaves[center]
        irmao = type(self)(
                self.arvore,
                self.chaves[center + 1:],
                self.filhos[center + 1:])
        self.chaves = self.chaves[:center]
        self.filhos = self.filhos[:center + 1]
        return irmao, median

    def inserir(self, index, item, ancestrais):
        self.chaves.insert(index, item)
        if len(self.chaves) > self.arvore.ordem:
            self.encolher(ancestrais)

    def remover(self, index, ancestrais):
        minimo = self.arvore.ordem // 2

        if self.filhos:
            ancestrais_adicionais = [(self, index + 1)]
            descendentes = self.filhos[index + 1]
            while descendentes.filhos:
                ancestrais_adicionais.append((descendentes, 0))
                descendentes = descendentes.filhos[0]
            if len(descendentes.chaves) > minimo:
                ancestrais.extend(ancestrais_adicionais)
                self.chaves[index] = descendentes.chaves[0]
                descendentes.remover(0, ancestrais)
                return

            ancestrais_adicionais = [(self, index)]
            descendentes = self.filhos[index]
            while descendentes.filhos:
                ancestrais_adicionais.append((descendentes, len(descendentes.filhos) - 1))
                descendentes = descendentes.filhos[-1]
            ancestrais.extend(ancestrais_adicionais)
            self.chaves[index] = descendentes.chaves[-1]
            descendentes.remover(len(descendentes.filhos) - 1, ancestrais)
        else:
            self.chaves.pop(index)
            if len(self.chaves) < minimo and ancestrais:
                self.crescer(ancestrais)

class ArvoreB(object):
    RAMO = FOLHA = _NoB

    def __init__(self, ordem):
        self.ordem = ordem
        self._raiz = self._ultimo = self.FOLHA(self)

    def inserir(self, item):
        ancestrais = self._caminho_ate(item)
        node, index = ancestrais[-1]
        while getattr(node, "filhos", None):
            node = node.filhos[index]
            index = bisect.bisect_left(node.chaves, item)
            ancestrais.append((node, index))
        node, index = ancestrais.pop()
        node.inserir(index, item, ancestrais)

    def _caminho_ate(self, item):
        atual = self._raiz
        ancestral = []

        while getattr(atual, "filhos", None):
            index = bisect.bisect_left(atual.chaves, item)
            ancestral.append((atual, index))
            if index < len(atual.chaves) \
                    and atual.chaves[index] == item:
                return ancestral
            atual = atual.filhos[index]

        index = bisect.bisect_left(atual.chaves, item)
        ancestral.append((atual, index))
        presente = index < len(atual.chaves)
        presente = presente and atual.chaves[index] == item

        return ancestral
    
    def remover(self, item):
        ancestrais = self._caminho_ate(item)

        if self._presente(item, ancestrais):
            node, index = ancestrais.pop()
            node.remover(index, ancestrais)
        else:
            raise ValueError("%r not in %s" % (item, self.__class__.__name__))

    def _presente(self, item, ancestrais):
        ultimo, index = ancestrais[-1]
        return index < len(ultimo.chaves) and ultimo.chaves[index] == item

    def __repr__(self):
        def recurse(node, accum, depth):
            accum.append(("  " * depth) + repr(node))
            for node in getattr(node, "filhos", []):
                recurse(node, accum, depth + 1)

        accum = []
        recurse(self._raiz, accum, 0)
        return "\n".join(accum)


# import random

arvoreB = ArvoreB(2)

# for i in range(0,20):
#     valor = random.randrange(1000)
#     arvoreB.inserir(valor)
#     print('\nVALOR INSERIDO: ', valor)
#     print('ARVORE:\n', arvoreB)

arvoreB.inserir(100)
print('\nINSERE 100:\n', arvoreB)
arvoreB.inserir(10)
print('\nINSERE 10:\n', arvoreB)
arvoreB.inserir(200)
print('\nINSERE 200:\n', arvoreB)
arvoreB.inserir(50)
print('\nINSERE 50:\n', arvoreB)
arvoreB.inserir(150)
print('\nINSERE 150:\n', arvoreB)
arvoreB.inserir(30)
print('\nINSERE 30:\n', arvoreB)
arvoreB.inserir(130)
print('\nINSERE 130:\n', arvoreB)
arvoreB.inserir(1)
print('\nINSERE 1:\n', arvoreB)
arvoreB.inserir(199)
print('\nINSERE 199:\n', arvoreB)
arvoreB.remover(1)
print('\nREMOVE 1:\n', arvoreB)
arvoreB.remover(10)
print('\nREMOVE 10:\n', arvoreB)