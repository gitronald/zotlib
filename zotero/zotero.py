""" Zotero Database to CSV

usage: python zotero.py


"""

import os
import utils
import sqlite3
import pandas as pd

def load_database(database_path):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    return cursor


def get_column_names(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    cols = next(zip(*cursor.description))
    return cols


def get_table_names(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [item[0] for item in cursor.fetchall()]
    return table_names


def get_table_entries(cursor, query, table_names=[], as_df=True):
    entries = cursor.execute(query).fetchall()
    if table_names and as_df:
        cols = utils.unlist([get_column_names(cursor, t) for t in table_names])
        return pd.DataFrame(entries, columns=cols)
    else:
        return entries

# import argparse as ap
# parser = ap.ArgumentParser()
# parser.add_argument("fp", "--filepath", required=True, 
#                     help="path to zotero.sqlite file")

# ------------------------------------------------------------------------------
# Settings

zotero_dir = "/mnt/c/Users/rer/Zotero"
zotero_fp = os.path.join(zotero_dir, "zotero.sqlite")
cursor = load_database(zotero_fp)
table_names = get_table_names(cursor)
print("Tables: ", table_names)

# ------------------------------------------------------------------------------
# Explore database tables

tables = {}
for table_name in table_names:
    cols = get_column_names(cursor, table_name)
    entries = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
    tables[table_name] = pd.DataFrame(entries, columns=cols)

for table_name, table in tables.items():
    utils.print_line()
    print(f"{table_name} - {table.shape}")
    if not table.empty:
        print(table.head())

# ------------------------------------------------------------------------------
# Join item IDs with fields and values

# Primary item linkage table
# itemData - (27482, 3)
#    itemID  fieldID  valueID
# 0       1        1        1
# 1       1        6        2
# 2       1       11        3
# 
# This table contains links between items and fields.
# So if we take itemID == 1
# 
# tables['itemData'].query("itemID == @itemID")
#     itemID  fieldID  valueID
# 0        1        1        1
# 1        1        6        2
# 2        1       11        3
# 3        1       13        4
# 4        1       14        5
# 5        1       16        6
# 6        1       19        7
# 7        1       32        8
# 8        1       37        9
# 9        1       70       10
# 10       1       73       11
# 
# So we want to get the values for the fields in `fieldsCombined` and the 
# values in `itemDataValues` that are associated with this item.

# Python approach
# Get field and value keys for a single item
# itemID = 1
# item = tables['itemData'].query("itemID == @itemID")
# item_fields = tables['fieldsCombined'].query("fieldID in @item['fieldID']")
# item_values = tables['itemDataValues'].query("valueID in @item['valueID']")
# item = item.merge(item_fields, on='fieldID').merge(item_values, on='valueID')
# item = item.set_index("fieldName")['value']

# SQL approach

def get_items(cursor):
    """ Get zotero items and merge details"""

    query = "SELECT * FROM items"
    table_names = ["items"]
    items = get_table_entries(cursor, query, table_names)

    # Get item details
    #   itemData : itemID, fieldID, valueID
    #   fieldsCombined : fieldID, fieldName, ...
    #   itemDataValues : valueID, value, ...
    query = """
    SELECT * FROM itemData
    LEFT JOIN fieldsCombined ON itemData.fieldID = fieldsCombined.fieldID
    LEFT JOIN itemDataValues ON itemData.valueID = itemDataValues.valueID
    """
    table_names = ['itemData', 'fieldsCombined', 'itemDataValues']
    entries = get_table_entries(cursor, query, table_names)
    details = entries.pivot(index='itemID', columns='fieldName', values='value')
    details = details.rename_axis(None, axis=1).reset_index()
    items = items.merge(details, how='left', on='itemID')

    # Merge item type names
    itemtypes = get_itemtypes(cursor)
    items = items.merge(itemtypes[['itemTypeID', 'typeName']], how='left', 
                        on='itemTypeID', validate='m:1')

    return items


def get_itemtypes(cursor):
    # Merge item types
    query = """
    SELECT * FROM itemTypes
    """
    table_names = ['itemTypes']
    return get_table_entries(cursor, query, table_names)


def get_creators(cursor):
    # Merge creators
    query = """
    SELECT * FROM itemCreators
    LEFT JOIN creators ON itemCreators.creatorID = creators.creatorID
    """
    table_names = ['itemCreators', 'creators']
    return get_table_entries(cursor, query, table_names)


def get_collections(cursor):
    # Merge collections
    query = """
    SELECT * FROM collectionItems
    LEFT JOIN collections ON collectionItems.collectionID = collections.collectionID
    """
    table_names = ['collectionItems', 'collections']
    return get_table_entries(cursor, query, table_names)

def get_libraries(cursor):
    # Merge libraries
    query = """
    SELECT * FROM libraries
    """
    table_names = ['libraries']
    return get_table_entries(cursor, query, table_names)


def save_csv(df, fp):
    df.to_csv(fp, index=False)
    print(f"saved: {fp} - {df.shape}")

# ------------------------------------------------------------------------------
# Save tables

items = get_items(cursor)
save_csv(items, "data/items.csv")

creators = get_creators(cursor)
save_csv(creators, "data/creators.csv")

collections = get_collections(cursor)
save_csv(collections, "data/collections.csv")

libraries = get_libraries(cursor)
save_csv(libraries, "data/libraries.csv")



# Concat creator names to single string "authors"
sep = ", "
creators['authors'] = creators['firstName'] + " " + creators['lastName']
item_creators = creators.groupby('itemID')['authors'].apply(lambda x: sep.join(x))
items = items.merge(item_creators, how='left', on='itemID')

# ------------------------------------------------------------------------------
# Condense publication title

title_cols = [
    'publicationTitle',
    'blogTitle', 'bookTitle', 'encyclopediaTitle', 'proceedingsTitle', 
    'seriesTitle', 'websiteTitle', 
    'publisher'
]
# mask = items.publicationTitle.isnull()
# items['n_titles'] = items[mask][title_cols].notnull().sum(axis=1)

def get_first_notnull(row):
    """ Get first not null value in row """
    valid_index = row.first_valid_index()
    return None if valid_index is None else row[valid_index]

items['publication'] = items[title_cols].apply(get_first_notnull, axis=1)

# ------------------------------------------------------------------------------
# Condense paper title

title_cols = [
    'titile', 'caseName', 'thesisTitle'
]

# items['title'] = items[title_cols].apply(get_first_notnull, axis=1)

# ------------------------------------------------------------------------------
# Clean

# Get datetime
items['date_raw'] = items['date'].copy()
items['datefmt'] = items['date_raw'].fillna('').str.split(' ', expand=True)[0]
mask = items.datefmt.str.endswith("00") # e.g. 2003-01-00 -> dt convert error
items.loc[mask, 'datefmt'] = items.loc[mask, 'datefmt'].str.split('-', expand=True)[0]
items['date'] = pd.to_datetime(items['datefmt'], errors='coerce')
items['year'] = items.date.dt.year
items['month'] = items.date.dt.month

# Check still missing dates
mask_no_date = ((items.date.isnull()) & items.date_raw.notnull())
print(f"items with no date: {mask_no_date.sum()}")
print(items[mask_no_date][['date_raw', 'datefmt']])

# Encoded characters
items['pages'] = items['pages'].fillna('').str.replace("–", "-")

# ------------------------------------------------------------------------------
# Filter columns

cols_main = ['itemID', 'typeName', 'authors', 'title', 'date', 'year',
             'publication', 'volume', 'issue', 'pages',  
             'DOI', 'url']
items[cols_main]

# ------------------------------------------------------------------------------
# Save CV items
cv = collections.query("collectionName == 'rer'")
cv_items = items.query("itemID in @cv['itemID']")
cv_items = cv_items[cols_main]
save_csv(cv_items, "data/cv.csv")

pd.set_option('display.width', 120)
pd.set_option('display.max_columns', 200)
