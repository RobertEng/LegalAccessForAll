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

def process_sqldump_data():
    pass


def process_scraper_data():
    '''
    Extract the information needed to visualize the statutes in a network.
    Put it into a standardized format.

    Here's the standardized format:
    "data": [
        {"id": "CA COML  4104",
         "titles": ["California Commercial Code - COM",
                    "Division 4. Bank Deposits and Collections",
                    "Chapter 1. General Provisions and Definitions"]},
         "text": ["(a)In this division unless the context otherwise requires:",
                  "(1)Account means any deposit or credit account with a bank,
                   including a demand, time, savings, passbook, share draft, or
                   like account, other than an account evidenced by a 
                   certificate of deposit."]},
        {"id": ... }
    ]
    '''
    statutes_file = 'CA_statutes_sample.csv'
    BEGIN_COM = 16641
    END_COM = 17262
    
    data = []
    with open(DATA_FOLDER + statutes_file, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        raw_data = [d for d in spamreader]

    for line in raw_data[BEGIN_COM: END_COM]:
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
        
        # Couldn't find section number. Who knows what happened.
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

        datum = {}
        datum['id'] = statute_fullname
        datum['titles'] = line[:section_num_index]
        datum['text'] = line[section_num_index + 1:]
        data.append(datum)
    return data


def data_to_force_graph(data):
    '''
    Convert standardized data format to force graph layout data structure.

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
    nodes, links = [], []
    divisions = ["None"]
    for d in data:
        node = {}
        node['id'] = d['id']
        # Add the group equal to the division
        if len(d['titles']) >= 2 and d['titles'][1] in divisions:
            node['group'] = divisions.index(d['titles'][1])
        elif len(d['titles']) >= 2 and d['titles'][1] not in divisions:
            divisions.append(d['titles'][1])
            node['group'] = divisions.index(d['titles'][1])
        else:
            print "Warning: No Division found"
            node['group'] = 0
        statute = ' '.join(d['text'])
        node['statute'] = statute
        nodes.append(node)

        # Add the links to sections which are mentioned in this statute
        pattern = re.compile(r"Section (\d+)", re.IGNORECASE)
        seen = set() # Keep track of sections we've seen, so we don't add twice
        statute_title = re.match("^([A-Z\s&]+)\s([0-9.]+)$", d['id']).group(1)
        
        for m in re.finditer(pattern, statute):
            if m.group(1) not in seen:
                link = {}
                link['source'] = d['id']
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

    network = {}
    network['nodes'] = nodes
    network['links'] = links
    with open('network.json', 'w') as f:
        json.dump(network, f)


def data_to_collapsible_graph(data):
    '''
    Converts the standardized format to hybrid collapsible force layout data
    structure.

    Example:
    {
        "name": "flare",
        "collapsible": true
        "children": [
            {"name": "AgglomerativeCluster", "group": 1,
                "refers": ["MergeEdge", "BetweennessCentrality"]
            },
            {"name": "CommunityStructure", "group": 1},
            {"name": "HierarchicalCluster", "group": 1},
            {"name": "MergeEdge", "group": 1},
            {"name": "graph", "group": 2,
                "children": [
                    {"name": "BetweennessCentrality", "group": 2},
                    {"name": "LinkDistance", "group": 2},
                ]
            }
        ]
    }
    '''
    network = {}
    divisions = ["None"]
    for d in data:

        # Set the group id equal to the division
        if len(d['titles']) >= 2 and d['titles'][1] in divisions:
            groupid = divisions.index(d['titles'][1])
        elif len(d['titles']) >= 2 and d['titles'][1] not in divisions:
            divisions.append(d['titles'][1])
            groupid = divisions.index(d['titles'][1])
        else:
            print "Warning: No Division found"
            groupid = 0

        cur = network
        for t in d['titles']:
            # Iterate to the node where d['titles'][i] is supposed to be.
            # If the current node doesn't exist in the network, then add it.
            if 'children' not in cur:
                cur['children'] = []
            if all(t != c['name'] for c in cur['children']):
                cur['children'].append({"name": t, "group": groupid})
            cur = next(x for x in cur['children'] if x['name'] == t)

        if 'children' not in cur:
            cur['children'] = []
        node = {"name": d['id'], "group": groupid}

        # Add the links to sections which are mentioned in this statute
        statute = ' '.join(d['text'])
        pattern = re.compile(r"Section (\d+)", re.IGNORECASE)
        seen = set() # Keep track of sections we've seen, so we don't add twice
        statute_title = re.match("^([A-Z\s&]+)\s([0-9.]+)$", d['id']).group(1)
        for m in re.finditer(pattern, statute):
            if m.group(1) not in seen:
                if "refers" not in node:
                    node['refers'] = []
                node['refers'].append(statute_title + ' ' + m.group(1))

        cur['children'].append(node)

    # HACKFIX: Accidentally puts root in a children list. Cut the root. I guess
    # this isn't a bug if there are more than one code.
    network = network['children'][0]
    # Remove group from the commercial code.
    network['group'] = 0
    # Mark the divisions (first layer) as collapsible
    for c in network['children']:
        c['collapsible'] = True
    # print network

    with open('collapsible.json', 'w') as f:
        json.dump(network, f)



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
        
        # Couldn't find section number. Who knows what happened.
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
    data = process_scraper_data()
    # data_to_force_graph(data)
    data_to_collapsible_graph(data)
    # visualize_network(nodes, links)

if __name__ == "__main__":
    main()
