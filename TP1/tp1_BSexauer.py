import re
import nltk
import spacy
from collections import Counter
from nltk.lm import MLE
from nltk.lm.preprocessing import padded_everygram_pipeline
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.lm import Laplace
nltk.download('floresta')
from nltk.corpus import floresta

nlp = spacy.load("pt_core_news_md")

latex = """
\\documentclass{article}

\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}

\\usepackage{microtype}
\\usepackage{xurl}
\\usepackage{hyperref}
\\usepackage{csquotes}
\\usepackage{multicol}

\\title{A fotografia como modelo narrativo e
suporte de reflexão teórica em
Un monde sans rivage, de Hélène Gaudy}
\\author{Bárbara Sexauer}

\\begin{document}
\\maketitle
"""

with open('BSexauer.txt', 'r') as f:
    text = f.read()

sections = re.split('<t>', text)

# Preparar o texto para análise
text_for_analysis = ""

for section in sections[1:-1]:
    content = '\n'.join(section.split('\n')[1:]).strip()
    content = re.sub(r'\n', ' ', content)
    notes = re.findall(r'<note>\d+ ([^<]+)<\\note>', content)
    content = re.sub(r'<note>\d+ ([^<]+)<\\note>', '', content)
    content = re.sub(r'@NOTE\d+', '', content)
    
    text_for_analysis += f"{content} "
    text_for_analysis += ' '.join(notes) + ' '

doc = nlp(text_for_analysis)

nltk.download('floresta')
nltk.download('punkt')

sentences = floresta.sents()
sentences = [[w.lower() for w in sent] for sent in sentences]

n = 3
train_data, padded_vocab = padded_everygram_pipeline(n, sentences)

model = Laplace(n)
model.fit(train_data, padded_vocab)

def sentence_perplexity(model, sentence_tokens):
    return model.perplexity(sentence_tokens)

test_sentences = nltk.sent_tokenize(text_for_analysis)

scores = []
for s in test_sentences:
    tokens = [w.lower() for w in nltk.word_tokenize(s)]
    pp = sentence_perplexity(model, tokens)
    print(f"Sentence: {s}")
    print(f"Perplexity: {pp:.2f}\n")
    scores.append((pp, s))

print(scores)

latex += """
\\begin{abstract}
Frases escolhidas com base na perplexidade do modelo de trigramas:
\\begin{itemize}
"""

# Seleção das 3 melhores frases
top_sentences = sorted(scores, key=lambda x: x[1])[:3] # sorting error. Devia ser x[0]
for score, sentence in top_sentences:
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

# Formatar o artigo para LaTeX
for section in sections[1:]:
    title = section.split('\n')[0].strip()
    title = re.sub(r'^\d+\.\s+', '', title)

    content = '\n'.join(section.split('\n')[1:]).strip()

    urls = re.findall(r'https://[^\\\n]*', content)
    for url in urls:
        content = content.replace(url, f'\\url{{{url}}}')

    n_notes = re.findall(r'<note>(\d) ([^<]+)', content)
    for num, note in n_notes:
        content = content.replace(f'@NOTE{num}', f'\\footnote{{{note}}}')
    
    content = re.sub(r'<note>\d [^<]+<\\note>', '', content)

    latex += f"\\section{{{title}}}\n"
        
    latex += content + "\n\n"

latex += """
\\section*{Artigo Original}
Bárbara Sexauer, A fotografia como modelo narrativo e suporte de reflexão teórica em Un monde sans rivage, de Hélène Gaudy: \\url{https://doi.org/10.51427/com.jcs.2025.8.5}
\\end{document}
"""

with open('BSexauer.tex', 'w', encoding='utf-8') as f:
    f.write(latex)