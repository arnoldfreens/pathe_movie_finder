import requests
import json
from bs4 import BeautifulSoup

#First we get the HTML content
def get_theater_html_content(url):
    response = requests.get(url)
    return response.text

# Retrieve JSON containing relevant data on movies playing
def parse_html_for_json_movie(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    script_tag = soup.find('script', {'type' : 'application/ld+json'})
    return json.loads(script_tag.string)
