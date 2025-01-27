import os
import tempfile
import streamlit as st
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from consts import SYSTEM_TEMPLATE, HUMAN_TEMPLATE
from handlers import PrintRetrievalHandler, StreamHandler, StaticFile
import os
import spacy
from retrievers import configure_retriever
from langchain.chains import RetrievalQA

nlp = spacy.load("en_core_web_sm")

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the 'docs' folder
pdf_directory = os.path.join(script_dir, 'docs')

# Check if the directory exists
if not os.path.exists(pdf_directory):
    print(f"Directory not found: {pdf_directory}")

messages = [
    SystemMessagePromptTemplate.from_template(SYSTEM_TEMPLATE),
    HumanMessagePromptTemplate.from_template(HUMAN_TEMPLATE)
]
qa_prompt = ChatPromptTemplate.from_messages(messages)

st.set_page_config(page_title="Ottobot", page_icon="🏆")

if st.button("Clear message history", key="clear_button"):
    st.session_state.clear_messages = True
st.title("💪 Train with Mark Ottobre")
st.caption("If you need any additional info please ask your trainer in the studio or send us an email at info@enterprisefitness.com.au")

if 'retriever' not in st.session_state:
    st.session_state.retriever = configure_retriever(st.session_state.static_files)

retriever = st.session_state.retriever

# Setup memory for contextual conversation
msgs = StreamlitChatMessageHistory()

memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=msgs, return_messages=True)

# Setup LLM and QA chain
llm = ChatOpenAI(
    model_name="gpt-4o", 
    openai_api_key=st.secrets["OPENAI_API_KEY"], 
    temperature=0.5, 
    streaming=True
)

qa_chain = RetrievalQA.from_chain_type(
    llm, 
    retriever=retriever, 
    verbose=True,
    chain_type="stuff",
    chain_type_kwargs={
        "prompt": qa_prompt,
        "memory": memory
    }
)

if len(msgs.messages) == 0 or st.session_state.get('clear_messages', False):
    msgs.clear()
    msgs.add_ai_message("""To provide a tailored performance plan, I need to gather some essential information. Could you please provide the following details:

\n\n- Age or date of birth.
\n- Weight.
\n- Height.
\n- Body fat percentage.
\n- What is his activity level? (e.g., training frequency per week, steps, etc.)
\n- How many meals per day does he want to eat?
\n- How many of those meals will be shakes? (You mentioned excluding shakes as meals, so please confirm if there will be any shakes at all.)
\n\nOnce I have this information, I can proceed with creating the plan.
""")
    st.session_state.clear_messages = False

avatars = {"human": "user", "ai": "assistant"}
for msg in msgs.messages:
    st.chat_message(avatars[msg.type]).write(msg.content)

if user_query := st.chat_input(placeholder="Ask me anything!"):
    st.chat_message("user").write(user_query)

    doc = nlp(user_query)
    processed_query = ' '.join([token.text for token in doc if token.ent_type_ != 'PERSON'])

    with st.chat_message("assistant"):
        retrieval_handler = PrintRetrievalHandler(st.container())
        stream_handler = StreamHandler(st.empty())
        
        # Use the correct input format for RetrievalQA
        response = qa_chain({"query": processed_query}, callbacks=[retrieval_handler, stream_handler])
        
        # Extract the answer from the response
        answer = response['result']
        msgs.add_ai_message(answer)
