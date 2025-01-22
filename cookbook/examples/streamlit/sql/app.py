from typing import List

import streamlit as st
from agno.agent import Agent
from agno.utils.log import logger

from sql_agent import get_sql_agent


st.set_page_config(
    page_title="SQL Agent",
    page_icon=":orange_heart:",
)
st.title("SQL Agent")
st.markdown("##### :orange_heart: built using [Agno](https://github.com/agno-ai/agno)")
with st.expander(":rainbow[:point_down: Example Questions]"):
    st.markdown("- Which driver has the most race wins?")
    st.markdown("- Which team won the most Constructors Championships?")


def main() -> None:
    # Get the agent
    sql_agent: Agent
    if "sql_agent" not in st.session_state or st.session_state["sql_agent"] is None:
        logger.info("---*--- Creating new SQL agent ---*---")
        sql_agent = get_sql_agent()
        st.session_state["sql_agent"] = sql_agent
    else:
        sql_agent = st.session_state["sql_agent"]

    # Initialize messages as a list if it doesn't exist or isn't a list
    if "messages" not in st.session_state or not isinstance(st.session_state["messages"], list):
        st.session_state["messages"] = [{"role": "agent", "content": "Ask me about F1 data from 1950 to 2020."}]

    def add_message(role: str, content: str) -> None:
        """Safely add a message to the session state"""
        if not isinstance(st.session_state["messages"], list):
            st.session_state["messages"] = []
        st.session_state["messages"].append({"role": role, "content": content})

    # Prompt for user input
    if prompt := st.chat_input():
        add_message("user", prompt)

    # Sample buttons
    if st.sidebar.button("Show tables"):
        _message = "Which tables do you have access to?"
        add_message("user", _message)

    if st.sidebar.button("Describe tables"):
        _message = "Tell me more about these tables."
        add_message("user", _message)

    if st.sidebar.button("Most Race Wins"):
        _message = "Which driver has the most race wins?"
        add_message("user", _message)

    if st.sidebar.button("Most Constructors Championships"):
        _message = "Which team won the most Constructors Championships?"
        add_message("user", _message)

    if st.sidebar.button("Longest Racing Career"):
        _message = "Tell me the name of the driver with the longest racing career? Also tell me when they started and when they retired."
        add_message("user", _message)

    if st.sidebar.button("Races per year"):
        _message = "Show me the number of races per year."
        add_message("user", _message)

    if st.sidebar.button("Team position for driver with most wins"):
        _message = "Write a query to identify the drivers that won the most races per year from 2010 onwards and the position of their team that year."
        add_message("user", _message)

    if st.sidebar.button(":orange_heart: This is awesome!"):
        _message = "You're awesome!"
        add_message("user", _message)

    # Display existing chat messages
    for message in st.session_state["messages"]:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is from a user, generate a new response
    last_message = st.session_state["messages"][-1]
    if last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("agent"):
            with st.spinner("Working..."):
                response = sql_agent.run(question)
                response_content = response.content if hasattr(response, 'content') else str(response)
                st.markdown(response_content)
                add_message("agent", response_content)

    st.sidebar.markdown("---")

    if st.sidebar.button("New Run"):
        restart_agent()


def restart_agent():
    logger.debug("---*--- Restarting agent ---*---")
    st.session_state["sql_agent"] = None
    st.rerun()


main()
