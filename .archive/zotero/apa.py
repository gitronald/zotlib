import textwrap
import pandas as pd

def check_key_value_exists(d, key):
    return key in d and not pd.isna(d[key])
    
def format_apa_reference(row):
    """
    Formats a row of a DataFrame into an APA reference string.

    Parameters:
        row (pd.Series): A row of a pandas DataFrame containing the fields 'authors',
                         'date', 'title', 'publication', 'volume', 'issue', 'pages',
                         'DOI', and 'url'.

    Returns:
        str: The formatted APA reference string.
    """
    # Start building the reference string
    reference = f"{row['authors']} ({row['year']}) {row['title']}."
    publication_details = ""

    if check_key_value_exists(row, 'publication'):
        publication_details += f"{row['publication']}"

    if check_key_value_exists(row, 'volume'):
        publication_details += f", {row['volume']}"
    
    if row['typeName'] == 'journalArticle':
        print(publication_details)
        reference += "_"+publication_details+"_"
    
    if check_key_value_exists(row, 'issue'):
        reference += f" ({row['issue']})."

    if check_key_value_exists(row, 'pages'):
        reference = reference[:-1] + f", {row['pages']}."

    # DOI or URL
    if check_key_value_exists(row, 'DOI'):
        # Add a hyperlink to the DOI if available
        ahref = f'<a href="https://doi.org/{row["DOI"]}" target="_blank">'
        reference += f' {ahref}{row["DOI"]}</a>. '
    elif check_key_value_exists(row, 'url'):
        # If no DOI is available, add a hyperlink to the URL
        ahref = f'<a href="{row["url"]}" target="_blank">'
        reference += f' {ahref}{row["url"]}</a>.'

    return reference


# ------------------------------------------------------------------------------
# Load items

dtypes = {
    'itemID': 'int64',
    'typeName': 'string',
    'title': 'string',
    'publication': 'string',
    'year': 'int64',
    'month': 'int64',
    'volume': 'string',
    'issue': 'string',
    'pages': 'string',
    'DOI': 'string',
    'url': 'string'
}

fp_items = 'data/cv.csv'
items = pd.read_csv(fp_items, dtype=dtypes, parse_dates=['date'])
items = items.sort_values("date", ascending=False)

# Create APA references
items['reference'] = items.apply(format_apa_reference, axis=1)

# Write to file
with open('output/apa.md', 'w') as outfile:
    for group, gdf in items.groupby("typeName"):
        outfile.write(f"{group} {''.join(['-']*50)}\n\n")
        for idx, reference in enumerate(gdf['reference'].tolist()):
            # print(textwrap.fill(reference, 100), '\n')
            outfile.write(f'{reference}\n\n')

# Wider column width
pd.set_option('display.width', 120)
pd.set_option('display.max_colwidth', 120)