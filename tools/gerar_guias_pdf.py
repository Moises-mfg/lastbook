#!/usr/bin/env python3
"""Gera guias originais A4 em português, sem acesso à rede.

Uso: python tools/gerar_guias_pdf.py [--render]
Dependência: reportlab. --render requer pdftoppm (Poppler) no PATH e cria PNGs
de cada página a 120 dpi para o leitor do aplicativo. Funciona em Linux,
macOS e Windows com essas dependências instaladas. Fontes PDF padrão evitam
dependência de fontes do sistema. Os PDFs não contêm formulários interativos.
"""

from argparse import ArgumentParser
from pathlib import Path
import shutil
import subprocess

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "brasil" / "web" / "guias"
INK = colors.HexColor("#17342c")
MUTED = colors.HexColor("#4b625b")
ACCENT = colors.HexColor("#bd643e")
PAPER = colors.HexColor("#eff4f0")
EDITION = "Edição 1 · novembro de 2026"

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("GuideTitle", fontName="Helvetica-Bold", fontSize=25,
                          leading=29, textColor=INK, spaceAfter=10))
STYLES.add(ParagraphStyle("Deck", fontName="Helvetica", fontSize=11, leading=16,
                          textColor=MUTED, spaceAfter=14))
STYLES.add(ParagraphStyle("Section", fontName="Helvetica-Bold", fontSize=12,
                          leading=16, textColor=INK, spaceBefore=12, spaceAfter=6))
STYLES.add(ParagraphStyle("Copy", fontName="Helvetica", fontSize=10.3,
                          leading=15, textColor=INK, spaceAfter=6))
STYLES.add(ParagraphStyle("SmallNote", fontName="Helvetica", fontSize=8,
                          leading=11, textColor=MUTED, spaceAfter=6))


class Check(Flowable):
    """Caixa vetorial, independente da disponibilidade de glifos Unicode."""
    def __init__(self, text):
        super().__init__()
        self.paragraph = Paragraph(text, STYLES["Copy"])

    def wrap(self, width, height):
        self.width = width
        _, self.text_height = self.paragraph.wrap(width - 18, height)
        self.height = self.text_height + 6
        return self.width, self.height

    def draw(self):
        self.canv.setStrokeColor(MUTED)
        self.canv.rect(0, self.height - 14, 7, 7, stroke=1, fill=0)
        self.paragraph.drawOn(self.canv, 18, 6)


def p(text, style="Copy"):
    return Paragraph(text, STYLES[style])


def section(title, *items):
    return [KeepTogether([p(title, "Section"), Check(items[0])]),
            *(Check(item) for item in items[1:])]


def fields(*labels):
    result = []
    for label in labels:
        result.extend([p(label, "SmallNote"), Spacer(1, 9 * mm),
                       p("__________________________________________________________________", "SmallNote")])
    return result


def heading(number, title, deck):
    return [p(f"GUIA {number} / O ÚLTIMO LIVRO", "SmallNote"),
            p(title, "GuideTitle"), p(deck, "Deck")]


def preparation():
    story = heading("01", "Organização e documentos",
                    "Um plano simples para localizar o essencial e combinar ajuda. "
                    "Faça em um dia tranquilo e revise quando a rotina mudar.")
    story += section("1. Monte uma pasta que você consiga encontrar",
        "Separe cópias legíveis dos documentos pessoais e dos comprovantes que sua família usa. "
        "Inclua apenas o necessário para sua realidade.",
        "Anote contatos de confiança, endereços importantes, seguros e serviços essenciais. "
        "Registre informações de saúde que a própria pessoa queira compartilhar.",
        "Identifique a pasta e guarde-a em local conhecido, protegido de umidade e de acesso indevido. "
        "Não deixe documentos sensíveis à vista.")
    story += section("2. Combine um plano com as pessoas da casa",
        "Defina quem ajuda crianças, pessoas com deficiência, idosos e animais. "
        "Pergunte de que apoio cada pessoa precisa; evite presumir.",
        "Escolha um ponto de encontro próximo e outro fora da área. Combine também um contato "
        "que possa receber recados quando as pessoas estiverem separadas.",
        "Planeje o que levar se houver orientação de saída. Priorize pessoas e animais; "
        "siga as instruções das autoridades locais e não retorne por objetos.")
    story += section("3. Confira o que já existe antes de comprar",
        "Localize lanterna, carregadores, rádio se disponível, chaves e itens de uso diário. "
        "Mantenha caminhos e saídas desobstruídos.",
        "Liste necessidades de alimentação, higiene, acessibilidade e cuidados dos animais. "
        "Use a rotina da casa para identificar o que precisa ser reposto.",
        "Se alguém depende de medicamento ou equipamento, combine antes um plano de continuidade "
        "com a equipe que acompanha essa pessoa. Não improvise doses ou fontes de energia.")
    story += [p("Comece hoje: reúna os contatos, escolha um lugar para a pasta e explique o plano a outra pessoa.", "Deck"), PageBreak()]
    story += heading("01", "Ficha da casa",
                     "Preencha a lápis ou imprima uma nova cópia quando algo mudar. "
                     "Guarde esta ficha como informação pessoal.")
    story += fields("Pessoa de referência e telefone:", "Contato fora da área e telefone:",
                    "Ponto de encontro próximo / alternativa fora da área:",
                    "Quem precisa de apoio e quem pode ajudar:",
                    "Onde ficam a pasta, as chaves e os itens essenciais:")
    story += section("Revisão em cinco minutos",
        "Ligue ou confira um contato; veja se as cópias estão legíveis e se os endereços continuam corretos.",
        "Simule encontrar a pasta e sair pelo trajeto habitual, sem correr e sem bloquear a saída.",
        "Marque a próxima revisão e avise as pessoas envolvidas quando mudar o plano.")
    story += [p("Última revisão: ____ / ____ / ______    Próxima revisão: ____ / ____ / ______", "Copy"),
              p("Modelo editorial original de organização doméstica. Adapte às orientações locais. "
                "Esta ficha não substitui documentos oficiais nem instruções de emergência.", "SmallNote")]
    return story


def energy():
    story = heading("02", "Luz e energia com segurança",
                    "Prepare iluminação e comunicação para uma interrupção. "
                    "Este guia não ensina instalações, reparos elétricos ou operação de geradores.")
    story += section("Antes de faltar energia",
        "Deixe uma lanterna ou luminária a pilha em local fácil de alcançar. Teste os botões "
        "e guarde pilhas compatíveis conforme o manual.",
        "Mantenha telefone e bateria portátil carregados conforme as instruções do fabricante. "
        "Identifique cabos compatíveis e deixe-os junto dos equipamentos.",
        "Combine prioridades: primeiro contato e iluminação; depois outros usos. "
        "A autonomia varia com aparelho, estado da bateria e modo de uso.")
    story += section("Quando a luz apagar",
        "Use lanternas e luminárias a pilha em vez de velas, tochas ou lampiões a combustível. "
        "Ilumine primeiro o caminho e os degraus.",
        "Economize a bateria do telefone: reduza brilho, feche tarefas dispensáveis e combine "
        "horários para conferir mensagens. Preserve um meio de receber avisos.",
        "Afaste-se de fios caídos e de equipamentos elétricos molhados. Não toque nem tente reparar; "
        "procure a concessionária ou o serviço de emergência local.")
    story += section("Regras que evitam improvisos perigosos",
        "Nunca use gerador, churrasqueira ou fogareiro a combustível dentro de casa, garagem, "
        "barraca ou outro espaço fechado ou parcialmente fechado.",
        "Um gerador portátil deve ficar ao ar livre, a pelo menos 6,1 metros de portas, janelas "
        "e entradas de ar. Siga também o manual e use detector de monóxido de carbono. "
        "Essas precauções não substituem instalação e avaliação profissionais.",
        "Não faça ligações improvisadas ao quadro ou às tomadas. Peça a profissional habilitado "
        "que avalie qualquer sistema fixo de energia de reserva.")
    story += [p("Se o local deixar de ser seguro, busque um lugar de apoio conforme a orientação local. "
                "Não espere o fim da bateria para pedir ajuda.", "Deck"), PageBreak()]
    story += heading("02", "Teste de iluminação",
                    "Faça um ensaio curto com as luzes normais acesas. Você não precisa desligar a instalação elétrica.")
    story += section("Roteiro de dez minutos",
        "Encontre a lanterna sem usar a luz do telefone. Confira se outra pessoa também sabe onde ela fica.",
        "Ilumine o caminho até a saída e veja se há obstáculos. Ajuste a posição da luminária "
        "para evitar quedas e ofuscamento.",
        "Conecte a bateria portátil ao aparelho escolhido. Confirme que carrega e verifique "
        "as condições do cabo segundo o manual.",
        "Anote o resultado. Troque ou encaminhe para assistência qualquer item que falhe, "
        "em vez de contar com ele em uma interrupção.")
    story += fields("Lanterna / localização / tipo de pilha:",
                    "Bateria portátil / cabo / data do último teste:",
                    "Local de apoio combinado e como chegar com segurança:")
    story += section("Antes de guardar",
        "Deixe os itens acessíveis e secos, fora do alcance de crianças pequenas quando necessário. "
        "Siga o fabricante para armazenamento e recarga.",
        "Marque uma nova conferência e mantenha uma cópia impressa dos contatos essenciais.")
    story += [p("Referência de segurança: CDC, What to Do to Protect Yourself During a Power Outage, "
                "consultado em 17/11/2026 (cdc.gov, seção Natural Disasters). "
                "Procedimentos e ficha de teste redigidos originalmente para este guia. "
                "As instruções essenciais estão nestas páginas; não é necessário abrir um link.", "SmallNote")]
    return story


def offline():
    story = heading("03", "Sem internet, com seus arquivos",
                    "Prepare uma pequena biblioteca local e uma cópia de segurança que você saiba recuperar. "
                    "O roteiro serve para Linux, macOS e Windows.")
    story += section("1. Escolha um conjunto pequeno e útil",
        "Crie uma pasta chamada Essenciais offline. Coloque cópias dos contatos, mapas da região, "
        "manuais dos seus equipamentos e guias que você tem autorização para guardar.",
        "Confira se o arquivo foi baixado de verdade. Um atalho, favorito ou ícone de nuvem "
        "pode depender da internet; abra o conteúdo para testar.",
        "Prefira formatos que os programas já instalados consigam abrir. Anote o aplicativo "
        "usado e mantenha cópias legíveis dos documentos importantes.")
    story += section("2. Faça uma cópia separada",
        "Copie a pasta para uma mídia externa confiável com espaço disponível. "
        "Confirme o destino antes de copiar; não formate nem apague a única cópia.",
        "Mantenha o original e a cópia em locais distintos. Uma pasta sincronizada pode repetir "
        "exclusões e alterações; mantenha também uma cópia independente, desconectada quando não usada.",
        "Se a mídia guardar dados pessoais, proteja o acesso e considere a criptografia disponível "
        "no seu sistema. Guarde a chave de recuperação separadamente e teste o desbloqueio.")
    story += section("3. Prove que funciona",
        "Desative o Wi-Fi e desconecte o cabo de rede. Abra alguns arquivos locais, incluindo um mapa "
        "e um documento importante. Registre o que ainda depende de conexão.",
        "Reconecte apenas a mídia de backup e copie um arquivo de teste para uma pasta temporária. "
        "Abra essa cópia e confira seu conteúdo. Não sobrescreva o original durante o teste.",
        "Ejete a mídia pelo sistema antes de removê-la e guarde-a com segurança. "
        "Atualize a cópia após mudanças importantes e repita o teste regularmente.")
    story += [p("Backup pronto é backup recuperável. Uma mensagem de cópia concluída, sozinha, "
                "não comprova que os arquivos poderão ser abertos.", "Deck"), PageBreak()]
    story += heading("03", "Registro do teste offline",
                    "Use esta página para saber o que foi conferido e o que ainda falta. "
                    "Não escreva senhas ou chaves de recuperação aqui.")
    story += fields("Pasta principal / aparelho / aplicativo usado:",
                    "Mídia de backup / local onde fica guardada:",
                    "Arquivo restaurado no teste / resultado:",
                    "O que não abriu sem internet / ação necessária:")
    story += section("Checklist de saída da internet",
        "Os arquivos necessários abrem com a rede desligada e estão numa pasta fácil de encontrar.",
        "Outra pessoa de confiança sabe localizar os materiais, respeitando quem pode acessar dados pessoais.",
        "Há uma cópia impressa dos contatos e um plano para manter o aparelho carregado.",
        "A cópia de segurança foi testada e a mídia está desconectada e guardada.")
    story += [p("Último teste: ____ / ____ / ______    Próximo teste: ____ / ____ / ______", "Copy"),
              p("Referência: CISA e MS-ISAC, Ransomware Guide (2020), recomendações de cópias offline "
                "e testes de recuperação; consultado em 17/11/2026 em cisa.gov. "
                "Roteiro e ficha originais. Os passos estão completos aqui, sem necessidade de conexão.", "SmallNote")]
    return story


class ReproducibleCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        kwargs["invariant"] = 1
        super().__init__(*args, **kwargs)


def footer(canvas_, doc):
    canvas_.saveState()
    width, height = A4
    canvas_.setFillColor(ACCENT)
    canvas_.rect(20 * mm, height - 15 * mm, 12 * mm, 1.3 * mm, fill=1, stroke=0)
    canvas_.setStrokeColor(colors.HexColor("#d0dcd5"))
    canvas_.line(20 * mm, 18 * mm, width - 20 * mm, 18 * mm)
    canvas_.setFont("Helvetica", 8)
    canvas_.setFillColor(MUTED)
    canvas_.drawString(20 * mm, 12 * mm, "O Último Livro · " + EDITION)
    canvas_.drawRightString(width - 20 * mm, 12 * mm, f"{doc.page} / 2")
    canvas_.restoreState()


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="gerar PNGs a 120 dpi com Poppler")
    args = parser.parse_args()
    poppler = shutil.which("pdftoppm") if args.render else None
    if args.render and not poppler:
        parser.error("--render requer pdftoppm (Poppler) no PATH")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for identifier, title, content in (
        ("preparacao", "Organização e documentos", preparation),
        ("energia", "Luz e energia com segurança", energy),
        ("offline", "Sem internet, com seus arquivos", offline),
    ):
        target = OUTPUT / f"{identifier}.pdf"
        document = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=20 * mm,
                                     rightMargin=20 * mm, topMargin=23 * mm,
                                     bottomMargin=24 * mm, title=title,
                                     author="O Último Livro", subject="Guia prático offline em português")
        document.build(content(), onFirstPage=footer, onLaterPages=footer,
                       canvasmaker=ReproducibleCanvas)
        if poppler:
            subprocess.run([poppler, "-r", "120", "-png", str(target),
                            str(OUTPUT / identifier)], check=True)
        print(f"Gerado: {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
