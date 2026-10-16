"""Sugestoes de cadastro a partir do codigo de barras."""
from django.http import JsonResponse
from django.views.decorators.cache import never_cache as NaoArmazenarResposta
from django.views.decorators.http import require_GET as ExigirGet
from django.views.decorators.http import require_POST as ExigirPost

from .ApiCatalogoProduto import ConsultarCatalogoProduto
from .ApiCatalogoEan import CatalogoEanEstaConfigurado, ConsultarCatalogoEan
from .ApiProduto import BuscarProdutoPorCodigoBarras
from .ApiPesquisaWebProduto import PesquisarProdutoNaWeb, PesquisaWebEstaConfigurada
from .LogicaCodigoBarras import EhCodigoGtin, NormalizarCodigoBarras
from .LogicaIdentificacaoProduto import (
    GuardarIdentificacaoProduto, ObterIdentificacaoProduto, SerializarIdentificacaoProduto,
)


def ObterResultadoLocal(Codigo):
    ProdutoLocal = BuscarProdutoPorCodigoBarras(Codigo)
    if ProdutoLocal is not None:
        if not ProdutoLocal.Ativo:
            return {"Situacao": "inativo", "Mensagem": "Este código pertence a um produto inativo."}
        return {"Situacao": "cadastrado", "Destino": f"/estoque/{ProdutoLocal.pk}/editar?entrada=1#NovaEntradaEstoque"}
    Registro = ObterIdentificacaoProduto(Codigo)
    if Registro is not None:
        Resultado = SerializarIdentificacaoProduto(Registro)
        if Resultado["Completo"]:
            return {**Resultado, "Mensagem": "Produto identificado. Confira os dados antes de cadastrar."}
    return None


def PrepararResultado(Codigo, Resultado, PermitirEan=False, PermitirWeb=False):
    if Resultado["Situacao"] == "encontrado":
        Resultado = GuardarIdentificacaoProduto(Codigo, Resultado)
    else:
        Registro = ObterIdentificacaoProduto(Codigo)
        if Registro is not None:
            Parcial = SerializarIdentificacaoProduto(Registro)
            Resultado = {**Resultado, **Parcial}
    Completo = Resultado.get("Completo", False)
    Mensagens = {
        "encontrado": "Produto identificado. Confira os dados antes de cadastrar." if Completo else "Dados parciais encontrados. Complete os campos que faltam.",
        "nao_encontrado": "Produto não identificado. Informe nome e marca manualmente.",
        "indisponivel": "Consulta indisponível no momento. Você pode preencher nome e marca.",
        "aguardando": "Aguardando uma nova consulta...",
        "nao_configurada": "Pesquisa não configurada. Informe nome e marca manualmente.",
        "limite": "Limite de consultas atingido. Você pode preencher nome e marca.",
        "codigo_nao_consultavel": "Sem consulta externa para este código.",
    }
    PodeComplementar = not Completo and EhCodigoGtin(Codigo)
    return {
        **Resultado, "Mensagem": Mensagens[Resultado["Situacao"]],
        "PesquisaEanDisponivel": PermitirEan and PodeComplementar and CatalogoEanEstaConfigurado(),
        "PesquisaWebDisponivel": PermitirWeb and PodeComplementar and PesquisaWebEstaConfigurada(),
    }


@NaoArmazenarResposta
@ExigirGet
def ComponenteConsultarCatalogoProduto(Request):
    try:
        Codigo = NormalizarCodigoBarras(Request.GET.get("codigo"), Obrigatorio=True)
    except ValueError as Erro:
        return JsonResponse({"Situacao": "codigo_invalido", "Mensagem": str(Erro)}, status=400)

    ResultadoLocal = ObterResultadoLocal(Codigo)
    if ResultadoLocal is not None:
        return JsonResponse(ResultadoLocal)
    return JsonResponse(PrepararResultado(Codigo, ConsultarCatalogoProduto(Codigo), PermitirEan=True, PermitirWeb=True))


@NaoArmazenarResposta
@ExigirPost
def ComponenteComplementarCodigo(Request):
    try:
        Codigo = NormalizarCodigoBarras(Request.POST.get("codigo"), Obrigatorio=True)
    except ValueError as Erro:
        return JsonResponse({"Situacao": "codigo_invalido", "Mensagem": str(Erro)}, status=400)
    ResultadoLocal = ObterResultadoLocal(Codigo)
    if ResultadoLocal is not None:
        return JsonResponse(ResultadoLocal)
    return JsonResponse(PrepararResultado(Codigo, ConsultarCatalogoEan(Codigo), PermitirWeb=True))


@NaoArmazenarResposta
@ExigirPost
def ComponentePesquisarCodigoWeb(Request):
    try:
        Codigo = NormalizarCodigoBarras(Request.POST.get("codigo"), Obrigatorio=True)
    except ValueError as Erro:
        return JsonResponse({"Situacao": "codigo_invalido", "Mensagem": str(Erro)}, status=400)
    ResultadoLocal = ObterResultadoLocal(Codigo)
    if ResultadoLocal is not None:
        return JsonResponse(ResultadoLocal)
    return JsonResponse(PrepararResultado(Codigo, PesquisarProdutoNaWeb(Codigo, Request.user.pk)))


def ObterScriptConsultaCatalogoProduto(ConsultarInicial=False):
    return """
    <script>
        (() => {
            const CampoCodigo = document.getElementById("id_CodigoBarras");
            const Estado = document.getElementById("ConsultaCatalogoProduto");
            const Mensagem = document.getElementById("MensagemCatalogoProduto");
            const Fonte = document.getElementById("FonteCatalogoProduto");
            const Campos = ["Nome", "Marca"].map((Nome) => document.getElementById(`id_${Nome}`));
            const CamposManuais = new Set(Campos.filter((Campo) => Campo.value));
            const Sugestoes = new Map();
            let Sequencia = 0;
            let Controlador = null;
            let UltimoCodigo = null;
            let AgendamentoConsulta = null;

            Campos.forEach((Campo) => Campo.addEventListener("input", () => CamposManuais.add(Campo)));

            const AplicarResultado = (Resultado) => {
                if (Resultado.Situacao === "cadastrado") {
                    window.location.assign(Resultado.Destino);
                    return;
                }
                Mensagem.textContent = Resultado.Mensagem || "Consulta indisponível no momento.";
                if (Resultado.Situacao !== "encontrado") return;
                Campos.forEach((Campo) => {
                    const Valor = Resultado.Dados[Campo.name];
                    if (Valor && !CamposManuais.has(Campo)) {
                        Campo.value = Valor;
                        Sugestoes.set(Campo, Valor);
                    }
                });
                Fonte.replaceChildren();
                const Fontes = Resultado.Fontes || (Resultado.Fonte ? [Resultado.Fonte] : []);
                Fontes.forEach((Referencia, Indice) => {
                    let Url;
                    try { Url = new URL(Referencia.Url); } catch { return; }
                    if (Url.protocol !== "https:") return;
                    Fonte.append(document.createTextNode(Indice ? "; " : " Fonte: "));
                    const Link = document.createElement("a");
                    Link.textContent = Referencia.Nome;
                    Link.href = Url.href;
                    Link.target = "_blank";
                    Link.rel = "noopener noreferrer";
                    Fonte.append(Link);
                    if (!Referencia.Complementar && !Referencia.PesquisaWeb && !Referencia.CatalogoEan) {
                        const Licenca = document.createElement("a");
                        Licenca.textContent = "ODbL";
                        Licenca.href = "https://opendatacommons.org/licenses/odbl/1-0/";
                        Licenca.target = "_blank";
                        Licenca.rel = "noopener noreferrer";
                        Fonte.append(document.createTextNode(" ("), Licenca, document.createTextNode(")"));
                    }
                });
                Fonte.hidden = !Fonte.childNodes.length;
            };

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
                const TempoLimite = setTimeout(() => ControladorConsulta.abort(), 60000);
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
                    if (Resultado.TentarNovamenteEm) {
                        AplicarResultado(Resultado);
                        await new Promise((Resolver) => {
                            const Espera = setTimeout(Resolver, Math.min(Resultado.TentarNovamenteEm, 5) * 1000);
                            Sinal.addEventListener("abort", () => { clearTimeout(Espera); Resolver(); }, { once: true });
                        });
                        if (Sinal.aborted || Versao !== Sequencia) return;
                        const NovaResposta = await fetch(`/estoque/consultar-codigo?${new URLSearchParams({ codigo: Codigo })}`, {
                            headers: { "Accept": "application/json" }, signal: Sinal,
                        });
                        Resultado = await NovaResposta.json();
                        if (Versao !== Sequencia || CampoCodigo.value.trim() !== Codigo) return;
                    }
                    AplicarResultado(Resultado);
                    for (const [Disponivel, Rota, Texto] of [
                        ["PesquisaEanDisponivel", "/estoque/complementar-codigo", "Consultando outros catálogos..."],
                        ["PesquisaWebDisponivel", "/estoque/pesquisar-codigo-web", "Pesquisando produto na internet..."],
                    ]) {
                        if (!Resultado[Disponivel]) continue;
                        if (Campos.every((Campo) => Campo.value.trim() || CamposManuais.has(Campo))) break;
                        Mensagem.textContent = Texto;
                        const RespostaComplementar = await fetch(Rota, {
                            method: "POST", signal: Sinal,
                            headers: { "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded" },
                            body: new URLSearchParams({
                                codigo: Codigo,
                                csrfmiddlewaretoken: CampoCodigo.form.elements.csrfmiddlewaretoken.value,
                            }),
                        });
                        Resultado = await RespostaComplementar.json();
                        if (Versao !== Sequencia || CampoCodigo.value.trim() !== Codigo) return;
                        AplicarResultado(Resultado);
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
