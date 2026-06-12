from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class DisclosureRule:
    code: str
    name: str
    theme: str
    keywords: tuple[str, ...]
    required_evidence: tuple[str, ...]
    suggestion: str


def rule(
    code: str,
    name: str,
    theme: str,
    keywords: tuple[str, ...],
    evidence: tuple[str, ...],
    suggestion: str,
) -> DisclosureRule:
    return DisclosureRule(code, name, theme, keywords, evidence, suggestion)


DISCLOSURE_RULES: list[DisclosureRule] = [
    rule("GRI 2-1", "組織詳細資訊", "一般揭露", ("公司名稱", "總部", "所在地", "營運據點", "法律形式", "組織"), ("公司名稱", "總部", "營運據點"), "補充公司正式名稱、總部所在地、主要營運據點與法律形式。"),
    rule("GRI 2-2", "永續報告涵蓋的實體", "一般揭露", ("報告邊界", "涵蓋範圍", "合併報表", "子公司", "實體", "範疇"), ("報告邊界", "涵蓋範圍", "子公司"), "說明本報告涵蓋哪些公司、廠區或子公司，並標示是否與財務報表邊界一致。"),
    rule("GRI 2-3", "報告期間、頻率與聯絡人", "一般揭露", ("報告期間", "出版日期", "發布日期", "報告頻率", "聯絡人", "聯絡窗口"), ("報告期間", "報告頻率", "聯絡"), "補上報告期間、發布日期、報告頻率與永續報告聯絡窗口。"),
    rule("GRI 2-6", "活動、價值鏈與商業關係", "一般揭露", ("價值鏈", "供應鏈", "產品", "服務", "市場", "客戶", "供應商"), ("產品", "服務", "供應鏈", "市場"), "補充主要產品服務、供應鏈上下游、主要市場與重要商業關係。"),
    rule("GRI 2-7", "員工", "社會", ("員工", "人數", "性別", "年齡", "聘僱", "全職", "兼職"), ("員工", "人數", "性別"), "以表格揭露員工總數，並依性別、地區、聘僱類型或年齡分組。"),
    rule("GRI 3-1", "決定重大主題的流程", "重大主題", ("重大性", "重大主題", "利害關係人", "鑑別", "排序", "議合"), ("重大性", "利害關係人", "排序"), "說明重大主題鑑別流程、利害關係人參與方式、排序方法與決策依據。"),
    rule("GRI 3-2", "重大主題清單", "重大主題", ("重大主題清單", "重大議題", "矩陣", "重大性矩陣", "優先順序"), ("重大主題", "清單"), "列出本年度重大主題清單，並說明與前一年度相比的新增、刪除或調整。"),
    rule("GRI 201-1", "直接產生與分配的經濟價值", "經濟", ("經濟價值", "營收", "營業收入", "成本", "薪資", "稅捐", "股利", "社區投資"), ("營收", "成本", "稅"), "揭露直接產生與分配的經濟價值，包含營收、營運成本、員工薪資、稅捐與社區投資。"),
    rule("GRI 202-1", "市場地位與薪酬", "經濟", ("最低薪資", "基本工資", "薪酬", "當地", "市場薪資", "新進人員"), ("薪資", "當地", "比例"), "補充主要營運地點不同性別新進人員薪資與當地最低薪資的比較。"),
    rule("GRI 203-1", "基礎設施投資與支援服務", "經濟", ("基礎設施", "投資", "公益", "公共服務", "社區", "支援服務"), ("投資", "社區", "影響"), "說明基礎設施投資或支援服務的內容、地點、金額與社會影響。"),
    rule("GRI 204-1", "採購實務", "經濟", ("採購", "在地採購", "供應商", "本地", "當地供應商", "採購金額"), ("採購", "供應商", "比例"), "補充在地供應商採購比例、採購金額與主要營運地點的定義。"),
    rule("GRI 205-1", "反貪腐風險評估", "治理", ("貪腐", "反貪腐", "誠信", "賄賂", "風險評估", "稽核"), ("反貪腐", "風險", "評估"), "揭露已完成貪腐風險評估的營運據點比例、風險類型與管理措施。"),
    rule("GRI 206-1", "反競爭行為", "治理", ("反競爭", "壟斷", "公平交易", "訴訟", "裁罰", "法律程序"), ("反競爭", "訴訟", "結果"), "說明是否有反競爭、反托拉斯或壟斷相關法律程序，並揭露結果。"),
    rule("GRI 207-1", "稅務策略", "治理", ("稅務", "稅務策略", "租稅", "稅捐", "稅務治理", "稅務風險"), ("稅務", "策略", "治理"), "補充稅務策略、稅務治理責任、風險管理與法遵承諾。"),
    rule("GRI 301-1", "使用的物料", "環境", ("物料", "原物料", "再生物料", "包材", "重量", "用量"), ("物料", "用量", "再生"), "揭露使用物料的重量或體積，並區分再生與非再生物料。"),
    rule("GRI 302-1", "組織內部能源消耗量", "環境", ("能源消耗", "用電量", "燃料", "柴油", "天然氣", "再生能源", "非再生能源"), ("能源消耗", "用電量", "燃料", "再生能源"), "補充組織內部能源消耗總量，並依再生能源、非再生能源、電力與燃料分類揭露。"),
    rule("GRI 302-3", "能源密集度", "環境", ("能源密集度", "單位產量", "每營收", "每人", "強度", "密集度"), ("能源密集度", "分母", "單位"), "補充能源密集度計算公式、分母基礎與使用單位。"),
    rule("GRI 303-1", "水資源與流放水互動", "環境", ("水資源", "取水", "排水", "耗水", "水風險", "水壓力"), ("取水", "排水", "水風險"), "說明與水資源的互動、取水來源、排水去向與水風險評估。"),
    rule("GRI 304-1", "生物多樣性", "環境", ("生物多樣性", "保護區", "棲地", "物種", "生態", "復育"), ("生物多樣性", "地點", "影響"), "揭露營運據點是否位於或鄰近保護區與高生物多樣性價值區域，並說明影響。"),
    rule("GRI 305-1", "直接溫室氣體排放", "環境", ("範疇一", "Scope 1", "直接排放", "溫室氣體", "二氧化碳當量", "CO2e"), ("範疇一", "CO2e", "排放係數"), "補充範疇一排放量、盤查邊界、排放係數來源與計算方法。"),
    rule("GRI 305-2", "能源間接溫室氣體排放", "環境", ("範疇二", "Scope 2", "間接排放", "外購電力", "電力排放", "CO2e"), ("範疇二", "外購電力", "CO2e"), "補充範疇二排放量，並說明使用市場基礎或地點基礎方法及係數來源。"),
    rule("GRI 305-4", "溫室氣體排放密集度", "環境", ("排放密集度", "碳密集度", "每營收", "每產量", "強度"), ("排放密集度", "分母", "單位"), "補充排放密集度公式、分母與涵蓋的溫室氣體範疇。"),
    rule("GRI 306-1", "廢棄物相關衝擊", "環境", ("廢棄物", "廢棄物管理", "有害廢棄物", "回收", "清運", "處理"), ("廢棄物", "處理", "回收"), "說明廢棄物產生來源、相關衝擊、處理方式與減量措施。"),
    rule("GRI 308-1", "供應商環境評估", "環境", ("供應商環境評估", "環境稽核", "供應商", "環境標準", "新供應商"), ("供應商", "環境", "評估"), "揭露新供應商使用環境準則篩選的比例與不符合改善機制。"),
    rule("GRI 401-1", "新進員工與離職", "社會", ("新進員工", "離職", "流動率", "留任", "招募", "員工異動"), ("新進員工", "離職", "比例"), "依年齡、性別與地區揭露新進員工人數、離職人數與流動率。"),
    rule("GRI 402-1", "勞資關係通知期", "社會", ("勞資", "重大營運變更", "通知期", "工會", "協商", "團體協約"), ("通知期", "勞資", "協商"), "說明重大營運變更前提供員工或代表的最短通知期與協商程序。"),
    rule("GRI 403-1", "職業安全衛生管理系統", "社會", ("職業安全", "職安衛", "安全衛生", "職災", "失能傷害", "管理系統"), ("職安衛", "管理系統", "職災"), "補充職業安全衛生管理系統涵蓋範圍、危害辨識、事故調查與改善措施。"),
    rule("GRI 404-1", "訓練與教育", "社會", ("訓練", "教育訓練", "平均時數", "培訓", "職涯發展", "學習"), ("訓練", "時數", "性別"), "依性別與員工類別揭露平均訓練時數，並說明職涯發展與轉銜計畫。"),
    rule("GRI 405-1", "多元化與平等機會", "社會", ("多元化", "平等機會", "董事會", "女性", "性別", "年齡", "族群"), ("性別", "年齡", "比例"), "依性別、年齡或其他多元指標揭露治理單位與員工組成。"),
    rule("GRI 406-1", "歧視事件", "社會", ("歧視", "申訴", "人權", "平等", "騷擾", "改善措施"), ("歧視", "事件", "改善"), "揭露歧視事件數量、處理狀態、補救措施與防止再發機制。"),
    rule("GRI 407-1", "結社自由與團體協商", "社會", ("結社自由", "團體協商", "工會", "勞權", "協約", "供應商風險"), ("結社自由", "團體協商", "風險"), "說明營運據點或供應商是否有結社自由與團體協商風險，以及改善措施。"),
    rule("GRI 408-1", "童工", "社會", ("童工", "未成年", "兒童", "人權風險", "供應商", "禁止童工"), ("童工", "風險", "措施"), "揭露童工風險評估結果、涉及營運或供應商，以及預防或補救措施。"),
    rule("GRI 409-1", "強迫或強制勞動", "社會", ("強迫勞動", "強制勞動", "人口販運", "勞動人權", "供應商", "外籍移工"), ("強迫勞動", "風險", "措施"), "揭露強迫或強制勞動風險、管理措施、供應商要求與補救程序。"),
    rule("GRI 410-1", "保全實務", "社會", ("保全", "安全人員", "人權訓練", "保全訓練", "安全實務"), ("保全", "人權", "訓練"), "揭露保全人員接受人權政策或程序訓練的比例與訓練內容。"),
    rule("GRI 411-1", "原住民族權利", "社會", ("原住民", "原住民族", "土地權", "諮商", "文化", "權利"), ("原住民", "事件", "權利"), "說明是否有涉及原住民族權利的事件、地點、補救措施與諮商機制。"),
    rule("GRI 413-1", "當地社區", "社會", ("當地社區", "社區參與", "社會衝擊", "公益", "影響評估", "社區投資"), ("社區", "評估", "參與"), "揭露營運據點是否有社區參與、衝擊評估與發展計畫。"),
    rule("GRI 414-1", "供應商社會評估", "社會", ("供應商社會評估", "供應商人權", "社會準則", "勞動條件", "新供應商"), ("供應商", "社會", "評估"), "揭露新供應商使用社會準則篩選的比例、重大負面衝擊與改善要求。"),
    rule("GRI 415-1", "公共政策", "治理", ("政治獻金", "公共政策", "遊說", "政治捐贈", "政黨", "倡議"), ("政治", "捐贈", "金額"), "揭露政治獻金或公共政策參與情形，包含金額、對象與治理規範。"),
    rule("GRI 416-1", "客戶健康與安全", "社會", ("客戶健康", "產品安全", "安全評估", "健康安全", "召回", "產品責任"), ("產品", "安全", "評估"), "揭露產品或服務接受健康與安全衝擊評估的比例與改善措施。"),
    rule("GRI 417-1", "行銷與標示", "社會", ("產品標示", "服務標示", "行銷", "標籤", "廣告", "法規遵循"), ("標示", "行銷", "法規"), "說明產品與服務資訊標示要求、行銷溝通管理與違規事件。"),
    rule("GRI 418-1", "客戶隱私", "社會", ("客戶隱私", "個資", "個人資料", "資料外洩", "隱私", "資安事件"), ("客戶隱私", "個資", "事件"), "揭露客戶隱私或個人資料外洩相關申訴、事件數量、處理方式與預防措施。"),
]


def extract_pdf_pages(file_bytes: bytes) -> list[dict[str, object]]:
    try:
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return [
            {"page": index + 1, "text": page.get_text("text") or ""}
            for index, page in enumerate(doc)
        ]
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return [
            {"page": index + 1, "text": page.extract_text() or ""}
            for index, page in enumerate(reader.pages)
        ]


def count_extractable_text(file_bytes: bytes) -> int:
    pages = extract_pdf_pages(file_bytes)
    return sum(len(normalize_text(str(page["text"]))) for page in pages)


def ocr_pdf_to_searchable_pdf(
    file_bytes: bytes,
    language: str = "chi_tra+eng",
    dpi: int = 200,
) -> bytes:
    try:
        import fitz
        import pytesseract
        from PIL import Image
        from pypdf import PdfReader, PdfWriter
    except ImportError as exc:
        raise RuntimeError("OCR 套件尚未安裝，請確認 requirements.txt 已包含 pytesseract 與 Pillow。") from exc

    source = fitz.open(stream=file_bytes, filetype="pdf")
    writer = PdfWriter()

    try:
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        for page in source:
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            page_pdf = pytesseract.image_to_pdf_or_hocr(
                image,
                extension="pdf",
                lang=language,
            )
            reader = PdfReader(io.BytesIO(page_pdf))
            writer.add_page(reader.pages[0])
    except pytesseract.pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("找不到 Tesseract OCR。Streamlit Cloud 需要 packages.txt 安裝系統套件。") from exc

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_pages(pages: Iterable[dict[str, object]], keywords: Iterable[str]) -> list[int]:
    matched_pages: list[int] = []
    for page in pages:
        text = str(page["text"])
        if any(keyword.lower() in text.lower() for keyword in keywords):
            matched_pages.append(int(page["page"]))
    return matched_pages


def collect_snippets(
    pages: Iterable[dict[str, object]], keywords: Iterable[str], max_snippets: int = 3
) -> list[str]:
    snippets: list[str] = []
    keyword_list = list(keywords)
    for page in pages:
        page_no = int(page["page"])
        text = normalize_text(str(page["text"]))
        for keyword in keyword_list:
            position = text.lower().find(keyword.lower())
            if position >= 0:
                start = max(position - 55, 0)
                end = min(position + 145, len(text))
                snippets.append(f"p.{page_no}: {text[start:end]}")
                break
        if len(snippets) >= max_snippets:
            break
    return snippets


def score_rule(pages: list[dict[str, object]], rule: DisclosureRule) -> dict[str, object]:
    matched_pages = find_pages(pages, rule.keywords)
    full_text = "\n".join(str(page["text"]) for page in pages)
    evidence_hits = [
        evidence
        for evidence in rule.required_evidence
        if evidence.lower() in full_text.lower()
    ]

    page_score = min(len(matched_pages) * 18, 45)
    evidence_score = round((len(evidence_hits) / len(rule.required_evidence)) * 45)
    data_score = 10 if re.search(r"\d", full_text) and matched_pages else 0
    score = min(page_score + evidence_score + data_score, 100)

    if score >= 80:
        status = "大致符合"
        gap = "目前已找到主要揭露內容，仍建議確認數據邊界、方法與係數來源是否完整。"
    elif score >= 50:
        status = "部分符合"
        missing = [item for item in rule.required_evidence if item not in evidence_hits]
        gap = "缺少或不明確：" + "、".join(missing)
    elif score > 0:
        status = "揭露不足"
        gap = "有相關文字，但缺少足夠數據、邊界、方法或佐證。"
    else:
        status = "未找到"
        gap = "報告書中未找到明確對應內容。"

    return {
        "GRI項目": rule.code,
        "項目名稱": rule.name,
        "主題": rule.theme,
        "狀態": status,
        "分數": score,
        "發現頁面": ", ".join(f"p.{page}" for page in matched_pages[:8]) or "-",
        "缺口": gap,
        "建議修改": rule.suggestion,
        "相關摘錄": "\n".join(collect_snippets(pages, rule.keywords)) or "-",
    }


def analyze_report(file_bytes: bytes, selected_codes: list[str]) -> pd.DataFrame:
    pages = extract_pdf_pages(file_bytes)
    rules = [rule for rule in DISCLOSURE_RULES if rule.code in selected_codes]
    rows = [score_rule(pages, rule) for rule in rules]
    return pd.DataFrame(rows)
