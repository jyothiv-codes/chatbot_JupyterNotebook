
import os
import requests
from bs4 import BeautifulSoup
import spacy
import textwrap
from prettytable import PrettyTable
import networkx as nx
import matplotlib.pyplot as plt


api_key = os.getenv(api_key)
cse_id = os.getenv(cse_id)
# Load the spaCy language model
nlp = spacy.load("en_core_web_sm")

def google_search(query, api_key, cse_id, num_results=10):
    search_url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}&num={num_results}"
    response = requests.get(search_url)
    results = response.json().get('items', [])
    print("Google search completed")
    return [item['link'] for item in results]

def extract_relevant_info(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        if not title_tag:
            print(f"Skipping {url}: No title tag found.")
            return {"error": "No title tag found"}

        title = title_tag.get_text()
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])
        
        return {"title": title, "text": text}
    
    except requests.exceptions.RequestException as e:
        print(f"Skipping {url}: {str(e)}")
        return {"error": str(e)}

def wrap_text(text, width):
    return "\n".join(textwrap.wrap(text, width=width))

def print_formatted_output(results):
    table = PrettyTable()
    table.field_names = ["Title", "Text"]

    for result in results:
        wrapped_title = wrap_text(result['title'], width=30)
        wrapped_text = wrap_text(result['text'], width=50)
        table.add_row([wrapped_title, wrapped_text])

    print(table)

def save_to_file(results, filename="output.txt"):
    with open(filename, "w") as file:
        for result in results:
            file.write(result['title'] + "\n\n")
            file.write(result['text'] + "\n")
            file.write("\n" + "="*50 + "\n\n")  # Separator between entries

def extract_entities_and_relationships(text):
    doc = nlp(text)
    entities = set()
    relationships = []

    # Extract entities
    for ent in doc.ents:
        entities.add((ent.text, ent.label_))

    # Extract simple relationships (basic dependency parsing)
    for token in doc:
        if token.dep_ in ('nsubj', 'dobj', 'attr'):
            head = token.head
            if head.dep_ in ('ROOT', 'prep'):
                relationship = (token.text, head.text)
                if relationship not in relationships:
                    relationships.append(relationship)

    print("Extracted Entities:", entities)
    print("Extracted Relationships:", relationships)
    G = nx.DiGraph()
    for relationship in relationships:
        entity1, entity2 = relationship
        G.add_edge(entity1, entity2)

    # Graph to be drawn for the following node
    node_of_interest = 'Altera'
    nodes_of_interest = list(G.neighbors(node_of_interest)) + [node_of_interest]
    subgraph = G.subgraph(nodes_of_interest)

    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(subgraph, seed=42)  
    nx.draw_networkx_nodes(subgraph, pos, node_size=2000, node_color='lightblue')
    nx.draw_networkx_edges(subgraph, pos, width=2, alpha=0.5, edge_color='b')
    nx.draw_networkx_labels(subgraph, pos, font_size=12, font_family='sans-serif')

    plt.title(f'Subgraph Centered Around {node_of_interest}')
    plt.show()


    return entities, relationships

def plot_graph(entities, relationships):
    G = nx.Graph()

    # Add nodes with labels
    for entity, label in entities:
        G.add_node(entity, label=label)

    # Add edges
    for rel in relationships:
        if len(rel) == 2 and rel[0] in G.nodes and rel[1] in G.nodes:
            G.add_edge(rel[0], rel[1])

    print("Nodes in Graph:", G.nodes)
    print("Edges in Graph:", G.edges)

    pos = nx.spring_layout(G)  # or another layout algorithm
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=500, edge_color='gray', font_size=10, font_weight='bold')
    plt.show()



def user_input_kg(query, api_key, cse_id):
    if len(query) > 0:
        curr_query = query
    else:
        curr_query = 'use cases of transformers in machine learning'
    query = curr_query
    urls = google_search(query, api_key, cse_id)
    all_entities = set()
    all_relationships = []
    results = []

    for url in urls:
        print("Currently processing", url)
        info = extract_relevant_info(url)
        if "error" not in info:
            results.append(info)
            entities, relationships = extract_entities_and_relationships(info['text'])
            all_entities.update(entities)
            all_relationships.extend(relationships)

    print_formatted_output(results)
    plot_graph(all_entities, all_relationships)
    return results


user_input_kg("Altera infuses AI", api_key, cse_id)
#user_input_kg("use cases of transformers in machine learning", api_key, cse_id)
