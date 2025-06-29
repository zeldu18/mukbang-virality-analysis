"""
YouTube scraper for mukbang video data collection
"""
import asyncio
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

import yt_dlp
from loguru import logger

from .base_scraper import BaseScraper, VideoData
from config import youtube_config, scraping_config


class YouTubeScraper(BaseScraper):
    """YouTube-specific scraper using yt-dlp"""
    
    def __init__(self):
        super().__init__("YouTube")
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'noplaylist': True,
            'ignoreerrors': True,
        }
    
    async def search_videos(self, query: str, max_results: int = None) -> List[VideoData]:
        """Search for videos using yt-dlp search"""
        if max_results is None:
            max_results = scraping_config.max_results_per_platform
        elif max_results <= 0:
            max_results = 1  # Ensure at least 1 result
        
        search_url = f"ytsearch{max_results}:{query}"
        videos = []
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                result = ydl.extract_info(search_url, download=False)
                
                if result and 'entries' in result:
                    for entry in result['entries']:
                        if entry:
                            video_data = self._parse_video_entry(entry)
                            if video_data:
                                videos.append(video_data)
                
                logger.info(f"Found {len(videos)} videos for query: {query}")
                
        except Exception as e:
            logger.error(f"Error searching YouTube for '{query}': {e}")
        
        return videos
    
    async def get_video_details(self, video_id: str) -> Optional[VideoData]:
        """Get detailed information about a specific video"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                result = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                if result:
                    return self._parse_video_entry(result)
                    
        except Exception as e:
            logger.error(f"Error getting video details for {video_id}: {e}")
        
        return None
    
    async def get_user_videos(self, user_id: str, max_results: int = None) -> List[VideoData]:
        """Get videos from a specific YouTube channel"""
        if max_results is None:
            max_results = scraping_config.max_results_per_platform
        
        videos = []
        
        try:
            # Try different URL formats for channels
            channel_urls = [
                f"https://www.youtube.com/channel/{user_id}",
                f"https://www.youtube.com/user/{user_id}",
                f"https://www.youtube.com/c/{user_id}",
                f"https://www.youtube.com/@{user_id}"
            ]
            
            for url in channel_urls:
                try:
                    with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                        result = ydl.extract_info(url, download=False)
                        
                        if result and 'entries' in result:
                            for entry in result['entries'][:max_results]:
                                if entry:
                                    video_data = self._parse_video_entry(entry)
                                    if video_data:
                                        videos.append(video_data)
                            
                            if videos:
                                break  # Found videos, no need to try other URLs
                                
                except Exception as e:
                    logger.debug(f"Failed to extract from {url}: {e}")
                    continue
            
            logger.info(f"Found {len(videos)} videos for channel: {user_id}")
            
        except Exception as e:
            logger.error(f"Error getting user videos for {user_id}: {e}")
        
        return videos
    
    async def get_trending_videos(self, max_results: int = None) -> List[VideoData]:
        """Get trending videos from YouTube"""
        if max_results is None:
            max_results = scraping_config.max_results_per_platform
        
        videos = []
        
        try:
            # Get trending videos
            trending_url = "https://www.youtube.com/feed/trending"
            
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                result = ydl.extract_info(trending_url, download=False)
                
                if result and 'entries' in result:
                    for entry in result['entries'][:max_results]:
                        if entry:
                            video_data = self._parse_video_entry(entry)
                            if video_data:
                                videos.append(video_data)
            
            logger.info(f"Found {len(videos)} trending videos")
            
        except Exception as e:
            logger.error(f"Error getting trending videos: {e}")
        
        return videos
    
    def _parse_video_entry(self, entry: Dict[str, Any]) -> Optional[VideoData]:
        """Parse yt-dlp video entry into VideoData object"""
        try:
            # Extract video ID
            video_id = entry.get('id', '')
            if not video_id:
                return None
            
            # Parse upload date
            upload_date = None
            if 'upload_date' in entry:
                try:
                    upload_date = datetime.strptime(entry['upload_date'], '%Y%m%d')
                except:
                    pass
            
            # Extract tags
            tags = entry.get('tags', [])
            if isinstance(tags, str):
                tags = [tags]
            
            # Extract categories
            categories = entry.get('categories', [])
            if isinstance(categories, str):
                categories = [categories]
            
            # Parse duration
            duration = entry.get('duration')
            if duration and duration > 0:
                duration = int(duration)
            else:
                duration = None
            
            # Extract view count
            view_count = entry.get('view_count')
            if view_count:
                view_count = int(view_count)
            
            # Extract like count
            like_count = entry.get('like_count')
            if like_count:
                like_count = int(like_count)
            
            # Extract comment count
            comment_count = entry.get('comment_count')
            if comment_count:
                comment_count = int(comment_count)
            
            # Extract creator info
            creator_name = entry.get('uploader', '')
            creator_id = entry.get('uploader_id', '')
            creator_followers = entry.get('uploader_follower_count')
            if creator_followers:
                creator_followers = int(creator_followers)
            
            # Extract thumbnail
            thumbnail_url = None
            if 'thumbnail' in entry:
                thumbnail_url = entry['thumbnail']
            elif 'thumbnails' in entry and entry['thumbnails']:
                thumbnail_url = entry['thumbnails'][0].get('url')
            
            # Check if video is live or private
            is_live = entry.get('live_status') == 'is_live'
            is_private = entry.get('availability') == 'private'
            age_restricted = entry.get('age_limit', 0) > 0
            
            # Extract language
            language = entry.get('language')
            
            # Platform-specific metadata
            platform_metadata = {
                'channel_url': entry.get('channel_url'),
                'channel_id': entry.get('channel_id'),
                'playable_in_embed': entry.get('playable_in_embed', False),
                'automatic_captions': entry.get('automatic_captions'),
                'subtitles': entry.get('subtitles'),
                'chapters': entry.get('chapters'),
                'heatmap': entry.get('heatmap'),
                'average_rating': entry.get('average_rating'),
                'webpage_url_basename': entry.get('webpage_url_basename'),
                'extractor': entry.get('extractor'),
            }
            
            return VideoData(
                platform="YouTube",
                video_id=video_id,
                title=entry.get('title', ''),
                description=entry.get('description', ''),
                url=entry.get('webpage_url', f"https://www.youtube.com/watch?v={video_id}"),
                thumbnail_url=thumbnail_url,
                duration=duration,
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                share_count=None,  # YouTube doesn't provide share count via yt-dlp
                upload_date=upload_date,
                creator_name=creator_name,
                creator_id=creator_id,
                creator_followers=creator_followers,
                tags=tags,
                categories=categories,
                language=language,
                is_live=is_live,
                is_private=is_private,
                age_restricted=age_restricted,
                platform_metadata=platform_metadata
            )
            
        except Exception as e:
            logger.error(f"Error parsing video entry: {e}")
            return None
    
    async def scrape_popular_channels(self) -> List[VideoData]:
        """Scrape videos from popular mukbang channels"""
        all_videos = []
        
        for channel in youtube_config.channels_to_monitor:
            logger.info(f"Scraping channel: {channel}")
            try:
                videos = await self.get_user_videos(channel, max_results=50)
                all_videos.extend(videos)
                await asyncio.sleep(scraping_config.request_delay)
            except Exception as e:
                logger.error(f"Error scraping channel {channel}: {e}")
                continue
        
        return all_videos
    
    async def scrape_by_categories(self) -> List[VideoData]:
        """Scrape videos by searching within specific categories"""
        all_videos = []
        
        for category in youtube_config.categories:
            for search_term in youtube_config.search_terms:
                query = f"{search_term} {category}"
                logger.info(f"Searching: {query}")
                try:
                    videos = await self.search_videos(query, max_results=20)
                    all_videos.extend(videos)
                    await asyncio.sleep(scraping_config.request_delay)
                except Exception as e:
                    logger.error(f"Error searching {query}: {e}")
                    continue
        
        return all_videos


# Convenience function for quick scraping
async def scrape_youtube_mukbang(max_results: int = 100) -> List[VideoData]:
    """Quick function to scrape mukbang videos from YouTube"""
    scraper = YouTubeScraper()
    
    # Search for mukbang videos
    videos = await scraper.scrape_batch(youtube_config.search_terms, max_results // len(youtube_config.search_terms))
    
    # Filter for mukbang content
    mukbang_videos = scraper.filter_mukbang_videos(videos)
    
    return mukbang_videos


if __name__ == "__main__":
    # Test the scraper
    async def test():
        scraper = YouTubeScraper()
        videos = await scraper.search_videos("mukbang", max_results=5)
        print(f"Found {len(videos)} videos")
        for video in videos:
            print(f"- {video.title} ({video.view_count} views)")
    
    asyncio.run(test()) 