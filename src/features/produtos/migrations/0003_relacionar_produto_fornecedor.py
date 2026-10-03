import django.db.models.deletion
from django.db import migrations, models


def RelacionarFornecedoresExistentes(Apps, SchemaEditor):
    ProdutoHistorico = Apps.get_model("produtos", "Produto")
    FornecedorHistorico = Apps.get_model("fornecedor", "Fornecedor")

    for ProdutoEstoque in ProdutoHistorico.objects.all().iterator():
        NomeFornecedor = " ".join(
            str(ProdutoEstoque.Fornecedor or "Não informado").split()
        )
        NomeFornecedor = NomeFornecedor or "Não informado"
        FornecedorProduto = FornecedorHistorico.objects.filter(
            Nome__iexact=NomeFornecedor
        ).first()

        if FornecedorProduto is None:
            FornecedorProduto = FornecedorHistorico.objects.create(
                Nome=NomeFornecedor
            )

        ProdutoHistorico.objects.filter(pk=ProdutoEstoque.pk).update(
            FornecedorCadastro_id=FornecedorProduto.pk
        )


def RestaurarNomesFornecedores(Apps, SchemaEditor):
    ProdutoHistorico = Apps.get_model("produtos", "Produto")
    FornecedorHistorico = Apps.get_model("fornecedor", "Fornecedor")

    for ProdutoEstoque in ProdutoHistorico.objects.all().iterator():
        NomeFornecedor = "Não informado"

        if ProdutoEstoque.FornecedorCadastro_id:
            FornecedorProduto = FornecedorHistorico.objects.filter(
                pk=ProdutoEstoque.FornecedorCadastro_id
            ).first()

            if FornecedorProduto:
                NomeFornecedor = FornecedorProduto.Nome

        ProdutoHistorico.objects.filter(pk=ProdutoEstoque.pk).update(
            Fornecedor=NomeFornecedor
        )


class Migration(migrations.Migration):
    dependencies = [
        ("fornecedor", "0001_initial"),
        ("produtos", "0002_produto_disponivel_produto_fornecedor_produto_marca_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="FornecedorCadastro",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="Produtos",
                to="fornecedor.fornecedor",
            ),
        ),
        migrations.RunPython(
            RelacionarFornecedoresExistentes,
            RestaurarNomesFornecedores,
        ),
        migrations.RemoveField(
            model_name="produto",
            name="Fornecedor",
        ),
        migrations.RenameField(
            model_name="produto",
            old_name="FornecedorCadastro",
            new_name="Fornecedor",
        ),
        migrations.AlterField(
            model_name="produto",
            name="Fornecedor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="Produtos",
                to="fornecedor.fornecedor",
            ),
        ),
    ]
