"""Comment card component for the Streamlit frontend."""
import streamlit as st
from datetime import datetime
import pytz
from typing import Dict, Any, List


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


def comment_card(comment: Dict[str, Any], level: int = 0):
    """Display a comment card with proper indentation based on level."""
    indent = level * 20  # 20px per level
    
    with st.container():
        if indent > 0:
            cols = st.columns([indent, 1000 - indent])
            container = cols[1]
        else:
            container = st
        
        with container:
            container.markdown(
                f"**{comment.get('by', 'unknown')}** • "
                f"{format_time(comment.get('time'))}"
            )
            
            if comment.get("text"):
                container.markdown(comment.get("text"))
            else:
                container.markdown("*[deleted]*")
            
            container.markdown("---")


def comment_thread(comments: List[Dict[str, Any]]):
    """Display a thread of comments with proper nesting."""
    comment_dict = {}
    for comment in comments:
        comment_id = comment.get("id")
        comment_dict[comment_id] = {
            "comment": comment,
            "children": []
        }
    
    root_comments = []
    for comment_id, comment_data in comment_dict.items():
        comment = comment_data["comment"]
        parent_id = comment.get("parent_id")
        
        if parent_id in comment_dict:
            comment_dict[parent_id]["children"].append(comment_id)
        else:
            root_comments.append(comment_id)
    
    def display_comment_tree(comment_id, level=0):
        if comment_id not in comment_dict:
            return
        
        comment_data = comment_dict[comment_id]
        comment_card(comment_data["comment"], level)
        
        for child_id in comment_data["children"]:
            display_comment_tree(child_id, level + 1)
    
    for root_id in root_comments:
        display_comment_tree(root_id)
