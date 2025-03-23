import streamlit as st
import requests
from bs4 import BeautifulSoup

# Fungsi untuk scraping satu halaman berdasarkan URL tag
def scrape_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
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
    response = requests.get(tag_url)
    soup = BeautifulSoup(response.content, 'html.parser')
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
    max_pages = detect_max_pages(tag_url)
    all_results = []
    
    for page in range(1, max_pages + 1):
        page_url = f"{tag_url}/page/{page}/?0"
        page_results = scrape_page(page_url)
        all_results.extend(page_results)
    
    return all_results

# Fungsi untuk membandingkan hasil dari beberapa tag
def compare_tags(tag_urls):
    tag_results = [scrape_tag(tag_url) for tag_url in tag_urls]
    if tag_results:
        common_entries = set(tuple(entry.items()) for entry in tag_results[0])
        for results in tag_results[1:]:
            common_entries &= set(tuple(entry.items()) for entry in results)
        return [dict(entry) for entry in common_entries]
    return []

# Streamlit UI
st.title("Web Scraper dan Perbandingan Tags")
st.write("Masukkan URL tag untuk dibandingkan")
num_tags = st.number_input("Berapa banyak tag URL yang ingin di-input?", min_value=1, step=1)

tag_urls = []
for i in range(num_tags):
    url = st.text_input(f"Masukkan URL tag ke-{i+1}")
    if url:
        tag_urls.append(url)

if st.button("Mulai Scraping") and tag_urls:
    common_entries = compare_tags(tag_urls)
    if common_entries:
        st.subheader("Hasil Perbandingan")
        cols = st.columns(3)
        for idx, entry in enumerate(common_entries):
            with cols[idx % 3]:
                if entry['img']:
                    st.image(entry['img'], use_container_width=True)
                st.markdown(f"[**{entry['title']}**]({entry['link']})")
    else:
        st.warning("Tidak ada entri yang sama ditemukan.")
