"""Validacao dos filtros do historico de vendas."""
from django import forms

from .models import Venda


ParametrosFiltrosHistorico = {
    "Busca": "busca",
    "DataInicial": "data_inicial",
    "DataFinal": "data_final",
    "Pagamento": "pagamento",
    "Situacao": "situacao",
}


class FormularioHistoricoVenda(forms.Form):
    Busca = forms.CharField(
        label="Pesquisar", required=False, max_length=200,
        widget=forms.TextInput(attrs={
            "type": "search", "class": "CampoFormulario",
            "placeholder": "Cliente, produto ou número da venda",
        }),
    )
    DataInicial = forms.DateField(
        label="Data inicial", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={
            "type": "date", "class": "CampoFormulario",
        }),
        error_messages={"invalid": "Informe uma data inicial válida."},
    )
    DataFinal = forms.DateField(
        label="Data final", required=False, input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(format="%Y-%m-%d", attrs={
            "type": "date", "class": "CampoFormulario",
        }),
        error_messages={"invalid": "Informe uma data final válida."},
    )
    Pagamento = forms.ChoiceField(
        label="Pagamento", required=False,
        choices=[("", "Todos os pagamentos")] + [
            (Valor, "Conta" if Valor == Venda.CONTA_CLIENTE else Rotulo)
            for Valor, Rotulo in Venda.OpcoesFormaPagamento
        ],
        widget=forms.Select(attrs={"class": "CampoFormulario"}),
        error_messages={"invalid_choice": "Selecione uma forma de pagamento válida."},
    )
    Situacao = forms.ChoiceField(
        label="Situação", required=False,
        choices=[("", "Todas as vendas"), ("atual", "Atuais"), ("arquivada", "Arquivadas")],
        widget=forms.Select(attrs={"class": "CampoFormulario"}),
        error_messages={"invalid_choice": "Selecione uma situação válida."},
    )

    def clean(self):
        Dados = super().clean()
        DataInicial = Dados.get("DataInicial")
        DataFinal = Dados.get("DataFinal")

        if DataInicial and DataFinal and DataFinal < DataInicial:
            self.add_error(
                "DataFinal", "A data final deve ser igual ou posterior à data inicial."
            )

        return Dados
