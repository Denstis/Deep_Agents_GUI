"""
Web Search Tools - DuckDuckGo search integration for DeepAgents
"""

import logging
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Check if DuckDuckGo search is available
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
    logger.info("DuckDuckGo search available")
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("DuckDuckGo search not available - install with: pip install duckduckgo-search")


class WebSearchTools:
    """Web search tools using DuckDuckGo."""
    
    @staticmethod
    @tool
    def web_search(query: str, num_results: int = 5) -> str:
        """Search the web for current information.
        
        Args:
            query: Search query string.
            num_results: Number of results to return (default: 5).
            
        Returns:
            Search results with titles and snippets.
        """
        if not DDGS_AVAILABLE:
            logger.warning("Web search requested but DuckDuckGo not available")
            return "Error: Web search is not available. Please install duckduckgo-search package."
        
        try:
            logger.info(f"Performing web search: '{query}' (num_results={num_results})")
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=num_results))
                if not results:
                    return f"No results found for '{query}'"
                
                formatted = []
                for i, r in enumerate(results[:num_results], 1):
                    title = r.get('title', 'No title')
                    body = r.get('body', 'No description')
                    url = r.get('href', 'No URL')
                    formatted.append(f"{i}. {title}\n   {body}\n   URL: {url}")
                
                result_text = "\n\n".join(formatted)
                logger.info(f"Web search returned {len(results)} results")
                return f"Search results for '{query}':\n\n{result_text}"
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return f"Error performing web search: {str(e)}"
    
    @staticmethod
    @tool
    def news_search(topic: str, num_results: int = 3) -> str:
        """Search for recent news on a topic.
        
        Args:
            topic: News topic to search for.
            num_results: Number of results to return (default: 3).
            
        Returns:
            Recent news articles about the topic.
        """
        if not DDGS_AVAILABLE:
            return "Error: News search is not available. Please install duckduckgo-search package."
        
        try:
            logger.info(f"Performing news search: '{topic}'")
            with DDGS() as ddgs:
                results = list(ddgs.news(topic, max_results=num_results))
                if not results:
                    return f"No news found for '{topic}'"
                
                formatted = []
                for i, r in enumerate(results[:num_results], 1):
                    title = r.get('title', 'No title')
                    source = r.get('source', 'Unknown source')
                    date = r.get('date', 'Unknown date')
                    url = r.get('url', 'No URL')
                    formatted.append(f"{i}. {title}\n   Source: {source} | Date: {date}\n   URL: {url}")
                
                result_text = "\n\n".join(formatted)
                logger.info(f"News search returned {len(results)} results")
                return f"Recent news about '{topic}':\n\n{result_text}"
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return f"Error performing news search: {str(e)}"
