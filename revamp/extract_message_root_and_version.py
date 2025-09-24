# pip install lxml
from lxml import etree
import re
from typing import Optional, Tuple, Dict, List

YEAR_MINOR_RX = re.compile(r"(?:^|/)(20\d{2})\.(\d)(?:/|$)")

def _local_name(tag: str) -> str:
    # "{uri}Local" -> "Local"; "Local" -> "Local"
    return tag.split("}", 1)[1] if tag.startswith("{") else tag

def _ns_uri_from_tag(tag: str) -> Optional[str]:
    # "{uri}Local" -> "uri"
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None

def _extract_version_from_uri(uri: str) -> Optional[str]:
    """
    From a namespace URI, pull '2018.2' -> '18.2'.
    If multiple matches exist, take the last (most specific).
    """
    matches = list(YEAR_MINOR_RX.finditer(uri))
    if not matches:
        return None
    year, minor = matches[-1].groups()
    yy = int(year) % 2000  # 2018 -> 18
    return f"{yy}.{minor}"

def detect_ndc_header(xml_path: str) -> Tuple[str, str, Optional[str]]:
    """
    Returns (message_root_normalized, ndc_version, root_namespace_uri?)
    - message_root_normalized: e.g., "OrderViewRS"
    - ndc_version: e.g., "18.2", "21.3", or "UNKNOWN"
    - root_namespace_uri: the URI bound to the root element (if any)
    """
    ns_uris: List[str] = []

    # Collect namespace decls early; stop after the first 'start'
    context = etree.iterparse(
        xml_path,
        events=("start", "start-ns"),
        huge_tree=True,
    )
    root = None
    root_ns_uri = None
    version_attr = None

    for event, payload in context:
        if event == "start-ns":
            prefix, uri = payload  # ('ns3', 'http://.../2018.2/IATA_OrderViewRS')
            ns_uris.append(uri)
            continue

        # event == "start" for the root (first element)
        elem = payload
        root = elem
        version_attr = elem.attrib.get("Version") or elem.attrib.get("version")
        root_ns_uri = _ns_uri_from_tag(elem.tag)
        break  # we only need the root

    if root is None:
        return ("UNKNOWN", "UNKNOWN", None)

    # Normalize message name (strip optional "IATA_" prefix)
    local = _local_name(root.tag)               # e.g., "IATA_OrderViewRS"
    if local.startswith("IATA_"):
        message_root = local[len("IATA_"):]     # -> "OrderViewRS"
    else:
        message_root = local

    # 1) Prefer explicit @Version on the root
    if version_attr:
        return (message_root, version_attr.strip(), root_ns_uri)

    # 2) Try the root namespace URI
    if root_ns_uri:
        v = _extract_version_from_uri(root_ns_uri)
        if v:
            return (message_root, v, root_ns_uri)

    # 3) Fall back: look across all declared namespace URIs; pick the "max"
    candidates = []
    for uri in ns_uris:
        v = _extract_version_from_uri(uri)
        if v:
            yy, minor = v.split(".")
            candidates.append((int(yy), int(minor), v, uri))
    if candidates:
        # choose the highest (year, minor)
        candidates.sort()
        _, _, best_v, best_uri = candidates[-1]
        return (message_root, best_v, best_uri)

    # 4) Give up
    return (message_root, "UNKNOWN", root_ns_uri)


if __name__ == "__main__":
    print(detect_ndc_header("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/05.Payment_OrderChange.r.xml"))
    print(detect_ndc_header("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/core/config/test_data/LATAM/OVRS_Qantas_17_2.xml"))
    print(detect_ndc_header("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/core/config/test_data/LATAM/OVRS_Air_France_18_2.xml"))