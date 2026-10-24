"""Avisos visuais e confirmações compartilhados pelas telas do sistema."""


def ObterEstilosAvisos():
    return """
    <style>
        body :is(.MensagemOperacao, .SucessoConfiguracao, .MensagemErro, .AvisoFornecedor, .MensagemFormulario.Erro) {
            --AvisoCor: #08765e; --AvisoFundo: #edf9f4; --AvisoBorda: #c8e9db; --AvisoIcone: #d4f0e3;
            position: relative; padding: 15px 48px 15px 58px; margin-bottom: 18px;
            border: 1px solid var(--AvisoBorda); border-radius: 10px;
            background: var(--AvisoFundo); color: var(--AvisoCor);
            box-shadow: 0 3px 10px rgba(31, 49, 61, 0.03); font-size: 14px; line-height: 1.5;
            overflow-wrap: anywhere; animation: EntradaAviso 160ms ease-out;
        }
        body :is(.MensagemOperacao.Erro, .MensagemErro, .MensagemFormulario.Erro) {
            --AvisoCor: #a4332e; --AvisoFundo: #fff4f2; --AvisoBorda: #f1d0ca; --AvisoIcone: #fbe0da;
        }
        body .AvisoFornecedor { --AvisoCor: #855413; --AvisoFundo: #fff8ec; --AvisoBorda: #efddbc; --AvisoIcone: #f8e8c9; }
        body :is(.MensagemOperacao, .SucessoConfiguracao, .MensagemErro, .AvisoFornecedor, .MensagemFormulario.Erro)::before {
            content: "✓"; position: absolute; left: 16px; top: 13px; width: 28px; height: 28px;
            display: grid; place-items: center; border-radius: 50%; background: var(--AvisoIcone);
            font-size: 16px; font-weight: 700; line-height: 1;
        }
        body :is(.MensagemOperacao.Erro, .MensagemErro, .AvisoFornecedor, .MensagemFormulario.Erro)::before { content: "!"; }
        .FecharMensagemSistema {
            position: absolute; top: 10px; right: 10px; width: 30px; height: 30px; padding: 0; border: 0;
            display: grid; place-items: center; border-radius: 6px; background: transparent;
            color: inherit; cursor: pointer; font: inherit; font-size: 22px;
        }
        .FecharMensagemSistema:hover { background: var(--AvisoIcone); }
        .FecharMensagemSistema:focus-visible { outline: 2px solid currentColor; outline-offset: 1px; }
        .DialogoConfirmacaoSistema {
            width: min(460px, calc(100vw - 32px)); max-height: calc(100dvh - 32px); padding: 0;
            border: 1px solid #e2e8ed; border-radius: 16px; color: #26313d; background: white;
            box-shadow: 0 24px 80px rgba(18, 35, 52, 0.25); overflow: auto;
        }
        .DialogoConfirmacaoSistema[open] { animation: EntradaConfirmacao 180ms ease-out; }
        .DialogoConfirmacaoSistema::backdrop { background: rgba(19, 32, 45, 0.45); backdrop-filter: blur(3px); }
        .ConteudoConfirmacaoSistema { position: relative; padding: 30px; }
        .IconeConfirmacaoSistema {
            width: 52px; height: 52px; display: grid; place-items: center; margin-bottom: 18px;
            border: 6px solid #fff7ed; border-radius: 50%; background: #ffead0; color: #b86a0c;
            font-size: 24px; font-weight: bold;
        }
        .FecharConfirmacaoSistema {
            position: absolute; top: 14px; right: 14px; width: 30px; height: 30px; padding: 0;
            border: 0; border-radius: 6px; color: #778494; background: transparent; cursor: pointer; font-size: 24px;
        }
        .FecharConfirmacaoSistema:hover { background: #f0f4f7; color: #26313d; }
        .DialogoConfirmacaoSistema h2 { margin: 0 0 10px; font-size: 22px; line-height: 1.3; font-weight: 700; overflow-wrap: anywhere; }
        .DialogoConfirmacaoSistema p { margin: 0; color: #647383; font-size: 14px; line-height: 1.65; overflow-wrap: anywhere; }
        .AcoesConfirmacaoSistema { display: flex; justify-content: flex-end; gap: 10px; margin-top: 26px; }
        .AcoesConfirmacaoSistema button { min-height: 42px; padding: 10px 16px; border-radius: 8px; font: inherit; font-size: 14px; font-weight: 700; cursor: pointer; }
        .CancelarConfirmacaoSistema { border: 1px solid #d7e1e9; color: #43576a; background: white; }
        .CancelarConfirmacaoSistema:hover { background: #f3f7fa; }
        .ConfirmarAcaoSistema { border: 1px solid #c94139; color: white; background: #cf4940; }
        .ConfirmarAcaoSistema:hover { background: #b73730; border-color: #b73730; }
        .DialogoConfirmacaoSistema button:focus-visible { outline: 3px solid #9bcfe9; outline-offset: 3px; }
        .ConfirmarAcaoSistema:disabled { opacity: 0.65; cursor: wait; }
        body:has(.DialogoConfirmacaoSistema[open]) { overflow: hidden; }
        @keyframes EntradaAviso { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes EntradaConfirmacao { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
        @media (prefers-reduced-motion: reduce) { body :is(.MensagemOperacao, .SucessoConfiguracao, .MensagemErro, .AvisoFornecedor, .MensagemFormulario.Erro), .DialogoConfirmacaoSistema[open] { animation: none; } }
        @media (max-width: 480px) {
            .ConteudoConfirmacaoSistema { padding: 24px; }
            .AcoesConfirmacaoSistema { flex-direction: column-reverse; }
            .AcoesConfirmacaoSistema button { width: 100%; }
        }
    </style>
    """


def ObterComponenteAvisos():
    return ObterEstilosAvisos() + r"""
    <dialog class="DialogoConfirmacaoSistema" id="DialogoConfirmacaoSistema" role="alertdialog"
            aria-labelledby="TituloConfirmacaoSistema" aria-describedby="DescricaoConfirmacaoSistema">
        <div class="ConteudoConfirmacaoSistema">
            <button class="FecharConfirmacaoSistema" type="button" aria-label="Fechar confirmação">×</button>
            <span class="IconeConfirmacaoSistema" aria-hidden="true">!</span>
            <h2 id="TituloConfirmacaoSistema"></h2>
            <p id="DescricaoConfirmacaoSistema"></p>
            <div class="AcoesConfirmacaoSistema">
                <button class="CancelarConfirmacaoSistema" type="button">Voltar</button>
                <button class="ConfirmarAcaoSistema" type="button">Confirmar</button>
            </div>
        </div>
    </dialog>
    <script>
        (() => {
            const Dialogo = document.getElementById("DialogoConfirmacaoSistema");
            const Titulo = document.getElementById("TituloConfirmacaoSistema");
            const Descricao = document.getElementById("DescricaoConfirmacaoSistema");
            const Cancelar = Dialogo.querySelector(".CancelarConfirmacaoSistema");
            const Confirmar = Dialogo.querySelector(".ConfirmarAcaoSistema");
            const Autorizados = new WeakSet();
            let Pendente;

            const Encerrar = () => {
                const Atual = Pendente;
                Pendente = null;
                Dialogo.close();
                if (Atual?.Foco?.isConnected) Atual.Foco.focus({ preventScroll: true });
                return Atual;
            };
            Cancelar.addEventListener("click", Encerrar);
            Dialogo.querySelector(".FecharConfirmacaoSistema").addEventListener("click", Encerrar);
            Dialogo.addEventListener("cancel", (Evento) => { Evento.preventDefault(); Encerrar(); });
            Dialogo.addEventListener("click", (Evento) => { if (Evento.target === Dialogo) Encerrar(); });

            Confirmar.addEventListener("click", () => {
                if (!Pendente) return;
                Confirmar.disabled = true;
                const Atual = Encerrar();
                if (!Atual.Formulario.isConnected) return;
                Autorizados.add(Atual.Formulario);
                try {
                    const Botao = Atual.Botao?.isConnected && Atual.Botao.form === Atual.Formulario ? Atual.Botao : undefined;
                    Atual.Formulario.requestSubmit(Botao);
                } finally {
                    Autorizados.delete(Atual.Formulario);
                }
            });

            document.addEventListener("submit", (Evento) => {
                const Formulario = Evento.target;
                if (!Formulario.matches("form[data-confirmar], form[data-confirmar-fechamento]") || Evento.defaultPrevented) return;
                if (Autorizados.has(Formulario)) { Autorizados.delete(Formulario); return; }
                let Pergunta = Formulario.dataset.confirmar;
                let Explicacao = Formulario.dataset.confirmarDescricao || "Confirme para continuar com esta ação.";
                let Acao = Formulario.dataset.confirmarAcao || "Confirmar";
                let Voltar = Formulario.dataset.confirmarCancelar || "Voltar";
                if (Formulario.hasAttribute("data-confirmar-fechamento")) {
                    const Numero = Formulario.elements.carrinho.value;
                    const Contador = document.querySelector(`[data-resumo-carrinho="${Numero}"][data-parte-resumo$="-quantidade"]`);
                    const TemItens = Number.parseInt(Contador?.textContent || "0", 10) > 0;
                    if (!TemItens && Formulario.dataset.clienteIdentificado !== "true") return;
                    Pergunta = `Fechar carrinho ${Numero}?`;
                    Explicacao = "Os itens e o nome do cliente deste atendimento serão descartados. Você pode continuar atendendo para manter o carrinho aberto.";
                    Acao = "Fechar carrinho";
                    Voltar = "Continuar atendendo";
                }
                Evento.preventDefault();
                if (Dialogo.open) return;
                Pendente = { Formulario, Botao: Evento.submitter, Foco: Evento.submitter || document.activeElement };
                Titulo.textContent = Pergunta;
                Descricao.textContent = Explicacao;
                Confirmar.textContent = Acao;
                Cancelar.textContent = Voltar;
                Confirmar.disabled = false;
                Dialogo.showModal();
                Cancelar.focus({ preventScroll: true });
            });

            const PrepararMensagens = (Raiz) => {
                const Seletor = '.MensagemOperacao:not([id]), .SucessoConfiguracao';
                const Mensagens = [...(Raiz.matches?.(Seletor) ? [Raiz] : []), ...(Raiz.querySelectorAll?.(Seletor) || [])];
                Mensagens.forEach((Mensagem) => {
                    if (Mensagem.querySelector(".FecharMensagemSistema")) return;
                    const Botao = document.createElement("button");
                    Botao.type = "button";
                    Botao.className = "FecharMensagemSistema";
                    Botao.setAttribute("aria-label", "Fechar mensagem");
                    Botao.textContent = "×";
                    Botao.addEventListener("click", () => {
                        const Campo = document.querySelector("main input:not([type='hidden']):not(:disabled), main select:not(:disabled)") || document.querySelector("main");
                        Campo?.focus({ preventScroll: true });
                        Mensagem.hidden = true;
                    });
                    Mensagem.append(Botao);
                });
            };
            PrepararMensagens(document);
            new MutationObserver((Mudancas) => Mudancas.forEach((Mudanca) => Mudanca.addedNodes.forEach(PrepararMensagens)))
                .observe(document.querySelector("main"), { childList: true, subtree: true });
        })();
    </script>
    """
