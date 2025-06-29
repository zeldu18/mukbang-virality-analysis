"""
Configuration file for Mukbang Analysis Multi-Platform Scraper
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for dir_path in [DATA_DIR, OUTPUT_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

@dataclass
class ScrapingConfig:
    """Configuration for scraping settings"""
    max_results_per_platform: int = 1000
    max_concurrent_requests: int = 5
    request_delay: float = 1.0  # seconds between requests
    timeout: int = 30
    retry_attempts: int = 3
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000

@dataclass
class YouTubeConfig:
    """YouTube-specific configuration"""
    search_terms: List[str] = None
    channels_to_monitor: List[str] = None
    categories: List[str] = None
    
    def __post_init__(self):
        if self.search_terms is None:
            self.search_terms = [
                "mukbang", "eating show", "food asmr", "먹방",
                "spicy noodle challenge", "food challenge", "eating challenge",
                "korean food mukbang", "japanese food mukbang", "chinese food mukbang"
            ]
        
        if self.channels_to_monitor is None:
            self.channels_to_monitor = [
                "SSSniperWolf", "Bella Poarch", "Zach Choi ASMR",
                "SAS-ASMR", "Honeyjubu", "Dorothy", "Jane ASMR"
            ]
        
        if self.categories is None:
            self.categories = ["Entertainment", "People & Blogs", "Howto & Style"]

@dataclass
class TikTokConfig:
    """TikTok-specific configuration"""
    search_terms: List[str] = None
    hashtags: List[str] = None
    users_to_monitor: List[str] = None
    
    def __post_init__(self):
        if self.search_terms is None:
            self.search_terms = [
                "mukbang", "eating", "food", "asmr", "먹방",
                "spicy", "noodles", "challenge", "foodie"
            ]
        
        if self.hashtags is None:
            self.hashtags = [
                "#mukbang", "#eating", "#food", "#asmr", "#먹방",
                "#spicy", "#noodles", "#challenge", "#foodie", "#eatingasmr"
            ]
        
        if self.users_to_monitor is None:
            self.users_to_monitor = [
                "zachchoi", "sasasmr", "honeyjubu", "dorothy", "janeasmr"
            ]

@dataclass
class InstagramConfig:
    """Instagram-specific configuration"""
    search_terms: List[str] = None
    hashtags: List[str] = None
    accounts_to_monitor: List[str] = None
    
    def __post_init__(self):
        if self.search_terms is None:
            self.search_terms = [
                "mukbang", "eating", "food", "asmr", "먹방",
                "spicy", "noodles", "challenge", "foodie"
            ]
        
        if self.hashtags is None:
            self.hashtags = [
                "mukbang", "eating", "food", "asmr", "먹방",
                "spicy", "noodles", "challenge", "foodie", "eatingasmr"
            ]
        
        if self.accounts_to_monitor is None:
            self.accounts_to_monitor = [
                "zachchoi", "sasasmr", "honeyjubu", "dorothy", "janeasmr"
            ]

@dataclass
class AudioConfig:
    """Audio processing configuration"""
    extract_audio: bool = True
    audio_format: str = "wav"
    sample_rate: int = 22050
    max_audio_duration: int = 300  # seconds (5 minutes)
    
    # Lightweight audio features
    extract_mfcc: bool = True
    extract_spectral_features: bool = True
    extract_rhythm_features: bool = False  # More computationally expensive
    
    # ASMR detection features
    detect_silence: bool = True
    detect_chewing_sounds: bool = True
    detect_speech: bool = True

@dataclass
class DatabaseConfig:
    """Database configuration"""
    database_url: str = f"sqlite:///{DATA_DIR}/mukbang_analysis.db"
    backup_interval_hours: int = 24
    max_database_size_gb: int = 10

@dataclass
class MonitoringConfig:
    """Real-time monitoring configuration"""
    enabled: bool = True
    check_interval_minutes: int = 30
    alert_threshold_views: int = 1000000  # Alert for videos with 1M+ views
    alert_threshold_likes: int = 100000   # Alert for videos with 100K+ likes
    
    # Notification settings
    send_notifications: bool = False
    notification_email: Optional[str] = None
    webhook_url: Optional[str] = None

# Load environment variables
def load_env_config():
    """Load configuration from environment variables"""
    return {
        "TIKTOK_SESSION_ID": os.getenv("TIKTOK_SESSION_ID"),
        "INSTAGRAM_USERNAME": os.getenv("INSTAGRAM_USERNAME"),
        "INSTAGRAM_PASSWORD": os.getenv("INSTAGRAM_PASSWORD"),
        "YOUTUBE_API_KEY": os.getenv("YOUTUBE_API_KEY"),
        "PROXY_URL": os.getenv("PROXY_URL"),
    }

# Initialize configurations
scraping_config = ScrapingConfig()
youtube_config = YouTubeConfig()
tiktok_config = TikTokConfig()
instagram_config = InstagramConfig()
audio_config = AudioConfig()
database_config = DatabaseConfig()
monitoring_config = MonitoringConfig()
env_config = load_env_config()

# Export all configurations
__all__ = [
    "BASE_DIR", "DATA_DIR", "OUTPUT_DIR", "LOGS_DIR",
    "scraping_config", "youtube_config", "tiktok_config", 
    "instagram_config", "audio_config", "database_config", 
    "monitoring_config", "env_config"
] 