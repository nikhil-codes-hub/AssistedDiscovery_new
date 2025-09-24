# high_signal_filter.py
# Add this on top of your existing iterparse_demo.py

import io, re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, List, Iterator, Tuple

# ---------- Regex library (aviation signals) ----------
RX = {
    "pnr": re.compile(r"^[A-Z0-9]{5,7}$"),
    "ticket13": re.compile(r"^\d{13}$"),
    "ticket14": re.compile(r"^\d{14}$"),  # warn-tier (some providers)
    "iata_airport": re.compile(r"^[A-Z]{3}$"),
    "airline_2l": re.compile(r"^[A-Z0-9]{2}$"),
    "currency": re.compile(r"^[A-Z]{3}$"),
    "fare_basis": re.compile(r"^[A-Z0-9]{3,12}$"),
    "ssr_code": re.compile(r"^[A-Z]{3,4}$"),
    "rfic": re.compile(r"^[A-Z]$"),
    "iso_date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    "iso_dt": re.compile(r"^\d{4}-\d{2}-\d{2}T"),
    "money_int": re.compile(r"^\d{1,9}$"),
}

# ---------- Minimal NodeFact for scoring ----------
@dataclass
class NodeFact:
    xpath: str
    tag: str
    parent: Optional[str]
    attrs: Dict[str, str]
    text: Optional[str]

def normalize_tag(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag

def iter_nodes(xml_bytes: bytes) -> Iterator[Tuple[str, Dict[str, str], Optional[str], List[str]]]:
    # Same as before (stdlib iterparse). Import from your previous file if you prefer.
    from xml.etree.ElementTree import iterparse
    path_stack: List[str] = []
    for event, elem in iterparse(io.BytesIO(xml_bytes), events=("start", "end")):
        tag = normalize_tag(elem.tag)
        if event == "start":
            path_stack.append(tag)
        else:
            xpath_norm = "/" + "/".join(path_stack)
            attrs = {k: v for k, v in sorted(elem.attrib.items())}
            text = (elem.text or "").strip() or None
            ancestors = path_stack[:-1]
            yield (xpath_norm, attrs, (text[:120] if text else None), ancestors)
            elem.clear()
            path_stack.pop()

# ---------- Whitelist-by-path (fast prefilter) ----------
WHITELIST_SUBSTRINGS = (
    # IDs / money
    "/BookingReferences/BookingReference/ID",
    "TicketDocNbr",
    "/TotalOrderPrice/DetailCurrencyPrice/Total",
    "/SimpleCurrencyPrice",
    # Fare & Taxes
    "/FareBasisCode/Code",
    "/Taxes/Breakdown/Tax",
    # Services / Ancillaries
    "ServiceDefinitionRef",
    "/ServiceDefinition/Encoding",
    # Baggage
    "/BaggageAllowance",
    "PieceMeasurements",
    "MaximumWeight",
    "PieceDimensionAllowance",
    # Segments
    "/FlightSegmentList/FlightSegment/",
    # SSR / Metadata
    "/SpecialServiceRequest",
    "/SSRCode",
)

def path_whitelisted(xpath: str) -> bool:
    return any(s in xpath for s in WHITELIST_SUBSTRINGS)

# ---------- Feature flags + significance score ----------
def feature_flags(n: NodeFact) -> Dict[str, bool]:
    text = n.text or ""
    flags = {
        "pnr": (n.tag == "ID" and "BookingReference" in n.xpath and RX["pnr"].match(text or "")),

        "ticket13": (n.tag == "TicketDocNbr" and RX["ticket13"].match(text)),
        "ticket14_warn": (n.tag == "TicketDocNbr" and RX["ticket14"].match(text)),

        "currency_amount": (
            (n.tag in ("Total", "SimpleCurrencyPrice", "Amount") and RX["money_int"].match(text or ""))
            and (("Code" in n.attrs and RX["currency"].match(n.attrs["Code"])) or "Code" in n.attrs)
        ),

        "fare_basis": ("FareBasisCode/Code" in n.xpath and RX["fare_basis"].match(text or "")),

        "tax_line": ("/Taxes/Breakdown/Tax" in n.xpath and n.tag in ("Tax", "TaxCode", "Amount")),

        "anc_encoding": ("/ServiceDefinition/Encoding" in n.xpath or n.tag in ("RFIC","Code","SubCode")),

        "baggage_piece": ("BaggageAllowance" in n.xpath and "PieceMeasurements" in n.xpath),
        "baggage_weight": ("MaximumWeight" in n.xpath and (text.isdigit() or text == "")),
        "baggage_dims": ("PieceDimensionAllowance" in n.xpath),

        "segment_core": ("/FlightSegmentList/FlightSegment/" in n.xpath and n.tag in (
            "Departure","Arrival","AirportCode","Date","Time","MarketingCarrier","AirlineID","FlightNumber","ClassOfService","Code"
        )),

        "ssr": ("/SpecialServiceRequest" in n.xpath or n.tag == "SSRCode"),
    }
    return flags

WEIGHTS = {
    "pnr": 1.0, "ticket13": 1.0, "ticket14_warn": 0.6,
    "currency_amount": 0.8, "fare_basis": 0.9,
    "tax_line": 0.8,
    "anc_encoding": 0.8,
    "baggage_piece": 0.7, "baggage_weight": 0.6, "baggage_dims": 0.6,
    "segment_core": 0.7,
    "ssr": 0.8,
}

def significance_score(n: NodeFact) -> Tuple[float, List[str]]:
    flags = feature_flags(n)
    score = 0.0
    reasons = []
    for k, v in flags.items():
        if v:
            score += WEIGHTS.get(k, 0.0)
            reasons.append(k)
    # Minor boost if node has a currency code attribute
    if "Code" in n.attrs and RX["currency"].match(n.attrs["Code"]):
        score += 0.15
        reasons.append("currency_code_attr")
    # Penalty for long free text
    if n.text and len(n.text) > 120:
        score -= 0.2
        reasons.append("long_text_penalty")
    return max(score, 0.0), reasons

# ---------- Stream, filter, and keep just the useful bits ----------
def stream_high_signal(xml_bytes: bytes, score_threshold: float = 0.6) -> Iterator[Dict]:
    for xpath, attrs, text, ancestors in iter_nodes(xml_bytes):
        tag = xpath.split("/")[-1]
        parent = ancestors[-1] if ancestors else None
        nf = NodeFact(xpath=xpath, tag=tag, parent=parent, attrs=attrs, text=text)
        if path_whitelisted(xpath):
            score, reasons = significance_score(nf)
            if score >= score_threshold:
                yield {
                    "xpath": xpath,
                    "tag": tag,
                    "parent": parent,
                    "attrs": attrs,
                    "text_preview": text,
                    "score": round(score, 2),
                    "reasons": reasons,
                }

# ---------- Example main ----------
if __name__ == "__main__":
    with open("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/05.Payment_OrderChange.r.xml", "rb") as f:
        data = f.read()

    print("=== High-signal nodes (top 20) ===")
    out = []
    for row in stream_high_signal(data, score_threshold=0.6):
        out.append(row)
        if len(out) >= 20:
            break
    for i, r in enumerate(out, 1):
        print(f"{i:02d}. {r['xpath']}  [{r['score']}]  reasons={r['reasons']}  text={r['text_preview']!r}")
