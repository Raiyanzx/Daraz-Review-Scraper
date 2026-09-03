import os
import re
import json
import time
import requests
import pandas as pd

CONFIG_FILE = "config.json"

def load_config():
    """Loads headers and cookies from an external config file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"[!] Error: '{CONFIG_FILE}' not found. Please create it based on the README.")
        return None, None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        headers = cfg.get("headers", {})
        cookie_string = cfg.get("cookie_string", "")
        cookies = dict(item.strip().split('=', 1) for item in cookie_string.split(';') if '=' in item)
        return headers, cookies
    except Exception as e:
        print(f"[!] Error parsing '{CONFIG_FILE}': {e}")
        return None, None

def clean_file_name(name):
    """Sanitizes text so it can safely be part of a file or folder name."""
    if not name:
        return "Anonymous"
    return re.sub(r'[\\/*?:"<>| ]', '_', name)[:25]

def extract_item_id(raw_input):
    """Extracts numeric item ID from direct number or full product URL."""
    raw_input = raw_input.strip()
    if raw_input.isdigit():
        return raw_input
    match = re.search(r'-i(\d+)', raw_input)
    if match:
        return match.group(1)
    match_param = re.search(r'itemId=(\d+)', raw_input)
    if match_param:
        return match_param.group(1)
    return None

def download_image(url, save_path):
    """Downloads an individual image safely."""
    try:
        if url.startswith("//"):
            url = "https:" + url
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            return True
    except Exception as e:
        print(f"      [!] Failed downloading {url}: {e}")
    return False

def scrape_daraz():
    headers, cookies = load_config()
    if not headers or not cookies:
        return

    raw_input = input("Enter Daraz Product URL or Item ID: ").strip()
    item_id = extract_item_id(raw_input)
    if not item_id:
        print("[!] Invalid Input. Could not resolve a product ID.")
        return

    limit_input = input("How many reviews to scrape? (Press Enter for 100): ").strip()
    max_reviews = int(limit_input) if limit_input.isdigit() else 100

    print("\nSelect Scraping Mode:")
    print("  1. Reviews & Images (Organized in reviewer folders)")
    print("  2. Solo Reviews (No images, CSV only)")
    print("  3. Solo Images  (Organized in reviewer folders)")
    print("  4. Flat Images Only (All photos saved directly into one folder)")
    mode_choice = input("Enter choice (1, 2, 3, or 4) [Default: 1]: ").strip()
    if mode_choice not in ['1', '2', '3', '4']:
        mode_choice = '1'

    download_images = mode_choice in ['1', '3', '4']
    only_with_images = mode_choice in ['3', '4']
    use_subfolders = mode_choice in ['1', '3']
    save_csv = mode_choice in ['1', '2']

    base_img_dir = f"daraz_images_{item_id}"
    if download_images:
        os.makedirs(base_img_dir, exist_ok=True)

    all_reviews = []
    base_url = "https://my.daraz.com.bd/pdp/review/getReviewList"

    current_page = 1
    total_pages = 1
    downloaded_images_count = 0

    mode_labels = {
        '1': 'Reviews & Images (Subfolders)',
        '2': 'Solo Reviews (CSV only)',
        '3': 'Solo Images (Subfolders)',
        '4': 'Flat Images (Single folder)'
    }

    print(f"\n[*] Target Item: {item_id}")
    print(f"[*] Mode: {mode_labels[mode_choice]}")
    print("[*] Tip: Press Ctrl + C at any time to halt early and save.\n")

    try:
        while current_page <= total_pages:
            if len(all_reviews) >= max_reviews:
                print(f"[!] Target limit of {max_reviews} reached.")
                break

            params = {
                'itemId': item_id,
                'pageSize': '10',
                'filter': '0',
                'sort': '0',
                'pageNo': str(current_page)
            }

            resp = requests.get(base_url, headers=headers, cookies=cookies, params=params, timeout=10)
            if resp.status_code != 200:
                print(f"[!] HTTP error {resp.status_code} on page {current_page}")
                break

            data = resp.json()
            if not data or not data.get('success'):
                print(f"[!] Failed: {data.get('msgInfo') if data else 'Empty response or expired cookies'}")
                break

            model = data.get('model') or {}
            paging = model.get('paging') or {}
            total_pages = paging.get('totalPages', total_pages)
            items = model.get('items') or []

            if not items:
                print(f"[-] No more reviews returned on page {current_page}.")
                break

            for item in items:
                if not isinstance(item, dict):
                    continue

                raw_images = item.get('images') or []
                image_urls = [img.get('url') for img in raw_images if isinstance(img, dict) and img.get('url')]

                if only_with_images and not image_urls:
                    continue

                review_id = str(item.get('reviewRateId'))
                buyer_name = item.get('buyerName') or 'Anonymous'
                safe_buyer = clean_file_name(buyer_name)

                saved_local_files = []

                if download_images and image_urls:
                    if use_subfolders:
                        dest_folder = os.path.join(base_img_dir, f"{safe_buyer}_{review_id}")
                        os.makedirs(dest_folder, exist_ok=True)
                        for idx, img_url in enumerate(image_urls, start=1):
                            filename = f"photo_{idx}.jpg"
                            local_path = os.path.join(dest_folder, filename)
                            if download_image(img_url, local_path):
                                saved_local_files.append(local_path)
                                downloaded_images_count += 1
                    else:
                        for idx, img_url in enumerate(image_urls, start=1):
                            filename = f"{safe_buyer}_{review_id}_{idx}.jpg"
                            local_path = os.path.join(base_img_dir, filename)
                            if download_image(img_url, local_path):
                                saved_local_files.append(local_path)
                                downloaded_images_count += 1

                seller_reply = item.get('sellerReply') or {}
                review_record = {
                    'item_id': item_id,
                    'review_id': review_id,
                    'buyer_name': buyer_name,
                    'rating': item.get('rating'),
                    'review_content': (item.get('reviewContent') or '').strip(),
                    'review_date': item.get('reviewTime'),
                    'sku_info': item.get('skuInfo'),
                    'upvotes': item.get('likeCount', 0),
                    'seller_reply': seller_reply.get('content') if isinstance(seller_reply, dict) else None,
                    'image_urls': " | ".join(image_urls) if image_urls else "",
                    'local_images': " | ".join(saved_local_files) if saved_local_files else ""
                }
                all_reviews.append(review_record)

                if len(all_reviews) >= max_reviews:
                    break

            print(f"[+] Page {current_page}/{total_pages} processed ({len(all_reviews)} reviews matched, {downloaded_images_count} photos stored)")
            current_page += 1
            time.sleep(1.2)

    except KeyboardInterrupt:
        print("\n\n[!] Stopped by user. Finalizing output...")

    finally:
        if all_reviews and save_csv:
            df = pd.DataFrame(all_reviews)
            filename = f"daraz_reviews_{item_id}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n[✓] Results Saved:")
            print(f"    - CSV Output: {len(df)} rows saved in {filename}")
            if download_images:
                print(f"    - Image Directory: {downloaded_images_count} photos in ./{base_img_dir}/")
        elif all_reviews and not save_csv:
            print(f"\n[✓] Finished: {downloaded_images_count} photos stored in ./{base_img_dir}/")
        else:
            print("\n[!] No matching records found.\n")

if __name__ == '__main__':
    scrape_daraz()