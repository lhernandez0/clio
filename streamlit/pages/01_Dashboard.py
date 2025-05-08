from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import requests

# Import shared utilities
from utils import (
    check_api_connection,
    debug_api_response,
    fetch_recent_headlines,
    fetch_trending_entities,
    get_sentiment_class,
    get_sentiment_icon,
    get_sentiment_stats,
    get_sources_info,
    get_todays_articles_count,
    load_css,
    perform_search,
    show_api_error,
)

import streamlit as st

# Configure page settings
st.set_page_config(
    page_title="News Analytics Dashboard - Clio", page_icon="📊", layout="wide"
)

# Add custom CSS
st.markdown(load_css(), unsafe_allow_html=True)


# Define a reusable function for API data loading with spinner
def load_api_data(api_function, *args, **kwargs):
    with st.spinner("Loading data..."):
        data = api_function(*args, **kwargs)
    return data


# Main content
st.markdown('<p class="main-header">News Analytics Dashboard</p>', unsafe_allow_html=True)
st.markdown("Real-time insights from news coverage")

# Check API connection
api_connected = check_api_connection()

if not api_connected:
    show_api_error()
    st.stop()

# Dashboard Settings - moved from sidebar to main content
st.markdown("### Dashboard Settings")
col_settings1, col_settings2 = st.columns([3, 1])

with col_settings1:
    time_period = st.radio(
        "Time Period",
        ["Today", "Last 3 Days", "Last 7 Days", "Last 30 Days"],
        index=0,
        horizontal=True,
        help="Select the time period for dashboard analytics",
    )

with col_settings2:
    with st.expander("Debug Settings"):
        debug_mode = st.checkbox(
            "Enable Debug Mode",
            value=False,
            help="Enable to show API debugging information",
        )

# Calculate date range based on selection
today = date.today()
if time_period == "Today":
    start_date = today
    days_range = 1
elif time_period == "Last 3 Days":
    start_date = today - timedelta(days=2)
    days_range = 3
elif time_period == "Last 7 Days":
    start_date = today - timedelta(days=6)
    days_range = 7
else:  # Last 30 Days
    start_date = today - timedelta(days=29)
    days_range = 30

end_date = today

# Divider after settings
st.markdown("---")

# Layout: Create a 2x2 grid of metrics at the top
col1, col2, col3, col4 = st.columns(4)

# Articles Count
with col1:
    st.markdown("### Articles Published")
    articles_count = load_api_data(
        get_todays_articles_count,
        start_date=start_date,
        end_date=end_date,
        debug=debug_mode,
    )

    if isinstance(articles_count, requests.Response):
        if debug_mode:
            debug_api_response(articles_count, "Articles Count API Response")
        try:
            data = articles_count.json()
            count = data.get("count", 0)
            st.markdown(
                f'<div class="metric-value">{count}</div>', unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="metric-label">articles {time_period.lower()}</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Error parsing API response: {str(e)}")
    else:
        st.markdown(
            f'<div class="metric-value">{articles_count}</div>', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="metric-label">articles {time_period.lower()}</div>',
            unsafe_allow_html=True,
        )

# Sources Count
with col2:
    st.markdown("### News Sources")
    sources_info = load_api_data(get_sources_info, days=days_range, debug=debug_mode)

    if isinstance(sources_info, requests.Response):
        if debug_mode:
            debug_api_response(sources_info, "Sources API Response")
        try:
            data = sources_info.json()
            sources_count = data.get("count", 0)
            st.markdown(
                f'<div class="metric-value">{sources_count}</div>', unsafe_allow_html=True
            )
            st.markdown(
                '<div class="metric-label">unique sources</div>', unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Error parsing API response: {str(e)}")
    elif sources_info:
        sources_count = sources_info.get("count", 0)
        st.markdown(
            f'<div class="metric-value">{sources_count}</div>', unsafe_allow_html=True
        )
        st.markdown(
            '<div class="metric-label">unique sources</div>', unsafe_allow_html=True
        )
    else:
        st.info("No sources found")

# Sentiment Overview
with col3:
    st.markdown("### Avg. Sentiment")
    sentiment_info = load_api_data(get_sentiment_stats, days=days_range, debug=debug_mode)

    if isinstance(sentiment_info, requests.Response):
        if debug_mode:
            debug_api_response(sentiment_info, "Sentiment API Response")
        try:
            data = sentiment_info.json()
            avg_sentiment = data.get("average")
            sentiment_class = get_sentiment_class(avg_sentiment)
            if avg_sentiment is not None:
                score = round(avg_sentiment, 2)
                st.markdown(
                    f'<div class="metric-value {sentiment_class}">{score}</div>',
                    unsafe_allow_html=True,
                )
                mood = (
                    "Positive"
                    if score > 0.1
                    else "Negative" if score < -0.1 else "Neutral"
                )
                st.markdown(
                    f'<div class="metric-label">Overall mood: {mood}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.info("No sentiment data available")
        except Exception as e:
            st.error(f"Error parsing API response: {str(e)}")
    elif sentiment_info:
        avg_sentiment = sentiment_info.get("average")
        sentiment_class = get_sentiment_class(avg_sentiment)
        if avg_sentiment is not None:
            score = round(avg_sentiment, 2)
            st.markdown(
                f'<div class="metric-value {sentiment_class}">{score}</div>',
                unsafe_allow_html=True,
            )
            mood = (
                "Positive" if score > 0.1 else "Negative" if score < -0.1 else "Neutral"
            )
            st.markdown(
                f'<div class="metric-label">Overall mood: {mood}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("No sentiment data available")
    else:
        st.info("No sentiment data available")

# Topic Count
with col4:
    st.markdown("### Trending Topics")
    trending_entities = load_api_data(
        fetch_trending_entities, days=days_range, size=100, debug=debug_mode
    )

    if isinstance(trending_entities, requests.Response):
        if debug_mode:
            debug_api_response(trending_entities, "Trending Topics API Response")
        # Extract data from response
        try:
            data = trending_entities.json()
            results = data.get("results", {})

            # Process the results similar to fetch_trending_entities
            processed_entities = []
            if isinstance(results, dict) and "_l_" in results:
                for item in results["_l_"]:
                    if isinstance(item, dict) and "key" in item and "doc_count" in item:
                        processed_entities.append(
                            {"entity": item["key"], "count": item["doc_count"]}
                        )

            trending_count = len(processed_entities)
            st.markdown(
                f'<div class="metric-value">{trending_count}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="metric-label">entities mentioned</div>',
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Error processing trending entities response: {str(e)}")
            trending_count = 0
    elif trending_entities:
        trending_count = len(trending_entities)
        st.markdown(
            f'<div class="metric-value">{trending_count}</div>', unsafe_allow_html=True
        )
        st.markdown(
            '<div class="metric-label">entities mentioned</div>', unsafe_allow_html=True
        )
    else:
        st.info("No trending topics found")

# Create tabs for different analysis views
tab1, tab2, tab3 = st.tabs(["Trending Entities", "Sentiment Analysis", "News Sources"])

# Tab 1: Trending Entities
with tab1:
    st.markdown("### Top Trending Entities")

    if trending_entities and not isinstance(trending_entities, requests.Response):
        # Get top 15 for the visualization
        top_entities = (
            trending_entities[:15] if len(trending_entities) > 15 else trending_entities
        )

        # Convert to DataFrame for visualization
        df_entities = pd.DataFrame(top_entities)

        # Create horizontal bar chart
        fig = px.bar(
            df_entities,
            x="count",
            y="entity",
            orientation="h",
            color="count",
            color_continuous_scale="Blues",
            labels={"count": "Mentions", "entity": "Entity"},
            height=500,
        )
        fig.update_layout(
            margin=dict(l=0, r=10, t=0, b=0),
            xaxis_title="Mentions",
            yaxis_title="",
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Show full list in an expander
        with st.expander("View all trending entities"):
            # Create a DataFrame with all trending entities
            df_all_entities = pd.DataFrame(trending_entities)
            st.dataframe(df_all_entities, use_container_width=True)

    else:
        st.info("No trending entities data available")

# Tab 2: Sentiment Analysis
with tab2:
    st.markdown("### Sentiment Distribution")
    sentiment_data = load_api_data(get_sentiment_stats, days=days_range, debug=debug_mode)

    if isinstance(sentiment_data, requests.Response):
        if debug_mode:
            debug_api_response(sentiment_data, "Sentiment Distribution API Response")
        try:
            data = sentiment_data.json()
            distribution = data.get("distribution", {})
            sentiment_distribution = {
                "positive": distribution.get("positive", 0),
                "neutral": distribution.get("neutral", 0),
                "negative": distribution.get("negative", 0),
            }
        except Exception as e:
            st.error(f"Error processing sentiment distribution: {str(e)}")
            sentiment_distribution = None
    elif sentiment_data:
        # Extract the distribution from the sentiment_data
        distribution = sentiment_data.get("distribution", {})
        sentiment_distribution = {
            "positive": distribution.get("positive", 0),
            "neutral": distribution.get("neutral", 0),
            "negative": distribution.get("negative", 0),
        }
    else:
        sentiment_distribution = None

    if sentiment_distribution:
        # Convert to DataFrame for visualization
        df_sentiment = pd.DataFrame(
            [
                {
                    "sentiment": "Positive",
                    "count": sentiment_distribution["positive"],
                    "color": "#4CAF50",
                },
                {
                    "sentiment": "Neutral",
                    "count": sentiment_distribution["neutral"],
                    "color": "#9E9E9E",
                },
                {
                    "sentiment": "Negative",
                    "count": sentiment_distribution["negative"],
                    "color": "#F44336",
                },
            ]
        )

        total = df_sentiment["count"].sum()
        if total > 0:  # Avoid division by zero
            df_sentiment["percentage"] = df_sentiment["count"] / total * 100
        else:
            df_sentiment["percentage"] = 0

        col_s1, col_s2 = st.columns([2, 1])

        with col_s1:
            # Create pie chart
            fig = px.pie(
                df_sentiment,
                values="count",
                names="sentiment",
                color="sentiment",
                color_discrete_map={
                    "Positive": "#4CAF50",
                    "Neutral": "#9E9E9E",
                    "Negative": "#F44336",
                },
                height=350,
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_s2:
            # Display sentiment distribution as text with metrics
            st.metric(
                "Positive", f"{df_sentiment.iloc[0]['percentage']:.1f}%", delta=None
            )
            st.metric("Neutral", f"{df_sentiment.iloc[1]['percentage']:.1f}%", delta=None)
            st.metric(
                "Negative", f"{df_sentiment.iloc[2]['percentage']:.1f}%", delta=None
            )
    else:
        st.info("No sentiment distribution data available")

# Tab 3: Source Analysis
with tab3:
    st.markdown("### Top News Sources")

    if sources_info and not isinstance(sources_info, requests.Response):
        # Process the sources data
        sources_data = sources_info.get("sources", {})

        if sources_data:
            # Create a DataFrame from the sources
            df_sources = pd.DataFrame(
                [
                    {"source": source, "count": count}
                    for source, count in sources_data.items()
                ]
            )

            # Sort by count and get top 15
            df_sources = df_sources.sort_values("count", ascending=False).head(15)

            # Create horizontal bar chart
            fig = px.bar(
                df_sources,
                x="count",
                y="source",
                orientation="h",
                color="count",
                color_continuous_scale="Viridis",
                labels={"count": "Number of Articles", "source": "Source"},
                height=500,
            )
            fig.update_layout(
                margin=dict(l=0, r=10, t=0, b=0),
                xaxis_title="Number of Articles",
                yaxis_title="",
                coloraxis_showscale=False,
                yaxis=dict(categoryorder="total ascending"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # Show all sources in an expander
            with st.expander("View all sources"):
                # Create a DataFrame with all sources
                all_sources = pd.DataFrame(
                    [
                        {"source": source, "count": count}
                        for source, count in sources_data.items()
                    ]
                ).sort_values("count", ascending=False)

                st.dataframe(all_sources, use_container_width=True)
        else:
            st.info("No source data available")
    else:
        st.info("No source data available")

# Recent Headlines section
st.markdown("### Recent Headlines")

# Add a search option
search_col1, search_col2 = st.columns([3, 1])
with search_col1:
    search_query = st.text_input(
        "Search headlines", placeholder="Enter keywords to filter headlines"
    )
with search_col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Add vertical space
    search_button = st.button("Search")

# Get headlines based on search or recent criteria
if search_query and (search_button or search_query):
    # If searching, use text search directly with a larger size
    with st.spinner(f"Searching for '{search_query}'..."):
        search_results = load_api_data(
            perform_search,
            query=search_query,
            search_type="Text",
            start_date=start_date,
            end_date=end_date,
            page=1,
            size=50,  # Get more results when searching
            sort="published:desc",
            debug=debug_mode,
        )

        if isinstance(search_results, requests.Response):
            if debug_mode:
                debug_api_response(search_results, "Search Results API Response")
            try:
                data = search_results.json()
                recent_headlines = data.get("results", [])
            except Exception as e:
                st.error(f"Error processing search results: {str(e)}")
                recent_headlines = []
        else:
            recent_headlines = search_results or []
else:
    # If not searching, just get recent headlines
    recent_headlines = load_api_data(
        fetch_recent_headlines, days=days_range, size=10, debug=debug_mode
    )

    if isinstance(recent_headlines, requests.Response):
        if debug_mode:
            debug_api_response(recent_headlines, "Recent Headlines API Response")
        try:
            data = recent_headlines.json()
            recent_headlines = data.get("headlines", [])
        except Exception as e:
            st.error(f"Error processing headlines response: {str(e)}")
            recent_headlines = []

# Display headlines
if recent_headlines:
    headline_count = len(recent_headlines)
    st.write(
        f"Showing {headline_count} {'article' if headline_count == 1 else 'articles'}"
    )

    for i, headline in enumerate(recent_headlines):
        sentiment = float(headline.get("sentiment", 0))
        sentiment_icon = get_sentiment_icon(sentiment)
        sentiment_class = get_sentiment_class(sentiment)

        # Format the date
        try:
            published_date = headline.get("published", "Unknown")
            if published_date != "Unknown":
                # Parse the date string
                dt = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
                # Format it as a more readable string
                published_date = dt.strftime("%B %d, %Y at %H:%M")
        except Exception:
            published_date = headline.get("published", "Unknown")

        # If searching, highlight the search term in the title and summary
        title = headline.get("title", "No title")
        summary = headline.get("summary", "")

        if search_query:
            # Highlight the search term in the title and summary
            search_term_lower = search_query.lower()
            title_lower = title.lower()
            summary_lower = summary.lower()

            if search_term_lower in title_lower:
                # Find the position of the search term in the title
                start_idx = title_lower.find(search_term_lower)
                end_idx = start_idx + len(search_term_lower)

                # Highlight the search term with a yellow background
                title = (
                    title[:start_idx]
                    + f'<span style="background-color: #FFFF00;">{title[start_idx:end_idx]}</span>'
                    + title[end_idx:]
                )

            if search_term_lower in summary_lower:
                # Find the position of the search term in the summary
                start_idx = summary_lower.find(search_term_lower)
                end_idx = start_idx + len(search_term_lower)

                # Highlight the search term with a yellow background
                summary = (
                    summary[:start_idx]
                    + f'<span style="background-color: #FFFF00;">{summary[start_idx:end_idx]}</span>'
                    + summary[end_idx:]
                )

        st.markdown(
            f"""
        <div style="margin-bottom: 20px; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); background-color: white;">
            <h3 style="margin-top: 0;">{title} {sentiment_icon}</h3>
            <p>{summary[:250]}{'...' if len(summary) > 250 else ''}</p>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span><b>Source:</b> {headline.get('source', 'Unknown')}</span>
                    <span style="margin-left: 15px;"><b>Published:</b> {published_date}</span>
                </div>
                <div>
                    <span><b>Sentiment:</b> <span class="{sentiment_class}">{round(sentiment, 2)}</span></span>
                    <a href="{headline.get('link', '#')}" target="_blank" style="margin-left: 15px;">Read More →</a>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add a horizontal rule after each headline except the last one
        if i < len(recent_headlines) - 1:
            st.markdown("---")
else:
    if search_query:
        st.info(
            f"No articles found matching '{search_query}' in the selected time period ({time_period})."
        )
    else:
        st.info(
            f"No recent headlines available for the selected time period ({time_period})."
        )

# Footer with data update information
st.markdown("---")
st.markdown(
    f"<p style='text-align: center; color: #666;'>Data as of {datetime.now().strftime('%B %d, %Y at %H:%M')}. Analyzed period: {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}.</p>",
    unsafe_allow_html=True,
)
