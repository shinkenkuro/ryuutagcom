import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import random

# List User-Agents untuk menghindari blokir
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0.1 Mobile/15E148 Safari/537.36"
]

# Konfigurasi sesi global dengan proxy opsional
session = requests.Session()
PROXY = "http://44.215.100.135:8118"    # Ganti dengan proxy jika diperlukan, contoh: "http://username:password@proxyserver:port"

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive"
    }

def fetch_url(url):
    try:
        time.sleep(random.uniform(2, 5))  # Delay random untuk menghindari deteksi bot
        response = session.get(url, headers=get_headers(), proxies={"http": PROXY, "https": PROXY} if PROXY else None)
        if response.status_code == 403:
            st.error(f"Access Denied (403) for {url}. Coba gunakan VPN atau proxy.")
            return None
        elif response.status_code != 200:
            st.error(f"Error fetching {url}, Status Code: {response.status_code}")
            return None
        return response.content
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
        return None

# Fungsi untuk scraping satu halaman berdasarkan URL tag
def scrape_page(url):
    content = fetch_url(url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    titles = soup.find_all('h3', class_='entry-title td-module-title')
    results = []
    
    for title in titles:
        a_tag = title.find('a')
        img_tag = title.find_parent().find('img', class_='entry-thumb') if title.find_parent() else None
        
        post_title = a_tag.get('title') if a_tag else "No Title"
        post_link = a_tag.get('href') if a_tag else "#"
        post_img = img_tag.get('data-img-url') if img_tag and 'data-img-url' in img_tag.attrs else None
        
        results.append({
            'title': post_title,
            'link': post_link,
            'img': post_img
        })
    return results

# Fungsi untuk mendeteksi jumlah halaman berdasarkan tag URL
def detect_max_pages(tag_url):
    content = fetch_url(tag_url)
    if not content:
        return 1
    
    soup = BeautifulSoup(content, 'html.parser')
    page_nav = soup.find('div', class_='page-nav td-pb-padding-side')
    
    if page_nav:
        last_page_link = page_nav.find('a', class_='last')
        if last_page_link:
            return int(last_page_link['title'])
        else:
            page_numbers = [int(a_tag['title']) for a_tag in page_nav.find_all('a', class_='page') if 'title' in a_tag.attrs]
            if page_numbers:
                return max(page_numbers)
    return 1

# Fungsi untuk scrape beberapa halaman berdasarkan tag
def scrape_tag(tag_url):
    tag_url = tag_url.rstrip("/")  # Normalisasi URL
    max_pages = detect_max_pages(tag_url)
    all_results = []
    
    for page in range(1, max_pages + 1):
        page_url = f"{tag_url}/page/{page}/?0"
        page_results = scrape_page(page_url)
        all_results.extend(page_results)
    
    return all_results

# Fungsi untuk membandingkan hasil dari beberapa tag
def compare_tags(tag_urls, exclude_urls):
    tag_results = [scrape_tag(tag_url) for tag_url in tag_urls]
    exclude_results = [scrape_tag(tag_url) for tag_url in exclude_urls]
    
    if tag_results:
        common_entries = set(tuple(entry.items()) for entry in tag_results[0])
        for results in tag_results[1:]:
            common_entries &= set(tuple(entry.items()) for entry in results)
        
        # Menghapus entri yang ada dalam daftar eksklusi
        exclude_entries = set(tuple(entry.items()) for exclude in exclude_results for entry in exclude)
        common_entries -= exclude_entries
        
        return [dict(entry) for entry in common_entries]
    return []

# Streamlit UI
st.title("Web Scraper dan Perbandingan Tags")
st.write("Masukkan URL tag untuk dibandingkan")

num_tags = st.number_input("Berapa banyak tag URL yang ingin di-input?", min_value=1, step=1)
num_exclude = st.number_input("Berapa banyak tag URL yang ingin dikecualikan?", min_value=0, step=1)

tag_urls = []
for i in range(num_tags):
    url = st.text_input(f"Masukkan URL tag ke-{i+1}")
    if url:
        tag_urls.append(url)

exclude_urls = []
for i in range(num_exclude):
    url = st.text_input(f"Masukkan URL tag yang ingin dikecualikan ke-{i+1}")
    if url:
        exclude_urls.append(url)

if st.button("Mulai Scraping") and tag_urls:
    st.write(f"Tag URLs: {tag_urls}")
    st.write(f"Exclude URLs: {exclude_urls}")
    
    common_entries = compare_tags(tag_urls, exclude_urls)
    
    if common_entries:
        st.subheader("Hasil Perbandingan")
        cols = st.columns(3)
        for idx, entry in enumerate(common_entries):
            with cols[idx % 3]:
                if entry['img']:
                    st.image(entry['img'], use_container_width=True)
                st.markdown(f"[**{entry['title']}**]({entry['link']})")
    else:
        st.warning("Tidak ada entri yang sama ditemukan atau semua hasil telah dikecualikan.")