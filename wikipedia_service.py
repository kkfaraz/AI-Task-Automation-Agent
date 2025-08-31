import requests
import logging
from typing import Optional
import re

logger = logging.getLogger(__name__)

class WikipediaService:
    """Service for fetching educational content from Wikipedia"""
    
    def __init__(self):
        self.api_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.search_api_url = "https://en.wikipedia.org/w/api.php"
    
    def fetch_topic_summary(self, topic: str) -> Optional[str]:
        """Fetch a summary for a given topic from Wikipedia"""
        try:
            # First, search for the best matching page
            page_title = self._search_for_page(topic)
            if not page_title:
                logger.warning(f"No Wikipedia page found for topic: {topic}")
                return None
            
            # Fetch the page summary
            summary_url = f"{self.api_url}{page_title}"
            headers = {
                'User-Agent': 'StudyPlannerApp/1.0 (Educational Use)'
            }
            
            response = requests.get(summary_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract and clean the summary
            extract = data.get('extract', '')
            if extract:
                # Clean up the text
                cleaned_summary = self._clean_wikipedia_text(extract)
                logger.info(f"Successfully fetched summary for: {topic}")
                return cleaned_summary
            else:
                logger.warning(f"No extract available for: {topic}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Wikipedia content for '{topic}': {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching Wikipedia content: {e}")
            return None
    
    def _search_for_page(self, topic: str) -> Optional[str]:
        """Search Wikipedia for the most relevant page title"""
        try:
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': topic,
                'format': 'json',
                'srlimit': 5,  # Get top 5 results
                'srprop': 'snippet'
            }
            
            headers = {
                'User-Agent': 'StudyPlannerApp/1.0 (Educational Use)'
            }
            
            response = requests.get(self.search_api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            if search_results:
                # Return the title of the most relevant result
                best_match = search_results[0]
                return best_match['title'].replace(' ', '_')
            else:
                return None
                
        except Exception as e:
            logger.error(f"Wikipedia search failed for '{topic}': {e}")
            return None
    
    def _clean_wikipedia_text(self, text: str) -> str:
        """Clean Wikipedia text for better readability"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove Wikipedia-specific formatting
        text = re.sub(r'\[[0-9]+\]', '', text)  # Remove citation numbers
        text = re.sub(r'\([^)]*\)', '', text)   # Remove parenthetical notes (optional)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Limit length for study purposes
        if len(text) > 1000:
            sentences = text.split('.')
            summary = ''
            for sentence in sentences:
                if len(summary) + len(sentence) < 800:
                    summary += sentence + '.'
                else:
                    break
            text = summary
        
        return text.strip()
    
    def fetch_multiple_topics(self, topics: list) -> dict:
        """Fetch summaries for multiple topics"""
        results = {}
        
        for topic in topics:
            summary = self.fetch_topic_summary(topic)
            results[topic] = summary
            
            # Add a small delay to be respectful to Wikipedia's servers
            import time
            time.sleep(0.5)
        
        return results
    
    def search_related_topics(self, main_topic: str, limit: int = 5) -> list:
        """Find related topics for additional study material"""
        try:
            # Search for pages related to the main topic
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': f'incategory:"{main_topic}" OR "{main_topic}"',
                'format': 'json',
                'srlimit': limit * 2,  # Get more results to filter
                'srprop': 'snippet|size'
            }
            
            headers = {
                'User-Agent': 'StudyPlannerApp/1.0 (Educational Use)'
            }
            
            response = requests.get(self.search_api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            # Filter and format results
            related_topics = []
            for result in search_results[:limit]:
                if result['title'].lower() != main_topic.lower():
                    related_topics.append({
                        'title': result['title'],
                        'snippet': self._clean_wikipedia_text(result.get('snippet', '')),
                        'relevance': 'related'
                    })
            
            return related_topics
            
        except Exception as e:
            logger.error(f"Failed to find related topics for '{main_topic}': {e}")
            return []

# Create a global instance for easy importing
wikipedia_service = WikipediaService()
