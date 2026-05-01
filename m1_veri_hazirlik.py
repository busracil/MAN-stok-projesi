"""
ENM412 – MAN Türkiye A.Ş. Stok Yönetimi Modernizasyonu
Modül 1 – Veri Hazırlığı, Zaman Serisi Özellikleri ve K-Means Kümeleme

Yazarlar : Büşra ÇİL, İrem ÇELİK, Sevde SÖZDEN
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import warnings
warnings.filterwarnings("ignore")


# ══════════════════════════════════════════════════════════════════════════════
# 1.  VERİ YÜKLEME
# ══════════════════════════════════════════════════════════════════════════════

AY_SIRALAMA = [
    "Oca-22","Şub-22","Mar-22","Nis-22","May-22","Haz-22",
    "Tem-22","Ağu-22","Eyl-22","Eki-22","Kas-22","Ara-22",
    "Oca-23","Şub-23","Mar-23","Nis-23","May-23","Haz-23",
    "Tem-23","Ağu-23","Eyl-23","Eki-23","Kas-23","Ara-23",
    "Oca-24","Şub-24","Mar-24","Nis-24","May-24","Haz-24",
    "Tem-24","Ağu-24","Eyl-24","Eki-24","Kas-24","Ara-24",
]


def _parse_tuketim(xl: pd.ExcelFile) -> pd.DataFrame:
    """
    'Tüketim Verisi' sayfasını işler.
    Dönen sütunlar:
        Parça_Kodu | Oca-22 … Ara-24  (36 aylık tüketim)
        | Toplam | Aylik_Ort | Std_Sap | Min_Ay | Max_Ay
        | Birim_Maliyet | Teslim_Sure_Gun | Siparis_Maliyeti
        | Elde_Tutma_Oran | Elde_Tutma_TL | Stoksuz_Maliyet
    """
    raw = pd.read_excel(xl, sheet_name="Tüketim Verisi", header=None)

    # Satır 0 → bölüm başlıkları (merge hücreleri), Satır 1 → gerçek başlıklar
    header_row = raw.iloc[1].tolist()

    # Sütun indekslerini bul
    col_map = {}
    ay_cols = {}
    for i, h in enumerate(header_row):
        h_str = str(h).strip()
        if h_str == "Parça Kodu":
            col_map["Parça_Kodu"] = i
        elif h_str in AY_SIRALAMA:
            ay_cols[h_str] = i
        elif "Toplam" in h_str:
            col_map["Toplam"] = i
        elif "Aylık Ort" in h_str:
            col_map["Aylik_Ort"] = i
        elif "Std. Sapma" in h_str or "Std" in h_str:
            col_map["Std_Sap"] = i
        elif "Min" in h_str:
            col_map["Min_Ay"] = i
        elif "Max" in h_str:
            col_map["Max_Ay"] = i
        elif "Birim Maliyet" in h_str:
            col_map["Birim_Maliyet"] = i
        elif "Teslim Süresi" in h_str and "gün" in h_str.lower():
            col_map["Teslim_Sure_Gun"] = i
        elif "Sipariş Maliyeti" in h_str:
            col_map["Siparis_Maliyeti"] = i
        elif "Elde Tutma" in h_str and "Oran" in h_str:
            col_map["Elde_Tutma_Oran"] = i
        elif "Elde Tutma" in h_str and "TL" in h_str:
            col_map["Elde_Tutma_TL"] = i
        elif "Stoksuz" in h_str:
            col_map["Stoksuz_Maliyet"] = i

    data = raw.iloc[2:].reset_index(drop=True)

    # Parça kodu
    df = pd.DataFrame()
    df["Parça_Kodu"] = data.iloc[:, col_map["Parça_Kodu"]].astype(str).str.strip()

    # 36 aylık tüketim
    for ay in AY_SIRALAMA:
        if ay in ay_cols:
            df[ay] = pd.to_numeric(data.iloc[:, ay_cols[ay]], errors="coerce").fillna(0)

    # Özet istatistikler ve maliyet sütunları
    for key, idx in col_map.items():
        if key != "Parça_Kodu":
            df[key] = pd.to_numeric(data.iloc[:, idx], errors="coerce")

    df = df[df["Parça_Kodu"].str.startswith("Part")].reset_index(drop=True)
    return df


def _parse_model(xl: pd.ExcelFile) -> pd.DataFrame:
    """'Model Parametreleri' sayfasını işler."""
    df = pd.read_excel(xl, sheet_name="Model Parametreleri")
    df.columns = [str(c).strip() for c in df.columns]

    rename = {
        "Parça Kodu": "Parça_Kodu",
        df.columns[1]: "Mu",          # Aylık Ort Tüketim
        df.columns[2]: "Sigma",       # Std Sapma
        df.columns[3]: "LT_gun",      # Teslim Süresi (gün)
        df.columns[4]: "LT_ay",       # Teslim Süresi (ay)
        df.columns[5]: "Birim_Maliyet",
        df.columns[6]: "Siparis_Maliyeti",
        df.columns[7]: "h",           # Elde Tutma (TL/adet/ay)
        df.columns[8]: "p",           # Stoksuz Kalma Maliyeti
        df.columns[9]: "Mu_L",        # Talep (LT) beklenti
        df.columns[10]: "Sigma_L",    # Talep (LT) std
        df.columns[11]: "SS_baslangic",
        df.columns[12]: "r_baslangic",
        df.columns[13]: "Q_baslangic",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df["Parça_Kodu"] = df["Parça_Kodu"].astype(str).str.strip()
    numeric_cols = [c for c in df.columns if c != "Parça_Kodu"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def veri_yukle(dosya_yolu: str) -> pd.DataFrame:
    """
    Tüm sayfaları birleştirir, temizler ve birleşik master DataFrame döner.

    Parametreler
    ------------
    dosya_yolu : str
        Excel (.xlsx) dosyasının yolu

    Döner
    -----
    pd.DataFrame
        Her satır bir parça, sütunlar tüketim + parametreler
    """
    xl = pd.ExcelFile(dosya_yolu)
    tuketim = _parse_tuketim(xl)
    model    = _parse_model(xl)

    master = tuketim.merge(model, on="Parça_Kodu", how="left", suffixes=("", "_mdl"))

    # Çakışan sütunları çöz: model sayfasındaki değerler öncelikli
    for col in ["Mu","Sigma","LT_gun","LT_ay","Birim_Maliyet","Siparis_Maliyeti","h","p"]:
        if col in master.columns and f"{col}_mdl" in master.columns:
            master[col] = master[col].combine_first(master[f"{col}_mdl"])
            master.drop(columns=[f"{col}_mdl"], inplace=True)

    return master


# ══════════════════════════════════════════════════════════════════════════════
# 2.  ZAMAN SERİSİ ÖZELLİK MÜHENDİSLİĞİ
# ══════════════════════════════════════════════════════════════════════════════

def zaman_serisi_ozellikler(master: pd.DataFrame) -> pd.DataFrame:
    """
    Her parça için 36 aylık tüketimden aşağıdaki özellikleri türetir:

    Lag özellikleri   : lag_1, lag_2, lag_3
    Rolling istatistik: roll3_mean, roll3_std, roll6_mean, roll6_std
    Trend             : lineer regresyon eğimi (trend_egim)
    Mevsimsellik      : 12-aylık otokorelasyon katsayısı (mevsim_kor)
    CV                : Varyasyon katsayısı (coeff_var)
    """
    ay_cols = [c for c in master.columns if c in AY_SIRALAMA]

    records = []
    for _, row in master.iterrows():
        ts = row[ay_cols].values.astype(float)
        n  = len(ts)

        # Lag
        lag1 = ts[-2] if n >= 2 else np.nan
        lag2 = ts[-3] if n >= 3 else np.nan
        lag3 = ts[-4] if n >= 4 else np.nan

        # Rolling
        roll3_mean = np.mean(ts[-3:])  if n >= 3  else np.nan
        roll3_std  = np.std(ts[-3:])   if n >= 3  else np.nan
        roll6_mean = np.mean(ts[-6:])  if n >= 6  else np.nan
        roll6_std  = np.std(ts[-6:])   if n >= 6  else np.nan

        # Trend (OLS eğimi)
        x = np.arange(n)
        if n > 1 and np.std(ts) > 0:
            trend_egim = np.polyfit(x, ts, 1)[0]
        else:
            trend_egim = 0.0

        # Mevsimsellik (lag-12 otokorelasyon)
        if n >= 13:
            mevsim_kor = np.corrcoef(ts[:-12], ts[12:])[0, 1]
        else:
            mevsim_kor = 0.0

        # CV
        mu_ts = np.mean(ts)
        coeff_var = (np.std(ts) / mu_ts) if mu_ts > 0 else 0.0

        records.append({
            "lag_1": lag1, "lag_2": lag2, "lag_3": lag3,
            "roll3_mean": roll3_mean, "roll3_std": roll3_std,
            "roll6_mean": roll6_mean, "roll6_std": roll6_std,
            "trend_egim": trend_egim,
            "mevsim_kor": mevsim_kor,
            "coeff_var": coeff_var,
        })

    ozellik_df = pd.DataFrame(records, index=master.index)
    return pd.concat([master, ozellik_df], axis=1)


# ══════════════════════════════════════════════════════════════════════════════
# 3.  K-MEANS KÜMELEMESİ
# ══════════════════════════════════════════════════════════════════════════════

KUMELEME_OZELLIKLERI = [
    "Mu", "Sigma", "coeff_var",
    "roll6_mean", "roll6_std",
    "trend_egim", "mevsim_kor",
    "LT_gun", "Birim_Maliyet",
]


def kmeans_kumele(df: pd.DataFrame,
                  k_min: int = 3,
                  k_max: int = 8,
                  random_state: int = 42) -> pd.DataFrame:
    """
    Silhouette skoru ile en iyi K değerini bulur ve Küme_ID sütunu ekler.

    Parametreler
    ------------
    df           : zaman_serisi_ozellikler() çıktısı
    k_min, k_max : denenecek küme sayısı aralığı
    random_state : tekrar üretilebilirlik

    Döner
    -----
    pd.DataFrame
        Orijinal df + 'Küme_ID' sütunu
    """
    mevcut_ozellikler = [c for c in KUMELEME_OZELLIKLERI if c in df.columns]
    X = df[mevcut_ozellikler].copy()
    X = X.fillna(X.median())

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    en_iyi_k     = k_min
    en_iyi_skor  = -1
    en_iyi_model = None

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels, sample_size=min(500, len(X_scaled)))
        if sil > en_iyi_skor:
            en_iyi_skor  = sil
            en_iyi_k     = k
            en_iyi_model = km

    df = df.copy()
    df["Küme_ID"] = en_iyi_model.predict(X_scaled)

    print(f"[K-Means] En iyi K={en_iyi_k}, Silhouette={en_iyi_skor:.4f}")
    return df, en_iyi_k


# ══════════════════════════════════════════════════════════════════════════════
# 4.  TAHMİN VERİSETİ HAZIRLAMA  (supervised learning formatı)
# ══════════════════════════════════════════════════════════════════════════════

def supervised_veri_hazirla(df: pd.DataFrame,
                             n_lag: int = 6,
                             hedef_ay_ileri: int = 1) -> pd.DataFrame:
    """
    Her parça × her zaman adımı için satır oluşturur.
    Özellikler: lag_1…lag_n, rolling istatistikler, ay/yıl dummy, Küme_ID, parametreler
    Hedef     : t + hedef_ay_ileri tüketimi

    Parametreler
    ------------
    df               : kmeans_kumele() çıktısı
    n_lag            : kaç aylık gecikmeli değer kullanılacak
    hedef_ay_ileri   : kaç ay sonrasını tahmin edeceğiz

    Döner
    -----
    pd.DataFrame  (NaN içermez)
    """
    ay_cols = [c for c in df.columns if c in AY_SIRALAMA]
    parametreler = ["LT_gun","LT_ay","Birim_Maliyet","Siparis_Maliyeti","h","p",
                    "Küme_ID","coeff_var","trend_egim","mevsim_kor"]
    parametreler = [c for c in parametreler if c in df.columns]

    records = []
    for _, row in df.iterrows():
        ts = [row[a] for a in ay_cols]
        n  = len(ts)

        for t in range(n_lag, n - hedef_ay_ileri + 1):
            rec = {"Parça_Kodu": row["Parça_Kodu"]}

            # Lag özellikleri
            for lag in range(1, n_lag + 1):
                rec[f"lag_{lag}"] = ts[t - lag]

            # Rolling
            window3 = ts[max(0, t-3):t]
            window6 = ts[max(0, t-6):t]
            rec["roll3_mean"] = np.mean(window3)
            rec["roll3_std"]  = np.std(window3)
            rec["roll6_mean"] = np.mean(window6)
            rec["roll6_std"]  = np.std(window6)

            # Zaman özellikleri
            abs_ay = t  # 0-indexed, 0=Oca-22
            rec["ay_sin"] = np.sin(2 * np.pi * (abs_ay % 12) / 12)
            rec["ay_cos"] = np.cos(2 * np.pi * (abs_ay % 12) / 12)
            rec["yil"]    = abs_ay // 12

            # Parametre özellikleri
            for p in parametreler:
                rec[p] = row[p]

            # Hedef
            rec["hedef"] = ts[t + hedef_ay_ileri - 1]
            records.append(rec)

    result = pd.DataFrame(records).dropna()
    return result


# ══════════════════════════════════════════════════════════════════════════════
# 5.  YARDIMCI: son bilinen değerler (inference için)
# ══════════════════════════════════════════════════════════════════════════════

def son_ozellik_vektoru(row: pd.Series, n_lag: int = 6) -> dict:
    """
    Tek bir parça satırından tahmin için gerekli özellik vektörünü çıkarır.
    (Eğitim pipeline'ı ile sütun sırasının aynı olması gerekir.)
    """
    ay_cols = [c for c in row.index if c in AY_SIRALAMA]
    ts = [row[a] for a in ay_cols]
    n  = len(ts)

    rec = {}
    for lag in range(1, n_lag + 1):
        rec[f"lag_{lag}"] = ts[n - lag] if n >= lag else 0.0

    window3 = ts[max(0, n-3):]
    window6 = ts[max(0, n-6):]
    rec["roll3_mean"] = np.mean(window3)
    rec["roll3_std"]  = np.std(window3)
    rec["roll6_mean"] = np.mean(window6)
    rec["roll6_std"]  = np.std(window6)

    t = n - 1
    rec["ay_sin"] = np.sin(2 * np.pi * (t % 12) / 12)
    rec["ay_cos"] = np.cos(2 * np.pi * (t % 12) / 12)
    rec["yil"]    = t // 12

    for p in ["LT_gun","LT_ay","Birim_Maliyet","Siparis_Maliyeti","h","p",
              "Küme_ID","coeff_var","trend_egim","mevsim_kor"]:
        if p in row.index:
            rec[p] = row[p]

    return rec
