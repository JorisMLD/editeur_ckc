# Mode d'emploi — Éditeur de procédures cKc

Ce document explique, pas à pas, comment installer et utiliser l'application, même sans connaissance préalable de Python ou des environnements de développement. Suivez les sections dans l'ordre la première fois.

---

## 1. Vue d'ensemble

Le projet comporte deux outils complémentaires :

L'**application d'édition** (`app_procedures.py`) : une interface visuelle, ouverte dans le navigateur, pour construire des procédures (enchaînements d'opérateurs et de contrôles), visualiser leur coût et exporter le tout en LaTeX.

Le **carnet d'analyse** (`methodo.ipynb`) : un notebook Python pour calculer les coûts en détail, les croiser avec des profils d'élèves et produire des graphiques radar. Il s'utilise dans un second temps, pour l'analyse.

Les deux s'appuient sur les mêmes fichiers de données au format CSV (des tableaux texte).

---

## 2. Installation (à faire une seule fois)

### 2.1. Vérifier que Python est installé

Ouvrez un terminal (sous Ubuntu : `Ctrl+Alt+T` ; dans VSCodium : menu Terminal → Nouveau terminal). Tapez :

```bash
python3 --version
```

Si un numéro de version s'affiche (par exemple `Python 3.12`), Python est présent. Sinon, installez-le via la logithèque Ubuntu ou le site officiel python.org.

### 2.2. Créer un environnement isolé

Un « environnement virtuel » est un dossier qui contient une installation de Python dédiée au projet, pour éviter que les bibliothèques n'entrent en conflit avec le reste du système. On le crée **hors** du dossier synchronisé (Nextcloud), pour qu'il ne soit pas copié entre machines :

```bash
python3 -m venv ~/venvs/ckc
```

Cette commande crée l'environnement dans votre dossier personnel, sous `venvs/ckc`.

### 2.3. Activer l'environnement

À chaque session de travail, il faut **activer** l'environnement avant de lancer l'application :

```bash
source ~/venvs/ckc/bin/activate
```

Une fois activé, le début de la ligne du terminal affiche `(ckc)`. C'est le signe que tout est prêt.

### 2.4. Installer les bibliothèques nécessaires

Toujours dans le terminal, avec l'environnement activé :

```bash
pip install streamlit pandas matplotlib numpy
```

Cette étape se fait une seule fois. Elle télécharge les outils dont l'application a besoin.

---

## 3. Lancer l'application d'édition

Placez-vous d'abord dans le dossier du projet (celui qui contient `app_procedures.py` et les fichiers CSV). Par exemple :

```bash
cd ~/chemin/vers/cKc_python
```

Activez l'environnement si ce n'est pas déjà fait :

```bash
source ~/venvs/ckc/bin/activate
```

Puis lancez :

```bash
streamlit run app_procedures.py
```

Une page s'ouvre automatiquement dans votre navigateur, à l'adresse `http://localhost:8501`. Si elle ne s'ouvre pas seule, copiez cette adresse dans votre navigateur.

Important : une application Streamlit se lance **toujours** avec `streamlit run`, jamais avec `python app_procedures.py`. Le bouton « exécuter » (▶) de VSCodium utilise `python` et provoquera une erreur ; passez par le terminal.

Pour arrêter l'application, revenez dans le terminal et appuyez sur `Ctrl+C`.

---

## 4. Utiliser l'application

### 4.1. Charger les données

Au premier affichage, la colonne de gauche (la « barre latérale ») liste les fichiers à charger : opérateurs, contrôles, DEME, procédures, profils élèves. Les noms par défaut correspondent aux fichiers du projet. Si vos fichiers portent d'autres noms, corrigez les champs.

Cliquez ensuite sur le bouton **⬇️ Charger**. Un message de confirmation vert apparaît. Les listes d'opérateurs et de contrôles deviennent alors disponibles.

À noter : à chaque chargement, une copie de sauvegarde du fichier de procédures est automatiquement créée dans un sous-dossier `backup/`, par sécurité.

### 4.2. Comprendre l'écran principal

La partie centrale montre d'abord le **tableau des procédures existantes**, avec pour chacune son coût selon trois dimensions : Manipulation (M), Perception visuelle (V) et Planification (P), plus un total.

En dessous se trouvent les zones pour créer ou modifier une procédure.

### 4.3. Créer une nouvelle procédure

Repérez la section **Nouvelle procédure**. Renseignez une **clé** (identifiant court et unique, sans espace, par exemple `proc_carre_1`) et un **nom** (libellé lisible). La description est facultative. Ces deux champs, clé et nom, sont obligatoires.

Cliquez sur **Commencer la sélection**. Une zone de construction apparaît, avec les opérateurs et les contrôles présentés sous forme de boutons, regroupés par catégorie dans des blocs repliables.

Chaque clic sur un bouton **ajoute l'élément correspondant à la fin du déroulement**. Le déroulement en cours et le coût s'actualisent en temps réel au-dessus des boutons.

Si vous vous trompez, le bouton **↩️ Retirer le dernier élément** annule le dernier ajout.

Quand la procédure est complète, cliquez sur **✅ Enregistrer la procédure**. Elle est ajoutée au tableau et le fichier `procedures.csv` est mis à jour.

### 4.4. Modifier ou supprimer une procédure

Sous le tableau, un menu déroulant permet de choisir une procédure existante. Le bouton **✏️ Éditer** recharge son contenu dans la zone de construction (vous pouvez alors ajouter ou retirer des étapes, puis réenregistrer). Le bouton **🗑️ Supprimer** la retire définitivement, après mise à jour du CSV.

### 4.5. Réglages d'affichage (barre latérale)

Plusieurs réglages facilitent le confort d'usage : le nombre de colonnes de boutons, le fait que les catégories soient dépliées ou repliées par défaut, et la hauteur de la zone de boutons (presets Compact / Moyen / Grand / Très grand). La zone de boutons dispose d'un ascenseur interne : le déroulement et les coûts restent visibles en haut pendant que vous faites défiler les boutons.

### 4.6. Appliquer un profil d'élève

Si un fichier de profils est chargé, un menu **Profil actif** apparaît dans la barre latérale. En choisissant un élève, le tableau et les métriques affichent, en plus du coût nominal, le coût ajusté à ce profil. « Nominal » correspond au coût de référence, sans ajustement.

### 4.7. Exporter en LaTeX

Le bouton **📤 Exporter en LaTeX** de la barre latérale génère un fichier `.tex` horodaté dans le dossier du projet. Il contient les tableaux des DEME, des opérateurs, des contrôles et des procédures, avec leurs coûts. Si un profil est actif, ses coûts ajustés figurent également.

---

## 5. Éditer les fichiers CSV

Les données (opérateurs, contrôles, DEME, profils) se modifient dans un tableur. Deux recommandations importantes :

Enregistrez toujours vos fichiers en **UTF-8**, pour préserver les accents. Dans LibreOffice : Enregistrer sous → cocher « Éditer les paramètres du filtre » → choisir l'encodage Unicode (UTF-8).

**Fermez le fichier dans le tableur avant de le charger dans l'application** ou de le sauvegarder sur GitHub. Un fichier ouvert dans LibreOffice crée un fichier de verrouillage temporaire qui peut gêner.

Si vous cherchez un éditeur plus léger que LibreOffice sous Windows, Modern CSV ou Rons CSV Editor sont de bonnes options, à condition de vérifier qu'ils lisent bien l'UTF-8 et utilisent la virgule comme séparateur.

---

## 6. Sauvegarder son travail sur GitHub

Le projet est versionné avec Git et hébergé sur GitHub. Après une session de travail, pour sauvegarder vos modifications en ligne, ouvrez un terminal dans le dossier du projet et lancez, dans l'ordre :

```bash
git add .
git commit -m "Description courte de ce qui a changé"
git push
```

Rappel : fermez vos CSV dans le tableur avant de faire cela.

Vous pouvez également utiliser l'onglet de gestion de version intégré à VSCodium (icône en forme de branches, dans la barre de gauche), qui propose les mêmes actions par boutons.

---

## 7. En cas de problème

**« streamlit : commande introuvable »** — l'environnement n'est pas activé. Relancez `source ~/venvs/ckc/bin/activate`.

**« No module named streamlit »** — soit l'environnement n'est pas activé, soit les bibliothèques n'ont pas été installées (voir section 2.4).

**Les listes d'opérateurs ne s'affichent pas** — vous n'avez pas cliqué sur **⬇️ Charger**, ou un nom de fichier dans la barre latérale ne correspond pas à un fichier réellement présent dans le dossier.

**Les accents s'affichent mal** — le fichier n'est pas en UTF-8. Réenregistrez-le dans ce format.

**Erreur mentionnant `height` ou `st.container`** — votre version de Streamlit est trop ancienne. Mettez-la à jour avec `pip install --upgrade streamlit`.
