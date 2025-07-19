import requests

@app.route('/getupdates')
def get_updates():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    res = requests.get(url)
    return res.text