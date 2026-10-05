"""Streamlit web interface for the lead generation agent.

Run:
    streamlit run app.py
"""

from __future__ import annotations

import html
import re
from datetime import datetime

import pandas as pd
import streamlit as st

import config
import places
from exporter import COLUMNS, THEMES, build_report, records_to_frame
from lead_generator import collect_leads, validate_pincode


st.set_page_config(
    page_title="LeadScout · Lead Generation",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# key -> (label, material icon, report column, accent colour)
CONTACTS = {
    "phone": ("Phone numbers", ":material/call:", "Phone Number", "#4F46E5"),
    "email": ("Emails", ":material/mail:", "Email ID", "#0EA5E9"),
    "website": ("Websites", ":material/language:", "Website", "#10B981"),
    "instagram": ("Instagram", ":material/photo_camera:", "Instagram", "#EC4899"),
    "facebook": ("Facebook", ":material/thumb_up:", "Facebook", "#2563EB"),
}
KPI_EMOJI = {"phone": "📞", "email": "✉️", "website": "🌐", "instagram": "📸", "facebook": "👍"}
# Widget state tied to one result set; cleared when a new search finishes.
RESULT_WIDGET_KEYS = ("flt", "q", "only_cols", "rpt_title", "rpt_by", "rpt_theme", "rpt_file")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--ink:#0F172A;--muted:#64748B;--line:#E2E8F0;--brand:#4F46E5;}
#MainMenu, footer {visibility:hidden;}
[data-testid="stHeader"]{background:transparent;}
.block-container{padding-top:1.4rem;padding-bottom:3rem;max-width:1280px;}
.stApp{background:
  radial-gradient(1100px 480px at 0% -10%, rgba(99,102,241,.10), transparent 60%),
  radial-gradient(900px 420px at 100% 0%, rgba(236,72,153,.07), transparent 60%), #F7F8FC;}
.ls-hero,.ls-kpi,.ls-head,.ls-step,.ls-live{font-family:'Inter',system-ui,sans-serif;}
@keyframes ls-rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}

.ls-hero{position:relative;overflow:hidden;border-radius:22px;padding:32px 36px;color:#fff;margin-bottom:20px;
  background:linear-gradient(130deg,#4338CA 0%,#6D28D9 55%,#DB2777 100%);
  box-shadow:0 24px 48px -24px rgba(79,70,229,.6);animation:ls-rise .5s ease both;}
.ls-hero::before,.ls-hero::after{content:"";position:absolute;border-radius:50%;background:rgba(255,255,255,.09);}
.ls-hero::before{width:300px;height:300px;right:-90px;top:-110px;}
.ls-hero::after{width:180px;height:180px;right:140px;bottom:-120px;}
.ls-eyebrow{display:inline-block;font-size:.72rem;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);padding:5px 12px;border-radius:999px;}
.ls-title{font-size:2.35rem;font-weight:800;letter-spacing:-.025em;margin:14px 0 6px;line-height:1.1;}
.ls-tag{color:rgba(255,255,255,.88);font-size:1.02rem;max-width:720px;}
.ls-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;position:relative;z-index:1;}
.ls-chip{font-size:.8rem;font-weight:500;padding:6px 12px;border-radius:999px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);}

[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px 24px 12px;
  box-shadow:0 14px 34px -22px rgba(15,23,42,.35);animation:ls-rise .5s ease .05s both;}
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{border-radius:12px;font-weight:600;
  min-height:44px;transition:transform .15s ease,box-shadow .2s ease,filter .2s ease;}
.stButton>button:hover,.stDownloadButton>button:hover,.stFormSubmitButton>button:hover{transform:translateY(-1px);
  box-shadow:0 10px 22px -12px rgba(79,70,229,.55);}
.stButton>button:active,.stDownloadButton>button:active,.stFormSubmitButton>button:active{transform:translateY(0);}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-primaryFormSubmit"]{
  background:linear-gradient(135deg,#4F46E5,#7C3AED)!important;border:none!important;color:#fff!important;}
[data-testid="stBaseButton-primary"]:hover,[data-testid="stBaseButton-primaryFormSubmit"]:hover{filter:brightness(1.08);}

.ls-head{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin:28px 0 12px;animation:ls-rise .4s ease both;}
.ls-head .t{font-size:1.35rem;font-weight:700;color:var(--ink);letter-spacing:-.01em;}
.ls-head .s{font-size:.9rem;color:var(--muted);margin-top:2px;}

.ls-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:4px 0 18px;}
@media (max-width:1000px){.ls-kpis{grid-template-columns:repeat(2,minmax(0,1fr));}}
.ls-kpi{background:#fff;border:1px solid var(--line);border-radius:16px;padding:16px 18px;
  box-shadow:0 8px 22px -18px rgba(15,23,42,.45);transition:transform .2s ease,box-shadow .2s ease;animation:ls-rise .45s ease both;}
.ls-kpi:hover{transform:translateY(-3px);box-shadow:0 18px 30px -20px rgba(15,23,42,.45);}
.ls-kpi .top{display:flex;justify-content:space-between;align-items:center;color:var(--muted);
  font-size:.74rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;}
.ls-kpi .ico{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:1rem;}
.ls-kpi .val{font-size:1.9rem;font-weight:800;color:var(--ink);margin-top:6px;line-height:1.1;}
.ls-kpi .sub{font-size:.78rem;color:var(--muted);margin-top:4px;}
.ls-bar{height:6px;border-radius:99px;background:#EEF2F7;margin-top:10px;overflow:hidden;}
.ls-bar>span{display:block;height:100%;border-radius:99px;transition:width .6s ease;}

.ls-live{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 10px;}
.ls-live span{font-size:.8rem;font-weight:500;color:#334155;background:#F1F5F9;border:1px solid var(--line);
  padding:5px 11px;border-radius:999px;}
.ls-live b{color:var(--ink);}

.ls-steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:26px;}
@media (max-width:900px){.ls-steps{grid-template-columns:1fr;}}
.ls-step{background:#fff;border:1px solid var(--line);border-radius:16px;padding:20px;animation:ls-rise .5s ease both;}
.ls-step .n{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-weight:700;color:#fff;
  background:linear-gradient(135deg,#4F46E5,#7C3AED);margin-bottom:12px;}
.ls-step .h{font-weight:700;color:var(--ink);margin-bottom:4px;}
.ls-step .p{font-size:.88rem;color:var(--muted);line-height:1.5;}

[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;
  box-shadow:0 10px 26px -22px rgba(15,23,42,.45);}
[data-testid="stExpander"] details{background:#fff;border-radius:14px;border-color:var(--line);}
.ls-foot{text-align:center;color:var(--muted);font-size:.8rem;margin-top:40px;}
</style>
"""


def _html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


def _has(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip() != ""


def hero() -> None:
    chips = "".join(
        f'<span class="ls-chip">{KPI_EMOJI[k]} {label}</span>' for k, (label, *_rest) in CONTACTS.items()
    )
    _html(
        '<div class="ls-hero">'
        '<span class="ls-eyebrow">Local business lead generation</span>'
        '<div class="ls-title">LeadScout</div>'
        '<div class="ls-tag">Find businesses by category and pincode, enrich them with phone, email, '
        "website and social profiles, then export a polished Excel report in one click.</div>"
        f'<div class="ls-chips">{chips}</div>'
        "</div>"
    )


def kpi_cards(df: pd.DataFrame) -> str:
    total = len(df)
    cards = [
        '<div class="ls-kpi"><div class="top">Total leads'
        '<span class="ico" style="background:#4F46E51A">📇</span></div>'
        f'<div class="val">{total}</div><div class="sub">all with phone numbers</div>'
        '<div class="ls-bar"><span style="width:100%;background:linear-gradient(90deg,#4F46E5,#7C3AED)"></span></div></div>'
    ]
    for key in ("email", "website", "instagram", "facebook"):
        label, _icon, column, colour = CONTACTS[key]
        count = int(_has(df[column]).sum()) if total else 0
        pct = round(count / total * 100) if total else 0
        cards.append(
            f'<div class="ls-kpi" style="animation-delay:{0.05 * len(cards):.2f}s"><div class="top">{label}'
            f'<span class="ico" style="background:{colour}1A">{KPI_EMOJI[key]}</span></div>'
            f'<div class="val">{count}</div><div class="sub">{pct}% coverage</div>'
            f'<div class="ls-bar"><span style="width:{pct}%;background:{colour}"></span></div></div>'
        )
    return f'<div class="ls-kpis">{"".join(cards)}</div>'


def empty_state() -> None:
    steps = (
        ("Search", "Enter a pincode, a business category and how many leads you need."),
        ("Filter", "Keep only leads with phone numbers, emails, websites, Instagram or Facebook."),
        ("Export", "Download a branded Excel report with a summary sheet, or CSV / JSON."),
    )
    cards = "".join(
        f'<div class="ls-step" style="animation-delay:{i * 0.08:.2f}s"><div class="n">{i}</div>'
        f'<div class="h">{title}</div><div class="p">{text}</div></div>'
        for i, (title, text) in enumerate(steps, start=1)
    )
    _html(f'<div class="ls-steps">{cards}</div>')


def search_form() -> None:
    with st.form("lead_search_form", border=False):
        c1, c2, c3 = st.columns([1.1, 2, 1.1])
        pincode = c1.text_input("Pincode", placeholder="e.g. 700075", max_chars=10)
        domain = c2.text_input("Business category", placeholder="e.g. restaurant, gym, salon, dentist")
        target = c3.number_input(
            "Number of records",
            min_value=1,
            max_value=200,
            value=min(max(int(config.MIN_RECORDS), 1), 200),
            step=5,
            help="How many leads to collect (1–200).",
        )
        required = st.pills(
            "Only collect leads that also have",
            options=[k for k in CONTACTS if k != "phone"],
            selection_mode="multi",
            format_func=lambda k: f"{CONTACTS[k][1]} {CONTACTS[k][0]}",
            help="Every lead always includes a phone number. Stricter requirements search longer.",
        )
        submitted = st.form_submit_button(
            "Generate leads", type="primary", icon=":material/travel_explore:", width="stretch"
        )

    if not submitted:
        return
    pincode, domain = pincode.strip(), domain.strip()
    if not validate_pincode(pincode):
        st.error("Invalid pincode — enter 4 to 10 digits.", icon=":material/error:")
        return
    if not domain:
        st.error("Please enter a business category.", icon=":material/error:")
        return
    run_search(pincode, domain, int(target), list(required or []))


def run_search(pincode: str, domain: str, target: int, required: list[str]) -> None:
    status = st.status(f"Searching for **{domain}** near **{pincode}**…", expanded=True)
    with status:
        bar = st.progress(0.0, text="Starting…")
        stats_slot = st.empty()
        table_slot = st.empty()

    def on_progress(event: dict) -> None:
        records = event.get("records") or []
        bar.progress(
            min(len(records) / target, 1.0),
            text=f"{event.get('message') or 'Working…'}  ·  {len(records)}/{target} leads",
        )
        stats_slot.markdown(
            '<div class="ls-live">'
            f"<span>Page <b>{event.get('current_page', 0)}</b></span>"
            f"<span>Candidates <b>{event.get('total_candidates', 0)}</b></span>"
            f"<span>No phone <b>{event.get('skipped_no_phone', 0)}</b></span>"
            f"<span>Missing required <b>{event.get('skipped_missing', 0)}</b></span>"
            "</div>",
            unsafe_allow_html=True,
        )
        if records:
            preview = records_to_frame(records)[["Business Name", "Phone Number", "Email ID", "Website"]]
            table_slot.dataframe(preview, hide_index=True, width="stretch", height=240)

    try:
        result = collect_leads(
            pincode=pincode,
            domain=domain,
            min_records=target,
            progress_callback=on_progress,
            export_excel=False,
            required_fields=required,
        )
    except (places.PlacesAPIError, ValueError) as exc:
        status.update(label="Lead search failed", state="error", expanded=True)
        st.error(str(exc), icon=":material/error:")
        return
    except Exception as exc:  # noqa: BLE001
        status.update(label="Unexpected error", state="error", expanded=True)
        st.error(f"Unexpected error: {exc}", icon=":material/error:")
        return

    status.update(label="Lead search completed", state="complete", expanded=False)
    for key in RESULT_WIDGET_KEYS:
        st.session_state.pop(key, None)
    st.session_state.result = result
    st.session_state.search = {"pincode": pincode, "domain": domain, "target": target, "required": required}
    st.session_state.flash = result["message"]
    st.rerun()


def filtered_view(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    with st.container(border=True):
        f1, f2 = st.columns([3, 2], vertical_alignment="bottom")
        selected = f1.pills(
            "Show only leads with",
            options=list(CONTACTS),
            selection_mode="multi",
            format_func=lambda k: f"{CONTACTS[k][1]} {CONTACTS[k][0]}",
            key="flt",
        )
        query = f2.text_input(
            "Search",
            placeholder="Search by name or address…",
            key="q",
            icon=":material/search:",
        )
        only_cols = st.toggle(
            "Show only the selected contact columns (e.g. a phone-numbers-only list)",
            key="only_cols",
            disabled=not selected,
        )

    view = df
    for key in selected:
        view = view[_has(view[CONTACTS[key][2]])]
    if query.strip():
        needle = query.strip()
        view = view[
            view["Business Name"].str.contains(needle, case=False, regex=False)
            | view["Address"].str.contains(needle, case=False, regex=False)
        ]
    columns = (
        ["Business Name"] + [CONTACTS[k][2] for k in CONTACTS if k in selected]
        if only_cols and selected
        else COLUMNS
    )
    return view[columns], [CONTACTS[k][0] for k in CONTACTS if k in selected]


def results_table(view: pd.DataFrame, total: int) -> None:
    st.caption(f"Showing **{len(view)}** of **{total}** leads")
    if view.empty:
        st.info("No leads match the current filters.", icon=":material/filter_alt_off:")
        return
    st.dataframe(
        view,
        hide_index=True,
        width="stretch",
        height=min(40 + 35 * len(view), 560),
        column_config={
            "Business Name": st.column_config.TextColumn(width="medium", pinned=True),
            "Address": st.column_config.TextColumn(width="large"),
            "Phone Number": st.column_config.TextColumn(width="small"),
            "Email ID": st.column_config.TextColumn(width="medium"),
            "Website": st.column_config.LinkColumn(display_text=r"https?://(?:www\.)?([^/?#]+)"),
            "Instagram": st.column_config.LinkColumn(display_text=r"https?://(?:www\.)?instagram\.com/([^/?#]+)"),
            "Facebook": st.column_config.LinkColumn(display_text=r"https?://(?:[\w-]+\.)?facebook\.com/([^/?#]+)"),
        },
    )


def downloads(view: pd.DataFrame, search: dict, filter_labels: list[str]) -> None:
    domain, pincode = search["domain"], search["pincode"]
    _html(
        '<div class="ls-head"><div><div class="t">Download report</div>'
        '<div class="s">Downloads include exactly the leads and columns shown above.</div></div></div>'
    )

    with st.expander("Customize Excel report", icon=":material/tune:"):
        a, b = st.columns(2)
        title = a.text_input("Report title", value=f"{domain.title()} Leads — {pincode}", key="rpt_title")
        prepared_by = b.text_input("Prepared by / company", placeholder="Optional", key="rpt_by")
        c, d = st.columns(2)
        theme = c.segmented_control("Colour theme", list(THEMES), default="Indigo", key="rpt_theme") or "Indigo"
        safe_domain = re.sub(r"\W+", "_", domain.lower()).strip("_")
        file_stem = d.text_input("File name", value=f"leads_{pincode}_{safe_domain}", key="rpt_file")
        e, f = st.columns(2)
        include_summary = e.toggle("Add summary sheet (coverage stats)", value=True)
        serial_numbers = f.toggle("Add serial number column (#)", value=True)

    now = datetime.now()
    subtitle = " • ".join(
        part
        for part in (
            domain.title(),
            f"Pincode {pincode}",
            f"{len(view)} leads",
            f"Generated {now:%d %b %Y, %I:%M %p}",
            f"Prepared by {prepared_by.strip()}" if prepared_by.strip() else "",
        )
        if part
    )
    metadata = {
        "Business category": domain,
        "Pincode": pincode,
        "Records requested": search["target"],
        "Required contacts": ", ".join(["Phone"] + [CONTACTS[k][0] for k in search["required"]]),
        "View filters": ", ".join(filter_labels) or "None",
        "Generated on": f"{now:%d %b %Y, %I:%M %p}",
        "Prepared by": prepared_by.strip(),
    }
    stem = re.sub(r"[^\w\-]+", "_", file_stem).strip("_") or "leads"
    disabled = view.empty

    d1, d2, d3 = st.columns([2, 1, 1])
    d1.download_button(
        "Download Excel report",
        data=build_report(
            view,
            title=title.strip() or "Lead Report",
            subtitle=subtitle,
            theme=theme,
            include_summary=include_summary,
            serial_numbers=serial_numbers,
            metadata=metadata,
        ),
        file_name=f"{stem}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        icon=":material/table_view:",
        width="stretch",
        on_click="ignore",
        disabled=disabled,
    )
    d2.download_button(
        "CSV",
        data=view.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{stem}.csv",
        mime="text/csv",
        icon=":material/description:",
        width="stretch",
        on_click="ignore",
        disabled=disabled,
    )
    d3.download_button(
        "JSON",
        data=view.to_json(orient="records", indent=2, force_ascii=False),
        file_name=f"{stem}.json",
        mime="application/json",
        icon=":material/data_object:",
        width="stretch",
        on_click="ignore",
        disabled=disabled,
    )


def results() -> None:
    result, search = st.session_state.result, st.session_state.search
    df = records_to_frame(result["records"])

    head, action = st.columns([5, 1], vertical_alignment="bottom")
    with head:
        _html(
            '<div class="ls-head"><div>'
            f'<div class="t">{len(df)} leads · {html.escape(search["domain"].title())} in {html.escape(search["pincode"])}</div>'
            f'<div class="s">{html.escape(result["message"])} · {result["total_candidates"]} candidates scanned '
            f'in {result["duration"]}s</div></div></div>'
        )
    if action.button("New search", icon=":material/refresh:", width="stretch"):
        for key in ("result", "search", *RESULT_WIDGET_KEYS):
            st.session_state.pop(key, None)
        st.rerun()

    if df.empty:
        st.warning(
            "No leads found. Try a broader category, a neighbouring pincode or fewer required contacts.",
            icon=":material/search_off:",
        )
        return

    _html(kpi_cards(df))
    view, filter_labels = filtered_view(df)
    results_table(view, len(df))
    downloads(view, search, filter_labels)


_html(CSS)
hero()
search_form()

if flash := st.session_state.pop("flash", None):
    st.toast(flash, icon="✅")

if "result" in st.session_state:
    results()
else:
    empty_state()

_html(
    '<div class="ls-foot">Data is gathered from Google Places and publicly accessible business websites. '
    "Email and social links are best-effort and may not be available for every business.</div>"
)
