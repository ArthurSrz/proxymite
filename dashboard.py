"""
Effectifs enseignants — Éducation Nationale · Rentrée 2024
Design system : Datack (datack.fr) — noir / jaune néon / blanc
"""

import base64
import hashlib
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ── Design tokens ───────────────────────────────────────────────────────────────
C = {
    "yellow": "#C8FF00",
    "black":  "#0D0D0D",
    "card":   "#1A1A1A",
    "white":  "#FFFFFF",
    "gray":   "#888888",
    "border": "#2A2A2A",
    "teal":   "#4ECDC4",
    "red":    "#FF6B6B",
}

# ── Logo ────────────────────────────────────────────────────────────────────────
_logo_path = Path("media/logo-datack.png")
_logo_b64  = base64.b64encode(_logo_path.read_bytes()).decode() if _logo_path.exists() else None

def logo_img(height: int = 48, margin: str = "0 auto") -> str:
    if _logo_b64:
        return f'<img src="data:image/png;base64,{_logo_b64}" style="height:{height}px;display:block;margin:{margin}">'
    return f'<span style="font-size:1.8rem;font-weight:900;color:{C["yellow"]}">DATACK</span>'

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Effectifs EN · Datack",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth ─────────────────────────────────────────────────────────────────────────
def _check_password(candidate: str) -> bool:
    correct = st.secrets.get("password", "")
    h = lambda s: hashlib.sha256(s.encode()).hexdigest()
    return h(candidate) == h(correct)

def _login_wall() -> None:
    st.markdown(f"""<style>
      html, body, .stApp {{ background-color:{C["black"]} !important; }}
      .stAppHeader, header[data-testid="stHeader"] {{ display:none !important; }}
      section[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display:none !important; }}
      .stMainBlockContainer {{ max-width:100% !important; }}
      [data-testid="stVerticalBlock"] {{ max-width:420px; margin:0 auto; }}
      input[type="password"] {{
        background:#1A1A1A !important; border:1px solid #2A2A2A !important;
        border-radius:10px !important; color:#fff !important;
        font-size:1rem !important; padding:12px 16px !important; width:100% !important;
      }}
      input[type="password"]::placeholder {{ color:{C["gray"]} !important; }}
      .stFormSubmitButton > button {{
        width:100%; background:{C["yellow"]} !important; color:{C["black"]} !important;
        border:none !important; border-radius:10px !important;
        font-weight:800 !important; padding:12px !important; margin-top:8px;
      }}
      [data-testid="stForm"] {{ border:none !important; padding:0 !important; }}
    </style>
    <div style="text-align:center;padding:80px 0 40px">
      {logo_img(48)}
      <p style="color:{C["gray"]};font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;margin:10px 0 0">
        × Éducation Nationale
      </p>
    </div>""", unsafe_allow_html=True)

    with st.form("login", border=False):
        pwd = st.text_input("", type="password", placeholder="Mot de passe…")
        submitted = st.form_submit_button("Accéder au tableau de bord")

    if submitted:
        if _check_password(pwd):
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

    st.markdown(f"<p style='text-align:center;color:{C['gray']};font-size:.72rem;margin-top:24px'>Accès restreint · Rentrée 2024</p>",
                unsafe_allow_html=True)

if not st.session_state.get("ok"):
    _login_wall()
    st.stop()

# ── Global CSS (post-auth) ───────────────────────────────────────────────────────
st.markdown(f"""<style>
  .stApp {{ background-color:{C["black"]}; color:{C["white"]}; }}
  .stAppHeader, header[data-testid="stHeader"] {{ display:none !important; }}
  section[data-testid="stSidebar"] {{
    background-color:{C["card"]}; border-right:1px solid {C["border"]};
  }}
  section[data-testid="stSidebar"] * {{ color:{C["white"]} !important; }}
  h1,h2,h3,h4 {{ color:{C["white"]} !important; font-weight:800 !important; letter-spacing:-.02em; }}
  [data-testid="stMetric"] {{
    background:{C["card"]}; border:1px solid {C["border"]}; border-radius:16px; padding:20px 24px !important;
  }}
  [data-testid="stMetricLabel"] p {{
    color:{C["gray"]} !important; font-size:.72rem !important;
    text-transform:uppercase; letter-spacing:.1em; white-space:normal !important;
  }}
  [data-testid="stMetricValue"] {{ color:{C["yellow"]} !important; font-size:1.9rem !important; font-weight:800 !important; }}
  [data-baseweb="tab-list"] {{
    background:{C["card"]}; border-radius:12px; padding:4px; gap:4px; border:1px solid {C["border"]};
  }}
  [data-baseweb="tab"] {{ color:{C["gray"]} !important; border-radius:8px !important; font-weight:600; padding:8px 16px !important; }}
  [aria-selected="true"] {{ background:{C["yellow"]} !important; color:{C["black"]} !important; }}
  [data-baseweb="select"] > div {{ background:{C["card"]} !important; border-color:{C["border"]} !important; border-radius:10px !important; }}
  [data-baseweb="popover"] {{ background:{C["card"]} !important; }}
  hr {{ border-color:{C["border"]} !important; }}
  .tag {{ display:inline-block; background:{C["yellow"]}; color:{C["black"]}; font-size:.68rem;
          font-weight:800; text-transform:uppercase; letter-spacing:.12em;
          padding:4px 12px; border-radius:100px; margin-bottom:6px; }}
  ::-webkit-scrollbar {{ width:5px; }}
  ::-webkit-scrollbar-thumb {{ background:{C["border"]}; border-radius:3px; }}
</style>""", unsafe_allow_html=True)

# ── Plotly base layout ───────────────────────────────────────────────────────────
_PLT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font_color=C["white"], font_family="Inter, system-ui, sans-serif",
    margin=dict(l=16, r=16, t=36, b=16),
    xaxis=dict(gridcolor=C["border"], tickcolor=C["gray"], linecolor=C["border"], tickfont_size=11),
    yaxis=dict(gridcolor=C["border"], tickcolor=C["gray"], linecolor=C["border"], tickfont_size=11),
    legend=dict(bgcolor="rgba(0,0,0,0)", font_color=C["white"], font_size=12),
)

def plt(**kw) -> dict:
    return {**_PLT, **kw}

def pie_layout(**kw) -> dict:
    base = {k: v for k, v in _PLT.items() if k not in ("xaxis", "yaxis")}
    return {**base, "margin": dict(l=16, r=16, t=16, b=16), **kw}

def tag(label: str) -> str:
    return f'<div class="tag">{label}</div>'

# ── Data ────────────────────────────────────────────────────────────────────────
@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv("data/effectifs_personnels_EN.csv", low_memory=False)
    df["has_etp"] = df["etp_enseignants"].notna()
    df["has_pct"] = df["pct_femmes"].notna()
    return df

df = load()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""<div style="padding:16px 0 24px">
      {logo_img(36, "0")}
      <span style="font-size:.6rem;color:{C['gray']};display:block;margin-top:8px;
            letter-spacing:.15em;text-transform:uppercase">× Éducation Nationale</span>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"<p style='color:{C['gray']};font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px'>Filtres</p>",
                unsafe_allow_html=True)

    regions = sorted(df["libelle_region"].dropna().unique())
    sel_regions = st.multiselect("Région", regions, placeholder="Toutes les régions")
    sel_secteur = st.radio("Secteur", ["Tous", "Public", "Privé"], horizontal=True)

    st.divider()
    st.markdown(f"<span style='color:{C['gray']};font-size:.72rem'>Source : data.education.gouv.fr<br>Rentrée 2024</span>",
                unsafe_allow_html=True)

# ── Filtering ────────────────────────────────────────────────────────────────────
dff = df.copy()
if sel_regions:
    dff = dff[dff["libelle_region"].isin(sel_regions)]
if sel_secteur != "Tous":
    dff = dff[dff["statut_public_prive"] == sel_secteur]

etp = dff[dff["has_etp"]]   # ~57K — basic count
pct = dff[dff["has_pct"]]   # ~10K — full % profile (2d degré only)

# ── Header ───────────────────────────────────────────────────────────────────────
total_etp = etp["etp_enseignants"].sum()

st.markdown(f"""<div style="padding:28px 0 20px">
  {tag("Rentrée 2024 · Effectifs enseignants")}
  <h1 style="font-size:2.4rem;margin:8px 0 4px;line-height:1.1">
    Les enseignants<br><span style="color:{C['yellow']}">de l'Éducation Nationale</span>
  </h1>
  <p style="color:{C['gray']};font-size:.88rem;margin:0">
    {len(etp):,} établissements avec données ETP &nbsp;·&nbsp;
    {total_etp:,.0f} ETP recensés &nbsp;·&nbsp;
    {len(pct):,} avec profil complet (2d degré)
  </p>
</div>""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────────────────────────────
cols = st.columns(5)
kpis = [
    ("ETP total enseignants",  f"{total_etp:,.0f}"),
    ("ETP moyen / école",      f"{etp['etp_enseignants'].mean():.1f}"),
    ("Femmes enseignantes",    f"{pct['pct_femmes'].mean():.1f}%"          if len(pct) else "—"),
    ("Non-titulaires",         f"{pct['pct_non_titulaires'].mean():.1f}%"  if len(pct) else "—"),
    ("Ancienneté ≥ 8 ans",     f"{pct['pct_anciennete_8_ans_plus'].mean():.1f}%" if len(pct) else "—"),
]
for col, (label, val) in zip(cols, kpis):
    col.metric(label, val)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 Vue d'ensemble", "👩‍🏫 Genre", "📅 Âge & Ancienneté", "🎓 Corps enseignant"])

# ── Tab 1 — Vue d'ensemble ───────────────────────────────────────────────────────
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(tag("Régions"), unsafe_allow_html=True)
        st.markdown("#### ETP enseignants par région")
        reg = (etp.groupby("libelle_region")["etp_enseignants"]
               .agg(total="sum", moy="mean", nb="count").reset_index()
               .sort_values("total", ascending=True))
        fig = px.bar(reg, x="total", y="libelle_region", orientation="h",
                     color="moy", color_continuous_scale=[[0,"#2A2A2A"],[1,C["yellow"]]],
                     labels={"total":"ETP total","libelle_region":"","moy":"ETP moy."},
                     hover_data={"nb":True,"moy":":.1f"})
        fig.update_layout(**plt(height=460, coloraxis_showscale=False))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown(tag("Distribution"), unsafe_allow_html=True)
        st.markdown("#### ETP par établissement")
        cap = etp["etp_enseignants"].quantile(0.99)
        fig = px.histogram(etp[etp["etp_enseignants"] <= cap], x="etp_enseignants", nbins=60,
                           color_discrete_sequence=[C["yellow"]],
                           labels={"etp_enseignants":"ETP enseignants"})
        med, moy = etp["etp_enseignants"].median(), etp["etp_enseignants"].mean()
        fig.add_vline(x=med, line_dash="dash", line_color=C["teal"],
                      annotation_text=f"Médiane {med:.1f}", annotation_font_color=C["teal"])
        fig.add_vline(x=moy, line_dash="dot", line_color=C["white"],
                      annotation_text=f"Moy. {moy:.1f}", annotation_font_color=C["white"],
                      annotation_position="top left")
        fig.update_layout(**plt(height=240, showlegend=False))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(tag("1er vs 2d degré"), unsafe_allow_html=True)
        st.markdown("#### ETP selon le degré d'enseignement")
        degre = (etp.groupby("degre")["etp_enseignants"]
                 .agg(total="sum").reset_index())
        degre["label"] = degre["degre"].map({"1d":"1er degré (écoles)","2d":"2d degré (collèges/lycées)"})
        fig = px.bar(degre, x="label", y="total",
                     color="degre", color_discrete_map={"1d":C["yellow"],"2d":C["teal"]},
                     text="total", labels={"total":"ETP total","label":"","degre":""})
        fig.update_traces(marker_line_width=0, texttemplate="%{text:,.0f}",
                          textposition="outside", textfont_color=C["white"])
        fig.update_layout(**plt(height=200, showlegend=False, yaxis_visible=False, yaxis_showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown(tag("Comparaison régionale"), unsafe_allow_html=True)
    st.markdown("#### ETP moyen vs nombre d'établissements par région")
    sc = (etp.groupby("libelle_region")
          .agg(nb=("etp_enseignants","count"), moy=("etp_enseignants","mean"), tot=("etp_enseignants","sum"))
          .reset_index())
    fig = px.scatter(sc, x="nb", y="moy", size="tot", text="libelle_region",
                     color="moy", color_continuous_scale=[[0,"#2A2A2A"],[1,C["yellow"]]],
                     labels={"nb":"Nb établissements","moy":"ETP moyen / étab.","tot":"ETP total"},
                     size_max=55)
    fig.update_traces(textposition="top center", textfont_color=C["white"], textfont_size=10,
                      marker_line_color=C["border"], marker_line_width=1)
    fig.update_layout(**plt(height=380, coloraxis_showscale=False))
    st.plotly_chart(fig, use_container_width=True)

# ── Tab 2 — Genre ────────────────────────────────────────────────────────────────
with tab2:
    if not len(pct):
        st.info("Données de genre disponibles pour les établissements du 2d degré uniquement.")
    else:
        col_c, col_d = st.columns([3, 2])

        with col_c:
            st.markdown(tag("Distribution nationale"), unsafe_allow_html=True)
            st.markdown("#### % Femmes enseignantes par établissement")
            moy_f = pct["pct_femmes"].mean()
            fig = px.histogram(pct, x="pct_femmes", nbins=50,
                               color_discrete_sequence=[C["yellow"]],
                               labels={"pct_femmes":"% Femmes"})
            fig.add_vline(x=moy_f, line_dash="dash", line_color=C["white"],
                          annotation_text=f"Moy. {moy_f:.1f}%", annotation_font_color=C["white"],
                          annotation_position="top left")
            fig.update_layout(**plt(height=300, showlegend=False))
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        with col_d:
            st.markdown(tag("Résumé"), unsafe_allow_html=True)
            st.markdown("#### Femmes / Hommes")
            pct_f = pct["pct_femmes"].mean()
            fig = go.Figure(go.Pie(
                labels=["Femmes","Hommes"], values=[pct_f, 100-pct_f],
                hole=0.62, marker_colors=[C["yellow"],"#2A2A2A"], textinfo="none",
                hovertemplate="%{label} : %{value:.1f}%<extra></extra>",
            ))
            fig.add_annotation(text=f"<b>{pct_f:.0f}%</b>", x=0.5, y=0.52, showarrow=False,
                               font=dict(size=32, color=C["yellow"]))
            fig.add_annotation(text="femmes", x=0.5, y=0.36, showarrow=False,
                               font=dict(size=13, color=C["gray"]))
            fig.update_layout(**pie_layout(height=300, showlegend=False))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown(tag("Par région"), unsafe_allow_html=True)
        st.markdown("#### % Femmes par région")
        reg_f = (pct.groupby("libelle_region")["pct_femmes"]
                 .mean().round(1).reset_index().sort_values("pct_femmes", ascending=False))
        avg_f = reg_f["pct_femmes"].mean()
        fig = go.Figure(go.Bar(
            x=reg_f["libelle_region"], y=reg_f["pct_femmes"],
            marker_color=[C["yellow"] if v >= avg_f else C["teal"] for v in reg_f["pct_femmes"]],
            marker_line_width=0,
            hovertemplate="%{x} : %{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=avg_f, line_dash="dash", line_color=C["white"],
                      annotation_text=f"Moy. {avg_f:.1f}%", annotation_font_color=C["white"])
        fig.update_layout(**plt(height=300))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(tag("Précarité"), unsafe_allow_html=True)
        st.markdown("#### % Non-titulaires par région")
        reg_nt = (pct.groupby("libelle_region")["pct_non_titulaires"]
                  .mean().round(1).reset_index().sort_values("pct_non_titulaires", ascending=True))
        fig = px.bar(reg_nt, x="pct_non_titulaires", y="libelle_region", orientation="h",
                     color="pct_non_titulaires",
                     color_continuous_scale=[[0,"#2A2A2A"],[.5,C["teal"]],[1,C["red"]]],
                     labels={"pct_non_titulaires":"% Non-titulaires","libelle_region":""})
        fig.update_layout(**plt(height=400, coloraxis_showscale=False))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 3 — Âge & Ancienneté ────────────────────────────────────────────────────
with tab3:
    if not len(etp):
        st.info("Pas de données ETP pour la sélection.")
    else:
        col_e, col_f = st.columns(2)

        age_groups = [("Moins de 35 ans","etp_moins_35_ans"), ("35 à 50 ans","etp_35_50_ans"), ("50 ans et plus","etp_50_ans_plus")]
        anc_groups = [("< 2 ans","etp_anciennete_moins_2_ans"), ("2 à 5 ans","etp_anciennete_2_5_ans"),
                      ("5 à 8 ans","etp_anciennete_5_8_ans"), ("8 ans et +","etp_anciennete_8_ans_plus")]

        def stacked_bars(groups, colors, title, tag_label):
            vals = [(label, etp[col].sum()) for label, col in groups]
            total = sum(v for _, v in vals if pd.notna(v))
            fig = go.Figure()
            for (label, val), color in zip(vals, colors):
                if pd.notna(val):
                    fig.add_trace(go.Bar(
                        name=label, x=[label], y=[val], marker_color=color, marker_line_width=0,
                        text=f"{val:,.0f}<br>{val/total*100:.1f}%",
                        textposition="inside", textfont=dict(color=C["black"], size=13),
                        hovertemplate=f"{label} : %{{y:,.0f}} ETP<extra></extra>",
                    ))
            fig.update_layout(**plt(height=320, showlegend=False, yaxis_title="ETP"))
            return fig

        with col_e:
            st.markdown(tag("Tranches d'âge"), unsafe_allow_html=True)
            st.markdown("#### ETP total par tranche d'âge")
            st.plotly_chart(stacked_bars(age_groups, [C["yellow"], C["teal"], C["red"]], "Âge", "Âge"),
                            use_container_width=True)

        with col_f:
            st.markdown(tag("Ancienneté"), unsafe_allow_html=True)
            st.markdown("#### ETP par ancienneté dans l'établissement")
            st.plotly_chart(stacked_bars(anc_groups, [C["teal"], C["yellow"], C["red"], C["red"]], "Anc", "Anc"),
                            use_container_width=True)

        if len(pct):
            st.divider()
            col_g, col_h = st.columns(2)
            pie_colors_age = [C["yellow"], C["teal"], C["red"]]
            pie_colors_anc = [C["teal"], C["yellow"], C["red"], "#45B7D1"]

            def pct_pie(labels, values, colors):
                fig = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.55, textinfo="none",
                    marker_colors=colors,
                    hovertemplate="%{label} : %{value:.1f}%<extra></extra>",
                ))
                fig.update_layout(**pie_layout(height=280,
                    legend=dict(orientation="v", font_color=C["white"], font_size=12, bgcolor="rgba(0,0,0,0)")))
                return fig

            with col_g:
                st.markdown(tag("Profil âge"), unsafe_allow_html=True)
                st.markdown("#### Répartition par âge (2d degré)")
                st.plotly_chart(pct_pie(
                    ["Moins de 35 ans","35 à 50 ans","50 ans et plus"],
                    [pct["pct_moins_35_ans"].mean(), pct["pct_35_50_ans"].mean(), pct["pct_plus_50_ans"].mean()],
                    pie_colors_age,
                ), use_container_width=True)

            with col_h:
                st.markdown(tag("Profil ancienneté"), unsafe_allow_html=True)
                st.markdown("#### Répartition par ancienneté (2d degré)")
                st.plotly_chart(pct_pie(
                    ["< 2 ans","2 à 5 ans","5 à 8 ans","8 ans et +"],
                    [pct["pct_anciennete_moins_2_ans"].mean(), pct["pct_anciennete_2_5_ans"].mean(),
                     pct["pct_anciennete_5_8_ans"].mean(), pct["pct_anciennete_8_ans_plus"].mean()],
                    pie_colors_anc,
                ), use_container_width=True)

# ── Tab 4 — Corps enseignant ──────────────────────────────────────────────────────
with tab4:
    if not len(pct):
        st.info("Données de corps disponibles pour les établissements du 2d degré uniquement.")
    else:
        st.markdown(f'<p style="color:{C["gray"]};font-size:.83rem;margin-bottom:16px">Données pour {len(pct):,} établissements du 2d degré.</p>',
                    unsafe_allow_html=True)
        col_i, col_j = st.columns([2, 3])

        with col_i:
            st.markdown(tag("Composition"), unsafe_allow_html=True)
            st.markdown("#### ETP moyen par corps")
            corps = pd.DataFrame({
                "Corps": ["Agrégés","Certifiés / PEPs","PLP","Autres titulaires","Non-titulaires"],
                "ETP":   [pct["etp_agreges"].mean(), pct["etp_certifies"].mean(), pct["etp_plp"].mean(),
                          pct["etp_autres_titulaires"].mean(), pct["etp_non_titulaires"].mean()],
            }).dropna()
            fig = go.Figure(go.Pie(
                labels=corps["Corps"], values=corps["ETP"], hole=0.55, textinfo="none",
                marker_colors=[C["yellow"], C["teal"], C["red"], "#45B7D1", "#FFEAA7"],
                hovertemplate="%{label} : %{value:.1f} ETP moy.<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(**pie_layout(height=320,
                legend=dict(orientation="v", font_color=C["white"], font_size=12, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig, use_container_width=True)

        with col_j:
            st.markdown(tag("Comparaison régionale"), unsafe_allow_html=True)
            st.markdown("#### % Agrégés / % Non-titulaires par région")
            rc = (pct.groupby("libelle_region")
                  .agg(pct_agg=("pct_agreges","mean"), pct_nt=("pct_non_titulaires","mean"))
                  .round(1).reset_index().sort_values("pct_agg", ascending=False))
            fig = go.Figure([
                go.Bar(name="% Agrégés", x=rc["libelle_region"], y=rc["pct_agg"],
                       marker_color=C["yellow"], marker_line_width=0),
                go.Bar(name="% Non-titulaires", x=rc["libelle_region"], y=rc["pct_nt"],
                       marker_color=C["red"], marker_line_width=0),
            ])
            fig.update_layout(**plt(height=320, barmode="group"))
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown(tag("Titularité"), unsafe_allow_html=True)
        st.markdown("#### Titulaires vs non-titulaires par région")
        rt = (pct.groupby("libelle_region")["pct_non_titulaires"]
              .mean().round(1).reset_index().sort_values("pct_non_titulaires", ascending=False))
        rt["pct_tit"] = 100 - rt["pct_non_titulaires"]
        fig = go.Figure([
            go.Bar(name="Titulaires", y=rt["libelle_region"], x=rt["pct_tit"],
                   orientation="h", marker_color=C["yellow"], marker_line_width=0,
                   hovertemplate="%{y} — titulaires : %{x:.1f}%<extra></extra>"),
            go.Bar(name="Non-titulaires", y=rt["libelle_region"], x=rt["pct_non_titulaires"],
                   orientation="h", marker_color=C["red"], marker_line_width=0,
                   hovertemplate="%{y} — non-titulaires : %{x:.1f}%<extra></extra>"),
        ])
        fig.update_layout(**plt(height=440, barmode="stack", xaxis_title="% enseignants", yaxis_title=""))
        st.plotly_chart(fig, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center;padding:36px 0 20px;color:{C["gray"]};
  font-size:.75rem;border-top:1px solid {C["border"]};margin-top:24px">
  Données : Ministère de l'Éducation Nationale — data.education.gouv.fr · Rentrée 2024<br>
  <span style="color:{C["yellow"]};font-weight:800">DATACK</span> × Proxymite
</div>""", unsafe_allow_html=True)
