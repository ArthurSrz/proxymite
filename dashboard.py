"""
Tableau de bord — Effectifs personnels de l'Éducation Nationale
Design system: Datack (datack.fr) — noir / jaune néon / blanc
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Effectifs EN · Datack",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Design system Datack ────────────────────────────────────────────────────────
YELLOW  = "#C8FF00"
BLACK   = "#0D0D0D"
CARD_BG = "#1A1A1A"
WHITE   = "#FFFFFF"
GRAY    = "#888888"
BORDER  = "#2A2A2A"

st.markdown(f"""
<style>
  /* Base */
  .stApp {{ background-color: {BLACK}; color: {WHITE}; }}
  section[data-testid="stSidebar"] {{ background-color: {CARD_BG}; border-right: 1px solid {BORDER}; }}
  section[data-testid="stSidebar"] * {{ color: {WHITE} !important; }}

  /* Typography */
  h1, h2, h3, h4 {{ color: {WHITE} !important; font-weight: 800 !important; letter-spacing: -0.02em; }}

  /* Metric cards */
  [data-testid="stMetric"] {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 20px 24px !important;
  }}
  [data-testid="stMetricLabel"] {{ color: {GRAY} !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.1em; }}
  [data-testid="stMetricValue"] {{ color: {YELLOW} !important; font-size: 2rem !important; font-weight: 800 !important; }}
  [data-testid="stMetricDelta"] {{ color: {WHITE} !important; }}

  /* Tabs */
  [data-baseweb="tab-list"] {{ background: {CARD_BG}; border-radius: 12px; padding: 4px; gap: 4px; }}
  [data-baseweb="tab"] {{ color: {GRAY} !important; border-radius: 8px !important; font-weight: 600; }}
  [aria-selected="true"] {{ background: {YELLOW} !important; color: {BLACK} !important; }}

  /* Selectbox / multiselect */
  [data-baseweb="select"] > div {{ background: {CARD_BG} !important; border-color: {BORDER} !important; color: {WHITE} !important; border-radius: 10px !important; }}
  [data-baseweb="popover"] {{ background: {CARD_BG} !important; }}

  /* Slider */
  [data-testid="stSlider"] div[role="slider"] {{ background: {YELLOW}; }}

  /* Divider */
  hr {{ border-color: {BORDER} !important; }}

  /* Section card wrapper */
  .datack-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
  }}
  .datack-tag {{
    display: inline-block;
    background: {YELLOW};
    color: {BLACK};
    font-size: 0.7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    padding: 4px 12px;
    border-radius: 100px;
    margin-bottom: 8px;
  }}

  /* Scrollbar */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: {BLACK}; }}
  ::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color=WHITE,
    font_family="Inter, system-ui, sans-serif",
    margin=dict(l=16, r=16, t=40, b=16),
    colorway=[YELLOW, "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
    xaxis=dict(gridcolor=BORDER, tickcolor=GRAY, linecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, tickcolor=GRAY, linecolor=BORDER),
    legend=dict(bgcolor="rgba(0,0,0,0)", font_color=WHITE),
)

# ── Data ────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("data/effectifs_personnels_EN.csv", low_memory=False)
    df["has_etp"] = df["etp_enseignants"].notna()
    df["has_pct"] = df["pct_femmes"].notna()
    df["annee_de_la_rentree_scolaire"] = df["annee_de_la_rentree_scolaire"].fillna(2024).astype(int)
    return df

df = load_data()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:0 0 24px 0">
      <span style="font-size:1.8rem;font-weight:900;color:{YELLOW};letter-spacing:-0.04em;">DATACK</span>
      <span style="font-size:0.65rem;color:{GRAY};display:block;margin-top:2px;letter-spacing:0.15em;text-transform:uppercase;">× Éducation Nationale</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Filtres**")

    all_regions = sorted(df["libelle_region"].dropna().unique())
    sel_regions = st.multiselect("Région", all_regions, placeholder="Toutes les régions")

    all_types = sorted(df["type_etablissement"].dropna().unique())
    sel_types = st.multiselect("Type d'établissement", all_types, placeholder="Tous les types")

    sel_secteur = st.radio("Secteur", ["Tous", "Public", "Privé"], horizontal=True)

    st.divider()
    st.markdown(f"<span style='color:{GRAY};font-size:0.75rem'>Source : data.education.gouv.fr<br>Rentrée 2024</span>", unsafe_allow_html=True)

# ── Apply filters ────────────────────────────────────────────────────────────────
dff = df.copy()
if sel_regions:
    dff = dff[dff["libelle_region"].isin(sel_regions)]
if sel_types:
    dff = dff[dff["type_etablissement"].isin(sel_types)]
if sel_secteur != "Tous":
    dff = dff[dff["statut_public_prive"] == sel_secteur]

dff_etp = dff[dff["has_etp"]]
dff_pct = dff[dff["has_pct"]]

# ── Header ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding: 32px 0 24px 0">
  <div class="datack-tag">Tableau de bord · Rentrée 2024</div>
  <h1 style="font-size:2.6rem;margin:8px 0 4px 0;line-height:1.1">
    Effectifs personnels<br>
    <span style="color:{YELLOW}">de l'Éducation Nationale</span>
  </h1>
  <p style="color:{GRAY};font-size:0.95rem;margin:0">
    {len(dff):,} établissements · {len(dff_etp):,} avec données ETP · {len(dff_pct):,} avec profil complet
  </p>
</div>
""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric("Établissements", f"{len(dff):,}")
with k2:
    avg_etp = dff_etp["etp_enseignants"].mean()
    st.metric("ETP enseignants (moy.)", f"{avg_etp:.1f}" if not pd.isna(avg_etp) else "—")
with k3:
    pct_f = dff_pct["pct_femmes"].mean()
    st.metric("% Femmes enseignantes", f"{pct_f:.1f}%" if not pd.isna(pct_f) else "—")
with k4:
    pct_nt = dff_pct["pct_non_titulaires"].mean()
    st.metric("% Non-titulaires", f"{pct_nt:.1f}%" if not pd.isna(pct_nt) else "—")
with k5:
    pct_senior = dff_pct["pct_anciennete_8_ans_plus"].mean()
    st.metric("% Ancienneté 8+ ans", f"{pct_senior:.1f}%" if not pd.isna(pct_senior) else "—")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺 Géographie", "🏫 Types & Secteurs", "👩‍🏫 Genre & Corps", "⏳ Âge & Ancienneté", "📊 Vue régionale"
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — GÉOGRAPHIE
# ═══════════════════════════════════════════════════════════════
with tab1:
    col_map, col_reg = st.columns([3, 2])

    with col_map:
        st.markdown(f'<div class="datack-tag">Carte</div>', unsafe_allow_html=True)
        st.markdown("#### Localisation des établissements")

        df_geo = dff[dff["latitude"].notna() & dff["longitude"].notna()].copy()

        # sample for performance
        sample = df_geo.sample(min(8000, len(df_geo)), random_state=42) if len(df_geo) > 8000 else df_geo

        color_map = {"Public": YELLOW, "Privé": "#FF6B6B"}
        fig_map = px.scatter_mapbox(
            sample,
            lat="latitude", lon="longitude",
            color="statut_public_prive",
            color_discrete_map=color_map,
            hover_name="nom_etablissement",
            hover_data={"libelle_region": True, "type_etablissement": True,
                        "latitude": False, "longitude": False},
            zoom=4.5, center={"lat": 46.5, "lon": 2.5},
            opacity=0.6,
            size_max=6,
        )
        fig_map.update_layout(
            mapbox_style="carto-darkmatter",
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            height=480,
            legend_title_text="Secteur",
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_reg:
        st.markdown(f'<div class="datack-tag">Régions</div>', unsafe_allow_html=True)
        st.markdown("#### Établissements par région")

        reg_counts = (
            dff.groupby("libelle_region")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=True)
            .tail(15)
        )
        fig_reg = px.bar(
            reg_counts, x="count", y="libelle_region",
            orientation="h",
            color="count",
            color_continuous_scale=[[0, "#333"], [1, YELLOW]],
        )
        fig_reg.update_layout(**PLOTLY_LAYOUT, height=480, showlegend=False, coloraxis_showscale=False)
        fig_reg.update_traces(marker_line_width=0)
        st.plotly_chart(fig_reg, use_container_width=True)

    # Density heatmap
    st.markdown(f'<div class="datack-tag">Densité</div>', unsafe_allow_html=True)
    st.markdown("#### ETP moyen par département (établissements avec données)")

    dept_etp = (
        dff_etp.groupby(["libelle_departement", "code_departement"])
        .agg(nb=("etp_enseignants", "count"), avg_etp=("etp_enseignants", "mean"))
        .reset_index()
        .sort_values("avg_etp", ascending=False)
        .head(25)
    )
    fig_dept = px.bar(
        dept_etp, x="libelle_departement", y="avg_etp",
        color="avg_etp",
        color_continuous_scale=[[0, "#333"], [1, YELLOW]],
        labels={"avg_etp": "ETP moy.", "libelle_departement": "Département"},
    )
    fig_dept.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False, coloraxis_showscale=False)
    fig_dept.update_traces(marker_line_width=0)
    st.plotly_chart(fig_dept, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 2 — TYPES & SECTEURS
# ═══════════════════════════════════════════════════════════════
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f'<div class="datack-tag">Répartition</div>', unsafe_allow_html=True)
        st.markdown("#### Par type d'établissement")

        type_counts = dff["type_etablissement"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]

        fig_type = px.pie(
            type_counts, names="type", values="count",
            hole=0.55,
            color_discrete_sequence=[YELLOW, "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"],
        )
        fig_type.update_traces(textfont_color=WHITE, pull=[0.04] + [0] * (len(type_counts) - 1))
        fig_type.update_layout(
            **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
            height=360,
        )
        st.plotly_chart(fig_type, use_container_width=True)

    with col_b:
        st.markdown(f'<div class="datack-tag">Secteur</div>', unsafe_allow_html=True)
        st.markdown("#### Public vs Privé par type")

        cross = (
            dff.groupby(["type_etablissement", "statut_public_prive"])
            .size()
            .reset_index(name="count")
        )
        fig_cross = px.bar(
            cross, x="type_etablissement", y="count",
            color="statut_public_prive",
            barmode="group",
            color_discrete_map={"Public": YELLOW, "Privé": "#FF6B6B"},
            labels={"type_etablissement": "", "count": "Nb établissements", "statut_public_prive": "Secteur"},
        )
        fig_cross.update_layout(**PLOTLY_LAYOUT, height=360)
        fig_cross.update_traces(marker_line_width=0)
        st.plotly_chart(fig_cross, use_container_width=True)

    st.divider()

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown(f'<div class="datack-tag">ETP</div>', unsafe_allow_html=True)
        st.markdown("#### ETP enseignants moyen par type")

        etp_type = (
            dff_etp.groupby("type_etablissement")["etp_enseignants"]
            .agg(["mean", "median", "count"])
            .reset_index()
            .sort_values("mean", ascending=False)
        )
        fig_etp_t = go.Figure()
        fig_etp_t.add_trace(go.Bar(
            name="Moyenne",
            x=etp_type["type_etablissement"],
            y=etp_type["mean"].round(1),
            marker_color=YELLOW, marker_line_width=0,
        ))
        fig_etp_t.add_trace(go.Bar(
            name="Médiane",
            x=etp_type["type_etablissement"],
            y=etp_type["median"].round(1),
            marker_color="#4ECDC4", marker_line_width=0,
        ))
        fig_etp_t.update_layout(**PLOTLY_LAYOUT, height=320, barmode="group")
        st.plotly_chart(fig_etp_t, use_container_width=True)

    with col_d:
        st.markdown(f'<div class="datack-tag">Nature</div>', unsafe_allow_html=True)
        st.markdown("#### Top 10 natures d'établissement")

        nat = dff["libelle_nature"].value_counts().head(10).reset_index()
        nat.columns = ["nature", "count"]
        nat = nat.sort_values("count", ascending=True)

        fig_nat = px.bar(nat, x="count", y="nature", orientation="h",
                         color="count",
                         color_continuous_scale=[[0, "#333"], [1, YELLOW]])
        fig_nat.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False, coloraxis_showscale=False)
        fig_nat.update_traces(marker_line_width=0)
        st.plotly_chart(fig_nat, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 3 — GENRE & CORPS
# ═══════════════════════════════════════════════════════════════
with tab3:
    if len(dff_pct) == 0:
        st.info("Pas de données de profil pour la sélection actuelle (réservées aux lycées/collèges).")
    else:
        col_e, col_f = st.columns(2)

        with col_e:
            st.markdown(f'<div class="datack-tag">Genre</div>', unsafe_allow_html=True)
            st.markdown("#### Distribution % femmes enseignantes")

            fig_fem = px.histogram(
                dff_pct, x="pct_femmes", nbins=40,
                color_discrete_sequence=[YELLOW],
                labels={"pct_femmes": "% Femmes", "count": "Nb établissements"},
            )
            fig_fem.add_vline(
                x=dff_pct["pct_femmes"].mean(), line_dash="dash",
                line_color=WHITE, annotation_text=f"Moy. {dff_pct['pct_femmes'].mean():.1f}%",
                annotation_font_color=WHITE,
            )
            fig_fem.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
            fig_fem.update_traces(marker_line_width=0)
            st.plotly_chart(fig_fem, use_container_width=True)

        with col_f:
            st.markdown(f'<div class="datack-tag">Corps</div>', unsafe_allow_html=True)
            st.markdown("#### Composition moyenne du corps enseignant")

            corps_labels = ["Agrégés", "Certifiés/PEPs", "PLP", "Autres titulaires", "Non-titulaires"]
            corps_vals = [
                dff_pct["pct_agreges"].mean(),
                dff_pct["pct_certifies"].mean(),
                dff_etp["etp_plp"].mean() if len(dff_etp) else 0,
                dff_pct["pct_non_titulaires"].mean() * 0,
                dff_pct["pct_non_titulaires"].mean(),
            ]

            etp_cols_corps = ["etp_agreges", "etp_certifies", "etp_plp", "etp_autres_titulaires", "etp_non_titulaires"]
            corps_etp_vals = [dff_pct[c].mean() if c in dff_pct.columns else 0 for c in etp_cols_corps]
            corps_labels_full = ["Agrégés", "Certifiés/PEPs", "PLP", "Autres titulaires", "Non-titulaires"]

            fig_corps = px.pie(
                names=corps_labels_full, values=corps_etp_vals,
                hole=0.55,
                color_discrete_sequence=[YELLOW, "#4ECDC4", "#FF6B6B", "#45B7D1", "#96CEB4"],
            )
            fig_corps.update_traces(textfont_color=WHITE)
            fig_corps.update_layout(
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                height=320,
            )
            st.plotly_chart(fig_corps, use_container_width=True)

        st.divider()

        # Gender by region
        st.markdown(f'<div class="datack-tag">Régions</div>', unsafe_allow_html=True)
        st.markdown("#### % Femmes enseignantes par région")

        reg_genre = (
            dff_pct.groupby("libelle_region")["pct_femmes"]
            .mean().round(1)
            .reset_index()
            .sort_values("pct_femmes", ascending=False)
        )
        fig_rg = px.bar(
            reg_genre, x="libelle_region", y="pct_femmes",
            color="pct_femmes",
            color_continuous_scale=[[0, "#333"], [0.5, "#4ECDC4"], [1, YELLOW]],
            labels={"pct_femmes": "% Femmes", "libelle_region": ""},
        )
        fig_rg.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=False, coloraxis_showscale=False)
        fig_rg.update_traces(marker_line_width=0)
        st.plotly_chart(fig_rg, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 4 — ÂGE & ANCIENNETÉ
# ═══════════════════════════════════════════════════════════════
with tab4:
    if len(dff_etp) == 0:
        st.info("Pas de données ETP pour la sélection actuelle.")
    else:
        col_g, col_h = st.columns(2)

        with col_g:
            st.markdown(f'<div class="datack-tag">Âge</div>', unsafe_allow_html=True)
            st.markdown("#### Pyramide des âges (ETP moyen)")

            age_data = pd.DataFrame({
                "Tranche": ["< 35 ans", "35–50 ans", "50+ ans"],
                "ETP moyen": [
                    dff_etp["etp_moins_35_ans"].mean(),
                    dff_etp["etp_35_50_ans"].mean(),
                    dff_etp["etp_50_ans_plus"].mean(),
                ]
            }).dropna()

            fig_age = px.bar(
                age_data, y="Tranche", x="ETP moyen",
                orientation="h",
                color="Tranche",
                color_discrete_sequence=[YELLOW, "#4ECDC4", "#FF6B6B"],
            )
            fig_age.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
            fig_age.update_traces(marker_line_width=0)
            st.plotly_chart(fig_age, use_container_width=True)

        with col_h:
            st.markdown(f'<div class="datack-tag">Ancienneté</div>', unsafe_allow_html=True)
            st.markdown("#### Ancienneté dans l'établissement (ETP moyen)")

            anc_data = pd.DataFrame({
                "Tranche": ["< 2 ans", "2–5 ans", "5–8 ans", "8+ ans"],
                "ETP moyen": [
                    dff_etp["etp_anciennete_moins_2_ans"].mean(),
                    dff_etp["etp_anciennete_2_5_ans"].mean(),
                    dff_etp["etp_anciennete_5_8_ans"].mean(),
                    dff_etp["etp_anciennete_8_ans_plus"].mean(),
                ]
            }).dropna()

            fig_anc = px.funnel(
                anc_data, y="Tranche", x="ETP moyen",
                color_discrete_sequence=[YELLOW],
            )
            fig_anc.update_layout(
                **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                height=280, showlegend=False,
            )
            st.plotly_chart(fig_anc, use_container_width=True)

        st.divider()

        if len(dff_pct) > 0:
            col_i, col_j = st.columns(2)

            with col_i:
                st.markdown(f'<div class="datack-tag">Profil âge</div>', unsafe_allow_html=True)
                st.markdown("#### Distribution % par tranche d'âge")

                age_pct = pd.DataFrame({
                    "Tranche": ["< 35 ans", "35–50 ans", "50+ ans"],
                    "Pct moyen": [
                        dff_pct["pct_moins_35_ans"].mean(),
                        dff_pct["pct_35_50_ans"].mean(),
                        dff_pct["pct_plus_50_ans"].mean(),
                    ]
                })

                fig_ap = px.pie(
                    age_pct, names="Tranche", values="Pct moyen", hole=0.5,
                    color_discrete_sequence=[YELLOW, "#4ECDC4", "#FF6B6B"],
                )
                fig_ap.update_traces(textfont_color=WHITE)
                fig_ap.update_layout(
                    **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                    height=280,
                )
                st.plotly_chart(fig_ap, use_container_width=True)

            with col_j:
                st.markdown(f'<div class="datack-tag">Profil ancienneté</div>', unsafe_allow_html=True)
                st.markdown("#### Distribution % par ancienneté")

                anc_pct = pd.DataFrame({
                    "Tranche": ["< 2 ans", "2–5 ans", "5–8 ans", "8+ ans"],
                    "Pct moyen": [
                        dff_pct["pct_anciennete_moins_2_ans"].mean(),
                        dff_pct["pct_anciennete_2_5_ans"].mean(),
                        dff_pct["pct_anciennete_5_8_ans"].mean(),
                        dff_pct["pct_anciennete_8_ans_plus"].mean(),
                    ]
                })

                fig_ancp = px.pie(
                    anc_pct, names="Tranche", values="Pct moyen", hole=0.5,
                    color_discrete_sequence=[YELLOW, "#4ECDC4", "#FF6B6B", "#45B7D1"],
                )
                fig_ancp.update_traces(textfont_color=WHITE)
                fig_ancp.update_layout(
                    **{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "yaxis")},
                    height=280,
                )
                st.plotly_chart(fig_ancp, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 5 — VUE RÉGIONALE
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown(f'<div class="datack-tag">Comparaison</div>', unsafe_allow_html=True)
    st.markdown("#### Tableau de bord régional comparatif")

    reg_summary = (
        dff.groupby("libelle_region").agg(
            nb_etablissements=("identifiant_de_l_etablissement", "count"),
            nb_avec_etp=("has_etp", "sum"),
            avg_etp=("etp_enseignants", "mean"),
            avg_pct_femmes=("pct_femmes", "mean"),
            avg_pct_non_tit=("pct_non_titulaires", "mean"),
            avg_pct_moins35=("pct_moins_35_ans", "mean"),
            avg_pct_50plus=("pct_plus_50_ans", "mean"),
        )
        .round(1)
        .reset_index()
        .rename(columns={
            "libelle_region": "Région",
            "nb_etablissements": "Établissements",
            "nb_avec_etp": "Avec ETP",
            "avg_etp": "ETP moy.",
            "avg_pct_femmes": "% Femmes",
            "avg_pct_non_tit": "% Non-tit.",
            "avg_pct_moins35": "% <35 ans",
            "avg_pct_50plus": "% 50+ ans",
        })
        .sort_values("Établissements", ascending=False)
    )

    st.dataframe(
        reg_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "% Femmes": st.column_config.ProgressColumn("% Femmes", min_value=0, max_value=100, format="%.1f%%"),
            "% Non-tit.": st.column_config.ProgressColumn("% Non-tit.", min_value=0, max_value=30, format="%.1f%%"),
        }
    )

    st.divider()

    col_k, col_l = st.columns(2)

    with col_k:
        st.markdown("#### ETP moyen vs % Femmes (par région)")

        scatter_reg = (
            dff_etp.groupby("libelle_region").agg(
                avg_etp=("etp_enseignants", "mean"),
                avg_pct_femmes=("pct_femmes", "mean"),
                count=("identifiant_de_l_etablissement", "count"),
            ).reset_index()
        )

        fig_scatter = px.scatter(
            scatter_reg,
            x="avg_etp", y="avg_pct_femmes",
            size="count", text="libelle_region",
            color="count",
            color_continuous_scale=[[0, "#333"], [1, YELLOW]],
            labels={"avg_etp": "ETP moyen", "avg_pct_femmes": "% Femmes", "count": "Nb étab."},
        )
        fig_scatter.update_traces(textposition="top center", textfont_color=WHITE, textfont_size=10)
        fig_scatter.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_l:
        st.markdown("#### % Non-titulaires par région")

        nt_reg = (
            dff_pct.groupby("libelle_region")["pct_non_titulaires"]
            .mean().round(1).reset_index()
            .sort_values("pct_non_titulaires", ascending=True)
        )

        fig_nt = px.bar(
            nt_reg, x="pct_non_titulaires", y="libelle_region",
            orientation="h",
            color="pct_non_titulaires",
            color_continuous_scale=[[0, "#333"], [0.5, "#4ECDC4"], [1, "#FF6B6B"]],
            labels={"pct_non_titulaires": "% Non-tit.", "libelle_region": ""},
        )
        fig_nt.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False, coloraxis_showscale=False)
        fig_nt.update_traces(marker_line_width=0)
        st.plotly_chart(fig_nt, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center;padding:40px 0 24px;color:{GRAY};font-size:0.78rem;border-top:1px solid {BORDER};margin-top:32px">
  Données : Ministère de l'Éducation Nationale — data.education.gouv.fr · Rentrée scolaire 2024<br>
  <span style="color:{YELLOW};font-weight:800">DATACK</span> × Proxymite · {len(df):,} établissements analysés
</div>
""", unsafe_allow_html=True)
