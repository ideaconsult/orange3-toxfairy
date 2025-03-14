import pandas as pd
from pyvis.network import Network
import re
import os.path


# + tags=["parameters"]
upstream = []
product = None
aop_file = None
# -

os.makedirs(product["aop_graph"], exist_ok=True)


def sanitize_filename(query):
    sanitized_query = re.sub(r'[\\/*?:"<>|]', '_', query)
    sanitized_query = sanitized_query.replace(' ', '_')
    return sanitized_query


df = pd.read_excel(aop_file)

df = df.dropna(subset=['type_s'])
df_new = df[['id', 'query', 'upstream_ke_s', 'downstream_ke_s', 'short_name_t']]
df_new = df_new.loc[df_new['query'] != r"gamma\ H2AX"]
unique_queries = df_new['query'].unique()

for query in unique_queries:
    df_filtered = df_new[df_new['query'] == query]
    net = Network(height="800px", width="1000px", directed=True)

    for index, row in df_filtered.iterrows():
        node_label = row['id']
        if pd.notna(row['short_name_t']):
            node_label = f"{row['id']} - {row['short_name_t']}"

        if row['id'] not in net.get_nodes():
            net.add_node(row['id'], label=node_label)

        if pd.notna(row['upstream_ke_s']) and not row['upstream_ke_s'].startswith('KER'):
            if row['upstream_ke_s'] not in net.get_nodes():
                net.add_node(row['upstream_ke_s'], label=row['upstream_ke_s'], color='rgba(255,0,0,0.4)')

        if pd.notna(row['downstream_ke_s']) and not row['downstream_ke_s'].startswith('KER'):
            if row['downstream_ke_s'] not in net.get_nodes():
                net.add_node(row['downstream_ke_s'], label=row['downstream_ke_s'], color='rgba(255,0,0,0.4)')

    for index, row in df_filtered.iterrows():
        if pd.notna(row['upstream_ke_s']) and pd.notna(row['downstream_ke_s']):
            if row['upstream_ke_s'] not in net.get_nodes():
                net.add_node(row['upstream_ke_s'], label=row['upstream_ke_s'])

            if row['downstream_ke_s'] not in net.get_nodes():
                net.add_node(row['downstream_ke_s'], label=row['downstream_ke_s'])

            net.add_edge(row['upstream_ke_s'], row['downstream_ke_s'], label=row['id'],
                         font={'color': 'red', 'weight': 'bold'})

    # net.show_buttons(filter_=['physics'])
    sanitized_query = sanitize_filename(query)
    file_name = os.path.join(product["aop_graph"], f"network_graph_{sanitized_query}.html")
    net.show(file_name, notebook=False)

