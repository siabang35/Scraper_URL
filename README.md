# 🕵️ LeadGen Scraper

**LeadGen Scraper** is a lead generation and enrichment tool built with Python and Streamlit. It supports lead scraping, validation, scoring, and enrichment using [Proxycurl API](https://nubela.co/proxycurl). The application features a user-friendly web interface for interacting with and analyzing leads.

---

## 📌 Features

- 🔍 Scrape and collect potential leads from websites or datasets.
- ✅ Validate email formats.
- 🌐 Extract domain and company names from emails or websites.
- 📊 Score leads based on available information.
- 💡 Enrich company data via Proxycurl API.
- 🧑‍💻 Interactive interface built with Streamlit.

---

## 💻 Project Structure

```
leadgen-scraper/
│
├── app/
│   ├── config.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── cohesive_clone.py
│   │   └── utils.py
│   ├── services/
│   │   └── enrichment.py
│   └── ui/
│       ├── components.py
│       └── streamlit_app.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   └── demo.ipynb
│
├── tests/
│   └── tests_scraper.py
│
├── .env
├── requirements.txt
├── README.md
└── submission_report.md
```

---

## ✅ Prerequisites

- Python 3.10 or higher
- Git
- Chrome & ChromeDriver (if scraping with Selenium or headless browser)
- Proxycurl API Key (for enrichment, optional)

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/siabang35/leadgen-scraper.git
cd leadgen-scraper
```

### 2. Create and Activate Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔐 Environment Configuration

Create a `.env` file in the root of the project:

```
.env
```

And add the following content:

```env
PROXYCURL_API_KEY=your_proxycurl_api_key_here

CHROME_DRIVER_PATH=C:\Users\your_name\Downloads\chromedriver-win64\chromedriver.exe

PYTHONPATH=.
```

---

## ▶️ Run the Streamlit App

To start the application:

```bash
# Make sure you are in the project root directory
streamlit run app/ui/streamlit_app.py
```

If you see this error:

```
ModuleNotFoundError: No module named 'app'
```

### ✅ Solution Option 1: Set PYTHONPATH before running

```bash
# On Windows
set PYTHONPATH=.
streamlit run app/ui/streamlit_app.py

# On macOS/Linux
export PYTHONPATH=.
streamlit run app/ui/streamlit_app.py
```

### ✅ Solution Option 2: Add path manually in the script

At the top of `streamlit_app.py`, add:

```python
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
```

---

## 🧪 Run Tests

To execute unit tests:

```bash
pytest tests/
```

---

## 📘 Notes

- Make sure ChromeDriver matches your Chrome version.
- Proxycurl API usage is optional but recommended for enrichment.
- Use `data/processed/` to store output CSV or JSON files after processing.

---

## 📄 License

MIT License. Free to use, modify, and distribute.

---

## 🙋 Support

If you encounter bugs or have suggestions, feel free to open an issue or pull request.

---

Happy scraping! 🚀
