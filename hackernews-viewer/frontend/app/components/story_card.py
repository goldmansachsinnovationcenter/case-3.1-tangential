"""Story card component for the Streamlit frontend."""
import streamlit as st
from datetime import datetime
import pytz
from typing import Dict, Any


def format_time(timestamp: str) -> str:
    """Format timestamp as relative time."""
    if not timestamp:
        return "Unknown time"
    
    dt = datetime.fromisoformat(timestamp)
    now = datetime.now(pytz.UTC)
    
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"


def story_card(story: Dict[str, Any], show_comments_button: bool = True):
    """Display a story card."""
    with st.container():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if story.get("url"):
                st.markdown(f"### [{story.get('title')}]({story.get('url')})")
            else:
                st.markdown(f"### {story.get('title')}")
        
        with col2:
            st.metric("Score", story.get("score", 0))
        
        st.markdown(
            f"Posted by **{story.get('by', 'unknown')}** • "
            f"{format_time(story.get('time'))} • "
            f"{story.get('descendants', 0)} comments"
        )
        
        if story.get("text"):
            with st.expander("Show text", expanded=False):
                st.markdown(story.get("text"))
        
        if show_comments_button:
            if st.button(f"View Comments", key=f"comments_{story.get('id')}"):
                st.session_state.selected_story = story.get("id")
                st.session_state.view = "story_detail"
                st.rerun()
        
        st.markdown("---")
