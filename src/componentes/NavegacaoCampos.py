"""Navegação entre campos pela posição visual usando as setas do teclado."""


def ObterScriptNavegacaoCampos():
    return r"""
    <script>
        (() => {
            const Seletor = 'input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]):not([type="submit"]):not([type="button"]):not([type="reset"]), select, textarea';
            document.addEventListener("keydown", (Evento) => {
                if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(Evento.key)
                    || Evento.defaultPrevented || Evento.isComposing || Evento.altKey || Evento.ctrlKey || Evento.metaKey || Evento.shiftKey) return;
                const Atual = Evento.target;
                if (!Atual.matches?.(Seletor)) return;
                const Raiz = Atual.closest("dialog[open]") || document.querySelector("main") || document;
                const CaixaAtual = Atual.getBoundingClientRect();
                const Vertical = ['ArrowUp', 'ArrowDown'].includes(Evento.key);
                const CentroAtual = Vertical ? CaixaAtual.left + CaixaAtual.width / 2 : CaixaAtual.top + CaixaAtual.height / 2;
                const Candidatos = [];

                Raiz.querySelectorAll(Seletor).forEach((Campo) => {
                    if (Campo === Atual || Campo.matches(":disabled, [readonly], [inert], [tabindex='-1']")
                        || Campo.closest("[inert], [hidden]") || !Campo.getClientRects().length
                        || window.getComputedStyle(Campo).visibility !== "visible") return;
                    const Caixa = Campo.getBoundingClientRect();
                    let Distancia;
                    if (Evento.key === 'ArrowUp' && Caixa.bottom <= CaixaAtual.top + 4) Distancia = CaixaAtual.top - Caixa.bottom;
                    else if (Evento.key === 'ArrowDown' && Caixa.top >= CaixaAtual.bottom - 4) Distancia = Caixa.top - CaixaAtual.bottom;
                    else if (Evento.key === 'ArrowLeft' && Caixa.right <= CaixaAtual.left + 4) Distancia = CaixaAtual.left - Caixa.right;
                    else if (Evento.key === 'ArrowRight' && Caixa.left >= CaixaAtual.right - 4) Distancia = Caixa.left - CaixaAtual.right;
                    else return;
                    const Centro = Vertical ? Caixa.left + Caixa.width / 2 : Caixa.top + Caixa.height / 2;
                    const Alinhado = Vertical
                        ? Caixa.left < CaixaAtual.right && Caixa.right > CaixaAtual.left
                        : Caixa.top < CaixaAtual.bottom && Caixa.bottom > CaixaAtual.top;
                    Candidatos.push({ Campo, Alinhado, Distancia: Math.max(Distancia, 0) + Math.abs(Centro - CentroAtual) });
                });
                Candidatos.sort((Primeiro, Segundo) => Number(Segundo.Alinhado) - Number(Primeiro.Alinhado) || Primeiro.Distancia - Segundo.Distancia);
                const Destino = Candidatos[0]?.Campo;
                if (!Destino) return;
                Evento.preventDefault();
                Destino.focus();
                if (Destino.matches('input[type="text"], input[type="search"], input[type="tel"], input[type="email"], input[type="password"], textarea')) Destino.select();
            }, true);
        })();
    </script>
    """
