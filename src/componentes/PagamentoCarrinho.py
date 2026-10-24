"""Cálculo de pagamento usado no carrinho e nos painéis de atendimento."""


def ObterScriptPagamentoCarrinho():
    return r"""
    <style>[data-formulario-pagamento] [hidden] { display: none; }</style>
    <script>
        (() => {
            const ConverterCentavos = (Valor) => {
                let Texto = String(Valor).trim();
                if (Texto.includes(",")) Texto = Texto.replaceAll(".", "").replace(",", ".");
                if (!/^\d+(?:\.\d{1,2})?$/.test(Texto)) return null;
                const [Reais, Centavos = ""] = Texto.split(".");
                const Resultado = Number(Reais) * 100 + Number(Centavos.padEnd(2, "0"));
                return Number.isSafeInteger(Resultado) && Resultado <= 999999999999 ? Resultado : null;
            };
            const FormatarCentavos = (Valor) => {
                const Texto = String(Math.abs(Valor)).padStart(3, "0");
                return `R$ ${Texto.slice(0, -2).replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${Texto.slice(-2)}`;
            };
            const InicializarPagamentos = () => {
                document.querySelectorAll("[data-formulario-pagamento]").forEach((Formulario) => {
                    if (Formulario.dataset.pagamentoInicializado) return;
                    Formulario.dataset.pagamentoInicializado = "true";
                    const Total = ConverterCentavos(Formulario.dataset.total);
                    const AreaDinheiro = Formulario.querySelector("[data-area-dinheiro]");
                    const AreaPix = Formulario.querySelector("[data-area-pix]");
                    const ValorPix = Formulario.querySelector('[name="valor_pix"]');
                    const ValorRecebido = Formulario.querySelector('[name="valor_recebido"]');
                    const Troco = Formulario.querySelector("[data-troco]");
                    const AreaTroco = Formulario.querySelector("[data-area-troco]");

                    const AtualizarValores = () => {
                        const Misto = Formulario.querySelector('[name="forma_pagamento"]:checked').value === "pix_dinheiro";
                        const Pix = Misto ? ConverterCentavos(ValorPix.value) : 0;
                        const PixValido = !Misto || (Pix !== null && Pix > 0 && Pix < Total);
                        ValorPix.setCustomValidity(PixValido ? "" : "Informe um valor no PIX maior que zero e menor que o total.");
                        const Recebido = ConverterCentavos(ValorRecebido.value);
                        const Diferenca = Recebido === null || !PixValido ? null : Recebido - (Total - Pix);
                        Troco.textContent = Diferenca === null ? "R$ 0,00" : Diferenca >= 0
                            ? FormatarCentavos(Diferenca)
                            : `Faltam ${FormatarCentavos(Diferenca)}`;
                    };
                    const AtualizarFormaPagamento = () => {
                        const Forma = Formulario.querySelector('[name="forma_pagamento"]:checked').value;
                        const Misto = Forma === "pix_dinheiro";
                        const Dinheiro = Forma === "dinheiro" || Misto;
                        AreaPix.hidden = !Misto;
                        AreaDinheiro.hidden = !Dinheiro;
                        AreaTroco.hidden = !Dinheiro;
                        ValorPix.required = Misto;
                        ValorPix.disabled = !Misto;
                        ValorRecebido.required = Dinheiro;
                        ValorRecebido.disabled = !Dinheiro;
                        AtualizarValores();
                    };
                    const CompletarPagamento = (CampoEditado, OutroCampo) => {
                        const Misto = Formulario.querySelector('[name="forma_pagamento"]:checked').value === "pix_dinheiro";
                        if (Misto) {
                            const Informado = ConverterCentavos(CampoEditado.value);
                            OutroCampo.value = Informado === null ? "" : FormatarCentavos(
                                Math.max(Total - Informado, 0)
                            ).replace("R$ ", "");
                        }
                        AtualizarValores();
                    };
                    Formulario.querySelectorAll('[name="forma_pagamento"]').forEach((Opcao) => {
                        Opcao.addEventListener("change", AtualizarFormaPagamento);
                    });
                    ValorPix.addEventListener("input", () => CompletarPagamento(ValorPix, ValorRecebido));
                    ValorRecebido.addEventListener("input", () => CompletarPagamento(ValorRecebido, ValorPix));
                    AtualizarFormaPagamento();
                });
            };
            InicializarPagamentos();
            document.addEventListener("carrinhos-atualizados", InicializarPagamentos);
        })();
    </script>
    """
