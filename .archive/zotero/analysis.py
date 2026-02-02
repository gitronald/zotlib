"""Analyze Zotero Data"""

import pandas as pd

fp = "/home/rer/proj/zotero/data/cv.csv"
df = pd.read_csv(fp)
# df.head()


tab = df.year.value_counts().sort_index(ascending=False).reset_index()
tab.columns = ['year', 'count']
display(tab)
