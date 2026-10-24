from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="ConfiguracaoComercio",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("NomeComercio", models.CharField(default="Controle de Estoque", max_length=120)),
            ],
            options={
                "verbose_name": "configuração do comércio", "verbose_name_plural": "configurações do comércio",
                "constraints": [models.CheckConstraint(condition=models.Q(id=1), name="ConfiguracaoComercioUnica")],
            },
        ),
        migrations.CreateModel(
            name="PerfilUsuario",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("FotoConteudo", models.BinaryField(blank=True, default=bytes)),
                ("FotoTipo", models.CharField(blank=True, max_length=30)),
                ("FotoVersao", models.CharField(blank=True, max_length=64)),
                ("Usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="PerfilComercio", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "perfil do usuário", "verbose_name_plural": "perfis dos usuários"},
        ),
    ]
