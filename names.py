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


HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Georgian Surname Lookup</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
        }

        h1 {
            text-align: center;
            margin-bottom: 10px;
            color: #fff;
            font-size: 2.2rem;
        }

        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 40px;
            font-size: 0.95rem;
        }

        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }

        .input-group {
            margin-bottom: 20px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #aaa;
            font-size: 0.9rem;
            font-weight: 500;
        }

        input[type="text"] {
            width: 100%;
            padding: 14px 18px;
            font-size: 1.1rem;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #4a9eff;
            box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.2);
        }

        input[type="text"]::placeholder {
            color: #666;
        }

        .btn {
            width: 100%;
            padding: 16px;
            font-size: 1.1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-primary {
            background: linear-gradient(135deg, #4a9eff 0%, #2d7dd2 100%);
            color: #fff;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(74, 158, 255, 0.3);
        }

        .btn-primary:active {
            transform: translateY(0);
        }

        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .results {
            display: none;
        }

        .results.visible {
            display: block;
        }

        .results-header {
            text-align: center;
            margin-bottom: 25px;
        }

        .results-header h2 {
            color: #fff;
            font-size: 1.5rem;
            margin-bottom: 8px;
        }

        .surname-display {
            font-size: 2rem;
            color: #4a9eff;
            font-weight: 700;
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
        }

        .stat-box {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }

        .stat-label {
            color: #888;
            font-size: 0.85rem;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value {
            color: #fff;
            font-size: 1.6rem;
            font-weight: 700;
        }

        .stat-subvalue {
            color: #666;
            font-size: 0.85rem;
            margin-top: 4px;
        }

        .country-table {
            width: 100%;
            border-collapse: collapse;
        }

        .country-table th {
            text-align: left;
            padding: 12px 16px;
            color: #888;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .country-table td {
            padding: 14px 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .country-table tr:last-child td {
            border-bottom: none;
        }

        .country-name {
            color: #fff;
            font-weight: 500;
        }

        .country-count {
            color: #4a9eff;
            font-weight: 600;
        }

        .country-freq {
            color: #888;
            font-size: 0.9rem;
        }

        .error-message {
            background: rgba(220, 53, 69, 0.15);
            border: 1px solid rgba(220, 53, 69, 0.3);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            color: #ff6b6b;
        }

        .loading {
            text-align: center;
            padding: 40px;
        }

        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top-color: #4a9eff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 16px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading-text {
            color: #888;
        }

    </style>
</head>
<body>
    <div class="container">
        <h1>Georgian Surname Lookup</h1>
        <p class="subtitle">Enter a surname in Georgian script to find its global distribution</p>

        <div class="card">
            <div class="input-group">
                <label for="georgianInput">Georgian Script</label>
                <input type="text" id="georgianInput" placeholder="e.g. ბერიძე" autocomplete="off">
            </div>

            <div class="input-group" style="margin-top: 20px;">
                <label for="latinInput">Latin Transliteration</label>
                <input type="text" id="latinInput" placeholder="e.g. Beridze" autocomplete="off">
            </div>

            <button class="btn btn-primary" id="searchBtn" style="margin-top: 20px;">
                Search
            </button>
        </div>

        <div class="card results" id="resultsCard">
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        const georgianInput = document.getElementById('georgianInput');
        const latinInput = document.getElementById('latinInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsCard = document.getElementById('resultsCard');
        const resultsContent = document.getElementById('resultsContent');

        // Georgian to Latin transliteration map
        const translitMap = {
            'ა': 'a', 'ბ': 'b', 'გ': 'g', 'დ': 'd', 'ე': 'e',
            'ვ': 'v', 'ზ': 'z', 'თ': 't', 'ი': 'i', 'კ': 'k',
            'ლ': 'l', 'მ': 'm', 'ნ': 'n', 'ო': 'o', 'პ': 'p',
            'ჟ': 'zh', 'რ': 'r', 'ს': 's', 'ტ': 't', 'უ': 'u',
            'ფ': 'p', 'ქ': 'k', 'ღ': 'gh', 'ყ': 'q', 'შ': 'sh',
            'ჩ': 'ch', 'ც': 'ts', 'ძ': 'dz', 'წ': 'ts', 'ჭ': 'ch',
            'ხ': 'kh', 'ჯ': 'j', 'ჰ': 'h'
        };

        function transliterate(text) {
            let result = '';
            for (let char of text) {
                result += translitMap[char] || char;
            }
            return result;
        }

        // Auto-transliterate on input
        georgianInput.addEventListener('input', function() {
            const georgianText = this.value;
            const latinText = transliterate(georgianText);
            latinInput.value = latinText;
        });

        // Search function
        async function searchSurname() {
            const surname = latinInput.value.trim();
            if (!surname) {
                alert('Please enter a surname');
                return;
            }

            // Show loading state
            searchBtn.disabled = true;
            resultsCard.classList.add('visible');
            resultsContent.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p class="loading-text">Searching for "${surname}"...</p>
                </div>
            `;

            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ surname })
                });

                const data = await response.json();

                if (data.error) {
                    resultsContent.innerHTML = `
                        <div class="error-message">
                            <strong>Not Found</strong><br>
                            ${data.error}
                        </div>
                    `;
                } else {
                    renderResults(data);
                }
            } catch (error) {
                resultsContent.innerHTML = `
                    <div class="error-message">
                        <strong>Error</strong><br>
                        Failed to connect to server: ${error.message}
                    </div>
                `;
            }

            searchBtn.disabled = false;
        }

        function renderResults(data) {
            // Calculate total from countries
            let totalFromCountries = 0;
            if (data.countries && data.countries.length > 0) {
                for (const c of data.countries) {
                    const countNum = parseInt(c.count.replace(/,/g, '')) || 0;
                    totalFromCountries += countNum;
                }
            }
            const globalCountNum = data.global_count ?
                parseInt(data.global_count.replace(/,/g, '')) || 0 :
                totalFromCountries;
            const globalCount = globalCountNum > 0 ?
                globalCountNum.toLocaleString() : 'N/A';

            // Calculate frequency as "1 in X people"
            const worldPopulation = 8000000000;
            let globalFreqText = 'N/A';
            if (globalCountNum > 0) {
                const oneIn = Math.round(worldPopulation / globalCountNum);
                globalFreqText = `1 in ${oneIn.toLocaleString()}`;
            }

            let countriesHtml = '';
            if (data.countries && data.countries.length > 0) {
                countriesHtml = `
                    <h3 style="color: #fff; margin-bottom: 15px; font-size: 1.1rem;">By Country</h3>
                    <table class="country-table">
                        <thead>
                            <tr>
                                <th>Country</th>
                                <th>Count</th>
                                <th>Frequency</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.countries.map(c => `
                                <tr>
                                    <td class="country-name">${c.name}</td>
                                    <td class="country-count">${Number(c.count).toLocaleString()}</td>
                                    <td class="country-freq">${c.frequency}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }

            resultsContent.innerHTML = `
                <div class="results-header">
                    <h2>Surname Distribution</h2>
                    <div class="surname-display">${data.surname}</div>
                    <div style="color: #4a9eff; font-size: 1.3rem; font-weight: 600; margin-top: 10px;">
                        Total: ${globalCount} people worldwide
                    </div>
                </div>

                <div class="stat-grid">
                    <div class="stat-box">
                        <div class="stat-label">Global Count</div>
                        <div class="stat-value">${globalCount}</div>
                        <div class="stat-subvalue">people worldwide</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Global Frequency</div>
                        <div class="stat-value">${globalFreqText}</div>
                        <div class="stat-subvalue">people worldwide</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Countries</div>
                        <div class="stat-value">${data.countries ? data.countries.length : 0}</div>
                        <div class="stat-subvalue">where found</div>
                    </div>
                </div>

                ${countriesHtml}
            `;
        }

        searchBtn.addEventListener('click', searchSurname);

        // Allow Enter key to trigger search
        latinInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchSurname();
            }
        });
    </script>
</body>
</html>
'''

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
