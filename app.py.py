#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
# =====================================================================
def calculate(m, l, r, c1, c2, p, ip, I, d_cap=0.05, side="long", funding_intervals=1):
    """
    All rates/percentages are given in PERCENT (0.05 means 0.05%).
    r is the signed price change in percent (+5 = price up 5%).
    Funding fee is always charged on the opening size s1.
    """
    # Convert percentages to fractions
    r_, c1_, c2_ = r / 100, c1 / 100, c2 / 100
    I_, cap = I / 100, d_cap / 100

    # Position sizes
    s1 = m * l
    s2 = s1 * (1 + r_)

    # Commission fees
    C1 = s1 * c1_
    C2 = s2 * c2_
    t = C1 + C2

    # Premium index and funding rate (as fractions)
    pi = (p - ip) / ip
    d = I_ - pi
    f = pi + max(-cap, min(cap, d))   # f = pi + clamp(I - pi, -cap, +cap)

    # Funding fee on s1 (positive = long pays, short receives)
    F = s1 * f * funding_intervals

    # Gross and net P/L
    if side == "long":
        gross = s2 - s1
        n = gross - (t + F)
    else:
        gross = s1 - s2
        n = gross - (t - F)

    return {
        "Opening size s1": s1,
        "Closing size s2": s2,
        "Initial commission C1": C1,
        "Last commission C2": C2,
        "Total commission / trading fee t": t,
        "Premium index (%)": pi * 100,
        "Funding rate f (%)": f * 100,
        "Funding fee F (long pays +)": F,
        "Gross P/L": gross,
        "Net P/L": n,
        "ROI on margin (%)": n / m * 100,
    }

# =====================================================================
# STREAMLIT WEB ARAYÜZÜ
# =====================================================================
st.set_page_config(page_title="Futures PnL Calculator", page_icon="📈", layout="centered")

st.title("📈 Kripto Vadeli İşlemler Hesaplayıcı")
st.caption("Claude hesaplama motoru entegre Streamlit arayüzü.")

# Yan Panel: Parametre Girişleri
st.sidebar.header("⚙️ Pozisyon Parametreleri")

side = st.sidebar.selectbox("Pozisyon Yönü (Side)", ["long", "short"], index=0)
m = st.sidebar.number_input("Margin (m) [USDT]", min_value=1.0, value=500.0, step=50.0)
l = st.sidebar.slider("Leverage (l)", min_value=1.0, max_value=125.0, value=10.0, step=1.0)
r = st.sidebar.number_input("Price Change r (%) [Örn: Kâr için 4.0, Düşüş için -2.0]", value=4.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("Komisyon Oranları (%)")

col_c1, col_c2 = st.sidebar.columns(2)
with col_c1:
    c1_type = st.selectbox("Açılış Emri", ["Maker (%0.02)", "Taker (%0.05)", "Özel"])
    if c1_type == "Maker (%0.02)":
        c1 = 0.02
    elif c1_type == "Taker (%0.05)":
        c1 = 0.05
    else:
        c1 = st.number_input("Açılış Komisyonu (%)", value=0.04, step=0.01)

with col_c2:
    c2_type = st.selectbox("Kapanış Emri", ["Taker (%0.05)", "Maker (%0.02)", "Özel"])
    if c2_type == "Maker (%0.02)":
        c2 = 0.02
    elif c2_type == "Taker (%0.05)":
        c2 = 0.05
    else:
        c2 = st.number_input("Kapanış Komisyonu (%)", value=0.04, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("Fonlama (Funding) Verileri")
p = st.sidebar.number_input("Perpetual Price (p) [USDT]", min_value=0.0, value=100150.0, step=10.0)
ip = st.sidebar.number_input("Index Price (iₚ) [USDT]", min_value=0.0, value=100000.0, step=10.0)
I = st.sidebar.number_input("Interest Rate I (%) per interval", value=0.01, step=0.005, format="%.4f")
d_cap = st.sidebar.number_input("Dampener Cap (%)", value=0.05, step=0.01, format="%.3f")
k = st.sidebar.number_input("Funding Intervals Held", min_value=0, max_value=30, value=1, step=1)

# Hesaplama Motorunu Çağırma
res = calculate(m=m, l=l, r=r, c1=c1, c2=c2, p=p, ip=ip, I=I, d_cap=d_cap, side=side, funding_intervals=k)

# Ana Ekran Sonuç Kartları
net_pnl = res["Net P/L"]
roi = res["ROI on margin (%)"]
pnl_color = "#16a34a" if net_pnl >= 0 else "#dc2626"

st.markdown(f"""
<div style="background-color: #0f172a; padding: 22px; border-radius: 12px; text-align: center; border: 1px solid #334155; margin-bottom: 20px;">
    <span style="color: #94a3b8; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Net Kazanç (Net P/L)</span>
    <h1 style="color: {pnl_color}; margin: 8px 0; font-size: 40px;">{net_pnl:+,.2f} USDT</h1>
    <span style="color: #e2e8f0; font-size: 16px;">Sermaye Getirisi (ROI): <b>%{roi:+,.2f}</b></span>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Açılış Hacmi (s₁)", value=f"{res['Opening size s1']:,.2f} USDT")
    st.metric(label="Toplam Komisyon (t)", value=f"{res['Total commission / trading fee t']:,.4f} USDT", 
              delta=f"C₁: {res['Initial commission C1']:.2f} | C₂: {res['Last commission C2']:.2f}", delta_color="inverse")
    st.metric(label="Brüt Kâr/Zarar (Gross)", value=f"{res['Gross P/L']:+,.2f} USDT")

with col2:
    st.metric(label="Kapanış Hacmi (s₂)", value=f"{res['Closing size s2']:,.2f} USDT")
    st.metric(label="Fonlama Ücreti (F)", value=f"{res['Funding fee F (long pays +)']:,.4f} USDT", 
              delta=f"Fonlama Oranı (f): %{res['Funding rate f (%)']:.4f}", delta_color="off")
    st.metric(label="Premium Index (pᵢ)", value=f"%{res['Premium index (%)']:.4f}")

# Claude'un Döndürdüğü Tüm Sonuçların Ham Tablosu
with st.expander("📋 Detaylı Çıktı Tablosu"):
    st.table({k: [f"{v:,.6f}"] for k, v in res.items()})

