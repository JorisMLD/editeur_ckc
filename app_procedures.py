# ============================================================
# Éditeur de procédures — v2
# ------------------------------------------------------------
# Nouveautés :
#   - Chargement inframaths.csv (IMs avec coûts m/v/p)
#   - Calcul de coût nominal par procédure (et par étape)
#   - Calcul de coût ajusté au profil élève
#   - Édition et suppression de procédures existantes
#   - Export LaTeX avec colonnes de coût
#   - Génération automatique d'un template profils.csv
# ============================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import shutil
import unicodedata

st.set_page_config(page_title="Éditeur de procédures", layout="wide")

# ============================================================
# CONSTANTES
# ============================================================
DIM_LABELS = {"m": "Manipulation", "v": "Perception", "p": "Planification"}


# ============================================================
# FONCTIONS UTILITAIRES — I/O
# ============================================================

def ensure_backup_dir():
    Path("backup").mkdir(exist_ok=True)

def backup_file(path: str) -> Path:
    ensure_backup_dir()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = Path("backup") / f"{Path(path).stem}_{ts}.csv"
    shutil.copy2(path, dst)
    return dst

def read_csv_auto(path: str) -> pd.DataFrame:
    """Lit un CSV avec détection automatique de l'encodage et du séparateur."""
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(path, encoding=enc, sep=None, engine="python")
        except Exception:
            continue
    raise ValueError(f"Impossible de lire {path}")

def normalize_col(c: str) -> str:
    """Nettoie un nom de colonne : sans accents, minuscule, underscores."""
    clean = (unicodedata.normalize("NFKD", str(c))
             .encode("ascii", errors="ignore").decode())
    return clean.strip().lower().replace(" ", "_").replace("-", "_")


# ============================================================
# CHARGEMENT — INFRAMATHS
# ============================================================

def load_inframaths(path: str) -> pd.DataFrame:
    """
    Charge inframaths.csv.
    Retourne un DataFrame indexé par le Code IM (I1..i11)
    avec colonnes m (Manipulation), v (Perception), p (Planification).
    """
    df = read_csv_auto(path)
    col_map = {}
    for c in df.columns:
        nc = normalize_col(c)
        if "code" in nc:
            col_map[c] = "code"
        elif "manipulation" in nc:
            col_map[c] = "m"
        elif "perception" in nc:
            col_map[c] = "v"
        elif "planif" in nc:
            col_map[c] = "p"
        elif "action" in nc or "observable" in nc:
            col_map[c] = "label"
        else:
            col_map[c] = nc
    df = df.rename(columns=col_map)
    df = df.set_index("code")
    df.index = df.index.str.upper()   # insensible à la casse : I1, i9 → I1, I9
    for dim in ["m", "v", "p"]:
        df[dim] = pd.to_numeric(df[dim], errors="coerce").fillna(0)
    return df


# ============================================================
# CHARGEMENT — OPÉRATEURS & CONTRÔLES
# ============================================================

def _extract_im_code(col_name: str) -> str:
    """Extrait le code IM depuis 'I1 Clic simple' → 'I1', insensible à la casse."""
    return col_name.split()[0].upper()

def _get_im_col_map(df: pd.DataFrame, im_codes: list) -> dict:
    """Retourne {im_code: nom_colonne_df} pour les colonnes IM présentes."""
    result = {}
    for col in df.columns:
        code = _extract_im_code(col)
        if code in im_codes:
            result[code] = col
    return result

def load_operateurs(path: str, im_codes: list) -> pd.DataFrame:
    """
    Charge operateurs.csv.
    Retourne DataFrame indexé par clef avec :
    - nom, finalite, scheme, detail
    - im_{code} pour chaque IM (nombre de mobilisations)
    """
    df = read_csv_auto(path)
    df.columns = [c.strip() for c in df.columns]

    clef_col = next((c for c in df.columns if c.lower().strip() == "clef"), None)
    nom_col  = next((c for c in df.columns if c.lower().strip() == "nom"),  None)

    result = df[[clef_col, nom_col]].copy()
    result.columns = ["clef", "nom"]
    result = result.dropna(subset=["clef"])  # supprimer lignes vides

    for alias, candidates in [
        ("finalite", ["Finalité immédiate", "Finalite immediate", "finalite_immediate"]),
        ("scheme",   ["Schème", "Scheme", "schème"]),
        ("detail",   ["détail", "detail", "Détail"]),
    ]:
        col = next((c for c in candidates if c in df.columns), None)
        if col:
            result[alias] = df[col].values

    im_col_map = _get_im_col_map(df, im_codes)
    for im_code, col in im_col_map.items():
        result[f"im_{im_code}"] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return result.set_index("clef")

def load_controles(path: str, im_codes: list) -> pd.DataFrame:
    """
    Charge controles.csv.
    Retourne DataFrame indexé par Clef avec :
    - categorie (fill-forward depuis la colonne groupement)
    - nom, assertion1, assertion2
    - im_{code} pour chaque IM
    """
    df = read_csv_auto(path)
    df.columns = [c.strip() for c in df.columns]

    # Colonne catégorie : colonne "Unnamed" qui contient des valeurs en majuscules
    cat_col = None
    for c in df.columns:
        if "unnamed" in c.lower():
            vals = df[c].dropna().astype(str)
            if len(vals) > 0 and vals.str.isupper().any():
                cat_col = c
                break

    clef_col = next((c for c in df.columns if c.lower().strip() in ["clef", "clé"]), None)
    nom_col  = next((c for c in df.columns if c.lower().strip() == "nom"), None)

    result = df[[clef_col, nom_col]].copy()
    result.columns = ["clef", "nom"]
    result = result.dropna(subset=["clef"])  # supprimer lignes vides

    if cat_col:
        result["categorie"] = df[cat_col].ffill().values
    else:
        result["categorie"] = ""

    for alias, candidates in [
        ("assertion1", ["Assertion 1", "Assertion1", "assertion_1"]),
        ("assertion2", ["Assertion 2", "Assertion2", "assertion_2"]),
    ]:
        col = next((c for c in candidates if c in df.columns), None)
        if col:
            result[alias] = df[col].values

    im_col_map = _get_im_col_map(df, im_codes)
    for im_code, col in im_col_map.items():
        result[f"im_{im_code}"] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return result.set_index("clef")


# ============================================================
# CHARGEMENT — PROCÉDURES
# ============================================================

def load_procedures_dict(csv_path: str, list_sep: str = "|") -> dict:
    if not Path(csv_path).exists():
        return {}
    df = read_csv_auto(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df["deroulement"] = (df["deroulement"].fillna("").astype(str)
                         .apply(lambda x: [t.strip() for t in x.split(list_sep) if t.strip()]))
    return df.set_index("clef")[["nom", "description", "deroulement"]].to_dict(orient="index")

def save_procedures_csv(d: dict, csv_path: str, list_sep: str = "|"):
    rows = [{"clef": k,
             "nom": v.get("nom", ""),
             "description": v.get("description", ""),
             "deroulement": list_sep.join(v.get("deroulement", []))}
            for k, v in d.items()]
    pd.DataFrame(rows, columns=["clef", "nom", "description", "deroulement"]
                 ).to_csv(csv_path, index=False, encoding="utf-8")


# ============================================================
# CHARGEMENT / GÉNÉRATION — PROFILS ÉLÈVES
# ============================================================

def create_profil_template(im_df: pd.DataFrame, path: str = "profils.csv"):
    """
    Génère un profil neutre en format large (une ligne par profil).
    Colonnes : clef_profil, nom_profil, mult_m, mult_v, mult_p, mult_I1...mult_I11
    """
    im_codes = im_df.index.tolist()
    row = {"clef_profil": "profil_neutre", "nom_profil": "Profil neutre (référence)",
           "mult_m": 1.0, "mult_v": 1.0, "mult_p": 1.0}
    for im in im_codes:
        row[f"mult_{im}"] = 1.0
    cols = ["clef_profil", "nom_profil", "mult_m", "mult_v", "mult_p"] + [f"mult_{im}" for im in im_codes]
    pd.DataFrame([row], columns=cols).to_csv(path, index=False, encoding="utf-8")
    return path

def load_profils(path: str) -> pd.DataFrame:
    """
    Charge profils.csv (format large).
    Index = clef_profil. Colonnes : nom_profil, mult_m, mult_v, mult_p, mult_I1...
    """
    df = read_csv_auto(path)
    df.columns = [c.strip() for c in df.columns]
    # Normaliser les codes IM en majuscules dans les noms de colonnes
    df.columns = [c.upper() if c.startswith("mult_I") or c.startswith("mult_i") else c for c in df.columns]
    return df.set_index("clef_profil")


# ============================================================
# CALCUL DES COÛTS
# ============================================================

def _im_cols_in(row: pd.Series, im_df: pd.DataFrame) -> list:
    """Retourne les codes IM ayant une mobilisation > 0 dans une ligne."""
    return [
        code for code in im_df.index
        if f"im_{code}" in row.index and float(row[f"im_{code}"]) > 0
    ]

def calc_nominal_cost(
    deroulement: list,
    ops_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    im_df: pd.DataFrame,
) -> dict:
    """
    Coût nominal (m, v, p) d'une procédure.
    Pour chaque étape du déroulement : somme des mobilisations × coût IM.
    """
    total = {"m": 0.0, "v": 0.0, "p": 0.0}
    for step in deroulement:
        row = None
        if ops_df is not None and step in ops_df.index:
            row = ops_df.loc[step]
        elif ctrl_df is not None and step in ctrl_df.index:
            row = ctrl_df.loc[step]
        if row is None:
            continue
        for im_code in _im_cols_in(row, im_df):
            count = float(row[f"im_{im_code}"])
            for dim in ["m", "v", "p"]:
                total[dim] += count * float(im_df.loc[im_code, dim])
    return total

def calc_profil_cost(
    deroulement: list,
    ops_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    im_df: pd.DataFrame,
    profil_row: pd.Series,
) -> dict:
    """
    Coût ajusté au profil élève.
    Formule :
      coût_dim = mult_dim × Σ_étapes Σ_IM ( count × coût_nominal_IM_dim × mult_IM )
    """
    total = {"m": 0.0, "v": 0.0, "p": 0.0}
    for step in deroulement:
        row = None
        if ops_df is not None and step in ops_df.index:
            row = ops_df.loc[step]
        elif ctrl_df is not None and step in ctrl_df.index:
            row = ctrl_df.loc[step]
        if row is None:
            continue
        for im_code in _im_cols_in(row, im_df):
            count    = float(row[f"im_{im_code}"])
            mult_im  = float(profil_row.get(f"mult_{im_code}", 1.0))
            for dim in ["m", "v", "p"]:
                nominal = count * float(im_df.loc[im_code, dim])
                total[dim] += nominal * mult_im
    # Multiplicateurs globaux par dimension
    for dim in ["m", "v", "p"]:
        total[dim] *= float(profil_row.get(f"mult_{dim}", 1.0))
    return total


# ============================================================
# INTERFACE — BOUTONS EN GRILLE
# ============================================================

def button_grid(labels: dict, prefix: str, ncols: int):
    """Grille de boutons : chaque clic ajoute la clef au déroulement courant."""
    cols = st.columns(ncols)
    for i, (code, label) in enumerate(labels.items()):
        with cols[i % ncols]:
            if st.button(str(label), key=f"{prefix}_{code}"):
                st.session_state.current_proc["deroulement"].append(code)
                st.rerun()


# ============================================================
# EXPORT LATEX
# ============================================================

def escape_latex(text) -> str:
    if not isinstance(text, str):
        return ""
    for src, dst in [("&","\\&"),("_","\\_"),("%","\\%"),
                     ("#","\\#"),("{","\\{"),("}","\\}")]:
        text = text.replace(src, dst)
    return text

def export_latex(
    ops_df: pd.DataFrame,
    ctrl_df: pd.DataFrame,
    im_df: pd.DataFrame,
    dict_procs: dict,
    profil_row: pd.Series = None,
) -> Path:
    tex = []

    # Préambule
    tex += [
        "% ---- Préambule LaTeX requis ----",
        "\\newcommand{\\rref}[1]{$r_{\\ref{#1}}$}",
        "\\newcommand{\\cref}[1]{$\\sigma_{\\ref{#1}}$}",
        "\\newcommand{\\pref}[1]{$\\rho_{\\ref{#1}}$}",
        "",
    ]

    # --- Tableau IMs ---
    tex += [
        "\\section*{Infra-maths}",
        "\\begin{longtable}{|c|p{5cm}|c|c|c|}",
        "\\hline",
        "Code & Action observable & $c_M$ & $c_V$ & $c_P$ \\\\ \\hline",
    ]
    for code, row in im_df.iterrows():
        label = escape_latex(str(row.get("label", code)))
        tex.append(f"{code} & {label} & {row['m']:.0f} & {row['v']:.0f} & {row['p']:.0f} \\\\ \\hline")
    tex.append("\\end{longtable}\n")

    # --- Tableau opérateurs ---
    tex += [
        "\\section*{Opérateurs}",
        "\\begin{longtable}{|c|p{3cm}|p{4cm}|p{4cm}|c|c|c|}",
        "\\hline",
        "$r_i$ & Nom & Finalité & Schème & $c_M$ & $c_V$ & $c_P$ \\\\ \\hline",
    ]
    for i, (k, row) in enumerate(ops_df.iterrows(), 1):
        cost = calc_nominal_cost([k], ops_df, ctrl_df, im_df)
        nom = escape_latex(str(row.get("nom", "")))
        fin = escape_latex(str(row.get("finalite", "")))
        sch = escape_latex(str(row.get("scheme", "")))
        tex.append(
            f"$r_{{{i}}}$\\label{{{k}}} & {nom} & {fin} & {sch}"
            f" & {cost['m']:.1f} & {cost['v']:.1f} & {cost['p']:.1f} \\\\ \\hline"
        )
    tex.append("\\end{longtable}\n")

    # --- Tableau contrôles ---
    tex += [
        "\\section*{Contrôles}",
        "\\begin{longtable}{|c|p{3cm}|p{4cm}|p{4cm}|c|c|c|}",
        "\\hline",
        "$\\sigma_j$ & Nom & Assertion 1 & Assertion 2 & $c_M$ & $c_V$ & $c_P$ \\\\ \\hline",
    ]
    for j, (k, row) in enumerate(ctrl_df.iterrows(), 1):
        cost = calc_nominal_cost([k], ops_df, ctrl_df, im_df)
        nom = escape_latex(str(row.get("nom", "")))
        a1  = escape_latex(str(row.get("assertion1", "")))
        a2  = escape_latex(str(row.get("assertion2", "")))
        tex.append(
            f"$\\sigma_{{{j}}}$\\label{{{k}}} & {nom} & {a1} & {a2}"
            f" & {cost['m']:.1f} & {cost['v']:.1f} & {cost['p']:.1f} \\\\ \\hline"
        )
    tex.append("\\end{longtable}\n")

    # --- Tableau procédures ---
    with_profil = profil_row is not None
    extra_cols  = "|c|c|c" if with_profil else ""
    extra_head  = " & $c_M^p$ & $c_V^p$ & $c_P^p$" if with_profil else ""
    tex += [
        "\\section*{Procédures}",
        f"\\begin{{longtable}}{{|c|p{{3cm}}|p{{4cm}}|p{{5cm}}|c|c|c{extra_cols}|}}",
        "\\hline",
        f"$\\rho_k$ & Nom & Description & Déroulement & $c_M$ & $c_V$ & $c_P${extra_head} \\\\ \\hline",
    ]
    ops_keys  = set(ops_df.index)
    ctrl_keys = set(ctrl_df.index)
    for idx, (k, v) in enumerate(dict_procs.items(), 1):
        der  = v.get("deroulement", [])
        nom  = escape_latex(v.get("nom", ""))
        desc = escape_latex(v.get("description", ""))
        der_str = " $\\to$ ".join([
            f"\\rref{{{c}}}" if c in ops_keys else
            f"\\cref{{{c}}}" if c in ctrl_keys else
            f"\\pref{{{c}}}"
            for c in der
        ])
        cost = calc_nominal_cost(der, ops_df, ctrl_df, im_df)
        line = (
            f"$\\rho_{{{idx}}}$\\label{{{k}}} & {nom} & {desc} & {der_str}"
            f" & {cost['m']:.1f} & {cost['v']:.1f} & {cost['p']:.1f}"
        )
        if with_profil:
            pc = calc_profil_cost(der, ops_df, ctrl_df, im_df, profil_row)
            line += f" & {pc['m']:.1f} & {pc['v']:.1f} & {pc['p']:.1f}"
        tex.append(line + " \\\\ \\hline")
    tex.append("\\end{longtable}\n")

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(f"export_latex_{ts}.tex")
    out.write_text("\n".join(tex), encoding="utf-8")
    return out


# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
div.stButton > button { font-size: 0.9rem; padding: 0.25rem 0.5rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE — INITIALISATION
# ============================================================
_defaults = {
    "dict_procedures": {},
    "operateurs":      None,
    "controles":       None,
    "inframaths":      None,
    "profils":         None,
    "profil_actif":    "Nominal",
    "ops_cols":        5,
    "sig_cols":        5,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ============================================================
# BARRE LATÉRALE
# ============================================================
st.sidebar.header("Fichiers de données")

ops_path  = st.sidebar.text_input("Opérateurs CSV",    value="operateurs.csv")
sig_path  = st.sidebar.text_input("Contrôles CSV",     value="controles.csv")
im_path   = st.sidebar.text_input("Inframaths CSV",    value="inframaths.csv")
proc_path = st.sidebar.text_input("Procédures CSV",    value="procedures.csv")
prof_path = st.sidebar.text_input("Profils élèves CSV",value="profils.csv")
list_sep  = st.sidebar.text_input("Séparateur déroulement", value="|", max_chars=1)

display_mode = st.sidebar.radio(
    "Afficher le déroulement avec :",
    ["Clefs", "Noms"], horizontal=True
)

# --- Boutons chargement / fin ---
col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    load_clicked = st.button("⬇️ Charger", type="primary", use_container_width=True)
with col_sb2:
    if st.button("🛑 Finir", use_container_width=True):
        st.session_state.pop("current_proc", None)
        st.sidebar.info("Édition terminée.")

if load_clicked:
    try:
        if Path(proc_path).exists():
            backup = backup_file(proc_path)
            st.sidebar.info(f"Sauvegarde : {backup}")
        im_df = load_inframaths(im_path)
        st.session_state.inframaths  = im_df
        st.session_state.operateurs  = load_operateurs(ops_path, im_df.index.tolist())
        st.session_state.controles   = load_controles(sig_path,  im_df.index.tolist())
        st.session_state.dict_procedures = load_procedures_dict(proc_path, list_sep=list_sep)
        if Path(prof_path).exists():
            st.session_state.profils = load_profils(prof_path)
        else:
            create_profil_template(im_df, prof_path)
            st.sidebar.info(f"Template profils créé : {prof_path}")
        st.success("Données chargées ✅")
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")

# --- Sélecteur de profil ---
st.sidebar.divider()
st.sidebar.subheader("Profil élève")
if st.session_state.profils is not None:
    profil_options = ["Nominal"] + st.session_state.profils.index.tolist()
    st.session_state.profil_actif = st.sidebar.selectbox("Profil actif", profil_options)
else:
    st.sidebar.caption("Aucun profil chargé — coûts nominaux uniquement.")



# --- Affichage des boutons ---
st.sidebar.divider()
st.sidebar.subheader("Affichage grilles")
st.session_state.ops_cols = st.sidebar.slider("Colonnes opérateurs", 2, 10, st.session_state.ops_cols)
st.session_state.sig_cols = st.sidebar.slider("Colonnes contrôles",  2, 10, st.session_state.sig_cols)

# --- Export LaTeX ---
st.sidebar.divider()
if st.sidebar.button("📤 Exporter en LaTeX", type="secondary", use_container_width=True):
    ops  = st.session_state.operateurs
    ctrl = st.session_state.controles
    im   = st.session_state.inframaths
    if ops is not None and ctrl is not None and im is not None and st.session_state.dict_procedures:
        profil_row = None
        if st.session_state.profil_actif != "Nominal" and st.session_state.profils is not None:
            profil_row = st.session_state.profils.loc[st.session_state.profil_actif]
        out_file = export_latex(ops, ctrl, im, st.session_state.dict_procedures, profil_row)
        st.sidebar.success(f"Export créé : {out_file}")
    else:
        st.sidebar.warning("Charger les données avant d'exporter.")


# ============================================================
# RACCOURCIS — données chargées
# ============================================================
ops    = st.session_state.operateurs
ctrl   = st.session_state.controles
im_df  = st.session_state.inframaths
profs  = st.session_state.profils

ops_labels = ops["nom"].to_dict()   if isinstance(ops,  pd.DataFrame) else {}
sig_labels = ctrl["nom"].to_dict()  if isinstance(ctrl, pd.DataFrame) else {}
labels_all = {**ops_labels, **sig_labels}

profil_row = None
if profs is not None and st.session_state.profil_actif != "Nominal":
    profil_row = profs.loc[st.session_state.profil_actif]


# ============================================================
# INTERFACE PRINCIPALE
# ============================================================
st.title("Éditeur de procédures")

# ---- Tableau des procédures existantes ----
st.subheader("Procédures existantes")

if st.session_state.dict_procedures and ops is not None and ctrl is not None and im_df is not None:
    rows = []
    for k, v in st.session_state.dict_procedures.items():
        der      = v.get("deroulement", [])
        der_disp = [labels_all.get(c, c) for c in der] if display_mode == "Noms" else der
        cost     = calc_nominal_cost(der, ops, ctrl, im_df)
        row = {
            "clef":        k,
            "nom":         v["nom"],
            "description": v["description"],
            "déroulement": " → ".join(der_disp),
            "Coût M":      round(cost["m"], 1),
            "Coût V":      round(cost["v"], 1),
            "Coût P":      round(cost["p"], 1),
            "Total":       round(sum(cost.values()), 1),
        }
        if profil_row is not None:
            pc = calc_profil_cost(der, ops, ctrl, im_df, profil_row)
            row["M (profil)"] = round(pc["m"], 1)
            row["V (profil)"] = round(pc["v"], 1)
            row["P (profil)"] = round(pc["p"], 1)
            row["Total (profil)"] = round(sum(pc.values()), 1)
        rows.append(row)

    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=300)

    # Édition / suppression
    st.markdown("**Modifier ou supprimer une procédure existante**")
    proc_keys = list(st.session_state.dict_procedures.keys())
    edit_key  = st.selectbox("Sélectionner une procédure", proc_keys, key="edit_select")
    col_edit, col_del = st.columns(2)
    with col_edit:
        if st.button("✏️ Éditer cette procédure"):
            existing = st.session_state.dict_procedures[edit_key]
            st.session_state.current_proc = {
                "clef":        edit_key,
                "nom":         existing["nom"],
                "description": existing["description"],
                "deroulement": existing["deroulement"].copy(),
                "_editing":    True,
            }
            st.rerun()
    with col_del:
        if st.button("🗑️ Supprimer cette procédure"):
            del st.session_state.dict_procedures[edit_key]
            save_procedures_csv(st.session_state.dict_procedures, proc_path, list_sep=list_sep)
            st.success(f"Procédure '{edit_key}' supprimée.")
            st.rerun()

elif not st.session_state.dict_procedures:
    st.info("Aucune procédure chargée. Utilisez le panneau latéral pour charger les données.")

st.divider()

# ---- Formulaire nouvelle / édition de procédure ----
is_editing = "current_proc" in st.session_state and st.session_state.current_proc.get("_editing", False)
st.subheader("Éditer une procédure" if is_editing else "Nouvelle procédure")

cur_defaults = st.session_state.get("current_proc", {})
with st.form("form_new_proc", clear_on_submit=False):
    colA, colB = st.columns([1, 1])
    with colA:
        new_key  = st.text_input("Clé",  value=cur_defaults.get("clef",  ""), key="form_clef")
        new_name = st.text_input("Nom",  value=cur_defaults.get("nom",   ""), key="form_nom")
    with colB:
        new_desc = st.text_area("Description",
                                value=cur_defaults.get("description", ""),
                                key="form_desc", height=80)
    go_select = st.form_submit_button("Commencer la sélection", type="secondary")

if go_select and new_key and new_name:
    existing_der = cur_defaults.get("deroulement", [])
    st.session_state.current_proc = {
        "clef":        new_key.strip(),
        "nom":         new_name.strip(),
        "description": new_desc.strip(),
        "deroulement": existing_der,
        "_editing":    is_editing,
    }
    st.rerun()

# ---- Zone de construction du déroulement ----
if "current_proc" in st.session_state:
    cur = st.session_state.current_proc
    der_disp = (
        [labels_all.get(c, c) for c in cur["deroulement"]]
        if display_mode == "Noms" else cur["deroulement"]
    )

    mode_label = "Édition" if cur.get("_editing") else "Construction"
    st.info(f"**{mode_label}** — procédure `{cur['clef']}`")
    st.markdown(f"**Nom :** {cur['nom']}  \n**Description :** {cur['description']}")
    st.write("**Déroulement actuel :**", " → ".join(der_disp) or "—")

    # Métriques de coût en temps réel
    if ops is not None and ctrl is not None and im_df is not None and cur["deroulement"]:
        cost = calc_nominal_cost(cur["deroulement"], ops, ctrl, im_df)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Manipulation",  f"{cost['m']:.1f}")
        mc2.metric("Perception",    f"{cost['v']:.1f}")
        mc3.metric("Planification", f"{cost['p']:.1f}")
        mc4.metric("Total",         f"{sum(cost.values()):.1f}")
        if profil_row is not None:
            pc = calc_profil_cost(cur["deroulement"], ops, ctrl, im_df, profil_row)
            st.caption(
                f"📊 Coût profil **{st.session_state.profil_actif}** — "
                f"M : {pc['m']:.1f} | V : {pc['v']:.1f} | P : {pc['p']:.1f} | "
                f"Total : {sum(pc.values()):.1f}"
            )

    # Grilles de boutons
    cL, cR = st.columns(2)
    with cL:
        st.markdown("### Opérateurs")
        if ops_labels:
            button_grid(ops_labels, "op", st.session_state.ops_cols)
        else:
            st.caption("Aucun opérateur chargé.")
    with cR:
        st.markdown("### Contrôles")
        if sig_labels:
            button_grid(sig_labels, "sig", st.session_state.sig_cols)
        else:
            st.caption("Aucun contrôle chargé.")

    # Bouton corriger
    c_corr, _, _ = st.columns([1, 3, 1])
    with c_corr:
        if st.button("↩️ Retirer le dernier élément"):
            if cur["deroulement"]:
                cur["deroulement"].pop()
                st.rerun()

    # Bouton enregistrer
    st.write("")
    _, c2, _ = st.columns([1, 1, 1])
    with c2:
        if st.button("✅ Enregistrer la procédure", type="primary"):
            st.session_state.dict_procedures[cur["clef"]] = {
                "nom":         cur["nom"],
                "description": cur["description"],
                "deroulement": cur["deroulement"].copy(),
            }
            save_procedures_csv(st.session_state.dict_procedures, proc_path, list_sep=list_sep)
            st.session_state.pop("current_proc", None)
            st.success("Procédure enregistrée et CSV mis à jour ✅")
            st.rerun()
