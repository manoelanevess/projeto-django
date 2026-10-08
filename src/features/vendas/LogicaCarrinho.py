"""Regras do carrinho e da conclusão de vendas."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction

from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda
from features.produtos.models import LoteEstoque, Produto

from .models import ContaCliente, ItemVenda, LancamentoContaCliente, Venda


ChaveSessaoCarrinhos = "CarrinhosVenda"
ChaveSessaoNomesCarrinhos = "NomesCarrinhosVenda"
NumerosCarrinhos = ("1", "2", "3")
Centavo = Decimal("0.01")
PrecisaoQuantidade = Decimal("0.001")
PrefixoChaveLote = "Lote:"


def ConverterQuantidade(Valor):
    try:
        Quantidade = Decimal(str(Valor).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Informe uma quantidade válida.") from None

    if Quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    return Quantidade.quantize(PrecisaoQuantidade, rounding=ROUND_HALF_UP)


def ValidarQuantidadeProduto(ProdutoVenda, Quantidade, LoteVenda=None):
    if ProdutoVenda.ExigeQuantidadeInteira() and Quantidade % 1 != 0:
        raise ValueError(f"{ProdutoVenda.Nome} deve ser vendido em unidades inteiras.")

    if LoteVenda is not None and not LoteVenda.EstaDisponivelParaVenda():
        raise ValueError(
            f"O lote selecionado de {ProdutoVenda.Nome} não está disponível."
        )

    if LoteVenda is None and not ProdutoVenda.EstaDisponivelParaVenda():
        raise ValueError(f"{ProdutoVenda.Nome} não está disponível para venda.")

    QuantidadeDisponivel = (
        LoteVenda.QuantidadeDisponivel
        if LoteVenda is not None
        else ProdutoVenda.QuantidadeEstoque
    )

    if (
        ProdutoVenda.ControlaQuantidadeEstoque()
        and Quantidade > QuantidadeDisponivel
    ):
        Unidade = ProdutoVenda.ObterUnidadeResumida()
        Disponivel = FormatarQuantidade(QuantidadeDisponivel)
        raise ValueError(
            f"Estoque insuficiente para {ProdutoVenda.Nome}. Disponível: {Disponivel} {Unidade}."
        )


def ObterChaveLote(LoteId):
    return f"{PrefixoChaveLote}{int(LoteId)}"


def ObterIdentificadorLoteDaChave(Chave):
    ChaveTexto = str(Chave)

    if not ChaveTexto.startswith(PrefixoChaveLote):
        return None

    try:
        return int(ChaveTexto.removeprefix(PrefixoChaveLote))
    except (TypeError, ValueError):
        return None


def BuscarLotesDisponiveisOrdenadosProduto(ProdutoId):
    Lotes = (
        LoteEstoque.objects.select_related("Produto", "Fornecedor")
        .filter(Produto_id=ProdutoId, Produto__Ativo=True, Ativo=True)
        .order_by("CriadoEm", "id")
    )

    return [Lote for Lote in Lotes if Lote.EstaDisponivelParaVenda()]


def BuscarLotePadraoProduto(ProdutoId):
    LotesDisponiveis = BuscarLotesDisponiveisOrdenadosProduto(ProdutoId)

    if not LotesDisponiveis:
        return None

    return LotesDisponiveis[0]


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

    CarrinhoNormalizado = {}
    FoiConvertido = False

    for ChaveItem, Quantidade in Carrinho.items():
        if ObterIdentificadorLoteDaChave(ChaveItem) is not None:
            CarrinhoNormalizado[ChaveItem] = Quantidade
            continue

        try:
            ProdutoId = int(ChaveItem)
        except (TypeError, ValueError):
            FoiConvertido = True
            continue

        LotePadrao = BuscarLotePadraoProduto(ProdutoId)

        if LotePadrao is None:
            FoiConvertido = True
            continue

        ChaveLote = ObterChaveLote(LotePadrao.id)
        CarrinhoNormalizado[ChaveLote] = Quantidade
        FoiConvertido = True

    if FoiConvertido:
        Carrinhos[Numero] = CarrinhoNormalizado
        Request.session[ChaveSessaoCarrinhos] = Carrinhos
        Request.session.modified = True
        Carrinho = CarrinhoNormalizado

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

    LotesDisponiveis = BuscarLotesDisponiveisOrdenadosProduto(ProdutoVenda.id)

    if not LotesDisponiveis:
        raise ValueError("Este produto não possui um lote disponível para venda.")

    QuantidadeInformada = ConverterQuantidade(ValorQuantidade)

    if ProdutoVenda.ExigeQuantidadeInteira() and QuantidadeInformada % 1 != 0:
        raise ValueError(f"{ProdutoVenda.Nome} deve ser vendido em unidades inteiras.")

    Carrinho = ObterCarrinhoSessao(Request, Numero).copy()
    QuantidadeRestante = QuantidadeInformada
    QuantidadeDisponivel = Decimal("0.000")

    for LoteVenda in LotesDisponiveis:
        ChaveLote = ObterChaveLote(LoteVenda.id)

        try:
            QuantidadeAtual = Decimal(Carrinho.get(ChaveLote, "0"))
        except (InvalidOperation, TypeError, ValueError):
            QuantidadeAtual = Decimal("0.000")

        if ProdutoVenda.ControlaQuantidadeEstoque():
            QuantidadeLivre = max(
                LoteVenda.QuantidadeDisponivel - QuantidadeAtual,
                Decimal("0.000"),
            )
            QuantidadeDisponivel += QuantidadeLivre
            QuantidadeAdicionar = min(QuantidadeRestante, QuantidadeLivre)
        else:
            QuantidadeAdicionar = QuantidadeRestante

        if QuantidadeAdicionar <= 0:
            continue

        QuantidadeTotal = QuantidadeAtual + QuantidadeAdicionar
        ValidarQuantidadeProduto(ProdutoVenda, QuantidadeTotal, LoteVenda)
        Carrinho[ChaveLote] = format(QuantidadeTotal, "f")
        QuantidadeRestante -= QuantidadeAdicionar

        if QuantidadeRestante == 0:
            break

    if QuantidadeRestante > 0:
        Disponivel = FormatarQuantidade(QuantidadeDisponivel)
        Unidade = ProdutoVenda.ObterUnidadeResumida()
        raise ValueError(
            f"Estoque insuficiente para {ProdutoVenda.Nome}. Disponível: {Disponivel} {Unidade}."
        )

    SalvarCarrinhoSessao(Request, Numero, Carrinho)

    return ProdutoVenda


def RemoverProdutoDoCarrinho(Request, NumeroCarrinho, ChaveItem):
    Numero = ValidarNumeroCarrinho(NumeroCarrinho)
    Carrinho = ObterCarrinhoSessao(Request, Numero)
    Carrinho.pop(str(ChaveItem), None)
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
    IdentificadoresLotes = [
        LoteId
        for Chave in Carrinho
        if (LoteId := ObterIdentificadorLoteDaChave(Chave)) is not None
    ]
    Lotes = {
        Lote.id: Lote
        for Lote in LoteEstoque.objects.select_related(
            "Produto", "Fornecedor"
        ).filter(id__in=IdentificadoresLotes)
    }
    Itens = []
    Total = Decimal("0.00")

    for ChaveItem, ValorQuantidade in Carrinho.items():
        try:
            LoteVenda = Lotes[ObterIdentificadorLoteDaChave(ChaveItem)]
            ProdutoVenda = LoteVenda.Produto
            Quantidade = ConverterQuantidade(ValorQuantidade)
        except (KeyError, TypeError, ValueError):
            continue

        Subtotal = (Quantidade * LoteVenda.PrecoVenda).quantize(
            Centavo,
            rounding=ROUND_HALF_UP,
        )
        Total += Subtotal
        Itens.append(
            {
                "Produto": ProdutoVenda,
                "Lote": LoteVenda,
                "NumeroLote": LoteVenda.ObterNumeroNoProduto(),
                "ChaveItem": ChaveItem,
                "Quantidade": Quantidade,
                "QuantidadeFormatada": FormatarQuantidade(Quantidade),
                "PrecoFormatado": FormatarValorMoeda(LoteVenda.PrecoVenda),
                "CustoFormatado": FormatarValorMoeda(LoteVenda.PrecoCusto),
                "Subtotal": Subtotal,
                "SubtotalFormatado": FormatarValorMoeda(Subtotal),
                "Unidade": ProdutoVenda.ObterUnidadeResumida(),
            }
        )

    Itens.sort(
        key=lambda Item: (
            Item["Produto"].Nome.lower(),
            Item["Lote"].CriadoEm,
            Item["Lote"].id,
        )
    )
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

    FormasPagamentoValidas = {Venda.DINHEIRO, Venda.PIX, Venda.CONTA_CLIENTE}

    if FormaPagamento not in FormasPagamentoValidas:
        raise ValueError("Selecione dinheiro, PIX ou conta do cliente.")

    if FormaPagamento == Venda.CONTA_CLIENTE and not NomeCliente:
        raise ValueError("Informe o nome do cliente para lançar na continha.")

    Identificadores = [
        ObterIdentificadorLoteDaChave(ChaveItem) for ChaveItem in Carrinho
    ]

    if any(LoteId is None for LoteId in Identificadores):
        raise ValueError("O carrinho contém um produto inválido.") from None

    with transaction.atomic():
        LotesBloqueados = {
            LoteVenda.id: LoteVenda
            for LoteVenda in LoteEstoque.objects.select_for_update()
            .select_related("Produto", "Fornecedor")
            .filter(
                id__in=Identificadores,
                Ativo=True,
                Produto__Ativo=True,
            )
        }

        if len(LotesBloqueados) != len(set(Identificadores)):
            raise ValueError("Um lote do carrinho não está mais disponível.")

        ItensVenda = []
        Total = Decimal("0.00")
        LucroTotal = Decimal("0.00")

        for ChaveItem, ValorQuantidade in Carrinho.items():
            LoteVenda = LotesBloqueados[
                ObterIdentificadorLoteDaChave(ChaveItem)
            ]
            ProdutoVenda = LoteVenda.Produto
            Quantidade = ConverterQuantidade(ValorQuantidade)
            ValidarQuantidadeProduto(ProdutoVenda, Quantidade, LoteVenda)
            Subtotal = (Quantidade * LoteVenda.PrecoVenda).quantize(
                Centavo,
                rounding=ROUND_HALF_UP,
            )
            CustoItem = (Quantidade * LoteVenda.PrecoCusto).quantize(
                Centavo,
                rounding=ROUND_HALF_UP,
            )
            LucroItem = (Subtotal - CustoItem).quantize(Centavo)
            Total += Subtotal
            LucroTotal += LucroItem
            ItensVenda.append(
                (LoteVenda, Quantidade, Subtotal, LucroItem)
            )

        Total = Total.quantize(Centavo, rounding=ROUND_HALF_UP)
        LucroTotal = LucroTotal.quantize(Centavo, rounding=ROUND_HALF_UP)
        ValorRecebido = None
        Troco = Decimal("0.00")
        ContaDaVenda = None

        if FormaPagamento == Venda.DINHEIRO:
            ValorRecebido = ConverterValorRecebido(ValorRecebidoInformado)

            if ValorRecebido < Total:
                ValorFaltante = FormatarValorMoeda(Total - ValorRecebido)
                raise ValueError(f"Faltam R$ {ValorFaltante} para concluir a compra.")

            Troco = (ValorRecebido - Total).quantize(Centavo)

        if FormaPagamento == Venda.CONTA_CLIENTE:
            ContaDaVenda, _ = ContaCliente.objects.select_for_update().get_or_create(
                Proprietario=Request.user,
                NomeCliente=NomeCliente,
                defaults={"Ativa": True},
            )

            if not ContaDaVenda.Ativa:
                ContaDaVenda.Ativa = True
                ContaDaVenda.save(update_fields=["Ativa", "AtualizadaEm"])

        VendaConcluida = Venda.objects.create(
            Proprietario=Request.user,
            NomeCliente=NomeCliente,
            ContaCliente=ContaDaVenda,
            FormaPagamento=FormaPagamento,
            Total=Total,
            Lucro=LucroTotal,
            ValorRecebido=ValorRecebido,
            Troco=Troco,
        )

        ProdutosAtualizados = {}

        for LoteVenda, Quantidade, Subtotal, LucroItem in ItensVenda:
            ProdutoVenda = LoteVenda.Produto
            ItemVenda.objects.create(
                Venda=VendaConcluida,
                Produto=ProdutoVenda,
                Lote=LoteVenda,
                NomeProduto=ProdutoVenda.Nome,
                UnidadeVenda=ProdutoVenda.UnidadeVenda,
                Quantidade=Quantidade,
                CustoUnitario=LoteVenda.PrecoCusto,
                PrecoUnitario=LoteVenda.PrecoVenda,
                Subtotal=Subtotal,
                Lucro=LucroItem,
            )
            if ProdutoVenda.ControlaQuantidadeEstoque():
                LoteVenda.QuantidadeDisponivel -= Quantidade

                if LoteVenda.QuantidadeDisponivel <= 0:
                    LoteVenda.QuantidadeDisponivel = Decimal("0.000")
                    LoteVenda.Ativo = False
                    LoteVenda.Disponivel = False

                LoteVenda.save(
                    update_fields=["QuantidadeDisponivel", "Ativo", "Disponivel"]
                )

            ProdutosAtualizados[ProdutoVenda.id] = ProdutoVenda

        if ContaDaVenda is not None:
            LancamentoContaCliente.objects.create(
                Conta=ContaDaVenda,
                Venda=VendaConcluida,
                Tipo=LancamentoContaCliente.COMPRA,
                Descricao=f"Venda #{VendaConcluida.id}",
                Valor=Total,
            )

        for ProdutoVenda in ProdutosAtualizados.values():
            ProdutoVenda.SincronizarResumoLotes()

    LimparCarrinho(Request, Numero)
    return VendaConcluida
