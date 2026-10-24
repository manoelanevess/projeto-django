"""Padronização dos nomes de cadastro em todas as entradas do sistema."""
from unicodedata import normalize as NormalizarUnicode


def NormalizarNomeCadastro(Valor):
    return NormalizarUnicode("NFC", " ".join(str(Valor or "").split())).title()


class NomesCadastroMixin:
    CamposNomesCadastro = ()

    def NormalizarNomesCadastro(self, Campos=None):
        for Campo in self.CamposNomesCadastro:
            if Campos is None or Campo in Campos:
                setattr(self, Campo, NormalizarNomeCadastro(getattr(self, Campo)))

    def clean(self):
        self.NormalizarNomesCadastro()
        super().clean()

    def save(self, *args, **kwargs):
        self.NormalizarNomesCadastro(kwargs.get("update_fields"))
        return super().save(*args, **kwargs)


def ObterScriptNomesCadastro():
    return r"""
    <script>
        (() => {
            const Seletor = 'input[name="Nome"], input[name="Marca"], input[name="Categoria"], input[name="Cidade"], input[name="nome_cliente"], input[name="NomeComercio"]';
            const Normalizar = (Campo) => {
                Campo.value = Campo.value.normalize("NFC").trim().replace(/\s+/gu, " ").toLocaleLowerCase("pt-BR")
                    .replace(/(^|[^\p{L}])(\p{L})/gu, (_, Antes, Letra) => Antes + Letra.toLocaleUpperCase("pt-BR"));
            };
            document.addEventListener("focusout", (Evento) => {
                if (Evento.target.matches?.(Seletor)) Normalizar(Evento.target);
            }, true);
            document.addEventListener("submit", (Evento) => {
                Evento.target.querySelectorAll(Seletor).forEach(Normalizar);
            }, true);
        })();
    </script>
    """
