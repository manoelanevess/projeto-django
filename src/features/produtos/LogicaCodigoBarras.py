"""Normalizacao dos codigos recebidos pelo leitor."""


def NormalizarCodigoBarras(Valor, Obrigatorio=False):
    Codigo = str(Valor or "").strip()

    if not Codigo:
        if Obrigatorio:
            raise ValueError("Informe o código de barras.")
        return None

    if len(Codigo) > 64 or any(
        ord(Caractere) < 32 or ord(Caractere) == 127 for Caractere in Codigo
    ):
        raise ValueError("Informe um código de barras válido com até 64 caracteres.")

    return Codigo


def EhCodigoGtin(Codigo):
    if not isinstance(Codigo, str) or len(Codigo) not in (8, 12, 13, 14):
        return False
    if not Codigo.isascii() or not Codigo.isdecimal() or not Codigo.strip("0"):
        return False

    Soma = sum(
        int(Digito) * (3 if Posicao % 2 == 0 else 1)
        for Posicao, Digito in enumerate(reversed(Codigo[:-1]))
    )
    return (Soma + int(Codigo[-1])) % 10 == 0
