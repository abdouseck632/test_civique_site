# Test Civique CSP — version 3

Version pédagogique avec :
- 191 questions officielles de connaissance ;
- fiches d'apprentissage avant les QCM ;
- QCM 20 questions ;
- examen blanc 40 questions ;
- nom/prénom enregistré localement ;
- historique des scores avec SQLite ;
- préparation par thème.

## Installation

```bash
pip install flask requests beautifulsoup4
python update_questions.py
python app.py
```

Puis ouvrir http://127.0.0.1:5000

### Base de données

Le fichier `civique.db` est créé automatiquement au premier démarrage. Il contient uniquement le nom choisi dans l'application et l'historique des tentatives. Les données restent locales à cette installation.

### Examen blanc

Le site propose 40 questions et considère 32/40 comme seuil de réussite, conformément aux informations officielles actuellement publiées. L'examen officiel comporte aussi des mises en situation ; elles ne sont pas publiées officiellement, donc ce site ne les présente pas comme des questions officielles.

### Questions QCM supplémentaires

`update_questions.py` peut récupérer les séries d'entraînement disponibles sur simulateur-examen-civique.fr. Ces questions/réponses sont pédagogiques et indépendantes de l'administration. Vérifier les conditions et attributions de la source avant toute redistribution publique.
# testcivique
