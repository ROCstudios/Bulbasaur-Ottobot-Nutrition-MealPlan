import streamlit as st
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.chains import ConversationalRetrievalChain
from consts import SYSTEM_TEMPLATE, HUMAN_TEMPLATE, REPHRASE_PROMPT
from handlers import PrintRetrievalHandler, StreamHandler
from retrievers import configure_retriever, get_static_files
from langchain.chains import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain

st.set_page_config(page_title="Ottobot", page_icon="🏆")
if st.button("Clear message history", key="clear_button"):
    st.session_state.clear_messages = True
st.title("💪 Train with Mark Ottobre")
st.caption(
    "If you need any additional info please ask your trainer in the studio or send us an email at info@enterprisefitness.com.au"
)

# Setup memory for contextual conversation
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=msgs,
    return_messages=True,
    output_key="answer",
)

# Initialize static_files in session state if not already present
if "static_files" not in st.session_state:
    st.session_state.static_files = get_static_files()

if "retriever" not in st.session_state:
    st.session_state.retriever = configure_retriever(st.session_state.static_files)

retriever = st.session_state.retriever

# Setup LLM and QA chain
llm = ChatOpenAI(
    model_name="gpt-4o",
    openai_api_key=st.secrets["OPENAI_API_KEY"],
    temperature=0.0,
    streaming=True,
)

combine_docs_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_TEMPLATE),
        ("human", HUMAN_TEMPLATE),
    ]
)

combine_docs_chain_llm = LLMChain(llm=llm, prompt=combine_docs_prompt)

combine_docs_chain = StuffDocumentsChain(
    llm_chain=combine_docs_chain_llm,
    document_variable_name="context",
    document_prompt=PromptTemplate(
        input_variables=["page_content"], template="{page_content}"
    ),
)

rephrase_prompt = PromptTemplate.from_template(REPHRASE_PROMPT)

question_generator = LLMChain(llm=llm, prompt=rephrase_prompt)

qa_chain = ConversationalRetrievalChain(
    retriever=st.session_state.retriever,
    combine_docs_chain=combine_docs_chain,
    question_generator=question_generator,
    memory=memory,
    return_source_documents=True,
    verbose=True,
)

if len(msgs.messages) == 0 or st.session_state.get("clear_messages", False):
    msgs.clear()
    msgs.add_ai_message(
        """To provide a tailored performance plan, I need to gather some essential information. Could you please provide the following details:

\n\n- Age or date of birth.
\n- Weight.
\n- Height.
\n- Body fat percentage.
\n- What is his activity level? (e.g., training frequency per week, steps, etc.)
\n- How many meals per day does he want to eat?
\n- How many of those meals will be shakes? (You mentioned excluding shakes as meals, so please confirm if there will be any shakes at all.)
\n\nOnce I have this information, I can proceed with creating the plan.
"""
    )
    st.session_state.clear_messages = False

avatars = {"human": "user", "ai": "assistant"}
for msg in msgs.messages:
    st.chat_message(avatars[msg.type]).write(msg.content)

if user_query := st.chat_input(placeholder="Ask me anything!"):
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        retrieval_handler = PrintRetrievalHandler(st.container())
        stream_handler = StreamHandler(st.empty())

        response = qa_chain(
            {"question": user_query}, callbacks=[retrieval_handler, stream_handler]
        )

        msgs.add_ai_message(response["answer"])
