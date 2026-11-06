# Règles de rédaction – « 15 minutes »

- Chaque article de `articles.json` a : slug, title, category, date, summary, body (liste de paragraphes), sources [{name,url?}], **author**, **motif**.
- **author** : alterner « Diego Carvalho » et « Mauricio Montero ».
- **motif** (illustration dessinée dans `illus.py`) : crowd (manifestation), tram, chart (chiffres/économie), parliament (politique/institutions), car, halloween, press (médias), communes, museum (culture/expos), village (vie locale/commune). Ajouter un motif dans `illus.py` si aucun ne convient.
- Textes entièrement réécrits, jamais copiés ; faits vérifiables uniquement, aucun détail inventé ; sources citées.
- Diego peut coller des « dossiers de presse » (préparés avec un autre outil) : s'en servir comme matière première, rédiger l'article de A à Z, ne reprendre que les faits confirmés.
- Build : `python3 build.py && touch docs/.nojekyll`, puis commit, `git pull --rebase`, push sur main.
- **Photos** : déposer le fichier dans `photos/` (à la racine du dépôt, pas dans docs/), puis ajouter à l'article `"image": "nom.jpg"` et `"image_credit": "Illustration générée par IA"` (ou « Photo : Prénom Nom »). Sans champ `image`, l'illustration dessinée (`motif`) est utilisée.

## Format des dossiers de presse reçus de Diego (ChatGPT)
Pour chaque actualité : identification (titre original, média, date de publication, auteur, lien, catégorie, lieu) ; contenu (titre développé, résumé détaillé, contexte, personnes/institutions, chiffres, chronologie, conséquences pour les habitants, réactions des autorités, informations manquantes).
Règles de publication :
1. Ne jamais inventer les informations manquantes.
2. Ne pas transformer une hypothèse en fait confirmé.
3. Ne pas présenter un article ancien comme une actualité du jour.
4. Ne pas confondre date de publication et date de l'événement.
5. Ne pas reproduire mot pour mot les articles des médias.
6. Pas deux articles sur le même événement sans angle différent.
7. Informations insuffisantes : mettre l'article en attente de vérification (ne pas publier).
Sujets en attente (détails insuffisants) : ARCAM (région Cossonay-Aubonne-Morges), Forward Morges.
