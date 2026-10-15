from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("produtos", "0007_codigo_barras_produto"),
    ]

    operations = [
        migrations.AddField(
            model_name="loteestoque",
            name="DataValidade",
            field=models.DateField(blank=True, null=True, verbose_name="data de validade"),
        ),
    ]
