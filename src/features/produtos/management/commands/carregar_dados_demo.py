"""Carrega cadastros fictícios apenas em um banco ainda vazio."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from features.fornecedor.models import Fornecedor
from features.produtos.models import CategoriaProduto, Produto


FornecedoresDemo = {
    "Distribuidora Bom Preço Demo": {"Cidade": "São Paulo", "Telefone": "(11) 4000-0101"},
    "Atacado Central Demonstração": {"Cidade": "Campinas", "Telefone": "(19) 4000-0202"},
    "Hortifruti Frescor Demo": {"Cidade": "São Paulo", "Telefone": "(11) 4000-0303"},
}

CategoriasDemo = (
    "Mercearia",
    "Bebidas",
    "Limpeza",
    "Higiene",
    "Hortifruti",
)

ProdutosDemo = (
    {
        "Nome": "Arroz Tipo 1 5 kg Demo", "Categoria": "Mercearia", "Marca": "Bom Grão",
        "Fornecedor": "Atacado Central Demonstração", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "24", "EstoqueMinimo": "5", "PrecoCusto": "22.50", "PrecoVenda": "29.90",
    },
    {
        "Nome": "Feijão Carioca 1 kg Demo", "Categoria": "Mercearia", "Marca": "Sabor da Terra",
        "Fornecedor": "Distribuidora Bom Preço Demo", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "30", "EstoqueMinimo": "6", "PrecoCusto": "6.20", "PrecoVenda": "8.49",
    },
    {
        "Nome": "Macarrão Espaguete 500 g Demo", "Categoria": "Mercearia", "Marca": "Massa Leve",
        "Fornecedor": "Atacado Central Demonstração", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "40", "EstoqueMinimo": "8", "PrecoCusto": "3.10", "PrecoVenda": "4.79",
    },
    {
        "Nome": "Café Torrado 500 g Demo", "Categoria": "Mercearia", "Marca": "Café da Serra",
        "Fornecedor": "Distribuidora Bom Preço Demo", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "18", "EstoqueMinimo": "4", "PrecoCusto": "14.00", "PrecoVenda": "19.90",
    },
    {
        "Nome": "Leite Integral 1 L Demo", "Categoria": "Bebidas", "Marca": "Vale do Leite",
        "Fornecedor": "Atacado Central Demonstração", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "36", "EstoqueMinimo": "10", "PrecoCusto": "4.10", "PrecoVenda": "5.49",
    },
    {
        "Nome": "Suco de Uva 1 L Demo", "Categoria": "Bebidas", "Marca": "Fruta Boa",
        "Fornecedor": "Distribuidora Bom Preço Demo", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "15", "EstoqueMinimo": "4", "PrecoCusto": "7.50", "PrecoVenda": "10.90",
    },
    {
        "Nome": "Detergente Neutro 500 ml Demo", "Categoria": "Limpeza", "Marca": "Brilho Fácil",
        "Fornecedor": "Distribuidora Bom Preço Demo", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "28", "EstoqueMinimo": "6", "PrecoCusto": "1.65", "PrecoVenda": "2.79",
    },
    {
        "Nome": "Sabão em Pó 1,6 kg Demo", "Categoria": "Limpeza", "Marca": "Casa Limpa",
        "Fornecedor": "Atacado Central Demonstração", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "12", "EstoqueMinimo": "3", "PrecoCusto": "12.00", "PrecoVenda": "16.90",
    },
    {
        "Nome": "Papel Higiênico 12 Rolos Demo", "Categoria": "Higiene", "Marca": "Toque Macio",
        "Fornecedor": "Atacado Central Demonstração", "UnidadeVenda": Produto.UNIDADE,
        "QuantidadeEstoque": "20", "EstoqueMinimo": "5", "PrecoCusto": "13.50", "PrecoVenda": "18.99",
    },
    {
        "Nome": "Banana Prata Demo", "Categoria": "Hortifruti", "Marca": "Hortifruti Frescor",
        "Fornecedor": "Hortifruti Frescor Demo", "UnidadeVenda": Produto.QUILOGRAMA,
        "QuantidadeEstoque": None, "EstoqueMinimo": None, "PrecoCusto": "4.00", "PrecoVenda": "6.99",
    },
    {
        "Nome": "Tomate Italiano Demo", "Categoria": "Hortifruti", "Marca": "Hortifruti Frescor",
        "Fornecedor": "Hortifruti Frescor Demo", "UnidadeVenda": Produto.QUILOGRAMA,
        "QuantidadeEstoque": None, "EstoqueMinimo": None, "PrecoCusto": "5.00", "PrecoVenda": "8.49",
    },
)


class Command(BaseCommand):
    help = "Cria fornecedores, categorias e produtos fictícios em um banco vazio."

    @transaction.atomic
    def handle(self, *args, **options):
        if (
            CategoriaProduto.objects.exists()
            or Fornecedor.objects.exists()
            or Produto.objects.exists()
        ):
            self.stdout.write(
                self.style.WARNING(
                    "Banco não está vazio; os dados de demonstração não foram carregados."
                )
            )
            return

        Categorias = {
            Nome: CategoriaProduto.objects.create(Nome=Nome)
            for Nome in CategoriasDemo
        }
        Fornecedores = {
            Nome: Fornecedor.objects.create(Nome=Nome, **Dados)
            for Nome, Dados in FornecedoresDemo.items()
        }

        for DadosProduto in ProdutosDemo:
            Dados = DadosProduto.copy()
            FornecedorNome = Dados.pop("Fornecedor")
            Dados["Fornecedor"] = Fornecedores[FornecedorNome]
            for Campo in ("PrecoCusto", "PrecoVenda"):
                Dados[Campo] = Decimal(Dados[Campo])
            Produto.objects.create(**Dados)

        self.stdout.write(
            self.style.SUCCESS(
                f"Dados de demonstração criados: {len(Fornecedores)} fornecedores, "
                f"{len(Categorias)} categorias e {len(ProdutosDemo)} produtos."
            )
        )
