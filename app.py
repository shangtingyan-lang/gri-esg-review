from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from gri_analyzer import DISCLOSURE_RULES, analyze_report


st.set_page_config(
    page_title="GRI ESG Report Review",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


THEME_ORDER = ["一般揭露", "重大主題", "經濟", "環境", "社會", "治理"]
STATUS_ORDER = ["未找到", "揭露不足", "部分符合", "大致符合"]
STATUS_TO_RISK = {
    "大致符合": "低",
    "部分符合": "中",
    "揭露不足": "高",
    "未找到": "高",
}
RISK_COLORS = {
    "高": "#b42318",
    "中": "#b54708",
    "低": "#027a48",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #172033;
            --muted: #667085;
            --line: #d0d5dd;
            --panel: #f8fafc;
            --blue: #1f4e79;
            --green: #027a48;
            --amber: #b54708;
            --red: #b42318;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 1480px;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        .app-kicker {
            color: var(--blue);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
        }

        .app-title {
            font-size: 2.1rem;
            font-weight: 760;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .app-subtitle {
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.6;
            max-width: 920px;
            margin-bottom: 1.2rem;
        }

        .section-label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-top: 1.2rem;
        }

        .notice {
            border: 1px solid var(--line);
            background: var(--panel);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            color: var(--ink);
            line-height: 1.65;
        }

        .risk-high { color: var(--red); font-weight: 700; }
        .risk-medium { color: var(--amber); font-weight: 700; }
        .risk-low { color: var(--green); font-weight: 700; }

        div[data-testid="stMetric"] {
            border: 1px solid var(--line);
            background: #ffffff;
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-size: 1.75rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid var(--line);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ordered_themes() -> list[str]:
    themes = {rule.theme for rule in DISCLOSURE_RULES}
    ordered = [theme for theme in THEME_ORDER if theme in themes]
    ordered.extend(sorted(themes - set(ordered)))
    return ordered


def prepare_results(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    prepared = df.copy()
    prepared["風險等級"] = prepared["狀態"].map(STATUS_TO_RISK).fillna("中")
    prepared["優先序"] = prepared["分數"].apply(
        lambda score: "P1 立即補強" if score < 50 else "P2 本期改善" if score < 80 else "P3 維持追蹤"
    )
    return prepared


def score_label(score: float) -> str:
    if score >= 80:
        return "可接受"
    if score >= 50:
        return "需補強"
    return "高風險"


def build_management_summary(df: pd.DataFrame, file_name: str) -> str:
    if df.empty:
        return "尚無分析結果。"

    overall_score = round(float(df["分數"].mean()), 1)
    high_risk = df[df["風險等級"] == "高"]
    medium_risk = df[df["風險等級"] == "中"]
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "# GRI 永續報告書檢核摘要",
        "",
        f"- 報告檔案：{file_name}",
        f"- 產出時間：{generated_at}",
        f"- 整體揭露完整度：{overall_score} / 100（{score_label(overall_score)}）",
        f"- 高風險缺口：{len(high_risk)} 項",
        f"- 中風險缺口：{len(medium_risk)} 項",
        "",
        "## 優先改善項目",
    ]

    focus = df.sort_values(["分數", "GRI項目"]).head(10)
    for _, row in focus.iterrows():
        lines.extend(
            [
                "",
                f"### {row['GRI項目']} {row['項目名稱']}",
                f"- 狀態：{row['狀態']}；分數：{row['分數']}；風險：{row['風險等級']}",
                f"- 發現頁面：{row['發現頁面']}",
                f"- 缺口：{row['缺口']}",
                f"- 建議修改：{row['建議修改']}",
            ]
        )

    return "\n".join(lines)


def render_header() -> None:
    st.markdown('<div class="app-kicker">GRI Disclosure Review</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-title">永續報告書 GRI 智能檢核平台</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="app-subtitle">'
        "上傳公司永續報告書 PDF，系統會依 GRI 揭露項目產出完整度分數、風險等級、來源頁碼、缺口說明與可執行的修改建議。"
        "</div>",
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="notice">
        <strong>開始檢核</strong><br>
        請先在左側上傳公司永續報告書 PDF，選擇要檢核的 GRI 主題與項目，再按下「開始檢核」。
        目前版本提供 GRI 2、GRI 3、GRI 201-207、GRI 301-308、GRI 401-418 的初篩檢核。
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.markdown("**1. 上傳報告書**  \n支援文字型 PDF，掃描影像 PDF 後續可再加入 OCR。")
    c2.markdown("**2. 自動對照 GRI**  \n系統逐頁保留頁碼，找出可能對應的揭露內容。")
    c3.markdown("**3. 產出改善清單**  \n輸出分數、缺口、來源頁碼與建議修正文案方向。")


def render_metrics(df: pd.DataFrame) -> None:
    overall_score = round(float(df["分數"].mean()), 1) if not df.empty else 0
    high_risk_count = int((df["風險等級"] == "高").sum()) if not df.empty else 0
    medium_risk_count = int((df["風險等級"] == "中").sum()) if not df.empty else 0
    low_risk_count = int((df["風險等級"] == "低").sum()) if not df.empty else 0

    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric("整體完整度", f"{overall_score}")
    metric_b.metric("高風險缺口", high_risk_count)
    metric_c.metric("中風險缺口", medium_risk_count)
    metric_d.metric("大致符合", low_risk_count)


def render_charts(df: pd.DataFrame) -> None:
    left, right = st.columns([1.1, 1])

    with left:
        st.markdown('<div class="section-label">Risk Distribution</div>', unsafe_allow_html=True)
        risk_counts = (
            df["風險等級"]
            .value_counts()
            .reindex(["高", "中", "低"], fill_value=0)
            .rename_axis("風險等級")
            .reset_index(name="項目數")
        )
        st.bar_chart(risk_counts, x="風險等級", y="項目數", color="#1f4e79", height=260)

    with right:
        st.markdown('<div class="section-label">Theme Average</div>', unsafe_allow_html=True)
        theme_scores = (
            df.groupby("主題", as_index=False)["分數"]
            .mean()
            .sort_values("分數", ascending=True)
        )
        st.bar_chart(theme_scores, x="主題", y="分數", color="#027a48", height=260)


def render_priority_list(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">Priority Actions</div>', unsafe_allow_html=True)
    focus = df.sort_values(["分數", "GRI項目"]).head(8)
    for _, row in focus.iterrows():
        risk_class = {
            "高": "risk-high",
            "中": "risk-medium",
            "低": "risk-low",
        }.get(row["風險等級"], "risk-medium")
        with st.expander(
            f"{row['優先序']} | {row['GRI項目']} {row['項目名稱']} | {row['分數']} 分",
            expanded=row["風險等級"] == "高",
        ):
            st.markdown(
                f"風險等級：<span class='{risk_class}'>{row['風險等級']}</span>",
                unsafe_allow_html=True,
            )
            st.write(f"發現頁面：{row['發現頁面']}")
            st.write(f"缺口：{row['缺口']}")
            st.write(f"建議修改：{row['建議修改']}")
            st.text(row["相關摘錄"])


def render_results_table(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">Disclosure Register</div>', unsafe_allow_html=True)
    view_columns = [
        "GRI項目",
        "項目名稱",
        "主題",
        "狀態",
        "風險等級",
        "優先序",
        "分數",
        "發現頁面",
        "缺口",
        "建議修改",
    ]
    st.dataframe(
        df[view_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "分數": st.column_config.ProgressColumn("分數", min_value=0, max_value=100),
            "風險等級": st.column_config.TextColumn("風險等級", width="small"),
            "發現頁面": st.column_config.TextColumn("發現頁面", width="medium"),
            "缺口": st.column_config.TextColumn("缺口", width="large"),
            "建議修改": st.column_config.TextColumn("建議修改", width="large"),
        },
    )


inject_styles()
render_header()

with st.sidebar:
    st.header("檢核設定")
    uploaded_file = st.file_uploader("公司永續報告書 PDF", type=["pdf"])

    themes = ordered_themes()
    selected_themes = st.multiselect("GRI 主題", themes, default=themes)
    available_rules = [rule for rule in DISCLOSURE_RULES if rule.theme in selected_themes]
    selected_codes = st.multiselect(
        "GRI 項目",
        [rule.code for rule in available_rules],
        default=[rule.code for rule in available_rules],
    )

    st.divider()
    st.caption(f"目前規則庫：{len(DISCLOSURE_RULES)} 個揭露項目")
    analyze_clicked = st.button("開始檢核", type="primary", use_container_width=True)

if not uploaded_file:
    render_empty_state()
    st.stop()

if not selected_codes:
    st.warning("請至少選擇一個 GRI 項目。")
    st.stop()

if analyze_clicked:
    with st.spinner("正在解析 PDF、比對 GRI 項目並產出改善清單..."):
        result = analyze_report(uploaded_file.read(), selected_codes)
    st.session_state["analysis_result"] = prepare_results(result)
    st.session_state["analysis_file_name"] = uploaded_file.name

result_df = st.session_state.get("analysis_result")
if result_df is None:
    st.info("設定完成後，請點擊左側「開始檢核」。")
    st.stop()

file_name = st.session_state.get("analysis_file_name", uploaded_file.name)

render_metrics(result_df)

summary_tab, detail_tab, export_tab = st.tabs(["管理摘要", "完整明細", "匯出報告"])

with summary_tab:
    render_charts(result_df)
    render_priority_list(result_df)

with detail_tab:
    filter_left, filter_right = st.columns([1, 1])
    with filter_left:
        risk_filter = st.multiselect("風險等級", ["高", "中", "低"], default=["高", "中", "低"])
    with filter_right:
        status_filter = st.multiselect("揭露狀態", STATUS_ORDER, default=STATUS_ORDER)

    filtered_df = result_df[
        result_df["風險等級"].isin(risk_filter) & result_df["狀態"].isin(status_filter)
    ]
    render_results_table(filtered_df)

with export_tab:
    csv = result_df.to_csv(index=False).encode("utf-8-sig")
    summary_text = build_management_summary(result_df, file_name)
    st.download_button(
        "下載完整 CSV",
        csv,
        file_name="gri_analysis_result.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.download_button(
        "下載管理摘要 Markdown",
        summary_text.encode("utf-8-sig"),
        file_name="gri_management_summary.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.text_area("管理摘要預覽", summary_text, height=420)
