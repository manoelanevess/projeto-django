"""Cadastro rápido de categorias a partir do estoque."""
from html import escape
from urllib.parse import urlencode

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods as ExigirMetodos

from componentes.LayoutBase import RenderizarLayoutBase

from .ComponenteProduto import DefinirMensagemProduto
from .FormularioCategoria import FormularioCategoriaProduto


CamposFiltroEstoque = ("busca", "inicio", "categoria", "fornecedor", "estoque")


def ObterFiltrosRetornoCategoria(Request):
    Dados = Request.POST if Request.method == "POST" else Request.GET
    Prefixo = "retorno_" if Request.method == "POST" else ""
    return {Campo: Dados.get(f"{Prefixo}{Campo}", "").strip() for Campo in CamposFiltroEstoque}


def RenderizarFormularioCategoria(Formulario, TokenCsrf, Filtros, EmDialogo=False):
    CamposOcultos = "".join(
        f'<input type="hidden" name="retorno_{Campo}" value="{escape(Filtros.get(Campo, ""))}">'
        for Campo in CamposFiltroEstoque
    )
    Erros = "".join(f'<p class="ErroCategoria" role="alert">{escape(str(Erro))}</p>'
                   for Erro in [*Formulario.non_field_errors(), *Formulario["Nome"].errors])
    Cancelar = ('<button class="BotaoSecundario" type="button" data-cancelar-categoria>Cancelar</button>'
                if EmDialogo else '<a class="BotaoSecundario" href="/estoque">Cancelar</a>')
    Atributos = {"id": "NomeNovaCategoria"}
    if not EmDialogo:
        Atributos["autofocus"] = True
    CampoNome = Formulario["Nome"].as_widget(attrs=Atributos)
    return f"""
    <form class="FormularioNovaCategoria" method="post" action="/estoque/categorias/nova">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        {CamposOcultos}
        <h2 id="TituloNovaCategoria">Adicionar categoria</h2>
        <p>A categoria ficará disponível na lista do cadastro de produtos.</p>
        <label for="NomeNovaCategoria">Nome da categoria</label>
        {CampoNome}
        {Erros}
        <div class="AcoesNovaCategoria">
            {Cancelar}
            <button class="BotaoPrimario" type="submit">Adicionar categoria</button>
        </div>
    </form>
    """


def ObterEstilosCategoria():
    return """
    <style>
        .DialogoNovaCategoria { width: min(440px, calc(100vw - 32px)); padding: 24px; border: 0; border-radius: 10px; }
        .DialogoNovaCategoria::backdrop { background: rgba(20, 32, 44, 0.4); }
        .FormularioNovaCategoria { display: grid; gap: 12px; }
        .FormularioNovaCategoria h2, .FormularioNovaCategoria p { margin: 0; }
        .FormularioNovaCategoria p { color: #536577; line-height: 1.5; }
        .FormularioNovaCategoria label { margin-top: 6px; font-weight: 600; }
        .FormularioNovaCategoria .CampoFormulario { width: 100%; min-width: 0; }
        .AcoesNovaCategoria { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 10px; margin-top: 8px; }
        .FormularioNovaCategoria .ErroCategoria { color: #a12c25; }
        .PainelNovaCategoria { max-width: 480px; margin: 0 auto; background: white; padding: 24px; border-radius: 10px; }
    </style>
    """


def RenderizarDialogoCategoria(TokenCsrf, Filtros):
    FormularioHtml = RenderizarFormularioCategoria(FormularioCategoriaProduto(), TokenCsrf, Filtros, EmDialogo=True)
    return ObterEstilosCategoria() + f"""
    <dialog class="DialogoNovaCategoria" id="DialogoNovaCategoria" aria-labelledby="TituloNovaCategoria">
        {FormularioHtml}
    </dialog>
    <script>
        (() => {{
            const Dialogo = document.getElementById("DialogoNovaCategoria");
            document.querySelector("[data-adicionar-categoria]").addEventListener("click", (Evento) => {{
                if (Evento.ctrlKey || Evento.metaKey || Evento.shiftKey || Evento.altKey) return;
                Evento.preventDefault();
                const Filtro = document.getElementById("FormularioBuscaEstoque");
                const Valores = new FormData(Filtro);
                Dialogo.querySelectorAll('[name^="retorno_"]').forEach((Campo) => {{
                    Campo.value = Valores.get(Campo.name.slice(8)) || "";
                }});
                Dialogo.showModal();
            }});
            Dialogo.querySelector("[data-cancelar-categoria]").addEventListener("click", () => Dialogo.close());
        }})();
    </script>
    """


@ExigirMetodos(["GET", "POST"])
def ComponenteFormularioCategoriaProduto(Request):
    Filtros = ObterFiltrosRetornoCategoria(Request)
    Formulario = FormularioCategoriaProduto(Request.POST if Request.method == "POST" else None)
    if Request.method == "POST" and Formulario.is_valid():
        try:
            with transaction.atomic():
                Categoria = Formulario.save()
        except IntegrityError:
            Formulario.add_error("Nome", "Esta categoria já está cadastrada.")
        else:
            DefinirMensagemProduto(Request, f"Categoria {Categoria.Nome} cadastrada. Já está disponível no cadastro de produtos.")
            Parametros = urlencode({Campo: Valor for Campo, Valor in Filtros.items() if Valor})
            return redirect(f"/estoque?{Parametros}" if Parametros else "/estoque")

    Conteudo = (ObterEstilosCategoria() + '<section class="PainelNovaCategoria">'
                + RenderizarFormularioCategoria(Formulario, ObterTokenCsrf(Request), Filtros) + '</section>')
    return HttpResponse(RenderizarLayoutBase("Adicionar categoria", Conteudo, RotaAtiva="estoque", Request=Request))
