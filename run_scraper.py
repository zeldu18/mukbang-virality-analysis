#!/usr/bin/env python3
"""
Main script to run mukbang data scraping
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from scrapers.youtube_scraper import YouTubeScraper
from config import DATA_DIR


async def scrape_youtube_data():
    """Scrape mukbang data from YouTube"""
    logger.info("🚀 Starting YouTube mukbang data scraping...")
    
    # Initialize the scraper
    scraper = YouTubeScraper()
    
    # Search terms for mukbang content
    search_terms = [
        "mukbang",
        "eating show", 
        "food asmr",
        "먹방",
        "spicy noodle challenge",
        "food challenge",
        "korean food mukbang",
        "japanese food mukbang"
    ]
    
    all_videos = []
    
    # Search for videos using each term
    for term in search_terms:
        logger.info(f"🔍 Searching for: {term}")
        try:
            videos = await scraper.search_videos(term, max_results=20)
            all_videos.extend(videos)
            logger.info(f"✅ Found {len(videos)} videos for '{term}'")
            
            # Wait a bit between searches to be respectful
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Error searching for '{term}': {e}")
            continue
    
    # Remove duplicates based on video ID
    unique_videos = {}
    for video in all_videos:
        if video.video_id not in unique_videos:
            unique_videos[video.video_id] = video
    
    videos_list = list(unique_videos.values())
    
    logger.info(f"📊 Total unique videos found: {len(videos_list)}")
    
    if videos_list:
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = DATA_DIR / f"youtube_mukbang_{timestamp}.csv"
        
        scraper.save_to_csv(videos_list, str(filename))
        logger.info(f"💾 Data saved to: {filename}")
        
        # Show some sample data
        logger.info("\n📋 Sample videos found:")
        for i, video in enumerate(videos_list[:5]):
            logger.info(f"  {i+1}. {video.title}")
            logger.info(f"     Views: {video.view_count:,} | Duration: {video.duration}s | Creator: {video.creator_name}")
        
        return filename
    else:
        logger.warning("⚠️ No videos found!")
        return None


async def main():
    """Main function"""
    logger.info("🍜 Mukbang Data Scraper Starting...")
    
    try:
        # Scrape YouTube data
        result_file = await scrape_youtube_data()
        
        if result_file:
            logger.info(f"🎉 Scraping completed successfully!")
            logger.info(f"📁 Data saved to: {result_file}")
        else:
            logger.error("❌ Scraping failed - no data collected")
            
    except Exception as e:
        logger.error(f"❌ Scraping failed with error: {e}")
        raise


if __name__ == "__main__":
    # Run the scraper
    asyncio.run(main()) 