from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vendas", "0005_alter_venda_formapagamento_contacliente_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contacliente",
            name="ExcluidaEm",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
