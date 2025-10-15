# Helsana Web Crawler

A simple web crawler to extract content from the Helsana website.

## Features

- Crawls a starting webpage and all links found on that page
- Extracts text content from each page
- Saves results to a text file
- Respects rate limiting (1 second delay between requests)
- Only crawls pages within the same domain

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the crawler:

```bash
python crawler.py
```

The crawler will:
1. Fetch the starting URL: https://www.helsana.ch/de/private.html
2. Extract all links from that page
3. Crawl each link and extract text content
4. Save all results to `helsana_crawled_data.txt`

## Output

The output file contains:
- Crawl metadata (date, starting URL, number of URLs)
- Content from each crawled page, clearly separated
- URL for each section of content

## Configuration

You can modify the following in `crawler.py`:
- `start_url`: The starting webpage to crawl
- `output_file`: The name of the output text file
