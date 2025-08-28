import streamlit as st
from streamlit_chat import message
import random
import time
from datetime import datetime

def initialize_chatbot():
    """Initialize chatbot session state"""
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = []
    if "chatbot_user_input" not in st.session_state:
        st.session_state.chatbot_user_input = ""

def get_dummy_response(user_message):
    """Generate dummy responses based on user input"""
    user_message_lower = user_message.lower()
    
    # Insurance-specific responses
    responses = {
        "greeting": [
            "Hello! Welcome to Datasonic AI Assistant. How can I help you today?",
            "Hi there! I'm here to assist you with your insurance operations.",
            "Greetings! What can I help you with regarding policies or claims?"
        ],
        "default": [
            "I'm here to help with Datasonic insurance operations. Can you tell me more about what you need?",
            "That's an interesting question! How can I assist you with your insurance tasks today?",
            "I'd be happy to help! Could you provide more details about what you're looking for?"
        ]
    }
    
    # Determine response category
    if any(word in user_message_lower for word in ["hello", "hi", "hey", "greetings"]):
        category = "greeting"
    else:
        category = "default"
    
    return random.choice(responses[category])

def chatbot_interface():
    initialize_chatbot()
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display welcome message if no messages
        if not st.session_state.chatbot_messages:
            message("👋 Welcome to Datasonic! I'm your AI assistant for insurance operations. How can I help you today?", 
                   key="welcome", avatar_style="bottts")
        
        # Display chat history
        for i, msg in enumerate(st.session_state.chatbot_messages):
            if msg["role"] == "user":
                message(msg["content"], is_user=True, key=f"user_{i}", avatar_style="personas")
            else:
                message(msg["content"], key=f"bot_{i}", avatar_style="bottts")
    
    # Chat input section
    st.markdown("---")
    
    # Create columns for input and button
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message here...", 
            value="",
            placeholder="Ask me anything!",
            key="chat_input"
        )
    
    with col2:
        send_button = st.button("Send", type="primary")
    
    # Process user input
    if send_button and user_input.strip():
        # Add user message
        st.session_state.chatbot_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Show typing indicator
        with st.spinner("Assistant is typing..."):
            time.sleep(1)  # Simulate thinking time
            
            # Generate bot response
            bot_response = get_dummy_response(user_input)
            
            # Add bot response
            st.session_state.chatbot_messages.append({
                "role": "assistant",
                "content": bot_response,
                "timestamp": datetime.now()
            })
        
        # Clear input and rerun
        st.rerun()
    
    # Chat management
    st.markdown("---")
    
    col1 = st.columns(1)[0]
    
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chatbot_messages = []
            st.success("Chat history cleared!")
            st.rerun()
    