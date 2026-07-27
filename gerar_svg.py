#!/usr/bin/env python3
"""
Le summary.json e escreve dashboard.svg.

Uso: python3 gerar_svg.py summary.json dashboard.svg
"""

import json
import sys

# Cores do tema dark do Grafana. Fixas de proposito: o SVG precisa
# ficar identico no light e no dark mode do GitHub.
FUNDO      = "#111217"
PAINEL     = "#181b1f"
BORDA      = "#2c3235"
TEXTO      = "#ccccdc"
TEXTO_FRACO= "#9fa7b3"
VERDE      = "#73bf69"
AZUL       = "#5794f2"
LARANJA    = "#ff9830"
VERMELHO   = "#f2495c"
AMARELO    = "#fade2a"


def total_do_repo(repo):
    """Soma todas as severidades de um repo, ignorando o campo 'repo'."""
    return sum(valor for chave, valor in repo.items() if chave != "repo")


def painel(x, y, largura, altura, titulo):
    """Retangulo de painel do Grafana com titulo."""
    return f"""
  <rect x="{x}" y="{y}" width="{largura}" height="{altura}" rx="3"
        fill="{PAINEL}" stroke="{BORDA}" stroke-width="1"/>
  <text x="{x + 12}" y="{y + 20}" font-family="Inter, sans-serif"
        font-size="11" fill="{TEXTO_FRACO}">{titulo}</text>"""


def cartao(x, y, titulo, valor, cor):
    """Painel de estatistica: titulo pequeno em cima, numero grande embaixo."""
    return painel(x, y, 152, 76, titulo) + f"""
  <text x="{x + 12}" y="{y + 58}" font-family="Inter, sans-serif"
        font-size="26" fill="{cor}">{valor}</text>"""


def barra_repo(x, y, nome, critical, high, medium, low, maximo, largura_max):
    """Barra horizontal empilhada por severidade, para um repositorio."""
    total = critical + high + medium + low
    # medium e low entram esmaecidos: o olho deve ir para critical e high.
    partes = [(critical, VERMELHO, 1), (high, LARANJA, 1),
              (medium, AMARELO, 0.75), (low, AZUL, 0.55)]

    svg = f"""
  <text x="{x}" y="{y + 9}" font-family="monospace" font-size="10"
        fill="{TEXTO_FRACO}">{nome[:30]}</text>"""

    inicio = x + 195
    for quantidade, cor, opacidade in partes:
        if quantidade == 0:
            continue
        comprimento = quantidade / maximo * largura_max
        svg += f"""
  <rect x="{inicio:.1f}" y="{y}" width="{comprimento:.1f}" height="10"
        fill="{cor}" opacity="{opacidade}"/>"""
        inicio += comprimento

    svg += f"""
  <text x="{x + 195 + largura_max + 30}" y="{y + 9}" text-anchor="end"
        font-family="monospace" font-size="10" fill="{TEXTO}">{total}</text>"""
    return svg


def gerar(dados):
    totais = dados["totals"]
    data = dados["generated_at"][:10]

    total_geral = (totais["critical"] + totais["high"]
                   + totais["medium"] + totais["low"])

    # Ordena os repos do mais problematico para o menos, e fica com os 8 piores.
    ordenados = sorted(dados["repos"], key=total_do_repo, reverse=True)
    piores = ordenados[:8]
    maximo = total_do_repo(piores[0])

    # Quanto os 8 piores representam do total.
    soma_piores = sum(total_do_repo(r) for r in piores)
    percentual = round(soma_piores / total_geral * 100)

    zerados = sum(1 for r in dados["repos"] if total_do_repo(r) == 0)

    altura = 434
    svg = f"""<svg width="680" height="{altura}" viewBox="0 0 680 {altura}"
     xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="680" height="{altura}" fill="{FUNDO}"/>

  <text x="15" y="24" font-family="Inter, sans-serif" font-size="13"
        fill="{TEXTO}">security posture</text>
  <text x="128" y="24" font-family="Inter, sans-serif" font-size="11"
        fill="#6e7583">/ {dados.get('owner', 'ISXDora')}</text>
  <text x="15" y="40" font-family="Inter, sans-serif" font-size="10"
        fill="#6e7583">varredura de dependências · todos os repositórios públicos</text>
  <rect x="524" y="14" width="141" height="20" rx="3"
        fill="{PAINEL}" stroke="{BORDA}"/>
  <text x="536" y="28" font-family="Inter, sans-serif" font-size="10"
        fill="{TEXTO_FRACO}">linha de base · {data}</text>
"""

    svg += cartao(15,  54, "repositórios", totais["repos"],   AZUL)
    svg += cartao(177, 54, "critical",         totais["critical"], VERMELHO)
    svg += cartao(339, 54, "high",             totais["high"],     LARANJA)
    svg += cartao(501, 54, "achados",            total_geral,        TEXTO)

    svg += painel(15, 142, 638, 174,
                  f"distribuição · {percentual}% dos achados estão em {len(piores)} de {totais['repos']} repositórios")
    y = 168
    for repo in piores:
        svg += barra_repo(27, y, repo["repo"],
                          repo.get("CRITICAL", 0), repo.get("HIGH", 0),
                          repo.get("MEDIUM", 0), repo.get("LOW", 0),
                          maximo, 380)
        y += 16

    # Legenda das cores
    legenda = [("critical", VERMELHO), ("high", LARANJA),
               ("medium", AMARELO), ("low", AZUL)]
    x = 27
    for nome, cor in legenda:
        svg += f"""
  <rect x="{x}" y="298" width="8" height="8" rx="2" fill="{cor}"/>
  <text x="{x + 13}" y="306" font-family="Inter, sans-serif" font-size="10"
        fill="{TEXTO_FRACO}">{nome}</text>"""
        x += 75

    svg += painel(15, 324, 638, 96, "alcance da medição")
    svg += f"""
  <text x="27" y="366" font-family="Inter, sans-serif" font-size="10.5"
        fill="{TEXTO_FRACO}">{zerados} dos {totais['repos']} repositórios não retornaram achados. Inclui projetos sem arquivo de dependência declarado,</text>
  <text x="27" y="382" font-family="Inter, sans-serif" font-size="10.5"
        fill="{TEXTO_FRACO}">que o scanner não consegue avaliar — ausência de achado não equivale a ausência de risco.</text>
  <line x1="27" y1="394" x2="641" y2="394" stroke="{BORDA}"/>
  <text x="27" y="410" font-family="monospace" font-size="9.5"
        fill="#6e7583">trivy · scan-type: repo · scanners: vuln</text>
  <text x="641" y="410" text-anchor="end" font-family="monospace" font-size="9.5"
        fill="#6e7583">série temporal a partir da 2ª execução</text>

</svg>"""
    return svg


if __name__ == "__main__":
    entrada = sys.argv[1] if len(sys.argv) > 1 else "summary.json"
    saida = sys.argv[2] if len(sys.argv) > 2 else "dashboard.svg"

    with open(entrada) as arquivo:
        dados = json.load(arquivo)

    with open(saida, "w") as arquivo:
        arquivo.write(gerar(dados))

    print(f"escrito: {saida}")
