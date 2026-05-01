"""
ENM412 – MAN Türkiye A.Ş. Stok Yönetimi Dashboard
Yazarlar: Büşra ÇİL, İrem ÇELİK, Sevde SÖZDEN

Streamlit Cloud'da çalıştırma:
    streamlit run dashboard.py
"""

import sys
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

from m1_veri_hazirlik import AY_SIRALAMA, GELECEK_AYLAR

# ══════════════════════════════════════════════════════════════════════════════
# SAYFA YAPISI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MAN Türkiye – Stok Optimizasyon Paneli",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
.main { background-color: #F8F9FC; }

.kart {
    background: white;
    border-radius: 12px;
    padding: 20px 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    text-align: center;
    border-top: 4px solid;
    margin-bottom: 8px;
}
.kart-Q   { border-color: #1E4D8C; }
.kart-r   { border-color: #C8102E; }
.kart-SS  { border-color: #F39200; }
.kart-HZ  { border-color: #00843D; }
.kart-baslik { font-size:12px; color:#666; font-weight:600;
               text-transform:uppercase; margin-bottom:6px; }
.kart-deger  { font-size:32px; font-weight:800; color:#1A1A2E; line-height:1.1; }
.kart-alt    { font-size:11px; color:#999; margin-top:4px; }

.aksiyon-kirmizi { background:#FEE2E2; border-left:4px solid #C8102E;
                   padding:12px 16px; border-radius:8px; color:#991B1B;
                   font-weight:600; margin:12px 0; }
.aksiyon-sari    { background:#FEF9C3; border-left:4px solid #F39200;
                   padding:12px 16px; border-radius:8px; color:#92400E;
                   font-weight:600; margin:12px 0; }
.aksiyon-yesil   { background:#DCFCE7; border-left:4px solid #00843D;
                   padding:12px 16px; border-radius:8px; color:#166534;
                   font-weight:600; margin:12px 0; }

.tasarruf-banner {
    background: linear-gradient(135deg, #00843D, #00A84F);
    border-radius: 12px; padding: 20px 28px; color: white;
    display: flex; justify-content: space-between; align-items: center;
    box-shadow: 0 4px 16px rgba(0,132,61,0.25); margin: 16px 0;
}
.tasarruf-banner.kirmizi {
    background: linear-gradient(135deg, #C8102E, #E01535);
    box-shadow: 0 4px 16px rgba(200,16,46,0.25);
}
.bolum-baslik {
    font-size:17px; font-weight:700; color:#1A1A2E;
    border-left:4px solid #1E4D8C; padding-left:12px; margin:24px 0 12px;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# VERİ YÜKLEME
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Model yükleniyor…")
def yukle_sistem(cache_yolu, veri_yolu):
    p = Path(cache_yolu)
    if p.exists():
        with open(p, "rb") as f:
            return pickle.load(f)
    else:
        from m5_pipeline import pipeline_calistir
        return pipeline_calistir(veri_yolu, cache_dosyasi=cache_yolu)


@st.cache_data(show_spinner=False)
def urun_analiz(_master_df, _kume_modelleri, _parca_modelleri,
                product_id, grid_adim, n_rep):
    from m4_sorgulama import urun_sorgula
    return urun_sorgula(
        product_id      = product_id,
        master_df       = _master_df,
        kume_modelleri  = _kume_modelleri,
        parca_modelleri = _parca_modelleri,
        n_ay_tahmin     = 6,
        grid_adim       = grid_adim,
        n_rep           = n_rep,
        yazdir          = False,
    )

# ══════════════════════════════════════════════════════════════════════════════
# SİDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:10px 0 20px;'>
        <h2 style='color:#1E4D8C; font-size:20px; font-weight:800; margin:0;'>
            🏭 MAN Türkiye A.Ş.
        </h2>
        <p style='color:#888; font-size:12px; margin:4px 0 0;'>
            ENM412 Stok Yönetimi Dashboard
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("⚙️ Sistem Ayarları")
    veri_yolu  = st.text_input("Veri Dosyası", value="dummy_veri_36ay.xlsx")
    cache_yolu = st.text_input("Model Cache",   value="enm412_cache.pkl")

    try:
        sistem = yukle_sistem(cache_yolu, veri_yolu)
        st.success(f"✅ {len(sistem['master_df']):,} parça yüklendi")
    except Exception as e:
        st.error(f"Yükleme hatası: {e}")
        st.stop()

    master_df       = sistem["master_df"]
    kume_modelleri  = sistem["kume_modelleri"]
    parca_modelleri = sistem["parca_modelleri"]
    batch_df        = sistem["batch_tahmin_df"]

    st.divider()
    st.subheader("🔍 Ürün Seçimi")
    tum_parcalar = sorted(master_df["Parça_Kodu"].tolist())
    product_id   = st.selectbox("Product ID", tum_parcalar, index=0)

    st.divider()
    st.subheader("🎛️ Simülasyon Parametreleri")
    grid_adim     = st.slider("Grid Çözünürlüğü", 4, 15, 8)
    n_rep         = st.slider("Replikasyon Sayısı", 5, 30, 10)

    hesapla = st.button("🚀 Analizi Çalıştır",
                        use_container_width=True, type="primary")

    st.divider()
    st.caption("Büşra ÇİL · İrem ÇELİK · Sevde SÖZDEN")
    st.caption("ENM412 – Endüstri Mühendisliğinde Tasarım II")

# ══════════════════════════════════════════════════════════════════════════════
# ANA PANEL BAŞLIĞI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<h1 style='color:#1A1A2E; font-size:26px; font-weight:800; margin-bottom:4px;'>
    🏭 Stok Yönetimi Optimizasyon Paneli
</h1>
<p style='color:#666; font-size:13px;'>
    MAN Türkiye A.Ş. | ENM412 | RF + XGBoost + LightGBM + CatBoost + SimPy + Grid Search + Optuna
</p>
""", unsafe_allow_html=True)
st.divider()

# Parça başlığı
parca_satiri = master_df[master_df["Parça_Kodu"] == product_id].iloc[0]
kume_no      = int(parca_satiri.get("Küme_ID", 0))
batch_satiri = batch_df[batch_df["Parça_Kodu"] == product_id]
sampiyon_adi = batch_satiri["Sampiyon"].values[0] if not batch_satiri.empty else "—"

c1, c2, c3, c4 = st.columns([3,1,1,1])
with c1: st.markdown(f"### 📦 {product_id}")
with c2: st.markdown(f"**Model:** {sampiyon_adi}")
with c3: st.markdown(f"**Küme:** {kume_no}")
with c4:
    mu_val = parca_satiri.get("Mu", 0)
    st.markdown(f"**Ort. Talep:** {mu_val:,.0f} adet/ay")

# ══════════════════════════════════════════════════════════════════════════════
# TAHMİN GRAFİĞİ
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="bolum-baslik">📈 Tüketim Geçmişi & 6 Aylık Tahmin</div>',
            unsafe_allow_html=True)

gercek_vals = [float(parca_satiri.get(a, 0)) for a in AY_SIRALAMA]

if not batch_satiri.empty:
    tahmin_cols = [c for c in batch_satiri.columns if c.startswith("Tahmin_Ay_")]
    tahmin_vals = batch_satiri[tahmin_cols].values[0].tolist()
    rmse_val    = float(batch_satiri["Model_RMSE"].values[0])
else:
    tahmin_vals = [mu_val] * 6
    rmse_val    = 0

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=AY_SIRALAMA, y=gercek_vals,
    name="Gerçek Tüketim",
    line=dict(color="#1E4D8C", width=2.5),
    mode="lines+markers", marker=dict(size=4),
    hovertemplate="%{x}: <b>%{y:,.0f} adet</b><extra></extra>",
))

fig.add_trace(go.Scatter(
    x=["Ara-24", "Oca-25"],
    y=[gercek_vals[-1], tahmin_vals[0]],
    mode="lines", line=dict(color="#C8102E", width=2, dash="dot"),
    showlegend=False, hoverinfo="skip",
))

ust = [max(0, t + rmse_val) for t in tahmin_vals]
alt = [max(0, t - rmse_val) for t in tahmin_vals]
fig.add_trace(go.Scatter(
    x=GELECEK_AYLAR + GELECEK_AYLAR[::-1],
    y=ust + alt[::-1],
    fill="toself", fillcolor="rgba(200,16,46,0.08)",
    line=dict(color="rgba(0,0,0,0)"),
    name="±RMSE Güven Bandı", hoverinfo="skip",
))

fig.add_trace(go.Scatter(
    x=GELECEK_AYLAR, y=tahmin_vals,
    name=f"Tahmin ({sampiyon_adi})",
    line=dict(color="#C8102E", width=3, dash="dash"),
    mode="lines+markers", marker=dict(size=8, symbol="diamond"),
    hovertemplate="%{x}: <b>%{y:,.0f} adet</b><extra></extra>",
))

# Tahmin başlangıç çizgisi
fig.add_trace(go.Scatter(
    x=["Ara-24","Ara-24"], y=[0, max(gercek_vals)*1.1],
    mode="lines", line=dict(color="#999", width=1.5, dash="dot"),
    showlegend=False, hoverinfo="skip",
))
fig.add_annotation(
    x="Ara-24", y=max(gercek_vals)*1.05 if max(gercek_vals) > 0 else 1,
    text="Tahmin →", showarrow=False,
    font=dict(size=11, color="#666"), xanchor="left",
)

fig.update_layout(
    height=350, margin=dict(l=20,r=20,t=20,b=20),
    plot_bgcolor="white", paper_bgcolor="white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=9)),
    yaxis=dict(showgrid=True, gridcolor="#F0F0F0", title="Tüketim (adet)"),
)
st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANALİZ
# ══════════════════════════════════════════════════════════════════════════════

if hesapla or "son_analiz" not in st.session_state or \
   st.session_state.get("son_pid") != product_id:
    with st.spinner(f"🔄 {product_id} için Grid Search + Optuna + SimPy çalışıyor…"):
        try:
            analiz = urun_analiz(
                master_df, kume_modelleri, parca_modelleri,
                product_id, grid_adim, n_rep
            )
            st.session_state["son_analiz"] = analiz
            st.session_state["son_pid"]    = product_id
        except Exception as e:
            st.error(f"Analiz hatası: {e}")
            st.stop()
else:
    analiz = st.session_state["son_analiz"]

# ══════════════════════════════════════════════════════════════════════════════
# AKSİYON UYARISI
# ══════════════════════════════════════════════════════════════════════════════

renk_map = {"red": "kirmizi", "orange": "sari", "green": "yesil"}
aksiyon_cls = renk_map.get(analiz["aksiyon_renk"], "yesil")
st.markdown(f'<div class="aksiyon-{aksiyon_cls}">{analiz["aksiyon"]}</div>',
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# OPTİMAL POLİTİKA KARTLARI — SATIR 1: ÖNERİLEN
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="bolum-baslik">📦 Optimal Stok Politikası</div>',
            unsafe_allow_html=True)

opt_Q  = analiz["optimal_Q"]
opt_r  = analiz["optimal_r"]
opt_SS = analiz["optimal_SS"]
hizmet = analiz["hizmet_duzeyi"] * 100
Q_eoq  = analiz["Q_eoq"]
r_eoq  = analiz["r_eoq"]
SS_eoq = analiz["SS_eoq"]

KART = """
<div class="kart kart-{cls}">
    <div class="kart-baslik">{baslik}</div>
    <div class="kart-deger">{deger}</div>
    <div class="kart-alt">{alt}</div>
</div>
"""

st.markdown("**📦 Önerilen Sistem (ML + Grid Search + Optuna + SimPy)**")
k1, k2, k3, k4 = st.columns(4)
with k1: st.markdown(KART.format(cls="Q", baslik="Sipariş Miktarı (Q*)",
    deger=f"{opt_Q:,}", alt="adet / sipariş"), unsafe_allow_html=True)
with k2: st.markdown(KART.format(cls="r", baslik="Yeniden Sipariş Noktası (r*)",
    deger=f"{opt_r:,}", alt="adet (ROP)"), unsafe_allow_html=True)
with k3: st.markdown(KART.format(cls="SS", baslik="Emniyet Stoğu (SS*)",
    deger=f"{opt_SS:,}", alt="adet (z=1.65)"), unsafe_allow_html=True)
with k4: st.markdown(KART.format(cls="HZ", baslik="Hizmet Düzeyi",
    deger=f"%{hizmet:.1f}", alt="SimPy çıktısı"), unsafe_allow_html=True)

st.markdown("**📐 EOQ Klasik Referans**")
e1, e2, e3, e4 = st.columns(4)
with e1: st.markdown(KART.format(cls="Q", baslik="EOQ Sipariş Miktarı",
    deger=f"{Q_eoq:,}", alt="√(2SD/h)"), unsafe_allow_html=True)
with e2: st.markdown(KART.format(cls="r", baslik="EOQ Yeniden Sipariş",
    deger=f"{r_eoq:,}", alt="μ_L + 1.65·σ_L"), unsafe_allow_html=True)
with e3: st.markdown(KART.format(cls="SS", baslik="EOQ Emniyet Stoğu",
    deger=f"{SS_eoq:,}", alt="1.65 × σ_L"), unsafe_allow_html=True)
with e4: st.markdown(KART.format(cls="HZ", baslik="EOQ Hizmet Hedefi",
    deger="%95.0", alt="z = 1.65"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TASARRUF BANNER
# ══════════════════════════════════════════════════════════════════════════════

tasarruf_tl   = analiz["tasarruf_tl"]
tasarruf_oran = analiz["tasarruf_oran"]
yeni_m        = analiz["yeni_maliyet"]
mevcut_m      = analiz["mevcut_maliyet"]
banner_cls    = "" if tasarruf_tl >= 0 else "kirmizi"
banner_icon   = "✅" if tasarruf_tl >= 0 else "⚠️"
banner_text   = "Aylık Tasarruf" if tasarruf_tl >= 0 else "Maliyet Artışı"

st.markdown(f"""
<div class="tasarruf-banner {banner_cls}">
    <div>
        <div style="font-size:13px;opacity:0.85;">{banner_icon} {banner_text}</div>
        <div style="font-size:32px;font-weight:900;">{abs(tasarruf_tl):,.2f} TL/ay</div>
        <div style="font-size:12px;opacity:0.75;">
            Yıllık projeksiyon: <b>{abs(tasarruf_tl)*12:,.0f} TL</b>
        </div>
    </div>
    <div style="text-align:right;">
        <div style="font-size:13px;opacity:0.85;">Tasarruf Oranı</div>
        <div style="font-size:44px;font-weight:900;">{abs(tasarruf_oran):.1f}%</div>
        <div style="font-size:12px;opacity:0.75;">
            Mevcut: {mevcut_m:,.0f} → Yeni: {yeni_m:,.0f} TL/ay
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# MALİYET KARŞILAŞTIRMASI
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="bolum-baslik">💰 Maliyet Karşılaştırması</div>',
            unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Detaylı Tablo", "📊 Bar Grafik", "🗺️ Grid Haritası"])

with tab1:
    tablo = analiz["detay_karsilastirma"].copy()
    for c in ["Mevcut (Q0/r0)", "EOQ Klasik", "Önerilen (ML+SimPy)", "Tasarruf (TL/ay)"]:
        if c in tablo.columns:
            tablo[c] = tablo[c].apply(lambda x: f"{x:,.2f} TL")
    if "Tasarruf (%)" in tablo.columns:
        tablo["Tasarruf (%)"] = tablo["Tasarruf (%)"].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "—")
    st.dataframe(tablo, hide_index=True, use_container_width=True)

with tab2:
    df_k = analiz["detay_karsilastirma"]

    def _get(col, kw):
        r = df_k[df_k["Maliyet Kalemi"].str.contains(kw)]
        return float(r[col].values[0]) if len(r) > 0 and col in df_k.columns else 0

    kategoriler = ["Elde Tutma","Sipariş","Stoksuz Kalma"]
    kw_list     = ["Elde","Sipariş","Stoksuz"]
    col_mev     = "Mevcut (Q0/r0)"
    col_eoq     = "EOQ Klasik"
    col_yeni    = "Önerilen (ML+SimPy)"

    fig2 = go.Figure()
    renkler = {
        "mev":  ["#1E4D8C","#2D6FAE","#5B93C5"],
        "eoq":  ["#F39200","#F5A623","#F7C46A"],
        "yeni": ["#C8102E","#E01535","#F05070"],
    }

    for i, (kat, kw) in enumerate(zip(kategoriler, kw_list)):
        fig2.add_trace(go.Bar(name=f"{kat} (Mevcut)", x=["Mevcut (Q0/r0)"],
            y=[_get(col_mev, kw)], marker_color=renkler["mev"][i],
            text=f"{_get(col_mev,kw):,.0f}", textposition="inside"))
        fig2.add_trace(go.Bar(name=f"{kat} (EOQ)", x=["EOQ Klasik"],
            y=[_get(col_eoq, kw)], marker_color=renkler["eoq"][i],
            text=f"{_get(col_eoq,kw):,.0f}", textposition="inside"))
        fig2.add_trace(go.Bar(name=f"{kat} (Önerilen)", x=["ML+SimPy"],
            y=[_get(col_yeni, kw)], marker_color=renkler["yeni"][i],
            text=f"{_get(col_yeni,kw):,.0f}", textposition="inside"))

    fig2.update_layout(
        barmode="stack", height=400,
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(title="TL/ay", gridcolor="#F0F0F0"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
        margin=dict(l=10,r=10,t=10,b=10),
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    grid_df = analiz.get("grid_sonuclari", pd.DataFrame())
    if not grid_df.empty and len(grid_df) > 1:
        try:
            pivot = grid_df.pivot_table(
                index="r", columns="Q", values="ort_maliyet", aggfunc="mean")
            fig3 = px.imshow(pivot, color_continuous_scale="RdYlGn_r",
                labels=dict(x="Q (Sipariş Miktarı)", y="r (Yeniden Sipariş)",
                            color="Maliyet (TL/ay)"), aspect="auto")
            fig3.add_trace(go.Scatter(
                x=[opt_Q], y=[opt_r], mode="markers",
                marker=dict(symbol="star", size=16, color="white",
                            line=dict(color="black", width=2)),
                name="Optimal (Q*, r*)", showlegend=True,
            ))
            fig3.update_layout(height=380, margin=dict(l=10,r=10,t=30,b=10))
            st.plotly_chart(fig3, use_container_width=True)
            st.caption(f"⭐ Optimal: Q*={opt_Q:,}, r*={opt_r:,} → {yeni_m:,.2f} TL/ay")
        except Exception:
            st.info("Grid haritası bu parça için oluşturulamadı.")
    else:
        st.info("Grid verileri yükleniyor...")

# ══════════════════════════════════════════════════════════════════════════════
# PORTFÖY GENEL BAKIŞ
# ══════════════════════════════════════════════════════════════════════════════

st.markdown('<div class="bolum-baslik">📊 Portföy Genel Bakış</div>',
            unsafe_allow_html=True)

pc1, pc2 = st.columns(2)

with pc1:
    samp = batch_df["Sampiyon"].str.upper().value_counts().reset_index()
    samp.columns = ["Model","Sayı"]
    fig_s = px.pie(samp, values="Sayı", names="Model",
        title="Şampiyon Model Dağılımı",
        color="Model",
        color_discrete_map={
            "RF":"#1E4D8C","XGB":"#C8102E",
            "LGBM":"#F39200","CATBOOST":"#00843D"
        }, hole=0.45)
    fig_s.update_layout(height=280, margin=dict(l=10,r=10,t=40,b=10),
                        plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig_s, use_container_width=True)

with pc2:
    kume = master_df["Küme_ID"].value_counts().sort_index().reset_index()
    kume.columns = ["Küme","Parça Sayısı"]
    kume["Küme"] = kume["Küme"].apply(lambda x: f"Küme {x}")
    fig_k = px.bar(kume, x="Küme", y="Parça Sayısı",
        title="K-Means Küme Dağılımı",
        color="Küme", color_discrete_sequence=px.colors.qualitative.Set2)
    fig_k.update_layout(height=280, margin=dict(l=10,r=10,t=40,b=10),
                        plot_bgcolor="white", paper_bgcolor="white",
                        xaxis=dict(showgrid=False),
                        yaxis=dict(gridcolor="#F0F0F0"), showlegend=False)
    st.plotly_chart(fig_k, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.divider()
st.markdown("""
<div style="text-align:center; color:#999; font-size:12px; padding:8px 0;">
    ENM412 Endüstri Mühendisliğinde Tasarım II &nbsp;|&nbsp;
    MAN Türkiye A.Ş. &nbsp;|&nbsp;
    Büşra ÇİL · İrem ÇELİK · Sevde SÖZDEN &nbsp;|&nbsp; 2024–2025
</div>
""", unsafe_allow_html=True)
