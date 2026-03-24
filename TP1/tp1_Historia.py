import re
import time
import json
import nltk
import spacy
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from collections import Counter

#driver = webdriver.Chrome()
#driver.get("https://www.todamateria.com.br/historia-da-fotografia/")

def download_image(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                f.write(response.content)
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")

html_doc = requests.get("https://www.todamateria.com.br/historia-da-fotografia/")
soup = BeautifulSoup(html_doc.text, 'html.parser')

titulo = soup.find("h1", class_="article-title").text
autor = soup.find("div", class_="author-article--t__info__name").span.text
conteudo = soup.find("div", class_="content-wrapper")

texto_para_analisar = ""

sections = {}
sections[titulo] = ""

current_section = None

for tag in conteudo.contents:
    if tag.name == "h2":
        current_section = tag.text
        sections[current_section] = ""

    elif tag.name == "h3":
        sections[current_section] += f"\\subsection*{{{tag.text}}}\n\n"

    elif tag.name == "p" and current_section is not None:
        sections[current_section] += tag.text + "\n\n"
        texto_para_analisar += tag.text + "\n\n"

    elif tag.name == "p" and current_section is None:
        sections[titulo] += tag.text + "\n\n"
        texto_para_analisar += tag.text + "\n\n"

    elif tag.name == "figure":
        img = tag.img
        caption = tag.figcaption.text if tag.figcaption else ""
        filename = img['src'].split("/")[-1] # Extrair o nome do arquivo do URL
        filename = filename.split("?")[0]  # Remover parâmetros do URL
        download_image(img['src'], f"HistoriaIMG/{filename}")

        sections[current_section] += f"""
        \\begin{{figure}}[H]
        \\includegraphics[width=\\linewidth]{{{filename}}}\n\n
        \\caption{{{caption}}}\n\n
        \\end{{figure}}
        """

    elif tag.name == "ul":
        sections[current_section] += f"\\begin{{itemize}}\n"
        for li in tag.find_all("li"):
            sections[current_section] += f"\\item{{{li.text}}}\n"
            texto_para_analisar += li.text + "\n\n"
        sections[current_section] += f"\\end{{itemize}}\n\n"

nlp = spacy.load("pt_core_news_md")
doc = nlp(texto_para_analisar)

# Lista de frases e texto sem pontuação
frases = nltk.sent_tokenize(texto_para_analisar)
text_no_punct = re.sub(r'[^\w\s-]', '', texto_para_analisar)
print(frases)

# Tokenização e geração de trigramas
tokens = nltk.word_tokenize(text_no_punct)
trigrams = list(nltk.trigrams(tokens))
trigram_counts = Counter(trigrams)

# Pontuação das frases
scores = []
for frase in frases:
    tokens = nltk.word_tokenize(frase)
    trigrams = list(nltk.trigrams(tokens))
    score = sum(trigram_counts[trigram] for trigram in trigrams)
    scores.append((frase, score))

res =f"""
\\documentclass{{article}}
\\usepackage{{graphicx}}
\\graphicspath{{ {{HistoriaIMG}} }}

\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}

\\usepackage{{microtype}}
\\usepackage{{xurl}}
\\usepackage{{hyperref}}
\\usepackage{{csquotes}}
\\usepackage{{multicol}}
\\usepackage{{float}}
\\usepackage[numbers]{{natbib}}

\\title{{{titulo}}}
\\author{{{autor}}}

\\begin{{document}}
\\maketitle
"""

res += """
\\begin{abstract}
Frases escolhidas com base na frequência de trigramas:
\\begin{itemize}
"""

# Seleção das 3 melhores frases
top_frases = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
for frase, score in top_frases:
    res += f"\\item {frase}\n"

res += """ 
\\end{itemize}
\\end{abstract}
"""

res += """
\\section*{Entidades Nomeadas}
\\begin{multicols}{4}
\\begin{itemize}
"""
for ent in doc.ents:
    res += f"\\item {ent.text} ({ent.label_})\n"
res += """
\\end{itemize}
\\end{multicols}
"""

for section in sections:
    res += f"\\section{{{section}}}\n\n"
    res += sections[section] + "\n\n"

with open('references.bib', 'w') as f:
    f.write(f"""
            @misc{{{autor},
                title={{{titulo}}},
                author={{{autor}}},
                howpublished={{\\url{{https://www.todamateria.com.br/historia-da-fotografia/}}}}
            }}
            """)

res += f"""
\\section*{{Artigo Original}}
Laura Aidar, História da Fotografia: \\url{{https://www.todamateria.com.br/historia-da-fotografia/}}
\\end{{document}}
"""

with open("Historia.tex", "w", encoding="utf8") as f:
    f.write(res)
    