import streamlit as st
import firebase_admin

from firebase_admin import credentials
from firebase_admin import auth
from firebase_admin import firestore
from streamlit_modal import Modal

def initialize_firebase_app():
    try:
        firebase_admin.get_app()
    except ValueError:
        secrets = st.secrets["firebase-auth"]

        cred = credentials.Certificate({
            "type": secrets["type"],
            "project_id": secrets["project_id"],
            "private_key_id": secrets["private_key_id"],
            "private_key": secrets["private_key"],
            "client_email": secrets["client_email"],
            "client_id": secrets["client_id"],
            "auth_uri": secrets["auth_uri"],
            "token_uri": secrets["token_uri"],
            "auth_provider_x509_cert_url": secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": secrets["client_x509_cert_url"]
        })

        # Initialize the Firebase app with the created credential
        firebase_admin.initialize_app(cred,
                                      {
                                          'storageBucket': 'gs://elmeto-12de0.appspot.com'
                                      }
                                      )

# Call the function to initialize the app
initialize_firebase_app()

st.title(':blue[Elmento AI] приветствует вас!!')

if 'username' not in st.session_state:
    st.session_state.username = ''

if 'useremail' not in st.session_state:
    st.session_state.useremail = ''

def f():
    try:
        user = auth.get_user_by_email(email)
        print(user.uid)

        st.success('Вход выполнен успешно!')

        st.session_state.username = user.uid
        st.session_state.useremail = user.email

        st.session_state.signout = True
        st.session_state.signedout = True
        st.session_state['logged_in'] = True
    except:
        st.warning('Ошибка входа')

# sign out function
# def t():
#     st.session_state.signout = False
#     st.session_state.signedout = False
#     st.session_state.username = ''

if 'signedout' not in st.session_state:
    st.session_state.signedout = False
if 'signout' not in st.session_state:
    st.session_state.signout = False

if not st.session_state['signedout']:
    db = firestore.client()
    st.session_state.db = db
#     docs = db.collection('users').get()

    choice = st.selectbox('Регистрация/Вход', ['Регистрация', 'Вход'])

    if choice == 'Вход':
        email = st.text_input('Адрес электронной почты')
        password = st.text_input('Пароль', type='password')
        st.write('Пожалуйста, убедитесь, что ваш пароль длиннее 6-ти символов.')
        st.button('Вход', on_click=f)

    else:
        email = st.text_input('Адрес электронной почты')
        password = st.text_input('Пароль', type='password')
        st.write('Пожалуйста, убедитесь, что ваш пароль длиннее 6-ти символов.')

        username = st.text_input('Введите ваше уникальное имя пользователя.')

        # Display the confirmation message and tick button
        if 'show_create_account' not in st.session_state:
            col1, col2 = st.columns([1, 8])
            with col1:
                if st.button('✅'):
                    st.session_state['show_create_account'] = True
            with col2:
                st.write("Пожалуйста, согласитесь с нашими политиками здесь: [Публичная Оферта](https://docs.google.com/document/d/1bxzRyWSG01d1KmWK_GPoNk0LACZp-oZ_/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true) , [Соглашение С Подпиской](https://docs.google.com/document/d/1fOx1Q0w35NZ5iNM4f-Cf7nMIAA-wnS3t/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true) , [Согласие ПнД](https://docs.google.com/document/d/1xR3ZNVAnkM5rn96EHQRdWToPRfhdynrq/edit?usp=sharing&ouid=117474650340329532887&rtpof=true&sd=true)")

        # Display the 'Создать мой аккаунт' button if tick button was clicked
        if 'show_create_account' in st.session_state and st.session_state['show_create_account']:
            if st.button('Создать мой аккаунт'):
                user = auth.create_user(email=email, password=password)
                doc_ref = db.collection('users').document(user.uid)
                doc_ref.set({
                    'uid': user.uid,
                    'email': email,
                    'username': username,
                    'timestamp': firestore.SERVER_TIMESTAMP
                })

                st.success('Аккаунт успешно создан!')
                st.markdown('Пожалуйста, войдите в систему, используя вашу электронную почту и пароль.')
                st.balloons()

if 'logged_in' in st.session_state and st.session_state.logged_in:
    st.write(st.session_state.useremail)

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

