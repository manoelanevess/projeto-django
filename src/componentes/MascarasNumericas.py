"""Entradas numéricas em português, com normalização antes da validação."""
from decimal import Decimal, InvalidOperation

from django import forms


def NormalizarNumeroMascarado(Valor):
    Texto = str(Valor).strip()
    if "," in Texto:
        Texto = Texto.replace(".", "").replace(",", ".")
    return Texto


class EntradaNumerica(forms.TextInput):
    def __init__(self, attrs=None):
        Atributos = dict(attrs or {})
        Atributos.setdefault("inputmode", "decimal")
        Atributos.setdefault("data-mascara", "moeda" if Atributos.get("step") == "0.01" else "quantidade")
        Atributos.setdefault("placeholder", "0,00" if Atributos["data-mascara"] == "moeda" else "0" if Atributos.get("step") == "1" else "0,000")
        super().__init__(attrs=Atributos)

    def value_from_datadict(self, data, files, name):
        Valor = super().value_from_datadict(data, files, name)
        return NormalizarNumeroMascarado(Valor) if Valor else Valor

    def format_value(self, value):
        if value is None or value == "":
            return None
        try:
            Numero = Decimal(NormalizarNumeroMascarado(value))
            if not Numero.is_finite():
                return str(value)
            if self.attrs.get("step") == "1" and Numero == Numero.to_integral_value():
                return format(Numero, ".0f")
            return format(Numero, ",f").replace(",", "X").replace(".", ",").replace("X", ".")
        except InvalidOperation:
            return str(value)


def ObterScriptMascarasNumericas():
    return r"""
    <style>
        input[data-mascara="moeda"], input[data-mascara="quantidade"] {
            text-align: right;
            font-variant-numeric: tabular-nums;
        }
        .EntradaComMascara {
            display: flex;
            align-items: center;
            min-width: 0;
            width: 100%;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            background: #fff;
            overflow: hidden;
        }
        .EntradaComMascara:focus-within { outline: 2px solid #0784ca; outline-offset: 1px; }
        .EntradaComMascara > input {
            flex: 1;
            min-width: 0;
            width: 100%;
            border: 0 !important;
            border-radius: 0;
            outline: none;
        }
        .PrefixoEntradaNumerica, .UnidadeEntradaNumerica {
            padding: 0 10px;
            color: #52616f;
            font-size: 13px;
            white-space: nowrap;
        }
        .EntradaComMascara:has(input:disabled) { background: #f0f3f5; opacity: .7; }
    </style>
    <script>
        (() => {
            const Seletor = 'input[data-mascara], input[type="number"], input[inputmode="decimal"]';
            const Normalizar = (Texto) => Texto.includes(",") ? Texto.replaceAll(".", "").replace(",", ".") : Texto;
            const Precisao = (Campo) => Campo.dataset.mascara === "moeda" ? 2
                : Campo.getAttribute("step") === "1" ? 0 : 3;
            const ApresentarFormato = (Campo) => {
                const Moeda = Campo.dataset.mascara === "moeda";
                if (Campo.dataset.mascara === "telefone") return;
                Campo.placeholder = Moeda ? "0,00" : Precisao(Campo) ? "0,000" : "0";
                let Unidade = "";
                if (!Moeda) {
                    const FormaVenda = Campo.form?.querySelector('[name="UnidadeVenda"]') || document.getElementById("id_UnidadeVenda");
                    const Rotulo = Campo.getAttribute("aria-label") || Campo.labels?.[0]?.textContent || "";
                    Unidade = Rotulo.includes("(kg)") ? "kg" : Rotulo.includes("(m)") ? "m"
                        : { unidade: "un", valor_fixo: "un", metro: "m", quilograma: "kg" }[FormaVenda?.value]
                        || (Precisao(Campo) ? "" : "un");
                }
                if (Moeda && Campo.closest(".CampoMoeda")) return;
                let Grupo = Campo.closest(".EntradaComMascara");
                if (!Grupo && (Moeda || Unidade)) {
                    Grupo = document.createElement("div");
                    Grupo.className = "EntradaComMascara";
                    Campo.before(Grupo);
                    Grupo.append(Campo);
                    const Indicador = document.createElement("span");
                    Indicador.setAttribute("aria-hidden", "true");
                    if (Moeda) {
                        Indicador.className = "PrefixoEntradaNumerica";
                        Indicador.textContent = "R$";
                        Grupo.prepend(Indicador);
                    } else {
                        Indicador.className = "UnidadeEntradaNumerica";
                        Grupo.append(Indicador);
                    }
                }
                if (!Moeda && Grupo) Grupo.querySelector(".UnidadeEntradaNumerica").textContent = Unidade;
            };
            const Validar = (Campo) => {
                if (Campo.dataset.mascara === "telefone") return;
                let Erro = "";
                const Valor = Number(Normalizar(Campo.value));
                const Minimo = Campo.getAttribute("min");
                const Maximo = Campo.getAttribute("max");
                if (Campo.value && (!Number.isFinite(Valor) || Valor < 0)) Erro = "Informe um número válido.";
                else if (Campo.value && Minimo !== null && Valor < Number(Minimo)) Erro = "O valor está abaixo do mínimo permitido.";
                else if (Campo.value && Maximo !== null && Valor > Number(Maximo)) Erro = "O valor ultrapassa o máximo permitido.";
                if (Erro || Campo.dataset.erroMascara) {
                    Campo.setCustomValidity(Erro);
                    Campo.dataset.erroMascara = Erro;
                }
            };
            const Formatar = (Campo) => {
                const Original = Campo.value;
                const Posicao = Campo.selectionStart ?? Original.length;
                const Antes = Original.slice(0, Posicao).replace(/[^\d,]/g, "");
                let Texto;
                if (Campo.dataset.mascara === "telefone") {
                    const Internacional = Original.trim().startsWith("+55");
                    const Digitos = Original.replace(/\D/g, "").replace(Internacional ? /^55/ : /^$/, "").slice(0, 11);
                    const Ddd = Digitos.slice(0, 2);
                    const Numero = Digitos.slice(2);
                    const Corte = Numero.length > 8 ? 5 : 4;
                    Texto = (Internacional ? "+55 " : "") + (Ddd ? `(${Ddd}${Ddd.length === 2 ? ") " : ""}` : "")
                        + Numero.slice(0, Corte) + (Numero.length > Corte ? "-" + Numero.slice(Corte) : "");
                } else {
                    const Limite = Precisao(Campo);
                    const Limpo = Original.replace(/[^\d,]/g, "");
                    const [Inteiros, ...Fracoes] = Limpo.split(",");
                    const ParteInteira = Inteiros.replace(/^0+(?=\d)/, "");
                    const Casas = Fracoes.join("").slice(0, Limite);
                    Texto = Limite ? ParteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".") : ParteInteira;
                    if (Limpo && Limite) Texto = (Texto || "0") + "," + Casas.padEnd(Limite, "0");
                    if (Posicao === 0 && Limpo.startsWith(",") && !/[1-9]/.test(Limpo)) Texto = "";
                }
                Campo.value = Texto;
                if (document.activeElement === Campo) {
                    let Contagem = 0;
                    let Cursor = 0;
                    const ZerosRemovidos = Campo.dataset.mascara === "telefone" ? 0 : (Original.replace(/[^\d,]/g, "").split(",")[0].match(/^0+(?=\d)/)?.[0].length || 0);
                    const ZeroInserido = Original.replace(/[^\d,]/g, "").startsWith(",") && Antes.includes(",") ? 1 : 0;
                    const Caracteres = Campo.dataset.mascara === "telefone" ? Original.slice(0, Posicao).replace(/\D/g, "").length : Math.max(Antes.length - ZerosRemovidos + ZeroInserido, 0);
                    while (Cursor < Texto.length && Contagem < Caracteres) {
                        if ((Campo.dataset.mascara === "telefone" ? /\d/ : /[\d,]/).test(Texto[Cursor])) Contagem++;
                        Cursor++;
                    }
                    Campo.setSelectionRange(Cursor, Cursor);
                }
                Validar(Campo);
            };
            const Preparar = (Campo) => {
                if (Campo.dataset.mascaraInicializada) return;
                Campo.dataset.mascaraInicializada = "true";
                const Canonico = Campo.type === "number" || !Campo.dataset.mascara;
                if (!Campo.dataset.mascara) Campo.dataset.mascara = Campo.type === "number" ? "quantidade" : "moeda";
                if (Campo.type === "number") Campo.type = "text";
                Campo.inputMode = Campo.dataset.mascara === "telefone" ? "tel" : Precisao(Campo) ? "decimal" : "numeric";
                ApresentarFormato(Campo);
                if (Canonico && Campo.dataset.mascara !== "telefone" && !Campo.value.includes(",")) Campo.value = Campo.value.replace(".", ",");
                Formatar(Campo);
            };
            const PrepararArvore = (Raiz) => {
                if (Raiz.matches?.(Seletor)) Preparar(Raiz);
                Raiz.querySelectorAll?.(Seletor).forEach(Preparar);
            };
            document.addEventListener("input", (Evento) => {
                const Campo = Evento.target;
                if (Evento.isComposing || !Campo.matches?.(Seletor)) return;
                Preparar(Campo);
                Formatar(Campo);
            }, true);
            document.addEventListener("focusout", (Evento) => {
                if (Evento.target.matches?.(Seletor)) Formatar(Evento.target);
            }, true);
            document.addEventListener("beforeinput", (Evento) => {
                const Campo = Evento.target;
                if (!Campo.matches?.(Seletor) || Campo.dataset.mascara === "telefone" || ![".", ","].includes(Evento.data)) return;
                Evento.preventDefault();
                if (!Precisao(Campo)) return;
                const Separador = Campo.value.indexOf(",");
                if (Separador >= 0) Campo.setSelectionRange(Separador + 1, Separador + 1);
                else {
                    Campo.setRangeText(",", Campo.selectionStart, Campo.selectionEnd, "end");
                    Campo.dispatchEvent(new Event("input", { bubbles: true }));
                }
            }, true);
            document.addEventListener("paste", (Evento) => {
                const Campo = Evento.target;
                if (!Campo.matches?.(Seletor) || Campo.dataset.mascara === "telefone") return;
                const Texto = Evento.clipboardData?.getData("text")?.trim();
                if (!Texto || Texto.includes(",") || !/^\d+\.\d+$/.test(Texto)) return;
                Evento.preventDefault();
                Campo.setRangeText(Texto.replace(".", ","), Campo.selectionStart, Campo.selectionEnd, "end");
                Campo.dispatchEvent(new Event("input", { bubbles: true }));
            }, true);
            PrepararArvore(document);
            new MutationObserver((Mudancas) => {
                Mudancas.forEach((Mudanca) => {
                    Mudanca.addedNodes.forEach(PrepararArvore);
                    if (Mudanca.type === "attributes" && Mudanca.target.matches(Seletor)) {
                        const Campo = Mudanca.target;
                        Campo.inputMode = Precisao(Campo) ? "decimal" : "numeric";
                        ApresentarFormato(Campo);
                        Validar(Campo);
                    }
                });
            }).observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["step", "min", "max"] });
        })();
    </script>
    """
