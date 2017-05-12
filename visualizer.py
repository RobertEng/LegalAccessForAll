'''
CS141 Legal Access For All
visualizer.py

'''

import json
import csv
import re
import sys
csv.field_size_limit(sys.maxsize)

################################################################################
# CONSTANTS
################################################################################

DATA_FOLDER = './data/'


################################################################################
# PROCESS STATUTES
################################################################################

def extract_network_from_sqldump():
    pass

def extract_network_from_scraper_data():
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
    statutes_file = 'CA_statutes_sample.csv'
    BEGIN_COM = 16641
    END_COM = 17262
    
    nodes, links = [], []
    current_division = ""
    # 0 is reserved for title nodes
    # 1 is reserved for unknown nodes
    current_division_num = 1 # im dumb and this gets incremented immediately.
    seen_titles = set()

    with open(DATA_FOLDER + statutes_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        data = [d for d in spamreader]

    for line in data[BEGIN_COM: END_COM]:
        # Keep track of the division so we can separate nodes into groups by
        # division. Increment if a new division is seen.
        if len(line) > 0 and line[1] != current_division:
            current_division = line[1]
            current_division_num += 1

        # Find the column with section number
        section_num_index = 0
        for i in range(len(line)):
            m = re.match("^([A-Z\s&]+)(App.)?\s+([0-9.]+)$", line[i])
            if m:
                section_num_index = i
                if section_num_index == 0:
                    print "The section number was the first one! Something's fishy"
                    sys.exit()
                break
        
        # Who knows what happened. Couldn't find section number
        if not m:
            print 'Could not find section title and num. Build a better regex!'
            # print line
            continue

        statute_title = m.group(1).strip()
        if m.group(3) != None:
            statute_num = m.group(3)
        else:
            statute_num = m.group(2)
        statute_fullname = statute_title + ' ' + statute_num

        # If I haven't seen this statute section yet, add it as a node
        if all(n['id'] != statute_fullname for n in nodes):
            node = {}
            node['id'] = statute_fullname
            node['group'] = current_division_num
            nodes.append(node)

        # Try to add title nodes (Divisions, Chapters, etc.) which contain
        # sections. Only add it if we haven't added it yet.
        for title_ind, title in enumerate(line[:section_num_index]):
            if all(n['id'] != title for n in nodes):
                node = {}
                node['id'] = title
                node['group'] = 0
                nodes.append(node)
            
            # If I haven't created this link already, create it and add it
            if title_ind > 0 and all(l['source'] != title and l['target'] != line[title_ind - 1] for l in links):
                link = {}
                link['source'] = title
                link['target'] = line[title_ind - 1]
                link['value'] = 1
                links.append(link)
            # TODO: If I have created this link, then increment its value
            # elif title_ind > 0:
            #     pass

        # Add the current statute to the title node
        link = {}
        link['source'] = statute_fullname
        link['target'] = line[section_num_index - 1]
        link['value'] = 1
        links.append(link)

        # TODO: Break up the current line into multiple nodes
        # if len(line[section_num_index + 1:]) > 1:
        #     print line[section_num_index + 2]
        # # print len(line[section_num_index + 1:])

        # Look in the statute for mentions of other section
        statute = ' '.join(line[section_num_index + 1:])
        # example = "the case of a motor vehicle, as defined in Section 415 of the Vehicle Code, or a trailer, as defined in Section 630 of that code, that is not to be used primarily for personal, family, or household purposes, that the amount of rental payments may be increased or decreased - See more at: http://codes.findlaw.com/ca/commercial-code/com-sect-1203.html#sthash.BU0brds0.dpuf"
        # statute = example

        pattern = re.compile(r"Section (\d+)", re.IGNORECASE)
        seen = set() # Keep track of sections we've seen, so we don't add twice
        for m in re.finditer(pattern, statute):
            if m.group(1) not in seen:
                link = {}
                link['source'] = statute_fullname
                link['target'] = statute_title + ' ' + m.group(1)
                link['value'] = 1
                links.append(link)

    # Some nodes are unfortunately not caught/parsed but still show up in the
    # statutes. Add the nodes.
    for l in links:
        if all(l['source'] != n['id'] for n in nodes):
            node = {}
            node['id'] = l['source']
            node['group'] = 1
            nodes.append(node)
        if all(l['target'] != n['id'] for n in nodes):
            node = {}
            node['id'] = l['target']
            node['group'] = 1
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
    nodes, links = extract_network_from_scraper_data()
    visualize_network(nodes, links)

if __name__ == "__main__":
    main()
