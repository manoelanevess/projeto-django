"""Preserva as categorias usadas e permite cadastrá-las antes dos produtos."""
from unicodedata import normalize as NormalizarUnicode

from django.db import migrations, models


def ImportarCategoriasExistentes(Apps, SchemaEditor):
    Produto = Apps.get_model("produtos", "Produto")
    CategoriaProduto = Apps.get_model("produtos", "CategoriaProduto")
    Banco = SchemaEditor.connection.alias
    Nomes = Produto.objects.using(Banco).exclude(Categoria="").order_by().values_list("Categoria", flat=True).distinct()
    for Nome in Nomes:
        Nome = NormalizarUnicode("NFC", " ".join(Nome.split())).title()
        if Nome:
            CategoriaProduto.objects.using(Banco).get_or_create(Nome=Nome)


class Migration(migrations.Migration):
    dependencies = [("produtos", "0009_identificacaoproduto")]

    operations = [
        migrations.CreateModel(
            name="CategoriaProduto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("Nome", models.CharField(max_length=80, unique=True)),
            ],
            options={
                "ordering": ["Nome"],
                "verbose_name": "categoria de produto",
                "verbose_name_plural": "categorias de produtos",
            },
        ),
        migrations.RunPython(ImportarCategoriasExistentes, migrations.RunPython.noop),
    ]
