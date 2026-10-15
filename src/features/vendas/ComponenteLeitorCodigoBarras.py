"""Leitura de produtos pelo codigo de barras nos carrinhos."""
from django.http import JsonResponse
from django.views.decorators.http import require_POST as ExigirPost

from features.produtos.ApiProduto import BuscarProdutoPorCodigoBarras, ObterLotesDisponiveisProduto

from .LogicaCarrinho import AdicionarProdutoAoCarrinho, ValidarNumeroCarrinho


@ExigirPost
def ComponenteLerCodigoCarrinho(Request):
    try:
        Numero = ValidarNumeroCarrinho(Request.POST.get("carrinho"), Request)
        PermitirPesquisa = Request.POST.get("permitir_pesquisa") == "1"
        try:
            ProdutoVenda = BuscarProdutoPorCodigoBarras(Request.POST.get("codigo"))
        except ValueError:
            if PermitirPesquisa:
                return JsonResponse({"Pesquisar": True})
            raise

        if ProdutoVenda is None and PermitirPesquisa:
            return JsonResponse({"Pesquisar": True})

        if ProdutoVenda is None or not ProdutoVenda.Ativo:
            return JsonResponse({"Erro": "Código de barras não cadastrado ou produto inativo."}, status=404)

        if not ObterLotesDisponiveisProduto(ProdutoVenda):
            raise ValueError(f"{ProdutoVenda.Nome} não está disponível para venda.")

        Quantidade = Request.POST.get("quantidade", "").strip()

        if not ProdutoVenda.ExigeQuantidadeInteira() and not Quantidade:
            return JsonResponse({
                "RequerQuantidade": True,
                "Nome": ProdutoVenda.Nome,
                "RotuloQuantidade": ProdutoVenda.ObterRotuloQuantidadeVenda(),
                "Passo": ProdutoVenda.ObterPassoVenda(),
            })

        AdicionarProdutoAoCarrinho(Request, Numero, ProdutoVenda.id, Quantidade or "1")
    except ValueError as Erro:
        return JsonResponse({"Erro": str(Erro)}, status=400)

    return JsonResponse({
        "RequerQuantidade": False,
        "NumeroCarrinho": Numero,
        "Mensagem": f"{ProdutoVenda.Nome} adicionado ao carrinho {Numero}.",
    })


def ObterComplementoLeitorCodigoBarras(NumeroInicial="1"):
    return """
    <style>
        .BuscaUnificadaCarrinho { margin: 0; min-width: 0; }
        .BuscaUnificadaCarrinho input[type="search"] { min-width: 0; }
        .MensagemLeitorCodigo { min-height: 16px; margin: 6px 0 12px; color: #0c614f; font-size: 12px; overflow-wrap: anywhere; }
        .MensagemLeitorCodigo.Erro { color: #a12c25; }
        .DialogoQuantidadeLeitor { width: min(430px, calc(100% - 32px)); padding: 24px; border: 1px solid #d6e0e6; border-radius: 6px; }
        .DialogoQuantidadeLeitor::backdrop { background: rgba(20, 32, 42, 0.42); }
        .DialogoQuantidadeLeitor h2 { margin: 0 0 18px; font-size: 20px; overflow-wrap: anywhere; }
        .DialogoQuantidadeLeitor label { display: block; margin-bottom: 6px; font-weight: 700; }
        .DialogoQuantidadeLeitor input { width: 100%; }
        .AcoesQuantidadeLeitor { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
    </style>
    <dialog class="DialogoQuantidadeLeitor" id="DialogoQuantidadeLeitor">
        <form method="dialog" id="FormularioQuantidadeLeitor">
            <h2 id="NomeProdutoLeitor"></h2>
            <label for="QuantidadeProdutoLeitor" id="RotuloQuantidadeLeitor"></label>
            <input class="CampoFormulario" id="QuantidadeProdutoLeitor" type="number" required>
            <div class="AcoesQuantidadeLeitor">
                <button class="BotaoSecundario" type="button" id="CancelarQuantidadeLeitor">Cancelar</button>
                <button class="BotaoPrimario" type="submit">Adicionar</button>
            </div>
        </form>
    </dialog>
    <script>
        (() => {
            const Dialogo = document.getElementById("DialogoQuantidadeLeitor");
            const CampoQuantidade = document.getElementById("QuantidadeProdutoLeitor");
            let FilaLeituras = Promise.resolve();

            document.getElementById("CancelarQuantidadeLeitor").addEventListener("click", () => Dialogo.close("cancelar"));
            document.getElementById("FormularioQuantidadeLeitor").addEventListener("submit", (Evento) => {
                Evento.preventDefault();
                Dialogo.close("adicionar");
            });

            const SolicitarQuantidade = (Dados, CampoLeitura) => new Promise((Resolver) => {
                document.getElementById("NomeProdutoLeitor").textContent = Dados.Nome;
                document.getElementById("RotuloQuantidadeLeitor").textContent = Dados.RotuloQuantidade;
                CampoQuantidade.min = Dados.Passo;
                CampoQuantidade.step = Dados.Passo;
                CampoQuantidade.value = "";
                Dialogo.returnValue = "";
                Dialogo.addEventListener("close", () => {
                    // Aguarda a saida da camada modal antes de receber outra leitura.
                    requestAnimationFrame(() => {
                        CampoLeitura.blur();
                        CampoLeitura.focus({ preventScroll: true });
                        Resolver(Dialogo.returnValue === "adicionar" ? CampoQuantidade.value : null);
                    });
                }, { once: true });
                Dialogo.showModal();
                CampoQuantidade.focus();
            });

            const EnviarLeitura = async (Formulario, Codigo, Quantidade = "") => {
                const Corpo = new FormData();
                Corpo.set("csrfmiddlewaretoken", Formulario.dataset.tokenCsrf);
                Corpo.set("carrinho", Formulario.dataset.leitorCodigo);
                Corpo.set("codigo", Codigo);
                Corpo.set("quantidade", Quantidade);
                if (!Quantidade) Corpo.set("permitir_pesquisa", "1");
                const Resposta = await fetch("/carrinho/ler-codigo", {
                    method: "POST",
                    body: Corpo,
                    credentials: "same-origin",
                });
                if (Resposta.redirected) throw new Error("Sua sessão expirou. Entre novamente.");
                const Dados = await Resposta.json();
                if (!Resposta.ok) throw new Error(Dados.Erro || "Não foi possível adicionar o produto.");
                return Dados;
            };

            const AtualizarResumo = async (Numero) => {
                const Resposta = await fetch(window.location.href, { credentials: "same-origin" });
                if (!Resposta.ok || Resposta.redirected) throw new Error("Falha ao atualizar o carrinho.");
                const Documento = new DOMParser().parseFromString(await Resposta.text(), "text/html");
                const Partes = document.querySelectorAll(`[data-resumo-carrinho="${Numero}"]`);
                for (const Parte of Partes) {
                    const NovaParte = Documento.querySelector(`[data-resumo-carrinho="${Numero}"][data-parte-resumo="${Parte.dataset.parteResumo}"]`);
                    if (!NovaParte) throw new Error("Resumo do carrinho indisponível.");
                    const FormaAnterior = Parte.querySelector('[name="forma_pagamento"]:checked')?.value;
                    const ValorAnterior = Parte.querySelector('[name="valor_recebido"]')?.value;
                    Parte.replaceChildren(...NovaParte.childNodes);
                    if (FormaAnterior) {
                        Parte.querySelectorAll('[name="forma_pagamento"]').forEach((Opcao) => {
                            Opcao.checked = Opcao.value === FormaAnterior;
                        });
                    }
                    if (ValorAnterior) Parte.querySelector('[name="valor_recebido"]').value = ValorAnterior;
                }
                document.dispatchEvent(new Event("carrinhos-atualizados"));
            };

            const ProcessarLeitura = async (Formulario, Codigo, Pesquisar) => {
                const Mensagem = document.querySelector(`[data-mensagem-leitor="${Formulario.dataset.leitorCodigo}"]`);
                Mensagem.classList.remove("Erro");
                Mensagem.textContent = "Consultando produto...";
                Formulario.setAttribute("aria-busy", "true");
                try {
                    let Dados = await EnviarLeitura(Formulario, Codigo);
                    if (Dados.Pesquisar) {
                        Mensagem.textContent = "";
                        Pesquisar();
                        return;
                    }
                    if (Dados.RequerQuantidade) {
                        const Quantidade = await SolicitarQuantidade(Dados, Formulario.querySelector("[data-campo-leitor]"));
                        if (Quantidade === null) {
                            Mensagem.textContent = "Leitura cancelada.";
                            return;
                        }
                        Dados = await EnviarLeitura(Formulario, Codigo, Quantidade);
                    }
                    try {
                        await AtualizarResumo(Dados.NumeroCarrinho);
                    } catch (Erro) {
                        throw new Error("Produto adicionado. Atualize a página para conferir o carrinho.");
                    }
                    Mensagem.textContent = Dados.Mensagem;
                } catch (Erro) {
                    Mensagem.classList.add("Erro");
                    Mensagem.textContent = Erro.message || "Não foi possível processar a leitura.";
                } finally {
                    Formulario.removeAttribute("aria-busy");
                }
            };

            document.querySelectorAll("[data-leitor-codigo]").forEach((Formulario) => {
                const Campo = Formulario.querySelector("[data-campo-leitor]");
                let RevisaoCampo = 0;
                Campo.addEventListener("input", () => RevisaoCampo++);
                Campo.addEventListener("keydown", (Evento) => {
                    if (Evento.key !== "Enter" || Evento.isComposing) return;
                    Evento.preventDefault();
                    const Codigo = Campo.value.trim();
                    if (!Codigo) return;
                    Campo.value = "";
                    Campo.dispatchEvent(new Event("input", { bubbles: true }));
                    Campo.focus();
                    const RevisaoLeitura = RevisaoCampo;
                    const Pesquisar = () => {
                        if (RevisaoCampo !== RevisaoLeitura) return;
                        Campo.value = Codigo;
                        Campo.dispatchEvent(new Event("input", { bubbles: true }));
                    };
                    FilaLeituras = FilaLeituras.then(() => ProcessarLeitura(Formulario, Codigo, Pesquisar));
                });
            });

            document.querySelector('[data-leitor-codigo="__NUMERO_INICIAL__"] [data-campo-leitor]')?.focus({ preventScroll: true });
        })();
    </script>
    """.replace("__NUMERO_INICIAL__", ValidarNumeroCarrinho(NumeroInicial))
