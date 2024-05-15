import streamlit as st
from firebase_admin import firestore, storage
import streamlit as st
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
import datetime
from langchain.prompts import PromptTemplate

db = firestore.client()

# FUNCTIONS
def response_func(prompt, text):
    text = str(text)
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=4000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    embeddings = OpenAIEmbeddings(openai_api_key = api_key)
    knowledge_base = FAISS.from_texts(chunks, embeddings)
    docs = knowledge_base.similarity_search(prompt)
    llm = OpenAI(openai_api_key=api_key, max_tokens=1000)
    #OpenAI(temperature=1, max_tokens=1000)

    chain = load_qa_chain(llm, chain_type="stuff")
    with get_openai_callback() as cb:
        result = chain.run(input_documents=docs, question=prompt)
    return result


def display_messages(chat_id, username):
    # Fetch messages from Firestore
    messages = db.collection('users').document(username).collection('chats').document(chat_id).collection(
        'messages').order_by("timestamp").stream()

    # Display messages using Streamlit's chat message format
    for message in messages:
        if 'message_user' in message.to_dict() and message.get('message_user'):
            with st.chat_message("user"):
                st.markdown(message.get('message_user'))

        if 'message_ai' in message.to_dict() and message.get('message_ai'):
            with st.chat_message("assistant"):
                st.markdown(message.get('message_ai'))

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Чат с Elmento")

# MAIN SCRIPT
if 'logged_in' in st.session_state and st.session_state.logged_in:
    secrets = st.secrets['openai-api-key']
    api_key = secrets["OPEN_AI_KEY"]
    if 'username' in st.session_state:
        username = st.session_state['username']
        # st.write(f"Logged in as: {username}")

        chats_ref = db.collection('users').document(username).collection('chats')
        chats = chats_ref.get()
        chats_all = [chat.to_dict() for chat in chats]
        chat_names = [chat['filename'] for chat in chats_all if 'filename' in chat]
        if chat_names:
            #st.sidebar.write("Выберите чат:")
            #st.sidebar.button
            #selected_chat_name = st.sidebar.selectbox("Выберите чат:", chat_names)
            # Custom CSS to style the expander as buttons
            with st.sidebar.expander("Выберите чат:", expanded=True):
                for chat_name in chat_names:
                    if st.button(chat_name, use_container_width=True):
                        st.session_state.selected_chat_name = chat_name

            if 'selected_chat_name' not in st.session_state:
                st.session_state.selected_chat_name = None

            if st.session_state.selected_chat_name:
                selected_chat_name = st.session_state.selected_chat_name
                selected_chat_data = next((chat for chat in chats_all if chat['filename'] == selected_chat_name), None)

                if selected_chat_data:
                    st.write(f"Начало чат-сессии для: {selected_chat_data['filename']}")
                    # st.write(f"The id in the selected file is: {selected_chat_data['chat_id']}")
                    display_messages(selected_chat_data['chat_id'], username)

                    with st.sidebar.expander("Выберите тип вопроса:", expanded=True):
                        question_types = [
                            "Структура научной статьи по ГОСТ",
                            "Структура курсовой работы по ГОСТ",
                            "Структура дипломной работы по ГОСТ"
                        ]
                        selected_question_type = None
                        for question_type in question_types:
                            if st.sidebar.button(question_type, use_container_width=True):
                                selected_question_type = question_type

                    # Further processing based on the selected question type
                    if selected_question_type == "Структура научной статьи по ГОСТ":
                        selected_question_type = f'''Write an essay in Russian following this format: Титульная страница:
                       - Заголовок статьи (ГОСТ 7.1-2003):
                         - Должен точно отражать тему исследования.
                         - Прописные буквы не использовать, кроме первой буквы и имен собственных.
                       - ФИО авторов:
                         - Указывать полностью.
                       - Место работы и должность каждого автора.
                       - Контактная информация авторов (адрес электронной почты).
                    
                    2. Аннотация (ГОСТ 7.9-95):
                       - Объем: 150-250 слов.
                       - Должна давать полное представление о содержании статьи.
                       - Включать следующие аспекты:
                         - Область применения или предмет исследования.
                         - Цель исследования.
                         - Методы исследования.
                         - Основные результаты.
                         - Выводы и практическая значимость.
                    
                    3. Ключевые слова (ГОСТ 7.9-95):
                       - Объем: от 5 до 10 словосочетаний.
                       - Отражают основное содержание статьи.
                       - Разделяются точкой с запятой.
                    
                    4. Введение:
                       - Постановка проблемы, обзор литературы, и актуальность темы.
                       - Цели и задачи исследования.
                       - Новизна и практическая значимость исследования.
                    
                    5. Материалы и методы (ГОСТ 7.32-2017):
                       - Подробное описание материалов и методов, используемых в исследовании.
                       - Структурированность и логическая последовательность изложения.
                    
                    6. Результаты и обсуждение:
                       - Описание основных результатов.
                       - Сравнение с предыдущими исследованиями.
                       - Интерпретация результатов в контексте поставленных задач.
                    
                    7. Заключение:
                       - Краткое подведение итогов исследования.
                       - Практическая значимость результатов.
                       - Перспективы дальнейшего исследования.
                    
                    8. Список литературы (ГОСТ 7.1-2003, ГОСТ 7.0.5-2008):
                       - Объем: минимум 10 источников.
                       - Оформление в соответствии с ГОСТ 7.0.5-2008:
                         - Книги: фамилия и инициалы авторов, заглавие, издательство, год издания, количество страниц.
                         - Статьи: фамилия и инициалы авторов, заглавие, название журнала, год, номер, страницы.
                         - Электронные ресурсы: фамилия и инициалы авторов, заглавие, доступность, URL, дата обращения.
                    
                    Требования к оформлению научной статьи по ГОСТ:
                    
                    1. Объем текста:
                       - 8-12 страниц основного текста (без титульной страницы, аннотации, списка литературы).
                    
                    5. Таблицы и рисунки:
                       - Таблицы нумеруются последовательно.
                       - Заголовки таблиц располагаются над таблицей и выравниваются по левому краю.
                       - Рисунки нумеруются и имеют подписи под рисунком по центру.
                       - Ссылки на таблицы и рисунки даются в тексте статьи.
                    
                    6. Ссылки в тексте:
                       - Оформляются по правилам ГОСТ 7.0.5-2008.
                       - Ссылки на источники указываются в квадратных скобках с порядковым номером источника по списку литературы.
                    '''
                        # st.write(f"Вы выбрали тип вопроса: {selected_question_type}")
                        chat_id = selected_chat_data['chat_id']
                        with st.chat_message("user"):
                            st.markdown(selected_question_type)
                        # st.session_state.messages.append({"role": "user", "content": prompt})
                        response = response_func(selected_question_type, selected_chat_data['pdf_text'])
                        with st.chat_message("assistant"):
                            st.markdown(response)
                        doc_ref = db.collection('users').document(username).collection('chats').document(
                            chat_id).collection(
                            'messages').document()
                        doc_ref.set({
                            'message_user': selected_question_type,
                            'message_ai': response,
                            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
                        })

                    if prompt := st.chat_input("Что вас интересует?"):
                        chat_id = selected_chat_data['chat_id']
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        # st.session_state.messages.append({"role": "user", "content": prompt})
                        prompt = f'Always reply in the same language as the question was asked in. {prompt}'
                        response = response_func(prompt, selected_chat_data['pdf_text'])
                        with st.chat_message("assistant"):
                            st.markdown(response)
                        doc_ref = db.collection('users').document(username).collection('chats').document(
                            chat_id).collection(
                            'messages').document()
                        doc_ref.set({
                            'message_user': prompt,
                            'message_ai': response,
                            'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
                        })
else:
    st.write('Пожалуйста, войдите в систему или зарегистрируйтесь, чтобы просмотреть эту страницу.')

