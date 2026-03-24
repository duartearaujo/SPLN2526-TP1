import re
import spacy
import nltk
from collections import Counter

nlp = spacy.load("pt_core_news_md")

latex = """
\\documentclass{article}
\\usepackage{graphicx}
\\graphicspath{ {BFerreiraHTML/img} }

\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}

\\usepackage{microtype}
\\usepackage{xurl}
\\usepackage{hyperref}
\\usepackage{csquotes}
\\usepackage{multicol}

\\title{Olhares do presente: A Fotografia como testemunho da pós-memória  
“An Ode to the Places I Never Met”}
\\author{Beatriz Ferreira}

\\begin{document}
\\maketitle
"""

with open('BFerreiraHTML/BFerreiras.html', 'r') as f:
    text = f.read()

with open('BFerreira1.txt', 'r') as f:
    text_for_analysis = f.read()

sections = re.split('<t>', text)

doc = nlp(text_for_analysis)

# Lista de frases e texto sem pontuação
sentences = nltk.sent_tokenize(text_for_analysis)
text_no_punct = re.sub(r'[^\w\s-]', '', text_for_analysis)
print(sentences)

# Tokenização e geração de trigramas
tokens = nltk.word_tokenize(text_no_punct)
trigrams = list(nltk.trigrams(tokens))
trigram_counts = Counter(trigrams)

# Pontuação das frases
scores = []
for sentence in sentences:
    tokens = nltk.word_tokenize(sentence)
    trigrams = list(nltk.trigrams(tokens))
    score = sum(trigram_counts[trigram] for trigram in trigrams)
    scores.append((sentence, score))

latex += """
\\begin{abstract}
Frases escolhidas com base na frequência de trigramas:
\\begin{itemize}
"""

# Seleção das 3 melhores frases
top_sentences = sorted(scores, key=lambda x: x[1], reverse=True)[:3]
for sentence, score in top_sentences:
    latex += f"\\item {sentence}\n"

latex += """ 
\\end{itemize}
\\end{abstract}
"""

latex += """
\\section*{Entidades Nomeadas}
\\begin{multicols}{4}
\\begin{itemize}
"""
for ent in doc.ents:
    latex += f"\\item {ent.text} ({ent.label_})\n"
latex += """
\\end{itemize}
\\end{multicols}
"""

# Formatar o texto para LaTeX
for section in sections[1:]:
    title = section.split('\n')[0].strip()
    title = re.sub(r'<b>', '', title)
    title = re.sub(r'</b>', '', title)
    title = re.sub(r'^\d+\.\s+', '', title)

    content = '\n'.join(section.split('\n')[1:]).strip()

    content = re.sub(r'<i>([^<]+)</i>', r'\\textit{\1}', content)
    content = re.sub(r'<b>([^<]+)</b>', r'\\textbf{\1}', content)
    content = re.sub(r'<subsec>\d+\.\d+ ([^<\n]+)', r'\\subsection{{{\1}}}', content)

    content = re.sub(r'<img src="([^"]+)"/>', r'\\includegraphics[width=\\linewidth]{\1}', content)

    urls = re.findall(r'https://[^\\\n]*', content)
    for url in urls:
        content = content.replace(url, f'\\url{{{url}}}')

    n_notes = re.findall(r'<note>(\d+) ([^<]+)', content)
    for num, note in n_notes:
        content = content.replace(f'@NOTE{num}', f'\\footnote{{{note}}}')
    
    content = re.sub(r'<note>\d+ [^<]+</note>', '', content)

    latex += f"\\section{{{title}}}\n"
        
    latex += content + "\n\n"

latex += """
\\section*{Artigo Original}
Beatriz Ferreira, Olhares do presente: A Fotografia como testemunho da pós-memória “An Ode to the Places I Never Met”: \\url{http://hdl.handle.net/10400.14/53004}
\\end{document}
"""

with open('BFerreira.tex', 'w', encoding='utf-8') as f:
    f.write(latex)