from pathlib import Path
import re
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# Research showcase
# The public app is built only from Script 9's thesis outputs. The source
# Bloomberg workbook and daily financial observations are intentionally absent.
# -----------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
ASSET_DIR = APP_DIR / "assets"

THESIS_TITLE = "Geopolitical Risk, Bitcoin, and Spillover Effects in South African Markets"
GITHUB_URL = (
    "https://github.com/ChrisCresswell/"
    "Geopolitical-Risk-Bitcoin-and-the-South-African-equity-market-testing-for-volatility-spillover"
)

st.set_page_config(
    page_title=THESIS_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Restrained academic styling; all charts and metrics refer to this thesis.
st.markdown(
    """
    <style>
      .block-container {padding-top: 2.1rem; padding-bottom: 3rem; max-width: 1440px;}
      h1, h2, h3 {letter-spacing: -0.02em;}
      .eyebrow {text-transform: uppercase; letter-spacing: .12em; font-size: .72rem;
                color: #62748a; font-weight: 700; margin-bottom: .35rem;}
      .lead {font-size: 1.07rem; line-height: 1.65; color: #425466; max-width: 980px;}
      .finding {border: 1px solid #dce4ec; border-radius: 12px; padding: 1rem 1.1rem;
                background: #fbfcfe; height: 100%;}
      .finding-label {font-size: .78rem; text-transform: uppercase; letter-spacing: .08em;
                      color: #62748a; font-weight: 700;}
      .finding-value {font-size: 1.8rem; font-weight: 750; color: #12243a; margin: .25rem 0;}
      .finding-detail {font-size: .91rem; color: #425466; line-height: 1.5;}
      .note {font-size: .86rem; color: #64748b; line-height: 1.55;}
      .section-rule {border: 0; border-top: 1px solid #e5eaf0; margin: 1.2rem 0;}
      div[data-testid="stMetric"] {background: #fbfcfe; border: 1px solid #e1e8ef;
        padding: .75rem .9rem; border-radius: 10px;}
      .footer {color: #718096; font-size: .82rem; border-top: 1px solid #e5eaf0;
               padding-top: 1rem; margin-top: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_table(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def num(value, default=float("nan")):
    """Convert an exported value to float, preserving formatted p-value text elsewhere."""
    try:
        if value is None or str(value).strip() in {"", "-", "NA", "NaN"}:
            return default
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def p_label(value):
    text = str(value).strip()
    if not text or text == "-":
        return "Not reported"
    return f"p {text}" if text.startswith("<") else f"p = {text}"


def split_estimate_p(text):
    """Parse exported display values such as '-0.0461 (<0.01)'."""
    s = str(text).strip()
    if not s or s == "-":
        return float("nan"), "Not reported"
    m = re.match(r"^\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\((.*?)\)\s*$", s)
    if not m:
        return num(s), "Not reported"
    return num(m.group(1)), p_label(m.group(2))


def image(name, caption=None):
    path = ASSET_DIR / name
    if path.exists():
        st.image(str(path), use_container_width=True)
        if caption:
            st.caption(caption)
    else:
        st.warning(f"Figure not found: {name}")


def section_title(title, subtitle=None):
    st.markdown(f"<div class='eyebrow'>Research analysis</div>", unsafe_allow_html=True)
    st.subheader(title)
    if subtitle:
        st.markdown(f"<div class='note'>{subtitle}</div>", unsafe_allow_html=True)


def show_table(df, *, height=320, hide_index=True):
    if df is None or df.empty:
        st.info("No table was exported for this section.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=hide_index, height=height)


def coefficient_bar(labels, estimates, pvalues, title, x_title):
    df = pd.DataFrame({"Term": labels, "Estimate": estimates, "Robust inference": pvalues})
    df = df.dropna(subset=["Estimate"])
    if df.empty:
        st.info("No coefficient estimates are available for this selection.")
        return
    fig = px.bar(
        df, x="Estimate", y="Term", orientation="h", text="Estimate",
        hover_data={"Robust inference": True, "Estimate": ":.4f"},
    )
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b", line_width=1)
    fig.update_traces(marker_color="#315b7d", texttemplate="%{x:.4f}", textposition="outside", cliponaxis=False)
    fig.update_layout(
        title=title, xaxis_title=x_title, yaxis_title="", height=max(280, 80 * len(df)),
        margin=dict(l=15, r=55, t=55, b=35), showlegend=False,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8edf2", zeroline=False)
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(labels)))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bars show coefficient estimates; p-values are available on hover. They are not confidence intervals.")


def event_forest_plot(df, estimate_col, lower_col, upper_col, label_col, title, unit):
    if df.empty:
        st.info("No event estimates are available for this selection.")
        return
    plot = df.copy()
    for c in [estimate_col, lower_col, upper_col]:
        plot[c] = pd.to_numeric(plot[c], errors="coerce")
    plot = plot.dropna(subset=[estimate_col, lower_col, upper_col])
    if plot.empty:
        st.info("The selected event rows do not contain confidence bounds.")
        return
    plot = plot.sort_values(label_col, ascending=True)
    fig = go.Figure()
    for _, r in plot.iterrows():
        fig.add_trace(go.Scatter(
            x=[r[estimate_col]], y=[r[label_col]], mode="markers",
            marker=dict(size=8, color="#244f73"),
            error_x=dict(type="data", symmetric=False,
                         array=[r[upper_col] - r[estimate_col]],
                         arrayminus=[r[estimate_col] - r[lower_col]],
                         color="#54738f", thickness=1.5, width=4),
            name=str(r[label_col]),
            hovertemplate=(f"{r[label_col]}<br>Estimate: {r[estimate_col]:.4f}<br>"
                           f"95% interval: [{r[lower_col]:.4f}, {r[upper_col]:.4f}]<extra></extra>"),
            showlegend=False,
        ))
    fig.add_vline(x=0, line_dash="dash", line_color="#64748b", line_width=1)
    fig.update_layout(
        title=title, xaxis_title=unit, yaxis_title="", height=max(360, 48 * len(plot)),
        margin=dict(l=20, r=25, t=55, b=45), plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e8edf2", zeroline=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Points are coefficient estimates; whiskers are the 95% Newey–West confidence intervals exported by Script 9.")


def hero_footer():
    st.markdown(
        f"<div class='footer'>Joint Honours research project · Stellenbosch University · 2026<br>"
        f"For the R source code, analysis scripts and further technical detail, "
        f"refer to the <a href='{GITHUB_URL}' target='_blank'>GitHub repository</a>."
        f"</div>",
        unsafe_allow_html=True,
    )


# Sidebar navigation
with st.sidebar:
    st.markdown("### Research showcase")
    st.caption("Geopolitical risk · Bitcoin · South African equity markets")
    page = st.radio(
        "Navigate",
        [
            "Overview",
            "Data & volatility modelling",
            "Geopolitical risk & Bitcoin",
            "Bitcoin & the JSE",
            "Regimes & event studies",
            "Methodology & limitations",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("**Research source code**")
    st.markdown(f"[Open GitHub repository]({GITHUB_URL})")
    st.caption("The public showcase uses thesis output tables and figures. The original Bloomberg workbook is not included.")


if page == "Overview":
    st.markdown("<div class='eyebrow'>Interactive empirical research</div>", unsafe_allow_html=True)
    st.title(THESIS_TITLE)
    st.markdown(
        "<div class='lead'>An empirical investigation of the relationship between geopolitical risk and "
        "Bitcoin conditional volatility, and whether Bitcoin volatility provides information about "
        "volatility in the South African equity market represented by the FTSE/JSE Capped All Share Index (J303).</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    audit = load_table("data_audit.csv")
    date_start, date_end, nobs = "3 Jan 2014", "22 Jun 2026", "3,113"
    if not audit.empty:
        values = dict(zip(audit["Item"], audit["Value"]))
        date_start = values.get("Cleaned estimation sample start date", date_start)
        date_end = values.get("Cleaned estimation sample end date", date_end)
        nobs = values.get("Rows retained after complete-case cleaning", nobs)
    c1, c2, c3 = st.columns(3)
    c1.metric("Research period", f"{date_start} – {date_end}")
    c2.metric("Complete observations", nobs)
    c3.metric("Selected volatility model", "EGARCH(1,1)")

    st.markdown("---")
    st.subheader("What did the research find?")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div class='finding'><div class='finding-label'>GPR → Bitcoin</div>"
            "<div class='finding-value'>−0.0461 pp</div>"
            "<div class='finding-detail'>A one-standard-deviation increase in lagged GPRD is associated with a small decrease in daily BTC conditional volatility (p &lt; 0.01). Incremental R²: 0.0006.</div></div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            "<div class='finding'><div class='finding-label'>Bitcoin ↔ J303</div>"
            "<div class='finding-value'>0.0319</div>"
            "<div class='finding-detail'>The contemporaneous BTC-volatility coefficient is positive and significant in the full-sample dynamic model (p = 0.03235). Incremental R²: 0.0014.</div></div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            "<div class='finding'><div class='finding-label'>Directional predictability</div>"
            "<div class='finding-value'>Not supported</div>"
            "<div class='finding-detail'>The Granger test does not find evidence that lagged Bitcoin volatility predicts J303 volatility (p = 0.7492).</div></div>",
            unsafe_allow_html=True,
        )
    st.write("")
    st.info(
        "Overall interpretation: the results indicate a small lagged association between geopolitical risk and Bitcoin volatility, "
        "and limited contemporaneous co-movement between Bitcoin and J303. They do not establish a stable, directional volatility spillover."
    )
    image("F04_Conditional_Volatility_Series.png", "Figure: Estimated conditional standard deviations for Bitcoin and J303.")
    st.subheader("Two connected research questions")
    q1, q2 = st.columns(2)
    q1.markdown("**1. Geopolitical risk and Bitcoin**\n\nDoes geopolitical risk provide information about Bitcoin conditional volatility after accounting for volatility persistence?")
    q2.markdown("**2. Bitcoin and the South African equity market**\n\nDoes Bitcoin conditional volatility provide additional or predictive information about J303 volatility?")
    hero_footer()


elif page == "Data & volatility modelling":
    section_title("Data and volatility modelling", "The preliminary tests and volatility models establish the time-series properties used in the empirical analysis.")
    st.subheader("Data coverage and audit")
    show_table(load_table("data_audit.csv"), height=240)
    st.subheader("Descriptive statistics")
    show_table(load_table("descriptive_statistics.csv"), height=240)
    image("F01_Returns_Panel.png", "Daily log returns for Bitcoin and the J303 index.")
    image("F02_GPR_Measures_Panel.png", "Daily geopolitical risk measures: aggregate GPRD, acts and threats.")
    st.subheader("Why use GARCH-family models?")
    st.write(
        "The preliminary tests indicate conditional heteroscedasticity in both return series. "
        "The research therefore compares standard GARCH(1,1), EGARCH(1,1) and GJR-GARCH(1,1) specifications, "
        "using Student-t innovations to accommodate the observed excess kurtosis."
    )
    st.markdown("**Candidate-model comparison**")
    show_table(load_table("garch_model_comparison.csv"), height=260)
    st.markdown("**Selected EGARCH parameter estimates**")
    show_table(load_table("egarch_parameters.csv"), height=330)
    image("F04_Conditional_Volatility_Series.png", "Estimated conditional volatility series used in the subsequent regressions.")
    st.markdown("**Final-model diagnostics**")
    diag = load_table("egarch_diagnostics.csv")
    show_table(diag, height=200)
    st.warning(
        "Diagnostic qualification: the Ljung–Box tests on standardised residuals remain significant for both series, "
        "and the Nyblom joint statistics exceed the reported 1% critical value. The squared-residual and ARCH tests "
        "do not indicate remaining ARCH effects at the 5% level. These issues are retained as model limitations."
    )
    image("F10_Standardized_Residuals_Panel.png", "Standardised residuals from the selected EGARCH models.")
    hero_footer()


elif page == "Geopolitical risk & Bitcoin":
    section_title("Geopolitical risk and Bitcoin", "The first core analysis tests whether GPR adds explanatory information about Bitcoin conditional volatility beyond its own persistence.")
    image("F05_GPR_Bitcoin_Volatility.png", "Exploratory relationship between aggregate GPRD and Bitcoin conditional volatility.")
    models = load_table("gpr_btc_models.csv")
    if not models.empty:
        sample = st.selectbox("Sample period", sorted(models["Sample"].unique(), key=lambda x: 0 if x == "Full sample" else 1), key="gpr_sample")
        sample_rows = models[models["Sample"] == sample].copy()
        options = [x for x in sample_rows["Model"].tolist() if "Dynamic" in x]
        chosen = st.selectbox("Dynamic specification", options, key="gpr_model") if options else None
        row = sample_rows[sample_rows["Model"] == chosen].iloc[0] if chosen else None
        if row is not None:
            metric_cols = st.columns(3)
            metric_cols[0].metric("Observations", row["N"])
            metric_cols[1].metric("Incremental R²", row["Delta_R2"] or "—")
            metric_cols[2].metric("Joint Newey–West p-value", p_label(row["Joint_Wald_P_Value"]))
            labels, vals, ps = [], [], []
            for lag, col, pcol in [
                ("GPRD t", "GPR_Lag0_Effect_pp_per_SD", "GPR_Lag0_NW_P_Value"),
                ("GPRD t−1", "GPR_Lag1_Effect_pp_per_SD", "GPR_Lag1_NW_P_Value"),
                ("GPRD t−2", "GPR_Lag2_Effect_pp_per_SD", "GPR_Lag2_NW_P_Value"),
            ]:
                v = num(row[col])
                if not math.isnan(v):
                    labels.append(lag); vals.append(v); ps.append(p_label(row[pcol]))
            coefficient_bar(labels, vals, ps, "GPRD lag coefficients", "Percentage-point effect per 1-SD increase in GPRD")
        show_table(sample_rows[["Model", "N", "GPR_Lag0_Effect_pp_per_SD", "GPR_Lag1_Effect_pp_per_SD", "GPR_Lag2_Effect_pp_per_SD", "GPR_Lag0_NW_P_Value", "GPR_Lag1_NW_P_Value", "GPR_Lag2_NW_P_Value", "Delta_R2", "Joint_Wald_P_Value"]], height=280)

    st.subheader("Aggregate GPR versus acts and threats")
    component = load_table("gpr_component_models.csv")
    if not component.empty:
        component_sample = st.selectbox("Component-model sample", sorted(component["Sample"].unique(), key=lambda x: 0 if x == "Full sample" else 1), key="gpr_component_sample")
        show_table(component[component["Sample"] == component_sample], height=250)

    st.subheader("Event-window estimates: GPR and Bitcoin")
    events = load_table("gpr_btc_events_21day.csv")
    if not events.empty:
        events["GPR_Measure"] = events["Event_ID"].str.extract(r"^(GPRD(?:_ACT|_THREAT)?)", expand=False)
        measures = sorted(events["GPR_Measure"].dropna().unique())
        selected_measure = st.selectbox("GPR measure", measures, key="gpr_event_measure")
        selected = events[events["GPR_Measure"] == selected_measure].copy()
        bounds = selected["CI_95_pp_per_SD"].str.extract(r"\[\s*([-+\d.eE]+)\s*,\s*([-+\d.eE]+)\s*\]")
        selected["CI_Lower"] = pd.to_numeric(bounds[0], errors="coerce")
        selected["CI_Upper"] = pd.to_numeric(bounds[1], errors="coerce")
        selected["Effect"] = pd.to_numeric(selected["GPR_Effect_pp_per_SD"], errors="coerce")
        event_forest_plot(selected, "Effect", "CI_Lower", "CI_Upper", "Peak_Date", "GPR–Bitcoin effects in 21-observation windows", "Effect on daily BTC volatility (pp per 1-SD GPR increase)")
        show_table(selected[["Peak_Date", "Event", "Correlation", "GPR_Effect_pp_per_SD", "CI_95_pp_per_SD", "NeweyWest_P_Value", "Significant"]], height=300)
    hero_footer()


elif page == "Bitcoin & the JSE":
    section_title("Bitcoin and the South African equity market", "The second core analysis tests contemporaneous and lagged BTC-volatility terms in models of J303 conditional volatility.")
    image("F06_Bitcoin_J303_Volatility.png", "Exploratory relationship between Bitcoin and J303 conditional volatility.")
    robust = load_table("btc_j303_currency_robustness.csv")
    if not robust.empty:
        st.subheader("Compare currency and sample specifications")
        sample = st.selectbox("Sample", robust["Sample"].unique().tolist(), key="btc_jse_sample")
        measure = st.selectbox("Bitcoin volatility measure", robust["Bitcoin measure"].unique().tolist(), key="btc_jse_currency")
        chosen = robust[(robust["Sample"] == sample) & (robust["Bitcoin measure"] == measure)]
        if not chosen.empty:
            r = chosen.iloc[0]
            cols = st.columns(3)
            cols[0].metric("Contemporaneous BTC coefficient", r["Bitcoin t (NW p)"].split(" (")[0])
            cols[1].metric("Incremental R²", r["Delta R2"])
            cols[2].metric("BTC → J303 Granger", r["Granger BTC-to-J303 p"])
            st.markdown("**Dynamic model summary**")
            show_table(chosen, height=150)

    st.subheader("Granger-causality tests")
    granger = load_table("granger_causality.csv")
    if not granger.empty:
        g_sample = st.selectbox("Granger-test sample", granger["Sample"].unique().tolist(), key="granger_sample")
        g_measure = st.selectbox("Granger-test BTC measure", granger["Bitcoin_Measure"].unique().tolist(), key="granger_measure")
        gsel = granger[(granger["Sample"] == g_sample) & (granger["Bitcoin_Measure"] == g_measure)]
        show_table(gsel, height=160)
        st.caption("The Granger tests use lagged values and assess predictive content. They do not establish structural causation.")
    st.subheader("Coefficient estimates for the ZAR specification")
    coefs = load_table("btc_j303_coefficients_zar.csv")
    if not coefs.empty:
        c_sample = st.selectbox("Coefficient sample", ["Full sample", "Post-2017"], key="btc_j303_coef_sample")
        estimate_col = "Full sample estimate" if c_sample == "Full sample" else "Post-2017 estimate"
        p_col = "Full sample NW p-value" if c_sample == "Full sample" else "Post-2017 NW p-value"
        labels, vals, ps = [], [], []
        for _, r in coefs.iterrows():
            labels.append(r["Term"])
            vals.append(num(r[estimate_col]))
            ps.append(p_label(r[p_col]))
        coefficient_bar(labels, vals, ps, "Dynamic BTC–J303 coefficients", "Coefficient estimate")
        show_table(coefs, height=230)
    image("F09_Bitcoin_J303_Event_Effects_21Day.png", "Bitcoin–J303 event-window coefficients and 95% Newey–West confidence intervals.")
    hero_footer()


elif page == "Regimes & event studies":
    section_title("Geopolitical-risk regimes and event studies", "The extension analyses ask whether the estimated relationships change under elevated geopolitical risk or around selected GPR peaks.")
    tab_regime, tab_events = st.tabs(["Risk regimes", "Event studies"])
    with tab_regime:
        st.subheader("Data-driven regime thresholds")
        show_table(load_table("gpr_thresholds.csv"), height=160)
        image("F07_GPR_Regimes.png", "Bitcoin conditional volatility and aggregate GPRD by lower and elevated GPR regimes.")
        regime_coeffs = load_table("gpr_regime_coefficients.csv")
        regime_fit = load_table("gpr_regime_model_fit.csv")
        if not regime_coeffs.empty:
            measure = st.selectbox("GPR measure for within-regime models", regime_coeffs["Measure"].unique().tolist(), key="regime_measure")
            st.markdown("**Dynamic coefficient estimates by regime**")
            show_table(regime_coeffs[regime_coeffs["Measure"] == measure], height=210)
            st.markdown("**Incremental model fit by regime**")
            show_table(regime_fit[regime_fit["Measure"] == measure], height=200)
        st.subheader("Formal Bitcoin–J303 regime-difference tests")
        show_table(load_table("btc_j303_regime_tests.csv"), height=180)
        st.caption("The formal tests jointly assess whether the dynamic BTC-volatility coefficients differ across lower- and elevated-GPR regimes.")
        st.subheader("GPR–Bitcoin interaction models")
        show_table(load_table("gpr_regime_interactions.csv"), height=260)
        st.subheader("Bitcoin–J303 interaction estimates")
        show_table(load_table("btc_j303_regime_interactions.csv"), height=300)
    with tab_events:
        st.subheader("GPR–Bitcoin event-window analysis")
        image("F08_GPR_Bitcoin_Event_Effects_21Day.png", "GPR–Bitcoin event-window coefficients and 95% Newey–West confidence intervals.")
        for title, filename in [
            ("Significant correlations by measure and window", "gpr_btc_event_correlation_grid.csv"),
            ("Significant Newey–West regressions by measure and window", "gpr_btc_event_regression_grid.csv"),
        ]:
            st.markdown(f"**{title}**")
            show_table(load_table(filename), height=170)
        st.subheader("Bitcoin–J303 event-window analysis")
        image("F09_Bitcoin_J303_Event_Effects_21Day.png", "Bitcoin–J303 event-window coefficients for the 10 distinct 21-observation windows.")
        summary = load_table("btc_j303_event_summary.csv")
        if not summary.empty:
            r = summary.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Specifications", r["Specifications"])
            c2.metric("Distinct windows", r["Distinct_Windows"])
            c3.metric("Significant windows", r["Significant_Distinct_Windows"])
        bevents = load_table("btc_j303_events_21day.csv")
        if not bevents.empty:
            measure_filter = st.multiselect("GPR measures selecting the window", sorted(set("; ".join(bevents["Measure"].astype(str)).replace(" ", "").split(";"))), default=[])
            filtered = bevents.copy()
            if measure_filter:
                filtered = filtered[filtered["Measure"].apply(lambda s: any(m in str(s).replace(" ", "") for m in measure_filter))]
            event_forest_plot(filtered, "BTC_Coefficient", "CI_Lower", "CI_Upper", "Event_Window", "BTC–J303 coefficients across distinct 21-observation windows", "Bitcoin-volatility coefficient")
            show_table(filtered[["Event_Window", "Peak_Date", "Measure", "N", "Correlation", "BTC_Coefficient", "CI_Lower", "CI_Upper", "NeweyWest_P_Value", "Significant", "Interpretation_Note"]], height=360)
            selected_window = st.selectbox("Inspect an event window", filtered["Event_Window"].tolist(), key="event_detail") if not filtered.empty else None
            if selected_window:
                row = filtered[filtered["Event_Window"] == selected_window].iloc[0]
                st.markdown(f"**Interpretation note:** {row.get('Interpretation_Note','') or 'No additional note recorded.'}")
                codes = [x.strip() for x in str(row.get("Event_Codes", "")).split(";") if x.strip()]
                sources = load_table("event_source_register.csv")
                if codes and not sources.empty:
                    st.markdown("**Associated audited event records**")
                    matched = sources[sources["Source_ID"].isin(codes)]
                    show_table(matched[[c for c in ["Source_ID", "Underlying_Event", "Story_Break_Date", "Primary_Source_Details"] if c in matched.columns]], height=220)
        st.caption("The 21-observation window is the primary specification. The 11- and 31-observation windows are sensitivity checks; event windows may overlap and small-window inference requires caution.")
    hero_footer()


else:  # Methodology & limitations
    section_title("Methodology and limitations", "The showcase is designed to make the analysis understandable without replacing the underlying R scripts or the full thesis.")
    st.subheader("Research design")
    st.markdown(
        """
        **Research question 1:** Does geopolitical risk provide information about Bitcoin conditional volatility?

        **Research question 2:** Does Bitcoin conditional volatility provide information about volatility in the South African equity market, represented by J303?

        The analysis estimates conditional volatility using EGARCH(1,1) specifications with Student-t innovations. The principal dynamic regressions account for persistence by including two lags of the dependent conditional-volatility series and test the additional contribution of current and lagged explanatory terms.
        """
    )
    st.subheader("Statistical methods")
    methods = [
        ("GARCH-family model selection", "Standard GARCH(1,1), EGARCH(1,1) and GJR-GARCH(1,1) are compared using log-likelihood, AIC and BIC, alongside residual diagnostics."),
        ("Newey–West inference", "Heteroscedasticity and autocorrelation-consistent covariance estimates are used for the specified regression tests."),
        ("Incremental explanatory power", "Full dynamic models are compared with restricted models containing only the relevant volatility-persistence terms."),
        ("Granger causality", "Two-lag tests assess whether lagged values of one conditional-volatility series improve prediction of the other. They do not establish structural causality."),
        ("GPR regimes", "Two-cluster k-means is used to obtain a threshold for each GPR measure. Formal interaction tests assess whether model slopes differ across regimes."),
        ("Geopolitical event windows", "Prominent peaks are identified using centred moving averages of 11, 21 and 31 trading observations; 21 observations form the primary event-window specification."),
    ]
    for heading, body in methods:
        with st.expander(heading):
            st.write(body)
    st.subheader("Limitations to keep in mind")
    limitations = [
        "The GPR index is a global, news-based measure and may not capture geopolitical risk specific to South Africa.",
        "The conditional-volatility series are estimated rather than directly observed. The regression standard errors do not fully incorporate uncertainty from estimating the EGARCH models.",
        "The selected EGARCH diagnostics indicate residual autocorrelation and parameter instability over the full sample.",
        "Bitcoin trades continuously whereas the J303 follows the JSE trading calendar. Alignment around JSE weekday holidays can produce return intervals that differ in calendar time.",
        "The event windows may overlap, can contain multiple geopolitical stories and involve multiple related specifications. Event associations should not automatically be attributed to a single event.",
        "The study focuses on Bitcoin and one South African equity index. Results may not generalise to other assets or markets, and the analysis does not establish portfolio hedging or diversification benefits.",
    ]
    for item in limitations:
        st.markdown(f"- {item}")
    st.subheader("Source code and further information")
    st.markdown(
        "For further information on the methodology, statistical analysis and implementation of this research, "
        f"refer to the [R source code and analysis scripts on GitHub]({GITHUB_URL})."
    )
    st.info("The public application package contains selected Script 9 result tables and thesis figures. The original daily workbook containing Bloomberg-derived financial data is deliberately excluded.")
    hero_footer()
