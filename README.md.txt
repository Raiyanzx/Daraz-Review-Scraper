# Daraz Product Review & Image Scraper

A lightweight, automated Python scraper to extract customer reviews, ratings, seller responses, and user-uploaded review photos from Daraz products directly into a UTF-8 CSV and structured local folders.

---

## Features

 Direct API Scraping Uses Daraz's internal JSON endpoint instead of heavy DOM parsing.
 4 Operational Modes
  1. Reviews & Images (Organized in reviewer-named subfolders)
  2. Solo Reviews (CSV data only, skips image downloads)
  3. Solo Images (Downloads photos organized by reviewer)
  4. Flat Images Only (Saves all photos into a single directory, named by reviewer)
 Bangla Unicode Support Exports using `utf-8-sig` encoding so Bengali and special characters render cleanly in Microsoft Excel.
 Resilient Exits Press `Ctrl + C` at any point to stop early without losing already-collected data.

---

## Installation

1. Clone or Download the Repository
   ```bash
   git clone [httpsgithub.comyour-usernamedaraz-review-scraper.git](httpsgithub.comyour-usernamedaraz-review-scraper.git)
   cd daraz-review-scraper
   ```

2. Install Required Python Dependencies
   ```bash
   pip install -r requirements.txt
   ```

---

## Setup & Configuration

Because Daraz uses short-lived session security tokens, you need to provide your active session cookies once before scraping

1. Open Daraz in your browser and open any product page.
2. Open Chrome DevTools (`F12` or right-click  Inspect), and go to the Network tab.
3. Click the FetchXHR filter button.
4. Scroll down to the customer reviews on the webpage and click Page 2.
5. Look for the network request named `getReviewList` (or starting with `1.0`).
6. Right-click the request  Copy  Copy as cURL (bash).
7. Open `config.json` and paste the cookie string from `-b '...'` into the `cookie_string` field.

---

## Usage

Run the scraper using Python

```bash
python scrape_daraz.py
```

### Prompts Explained
1. Product URL or Item ID Paste either the full product URL or just the numeric Item ID.
2. Review Count Choose how many total reviews to gather (default 100).
3. Mode Selection Select 1, 2, 3, or 4 according to your workflow.

---

## Output Structure

 CSV File (`daraz_reviews_itemId.csv`)
   `item_id`, `review_id`, `buyer_name`, `rating`, `review_content`, `review_date`, `sku_info`, `upvotes`, `seller_reply`, `image_urls`, `local_images`
 Images Directory (`daraz_images_itemId`)
   Subfolder mode `daraz_images_itemIdBuyerName_reviewIdphoto_1.jpg`
   Flat mode `daraz_images_itemIdBuyerName_reviewId_1.jpg`

---

## Disclaimer
This project is for educational and research purposes only. Please respect Daraz's Terms of Service and rate limits when running requests.