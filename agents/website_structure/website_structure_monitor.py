"""
Website Structure Monitor - Proactively monitors HTML structure changes.

This agent periodically checks target websites for structural changes
and detects issues before scrapers break.
"""

import hashlib
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
import json

import requests
from bs4 import BeautifulSoup


@dataclass
class StructureSnapshot:
    """Represents a snapshot of website HTML structure."""
    url: str
    timestamp: datetime
    html_hash: str  # Hash of HTML content
    structure_hash: str  # Hash of structure (ignoring content)
    key_elements: Dict[str, Any]  # Important elements and their signatures
    selectors_status: Dict[str, bool]  # Which selectors still work
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class StructureChange:
    """Represents a detected structure change."""
    url: str
    change_type: str  # 'STRUCTURE_CHANGE', 'SELECTOR_BROKEN', 'CONTENT_CHANGE'
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    detected_at: datetime
    baseline_snapshot: StructureSnapshot
    current_snapshot: StructureSnapshot
    broken_selectors: List[str]
    description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['detected_at'] = self.detected_at.isoformat()
        data['baseline_snapshot'] = self.baseline_snapshot.to_dict()
        data['current_snapshot'] = self.current_snapshot.to_dict()
        return data


class WebsiteStructureMonitor:
    """
    Monitors website HTML structures for changes.
    
    This proactively detects when websites change their HTML structure,
    allowing us to fix scrapers before they break.
    
    Usage:
        monitor = WebsiteStructureMonitor()
        
        # Register a URL to monitor
        monitor.register_url(
            url='https://example.com/data',
            selectors=['.nav-value', '#price'],
            scraper_name='bdc_discount'
        )
        
        # Check for changes
        changes = monitor.check_for_changes()
    """
    
    def __init__(self, storage_dir: str = "logs/website_structure"):
        """
        Initialize structure monitor.
        
        Args:
            storage_dir: Directory to store structure snapshots
        """
        self.logger = logging.getLogger(__name__)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Registered URLs to monitor
        self.monitored_urls: Dict[str, Dict[str, Any]] = {}
        
        # Structure snapshots (baselines)
        self.baselines: Dict[str, StructureSnapshot] = {}
        
        # Load existing baselines
        self._load_baselines()
    
    def register_url(self, url: str, selectors: List[str], 
                    scraper_name: str, check_interval_hours: int = 24):
        """
        Register a URL to monitor for structure changes.
        
        Args:
            url: URL to monitor
            selectors: List of CSS selectors/XPath used by scraper
            scraper_name: Name of scraper using this URL
            check_interval_hours: How often to check (default: 24 hours)
        """
        self.monitored_urls[url] = {
            'selectors': selectors,
            'scraper_name': scraper_name,
            'check_interval_hours': check_interval_hours,
            'last_checked': None,
            'registered_at': datetime.now(timezone.utc)
        }
        
        self.logger.info(f"📋 Registered URL for monitoring: {url} (scraper: {scraper_name})")
        
        # Create initial baseline if doesn't exist
        if url not in self.baselines:
            self._create_baseline(url)
    
    def _create_baseline(self, url: str) -> Optional[StructureSnapshot]:
        """Create baseline snapshot for a URL."""
        try:
            self.logger.info(f"📸 Creating baseline snapshot for {url}...")
            
            snapshot = self._capture_snapshot(url)
            
            if snapshot:
                self.baselines[url] = snapshot
                self._save_baseline(url, snapshot)
                self.logger.info(f"✅ Baseline created for {url}")
                return snapshot
            else:
                self.logger.warning(f"⚠️  Failed to create baseline for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error creating baseline for {url}: {e}")
            return None
    
    def _capture_snapshot(self, url: str) -> Optional[StructureSnapshot]:
        """
        Capture a snapshot of website structure.
        
        Args:
            url: URL to capture
            
        Returns:
            StructureSnapshot or None if failed
        """
        try:
            # Fetch HTML
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; BoomBustSentinel/1.0; +https://boom-bust-sentinel.com)'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Calculate hashes
            html_hash = hashlib.sha256(html_content.encode()).hexdigest()
            
            # Extract structure (remove content, keep structure)
            structure_html = self._extract_structure(soup)
            structure_hash = hashlib.sha256(structure_html.encode()).hexdigest()
            
            # Extract key elements
            key_elements = self._extract_key_elements(soup)
            
            # Check selector status
            selectors = self.monitored_urls.get(url, {}).get('selectors', [])
            selectors_status = {}
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    selectors_status[selector] = len(elements) > 0
                except Exception:
                    selectors_status[selector] = False
            
            return StructureSnapshot(
                url=url,
                timestamp=datetime.now(timezone.utc),
                html_hash=html_hash,
                structure_hash=structure_hash,
                key_elements=key_elements,
                selectors_status=selectors_status
            )
            
        except Exception as e:
            self.logger.error(f"Error capturing snapshot for {url}: {e}")
            return None
    
    def _extract_structure(self, soup: BeautifulSoup) -> str:
        """
        Extract HTML structure (without content).
        
        This creates a simplified version of HTML that focuses on structure:
        - Tag names
        - Attributes (id, class, data-*)
        - Hierarchy
        - Ignores text content
        """
        structure_parts = []
        
        for element in soup.find_all():
            # Get tag name
            tag_name = element.name
            
            # Get important attributes
            attrs = {}
            if element.get('id'):
                attrs['id'] = element.get('id')
            if element.get('class'):
                attrs['class'] = sorted(element.get('class'))
            # Include data attributes
            for attr in element.attrs:
                if attr.startswith('data-'):
                    attrs[attr] = element.get(attr)
            
            # Create structure signature
            structure_parts.append(f"{tag_name}:{json.dumps(attrs, sort_keys=True)}")
        
        return "\n".join(structure_parts)
    
    def _extract_key_elements(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract key elements that are likely important for scraping."""
        key_elements = {}
        
        # Find elements with IDs (usually important)
        for element in soup.find_all(id=True):
            element_id = element.get('id')
            key_elements[f"#{element_id}"] = {
                'tag': element.name,
                'classes': sorted(element.get('class', [])),
                'has_text': bool(element.get_text(strip=True))
            }
        
        # Find common data containers
        for element in soup.find_all(class_=lambda x: x and any(
            keyword in ' '.join(x).lower() 
            for keyword in ['nav', 'price', 'value', 'data', 'metric', 'stat']
        )):
            classes = ' '.join(element.get('class', []))
            if classes not in key_elements:
                key_elements[f".{classes}"] = {
                    'tag': element.name,
                    'has_id': bool(element.get('id')),
                    'has_text': bool(element.get_text(strip=True))
                }
        
        return key_elements
    
    def check_for_changes(self, url: Optional[str] = None) -> List[StructureChange]:
        """
        Check for structure changes.
        
        Args:
            url: Specific URL to check (None for all registered URLs)
            
        Returns:
            List of detected StructureChange objects
        """
        changes = []
        
        urls_to_check = [url] if url else list(self.monitored_urls.keys())
        
        for check_url in urls_to_check:
            if check_url not in self.monitored_urls:
                continue
            
            # Check if it's time to check this URL
            last_checked = self.monitored_urls[check_url].get('last_checked')
            check_interval = self.monitored_urls[check_url]['check_interval_hours']
            
            if last_checked:
                hours_since_check = (
                    datetime.now(timezone.utc) - last_checked
                ).total_seconds() / 3600
                
                if hours_since_check < check_interval:
                    continue  # Not time to check yet
            
            self.logger.info(f"🔍 Checking structure for {check_url}...")
            
            # Capture current snapshot
            current_snapshot = self._capture_snapshot(check_url)
            
            if not current_snapshot:
                continue
            
            # Update last checked time
            self.monitored_urls[check_url]['last_checked'] = datetime.now(timezone.utc)
            
            # Compare with baseline
            baseline = self.baselines.get(check_url)
            
            if not baseline:
                # No baseline yet, create one
                self.baselines[check_url] = current_snapshot
                self._save_baseline(check_url, current_snapshot)
                continue
            
            # Detect changes
            change = self._detect_change(check_url, baseline, current_snapshot)
            
            if change:
                changes.append(change)
                self.logger.warning(f"⚠️  Structure change detected for {check_url}: {change.change_type}")
        
        return changes
    
    def _detect_change(self, url: str, baseline: StructureSnapshot,
                      current: StructureSnapshot) -> Optional[StructureChange]:
        """Detect changes between baseline and current snapshot."""
        changes_detected = []
        broken_selectors = []
        severity = 'LOW'
        
        # Check structure hash
        if baseline.structure_hash != current.structure_hash:
            changes_detected.append("HTML structure changed")
            severity = 'MEDIUM'
        
        # Check HTML hash (content change)
        if baseline.html_hash != current.html_hash:
            if baseline.structure_hash == current.structure_hash:
                changes_detected.append("Content changed (structure same)")
            else:
                changes_detected.append("Both structure and content changed")
        
        # Check selector status
        baseline_selectors = baseline.selectors_status
        current_selectors = current.selectors_status
        
        for selector in baseline_selectors:
            if selector in current_selectors:
                if baseline_selectors[selector] and not current_selectors[selector]:
                    broken_selectors.append(selector)
                    changes_detected.append(f"Selector broken: {selector}")
                    severity = 'HIGH'
        
        # If any selector is broken, it's critical
        if broken_selectors:
            severity = 'CRITICAL'
        
        if not changes_detected:
            return None
        
        return StructureChange(
            url=url,
            change_type='STRUCTURE_CHANGE' if broken_selectors else 'CONTENT_CHANGE',
            severity=severity,
            detected_at=datetime.now(timezone.utc),
            baseline_snapshot=baseline,
            current_snapshot=current,
            broken_selectors=broken_selectors,
            description="; ".join(changes_detected)
        )
    
    def _save_baseline(self, url: str, snapshot: StructureSnapshot):
        """Save baseline snapshot to disk."""
        # Create safe filename from URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        baseline_file = self.storage_dir / f"baseline_{url_hash}.json"
        
        with open(baseline_file, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    def _load_baselines(self):
        """Load baseline snapshots from disk."""
        for baseline_file in self.storage_dir.glob("baseline_*.json"):
            try:
                with open(baseline_file, 'r') as f:
                    data = json.load(f)
                    
                    # Reconstruct snapshot
                    snapshot = StructureSnapshot(
                        url=data['url'],
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        html_hash=data['html_hash'],
                        structure_hash=data['structure_hash'],
                        key_elements=data['key_elements'],
                        selectors_status=data['selectors_status']
                    )
                    
                    self.baselines[snapshot.url] = snapshot
                    
            except Exception as e:
                self.logger.warning(f"Failed to load baseline from {baseline_file}: {e}")
    
    def update_baseline(self, url: str):
        """Update baseline to current structure (after fixing scraper)."""
        snapshot = self._capture_snapshot(url)
        if snapshot:
            self.baselines[url] = snapshot
            self._save_baseline(url, snapshot)
            self.logger.info(f"✅ Baseline updated for {url}")
    
    def get_monitored_urls(self) -> Dict[str, Dict[str, Any]]:
        """Get list of monitored URLs."""
        return self.monitored_urls.copy()
    
    def get_baselines(self) -> Dict[str, StructureSnapshot]:
        """Get all baseline snapshots."""
        return self.baselines.copy()

