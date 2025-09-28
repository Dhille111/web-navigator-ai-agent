"""
Content extraction utilities for web scraping and data processing
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractedData:
    """Structured extracted data"""
    title: Optional[str] = None
    price: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[str] = None
    image_url: Optional[str] = None
    raw_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'title': self.title,
            'price': self.price,
            'url': self.url,
            'description': self.description,
            'rating': self.rating,
            'image_url': self.image_url,
            'raw_data': self.raw_data
        }


class ContentExtractor:
    """Utility class for extracting and processing web content"""
    
    def __init__(self):
        self.price_patterns = [
            r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*rupees?',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*₹'
        ]
        
        self.rating_patterns = [
            r'(\d+(?:\.\d+)?)\s*out\s*of\s*5',
            r'(\d+(?:\.\d+)?)\s*\/\s*5',
            r'(\d+(?:\.\d+)?)\s*stars?',
            r'rating[:\s]*(\d+(?:\.\d+)?)'
        ]
    
    def extract_from_html(self, html: str, selectors: Dict[str, str]) -> List[ExtractedData]:
        """Extract data from HTML using CSS selectors"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Find all matching elements
            elements = soup.select(selectors.get('results', 'body'))
            
            for element in elements:
                data = self._extract_element_data(element, selectors)
                if data:
                    results.append(data)
            
            logger.info(f"Extracted {len(results)} items from HTML")
            return results
            
        except Exception as e:
            logger.error(f"Failed to extract from HTML: {e}")
            return []
    
    def _extract_element_data(self, element, selectors: Dict[str, str]) -> Optional[ExtractedData]:
        """Extract data from a single element"""
        try:
            data = ExtractedData()
            
            # Extract title
            if 'title' in selectors:
                title_elem = element.select_one(selectors['title'])
                if title_elem:
                    data.title = self._clean_text(title_elem.get_text())
            
            # Extract price
            if 'price' in selectors:
                price_elem = element.select_one(selectors['price'])
                if price_elem:
                    data.price = self._extract_price(price_elem.get_text())
            
            # Extract URL
            if 'link' in selectors:
                link_elem = element.select_one(selectors['link'])
                if link_elem:
                    href = link_elem.get('href')
                    if href:
                        data.url = self._normalize_url(href)
            
            # Extract description
            if 'description' in selectors:
                desc_elem = element.select_one(selectors['description'])
                if desc_elem:
                    data.description = self._clean_text(desc_elem.get_text())
            
            # Extract rating
            if 'rating' in selectors:
                rating_elem = element.select_one(selectors['rating'])
                if rating_elem:
                    data.rating = self._extract_rating(rating_elem.get_text())
            
            # Extract image URL
            if 'image' in selectors:
                img_elem = element.select_one(selectors['image'])
                if img_elem:
                    src = img_elem.get('src')
                    if src:
                        data.image_url = self._normalize_url(src)
            
            # Store raw element data
            data.raw_data = {
                'html': str(element),
                'text': element.get_text(),
                'attributes': dict(element.attrs) if hasattr(element, 'attrs') else {}
            }
            
            # Only return if we have at least some data
            if any([data.title, data.price, data.url, data.description]):
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract element data: {e}")
            return None
    
    def extract_from_playwright_data(self, playwright_data: List[Dict[str, Any]], selectors: Dict[str, str]) -> List[ExtractedData]:
        """Extract data from Playwright extraction results"""
        try:
            results = []
            
            for item in playwright_data:
                data = ExtractedData()
                
                # Extract title from text or attributes
                if 'text' in item:
                    data.title = self._clean_text(item['text'])
                
                # Extract price from text
                if 'text' in item:
                    price = self._extract_price(item['text'])
                    if price:
                        data.price = price
                
                # Extract URL from href attribute
                if 'attributes' in item and 'href' in item['attributes']:
                    data.url = self._normalize_url(item['attributes']['href'])
                
                # Extract description from text
                if 'text' in item:
                    data.description = self._clean_text(item['text'])
                
                # Extract rating from text
                if 'text' in item:
                    rating = self._extract_rating(item['text'])
                    if rating:
                        data.rating = rating
                
                # Extract image URL from src attribute
                if 'attributes' in item and 'src' in item['attributes']:
                    data.image_url = self._normalize_url(item['attributes']['src'])
                
                # Store raw data
                data.raw_data = item
                
                # Only add if we have meaningful data
                if any([data.title, data.price, data.url, data.description]):
                    results.append(data)
            
            logger.info(f"Extracted {len(results)} items from Playwright data")
            return results
            
        except Exception as e:
            logger.error(f"Failed to extract from Playwright data: {e}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?₹$€£¥]', '', text)
        
        return text.strip()
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text"""
        if not text:
            return None
        
        for pattern in self.price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = match.group(1)
                # Add currency symbol if not present
                if not any(symbol in price for symbol in ['₹', 'Rs', 'INR']):
                    price = f"₹{price}"
                return price
        
        return None
    
    def _extract_rating(self, text: str) -> Optional[str]:
        """Extract rating from text"""
        if not text:
            return None
        
        for pattern in self.rating_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL"""
        if not url:
            return ""
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = 'https://example.com' + url
            else:
                url = 'https://' + url
        
        return url
    
    def filter_by_price(self, data: List[ExtractedData], max_price: Optional[float] = None, min_price: Optional[float] = None) -> List[ExtractedData]:
        """Filter data by price range"""
        if not max_price and not min_price:
            return data
        
        filtered = []
        
        for item in data:
            if not item.price:
                continue
            
            # Extract numeric price
            price_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', item.price)
            if not price_match:
                continue
            
            try:
                price_value = float(price_match.group(1).replace(',', ''))
                
                if max_price and price_value > max_price:
                    continue
                
                if min_price and price_value < min_price:
                    continue
                
                filtered.append(item)
                
            except ValueError:
                continue
        
        return filtered
    
    def sort_by_rating(self, data: List[ExtractedData], reverse: bool = True) -> List[ExtractedData]:
        """Sort data by rating"""
        def get_rating_value(item):
            if not item.rating:
                return 0.0
            
            try:
                return float(item.rating)
            except ValueError:
                return 0.0
        
        return sorted(data, key=get_rating_value, reverse=reverse)
    
    def sort_by_price(self, data: List[ExtractedData], reverse: bool = False) -> List[ExtractedData]:
        """Sort data by price"""
        def get_price_value(item):
            if not item.price:
                return float('inf') if reverse else 0.0
            
            price_match = re.search(r'(\d+(?:,\d{3})*(?:\.\d{2})?)', item.price)
            if not price_match:
                return float('inf') if reverse else 0.0
            
            try:
                return float(price_match.group(1).replace(',', ''))
            except ValueError:
                return float('inf') if reverse else 0.0
        
        return sorted(data, key=get_price_value, reverse=reverse)
    
    def limit_results(self, data: List[ExtractedData], limit: int) -> List[ExtractedData]:
        """Limit number of results"""
        return data[:limit]
    
    def deduplicate(self, data: List[ExtractedData], key_fields: List[str] = None) -> List[ExtractedData]:
        """Remove duplicate entries"""
        if not key_fields:
            key_fields = ['title', 'url']
        
        seen = set()
        unique_data = []
        
        for item in data:
            # Create key from specified fields
            key_parts = []
            for field in key_fields:
                value = getattr(item, field, '')
                if value:
                    key_parts.append(str(value).lower().strip())
            
            key = '|'.join(key_parts)
            
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        return unique_data


class ExtractorFactory:
    """Factory for creating content extractors"""
    
    @staticmethod
    def create_extractor() -> ContentExtractor:
        """Create a content extractor"""
        return ContentExtractor()


# Example usage
if __name__ == "__main__":
    # Test the extractor
    extractor = ExtractorFactory.create_extractor()
    
    # Sample HTML for testing
    sample_html = """
    <div class="product">
        <h3 class="title">Laptop Model XYZ</h3>
        <span class="price">₹45,000</span>
        <a href="/product/123">View Details</a>
        <p class="description">High-performance laptop for work and gaming</p>
        <span class="rating">4.5 out of 5</span>
    </div>
    """
    
    selectors = {
        'results': '.product',
        'title': '.title',
        'price': '.price',
        'link': 'a',
        'description': '.description',
        'rating': '.rating'
    }
    
    results = extractor.extract_from_html(sample_html, selectors)
    
    for result in results:
        print(f"Title: {result.title}")
        print(f"Price: {result.price}")
        print(f"URL: {result.url}")
        print(f"Rating: {result.rating}")
        print("---")
