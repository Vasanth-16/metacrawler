import asyncio
import aiohttp
from urllib.parse import quote_plus
from flask import Flask, render_template, request
import webbrowser
app = Flask(__name__)


GOOGLE_API_KEY = "xxxxxxxxxxxxxxx"
GOOGLE_CX = "xxxxxxxxxxxxx"
BING_API_KEY = "xxxxxxxxxxxxx"

async def fetch(session, url, headers=None):
    
    try:
        async with session.get(url, headers=headers) as response:
            return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def search_google(query, num_results=30):
   
    results = []
    for start in range(1, num_results, 10):  
        url = f"https://www.googleapis.com/customsearch/v1?q={quote_plus(query)}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&num=10&start={start}"
        async with aiohttp.ClientSession() as session:
            data = await fetch(session, url)
            if data and "items" in data:
                results.extend([{"title": item["title"], "link": item["link"]} for item in data["items"]])
    return results[:num_results]  

async def search_bing(query, num_results=30):
    
    url = f"https://api.bing.microsoft.com/v7.0/search?q={quote_plus(query)}&count={num_results}"
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url, headers)
        if data and "webPages" in data:
            return [{"title": item["name"], "link": item["url"]} for item in data["webPages"]["value"]]
    return []

async def search_duckduckgo(query, num_results=20):
    
    url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json"
    async with aiohttp.ClientSession() as session:
        data = await fetch(session, url)
        if data and "RelatedTopics" in data:
            results = [{"title": item["Text"], "link": item["FirstURL"]} for item in data if "Text" in item and "FirstURL" in item]
            return results[:num_results]  
    return []

async def meta_search(query, num_results=60):
    
    google_results, bing_results, duckduckgo_results = await asyncio.gather(
        search_google(query, num_results=30),
        search_bing(query, num_results=30),
        search_duckduckgo(query, num_results=20),
    )

    all_results = google_results + bing_results + duckduckgo_results


    unique_results = []
    seen_links = set()
    for result in all_results:
        if result["link"] not in seen_links:
            unique_results.append(result)
            seen_links.add(result["link"])

    return unique_results[:num_results]  

@app.route("/", methods=["GET", "POST"])
async def index():
    results = []
    if request.method == "POST":
        search_query = request.form.get("search_query", "").strip()
        if search_query:
            results = await meta_search(search_query, num_results=60)  
    return render_template("index.html", results=results)

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5001")  
    app.run(debug=True, host="127.0.0.1", port=5001)
