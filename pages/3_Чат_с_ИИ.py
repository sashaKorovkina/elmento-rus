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
from openai import BadRequestError

db = firestore.client()

# FUNCTIONS
def response_func(prompt, text):
    try:
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
        llm = OpenAI(model_name="gpt-3.5-turbo-instruct", openai_api_key=api_key, max_tokens=1200)
        #OpenAI(temperature=1, max_tokens=1000)

        chain = load_qa_chain(llm, chain_type="stuff")
        with get_openai_callback() as cb:
            result = chain.run(input_documents=docs, question=prompt)
        return result
    except BadRequestError as e:
        st.error("Ух ты, это огромный файл! Мы не можем его обработать прямо сейчас, но обязательно свяжемся с нашими разработчиками для улучшения системы!")


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
                        selected_question_type = f'''Write an essay in Russian following this format and keep it under 1000 tokens: 
                        Титульная страница:
                       - Заголовок статьи (ГОСТ 7.1-2003):
                         - Должен точно отражать тему исследования.
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

                    if selected_question_type == "Структура курсовой работы по ГОСТ":
                        selected_question_type = f'''Write an essay in Russian following this format and keep it under 1000 tokens: 
                        1. Титульный лист:
                           - Оформляется в соответствии с требованиями учебного заведения.
                           - Включает:
                             - Название учебного заведения.
                             - Факультет и кафедру.
                             - Название курсовой работы.
                             - Данные об авторе: ФИО, курс, группа.
                             - Данные о руководителе: должность, ФИО.
                             - Город и год выполнения.
                        
                        2. Задание на курсовую работу:
                           - Форма задания предоставляется кафедрой.
                           - Включает:
                             - Тему работы.
                             - Перечень вопросов, подлежащих изучению.
                             - Требования к оформлению работы.
                             - График выполнения.
                        
                        3. Реферат/аннотация (ГОСТ 7.9-95):
                           - Краткая характеристика содержания курсовой работы.
                           - Объем: 150-250 слов.
                           - Включает:
                             - Предмет исследования.
                             - Цель и задачи работы.
                             - Методы исследования.
                             - Основные результаты и выводы.
                             - Практическая значимость.
                        
                        4. Содержание (ГОСТ 7.32-2017):
                           - Перечень всех разделов, подразделов и приложений с указанием номеров страниц.
                           - Оформляется с нумерацией разделов и подразделов.
                        
                        5. Введение:
                           - Обоснование актуальности темы исследования.
                           - Формулировка цели и задач работы.
                           - Обзор литературы по теме.
                           - Объект и предмет исследования.
                           - Новизна исследования.
                           - Методы исследования.
                           - Структура работы.
                        
                        6. Основная часть:
                           - Делится на главы и разделы.
                           - Каждая глава должна завершаться краткими выводами.
                           - Пример структуры основной части:
                             - Глава 1: Теоретические аспекты исследования.
                               - 1.1. История проблемы.
                               - 1.2. Классификация основных понятий.
                             - Глава 2: Анализ предметной области.
                               - 2.1. Описание объекта исследования.
                               - 2.2. Методы и результаты анализа.
                             - Глава 3: Разработка и внедрение предложений.
                               - 3.1. Описание предложенных решений.
                               - 3.2. Оценка эффективности внедрения.
                        
                        7. Заключение:
                           - Краткое изложение результатов исследования.
                           - Выводы по каждой задаче работы.
                           - Практическая значимость результатов.
                           - Рекомендации и перспективы дальнейшего исследования.
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

                    if selected_question_type == "Структура дипломной работы по ГОСТ":
                        selected_question_type = f'''Write an essay in Russian based on the content of the file following the format below and keep it under 1000 tokens: 
                        1. Титульный лист:
                           - Оформляется по требованиям вуза.
                           - Включает:
                             - Название учебного заведения.
                             - Факультет и кафедру.
                             - Вид работы: дипломная работа.
                             - Тему дипломной работы.
                             - Данные автора: ФИО, курс, группа.
                             - Данные руководителя: должность, ФИО.
                             - Данные рецензента: должность, ФИО.
                             - Город и год выполнения.
                        
                        2. Задание на дипломную работу:
                           - Форма задания предоставляется кафедрой.
                           - Включает:
                             - Тему работы.
                             - Содержание и структуру работы.
                             - Перечень задач, подлежащих изучению.
                             - Требования к оформлению работы.
                             - График выполнения.
                        
                        3. Аннотация (ГОСТ 7.9-95):
                           - Краткое изложение содержания дипломной работы.
                           - Объем: 150-250 слов.
                           - Включает:
                             - Предмет исследования.
                             - Цель и задачи работы.
                             - Методы исследования.
                             - Основные результаты и выводы.
                             - Практическая значимость.
                        
                        4. Содержание (ГОСТ 7.32-2017):
                           - Перечень всех разделов, подразделов и приложений с указанием номеров страниц.
                           - Оформляется с нумерацией разделов и подразделов.
                        
                        5. Введение:
                           - Обоснование актуальности темы исследования.
                           - Формулировка цели и задач работы.
                           - Обзор литературы по теме.
                           - Объект и предмет исследования.
                           - Новизна исследования.
                           - Методы исследования.
                           - Структура работы.
                        
                        6. Основная часть:
                           - Основная часть делится на главы и разделы.
                           - Каждая глава должна завершаться краткими выводами.
                           - Пример структуры основной части:
                             - Глава 1: Теоретические аспекты исследования
                               - 1.1 История проблемы.
                               - 1.2 Классификация основных понятий.
                               - 1.3 Анализ литературы по теме.
                             - Глава 2: Анализ предметной области
                               - 2.1 Описание объекта исследования.
                               - 2.2 Методы анализа предметной области.
                               - 2.3 Результаты анализа.
                             - Глава 3: Разработка и внедрение предложений
                               - 3.1 Описание предложенных решений.
                               - 3.2 Оценка эффективности внедрения.
                               - 3.3 Экономическая оценка.
                        
                        7. Заключение:
                           - Краткое изложение результатов исследования.
                           - Выводы по каждой задаче работы.
                           - Практическая значимость результатов.
                           - Рекомендации и перспективы дальнейшего исследования.
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
                        prompt_final = f' Respond based on the provided data from the initial prompt, maintaining the same language as the original text. Ensure the output is grammatically correct. If the text''s language is unrecognized, provide the response in Russian: {prompt}'
                        response = response_func(prompt_final, selected_chat_data['pdf_text'])
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

st.markdown("""
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 20px 0;
        }
        .footer a {
            margin: 0 10px;
            color: #000;
            text-decoration: none;
        }
        .footer a:hover {
            text-decoration: underline;
        }
        .spacer {
            height: 300px; /* Adjust this height to create the desired space */
        }
    </style>
    <div class="footer">
        <a href="https://docs.google.com/document/d/1bxzRyWSG01d1KmWK_GPoNk0LACZp-oZ_/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true">Публичная Оферта</a> | 
        <a href="https://docs.google.com/document/d/1fOx1Q0w35NZ5iNM4f-Cf7nMIAA-wnS3t/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true">Соглашение с Подпиской</a> | 
        <a href="https://docs.google.com/document/d/1xR3ZNVAnkM5rn96EHQRdWToPRfhdynrq/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true">Согласие ПнД</a>
    </div>
""", unsafe_allow_html=True)


