"""
Scraper Analyzer - Automatically discovers URLs and selectors from scrapers.

This analyzes scraper code to extract:
- URLs that scrapers use
- CSS selectors and XPath expressions
- HTML parsing patterns
"""

import ast
import inspect
import logging
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass


@dataclass
class ScraperUrlInfo:
    """Information about a URL used by a scraper."""
    url: str
    scraper_name: str
    method_name: str
    url_type: str  # 'base', 'dynamic', 'static'
    selectors: List[str]  # CSS selectors or XPath used
    description: str


class ScraperAnalyzer:
    """
    Analyzes scraper code to discover URLs and selectors.
    
    This automatically extracts information from scraper classes
    so you don't have to manually register URLs.
    
    Usage:
        analyzer = ScraperAnalyzer()
        urls = analyzer.analyze_scraper(BDCDiscountScraper)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_scraper(self, scraper_class) -> List[ScraperUrlInfo]:
        """
        Analyze a scraper class to discover URLs and selectors.
        
        Args:
            scraper_class: The scraper class to analyze
            
        Returns:
            List of ScraperUrlInfo objects
        """
        scraper_name = scraper_class.__name__.replace('Scraper', '').lower()
        urls = []
        
        # Get source code
        try:
            source = inspect.getsource(scraper_class)
        except OSError:
            self.logger.warning(f"Could not get source for {scraper_class.__name__}")
            return urls
        
        # Extract URLs from source
        urls.extend(self._extract_urls_from_source(source, scraper_name))
        
        # Extract selectors from source
        selectors = self._extract_selectors_from_source(source)
        
        # Match selectors to URLs
        for url_info in urls:
            # Try to match selectors to URLs based on context
            url_info.selectors = self._match_selectors_to_url(url_info, selectors, source)
        
        return urls
    
    def _extract_urls_from_source(self, source: str, scraper_name: str) -> List[ScraperUrlInfo]:
        """Extract URLs from source code."""
        urls = []
        
        # Pattern for URLs
        url_patterns = [
            r'["\'](https?://[^"\']+)["\']',  # String URLs
            r'f["\'](https?://[^"\']+)["\']',  # f-string URLs
        ]
        
        # Pattern for URL variables
        url_var_patterns = [
            r'(\w+_URL)\s*=\s*["\'](https?://[^"\']+)["\']',
            r'(\w+_BASE_URL)\s*=\s*["\'](https?://[^"\']+)["\']',
        ]
        
        # Extract static URLs
        for pattern in url_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                url = match.group(1) if len(match.groups()) > 0 else match.group(0).strip('"\'')
                if url.startswith('http'):
                    urls.append(ScraperUrlInfo(
                        url=url,
                        scraper_name=scraper_name,
                        method_name='unknown',
                        url_type='static',
                        selectors=[],
                        description=f"Found in {scraper_name} scraper"
                    ))
        
        # Extract URL variables
        for pattern in url_var_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                var_name = match.group(1)
                url = match.group(2)
                urls.append(ScraperUrlInfo(
                    url=url,
                    scraper_name=scraper_name,
                    method_name=var_name,
                    url_type='base',
                    selectors=[],
                    description=f"Base URL variable: {var_name}"
                ))
        
        # Extract from config dictionaries (like BDC_CONFIG)
        config_pattern = r'(\w+_CONFIG)\s*=\s*\{[^}]*\}'
        config_matches = re.finditer(config_pattern, source, re.DOTALL)
        
        for config_match in config_matches:
            config_content = config_match.group(0)
            # Look for URLs in config
            url_matches = re.finditer(r'["\'](https?://[^"\']+)["\']', config_content)
            for url_match in url_matches:
                url = url_match.group(1)
                urls.append(ScraperUrlInfo(
                    url=url,
                    scraper_name=scraper_name,
                    method_name='config',
                    url_type='static',
                    selectors=[],
                    description=f"Found in {config_match.group(1)}"
                ))
        
        return urls
    
    def _extract_selectors_from_source(self, source: str) -> List[str]:
        """Extract CSS selectors and XPath from source code."""
        selectors = []
        
        # CSS selector patterns
        css_patterns = [
            r'\.select\(["\']([^"\']+)["\']\)',  # soup.select('.class')
            r'\.find\(["\']([^"\']+)["\']\)',  # soup.find('tag')
            r'\.find_all\(["\']([^"\']+)["\']\)',  # soup.find_all('tag')
            r'selectors?\s*=\s*\[([^\]]+)\]',  # selectors = ['.class', '#id']
        ]
        
        for pattern in css_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                selector = match.group(1)
                # Clean up selector
                selector = selector.strip('"\'')
                if selector and selector not in selectors:
                    selectors.append(selector)
        
        # XPath patterns
        xpath_patterns = [
            r'\.findall\(["\']([^"\']+)["\']\)',  # root.findall('.//tag')
            r'xpath\s*=\s*["\']([^"\']+)["\']',  # xpath = './/tag'
        ]
        
        for pattern in xpath_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                xpath = match.group(1)
                xpath = xpath.strip('"\'')
                if xpath and xpath not in selectors:
                    selectors.append(xpath)
        
        return selectors
    
    def _match_selectors_to_url(self, url_info: ScraperUrlInfo, 
                               all_selectors: List[str], source: str) -> List[str]:
        """Try to match selectors to a specific URL based on context."""
        matched_selectors = []
        
        # Simple heuristic: if URL appears near selectors in code, they're related
        # This is a simplified approach - could be improved with AST parsing
        
        # For now, return all selectors found in the scraper
        # In a real implementation, we'd do more sophisticated matching
        return all_selectors[:5]  # Limit to first 5 to avoid noise
    
    def analyze_all_scrapers(self) -> Dict[str, List[ScraperUrlInfo]]:
        """Analyze all scrapers in the scrapers module."""
        from scrapers.bdc_discount_scraper import BDCDiscountScraper
        from scrapers.credit_fund_scraper import CreditFundScraper
        from scrapers.bank_provision_scraper import BankProvisionScraper
        from scrapers.bond_issuance_scraper import BondIssuanceScraper
        
        scrapers = {
            'bdc_discount': BDCDiscountScraper,
            'credit_fund': CreditFundScraper,
            'bank_provision': BankProvisionScraper,
            'bond_issuance': BondIssuanceScraper,
        }
        
        results = {}
        
        for name, scraper_class in scrapers.items():
            try:
                urls = self.analyze_scraper(scraper_class)
                results[name] = urls
                self.logger.info(f"✅ Analyzed {name}: found {len(urls)} URL(s)")
            except Exception as e:
                self.logger.error(f"❌ Error analyzing {name}: {e}")
                results[name] = []
        
        return results

