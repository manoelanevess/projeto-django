"""Sugestoes de cadastro a partir do codigo de barras."""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache as NaoArmazenarResposta
from django.views.decorators.http import require_GET as ExigirGet
from django.views.decorators.http import require_POST as ExigirPost

from .ApiCatalogoProduto import ConsultarCatalogoProduto
from .ApiProduto import BuscarProdutoPorCodigoBarras
from .ApiPesquisaWebProduto import PesquisarProdutoNaWeb, PesquisaWebEstaConfigurada
from .LogicaCodigoBarras import NormalizarCodigoBarras


@NaoArmazenarResposta
@ExigirGet
def ComponenteConsultarCatalogoProduto(Request):
    try:
        Codigo = NormalizarCodigoBarras(Request.GET.get("codigo"), Obrigatorio=True)
    except ValueError as Erro:
        return JsonResponse({"Situacao": "codigo_invalido", "Mensagem": str(Erro)}, status=400)

    ProdutoEncontrado = BuscarProdutoPorCodigoBarras(Codigo)
    if ProdutoEncontrado is not None:
        if not ProdutoEncontrado.Ativo:
            return JsonResponse({
                "Situacao": "inativo", "Mensagem": "Este código pertence a um produto inativo.",
            })
        return JsonResponse({
            "Situacao": "cadastrado",
            "Destino": f"/estoque/{ProdutoEncontrado.pk}/editar?entrada=1#NovaEntradaEstoque",
        })

    Resultado = ConsultarCatalogoProduto(Codigo)
    Mensagens = {
        "encontrado": "Sugestões encontradas.",
        "nao_encontrado": "Produto não encontrado no catálogo. Informe nome, marca e categoria manualmente.",
        "indisponivel": "Catálogo indisponível no momento.",
        "codigo_nao_consultavel": "Sem consulta externa para este código.",
    }
    return JsonResponse({
        **Resultado, "Mensagem": Mensagens[Resultado["Situacao"]],
        "PesquisaWebDisponivel": Resultado["Situacao"] in ("nao_encontrado", "indisponivel") and PesquisaWebEstaConfigurada(),
    })


@NaoArmazenarResposta
@ExigirPost
def ComponentePesquisarCodigoWeb(Request):
    try:
        Codigo = NormalizarCodigoBarras(Request.POST.get("codigo"), Obrigatorio=True)
    except ValueError as Erro:
        return JsonResponse({"Situacao": "codigo_invalido", "Mensagem": str(Erro)}, status=400)
    ProdutoLocal = BuscarProdutoPorCodigoBarras(Codigo)
    if ProdutoLocal is not None:
        if not ProdutoLocal.Ativo:
            return JsonResponse({"Situacao": "inativo", "Mensagem": "Este código pertence a um produto inativo."})
        return JsonResponse({"Situacao": "cadastrado", "Destino": f"/estoque/{ProdutoLocal.pk}/editar?entrada=1#NovaEntradaEstoque"})
    Resultado = PesquisarProdutoNaWeb(Codigo, Request.user.pk)
    Mensagens = {
        "encontrado": "Sugestões da internet. Confira os dados antes de cadastrar.",
        "nao_encontrado": "Não foi possível identificar o produto na internet. Preencha os campos manualmente.",
        "nao_configurada": "Pesquisa na internet ainda não configurada. Preencha os campos manualmente.",
        "indisponivel": "Pesquisa na internet indisponível no momento. Preencha os campos manualmente.",
        "limite": "Limite de pesquisas atingido. Tente mais tarde ou preencha os campos manualmente.",
        "codigo_nao_consultavel": "Sem pesquisa na internet para este código.",
    }
    return JsonResponse({**Resultado, "Mensagem": Mensagens[Resultado["Situacao"]]})


def ObterScriptConsultaCatalogoProduto(ConsultarInicial=False):
    return """
    <script>
        (() => {
            const CampoCodigo = document.getElementById("id_CodigoBarras");
            const Estado = document.getElementById("ConsultaCatalogoProduto");
            const Mensagem = document.getElementById("MensagemCatalogoProduto");
            const Fonte = document.getElementById("FonteCatalogoProduto");
            const Campos = ["Nome", "Marca", "Categoria"].map((Nome) => document.getElementById(`id_${Nome}`));
            const CamposManuais = new Set(Campos.filter((Campo) => Campo.value));
            const Sugestoes = new Map();
            let Sequencia = 0;
            let Controlador = null;
            let UltimoCodigo = null;
            let AgendamentoConsulta = null;

            Campos.forEach((Campo) => Campo.addEventListener("input", () => CamposManuais.add(Campo)));

            const InvalidarConsulta = () => {
                clearTimeout(AgendamentoConsulta);
                AgendamentoConsulta = null;
                Sequencia += 1;
                Controlador?.abort();
                Controlador = null;
                Estado.setAttribute("aria-busy", "false");
            };

            CampoCodigo.addEventListener("input", () => {
                InvalidarConsulta();
                Estado.hidden = true;
                Fonte.hidden = true;
                UltimoCodigo = null;
                Sugestoes.forEach((Valor, Campo) => {
                    if (!CamposManuais.has(Campo) && Campo.value === Valor) Campo.value = "";
                });
                Sugestoes.clear();
                if (/^(?:[0-9]{8}|[0-9]{12,14})$/.test(CampoCodigo.value.trim())) {
                    AgendamentoConsulta = setTimeout(ConsultarCodigo, 350);
                }
            });

            const ConsultarCodigo = async () => {
                const Codigo = CampoCodigo.value.trim();
                if (Codigo === UltimoCodigo && Controlador !== null) return;
                InvalidarConsulta();
                if (!Codigo) {
                    Estado.hidden = true;
                    return;
                }
                UltimoCodigo = Codigo;
                const Versao = Sequencia;
                Controlador = new AbortController();
                const Sinal = Controlador.signal;
                const ControladorConsulta = Controlador;
                let TempoLimite = setTimeout(() => ControladorConsulta.abort(), 6000);
                Estado.hidden = false;
                Fonte.hidden = true;
                Estado.setAttribute("aria-busy", "true");
                Mensagem.textContent = "Consultando produto...";
                try {
                    const Resposta = await fetch(`/estoque/consultar-codigo?${new URLSearchParams({ codigo: Codigo })}`, {
                        headers: { "Accept": "application/json" }, signal: Sinal,
                    });
                    let Resultado = await Resposta.json();
                    if (Versao !== Sequencia || CampoCodigo.value.trim() !== Codigo) return;
                    if (Resultado.PesquisaWebDisponivel) {
                        clearTimeout(TempoLimite);
                        TempoLimite = setTimeout(() => ControladorConsulta.abort(), 40000);
                        Mensagem.textContent = "Pesquisando produto na internet...";
                        const RespostaWeb = await fetch("/estoque/pesquisar-codigo-web", {
                            method: "POST", signal: Sinal,
                            headers: { "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded" },
                            body: new URLSearchParams({
                                codigo: Codigo,
                                csrfmiddlewaretoken: CampoCodigo.form.elements.csrfmiddlewaretoken.value,
                            }),
                        });
                        Resultado = await RespostaWeb.json();
                        if (Versao !== Sequencia || CampoCodigo.value.trim() !== Codigo) return;
                    }
                    if (Resultado.Situacao === "cadastrado") {
                        window.location.assign(Resultado.Destino);
                        return;
                    }
                    Mensagem.textContent = Resultado.Mensagem || "Catálogo indisponível no momento.";
                    if (Resultado.Situacao === "encontrado") {
                        Campos.forEach((Campo) => {
                            const Valor = Resultado.Dados[Campo.name];
                            if (Valor && !CamposManuais.has(Campo)) {
                                Campo.value = Valor;
                                Sugestoes.set(Campo, Valor);
                            }
                        });
                        if (!Object.keys(Resultado.Dados).length) Mensagem.textContent = "Produto encontrado sem dados de cadastro.";
                        const LinkFonte = Fonte.querySelector("a");
                        LinkFonte.textContent = Resultado.Fonte?.Nome || "Open Food Facts";
                        LinkFonte.href = Resultado.Fonte?.Url || `https://world.openfoodfacts.org/product/${encodeURIComponent(Codigo)}`;
                        document.getElementById("LicencaCatalogoProduto").hidden = Boolean(Resultado.Fonte?.Complementar || Resultado.Fonte?.PesquisaWeb);
                        Fonte.hidden = false;
                    }
                } catch (Erro) {
                    if (Versao === Sequencia) Mensagem.textContent = "Catálogo indisponível no momento.";
                } finally {
                    clearTimeout(TempoLimite);
                    if (Versao === Sequencia) {
                        Estado.setAttribute("aria-busy", "false");
                        Controlador = null;
                    }
                }
            };

            CampoCodigo.addEventListener("keydown", (Evento) => {
                if (Evento.key !== "Enter" || Evento.isComposing) return;
                Evento.preventDefault();
                if (!Evento.repeat) ConsultarCodigo();
            });
            CampoCodigo.addEventListener("change", () => {
                if (CampoCodigo.value.trim() !== UltimoCodigo) ConsultarCodigo();
            });
            CampoCodigo.form.addEventListener("submit", InvalidarConsulta);
            if (__ConsultarInicial__) ConsultarCodigo();
        })();
    </script>
    """.replace("__ConsultarInicial__", "true" if ConsultarInicial else "false")
