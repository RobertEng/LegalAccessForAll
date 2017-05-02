'''
CS141 Legal Access For All
visualizer.py

'''

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
    nodes, links = [], []

    return nodes, links


def visualize_network(nodes, links):
    '''
    Visualize the passed in nodes and links in d3.js
    '''
    pass



def main():
    nodes, links = extract_network()
    visualize_network(nodes, links)

if __name__ == "__main__":
    main()
