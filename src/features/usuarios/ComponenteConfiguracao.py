"""Configurações acessadas pelo perfil no cabeçalho."""
from html import escape

from django.http import Http404, HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect
from django.views.decorators.http import require_GET as ExigirGet, require_http_methods as ExigirMetodos

from componentes.LayoutBase import RenderizarLayoutBase

from .ApiConfiguracao import ObterFotoPerfilUrl, ObterNomeComercio
from .FormularioConfiguracao import FormularioConfiguracao
from .LogicaConfiguracao import SalvarConfiguracao
from .models import PerfilUsuario


def RenderizarErrosConfiguracao(Formulario, Campo):
    return "".join(f'<p class="ErroConfiguracao" role="alert">{escape(str(Erro))}</p>'
                   for Erro in Formulario[Campo].errors)


@ExigirMetodos(["GET", "POST"])
def ComponenteConfiguracoes(Request):
    Formulario = FormularioConfiguracao(
        Request.POST if Request.method == "POST" else None,
        Request.FILES if Request.method == "POST" else None,
        initial={"NomeComercio": ObterNomeComercio(Request)},
    )
    if Request.method == "POST" and Formulario.is_valid():
        SalvarConfiguracao(Request.user, Formulario.cleaned_data)
        Request.session["MensagemConfiguracao"] = "Configurações salvas com sucesso."
        return redirect("Configuracoes")

    FotoUrl = ObterFotoPerfilUrl(Request)
    FotoSegura = escape(FotoUrl)
    Mensagem = Request.session.pop("MensagemConfiguracao", "")
    MensagemHtml = f'<p class="SucessoConfiguracao" role="status">{escape(Mensagem)}</p>' if Mensagem else ""
    TokenCsrf = escape(ObterTokenCsrf(Request))
    Conteudo = f"""
    <style>
        .CabecalhoConfiguracao {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 20px; }}
        .CabecalhoConfiguracao h1 {{ margin: 0; }}
        .FormularioConfiguracao {{ max-width: 760px; padding: 28px; border-radius: 8px; background: white; box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08); }}
        .SecaoConfiguracao + .SecaoConfiguracao {{ border-top: 1px solid #e1e8ed; padding-top: 24px; margin-top: 24px; }}
        .SecaoConfiguracao h2 {{ margin-bottom: 8px; font-size: 19px; }}
        .DescricaoConfiguracao {{ color: #667482; line-height: 1.5; margin: 0 0 18px; }}
        .SecaoConfiguracao label {{ display: block; margin-bottom: 8px; font-size: 14px; font-weight: 700; }}
        .SecaoConfiguracao .CampoFormulario {{ width: 100%; min-width: 0; }}
        .AreaFotoConfiguracao {{ display: flex; align-items: center; gap: 24px; }}
        .PreviaFotoConfiguracao {{ flex: 0 0 96px; height: 96px; border-radius: 50%; overflow: hidden; background: #e5f3fa; color: #056da8; display: grid; place-items: center; font-size: 32px; font-weight: bold; }}
        .PreviaFotoConfiguracao img {{ width: 96px; height: 96px; object-fit: cover; }}
        .PreviaFotoConfiguracao [hidden] {{ display: none; }}
        .EscolhaFotoConfiguracao {{ flex: 1; min-width: 0; }}
        .EscolhaFotoConfiguracao small {{ display: block; margin-top: 8px; color: #667482; line-height: 1.5; }}
        .AcoesConfiguracao {{ display: flex; justify-content: flex-end; gap: 10px; margin-top: 28px; }}
        .ErroConfiguracao {{ color: #a12c25; margin: 8px 0 0; font-size: 14px; }}
        .SucessoConfiguracao {{ max-width: 760px; padding: 12px 14px; border-left: 4px solid #14866d; border-radius: 4px; color: #0c614f; background: #e7f7f2; margin: 0 0 18px; }}
        @media (max-width: 600px) {{
            .FormularioConfiguracao {{ padding: 20px; }}
            .AreaFotoConfiguracao {{ align-items: flex-start; flex-direction: column; }}
            .PreviaFotoConfiguracao {{ flex-basis: auto; width: 96px; }}
            .CabecalhoConfiguracao {{ align-items: flex-start; flex-direction: column; }}
        }}
    </style>
    <div class="CabecalhoConfiguracao">
        <h1>Configurações</h1>
        <a class="BotaoSecundario" href="/">Voltar ao início</a>
    </div>
    {MensagemHtml}
    <form class="FormularioConfiguracao" method="post" action="/configuracoes" enctype="multipart/form-data">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        <section class="SecaoConfiguracao" aria-labelledby="TituloComercio">
            <h2 id="TituloComercio">Seu comércio</h2>
            <p class="DescricaoConfiguracao">Personalize o nome que aparece no sistema.</p>
            <label for="id_NomeComercio">Nome do comércio</label>
            {Formulario["NomeComercio"]}
            {RenderizarErrosConfiguracao(Formulario, "NomeComercio")}
        </section>
        <section class="SecaoConfiguracao" aria-labelledby="TituloPerfil">
            <h2 id="TituloPerfil">Seu perfil</h2>
            <p class="DescricaoConfiguracao">Sua foto aparece ao lado de Proprietário no topo das páginas.</p>
            <div class="AreaFotoConfiguracao">
                <div class="PreviaFotoConfiguracao">
                    <img id="PreviaFotoPerfil" alt="Prévia da foto de perfil"{f' src="{FotoSegura}"' if FotoUrl else ' hidden'}>
                    <span id="InicialPerfil" aria-hidden="true"{' hidden' if FotoUrl else ''}>P</span>
                </div>
                <div class="EscolhaFotoConfiguracao">
                    <label for="id_FotoPerfil">Trocar foto de perfil</label>
                    {Formulario["FotoPerfil"]}
                    <small>JPG, PNG ou WebP, até 2 MB. Sem escolher outra foto, a atual será mantida.</small>
                    <p class="ErroConfiguracao" id="ErroPreviaFoto" role="alert" hidden></p>
                    {RenderizarErrosConfiguracao(Formulario, "FotoPerfil")}
                </div>
            </div>
        </section>
        <div class="AcoesConfiguracao">
            <a class="BotaoSecundario" href="/">Cancelar</a>
            <button class="BotaoPrimario" type="submit">Salvar alterações</button>
        </div>
    </form>
    <script>
        (() => {{
            const Campo = document.getElementById("id_FotoPerfil");
            const Previa = document.getElementById("PreviaFotoPerfil");
            const Inicial = document.getElementById("InicialPerfil");
            const Erro = document.getElementById("ErroPreviaFoto");
            const FotoAtual = Previa.getAttribute("src");
            let UrlTemporaria;
            const RestaurarFoto = () => {{
                if (FotoAtual) Previa.src = FotoAtual;
                else Previa.removeAttribute("src");
                Previa.hidden = !FotoAtual;
                Inicial.hidden = !!FotoAtual;
            }};
            const InformarErro = (Mensagem) => {{
                Campo.setCustomValidity(Mensagem);
                Erro.textContent = Mensagem;
                Erro.hidden = false;
                RestaurarFoto();
            }};
            Campo.addEventListener("change", () => {{
                if (UrlTemporaria) URL.revokeObjectURL(UrlTemporaria);
                UrlTemporaria = null;
                Campo.setCustomValidity("");
                Erro.hidden = true;
                const Foto = Campo.files[0];
                if (!Foto) return RestaurarFoto();
                if (Foto.size > 2 * 1024 * 1024) return InformarErro("A foto deve ter no máximo 2 MB.");
                if (!["image/jpeg", "image/png", "image/webp"].includes(Foto.type)) return InformarErro("Escolha uma foto JPG, PNG ou WebP.");
                UrlTemporaria = URL.createObjectURL(Foto);
                Campo.setCustomValidity("Aguarde a prévia da foto carregar.");
                const Imagem = new Image();
                const UrlAtual = UrlTemporaria;
                Imagem.onload = () => {{
                    if (UrlTemporaria !== UrlAtual) return;
                    Campo.setCustomValidity("");
                    Previa.src = UrlAtual;
                    Previa.hidden = false;
                    Inicial.hidden = true;
                }};
                Imagem.onerror = () => {{
                    if (UrlTemporaria === UrlAtual) InformarErro("Não foi possível abrir esta foto. Escolha outra imagem.");
                }};
                Imagem.src = UrlAtual;
            }});
            window.addEventListener("beforeunload", () => {{ if (UrlTemporaria) URL.revokeObjectURL(UrlTemporaria); }});
        }})();
    </script>
    """
    return HttpResponse(RenderizarLayoutBase("Configurações", Conteudo, RotaAtiva="configuracoes", Request=Request))


@ExigirGet
def ComponenteFotoPerfil(Request):
    Perfil = PerfilUsuario.objects.filter(Usuario=Request.user).first()
    if Perfil is None or not Perfil.FotoConteudo or Perfil.FotoTipo not in {"image/png", "image/jpeg", "image/webp"}:
        raise Http404("Foto de perfil não encontrada.")
    Resposta = HttpResponse(bytes(Perfil.FotoConteudo), content_type=Perfil.FotoTipo)
    Resposta["Cache-Control"] = "private, no-store"
    Resposta["X-Content-Type-Options"] = "nosniff"
    Resposta["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return Resposta
