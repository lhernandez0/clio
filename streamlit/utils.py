import time
from datetime import date, timedelta

import requests

import streamlit as st

# Set the base URL for your FastAPI backend
API_BASE_URL = "http://localhost:8000"


# Check API connectivity
def check_api_connection(retries=3, retry_delay=1):
    """
    Check if the API is reachable with retry mechanism

    Args:
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        bool: True if API is reachable, False otherwise
    """
    for attempt in range(retries):
        try:
            response = requests.get(
                f"{API_BASE_URL}/search/trending/",
                params={"days": 1, "size": 1},
                timeout=3,
            )
            if response.status_code == 200:
                return True
            else:
                st.warning(
                    f"API returned status code {response.status_code}. Retrying {attempt+1}/{retries}..."
                )
        except Exception as e:
            if attempt < retries - 1:  # Don't show warning on the last attempt
                # st.warning(f"Could not connect to API. Retrying {attempt+1}/{retries}... ({str(e)})")
                # Only log in console
                print(
                    f"Could not connect to API. Retrying {attempt+1}/{retries}... ({str(e)})"
                )

        if attempt < retries - 1:  # Don't sleep after the last attempt
            time.sleep(retry_delay)

    return False


# Dashboard specific utility functions
def get_todays_articles_count(start_date=None, end_date=None, debug=False):
    """
    Get the count of articles for a date range

    Args:
        start_date: Start date for the range (defaults to today if None)
        end_date: End date for the range (defaults to today if None)
        debug: If True, returns the full response object

    Returns:
        int: Count of articles if successful, 0 if failed
        requests.Response: The full response object if debug is True
    """
    if start_date is None or end_date is None:
        start_date = date.today()
        end_date = date.today()

    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/articles/count/",
            params={"start_date": start_date, "end_date": end_date},
            timeout=10,
        )

        if debug:
            return response

        if response.status_code == 200:
            data = response.json()
            return data.get("count", 0)
        else:
            st.error(f"API returned status code {response.status_code}")
            return 0
    except Exception as e:
        st.error(f"Error fetching articles count: {str(e)}")
        return 0


def get_sources_info(days=1, debug=False):
    """
    Get information about news sources

    Args:
        days: Number of days to look back
        debug: If True, returns the full response object

    Returns:
        dict: Dictionary with sources count and list if successful, None if failed
        requests.Response: The full response object if debug is True
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/sources/",
            params={"start_date": start_date, "end_date": today},
            timeout=10,
        )

        if debug:
            return response

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API returned status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching sources info: {str(e)}")
        return None


def get_sentiment_stats(days=1, debug=False):
    """
    Get sentiment statistics for a time period

    Args:
        days: Number of days to look back
        debug: If True, returns the full response object

    Returns:
        dict: Dictionary with sentiment statistics if successful, None if failed
        requests.Response: The full response object if debug is True
    """
    today = date.today()
    start_date = today - timedelta(days=days - 1)

    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/sentiment/",
            params={"start_date": start_date, "end_date": today},
            timeout=10,
        )

        if debug:
            return response

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API returned status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching sentiment stats: {str(e)}")
        return None


def fetch_recent_headlines(days=1, size=10, debug=False):
    """
    Fetch recent headlines from the API

    Args:
        days: Number of days to look back
        size: Maximum number of headlines to return
        debug: If True, returns the full response object

    Returns:
        list: List of headlines with metadata if successful, None if failed
        requests.Response: The full response object if debug is True
    """
    today = date.today()
    # Calculate start date - start from (days-1) to include today
    start_date = today - timedelta(days=days - 1)

    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/headlines/",
            params={"start_date": start_date, "end_date": today, "size": size},
            timeout=10,
        )

        if debug:
            return response

        if response.status_code == 200:
            data = response.json()
            return data.get("headlines", [])
        else:
            st.error(f"API returned status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching recent headlines: {str(e)}")
        return None


# Fetch trending entities with improved handling
def fetch_trending_entities(days=1, size=10, debug=False):
    """
    Fetch trending entities from the API

    Args:
        days: Number of days to look back
        size: Maximum number of entities to return
        debug: If True, returns the full response object

    Returns:
        list: List of trending entities if successful, None if failed
        requests.Response: The full response object if debug is True
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/search/trending/",
            params={"days": days, "size": size},
            timeout=10,
        )

        # Log the raw response for debugging
        if debug:
            st.write("### Raw Response")
            try:
                st.json(response.json())
            except Exception as e:
                st.write("Failed to parse response as JSON")
                print(e)
                st.write(response.text)
            return response

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", {})

            # Handle the nested _l_ array structure
            entities_list = []
            if isinstance(results, dict) and "_l_" in results:
                for item in results["_l_"]:
                    if isinstance(item, dict) and "key" in item and "doc_count" in item:
                        entities_list.append(
                            {"entity": item["key"], "count": item["doc_count"]}
                        )

            if debug:
                st.write("Debug: Processed entities list:", entities_list)

            return entities_list
        else:
            st.error(f"API returned status code {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching trending entities: {str(e)}")
        return None


# Perform search - keep this for the search functionality
def perform_search(
    query, search_type, start_date, end_date, page, size, sort=None, debug=False
):
    """
    Perform search query against the API

    Args:
        query: Search query string
        search_type: "Text" or "Semantic"
        start_date: Start date for search
        end_date: End date for search
        page: Page number
        size: Results per page
        sort: Sort parameter (e.g., "published:desc")
        debug: If True, returns the full response object

    Returns:
        list: List of search results if successful, None if failed
        requests.Response: The full response object if debug is True
    """
    endpoint = "/search/semantic/" if search_type == "Semantic" else "/search/text/"
    try:
        if debug:
            st.write(f"Debug: Making {search_type} search request to {endpoint}")
            st.write(f"Debug: Query: {query}")
            st.write(f"Debug: Date range: {start_date} to {end_date}")
            st.write(f"Debug: Page: {page}, Size: {size}")
            if sort:
                st.write(f"Debug: Sort: {sort}")

        # For empty or wildcard queries, use a more specific query
        if query in ["*", ""]:
            query = "news"  # Use a generic term that should match most articles

        params = {
            "query": query,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "page": page,
            "size": size,
        }

        if sort:
            params["sort"] = sort

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=10,
        )

        if debug:
            st.write(f"Debug: Response status code: {response.status_code}")
            try:
                st.write("Debug: Response body:")
                st.json(response.json())
            except Exception as e:
                st.write("Debug: Raw response text:")
                st.write(response.text)
                print(e)
            return response

        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, dict):
                st.warning(
                    f"Unexpected response format: Expected dictionary, got {type(data)}"
                )
                return []

            results = data.get("results", [])
            if not isinstance(results, list):
                st.warning(
                    f"Unexpected results format: Expected list, got {type(results)}"
                )
                return []

            return results
        else:
            st.error(f"API returned status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {str(e)}")
        return None


# Helper functions for sentiment display
def get_sentiment_class(sentiment):
    """Return CSS class based on sentiment value"""
    if sentiment is None:
        return "sentiment-neutral"
    if sentiment > 0.1:
        return "sentiment-positive"
    elif sentiment < -0.1:
        return "sentiment-negative"
    else:
        return "sentiment-neutral"


def get_sentiment_icon(sentiment):
    """Return emoji based on sentiment value"""
    if sentiment is None:
        return "😐"
    if sentiment > 0.1:
        return "😀"
    elif sentiment < -0.1:
        return "😞"
    else:
        return "😐"


# Custom CSS for consistent styling across pages
def load_css():
    return """
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            font-weight: 700;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #424242;
            font-weight: 500;
        }
        .card {
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            background-color: white;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 1rem;
            color: #616161;
        }
        .sentiment-positive {
            color: #4CAF50;
        }
        .sentiment-negative {
            color: #F44336;
        }
        .sentiment-neutral {
            color: #9E9E9E;
        }
        .connection-error {
            padding: 20px;
            border-radius: 5px;
            background-color: #FFEBEE;
            color: #C62828;
            margin-bottom: 20px;
        }
        .debug-info {
            margin-top: 20px;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 5px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
    </style>
    """


# Display API connection error if needed
def show_api_error():
    st.markdown(
        f"""
    <div class="connection-error">
        <h3>⚠️ API Connection Error</h3>
        <p>Could not connect to the backend API at {API_BASE_URL}. Please ensure the API server is running and accessible.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# Debug helper for API responses
def debug_api_response(response, label="API Response"):
    """Display API response for debugging"""
    with st.expander(f"Debug: {label}"):
        if isinstance(response, requests.Response):
            st.markdown("### Request")
            st.markdown(f"**URL**: {response.url}")
            st.markdown(f"**Status Code**: {response.status_code}")

            st.markdown("### Response Headers")
            st.json(dict(response.headers))

            st.markdown("### Response Body")
            try:
                st.json(response.json())
            except Exception as e:
                print(e)
                st.text(response.text)

        elif response is None:
            st.markdown("No response (None)")
        else:
            st.json(response)


# We'll keep fetch_sentiment_distribution for backward compatibility
def fetch_sentiment_distribution(days=7, debug=False):
    """
    Fetch sentiment distribution data

    Args:
        days: Number of days to analyze
        debug: If True, returns the full response object

    Returns:
        dict: Dictionary with sentiment distribution data if successful, None if failed
    """
    sentiment_stats = get_sentiment_stats(days=days, debug=debug)

    if debug:
        return sentiment_stats

    if sentiment_stats:
        # Convert the format to match the existing code
        distribution = sentiment_stats.get("distribution", {})
        return {
            "positive": distribution.get("positive", 0),
            "neutral": distribution.get("neutral", 0),
            "negative": distribution.get("negative", 0),
        }
    return None
