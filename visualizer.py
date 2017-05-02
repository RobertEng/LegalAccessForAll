'''
CS141 Legal Access For All
visualizer.py

'''

import json
import csv
import re

def extract_network():
    '''
    Extract the information needed to visualize the statutes in a network.
    A statute is a node. When a statute refers to another node, this is a link
    from the statute which refers to the statute which is being referred.

    Returns list of nodes and links.

    Example:
      "nodes": [
        {"id": "Myriel", "group": 1},
        {"id": "Mme.Hucheloup", "group": 8}
      ],
      "links": [
        {"source": "Napoleon", "target": "Myriel", "value": 1},
        {"source": "Mlle.Baptistine", "target": "Myriel", "value": 8},
        {"source": "Cravatte", "target": "Myriel", "value": 1}
      ]
    '''
    textfile = open("./data/CA_statutes.csv", 'r')
    filetext = textfile.read()
    textfile.close()
    nodes, links = [], []
    current_division = ""
    current_division_num = 0
    
    BEGIN_COM = 16641
    END_COM = 17262

    with open('./data/CA_statutes.csv', 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        data = [d for d in spamreader]

    search_regex = "^([A-Z\s]+)\s([0-9.\s]+)$"
    for line in data[BEGIN_COM: END_COM]:
        # Keep track of the division so we can separate nodes into groups by
        # division. Increment if a new division is seen.
        if len(line) > 0 and line[1] != current_division:
            current_division = line[1]
            current_division_num += 1

        # Find the column with section number
        section_num_index = 0
        for i in range(len(line)):
            m = re.match(search_regex, line[i])
            if m:
                section_num_index = i
                break
        
        # Who knows what happened. Couldn't find section number
        if not m:
            continue

        statute_title = m.group(1).strip()
        statute_num = m.group(2)
        statute_fullname = statute_title + ' ' + statute_num

        # If I haven't seen this statute section yet, add it as a node
        if all(n['id'] != statute_fullname for n in nodes):
            node = {}
            node['id'] = statute_fullname
            node['group'] = current_division_num
            nodes.append(node)

        # Look in the statute for mentions of other section
        statute = ' '.join(line[section_num_index + 1:])
        # example = "the case of a motor vehicle, as defined in Section 415 of the Vehicle Code, or a trailer, as defined in Section 630 of that code, that is not to be used primarily for personal, family, or household purposes, that the amount of rental payments may be increased or decreased - See more at: http://codes.findlaw.com/ca/commercial-code/com-sect-1203.html#sthash.BU0brds0.dpuf"
        # statute = example

        pattern = re.compile(r"Section (\d+)", re.IGNORECASE)
        seen = set() # Keep track of sections we've seen, so we don't add twice
        for m in re.finditer(pattern, statute):
            if m.group(1) not in seen:
                link = {}
                link['source'] = statute_title + ' ' + statute_num
                link['target'] = statute_title + ' ' + m.group(1)
                link['value'] = 1
                links.append(link)

    # Some nodes are unfortunately not caught/parsed but still show up in the
    # statutes. Add the nodes.
    for l in links:
        if all(l['source'] != n['id'] for n in nodes):
            node = {}
            node['id'] = l['source']
            node['group'] = 0
            nodes.append(node)
        if all(l['target'] != n['id'] for n in nodes):
            node = {}
            node['id'] = l['target']
            node['group'] = 0
            nodes.append(node)

    return nodes, links


def visualize_network(nodes, links):
    '''
    Visualize the passed in nodes and links in d3.js
    '''
    network = {}
    network['nodes'] = nodes
    network['links'] = links
    with open('network.json', 'w') as f:
        json.dump(network, f)


def main():
    nodes, links = extract_network()
    visualize_network(nodes, links)

if __name__ == "__main__":
    main()
