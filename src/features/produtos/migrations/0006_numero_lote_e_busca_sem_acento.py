from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations, models


def PrepararProdutosELotes(Apps, SchemaEditor):
    Produto = Apps.get_model("produtos", "Produto")
    LoteEstoque = Apps.get_model("produtos", "LoteEstoque")

    for ProdutoExistente in Produto.objects.all().iterator():
        Nome = ProdutoExistente.Nome

        if Nome:
            NomeNormalizado = Nome[0].upper() + Nome[1:]
            Produto.objects.filter(pk=ProdutoExistente.pk).update(
                Nome=NomeNormalizado
            )

    ProdutosComLotes = (
        LoteEstoque.objects.order_by()
        .values_list("Produto_id", flat=True)
        .distinct()
    )

    for ProdutoId in ProdutosComLotes:
        Lotes = LoteEstoque.objects.filter(Produto_id=ProdutoId).order_by("id")

        for Numero, Lote in enumerate(Lotes, start=1):
            LoteEstoque.objects.filter(pk=Lote.pk).update(Numero=Numero)


class Migration(migrations.Migration):
    dependencies = [
        ("produtos", "0005_loteestoque"),
    ]

    operations = [
        UnaccentExtension(),
        migrations.AddField(
            model_name="loteestoque",
            name="Numero",
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
        migrations.RunPython(
            PrepararProdutosELotes,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="loteestoque",
            name="Numero",
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AddConstraint(
            model_name="loteestoque",
            constraint=models.UniqueConstraint(
                fields=("Produto", "Numero"),
                name="LoteNumeroUnicoPorProduto",
            ),
        ),
    ]
