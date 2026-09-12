from flask import Flask, render_template, jsonify, request
import json, random, sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
BASE = Path(__file__).parent
DATA = json.loads((BASE / 'data.json').read_text(encoding='utf-8'))
full = BASE / 'qcm_scraped.json'
if full.exists():
    DATA['qcm'] = json.loads(full.read_text(encoding='utf-8'))
DB = BASE / 'civique.db'

THEME_GUIDES = {
    'Principes et valeurs de la République': 'Comprendre les valeurs, symboles et principes qui fondent la République française : liberté, égalité, fraternité, laïcité, démocratie et égalité entre les femmes et les hommes.',
    'Système institutionnel et politique': 'Comprendre comment fonctionne la République : Président, Gouvernement, Parlement, collectivités territoriales, élections et Union européenne.',
    'Droits et devoirs': 'Connaître les principaux droits et obligations d’une personne vivant en France : liberté, égalité devant la loi, respect des règles, impôts, justice et obligations civiques.',
    'Histoire géographie et culture': 'Retenir les grandes dates, les personnages, les territoires, les symboles et les éléments essentiels de l’histoire et de la culture françaises.',
    'Vivre dans la société française': 'Comprendre les règles de la vie quotidienne en France : famille, école, travail, santé, logement, services publics et relations entre les personnes.'
}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mode TEXT NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL,
        percent INTEGER NOT NULL,
        passed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id, created_at DESC);
    ''')
    con.commit(); con.close()

init_db()

@app.route('/')
def index():
    themes = {}
    for q in DATA['questions']:
        themes[q['theme']] = themes.get(q['theme'], 0) + 1
    return render_template('index.html', themes=themes, total=len(DATA['questions']))

@app.route('/api/questions')
def api_questions():
    result = []
    qcm_by_text = {x[0]: x for x in DATA['qcm']}
    for i, q in enumerate(DATA['questions']):
        item = dict(q)
        item['id'] = i + 1
        item['guide'] = THEME_GUIDES.get(q['theme'], '')
        # If an equivalent QCM exists, expose its pedagogical explanation in study mode.
        if q['question'] in qcm_by_text:
            x = qcm_by_text[q['question']]
            item['learning'] = x[3]
            item['answer_available'] = True
        else:
            item['learning'] = None
            item['answer_available'] = False
        result.append(item)
    return jsonify(result)

@app.route('/api/qcm')
def api_qcm():
    size = int(request.args.get('size', 20))
    size = 40 if size == 40 else 20
    selected = random.sample(DATA['qcm'], min(size, len(DATA['qcm'])))
    result = []
    for item in selected:
        text, choices, correct, explanation = item
        pairs = list(enumerate(choices)); random.shuffle(pairs)
        new_choices = [p[1] for p in pairs]
        new_correct = next(i for i, p in enumerate(pairs) if p[0] == correct)
        result.append({'question': text, 'choices': new_choices, 'correct': new_correct, 'explanation': explanation})
    return jsonify(result)

@app.post('/api/user')
def create_user():
    name = (request.json or {}).get('name', '').strip()
    if not name or len(name) > 80:
        return jsonify({'error': 'Nom invalide'}), 400
    con = db(); cur = con.execute('INSERT INTO users(name, created_at) VALUES (?, ?)', (name, datetime.now().isoformat(timespec='seconds')))
    con.commit(); uid = cur.lastrowid; con.close()
    return jsonify({'id': uid, 'name': name})

@app.get('/api/history/<int:user_id>')
def history(user_id):
    con = db(); rows = con.execute('SELECT id, mode, score, total, percent, passed, created_at FROM attempts WHERE user_id=? ORDER BY id DESC LIMIT 20', (user_id,)).fetchall(); con.close()
    return jsonify([dict(r) for r in rows])

@app.post('/api/attempt')
def save_attempt():
    data = request.json or {}; user_id = int(data.get('user_id', 0)); score = int(data.get('score', 0)); total = int(data.get('total', 0)); mode = data.get('mode', 'qcm')
    if not user_id or not total or score < 0 or score > total: return jsonify({'error': 'Données invalides'}), 400
    percent = round(score / total * 100); passed = int(mode == 'examen' and total == 40 and score >= 32)
    con = db(); con.execute('INSERT INTO attempts(user_id, mode, score, total, percent, passed, created_at) VALUES (?,?,?,?,?,?,?)', (user_id, mode, score, total, percent, passed, datetime.now().isoformat(timespec='seconds'))); con.commit(); con.close()
    return jsonify({'ok': True, 'percent': percent, 'passed': bool(passed)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
