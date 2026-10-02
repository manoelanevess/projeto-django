"""Regras do carrinho e da conclusão de vendas."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction

from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda
from features.produtos.models import Produto

from .models import ItemVenda, Venda


ChaveSessaoCarrinhos = "CarrinhosVenda"
ChaveSessaoNomesCarrinhos = "NomesCarrinhosVenda"
NumerosCarrinhos = ("1", "2", "3")
Centavo = Decimal("0.01")
PrecisaoQuantidade = Decimal("0.001")


def ConverterQuantidade(Valor):
    try:
        Quantidade = Decimal(str(Valor).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Informe uma quantidade válida.") from None

    if Quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    return Quantidade.quantize(PrecisaoQuantidade, rounding=ROUND_HALF_UP)


def ValidarQuantidadeProduto(ProdutoVenda, Quantidade):
    if ProdutoVenda.UnidadeVenda == Produto.UNIDADE and Quantidade % 1 != 0:
        raise ValueError(f"{ProdutoVenda.Nome} deve ser vendido em unidades inteiras.")

    if Quantidade > ProdutoVenda.QuantidadeEstoque:
        Unidade = ProdutoVenda.ObterUnidadeResumida()
        Disponivel = FormatarQuantidade(ProdutoVenda.QuantidadeEstoque)
        raise ValueError(
            f"Estoque insuficiente para {ProdutoVenda.Nome}. Disponível: {Disponivel} {Unidade}."
        )


def ValidarNumeroCarrinho(NumeroCarrinho):
    NumeroNormalizado = str(NumeroCarrinho or "1")

    if NumeroNormalizado not in NumerosCarrinhos:
        raise ValueError("Selecione um carrinho válido.")

    return NumeroNormalizado


def ObterNomesCarrinhosSessao(Request):
    NomesCarrinhos = Request.session.get(ChaveSessaoNomesCarrinhos, {})

    if not isinstance(NomesCarrinhos, dict):
        NomesCarrinhos = {}

    return NomesCarrinhos


def ObterNomePersonalizadoCarrinho(Request, NumeroCarrinho):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Nome = ObterNomesCarrinhosSessao(Request).get(Numero, "")
    return str(Nome).strip()


def ObterNomeExibicaoCarrinho(Request, NumeroCarrinho):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    return ObterNomePersonalizadoCarrinho(Request, Numero) or f"Carrinho {Numero}"


def DefinirNomeCarrinho(Request, NumeroCarrinho, NomeInformado):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Nome = " ".join(str(NomeInformado or "").split())

    if len(Nome) > 80:
        raise ValueError("O nome do cliente deve ter no máximo 80 caracteres.")

    NomesCarrinhos = ObterNomesCarrinhosSessao(Request)

    if Nome:
        NomesCarrinhos[Numero] = Nome
    else:
        NomesCarrinhos.pop(Numero, None)

    Request.session[ChaveSessaoNomesCarrinhos] = NomesCarrinhos
    Request.session.modified = True
    return Nome or f"Carrinho {Numero}"


def LimparNomeCarrinho(Request, NumeroCarrinho):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    NomesCarrinhos = ObterNomesCarrinhosSessao(Request)
    NomesCarrinhos.pop(Numero, None)
    Request.session[ChaveSessaoNomesCarrinhos] = NomesCarrinhos
    Request.session.modified = True


def ObterCarrinhosSessao(Request):
    Carrinhos = Request.session.get(ChaveSessaoCarrinhos, {})

    if not isinstance(Carrinhos, dict):
        Carrinhos = {}

    return Carrinhos


def ObterCarrinhoSessao(Request, NumeroCarrinho="1"):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinhos = ObterCarrinhosSessao(Request)
    Carrinho = Carrinhos.get(Numero, {})

    if not isinstance(Carrinho, dict):
        Carrinho = {}

    return Carrinho


def SalvarCarrinhoSessao(Request, NumeroCarrinho, Carrinho):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinhos = ObterCarrinhosSessao(Request)
    Carrinhos[Numero] = Carrinho
    Request.session[ChaveSessaoCarrinhos] = Carrinhos
    Request.session.modified = True


def AdicionarProdutoAoCarrinho(
    Request,
    NumeroCarrinho,
    ProdutoId,
    ValorQuantidade,
):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)

    try:
        ProdutoVenda = Produto.objects.get(pk=ProdutoId, Ativo=True)
    except (Produto.DoesNotExist, TypeError, ValueError):
        raise ValueError("Produto não encontrado ou indisponível.") from None

    QuantidadeInformada = ConverterQuantidade(ValorQuantidade)
    Carrinho = ObterCarrinhoSessao(Request, Numero)

    try:
        QuantidadeAtual = Decimal(Carrinho.get(str(ProdutoVenda.id), "0"))
    except InvalidOperation:
        QuantidadeAtual = Decimal("0")

    QuantidadeTotal = QuantidadeAtual + QuantidadeInformada
    ValidarQuantidadeProduto(ProdutoVenda, QuantidadeTotal)

    Carrinho[str(ProdutoVenda.id)] = format(QuantidadeTotal, "f")
    SalvarCarrinhoSessao(Request, Numero, Carrinho)

    return ProdutoVenda


def RemoverProdutoDoCarrinho(Request, NumeroCarrinho, ProdutoId):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinho = ObterCarrinhoSessao(Request, Numero)
    Carrinho.pop(str(ProdutoId), None)
    SalvarCarrinhoSessao(Request, Numero, Carrinho)


def LimparCarrinho(Request, NumeroCarrinho):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinhos = ObterCarrinhosSessao(Request)
    Carrinhos.pop(Numero, None)
    Request.session[ChaveSessaoCarrinhos] = Carrinhos
    Request.session.modified = True
    LimparNomeCarrinho(Request, Numero)


def MontarResumoCarrinho(Request, NumeroCarrinho="1"):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinho = ObterCarrinhoSessao(Request, Numero)
    Identificadores = []

    for ProdutoId in Carrinho:
        try:
            Identificadores.append(int(ProdutoId))
        except (TypeError, ValueError):
            continue

    Produtos = {
        ProdutoVenda.id: ProdutoVenda
        for ProdutoVenda in Produto.objects.filter(id__in=Identificadores)
    }
    Itens = []
    Total = Decimal("0.00")

    for ProdutoId, ValorQuantidade in Carrinho.items():
        try:
            ProdutoVenda = Produtos[int(ProdutoId)]
            Quantidade = ConverterQuantidade(ValorQuantidade)
        except (KeyError, TypeError, ValueError):
            continue

        Subtotal = (Quantidade * ProdutoVenda.PrecoVenda).quantize(
            Centavo,
            rounding=ROUND_HALF_UP,
        )
        Total += Subtotal
        Itens.append(
            {
                "Produto": ProdutoVenda,
                "Quantidade": Quantidade,
                "QuantidadeFormatada": FormatarQuantidade(Quantidade),
                "PrecoFormatado": FormatarValorMoeda(ProdutoVenda.PrecoVenda),
                "Subtotal": Subtotal,
                "SubtotalFormatado": FormatarValorMoeda(Subtotal),
                "Unidade": ProdutoVenda.ObterUnidadeResumida(),
            }
        )

    Itens.sort(key=lambda Item: Item["Produto"].Nome.lower())
    Total = Total.quantize(Centavo, rounding=ROUND_HALF_UP)

    return {
        "Numero": Numero,
        "Nome": ObterNomeExibicaoCarrinho(Request, Numero),
        "NomePersonalizado": ObterNomePersonalizadoCarrinho(Request, Numero),
        "Itens": Itens,
        "QuantidadeProdutos": len(Itens),
        "Total": Total,
        "TotalFormatado": FormatarValorMoeda(Total),
    }


def MontarResumosCarrinhos(Request):
    return [
        MontarResumoCarrinho(Request, NumeroCarrinho)
        for NumeroCarrinho in NumerosCarrinhos
    ]


def ConverterValorRecebido(Valor):
    try:
        ValorRecebido = Decimal(str(Valor).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Informe o valor recebido em dinheiro.") from None

    if ValorRecebido < 0:
        raise ValueError("O valor recebido não pode ser negativo.")

    return ValorRecebido.quantize(Centavo, rounding=ROUND_HALF_UP)


def ConcluirVenda(
    Request,
    NumeroCarrinho,
    FormaPagamento,
    ValorRecebidoInformado="",
):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinho = ObterCarrinhoSessao(Request, Numero)
    NomeCliente = ObterNomePersonalizadoCarrinho(Request, Numero)

    if not Carrinho:
        raise ValueError("Adicione pelo menos um produto antes de concluir a compra.")

    if FormaPagamento not in {Venda.DINHEIRO, Venda.PIX}:
        raise ValueError("Selecione dinheiro ou PIX como forma de pagamento.")

    try:
        Identificadores = [int(ProdutoId) for ProdutoId in Carrinho]
    except (TypeError, ValueError):
        raise ValueError("O carrinho contém um produto inválido.") from None

    with transaction.atomic():
        ProdutosBloqueados = {
            ProdutoVenda.id: ProdutoVenda
            for ProdutoVenda in Produto.objects.select_for_update().filter(
                id__in=Identificadores,
                Ativo=True,
            )
        }

        if len(ProdutosBloqueados) != len(Identificadores):
            raise ValueError("Um produto do carrinho não está mais disponível.")

        ItensVenda = []
        Total = Decimal("0.00")

        for ProdutoId, ValorQuantidade in Carrinho.items():
            ProdutoVenda = ProdutosBloqueados[int(ProdutoId)]
            Quantidade = ConverterQuantidade(ValorQuantidade)
            ValidarQuantidadeProduto(ProdutoVenda, Quantidade)
            Subtotal = (Quantidade * ProdutoVenda.PrecoVenda).quantize(
                Centavo,
                rounding=ROUND_HALF_UP,
            )
            Total += Subtotal
            ItensVenda.append((ProdutoVenda, Quantidade, Subtotal))

        Total = Total.quantize(Centavo, rounding=ROUND_HALF_UP)
        ValorRecebido = None
        Troco = Decimal("0.00")

        if FormaPagamento == Venda.DINHEIRO:
            ValorRecebido = ConverterValorRecebido(ValorRecebidoInformado)

            if ValorRecebido < Total:
                ValorFaltante = FormatarValorMoeda(Total - ValorRecebido)
                raise ValueError(f"Faltam R$ {ValorFaltante} para concluir a compra.")

            Troco = (ValorRecebido - Total).quantize(Centavo)

        VendaConcluida = Venda.objects.create(
            Proprietario=Request.user,
            NomeCliente=NomeCliente,
            FormaPagamento=FormaPagamento,
            Total=Total,
            ValorRecebido=ValorRecebido,
            Troco=Troco,
        )

        for ProdutoVenda, Quantidade, Subtotal in ItensVenda:
            ItemVenda.objects.create(
                Venda=VendaConcluida,
                Produto=ProdutoVenda,
                NomeProduto=ProdutoVenda.Nome,
                UnidadeVenda=ProdutoVenda.UnidadeVenda,
                Quantidade=Quantidade,
                PrecoUnitario=ProdutoVenda.PrecoVenda,
                Subtotal=Subtotal,
            )
            ProdutoVenda.QuantidadeEstoque -= Quantidade
            ProdutoVenda.save(update_fields=["QuantidadeEstoque"])

    LimparCarrinho(Request, Numero)
    return VendaConcluida
