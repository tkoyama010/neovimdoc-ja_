import requests
from bs4 import BeautifulSoup
import os
import polib
from urllib.parse import urljoin, urlparse

# Base URL and output directories
base_url = "https://neovim.io/doc/user/"
output_dir = "./translated_html"
po_dir = "./po_files"

# Create output directories
os.makedirs(output_dir, exist_ok=True)
os.makedirs(po_dir, exist_ok=True)

# Set to keep track of visited URLs to avoid duplicates
visited_urls = set()

# Function to fetch HTML content from the website
def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to retrieve {url}")
        return None

# Function to extract text from HTML and create a PO file
def create_po_file(html_content, po_file_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    po = polib.POFile()

    # Extract text and add it to the PO file
    for tag in soup.find_all(text=True):
        text = tag.strip()
        if text:
            entry = polib.POEntry(msgid=text, msgstr="")
            po.append(entry)

    po.save(po_file_path)
    print(f"PO file created at {po_file_path}")

# Function to translate the PO file into Japanese
def translate_po_file(po_file_path, translated_po_file_path):
    po = polib.pofile(po_file_path)

    # Example: Manually add a translation
    # In practice, this could use a translation API or a dictionary
    for entry in po:
        entry.msgstr = "Japanese translation: " + entry.msgid  # Example translation

    po.save(translated_po_file_path)
    print(f"Translated PO file saved at {translated_po_file_path}")

# Function to apply translations from the PO file to the HTML content
def apply_translation_to_html(html_content, translated_po_file_path, output_html_path):
    soup = BeautifulSoup(html_content, 'html.parser')
    po = polib.pofile(translated_po_file_path)

    translations = {entry.msgid: entry.msgstr for entry in po}

    # Replace original text with translated text
    for tag in soup.find_all(text=True):
        text = tag.strip()
        if text in translations:
            tag.replace_with(translations[text])

    # Save the translated HTML content
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup.prettify()))

    print(f"Translated HTML saved at {output_html_path}")

# Function to recursively fetch and process all HTML files
def fetch_and_process_all_html(url):
    # Avoid revisiting the same URL
    if url in visited_urls:
        return
    visited_urls.add(url)

    # Fetch the HTML content
    html_content = fetch_html(url)
    if not html_content:
        return

    # Create a local path for the output
    parsed_url = urlparse(url)
    html_filename = os.path.join(output_dir, parsed_url.path.lstrip('/') + "index.html")
    po_filename = os.path.join(po_dir, parsed_url.path.lstrip('/').replace('/', '_') + ".po")

    # Ensure the directories exist
    os.makedirs(os.path.dirname(html_filename), exist_ok=True)

    # Create the PO file and apply translation
    create_po_file(html_content, po_filename)
    translated_po_filename = po_filename.replace(".po", "_translated.po")
    translate_po_file(po_filename, translated_po_filename)
    apply_translation_to_html(html_content, translated_po_filename, html_filename)

    # Parse the HTML and find all links
    soup = BeautifulSoup(html_content, 'html.parser')
    for link_tag in soup.find_all('a', href=True):
        link_url = urljoin(url, link_tag['href'])

        # Only process internal links (same domain)
        if base_url in link_url and link_url not in visited_urls and link_url.endswith('.html'):
            fetch_and_process_all_html(link_url)

# Main process
def main():
    # Start by processing the base URL recursively
    fetch_and_process_all_html(base_url)

if __name__ == "__main__":
    main()
