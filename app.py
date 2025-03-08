from flask import Flask, request, render_template, jsonify
import requests
import subprocess

app = Flask(__name__)

# Replace with your Google Custom Search API key and Engine ID
GOOGLE_API_KEY = "ADD YOU KEY HERE"
GOOGLE_ENGINE_ID = "ADD YOUR KEY HERE"
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

# Default Ollama command
OLLAMA_CMD = "ollama"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    # Get the search query and selected model from the form
    query = request.form.get('query')
    model = request.form.get('model')  # Get the selected model from the form

    # Debug: Print the query and model to the terminal
    print(f"Query: {query}, Model: {model}")

    # Validate the query and model
    if not query:
        return jsonify({"error": "No query provided"}), 400

    if not model:
        return jsonify({"error": "No model selected"}), 400

    # Step 1: Search using Google Custom Search
    params = {
        'key': GOOGLE_API_KEY,
        'cx': GOOGLE_ENGINE_ID,
        'q': query,
        'num': 2  # Limit to top 2 results
    }
    response = requests.get(GOOGLE_SEARCH_URL, params=params)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch results from Google Custom Search"}), 500

    # Get the top 2 results from Google Custom Search
    results = response.json().get('items', [])[:2]

    # Step 2: Summarize each result using Ollama with the selected model
    summarized_results = []
    for result in results:
        title = result.get('title', 'No Title')  # Get the title or use a default
        url = result.get('link', '#')  # Get the URL or use a default
        content = result.get('snippet', '')  # Get the snippet or default to an empty string

        # Skip summarization if content is empty or None
        if not content:
            summarized_results.append({
                'title': title,
                'url': url,
                'summary': 'No content available for summarization.'
            })
            continue

        # Ensure content is a string and limit its length to 500 characters
        content = str(content)[:500]

        # Use Ollama to summarize the content with the selected model
        try:
            process = subprocess.Popen(
                [OLLAMA_CMD, "run", model, f"Summarize the following text: {content}"],  # Use the selected model
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True  # Ensure subprocess uses text mode
            )
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                # If the Ollama command fails, capture the error
                summary = f"Error summarizing: {stderr.strip()}"
            else:
                # If successful, capture the summary
                summary = stdout.strip()
        except Exception as e:
            # Handle any exceptions during the subprocess call
            summary = f"Error summarizing: {str(e)}"

        # Add the summarized result to the list
        summarized_results.append({
            'title': title,
            'url': url,
            'summary': summary
        })

    # Return the summarized results as JSON
    return jsonify(summarized_results)

if __name__ == '__main__':
    app.run(host='192.168.50.12', debug=True)
