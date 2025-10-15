#!/usr/bin/env python3
"""
Web Crawler for Helsana Website
Crawls a given webpage and all links on that page, saving results to a text file.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from datetime import datetime
import sys


class HelsanaWebCrawler:
    def __init__(self, start_url, output_file="crawled_data.txt"):
        self.start_url = start_url
        self.output_file = output_file
        self.visited_urls = set()
        self.base_domain = urlparse(start_url).netloc
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        parsed = urlparse(url)
        return (
            parsed.scheme in ['http', 'https'] and
            parsed.netloc == self.base_domain
        )
    
    def get_page_content(self, url):
        """Fetch and parse a webpage"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links(self, html, base_url):
        """Extract all links from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Remove fragment identifiers
            full_url = full_url.split('#')[0]
            
            if self.is_valid_url(full_url):
                links.add(full_url)
        
        return links
    
    def extract_text_content(self, html, url):
        """Extract meaningful text content from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def crawl(self):
        """Main crawling function"""
        print(f"Starting crawl of: {self.start_url}")
        print(f"Output file: {self.output_file}")
        print("=" * 80)
        
        # First, get all links from the start page
        html = self.get_page_content(self.start_url)
        if not html:
            print("Failed to fetch the starting page!")
            return
        
        # Extract links from the start page
        all_links = self.extract_links(html, self.start_url)
        all_links.add(self.start_url)  # Include the start page itself
        
        print(f"\nFound {len(all_links)} unique links to crawl")
        print("=" * 80)
        
        # Open output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"Web Crawl Results\n")
            f.write(f"Start URL: {self.start_url}\n")
            f.write(f"Crawl Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total URLs to crawl: {len(all_links)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Crawl each URL
            for idx, url in enumerate(sorted(all_links), 1):
                if url in self.visited_urls:
                    continue
                
                print(f"[{idx}/{len(all_links)}] Crawling: {url}")
                
                html = self.get_page_content(url)
                if html:
                    text_content = self.extract_text_content(html, url)
                    
                    # Write to file
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"URL [{idx}]: {url}\n")
                    f.write(f"{'=' * 80}\n\n")
                    f.write(text_content)
                    f.write(f"\n\n{'=' * 80}\n")
                    f.write(f"End of content from: {url}\n")
                    f.write(f"{'=' * 80}\n\n")
                    
                    self.visited_urls.add(url)
                    
                    # Be nice to the server
                    time.sleep(1)
                else:
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"URL [{idx}]: {url}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"ERROR: Failed to fetch this URL\n")
                    f.write(f"{'=' * 80}\n\n")
        
        print("=" * 80)
        print(f"\nCrawling completed!")
        print(f"Total URLs crawled: {len(self.visited_urls)}")
        print(f"Results saved to: {self.output_file}")


def main():
    # Configuration
    start_url = "https://www.helsana.ch/de/private.html"
    output_file = "helsana_crawled_data.txt"
    
    # Create crawler instance
    crawler = HelsanaWebCrawler(start_url, output_file)
    
    # Start crawling
    crawler.crawl()


if __name__ == "__main__":
    main()
