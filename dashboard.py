"""
ENM412 – MAN Türkiye A.Ş. Stok Yönetimi Optimizasyonu
Streamlit Dashboard – Web Arayüzü (v2 — CSV tabanlı)

Yazarlar : Büşra ÇİL, İrem ÇELİK, Sevde SÖZDEN

Çalıştırma:
    streamlit run dashboard.py

Gereksinimler:
    pip install streamlit plotly pandas numpy
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# SAYFA YAPISI
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MAN Türkiye – Stok Optimizasyon Paneli",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CSS / TEMA
# ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main { background-color: #F8F9FC; }
    .kart {
        background: white;
        border-radius: 12px;
        padding: 24px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        text-align: center;
        border-top: 4px solid;
    }
    .kart-Q   { border-color: #1E4D8C; }
    .kart-r   { border-color: #C8102E; }
    .kart-SS  { border-color: #F39200; }
    .kart-HZ  { border-color: #00843D; }
    .kart-baslik {
        font-size: 13px; color: #666; font-weight: 600;
        letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 8px;
    }
    .kart-deger { font-size: 36px; font-weight: 800; color: #1A1A2E; line-height: 1.1; }
    .kart-alt   { font-size: 12px; color: #999; margin-top: 6px; }
    .metrik-kart {
        background: white; border-radius: 12px; padding: 18px 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07); text-align: center;
        border-top: 4px solid #1E4D8C;
    }
    .metrik-baslik { font-size: 12px; color: #666; font-weight: 600;
                     text-transform: uppercase; margin-bottom: 6px; }
    .metrik-deger  { font-size: 28px; font-weight: 800; color: #1A1A2E; }
    .metrik-model  { font-size: 11px; color: #999; margin-top: 4px; }
    .tasarruf-banner {
        background: linear-gradient(135deg, #00843D, #00A84F);
        border-radius: 12px; padding: 20px 28px; color: white;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 16px rgba(0,132,61,0.25);
    }
    .tasarruf-banner.kirmizi {
        background: linear-gradient(135deg, #C8102E, #E01535);
        box-shadow: 0 4px 16px rgba(200,16,46,0.25);
    }
    .bolum-baslik {
        font-size: 18px; font-weight: 700; color: #1A1A2E;
        border-left: 4px solid #1E4D8C; padding-left: 12px; margin: 28px 0 16px;
    }
    .chip { display: inline-block; padding: 3px 12px; border-radius: 20px;
            font-size: 12px; font-weight: 600; }
    .chip-rf  { background: #E8F0FB; color: #1E4D8C; }
    .chip-xgb { background: #FDE8EC; color: #C8102E; }
    .sidebar-brand { text-align: center; padding: 10px 0 20px; }
    .sidebar-brand h2 { color: #1E4D8C; font-size: 20px; font-weight: 800; margin: 0; }
    .sidebar-brand p  { color: #888; font-size: 12px; margin: 4px 0 0; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# VERİ YÜKLEME
# ──────────────────────────────────────────────────────────────

VERI_KLASORU = Path(".")

@st.cache_data(show_spinner="Veriler yükleniyor…")
def verileri_yukle():
    """CSV çıktı dosyalarını yükler ve önbelleğe alır."""

    dosyalar = {
        "parametreler":  "parca_parametreleri.csv",
        "tuketim_uzun":  "tuketim_uzun.csv",
        "tuketim_genis": "tuketim_genis.csv",
        "tahmin":        "tahmin_sonuclari.csv",
        "performans":    "model_performans.csv",
        "baz_hat":       "simulasyon_sonuclari.csv",
        "karsilastirma": "karsilastirma_raporu.csv",
    }

    eksik = []
    veri  = {}
    for anahtar, dosya in dosyalar.items():
        yol = VERI_KLASORU / dosya
        if yol.exists():
            df = pd.read_csv(yol)
            if "tarih" in df.columns:
                df["tarih"] = pd.to_datetime(df["tarih"])
            veri[anahtar] = df
        else:
            eksik.append(dosya)
            veri[anahtar] = pd.DataFrame()

    return veri, eksik


# ──────────────────────────────────────────────────────────────
# SİDEBAR
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>🏭 MAN Türkiye A.Ş.</h2>
        <p>ENM412 – Stok Yönetimi Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    veri, eksik_dosyalar = verileri_yukle()

    if eksik_dosyalar:
        st.warning(f"⚠️ Eksik dosyalar:\n" + "\n".join(f"- {d}" for d in eksik_dosyalar))
        st.info("Önce modülleri sırayla çalıştırın:\n"
                "`python 01_veri_yukle.py`\n"
                "`python 02_talep_tahmini.py`\n"
                "`python 03_simulasyon.py`\n"
                "`python 04_optimizasyon.py`")
    else:
        n_parca = len(veri["parametreler"])
        st.success(f"✅ {n_parca:,} parça yüklendi")

    st.subheader("🔍 Ürün Seçimi")
    tum_parcalar = sorted(veri["parametreler"]["parca_no"].tolist()) \
                   if not veri["parametreler"].empty else []
    product_id = st.selectbox("Parça Seçin", tum_parcalar, index=0) \
                 if tum_parcalar else None

    st.divider()
    st.caption("Büşra ÇİL · İrem ÇELİK · Sevde SÖZDEN")
    st.caption("ENM412 – Endüstri Mühendisliğinde Tasarım I")


# ──────────────────────────────────────────────────────────────
# BAŞLIK
# ──────────────────────────────────────────────────────────────

st.markdown("""
<h1 style='color:#1A1A2E; font-size:28px; font-weight:800; margin-bottom:4px;'>
    🏭 Stok Yönetimi Optimizasyon Paneli
</h1>
<p style='color:#666; font-size:14px; margin-bottom:0;'>
    MAN Türkiye A.Ş. | ENM412 Tasarım Projesi | ML + SimPy Hibrit Sistemi
</p>
""", unsafe_allow_html=True)

st.divider()

if not product_id:
    st.info("Lütfen sol panelden bir parça seçin ve önce tüm modülleri çalıştırın.")
    st.stop()

# ──────────────────────────────────────────────────────────────
# SEÇİLİ PARÇA VERİSİ
# ──────────────────────────────────────────────────────────────

param_satir = veri["parametreler"][veri["parametreler"]["parca_no"] == product_id]
kar_satir   = veri["karsilastirma"][veri["karsilastirma"]["parca_no"] == product_id] \
              if not veri["karsilastirma"].empty else pd.DataFrame()
baz_satir   = veri["baz_hat"][veri["baz_hat"]["parca_no"] == product_id] \
              if not veri["baz_hat"].empty else pd.DataFrame()
tahmin_satir= veri["tahmin"][veri["tahmin"]["parca_no"] == product_id] \
              if not veri["tahmin"].empty else pd.DataFrame()
tuketim_parca = veri["tuketim_uzun"][veri["tuketim_uzun"]["parca_no"] == product_id] \
                if not veri["tuketim_uzun"].empty else pd.DataFrame()

# Şampiyon model
sampiyon_model = "—"
if not veri["performans"].empty:
    perf = veri["performans"]
    sampiyon_idx = perf["mae"].idxmin() if "mae" in perf.columns else 0
    sampiyon_model = perf.loc[sampiyon_idx, "model"] if "model" in perf.columns else "RF"
    sampiyon_model = "RF" if "Random" in str(sampiyon_model) else "XGB"

aylik_ort = float(param_satir["aylik_ort"].values[0]) if not param_satir.empty else 0

# Parça başlık satırı
col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1, 1, 1])
with col_h1:
    st.markdown(f"### 📦 {product_id}")
with col_h2:
    chip_cls = "chip-rf" if sampiyon_model == "RF" else "chip-xgb"
    st.markdown(f'<span class="chip {chip_cls}">Model: {sampiyon_model}</span>',
                unsafe_allow_html=True)
with col_h3:
    tedarik = int(param_satir["tedarik_suresi"].values[0]) if not param_satir.empty else 0
    st.markdown(f'<span class="chip chip-rf">Tedarik: {tedarik} gün</span>',
                unsafe_allow_html=True)
with col_h4:
    st.markdown(f"Ort. Talep: **{aylik_ort:,.0f}** adet/ay")


# ──────────────────────────────────────────────────────────────
# BÖLÜM 0: MODEL PERFORMANS METRİKLERİ (MAE / RMSE / MAPE)
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="bolum-baslik">🎯 Model Performans Metrikleri (Backtesting)</div>',
            unsafe_allow_html=True)

if not veri["performans"].empty:
    perf_df = veri["performans"]
    rf_row  = perf_df[perf_df["model"].str.contains("Random|RF", case=False, na=False)]
    xgb_row = perf_df[perf_df["model"].str.contains("XGB|XGBoost", case=False, na=False)]

    def metrik_al(df, sutun):
        return float(df[sutun].values[0]) if not df.empty and sutun in df.columns else 0

    rf_mae   = metrik_al(rf_row,  "mae")
    rf_rmse  = metrik_al(rf_row,  "rmse")
    rf_mape  = metrik_al(rf_row,  "mape")
    xgb_mae  = metrik_al(xgb_row, "mae")
    xgb_rmse = metrik_al(xgb_row, "rmse")
    xgb_mape = metrik_al(xgb_row, "mape")

    # Şampiyon hangisi?
    rf_sampiyon  = rf_mae  <= xgb_mae
    xgb_sampiyon = not rf_sampiyon
    rf_label  = "🏆 Random Forest" if rf_sampiyon  else "Random Forest"
    xgb_label = "🏆 XGBoost"       if xgb_sampiyon else "XGBoost"

    # 6 metrik kartı
    mc = st.columns(6)
    metrikler = [
        (rf_label,  "MAE",    rf_mae,   "#1E4D8C"),
        (rf_label,  "RMSE",   rf_rmse,  "#1E4D8C"),
        (rf_label,  "MAPE",   rf_mape,  "#1E4D8C"),
        (xgb_label, "MAE",    xgb_mae,  "#C8102E"),
        (xgb_label, "RMSE",   xgb_rmse, "#C8102E"),
        (xgb_label, "MAPE",   xgb_mape, "#C8102E"),
    ]
    for i, (model, metrik, deger, renk) in enumerate(metrikler):
        with mc[i]:
            fmt = f"%{deger:.1f}" if metrik == "MAPE" else f"{deger:,.2f}"
            st.markdown(f"""
            <div class="metrik-kart" style="border-top-color:{renk};">
                <div class="metrik-baslik">{metrik}</div>
                <div class="metrik-deger" style="color:{renk};">{fmt}</div>
                <div class="metrik-model">{model}</div>
            </div>
            """, unsafe_allow_html=True)

    # Karşılaştırma bar grafiği
    st.markdown("<br>", unsafe_allow_html=True)
    fig_perf = go.Figure()
    metrik_isimler = ["MAE", "RMSE", "MAPE (%)"]
    rf_vals  = [rf_mae,  rf_rmse,  rf_mape]
    xgb_vals = [xgb_mae, xgb_rmse, xgb_mape]

    x = np.arange(len(metrik_isimler))
    fig_perf.add_trace(go.Bar(
        name="Random Forest" + (" 🏆" if rf_sampiyon else ""),
        x=metrik_isimler, y=rf_vals,
        marker_color="#1E4D8C", opacity=0.85,
        text=[f"{v:,.2f}" for v in rf_vals], textposition="outside",
    ))
    fig_perf.add_trace(go.Bar(
        name="XGBoost" + (" 🏆" if xgb_sampiyon else ""),
        x=metrik_isimler, y=xgb_vals,
        marker_color="#C8102E", opacity=0.85,
        text=[f"{v:,.2f}" for v in xgb_vals], textposition="outside",
    ))
    fig_perf.update_layout(
        barmode="group", height=320,
        plot_bgcolor="white", paper_bgcolor="white",
        yaxis=dict(gridcolor="#F0F0F0", title="Hata Değeri"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.01),
        margin=dict(l=10, r=10, t=20, b=10),
    )
    st.plotly_chart(fig_perf, use_container_width=True)
else:
    st.info("Model performans verisi bulunamadı. `02_talep_tahmini.py` çalıştırıldı mı?")


# ──────────────────────────────────────────────────────────────
# BÖLÜM 1: TÜKETİM GEÇMİŞİ & TAHMİN GRAFİĞİ
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="bolum-baslik">📈 Tüketim Geçmişi & Gelecek Dönem Tahmini</div>',
            unsafe_allow_html=True)

if not tuketim_parca.empty:
    tuketim_sirali = tuketim_parca.sort_values("tarih")
    gecmis_tarih   = tuketim_sirali["tarih"].dt.strftime("%Y-%m").tolist()
    gecmis_vals    = tuketim_sirali["tuketim"].tolist()

    # Tahmin değerleri
    if not tahmin_satir.empty:
        tahmin_sirali = tahmin_satir.sort_values("tahmin_tarihi")
        tahmin_tarih  = pd.to_datetime(tahmin_sirali["tahmin_tarihi"]).dt.strftime("%Y-%m").tolist()
        tahmin_vals   = tahmin_sirali["tahmin"].tolist()
    else:
        tahmin_tarih = []
        tahmin_vals  = []

    # RMSE bant için
    rmse_bant = xgb_rmse if not xgb_sampiyon else rf_rmse if not veri["performans"].empty else 0

    fig1 = go.Figure()

    # Geçmiş
    fig1.add_trace(go.Scatter(
        x=gecmis_tarih, y=gecmis_vals,
        name="Gerçek Tüketim",
        line=dict(color="#1E4D8C", width=2.5),
        mode="lines+markers", marker=dict(size=4),
        hovertemplate="%{x}: <b>%{y:,.0f} adet</b><extra></extra>",
    ))

    if tahmin_tarih:
        # Bağlantı
        fig1.add_trace(go.Scatter(
            x=[gecmis_tarih[-1], tahmin_tarih[0]],
            y=[gecmis_vals[-1],  tahmin_vals[0]],
            mode="lines", line=dict(color="#C8102E", width=2, dash="dot"),
            showlegend=False, hoverinfo="skip",
        ))

        # Güven bandı
        ust = [max(0, t + rmse_bant) for t in tahmin_vals]
        alt = [max(0, t - rmse_bant) for t in tahmin_vals]
        fig1.add_trace(go.Scatter(
            x=tahmin_tarih + tahmin_tarih[::-1],
            y=ust + alt[::-1],
            fill="toself", fillcolor="rgba(200,16,46,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            name="±RMSE Güven Bandı", hoverinfo="skip",
        ))

        # Tahmin
        fig1.add_trace(go.Scatter(
            x=tahmin_tarih, y=tahmin_vals,
            name=f"Tahmin ({sampiyon_model})",
            line=dict(color="#C8102E", width=3, dash="dash"),
            mode="lines+markers", marker=dict(size=8, symbol="diamond"),
            hovertemplate="%{x}: <b>%{y:,.0f} adet</b><extra></extra>",
        ))

        # Ayrım çizgisi
        fig1.add_vline(x=gecmis_tarih[-1], line_width=1.5,
                       line_dash="dot", line_color="#999")
        fig1.add_annotation(
            x=gecmis_tarih[-1], y=max(gecmis_vals) * 1.05,
            text="Tahmin Başlangıcı →", showarrow=False,
            font=dict(size=11, color="#666"), xanchor="left",
        )

    fig1.update_layout(
        height=360, margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        xaxis=dict(showgrid=False, tickangle=-40, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0",
                   title="Tüketim (adet)", tickformat=","),
        hoverlabel=dict(bgcolor="white", font_size=13),
    )
    st.plotly_chart(fig1, use_container_width=True)
else:
    st.info("Seçilen parça için tüketim verisi bulunamadı.")


# ──────────────────────────────────────────────────────────────
# BÖLÜM 2: OPTİMAL POLİTİKA KARTLARI
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="bolum-baslik">📦 Stok Politikası Parametreleri: Mevcut vs Önerilen</div>',
            unsafe_allow_html=True)

kart_html = """
<div class="kart kart-{cls}">
    <div class="kart-baslik">{baslik}</div>
    <div class="kart-deger">{deger}</div>
    <div class="kart-alt">{alt}</div>
</div>
"""

if not param_satir.empty and not kar_satir.empty:
    mevcut_r = int(param_satir["mevcut_r"].values[0])
    mevcut_Q = int(param_satir["mevcut_Q"].values[0])
    mevcut_SS= int(param_satir["mevcut_SS"].values[0])
    opt_r    = int(kar_satir["onerilen_r"].values[0])
    opt_Q    = int(kar_satir["onerilen_Q"].values[0])
    hizmet   = float(kar_satir["servis_seviyesi"].values[0]) * 100
    ort_stok = float(kar_satir["ortalama_stok"].values[0]) if "ortalama_stok" in kar_satir.columns else 0

    # EOQ emniyet stoğu
    aylik_std  = float(param_satir["aylik_std"].values[0]) if "aylik_std" in param_satir.columns else 0
    tedarik_ay = tedarik / 21
    opt_SS     = max(int(round(1.65 * aylik_std * np.sqrt(tedarik_ay))), 0)

    # Önerilen sistem kartları
    st.markdown("<div style='font-size:13px;font-weight:700;color:#666;margin-bottom:8px;'>📦 ÖNERİLEN SİSTEM (ML + Grid Search + SimPy)</div>",
                unsafe_allow_html=True)
    kc1, kc2, kc3, kc4 = st.columns(4)
    with kc1:
        st.markdown(kart_html.format(cls="Q", baslik="Sipariş Miktarı (Q*)",
            deger=f"{opt_Q:,}", alt="adet / sipariş"), unsafe_allow_html=True)
    with kc2:
        st.markdown(kart_html.format(cls="r", baslik="Yeniden Sipariş Noktası (r*)",
            deger=f"{opt_r:,}", alt="adet (ROP)"), unsafe_allow_html=True)
    with kc3:
        st.markdown(kart_html.format(cls="SS", baslik="Emniyet Stoğu (SS*)",
            deger=f"{opt_SS:,}", alt="adet (z = 1.65)"), unsafe_allow_html=True)
    with kc4:
        st.markdown(kart_html.format(cls="HZ", baslik="Hizmet Düzeyi",
            deger=f"{hizmet:.1f}%", alt="simülasyon çıktısı"), unsafe_allow_html=True)

    # Mevcut sistem kartları
    st.markdown("<br><div style='font-size:13px;font-weight:700;color:#666;margin-bottom:8px;'>📋 MEVCUT SİSTEM (EOQ bazlı, sezgisel)</div>",
                unsafe_allow_html=True)
    km1, km2, km3, km4 = st.columns(4)
    with km1:
        st.markdown(kart_html.format(cls="Q", baslik="Mevcut Sipariş Miktarı (Q₀)",
            deger=f"{mevcut_Q:,}", alt="adet / sipariş"), unsafe_allow_html=True)
    with km2:
        st.markdown(kart_html.format(cls="r", baslik="Mevcut Yeniden Sipariş (r₀)",
            deger=f"{mevcut_r:,}", alt="adet (ROP)"), unsafe_allow_html=True)
    with km3:
        st.markdown(kart_html.format(cls="SS", baslik="Mevcut Emniyet Stoğu",
            deger=f"{mevcut_SS:,}", alt="adet"), unsafe_allow_html=True)
    with km4:
        st.markdown(kart_html.format(cls="HZ", baslik="Ort. Stok Seviyesi",
            deger=f"{ort_stok:,.0f}", alt="adet (simülasyon)"), unsafe_allow_html=True)
else:
    st.info("Optimizasyon verisi bulunamadı. `04_optimizasyon.py` çalıştırıldı mı?")


# ──────────────────────────────────────────────────────────────
# BÖLÜM 3: TASARRUF BANNER
# ──────────────────────────────────────────────────────────────

if not kar_satir.empty:
    tasarruf_tl   = float(kar_satir["maliyet_tasarrufu"].values[0])  if "maliyet_tasarrufu" in kar_satir.columns else 0
    tasarruf_oran = float(kar_satir["tasarruf_orani"].values[0])     if "tasarruf_orani"     in kar_satir.columns else 0
    yeni_maliyet  = float(kar_satir["optimize_maliyet"].values[0])   if "optimize_maliyet"   in kar_satir.columns else 0
    mevcut_mal    = float(kar_satir["mevcut_maliyet"].values[0])     if "mevcut_maliyet"     in kar_satir.columns else 0

    st.markdown("")
    if tasarruf_tl >= 0:
        banner_cls, banner_icon, banner_text = "", "✅", "Dönemsel Tasarruf"
    else:
        banner_cls, banner_icon, banner_text = "kirmizi", "⚠️", "Maliyet Artışı"

    st.markdown(f"""
    <div class="tasarruf-banner {banner_cls}" style="margin-top:20px;">
        <div>
            <div style="font-size:14px; opacity:0.85;">{banner_icon} {banner_text}</div>
            <div style="font-size:34px; font-weight:900;">{abs(tasarruf_tl):,.2f} TL</div>
            <div style="font-size:13px; opacity:0.75;">
                Mevcut: {mevcut_mal:,.0f} → Önerilen: {yeni_maliyet:,.0f} TL
            </div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:13px; opacity:0.85;">Tasarruf Oranı</div>
            <div style="font-size:48px; font-weight:900;">{abs(tasarruf_oran):.1f}%</div>
            <div style="font-size:12px; opacity:0.75;">Simülasyon dönemi ({90} iş günü)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# BÖLÜM 4: MALİYET KARŞILAŞTIRMASI
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="bolum-baslik">💰 Maliyet Karşılaştırması: Mevcut vs Önerilen</div>',
            unsafe_allow_html=True)

if not baz_satir.empty and not kar_satir.empty:
    tab1, tab2 = st.tabs(["📋 Detaylı Tablo", "📊 Bar Grafik"])

    with tab1:
        maliyet_kalemler = {
            "Sipariş Maliyeti":   ("siparis_maliyeti_toplam", "siparis_maliyeti_toplam"),
            "Elde Tutma Maliyeti":("elde_tutma_toplam",       "elde_tutma_toplam"),
            "Stoksuz Kalma Cezası":("stoksuz_ceza_toplam",   "stoksuz_ceza_toplam"),
        }

        tablo_rows = []
        for kalem, (baz_col, opt_col) in maliyet_kalemler.items():
            baz_val = float(baz_satir[baz_col].values[0]) if baz_col in baz_satir.columns else 0
            opt_val = baz_val * (1 - abs(tasarruf_oran)/100) if "tasarruf_oran" in kar_satir.columns else 0
            tablo_rows.append({
                "Maliyet Kalemi": kalem,
                "Mevcut Sistem (TL)":   f"{baz_val:,.2f}",
                "Önerilen Sistem (TL)": f"{opt_val:,.2f}",
                "Fark (TL)":            f"{baz_val - opt_val:,.2f}",
            })

        tablo_rows.append({
            "Maliyet Kalemi": "🔷 TOPLAM",
            "Mevcut Sistem (TL)":   f"{mevcut_mal:,.2f}",
            "Önerilen Sistem (TL)": f"{yeni_maliyet:,.2f}",
            "Fark (TL)":            f"{tasarruf_tl:,.2f}",
        })

        st.dataframe(pd.DataFrame(tablo_rows), hide_index=True, use_container_width=True)

    with tab2:
        kategoriler = ["Sipariş", "Elde Tutma", "Stoksuz Kalma"]
        baz_vals_bar = [
            float(baz_satir["siparis_maliyeti_toplam"].values[0]) if "siparis_maliyeti_toplam" in baz_satir.columns else 0,
            float(baz_satir["elde_tutma_toplam"].values[0])       if "elde_tutma_toplam"       in baz_satir.columns else 0,
            float(baz_satir["stoksuz_ceza_toplam"].values[0])     if "stoksuz_ceza_toplam"     in baz_satir.columns else 0,
        ]
        oran = 1 - abs(tasarruf_oran) / 100
        opt_vals_bar = [v * oran for v in baz_vals_bar]

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="Mevcut Sistem",  x=kategoriler, y=baz_vals_bar,
                              marker_color="#1E4D8C", opacity=0.85,
                              text=[f"{v:,.0f}" for v in baz_vals_bar], textposition="outside"))
        fig2.add_trace(go.Bar(name="Önerilen Sistem", x=kategoriler, y=opt_vals_bar,
                              marker_color="#C8102E", opacity=0.85,
                              text=[f"{v:,.0f}" for v in opt_vals_bar], textposition="outside"))
        fig2.update_layout(
            barmode="group", height=380,
            plot_bgcolor="white", paper_bgcolor="white",
            yaxis=dict(title="TL", gridcolor="#F0F0F0"),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.01),
            margin=dict(l=10, r=10, t=20, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# BÖLÜM 5: PORTFÖY GENEL BAKIŞ
# ──────────────────────────────────────────────────────────────

st.markdown('<div class="bolum-baslik">📊 Portföy Genel Bakış</div>',
            unsafe_allow_html=True)

if not veri["karsilastirma"].empty:
    kar_df = veri["karsilastirma"]
    pc1, pc2, pc3 = st.columns(3)

    with pc1:
        # Şampiyon model pasta grafiği
        if not veri["performans"].empty:
            perf = veri["performans"]
            model_labels = perf["model"].tolist() if "model" in perf.columns else ["RF", "XGB"]
            mae_vals     = perf["mae"].tolist()   if "mae"   in perf.columns else [0, 0]
            fig_s = go.Figure(go.Pie(
                labels=model_labels, values=[1/v if v > 0 else 0 for v in mae_vals],
                hole=0.45,
                marker_colors=["#1E4D8C", "#C8102E"],
            ))
            fig_s.update_layout(
                title="Şampiyon Model (MAE bazlı)",
                height=280, margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
            )
            st.plotly_chart(fig_s, use_container_width=True)

    with pc2:
        # Tasarruf oranı histogramı
        if "tasarruf_orani" in kar_df.columns:
            fig_h = go.Figure(go.Histogram(
                x=kar_df["tasarruf_orani"].dropna(),
                nbinsx=30, marker_color="#00843D", opacity=0.85,
            ))
            ort_tasarruf = kar_df["tasarruf_orani"].mean()
            fig_h.add_vline(x=ort_tasarruf, line_color="black",
                            line_dash="dash", line_width=2,
                            annotation_text=f"Ort: %{ort_tasarruf:.1f}",
                            annotation_position="top right")
            fig_h.update_layout(
                title="Maliyet Tasarruf Oranı Dağılımı (%)",
                height=280, margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis_title="Tasarruf (%)", yaxis_title="Parça Sayısı",
                yaxis=dict(gridcolor="#F0F0F0"), xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_h, use_container_width=True)

    with pc3:
        # Servis seviyesi dağılımı
        if "servis_seviyesi" in kar_df.columns:
            ss_vals = kar_df["servis_seviyesi"].dropna() * 100
            fig_ss = go.Figure(go.Histogram(
                x=ss_vals, nbinsx=25, marker_color="#1E4D8C", opacity=0.85,
            ))
            fig_ss.add_vline(x=95, line_color="#C8102E",
                             line_dash="dash", line_width=2,
                             annotation_text="Hedef: %95",
                             annotation_position="top left")
            fig_ss.update_layout(
                title="Servis Seviyesi Dağılımı (%)",
                height=280, margin=dict(l=10, r=10, t=40, b=10),
                plot_bgcolor="white", paper_bgcolor="white",
                xaxis_title="Servis Seviyesi (%)", yaxis_title="Parça Sayısı",
                yaxis=dict(gridcolor="#F0F0F0"), xaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_ss, use_container_width=True)

    # Portföy özet metrikleri
    st.markdown("<br>", unsafe_allow_html=True)
    pm1, pm2, pm3, pm4, pm5 = st.columns(5)
    ozet_metrikler = [
        ("Toplam Parça",          f"{len(kar_df):,}",                                      "portföy"),
        ("Ort. Tasarruf",         f"%{kar_df['tasarruf_orani'].mean():.1f}"
                                  if 'tasarruf_orani' in kar_df.columns else "—",          "maliyet"),
        ("Toplam Tasarruf",       f"{kar_df['maliyet_tasarrufu'].sum():,.0f} TL"
                                  if 'maliyet_tasarrufu' in kar_df.columns else "—",       "toplam"),
        ("%95 Sev. Sağlayan",     f"%{(kar_df['servis_seviyesi']>=0.95).mean()*100:.0f}"
                                  if 'servis_seviyesi' in kar_df.columns else "—",         "servis"),
        ("Ort. Servis Seviyesi",  f"%{kar_df['servis_seviyesi'].mean()*100:.1f}"
                                  if 'servis_seviyesi' in kar_df.columns else "—",         "hizmet"),
    ]
    for col, (baslik, deger, _) in zip([pm1,pm2,pm3,pm4,pm5], ozet_metrikler):
        with col:
            st.metric(baslik, deger)


# ──────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────

st.divider()
st.markdown("""
<div style="text-align:center; color:#999; font-size:12px; padding:10px 0;">
    ENM412 Endüstri Mühendisliğinde Tasarım I &nbsp;|&nbsp;
    MAN Türkiye A.Ş. Stok Yönetimi Optimizasyonu &nbsp;|&nbsp;
    Büşra ÇİL · İrem ÇELİK · Sevde SÖZDEN &nbsp;|&nbsp; 2025–2026
</div>
""", unsafe_allow_html=True)
