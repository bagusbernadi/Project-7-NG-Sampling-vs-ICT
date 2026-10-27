"""Dashboard Streamlit (data SIMULASI): ringkasan, jalur uji, kondisi produksi, simulasi aturan skip.
Hanya membaca CSV di results/ (streamlit run app.py)."""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RES = Path(__file__).resolve().parents[3] / "results"
P, A_ = RES / "3-presentation", RES / "2-analysis"
NAMES = {"ic_lot": "Lot IC", "pcb_lot": "Lot PCB", "conn_lot": "Lot konektor", "smt_op": "Operator SMT", "smt_line": "Lini SMT", "shift": "Shift"}
st.set_page_config(page_title="NG Sampling vs ICT", layout="wide")


@st.cache_data
def load():
    r = lambda n, **k: pd.read_csv(P / n, **k)
    return (r("dash_conditions.csv"), r("dash_daily.csv", parse_dates=["date"]), r("dash_weekly.csv"), r("dash_path.csv"), r("dash_mode.csv"), r("dash_hypotheses.csv"),
            r("dash_cross.csv"), r("dash_threshold_sim.csv"), pd.read_csv(A_ / "daily_lag_corr.csv"))


cd, daily, wk, pth, mode, hyp, cross, sim, lag = load()
page = st.sidebar.radio("Halaman", ["Ringkasan", "Jalur uji", "Kondisi produksi", "Simulasi aturan skip"])
st.title("Project 7: NG Sampling vs ICT")
st.caption("Data SIMULASI board 8-layer (bukan data pabrik). Waktu ICT dan volume per bulan adalah asumsi. Pola belum tentu penyebab.")
sk, ic = pth.set_index("jalur").loc["Skip"], pth.set_index("jalur").loc["ICT"]

if page == "Ringkasan":
    c = st.columns(4)
    c[0].metric("NG rate FCT unit di-skip", f"{sk.ng_rate:.1%}")
    c[1].metric("NG rate FCT unit lolos ICT", f"{ic.ng_rate:.1%}")
    c[2].metric("Risiko relatif (di-skip / ICT)", f"{sk.relative_risk:.2f}")
    c[3].metric("p (uji Fisher)", f"{sk.p_fisher:.1e}")
    st.subheader("Hipotesis")
    st.dataframe(hyp[["id", "hipotesis", "verdict", "bukti"]], hide_index=True)

elif page == "Jalur uji":
    c = st.columns(2)
    with c[0]:
        fig = go.Figure(go.Bar(x=["Lolos ICT", "Di-skip"], y=[ic.ng_rate, sk.ng_rate], error_y=dict(type="data", symmetric=False, array=[ic.ci_high - ic.ng_rate, sk.ci_high - sk.ng_rate], arrayminus=[ic.ng_rate - ic.ci_low, sk.ng_rate - sk.ci_low]), marker_color=["#1a73e8", "#e37400"]))
        fig.update_layout(height=320, yaxis_tickformat=".1%", yaxis_title="NG rate FCT (CI 95%)", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")
    with c[1]:
        m = mode.set_index("jalur")
        st.dataframe(mode.rename(columns={"vd": "Voltage drop", "lc": "Leakage current", "porsi_vd": "porsi VD"})[["jalur", "ng", "Voltage drop", "Leakage current", "porsi VD"]], hide_index=True)
        st.dataframe(cross.rename(columns={"ict_result": "hasil ICT", "n": "unit", "porsi_fct_ng": "porsi NG di FCT"})[["hasil ICT", "OK", "NG", "unit", "porsi NG di FCT"]], hide_index=True)
    d = daily[daily.fct_tested > 0]
    fig = go.Figure([go.Scatter(x=d.date, y=d.ict_ok_rate, name="ICT OK rate"), go.Scatter(x=d.date, y=d.fct_ok_rate, name="FCT OK rate")])
    fig.update_layout(height=300, yaxis_tickformat=".0%", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Korelasi OK rate harian ICT dan FCT: hari sama r = {lag.korelasi[0]:.2f}, jeda 1 hari r = {lag.korelasi[1]:.2f}. Unit diuji FCT di hari berbeda dari ICT.")

elif page == "Kondisi produksi":
    cond = st.selectbox("Kondisi", list(NAMES), format_func=NAMES.get)
    minn = st.slider("Jumlah unit minimum di-skip", 1, 200, 30)
    d = cd[cd.kondisi == cond].sort_values("ng_rate_skip")
    colors = ["#9aa0a6" if n < minn else "#1a73e8" for n in d.n_skip]
    fig = go.Figure(go.Bar(x=d.nilai, y=d.ng_rate_skip, marker_color=colors, error_y=dict(type="data", symmetric=False, array=d.ci_high - d.ng_rate_skip, arrayminus=d.ng_rate_skip - d.ci_low),
                           customdata=d.n_skip, hovertemplate="%{x}: %{y:.1%} (n=%{customdata})<extra></extra>"))
    fig.update_layout(height=340, yaxis_tickformat=".1%", yaxis_title="late NG rate (CI 95%)", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(d[["nilai", "n_skip", "ng_skip", "ng_rate_skip", "ci_low", "ci_high", "n_ict", "ng_rate_ict", "p_bonferroni"]].rename(columns={"n_skip": "unit di-skip", "ng_skip": "late NG", "ng_rate_skip": "late NG rate"}), hide_index=True)
    st.caption("Abu-abu = unit di-skip kurang dari batas minimum; tidak dijadikan dasar aturan. Lot yang berdekatan waktu bisa saling memengaruhi (perancu).")

else:
    fam = st.selectbox("Aturan berdasarkan", sorted(sim.aturan.unique()), index=2)
    T = st.select_slider("Batas late NG rate untuk boleh skip", sorted(sim.batas.unique()), value=0.03, format_func=lambda v: f"{v:.1%}")
    c = st.columns(2)
    vol = c[0].number_input("Volume unit per bulan (asumsi)", 500, 20000, 4000, 500)
    mnt = c[1].number_input("Menit ICT per unit (asumsi)", 0.5, 20.0, 3.0, 0.5)
    r = sim[(sim.aturan == fam) & (sim.batas.sub(T).abs() < 1e-9)].iloc[0]
    f = vol / 4000
    m = st.columns(4)
    m[0].metric("Unit aman skip", f"{r.porsi_unit_aman:.0%}")
    m[1].metric("Jam ICT dihemat per bulan (estimated)", f"{r.unit_ict_dihemat_per_bulan * f * mnt / 60:,.1f}")
    m[2].metric("Tambahan late NG per bulan (estimated)", f"{r.tambahan_late_ng_per_bulan * f:,.1f}")
    m[3].metric("Late NG dihindari bila ICT dialihkan (estimated)", f"{r.late_ng_dihindari_per_bulan * f:,.1f}")
    st.info(f"Late NG rate unit aman yang di-skip: {r.late_ng_rate_skip_aman:.1%} (batas {T:.1%}); rate semua unit di-skip: {r.late_ng_rate_skip_semua:.1%}. Evaluasi walk-forward pada data simulasi.")
    fig = go.Figure([go.Scatter(x=sim[sim.aturan == fam].batas, y=sim[sim.aturan == fam].unit_ict_dihemat_per_bulan * f * mnt / 60, name="Jam ICT dihemat"),
                     go.Scatter(x=sim[sim.aturan == fam].batas, y=sim[sim.aturan == fam].tambahan_late_ng_per_bulan * f, name="Tambahan late NG", yaxis="y2")])
    fig.update_layout(height=320, xaxis_tickformat=".1%", yaxis2=dict(overlaying="y", side="right"), margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h"))
    st.plotly_chart(fig, width="stretch")
