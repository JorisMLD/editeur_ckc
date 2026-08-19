# Éditeur de procédures cKc — Documentation technique

Ce dépôt regroupe les outils logiciels du projet de recherche cKc / DYSDYN portant sur la modélisation du coût cognitif de procédures géométriques. Il comporte deux composants Python indépendants mais complémentaires : une application interactive d'édition (`app_procedures.py`) et un carnet d'analyse (`methodo.ipynb`).

Ce document décrit l'architecture du code. Pour l'installation et l'utilisation, voir `MODE_EMPLOI.md`.

---

## 1. Modèle conceptuel

Le domaine repose sur quelques notions imbriquées.

Les **DEME** (anciennement « infra-maths » ou IM) sont les actions élémentaires observables, codées de I1 à I11. Chaque DEME porte un coût selon trois dimensions : manipulation (`m`), perception visuelle (`v`) et planification (`p`).

Les **opérateurs** sont des actions instrumentales, les **contrôles** des vérifications. Chacun mobilise un certain nombre de DEME, indiqué par un décompte dans les colonnes I1 à I11 de son fichier.

Une **procédure** est un enchaînement ordonné d'opérateurs et de contrôles.

Un **profil élève** est un jeu de multiplicateurs qui pondère le coût nominal pour modéliser les difficultés propres à un élève.

La formule de coût d'une procédure, pour une dimension donnée, est :

```
coût_dim = mult_dim × Σ_étapes Σ_DEME ( occurrences_DEME × coût_nominal_DEME_dim × mult_DEME )
```

où `mult_dim` et `mult_DEME` valent 1 dans le cas nominal, et prennent les valeurs du profil lorsqu'un élève est sélectionné.

---

## 2. Fichiers de données

Le format retenu est le CSV, pour sa simplicité, sa lisibilité en texte brut et sa robustesse à la synchronisation. Tous les fichiers sont attendus en UTF-8, mais le chargement tolère aussi latin-1 et cp1252 par détection automatique.

`DEME.csv` — table des actions élémentaires. Colonnes : code (numérique, normalisé en I1…I11 à la lecture), libellé de l'action, et les trois coûts (manipulation, perception visuelle, planification).

`operateurs.csv` — un opérateur par ligne. Colonnes utiles : une colonne de catégorie et une de numéro (les deux premières, sans en-tête explicite), `clef`, `Nom`, finalité, schème, détail, et les colonnes de décompte I1…I11.

`controles.csv` — un contrôle par ligne. Structure analogue : catégorie et numéro en tête, `Clef`, `Nom`, deux assertions, et les colonnes I1…I11.

`procedures.csv` — géré par l'application. Colonnes : `clef`, `nom`, `description`, `deroulement` (les clés d'étapes séparées par `|`).

`profils.csv` — format large, un profil par ligne. Colonnes : `clef_profil`, `nom_profil`, les multiplicateurs globaux `mult_m`, `mult_v`, `mult_p`, puis un multiplicateur par DEME `mult_I1`…`mult_I11`.

---

## 3. Architecture de `app_procedures.py`

Le script est une application Streamlit d'un seul tenant, organisée en sections repérées par des bandeaux de commentaires.

### 3.1. Fonctions d'entrée-sortie

`read_csv_auto` lit un CSV en essayant successivement plusieurs encodages et en laissant pandas détecter le séparateur. `normalize_col` nettoie un nom de colonne (sans accents, minuscules, underscores) pour rendre la reconnaissance des colonnes robuste aux variations de casse et d'orthographe. `backup_file` copie un fichier dans le sous-dossier `backup/` avec un horodatage.

### 3.2. Chargement des données

`load_inframaths` lit `DEME.csv`, mappe les colonnes vers les noms internes (`m`, `v`, `p`, `label`), filtre les lignes vides et normalise les codes numériques en I1…I11 pour les faire correspondre aux colonnes des opérateurs et contrôles.

`load_operateurs` et `load_controles` suivent la même logique. Ils repèrent les colonnes par nom (insensible à la casse), capturent la catégorie (propagée vers le bas par remplissage, `ffill`) et le numéro issus des colonnes sans en-tête, filtrent les lignes sans clé, puis convertissent les colonnes DEME en nombres. Un point d'attention corrigé : la propagation de catégorie est faite sur le tableau complet **avant** le filtrage des lignes vides, faute de quoi les catégories se désaligneraient.

`load_procedures_dict` et `save_procedures_csv` assurent l'aller-retour entre le CSV de procédures et la structure interne (un dictionnaire indexé par clé, dont le déroulement est une liste de clés d'étapes).

`create_profil_template` et `load_profils` gèrent le fichier de profils au format large.

### 3.3. Calcul des coûts

`calc_nominal_cost` applique la formule de coût sans pondération : pour chaque étape, il additionne les contributions de chaque DEME mobilisé. `calc_profil_cost` reprend le même parcours en appliquant les multiplicateurs par DEME, puis les multiplicateurs globaux de dimension. La fonction auxiliaire `_im_cols_in` liste les DEME effectivement mobilisés dans une ligne (décompte strictement positif).

### 3.4. Interface

`button_grid` et `button_grid_grouped` produisent les grilles de boutons ; la seconde regroupe les éléments par catégorie dans des blocs repliables (`st.expander`), en préservant l'ordre d'apparition des catégories. Un clic sur un bouton ajoute la clé correspondante au déroulement en cours.

Le corps du script construit ensuite la barre latérale (choix des fichiers, profil actif, réglages d'affichage, export), le tableau des procédures existantes avec leurs coûts, les formulaires de création et d'édition, et la zone de construction encapsulée dans un conteneur à hauteur fixe avec ascenseur.

### 3.5. Export LaTeX

`export_latex` produit un fichier `.tex` horodaté contenant quatre tableaux (DEME, opérateurs, contrôles, procédures). Les numéros de ligne sont repris de la colonne de numéro du CSV via `fmt_numero` (qui préserve les valeurs comme « 11bis » tout en supprimant les décimales parasites). À chaque changement de catégorie, une ligne pleine largeur (`\multicolumn`) est insérée en en-tête de groupe. `escape_latex` échappe les caractères spéciaux. Les références croisées utilisent des macros `\rref`, `\cref`, `\pref` à définir dans le préambule du document LaTeX cible.

---

## 4. Architecture de `methodo.ipynb`

Le notebook est le volet analytique. Il n'est pas encore aligné sur la terminologie la plus récente (il parle de descripteurs `de_` là où l'application parle de DEME `im_`) et devra être repris ultérieurement pour harmonisation.

Sa structure suit quatre temps. D'abord l'**import** des données (contrôles, opérateurs, procédures, et un fichier `eleves.csv` de profils). Ensuite le **calcul des coûts**, décliné selon quatre croisements : une procédure seule, toutes les procédures, le croisement avec un élève, et le croisement complet élèves × procédures sous forme de tableau multi-indexé. Puis l'**export** de ces tableaux en CSV. Enfin la **visualisation** par graphiques radar (matplotlib), comparant coût brut de la procédure, profil de l'élève et coût combiné, avec une fonction d'export de l'ensemble des graphiques en fichiers PNG.

Les fonctions de calcul du notebook reposent sur la même logique que l'application, mais avec des conventions distinctes. Un chantier d'harmonisation entre les deux composants (nommage des colonnes, source unique des coûts DEME, format des profils) est à prévoir.

---

## 5. Choix techniques et points d'attention

Le format CSV a été préféré au xlsx pour la robustesse à la synchronisation (Nextcloud) et au versionnement (Git), un fichier texte se prêtant à la détection et à la résolution de conflits, contrairement à un binaire.

La numérotation des opérateurs et contrôles est reprise du CSV plutôt que recalculée, afin de respecter des valeurs non séquentielles comme « 11bis ».

Les valeurs manquantes dans les colonnes de décompte DEME sont traitées comme des zéros.

Les codes DEME sont insensibles à la casse (i9 et I9 sont équivalents), la normalisation ramenant tout en majuscules.

Un bouton de régénération du template de profils a été volontairement retiré de l'interface : il présentait un risque d'écrasement des profils existants. Ce type d'action destructrice ne doit pas être exposé sans garde-fou.

L'environnement virtuel et le dossier `backup/` sont exclus de la synchronisation et du versionnement (`.gitignore`), le premier pour éviter les conflits entre machines, le second parce qu'il s'agit de copies locales de sécurité.

---

## 6. Structure du dépôt

```
cKc_python/
├── app_procedures.py     Application d'édition (Streamlit)
├── methodo.ipynb         Carnet d'analyse (Jupyter)
├── DEME.csv              Table des actions élémentaires et coûts
├── operateurs.csv        Opérateurs et DEME mobilisés
├── controles.csv         Contrôles et DEME mobilisés
├── procedures.csv        Procédures (géré par l'application)
├── profils.csv           Profils élèves (multiplicateurs)
├── README.md             Ce document
├── MODE_EMPLOI.md        Guide d'installation et d'utilisation
├── .gitignore            Exclusions Git
└── backup/               Sauvegardes horodatées (non versionné)
```
