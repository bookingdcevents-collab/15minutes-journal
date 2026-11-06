# Règles de rédaction – « 15 minutes »

- Chaque article de `articles.json` a : slug, title, category, date, summary, body (liste de paragraphes), sources [{name,url?}], **author**, **motif**.
- **author** : alterner « Diego Carvalho » et « Mauricio Montero ».
- **motif** (illustration dessinée dans `illus.py`) : crowd (manifestation), tram, chart (chiffres/économie), parliament (politique/institutions), car, halloween, press (médias), communes, museum (culture/expos), village (vie locale/commune). Ajouter un motif dans `illus.py` si aucun ne convient.
- Textes entièrement réécrits, jamais copiés ; faits vérifiables uniquement, aucun détail inventé ; sources citées.
- Diego peut coller des « dossiers de presse » (préparés avec un autre outil) : s'en servir comme matière première, rédiger l'article de A à Z, ne reprendre que les faits confirmés.
- Build : `python3 build.py && touch docs/.nojekyll`, puis commit, `git pull --rebase`, push sur main.
- **Photos** : déposer le fichier dans `photos/` (à la racine du dépôt, pas dans docs/), puis ajouter à l'article `"image": "nom.jpg"` et `"image_credit": "Illustration générée par IA"` (ou « Photo : Prénom Nom »). Sans champ `image`, l'illustration dessinée (`motif`) est utilisée.
