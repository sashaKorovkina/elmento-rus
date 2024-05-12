from openai import OpenAI
import streamlit as st



# Display FAQs
st.title("Часто задаваемые вопросы (FAQ):")

st.markdown("""
1. **Как пользоваться нейросетью?**
   1) Зайдите в раздел “Мой профиль” и создайте там учетную запись. Войдите в нее.
   2) Для того чтобы нейросеть работала, вам необходимо внести API ключ, которЫЙ находится на видном месте каждой страницы.
   3) Вы можете загрузить документы в разделе "Файлы".
   4) В разделе “Файлы”, вы можете выбрать документ для обработки. Вы можете нажать на кнопку “Получить сводку”, чтобы получить краткое содержание документа или “Общение с ИИ”, чтобы самостоятельно задать вопрос по файлу.

2. **Когда проект выйдет полностью?**
   Сейчас Elemento AI находится в стадии разработки и тестирования. Мы полагаем, что сможем закончить основную часть работ в течение нескольких месяцев.

3. **Какие предусмотрены тарифы?**
   На данный момент никаких тарифов не предусмотрено. В первый месяц нейросеть доступна бесплатно.

4. **Я нашел баг/ошибку. Куда обращаться?**
    ...к нашему сотруднику @andreyelmento в Телеграм.
""")

# if "messages" not in st.session_state:
#     st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
#
# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])
#
# if prompt := st.chat_input():
#     if not openai_api_key:
#         st.info("Please add your OpenAI API key to continue.")
#         st.stop()
#
#     client = OpenAI(api_key=openai_api_key)
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     st.chat_message("user").write(prompt)
#     response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
#     msg = response.choices[0].message.content
#     st.session_state.messages.append({"role": "assistant", "content": msg})
#     st.chat_message("assistant").write(msg)
