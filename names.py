"""
Georgian Surname Lookup Tool
Flask backend with separate index.html frontend for surname transliteration and Forebears.io lookup.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for the API

# Georgian to Latin transliteration map (official National romanization standard)
GEORGIAN_TO_LATIN = {
    'ა': 'a', 'ბ': 'b', 'გ': 'g', 'დ': 'd', 'ე': 'e',
    'ვ': 'v', 'ზ': 'z', 'თ': 't', 'ი': 'i', 'კ': 'k',
    'ლ': 'l', 'მ': 'm', 'ნ': 'n', 'ო': 'o', 'პ': 'p',
    'ჟ': 'zh', 'რ': 'r', 'ს': 's', 'ტ': 't', 'უ': 'u',
    'ფ': 'p', 'ქ': 'k', 'ღ': 'gh', 'ყ': 'q', 'შ': 'sh',
    'ჩ': 'ch', 'ც': 'ts', 'ძ': 'dz', 'წ': 'ts', 'ჭ': 'ch',
    'ხ': 'kh', 'ჯ': 'j', 'ჰ': 'h'
}

def transliterate_georgian(text):
    """Convert Georgian script to Latin script using official romanization."""
    result = []
    i = 0
    while i < len(text):
        # Check for multi-character mappings first (though our map is single-char)
        char = text[i]
        if char in GEORGIAN_TO_LATIN:
            result.append(GEORGIAN_TO_LATIN[char])
        elif char.isalpha():
            # Keep non-Georgian letters as-is (for mixed input)
            result.append(char)
        else:
            # Keep spaces, punctuation, etc.
            result.append(char)
        i += 1
    return ''.join(result)


def scrape_forebears(surname):
    """
    Scrape surname data from Forebears.io.
    Returns global count, country breakdown, and frequency info.
    """
    url = f"https://forebears.io/surnames/{surname}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch data: {str(e)}'}

    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract global count
    global_count = None
    global_frequency = None

    # Look for the main count display
    count_elem = soup.find('span', class_='count')
    if not count_elem:
        count_elem = soup.find('span', {'data-bind': 'text: count'})
    if count_elem:
        count_text = count_elem.get_text(strip=True)
        # Extract number from text like "123,456"
        global_count = count_text.replace(',', '')

    # Look for frequency (1 in X people)
    freq_elem = soup.find('span', {'data-bind': 'text: frequency'})
    if not freq_elem:
        freq_elem = soup.find('span', class_='frequency')
    if freq_elem:
        global_frequency = freq_elem.get_text(strip=True)

    # Extract country breakdown from table
    countries = []
    table = soup.find('table')
    if table:
        rows = table.find_all('tr')[1:]  # Skip header row
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                # Country name (may be in a link)
                country_link = cols[0].find('a')
                country_name = country_link.get_text(strip=True) if country_link else cols[0].get_text(strip=True)

                # Count
                count_text = cols[1].get_text(strip=True) if len(cols) > 1 else 'N/A'
                count_val = count_text.replace(',', '')

                # Frequency
                freq_text = cols[2].get_text(strip=True) if len(cols) > 2 else 'N/A'

                # Rank
                rank_text = cols[3].get_text(strip=True) if len(cols) > 3 else 'N/A'

                countries.append({
                    'name': country_name,
                    'count': count_val,
                    'frequency': freq_text,
                    'rank': rank_text
                })

    # If no data found, surname might not exist
    if not global_count and not countries:
        return {'error': f'Surname "{surname}" not found on Forebears.io'}

    return {
        'surname': surname,
        'global_count': global_count,
        'global_frequency': global_frequency,
        'countries': countries
    }


@app.route('/')
def index():
    """Serve the main page."""
    return send_from_directory('.', 'index.html')


@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint to search for surname data."""
    data = request.get_json()

    if not data or 'surname' not in data:
        return jsonify({'error': 'No surname provided'}), 400

    surname = data['surname'].strip()
    if not surname:
        return jsonify({'error': 'Empty surname'}), 400

    result = scrape_forebears(surname)
    return jsonify(result)


if __name__ == '__main__':
    print("Starting Georgian Surname Lookup Tool...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
