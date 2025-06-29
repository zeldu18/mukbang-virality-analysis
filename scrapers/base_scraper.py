"""
Base scraper class for multi-platform mukbang data collection
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import scraping_config


@dataclass
class VideoData:
    """Standardized video data structure across platforms"""
    platform: str
    video_id: str
    title: str
    description: Optional[str]
    url: str
    thumbnail_url: Optional[str]
    duration: Optional[int]  # seconds
    view_count: Optional[int]
    like_count: Optional[int]
    comment_count: Optional[int]
    share_count: Optional[int]
    upload_date: Optional[datetime]
    creator_name: Optional[str]
    creator_id: Optional[str]
    creator_followers: Optional[int]
    tags: List[str]
    categories: List[str]
    language: Optional[str]
    is_live: bool = False
    is_private: bool = False
    age_restricted: bool = False
    
    # Audio features (if extracted)
    audio_features: Optional[Dict[str, Any]] = None
    
    # Platform-specific metadata
    platform_metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        data = {
            'platform': self.platform,
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'duration': self.duration,
            'view_count': self.view_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'share_count': self.share_count,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'creator_name': self.creator_name,
            'creator_id': self.creator_id,
            'creator_followers': self.creator_followers,
            'tags': ','.join(self.tags) if self.tags else None,
            'categories': ','.join(self.categories) if self.categories else None,
            'language': self.language,
            'is_live': self.is_live,
            'is_private': self.is_private,
            'age_restricted': self.age_restricted,
            'audio_features': str(self.audio_features) if self.audio_features else None,
            'platform_metadata': str(self.platform_metadata) if self.platform_metadata else None,
            'scraped_at': datetime.now().isoformat()
        }
        return data


class BaseScraper(ABC):
    """Abstract base class for platform-specific scrapers"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.session = self._create_session()
        self.rate_limiter = RateLimiter(
            requests_per_minute=scraping_config.requests_per_minute,
            requests_per_hour=scraping_config.requests_per_hour
        )
        logger.info(f"Initialized {platform_name} scraper")
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic and headers"""
        session = requests.Session()
        
        # Configure retry strategy - updated for newer urllib3
        retry_strategy = Retry(
            total=scraping_config.retry_attempts,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # Updated parameter name
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    @abstractmethod
    async def search_videos(self, query: str, max_results: int = None) -> List[VideoData]:
        """Search for videos using the given query"""
        pass
    
    @abstractmethod
    async def get_video_details(self, video_id: str) -> Optional[VideoData]:
        """Get detailed information about a specific video"""
        pass
    
    @abstractmethod
    async def get_user_videos(self, user_id: str, max_results: int = None) -> List[VideoData]:
        """Get videos from a specific user/creator"""
        pass
    
    @abstractmethod
    async def get_trending_videos(self, max_results: int = None) -> List[VideoData]:
        """Get trending videos from the platform"""
        pass
    
    async def scrape_batch(self, queries: List[str], max_results_per_query: int = None) -> List[VideoData]:
        """Scrape videos for multiple queries"""
        all_videos = []
        
        for query in queries:
            logger.info(f"Searching for '{query}' on {self.platform_name}")
            try:
                videos = await self.search_videos(query, max_results_per_query)
                all_videos.extend(videos)
                logger.info(f"Found {len(videos)} videos for '{query}'")
                
                # Rate limiting between queries
                await asyncio.sleep(scraping_config.request_delay)
                
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
                continue
        
        return all_videos
    
    async def scrape_with_retry(self, func, *args, **kwargs):
        """Execute a scraping function with retry logic"""
        for attempt in range(scraping_config.retry_attempts):
            try:
                await self.rate_limiter.wait_if_needed()
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < scraping_config.retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
    
    def save_to_csv(self, videos: List[VideoData], filename: str):
        """Save video data to CSV file"""
        if not videos:
            logger.warning("No videos to save")
            return
        
        df = pd.DataFrame([video.to_dict() for video in videos])
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(videos)} videos to {filename}")
    
    def filter_mukbang_videos(self, videos: List[VideoData]) -> List[VideoData]:
        """Filter videos to only include mukbang-related content"""
        mukbang_keywords = [
            'mukbang', '먹방', 'eating', 'food', 'asmr', 'challenge',
            'spicy', 'noodles', 'ramen', 'korean', 'japanese', 'chinese',
            'eating show', 'food review', '먹방', '음식', '맛집'
        ]
        
        filtered_videos = []
        for video in videos:
            if not video.title or not video.description:
                continue
            
            text_to_check = f"{video.title.lower()} {video.description.lower()}"
            
            # Check if any mukbang keywords are present
            if any(keyword in text_to_check for keyword in mukbang_keywords):
                filtered_videos.append(video)
        
        logger.info(f"Filtered {len(videos)} videos to {len(filtered_videos)} mukbang videos")
        return filtered_videos


class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_times = []
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old requests outside the time windows
        self.request_times = [t for t in self.request_times if now - t < 3600]  # Keep last hour
        
        # Check minute limit
        recent_requests = [t for t in self.request_times if now - t < 60]
        if len(recent_requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - recent_requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Check hour limit
        if len(self.request_times) >= self.requests_per_hour:
            sleep_time = 3600 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Hourly rate limit reached, waiting {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now) 