"""Pesquisa incremental em listagens MPA, preservando formulario e query string."""
import json


def ObterScriptBuscaIncremental(FormularioId, CampoId, ResultadosId, ErroId):
    Configuracao = json.dumps({
        "Formulario": FormularioId, "Campo": CampoId, "Resultados": ResultadosId, "Erro": ErroId,
    }).replace("</", "<\\/")
    return """
    <script>
        (() => {
            const Configuracao = __CONFIGURACAO__;
            const Formulario = document.getElementById(Configuracao.Formulario);
            const Campo = document.getElementById(Configuracao.Campo);
            const Resultados = document.getElementById(Configuracao.Resultados);
            const ErroBusca = document.getElementById(Configuracao.Erro);
            let Temporizador;
            let Controle;

            const Cancelar = () => {
                clearTimeout(Temporizador);
                Controle?.abort();
                Controle = null;
                Resultados.removeAttribute("aria-busy");
            };
            const AtualizarUrl = () => {
                const Endereco = new URL(Formulario.action);
                if (Endereco.pathname === window.location.pathname) Endereco.search = window.location.search;
                Array.from(Formulario.elements).forEach((Campo) => {
                    if (Campo.name) Endereco.searchParams.delete(Campo.name);
                });
                const Parametros = new URLSearchParams(new FormData(Formulario));
                Parametros.forEach((Valor, Nome) => {
                    if (Valor.trim()) Endereco.searchParams.set(Nome, Valor.trim());
                });
                window.history.replaceState(null, "", Endereco);
                return Endereco;
            };
            const Pesquisar = async () => {
                Cancelar();
                const Endereco = AtualizarUrl();
                const Atual = new AbortController();
                Controle = Atual;
                Resultados.setAttribute("aria-busy", "true");
                ErroBusca.hidden = true;
                try {
                    const Resposta = await fetch(Endereco, { credentials: "same-origin", signal: Atual.signal });
                    if (!Resposta.ok) throw new Error("Falha na pesquisa");
                    const Documento = new DOMParser().parseFromString(await Resposta.text(), "text/html");
                    const NovosResultados = Documento.getElementById(Configuracao.Resultados);
                    if (!NovosResultados) throw new Error("Resultados indisponiveis");
                    if (Controle !== Atual) return;
                    Resultados.replaceChildren(...NovosResultados.childNodes);
                    Formulario.dispatchEvent(new CustomEvent("busca-incremental-atualizada", { detail: { Documento } }));
                } catch (Erro) {
                    if (Erro.name !== "AbortError" && Controle === Atual) ErroBusca.hidden = false;
                } finally {
                    if (Controle === Atual) Resultados.removeAttribute("aria-busy");
                }
            };
            Campo.addEventListener("input", (Evento) => {
                Cancelar();
                ErroBusca.hidden = true;
                if (Evento.isComposing) return;
                AtualizarUrl();
                Temporizador = setTimeout(Pesquisar, 160);
            });
            Campo.addEventListener("compositionstart", Cancelar);
            Campo.addEventListener("compositionend", Pesquisar);
            Formulario.querySelectorAll("select, input[type='date']").forEach((Selecao) => Selecao.addEventListener("change", Pesquisar));
            Formulario.addEventListener("submit", (Evento) => {
                Evento.preventDefault();
                Pesquisar();
            });
            Formulario.addEventListener("cancelar-busca-incremental", Cancelar);
            window.addEventListener("beforeunload", Cancelar);
        })();
    </script>
    """.replace("__CONFIGURACAO__", Configuracao)
