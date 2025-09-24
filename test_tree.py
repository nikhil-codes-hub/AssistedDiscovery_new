from xml.etree import ElementTree as ET

def process(xml_file, target):
    with open(xml_file) as f:
        tree = ET.parse(f)
        path = find_path(tree.getroot(), target)
        return path
        

def find_path(node, target, ancestors=None):
    if ancestors is None:
        ancestors = []
    node_tag = node.tag
    if node_tag == target:
        return ancestors + [node_tag]
    for child in node:
        path = find_path(child, target, ancestors + [node_tag])
        if path:
            return path
    return None
    
if __name__ == "__main__":
    path = process("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/05.Payment_OrderChange.r.xml", "PassengerList")
    print("/".join(path))
    
    path = process("/Users/nlepakshi/Library/Mobile Documents/com~apple~CloudDocs/office_projects/restart_refactoring_coding/AssistedDiscovery/05.Payment_OrderChange.r.xml", "FareComponent")
    print("/".join(path))
    
    
    