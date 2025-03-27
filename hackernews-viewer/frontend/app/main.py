"""Main Streamlit application."""
import streamlit as st
import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv

from app.components.story_card import story_card
from app.components.comment_card import comment_thread
from app.utils.api import (
    get_top_stories, 
    get_story, 
    get_story_comments, 
    get_user, 
    get_system_status, 
    trigger_refresh
)

load_dotenv()

st.set_page_config(
    page_title="HackerNews Viewer",
    page_icon="📰",
    layout="wide",
)

if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_story" not in st.session_state:
    st.session_state.selected_story = None
if "refresh_status" not in st.session_state:
    st.session_state.refresh_status = None


st.title("HackerNews Viewer")
st.subheader("Top Stories and Comments")


def go_home():
    st.session_state.view = "home"
    st.session_state.selected_story = None


with st.sidebar:
    st.title("Navigation")
    
    if st.button("Home", use_container_width=True):
        go_home()
    
    st.markdown("---")
    
    st.subheader("System Status")
    
    async def load_status():
        try:
            return await get_system_status()
        except Exception as e:
            st.error(f"Error loading system status: {str(e)}")
            return {"status": "error", "last_refresh": None}
    
    status = asyncio.run(load_status())
    
    if status["status"] == "ok":
        st.success("System: Online")
    else:
        st.error("System: Offline")
    
    if status.get("last_refresh"):
        refresh_time = datetime.fromisoformat(status["last_refresh"]["refresh_time"])
        st.write(f"Last refresh: {refresh_time.strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"Stories: {status['last_refresh']['stories_refreshed']}")
        st.write(f"Comments: {status['last_refresh']['comments_refreshed']}")
    else:
        st.write("No refresh data available")
    
    if st.button("Refresh Data", use_container_width=True):
        try:
            result = asyncio.run(trigger_refresh())
            st.session_state.refresh_status = "Refresh started"
            st.success("Refresh started")
        except Exception as e:
            st.session_state.refresh_status = f"Error: {str(e)}"
            st.error(f"Error: {str(e)}")


if st.session_state.view == "home":
    st.header("Top Stories")
    
    async def load_stories():
        try:
            return await get_top_stories(limit=5)
        except Exception as e:
            st.error(f"Error loading stories: {str(e)}")
            return []
    
    stories = asyncio.run(load_stories())
    
    if stories:
        for story in stories:
            story_card(story)
    else:
        st.info("No stories available. Try refreshing the data.")

elif st.session_state.view == "story_detail":
    if st.session_state.selected_story:
        if st.button("← Back to Stories"):
            go_home()
        
        async def load_story_detail():
            try:
                story = await get_story(st.session_state.selected_story)
                comments = await get_story_comments(st.session_state.selected_story, limit=10)
                return story, comments
            except Exception as e:
                st.error(f"Error loading story details: {str(e)}")
                return None, []
        
        story, comments = asyncio.run(load_story_detail())
        
        if story:
            story_card(story, show_comments_button=False)
            
            st.header(f"Comments ({len(comments)})")
            
            if comments:
                comment_thread(comments)
            else:
                st.info("No comments available for this story.")
        else:
            st.error("Story not found")
            if st.button("Return to Home"):
                go_home()


st.markdown("---")
st.markdown("Data source: [HackerNews API](https://github.com/HackerNews/API)")
st.markdown("© 2025 HackerNews Viewer")
