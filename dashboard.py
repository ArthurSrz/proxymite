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
      [data-testid="stImage"] img {{ margin:0 auto; display:block; max-height:52px; width:auto; }}
    </style>""", unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        if _logo_path.exists():
            st.image(str(_logo_path), width="stretch")
        else:
            st.markdown(f"<div style='text-align:center'><span style='font-size:2rem;font-weight:900;color:{C['yellow']}'>DATACK</span></div>",
                        unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;color:{C['gray']};font-size:.72rem;letter-spacing:.15em;text-transform:uppercase;margin:4px 0 32px'>× Éducation Nationale</p>",
                    unsafe_allow_html=True)

    with st.form("login", border=False):
        _, mid2, _ = st.columns([1, 2, 1])
        with mid2:
            pwd = st.text_input("Mot de passe", type="password", placeholder="Mot de passe…", label_visibility="collapsed")
            submitted = st.form_submit_button("Accéder au tableau de bord")

    if submitted:
        if _check_password(pwd):
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")

    _, mid3, _ = st.columns([1, 2, 1])
    with mid3:
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
  .tag-b {{ display:inline-block; background:{C["teal"]}; color:{C["black"]}; font-size:.68rem;
            font-weight:800; text-transform:uppercase; letter-spacing:.12em;
            padding:4px 12px; border-radius:100px; margin-bottom:6px; }}
  ::-webkit-scrollbar {{ width:5px; }}
  ::-webkit-scrollbar-thumb {{ background:{C["border"]}; border-radius:3px; }}
  /* Force columns to stay side-by-side — prevent Streamlit responsive stacking */
  [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap !important; }}
  [data-testid="column"] {{ min-width:0 !important; overflow:hidden; }}
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

def tag(label: str, b: bool = False) -> str:
    cls = "tag-b" if b else "tag"
    return f'<div class="{cls}">{label}</div>'

# ── Data ────────────────────────────────────────────────────────────────────────
@st.cache_data
def load() -> pd.DataFrame:
    df = pd.read_csv("data/effectifs_personnels_EN.csv", low_memory=False)
    df["has_etp"] = df["etp_enseignants"].notna()
    df["has_pct"] = df["pct_femmes"].notna()
    return df

df = load()

# ── Sidebar ─────────────────────────────────────────────────────────────────────
def _filter_group(prefix: str, df_full: pd.DataFrame) -> pd.DataFrame:
    """Render cascading filters (région → académie → département → secteur) and return filtered df."""
    regions   = sorted(df_full["libelle_region"].dropna().unique())
    sel_r     = st.multiselect("Région", regions, placeholder="Toutes", key=f"{prefix}_reg")

    sub = df_full[df_full["libelle_region"].isin(sel_r)] if sel_r else df_full
    academies = sorted(sub["libelle_academie"].dropna().unique())
    sel_a     = st.multiselect("Académie", academies, placeholder="Toutes", key=f"{prefix}_acad")

    sub2 = sub[sub["libelle_academie"].isin(sel_a)] if sel_a else sub
    depts = sorted(sub2["libelle_departement"].dropna().unique())
    sel_d = st.multiselect("Département", depts, placeholder="Tous", key=f"{prefix}_dept")

    sel_s = st.radio("Secteur", ["Tous", "Public", "Privé"], horizontal=True, key=f"{prefix}_sec")

    out = df_full.copy()
    if sel_r: out = out[out["libelle_region"].isin(sel_r)]
    if sel_a: out = out[out["libelle_academie"].isin(sel_a)]
    if sel_d: out = out[out["libelle_departement"].isin(sel_d)]
    if sel_s != "Tous": out = out[out["statut_public_prive"] == sel_s]
    return out

with st.sidebar:
    st.markdown(f"""<div style="padding:16px 0 24px">
      {logo_img(36, "0")}
      <span style="font-size:.6rem;color:{C['gray']};display:block;margin-top:8px;
            letter-spacing:.15em;text-transform:uppercase">× Éducation Nationale</span>
    </div>""", unsafe_allow_html=True)

    ab_mode = st.toggle("Mode A/B", value=False, help="Comparer deux groupes côte à côte")

    st.markdown(f"<p style='color:{C['yellow']};font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;margin:12px 0 4px'>{'Groupe A' if ab_mode else 'Filtres'}</p>",
                unsafe_allow_html=True)
    dff_a = _filter_group("a", df)

    if ab_mode:
        st.divider()
        st.markdown(f"<p style='color:{C['teal']};font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;margin:4px 0 4px'>Groupe B</p>",
                    unsafe_allow_html=True)
        dff_b = _filter_group("b", df)
    else:
        dff_b = None

    st.divider()
    st.markdown(f"<span style='color:{C['gray']};font-size:.72rem'>Source : data.education.gouv.fr<br>Rentrée 2024</span>",
                unsafe_allow_html=True)

# ── Derived subsets ──────────────────────────────────────────────────────────────
etp_a = dff_a[dff_a["has_etp"]]
pct_a = dff_a[dff_a["has_pct"]]
etp_b = dff_b[dff_b["has_etp"]] if dff_b is not None else None
pct_b = dff_b[dff_b["has_pct"]] if dff_b is not None else None

# ── Header ───────────────────────────────────────────────────────────────────────
def _scope_label(etp, pct) -> str:
    return f"{len(etp):,} étab. ETP · {etp['etp_enseignants'].sum():,.0f} ETP · {len(pct):,} profil complet"

st.markdown(f"""<div style="padding:28px 0 20px">
  {tag("Rentrée 2024 · Effectifs enseignants")}
  <h1 style="font-size:2.4rem;margin:8px 0 4px;line-height:1.1">
    Les enseignants<br><span style="color:{C['yellow']}">de l'Éducation Nationale</span>
  </h1>
  <p style="color:{C['gray']};font-size:.88rem;margin:0">{_scope_label(etp_a, pct_a)}</p>
</div>""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────────────────────────────
def _kpi_rows(etp, pct, label_suffix=""):
    return [
        (f"ETP total{label_suffix}",      f"{etp['etp_enseignants'].sum():,.0f}"),
        (f"ETP moyen / école{label_suffix}", f"{etp['etp_enseignants'].mean():.1f}"),
        (f"Femmes{label_suffix}",          f"{pct['pct_femmes'].mean():.1f}%"          if len(pct) else "—"),
        (f"Non-titulaires{label_suffix}",  f"{pct['pct_non_titulaires'].mean():.1f}%"  if len(pct) else "—"),
        (f"Ancienneté ≥8 ans{label_suffix}", f"{pct['pct_anciennete_8_ans_plus'].mean():.1f}%" if len(pct) else "—"),
    ]

def _kpi_html_row(kpis, color, header):
    cards = "".join(f"""
      <div style="background:{C['card']};border:1px solid {C['border']};border-radius:16px;
                  padding:20px 24px;flex:1;min-width:0;overflow:hidden">
        <p style="color:{C['gray']};font-size:.72rem;text-transform:uppercase;
                  letter-spacing:.1em;margin:0 0 8px;white-space:nowrap;
                  overflow:hidden;text-overflow:ellipsis">{label}</p>
        <p style="color:{color};font-size:1.9rem;font-weight:800;margin:0">{val}</p>
      </div>""" for label, val in kpis)
    return f"""
      <p style="color:{color};font-weight:800;font-size:.75rem;text-transform:uppercase;
                letter-spacing:.1em;margin:12px 0 6px">{header}</p>
      <div style="display:flex;gap:12px;margin-bottom:4px">{cards}</div>"""

if ab_mode and etp_b is not None:
    st.markdown(
        _kpi_html_row(_kpi_rows(etp_a, pct_a), C["yellow"], f"Groupe A — {_scope_label(etp_a, pct_a)}") +
        _kpi_html_row(_kpi_rows(etp_b, pct_b), C["teal"],   f"Groupe B — {_scope_label(etp_b, pct_b)}"),
        unsafe_allow_html=True,
    )
else:
    cols = st.columns(5)
    for col, (label, val) in zip(cols, _kpi_rows(etp_a, pct_a)):
        col.metric(label, val)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Vue d'ensemble", "👩‍🏫 Genre", "📅 Âge & Ancienneté", "🎓 Corps enseignant", "🏫 Établissement"])

# ── Tab 1 — Vue d'ensemble ───────────────────────────────────────────────────────
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(tag("Régions"), unsafe_allow_html=True)
        st.markdown("#### ETP enseignants par région")
        if ab_mode and etp_b is not None:
            reg_a = etp_a.groupby("libelle_region")["etp_enseignants"].sum().reset_index().rename(columns={"etp_enseignants":"A"})
            reg_b = etp_b.groupby("libelle_region")["etp_enseignants"].sum().reset_index().rename(columns={"etp_enseignants":"B"})
            reg   = reg_a.merge(reg_b, on="libelle_region", how="outer").fillna(0).sort_values("A", ascending=True)
            fig = go.Figure([
                go.Bar(name="Groupe A", y=reg["libelle_region"], x=reg["A"], orientation="h",
                       marker_color=C["yellow"], marker_line_width=0),
                go.Bar(name="Groupe B", y=reg["libelle_region"], x=reg["B"], orientation="h",
                       marker_color=C["teal"], marker_line_width=0),
            ])
            fig.update_layout(**plt(height=460, barmode="group"))
        else:
            reg = (etp_a.groupby("libelle_region")["etp_enseignants"]
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
        cap = etp_a["etp_enseignants"].quantile(0.99)
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=etp_a[etp_a["etp_enseignants"] <= cap]["etp_enseignants"],
            nbinsx=60, marker_color=C["yellow"], marker_line_width=0,
            name="Groupe A" if ab_mode else "ETP",
        ))
        if ab_mode and etp_b is not None:
            cap_b = etp_b["etp_enseignants"].quantile(0.99)
            fig.add_trace(go.Histogram(
                x=etp_b[etp_b["etp_enseignants"] <= cap_b]["etp_enseignants"],
                nbinsx=60, marker_color=C["teal"], marker_line_width=0,
                name="Groupe B", opacity=0.7,
            ))
            fig.update_layout(**plt(height=240, barmode="overlay"))
        else:
            med, moy = etp_a["etp_enseignants"].median(), etp_a["etp_enseignants"].mean()
            fig.add_vline(x=med, line_dash="dash", line_color=C["teal"],
                          annotation_text=f"Médiane {med:.1f}",
                          annotation_font_color=C["teal"], annotation_position="top right")
            fig.add_vline(x=moy, line_dash="dot", line_color=C["white"],
                          annotation_text=f"Moy. {moy:.1f}",
                          annotation_font_color=C["white"], annotation_position="bottom right")
            fig.update_layout(**plt(height=240, showlegend=False))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(tag("1er vs 2d degré"), unsafe_allow_html=True)
        st.markdown("#### ETP selon le degré d'enseignement")
        if ab_mode and etp_b is not None:
            da = etp_a.groupby("degre")["etp_enseignants"].sum().reset_index()
            db = etp_b.groupby("degre")["etp_enseignants"].sum().reset_index()
            da["label"] = da["degre"].map({"1d":"1er degré","2d":"2d degré"})
            db["label"] = db["degre"].map({"1d":"1er degré","2d":"2d degré"})
            fig = go.Figure([
                go.Bar(name="Groupe A", x=da["label"], y=da["etp_enseignants"], marker_color=C["yellow"], marker_line_width=0),
                go.Bar(name="Groupe B", x=db["label"], y=db["etp_enseignants"], marker_color=C["teal"], marker_line_width=0),
            ])
            fig.update_layout(**plt(height=200, barmode="group"))
        else:
            degre = etp_a.groupby("degre")["etp_enseignants"].agg(total="sum").reset_index()
            degre["label"] = degre["degre"].map({"1d":"1er degré (écoles)","2d":"2d degré (collèges/lycées)"})
            fig = px.bar(degre, x="label", y="total",
                         color="degre", color_discrete_map={"1d":C["yellow"],"2d":C["teal"]},
                         text="total", labels={"total":"ETP total","label":"","degre":""})
            fig.update_traces(marker_line_width=0, texttemplate="%{text:,.0f}",
                              textposition="outside", textfont_color=C["white"])
            fig.update_layout(**plt(height=200, showlegend=False, yaxis_visible=False, yaxis_showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

    if not ab_mode:
        st.divider()
        st.markdown(tag("Comparaison régionale"), unsafe_allow_html=True)
        st.markdown("#### ETP moyen vs nombre d'établissements par région")
        sc = (etp_a.groupby("libelle_region")
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
    if not len(pct_a):
        st.info("Données de genre disponibles pour les établissements du 2d degré uniquement.")
    else:
        col_c, col_d = st.columns([3, 2])

        with col_c:
            st.markdown(tag("Distribution nationale"), unsafe_allow_html=True)
            st.markdown("#### % Femmes enseignantes par établissement")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=pct_a["pct_femmes"], nbinsx=50,
                marker_color=C["yellow"], marker_line_width=0,
                name="Groupe A" if ab_mode else "Étab.",
            ))
            if ab_mode and pct_b is not None and len(pct_b):
                fig.add_trace(go.Histogram(
                    x=pct_b["pct_femmes"], nbinsx=50,
                    marker_color=C["teal"], marker_line_width=0, opacity=0.7,
                    name="Groupe B",
                ))
                fig.update_layout(**plt(height=300, barmode="overlay"))
            else:
                moy_f = pct_a["pct_femmes"].mean()
                fig.add_vline(x=moy_f, line_dash="dash", line_color=C["white"],
                              annotation_text=f"Moy. {moy_f:.1f}%", annotation_font_color=C["white"],
                              annotation_position="top left")
                fig.update_layout(**plt(height=300, showlegend=False))
            st.plotly_chart(fig, use_container_width=True)

        with col_d:
            if ab_mode and pct_b is not None and len(pct_b):
                st.markdown(tag("A vs B"), unsafe_allow_html=True)
                st.markdown("#### % Femmes moyen")
                pct_fa = pct_a["pct_femmes"].mean()
                pct_fb = pct_b["pct_femmes"].mean()
                fig = go.Figure([
                    go.Bar(name="Groupe A", x=["A"], y=[pct_fa], marker_color=C["yellow"], marker_line_width=0,
                           text=[f"{pct_fa:.1f}%"], textposition="outside", textfont_color=C["white"]),
                    go.Bar(name="Groupe B", x=["B"], y=[pct_fb], marker_color=C["teal"], marker_line_width=0,
                           text=[f"{pct_fb:.1f}%"], textposition="outside", textfont_color=C["white"]),
                ])
                fig.update_layout(**plt(height=300, showlegend=False, yaxis_title="% Femmes"))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown(tag("Résumé"), unsafe_allow_html=True)
                st.markdown("#### Femmes / Hommes")
                pct_f = pct_a["pct_femmes"].mean()
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
        if ab_mode and pct_b is not None and len(pct_b):
            rfa = pct_a.groupby("libelle_region")["pct_femmes"].mean().round(1).reset_index().rename(columns={"pct_femmes":"A"})
            rfb = pct_b.groupby("libelle_region")["pct_femmes"].mean().round(1).reset_index().rename(columns={"pct_femmes":"B"})
            rf  = rfa.merge(rfb, on="libelle_region", how="outer").fillna(0).sort_values("A", ascending=False)
            fig = go.Figure([
                go.Bar(name="Groupe A", x=rf["libelle_region"], y=rf["A"], marker_color=C["yellow"], marker_line_width=0),
                go.Bar(name="Groupe B", x=rf["libelle_region"], y=rf["B"], marker_color=C["teal"], marker_line_width=0),
            ])
            fig.update_layout(**plt(height=300, barmode="group"))
        else:
            reg_f = (pct_a.groupby("libelle_region")["pct_femmes"]
                     .mean().round(1).reset_index().sort_values("pct_femmes", ascending=False))
            avg_f = reg_f["pct_femmes"].mean()
            fig = go.Figure(go.Bar(
                x=reg_f["libelle_region"], y=reg_f["pct_femmes"],
                marker_color=[C["yellow"] if v >= avg_f else C["teal"] for v in reg_f["pct_femmes"]],
                marker_line_width=0, hovertemplate="%{x} : %{y:.1f}%<extra></extra>",
            ))
            fig.add_hline(y=avg_f, line_dash="dash", line_color=C["white"],
                          annotation_text=f"Moy. {avg_f:.1f}%", annotation_font_color=C["white"])
            fig.update_layout(**plt(height=300))
        st.plotly_chart(fig, use_container_width=True)

        st.markdown(tag("Précarité"), unsafe_allow_html=True)
        st.markdown("#### % Non-titulaires par région")
        if ab_mode and pct_b is not None and len(pct_b):
            nta = pct_a.groupby("libelle_region")["pct_non_titulaires"].mean().round(1).reset_index().rename(columns={"pct_non_titulaires":"A"})
            ntb = pct_b.groupby("libelle_region")["pct_non_titulaires"].mean().round(1).reset_index().rename(columns={"pct_non_titulaires":"B"})
            nt  = nta.merge(ntb, on="libelle_region", how="outer").fillna(0).sort_values("A", ascending=True)
            fig = go.Figure([
                go.Bar(name="Groupe A", y=nt["libelle_region"], x=nt["A"], orientation="h",
                       marker_color=C["yellow"], marker_line_width=0),
                go.Bar(name="Groupe B", y=nt["libelle_region"], x=nt["B"], orientation="h",
                       marker_color=C["teal"], marker_line_width=0),
            ])
            fig.update_layout(**plt(height=400, barmode="group"))
        else:
            reg_nt = (pct_a.groupby("libelle_region")["pct_non_titulaires"]
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
    if not len(etp_a):
        st.info("Pas de données ETP pour la sélection.")
    else:
        age_groups = [("< 35 ans","etp_moins_35_ans"), ("35–50 ans","etp_35_50_ans"), ("50 ans+","etp_50_ans_plus")]
        anc_groups = [("< 2 ans","etp_anciennete_moins_2_ans"), ("2–5 ans","etp_anciennete_2_5_ans"),
                      ("5–8 ans","etp_anciennete_5_8_ans"), ("8 ans+","etp_anciennete_8_ans_plus")]

        def grouped_bars(groups, etp_src_a, etp_src_b, colors, height=320):
            labels = [label for label, _ in groups]
            vals_a = [etp_src_a[col].sum() for _, col in groups]
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Groupe A" if ab_mode else "ETP",
                                 x=labels, y=vals_a,
                                 marker_color=colors[0] if not ab_mode else C["yellow"],
                                 marker_line_width=0,
                                 text=[f"{v:,.0f}" for v in vals_a], textposition="outside",
                                 textfont_color=C["white"]))
            if ab_mode and etp_src_b is not None:
                vals_b = [etp_src_b[col].sum() for _, col in groups]
                fig.add_trace(go.Bar(name="Groupe B",
                                     x=labels, y=vals_b,
                                     marker_color=C["teal"], marker_line_width=0,
                                     text=[f"{v:,.0f}" for v in vals_b], textposition="outside",
                                     textfont_color=C["white"]))
                fig.update_layout(**plt(height=height, barmode="group"))
            else:
                for i, (color, label, val) in enumerate(zip(colors, labels, vals_a)):
                    fig.data[0].marker.color = colors
                fig.update_layout(**plt(height=height, showlegend=False))
            return fig

        col_e, col_f = st.columns(2)
        with col_e:
            st.markdown(tag("Tranches d'âge"), unsafe_allow_html=True)
            st.markdown("#### ETP par tranche d'âge")
            st.plotly_chart(grouped_bars(age_groups, etp_a, etp_b,
                                         [C["yellow"], C["teal"], C["red"]]), use_container_width=True)
        with col_f:
            st.markdown(tag("Ancienneté"), unsafe_allow_html=True)
            st.markdown("#### ETP par ancienneté dans l'établissement")
            st.plotly_chart(grouped_bars(anc_groups, etp_a, etp_b,
                                         [C["teal"], C["yellow"], C["red"], "#45B7D1"]), use_container_width=True)

        if len(pct_a) and not ab_mode:
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
                    ["< 35 ans","35–50 ans","50 ans+"],
                    [pct_a["pct_moins_35_ans"].mean(), pct_a["pct_35_50_ans"].mean(), pct_a["pct_plus_50_ans"].mean()],
                    pie_colors_age,
                ), use_container_width=True)

            with col_h:
                st.markdown(tag("Profil ancienneté"), unsafe_allow_html=True)
                st.markdown("#### Répartition par ancienneté (2d degré)")
                st.plotly_chart(pct_pie(
                    ["< 2 ans","2–5 ans","5–8 ans","8 ans+"],
                    [pct_a["pct_anciennete_moins_2_ans"].mean(), pct_a["pct_anciennete_2_5_ans"].mean(),
                     pct_a["pct_anciennete_5_8_ans"].mean(), pct_a["pct_anciennete_8_ans_plus"].mean()],
                    pie_colors_anc,
                ), use_container_width=True)

# ── Tab 4 — Corps enseignant ──────────────────────────────────────────────────────
with tab4:
    if not len(pct_a):
        st.info("Données de corps disponibles pour les établissements du 2d degré uniquement.")
    else:
        st.markdown(f'<p style="color:{C["gray"]};font-size:.83rem;margin-bottom:16px">{len(pct_a):,} établissements du 2d degré.</p>',
                    unsafe_allow_html=True)
        col_i, col_j = st.columns([2, 3])

        with col_i:
            st.markdown(tag("Composition"), unsafe_allow_html=True)
            st.markdown("#### ETP moyen par corps")
            corps_labels = ["Agrégés","Certifiés / PEPs","PLP","Autres titulaires","Non-titulaires"]
            corps_cols   = ["etp_agreges","etp_certifies","etp_plp","etp_autres_titulaires","etp_non_titulaires"]
            corps_colors = [C["yellow"], C["teal"], C["red"], "#45B7D1", "#FFEAA7"]
            if ab_mode and pct_b is not None and len(pct_b):
                vals_a = [pct_a[c].mean() for c in corps_cols]
                vals_b = [pct_b[c].mean() for c in corps_cols]
                fig = go.Figure([
                    go.Bar(name="Groupe A", x=corps_labels, y=vals_a, marker_color=C["yellow"], marker_line_width=0),
                    go.Bar(name="Groupe B", x=corps_labels, y=vals_b, marker_color=C["teal"], marker_line_width=0),
                ])
                fig.update_layout(**plt(height=320, barmode="group"))
            else:
                corps = pd.DataFrame({"Corps": corps_labels, "ETP": [pct_a[c].mean() for c in corps_cols]}).dropna()
                fig = go.Figure(go.Pie(
                    labels=corps["Corps"], values=corps["ETP"], hole=0.55, textinfo="none",
                    marker_colors=corps_colors,
                    hovertemplate="%{label} : %{value:.1f} ETP moy.<br>%{percent}<extra></extra>",
                ))
                fig.update_layout(**pie_layout(height=320,
                    legend=dict(orientation="v", font_color=C["white"], font_size=12, bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig, use_container_width=True)

        with col_j:
            st.markdown(tag("Comparaison régionale"), unsafe_allow_html=True)
            st.markdown("#### % Agrégés / % Non-titulaires par région")
            rc = (pct_a.groupby("libelle_region")
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
        rt = (pct_a.groupby("libelle_region")["pct_non_titulaires"]
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

# ── Tab 5 — Établissement ────────────────────────────────────────────────────────
with tab5:
    st.markdown(tag("Maillage établissement"), unsafe_allow_html=True)
    st.markdown("#### Profil d'un établissement")

    # Search within the current filter A selection for relevance
    search_pool = dff_a if len(dff_a) < len(df) else df
    etab_options = (search_pool.dropna(subset=["nom_etablissement"])
                    .assign(label=lambda d: d["nom_etablissement"] + " — " + d["nom_commune"].fillna("") + " (" + d["code_departement"].fillna("") + ")")
                    .sort_values("label")[["label","identifiant_de_l_etablissement"]]
                    .drop_duplicates("identifiant_de_l_etablissement"))

    sel_etab_label = st.selectbox(
        "Rechercher un établissement",
        options=[""] + etab_options["label"].tolist(),
        format_func=lambda x: "Sélectionner…" if x == "" else x,
        label_visibility="collapsed",
    )

    if sel_etab_label and sel_etab_label != "":
        uai = etab_options.loc[etab_options["label"] == sel_etab_label, "identifiant_de_l_etablissement"].iloc[0]
        row = df[df["identifiant_de_l_etablissement"] == uai].iloc[0]

        # ── Identity card ──
        st.markdown(f"""<div style="background:{C['card']};border:1px solid {C['border']};
            border-radius:16px;padding:20px 24px;margin:16px 0">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <h3 style="margin:0 0 4px;color:{C['white']}">{row['nom_etablissement']}</h3>
              <p style="margin:0;color:{C['gray']};font-size:.85rem">
                {row.get('adresse_1','')} — {row.get('nom_commune','')} ({row.get('code_postal','')})
              </p>
            </div>
            <div style="text-align:right">
              <span style="background:{C['yellow']};color:{C['black']};padding:4px 12px;border-radius:100px;
                font-size:.72rem;font-weight:800">{row.get('type_etablissement','')}</span><br>
              <span style="color:{C['gray']};font-size:.75rem;margin-top:4px;display:inline-block">
                {row.get('statut_public_prive','')} · {row.get('libelle_academie','')} · {row.get('libelle_departement','')}
              </span>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # ── KPIs for this établissement ──
        has_etp_row = pd.notna(row.get("etp_enseignants"))
        has_pct_row = pd.notna(row.get("pct_femmes"))

        kpi_cols = st.columns(4)
        kpi_cols[0].metric("ETP enseignants",    f"{row['etp_enseignants']:.1f}"     if has_etp_row else "—")
        kpi_cols[1].metric("% Femmes",           f"{row['pct_femmes']:.1f}%"         if has_pct_row else "—")
        kpi_cols[2].metric("% Non-titulaires",   f"{row['pct_non_titulaires']:.1f}%" if has_pct_row else "—")
        kpi_cols[3].metric("% Ancienneté ≥8 ans",f"{row['pct_anciennete_8_ans_plus']:.1f}%" if has_pct_row else "—")

        # ── Contexte académie ──
        acad = row.get("libelle_academie")
        if acad and has_etp_row:
            peer = df[(df["libelle_academie"] == acad) & df["has_etp"]]
            peer_pct = df[(df["libelle_academie"] == acad) & df["has_pct"]]
            st.divider()
            st.markdown(f"<p style='color:{C['gray']};font-size:.8rem'>Comparaison avec l'académie de <b style='color:{C['white']}'>{acad}</b> ({len(peer):,} étab.)</p>", unsafe_allow_html=True)

            # Normalize all metrics to académie mean so axes are comparable (1.0 = average)
            metrics = ["ETP enseignants", "% Femmes", "% Non-titulaires", "% Anc. ≥8 ans"]
            acad_means = [
                peer["etp_enseignants"].mean(),
                peer_pct["pct_femmes"].mean() if len(peer_pct) else None,
                peer_pct["pct_non_titulaires"].mean() if len(peer_pct) else None,
                peer_pct["pct_anciennete_8_ans_plus"].mean() if len(peer_pct) else None,
            ]
            school_vals = [
                row["etp_enseignants"] if has_etp_row else None,
                row["pct_femmes"] if has_pct_row else None,
                row["pct_non_titulaires"] if has_pct_row else None,
                row["pct_anciennete_8_ans_plus"] if has_pct_row else None,
            ]
            # Keep only axes where both values exist
            valid = [(m, sv, am) for m, sv, am in zip(metrics, school_vals, acad_means)
                     if sv is not None and am is not None and am > 0]
            if valid:
                theta, school_r, acad_r = zip(*[(m, sv / am, 1.0) for m, sv, am in valid])
                theta = list(theta) + [theta[0]]  # close the polygon
                school_r = list(school_r) + [school_r[0]]
                acad_r   = [1.0] * len(theta)
                radar_fig = go.Figure()
                radar_fig.add_trace(go.Scatterpolar(
                    r=acad_r, theta=theta, fill="toself", name=f"Académie {acad}",
                    line_color=C["teal"], fillcolor=f"{C['teal']}22",
                ))
                radar_fig.add_trace(go.Scatterpolar(
                    r=school_r, theta=theta, fill="toself", name=row["nom_etablissement"],
                    line_color=C["yellow"], fillcolor=f"{C['yellow']}33",
                ))
                radar_fig.update_layout(
                    polar=dict(
                        bgcolor=C["card"],
                        radialaxis=dict(visible=True, range=[0, 2], tickvals=[0.5, 1, 1.5],
                                        ticktext=["0.5×", "moy.", "1.5×"],
                                        gridcolor=C["border"], linecolor=C["border"],
                                        tickfont_color=C["gray"]),
                        angularaxis=dict(gridcolor=C["border"], linecolor=C["border"],
                                         tickfont_color=C["white"]),
                    ),
                    showlegend=True, height=380,
                    paper_bgcolor="rgba(0,0,0,0)", font_color=C["white"],
                    legend=dict(bgcolor="rgba(0,0,0,0)", font_color=C["white"]),
                    margin=dict(l=60, r=60, t=40, b=40),
                )
                st.plotly_chart(radar_fig, use_container_width=True)



            ctx_cols = st.columns(4)
            ctx_cols[0].metric("ETP moy. académie",    f"{peer['etp_enseignants'].mean():.1f}",
                               delta=f"{row['etp_enseignants'] - peer['etp_enseignants'].mean():.1f}")
            if len(peer_pct):
                ctx_cols[1].metric("% Femmes académie",   f"{peer_pct['pct_femmes'].mean():.1f}%",
                                   delta=f"{(row['pct_femmes'] - peer_pct['pct_femmes'].mean()):.1f}pp" if has_pct_row else None)
                ctx_cols[2].metric("% Non-tit. académie", f"{peer_pct['pct_non_titulaires'].mean():.1f}%",
                                   delta=f"{(row['pct_non_titulaires'] - peer_pct['pct_non_titulaires'].mean()):.1f}pp" if has_pct_row else None)
                ctx_cols[3].metric("% ≥8 ans académie",   f"{peer_pct['pct_anciennete_8_ans_plus'].mean():.1f}%",
                                   delta=f"{(row['pct_anciennete_8_ans_plus'] - peer_pct['pct_anciennete_8_ans_plus'].mean()):.1f}pp" if has_pct_row else None)

    else:
        st.markdown(f"<p style='color:{C['gray']};font-size:.9rem;margin-top:16px'>Sélectionnez un établissement pour afficher son profil complet et le comparer à son académie.</p>",
                    unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown(f"""<div style="text-align:center;padding:36px 0 20px;color:{C["gray"]};
  font-size:.75rem;border-top:1px solid {C["border"]};margin-top:24px">
  Données : Ministère de l'Éducation Nationale — data.education.gouv.fr · Rentrée 2024<br>
  <span style="color:{C["yellow"]};font-weight:800">DATACK</span> × Proxymite
</div>""", unsafe_allow_html=True)
