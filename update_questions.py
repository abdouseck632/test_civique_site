import json, re
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = 'https://simulateur-examen-civique.fr/revisions/carte-sejour-serie-{}.html'
out=[]
for n in range(1,5):
    url=BASE.format(n)
    print('Téléchargement',url)
    html=requests.get(url,timeout=30).text
    soup=BeautifulSoup(html,'html.parser')
    for h3 in soup.find_all('h3'):
        text=h3.get_text(' ',strip=True)
        m=re.match(r'\d+\.\s*(.*)',text)
        if not m: continue
        q=m.group(1).strip()
        # options are the list items until the next h3; locate the following siblings
        opts=[]; answer=None; explanation=''
        node=h3.find_next_sibling()
        while node and node.name!='h3':
            t=node.get_text(' ',strip=True)
            if t.startswith('Réponse :'):
                answer=t
            elif node.name=='ul':
                opts += [li.get_text(' ',strip=True) for li in node.find_all('li')]
            elif t.startswith('Réponse :'):
                answer=t
            node=node.find_next_sibling()
        if len(opts)==4 and answer:
            letter=re.search(r'Réponse\s*:\s*([ABCD])\.',answer)
            if letter:
                correct='ABCD'.index(letter.group(1))
                exp=answer.split('.',1)[1].strip() if '.' in answer else ''
                out.append({'question':q,'choices':opts,'correct':correct,'explanation':exp,'source_series':n})

# Deduplicate by question text, preserving first occurrence.
seen=set(); clean=[]
for x in out:
    k=x['question'].lower().strip()
    if k not in seen:
        seen.add(k); clean.append(x)
Path('qcm_scraped.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(clean)} questions QCM enregistrées dans qcm_scraped.json')
