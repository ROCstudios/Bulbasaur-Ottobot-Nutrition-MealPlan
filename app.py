import streamlit as st
from ottobot import get_ottobot_with_vectore_store, load_thread_assign_to_assistant

thread_id = None

def main():
    st.title("Continuous Chat with History")

    # Initialize simplest ottobot
    ottobot = get_ottobot_with_vectore_store("ottobotV2", [
        "docs/CALCULATOR A.M. Nutrition & Lifestyle Protocol Data Sources.pdf",
        "docs/MACROS A.M. Nutrition & Lifestyle Protocol Data Sources.pdf",
        "docs/MACROS Mark Ottobre Master File Data Sources.pdf",
        "docs/Mark Ottobre Master File Data Sources.pdf",
        "docs/Mark Ottobre Master File.pdf",
        "docs/MEAL PLANS A.M. Nutrition & Lifestyle Protocol Data Sources.pdf",
        "docs/OVERVIEW A.M. Nutrition & Lifestyle Protocol Data Sources.pdf",
        "docs/PROGRAM Mark Ottobre Master File Data Sources.pdf",
        "docs/SYSTEM Mark Ottobre Master File Data Sources.pdf",
        "docs/TIMELINE A.M. Nutrition & Lifestyle Protocol Data Sources.pdf",
        "docs/TIMELINE Mark Ottobre Master File Data Sources.pdf",
        "docs/The Enterprise Diet.pdf",
        "docs/ENTERPRISE FITNESS - USER MANUAL.pdf",
    ])

    # Chat UI
    st.subheader("Chat with Your Knowledge Base")
    user_question = st.text_input("Ask a question:", "")

    st.sidebar.header("Manage Threads")
    st.sidebar.caption("Create a new thread or load an existing thread")
    # Sidebar for Thread ID
    with st.sidebar:
        thread_id = st.text_input("Thread ID:", key="thread_id")
        if st.button("Load Thread"):
            thread_id = load_thread_assign_to_assistant(thread_id, ottobot.id)

    if st.button("Send"):
        if user_question.strip():
            with st.spinner("Generating response..."):
                response = ottobot.run(user_question)
                st.session_state["chat_history"].append((user_question, response))

    # Display chat history
    st.subheader("Conversation History")

    # Move the CSS to a separate component using st.markdown
    st.markdown("""
        <style>
        .chat-container {
            display: flex;
            flex-direction: column;
            margin-top: 10px;
        }
        .chat-bubble {
            max-width: 75%;
            padding: 10px 15px;
            margin: 5px 0;
            border-radius: 15px;
            font-size: 16px;
            line-height: 1.5;
        }
        .user-bubble {
            background-color: #DCF8C6;
            align-self: flex-end;
            border: 1px solid #B9E9A8;
        }
        .ai-bubble {
            background-color: #ECECEC;
            align-self: flex-start;
            border: 1px solid #D4D4D4;
        }
        </style>
    """, unsafe_allow_html=True)

    # Display each message separately
    # if st.session_state["chat_history"]:
    #     for question, answer in st.session_state["chat_history"]:
    #         st.markdown(f'<div class="chat-bubble user-bubble" style="text-align: right">{question}</div>', unsafe_allow_html=True)
    #         st.markdown(f'<div class="chat-bubble ai-bubble">{answer}</div>', unsafe_allow_html=True)
    # else:
    #     st.info("Start a conversation by asking a question.")

if __name__ == "__main__":
    main()
