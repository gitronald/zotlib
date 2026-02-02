from bs4 import BeautifulSoup
import requests

# Replace with the URL of the page you want to parse
url = "https://psycnet.apa.org/record/2021-49362-001"
response = requests.get(url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Find the meta tag with the name "citation_doi"
doi_meta = soup.find('meta', attrs={'name': 'citation_doi'})

# Extract the DOI from the content attribute
if doi_meta:
    doi = doi_meta.get('content')
    print(f"DOI: {doi}")
else:
    print("DOI not found")