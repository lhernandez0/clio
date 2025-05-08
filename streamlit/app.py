from datetime import date, timedelta

import pandas as pd
import plotly.express as px

# Import shared utilities
from utils import (
    check_api_connection,
    fetch_recent_headlines,
    fetch_sentiment_distribution,
    fetch_trending_entities,
    get_sentiment_class,
    get_sentiment_icon,
    load_css,
    perform_search,
    show_api_error,
)

import streamlit as st

# Configure page settings
st.set_page_config(page_title="Clio News Analytics", page_icon="📰", layout="wide")

# Add custom CSS
st.markdown(load_css(), unsafe_allow_html=True)

# Main content
st.markdown('<p class="main-header">Clio News Analytics</p>', unsafe_allow_html=True)

# Introduction section
st.markdown(
    """
### Welcome to Clio News Analytics Platform

Clio is a powerful news analytics platform that helps you gain insights from news articles through advanced search,
entity analysis, sentiment tracking, and AI-powered assistance.

**Features available in this demo:**

- **Dashboard**: Overview of news metrics, trending topics, and latest headlines
- **Advanced Search**: Search for news with both text and semantic search capabilities
- **Trends Analysis**: Track entity mentions and relationships
- **News Assistant**: Ask questions about news and get AI-powered responses
- **Article Explorer**: Examine individual articles with detailed analysis
"""
)

# Check API connection
api_connected = check_api_connection()

if not api_connected:
    show_api_error()
    st.stop()

# Quick search bar
st.markdown("### Quick Search")
quick_search = st.text_input(
    "Search news", placeholder="Enter a search term (min. 4 characters)"
)

if len(quick_search) >= 4:
    with st.spinner("Searching..."):
        today = date.today()
        start_date = today - timedelta(days=7)

        results = perform_search(
            query=quick_search,
            search_type="Text",
            start_date=start_date,
            end_date=today,
            page=1,
            size=5,
        )

    if results is not None:
        if results:
            st.markdown("#### Results")
            for result in results:
                sentiment = result.get("sentiment", 0)
                sentiment_icon = get_sentiment_icon(sentiment)
                sentiment_class = get_sentiment_class(sentiment)

                st.markdown(
                    f"""
                <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0;">
                    <h4>{result['title']} {sentiment_icon}</h4>
                    <p>{result['summary'][:200]}...</p>
                    <p><small><b>Source:</b> {result['source']} | <b>Published:</b> {result['published']} |
                    <b>Sentiment:</b> <span class="{sentiment_class}">{round(sentiment, 2)}</span></small></p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("[View all results →](Search)")
        else:
            st.info("No results found for your query.")
    else:
        st.error("Failed to perform search. Please check your API connection.")

st.markdown("---")

# Trending entities overview
st.markdown("### Trending Topics")

with st.spinner("Loading trending topics..."):
    trending_entities = fetch_trending_entities(days=1, size=10)

if trending_entities:
    try:
        # Ensure all entries have the same structure
        valid_entities = []
        for entity in trending_entities:
            # Check if it's a dictionary with required keys
            if isinstance(entity, dict) and "entity" in entity and "count" in entity:
                valid_entities.append(entity)

        if valid_entities:
            # Convert to DataFrame for visualization
            df_entities = pd.DataFrame(valid_entities)

            # Create horizontal bar chart
            fig = px.bar(
                df_entities,
                x="count",
                y="entity",
                orientation="h",
                color="count",
                color_continuous_scale="Blues",
                labels={"count": "Mentions", "entity": "Entity"},
                height=400,
            )
            fig.update_layout(
                margin=dict(l=0, r=10, t=0, b=0),
                xaxis_title="Mentions",
                yaxis_title="",
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("[Explore trends →](Trends)")
        else:
            st.info("No valid trending entities found in the response.")
    except Exception as e:
        st.error(f"Error processing trending entities: {str(e)}")
else:
    st.info(
        "Could not retrieve trending entities. The endpoint may not be available or no data was returned."
    )

# Latest Headlines section
st.markdown("### Latest Headlines")

with st.spinner("Loading recent headlines..."):
    recent_headlines = fetch_recent_headlines(days=1, size=5)

if recent_headlines:
    for headline in recent_headlines:
        sentiment = headline.get("sentiment", 0)
        sentiment_icon = get_sentiment_icon(sentiment)
        sentiment_class = get_sentiment_class(sentiment)

        st.markdown(
            f"""
        <div style="margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #e0e0e0;">
            <h4>{headline['title']} {sentiment_icon}</h4>
            <p>{headline['summary'][:200]}...</p>
            <p><small><b>Source:</b> {headline['source']} | <b>Published:</b> {headline['published']} |
            <b>Sentiment:</b> <span class="{sentiment_class}">{round(sentiment, 2)}</span></small></p>
        </div>
        """,
            unsafe_allow_html=True,
        )
else:
    st.info(
        "Could not retrieve recent headlines. The search endpoint may not be available or no articles were found for the last 24 hours."
    )

# Sentiment Distribution section
st.markdown("### Sentiment Distribution")

with st.spinner("Loading sentiment distribution..."):
    sentiment_data = fetch_sentiment_distribution(days=7)

if sentiment_data:
    # Convert to DataFrame for visualization
    df_sentiment = pd.DataFrame(
        [
            {"sentiment": "Positive", "count": sentiment_data["positive"]},
            {"sentiment": "Neutral", "count": sentiment_data["neutral"]},
            {"sentiment": "Negative", "count": sentiment_data["negative"]},
        ]
    )

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
        height=400,
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(
        "This visualization requires a new API endpoint to provide sentiment distribution data across articles."
    )
