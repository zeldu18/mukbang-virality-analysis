#!/usr/bin/env python3
"""
Test script for the mukbang scraper
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from scrapers.youtube_scraper import YouTubeScraper, scrape_youtube_mukbang


async def test_youtube_scraper():
    """Test the YouTube scraper"""
    logger.info("Testing YouTube scraper...")
    
    try:
        # Test basic search
        scraper = YouTubeScraper()
        logger.info("✓ YouTube scraper initialized successfully")
        
        # Test search functionality
        videos = await scraper.search_videos("mukbang", max_results=3)
        logger.info(f"✓ Found {len(videos)} videos in search")
        
        if videos:
            # Test video parsing
            video = videos[0]
            logger.info(f"✓ Sample video: {video.title}")
            logger.info(f"  - Views: {video.view_count}")
            logger.info(f"  - Duration: {video.duration} seconds")
            logger.info(f"  - Creator: {video.creator_name}")
        
        # Test convenience function
        mukbang_videos = await scrape_youtube_mukbang(max_results=5)
        logger.info(f"✓ Found {len(mukbang_videos)} mukbang videos")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False


async def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import pandas as pd
        logger.info("✓ pandas imported successfully")
        
        import yt_dlp
        logger.info("✓ yt-dlp imported successfully")
        
        import requests
        logger.info("✓ requests imported successfully")
        
        from config import youtube_config, scraping_config
        logger.info("✓ config imported successfully")
        
        from scrapers.base_scraper import BaseScraper, VideoData
        logger.info("✓ base_scraper imported successfully")
        
        return True
        
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


async def main():
    """Run all tests"""
    logger.info("Starting mukbang scraper tests...")
    
    # Test imports first
    imports_ok = await test_imports()
    if not imports_ok:
        logger.error("Import tests failed. Please check your dependencies.")
        return
    
    # Test YouTube scraper
    scraper_ok = await test_youtube_scraper()
    if not scraper_ok:
        logger.error("Scraper tests failed.")
        return
    
    logger.info("🎉 All tests passed! Your scraper is ready to use.")


if __name__ == "__main__":
    asyncio.run(main()) 