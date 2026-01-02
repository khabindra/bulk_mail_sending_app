from django.http import HttpResponse

def home(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Bulk Mail Services - Home</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                color: #333;
            }
            header {
                background-color: #007BFF;
                padding: 20px;
                width: 100%;
                text-align: center;
                color: white;
            }
            h1 {
                margin: 0;
            }
            p {
                max-width: 600px;
                text-align: center;
                margin: 20px auto;
                font-size: 1.2em;
            }
            a.button {
                display: inline-block;
                padding: 15px 25px;
                margin-top: 20px;
                background-color: #007BFF;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-size: 1em;
            }
            a.button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Welcome to Bulk Mail Services</h1>
        </header>
        <p>Efficiently send your emails to a large audience with our reliable bulk mail solutions. Manage campaigns, track delivery, and ensure your message reaches everyone.</p>
        <a href="/register" class="button">Get Started</a>
    </body>
    </html>
    """
    return HttpResponse(html_content)