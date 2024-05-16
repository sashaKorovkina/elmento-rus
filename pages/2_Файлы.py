import streamlit as st
import requests
from PIL import Image
import io
import pytesseract
from streamlit.components.v1 import html
from firebase_admin import firestore, storage
import fitz
import contextlib
from math import ceil
import os
import base64
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from subprocess import PIPE, run

# CHANGE FOR CLOUD DEPLOY!!!!

pytesseract.pytesseract.tesseract_cmd = None
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\sasha\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# search for tesseract binary in path
@st.cache_resource
def find_tesseract_binary() -> str:
    return shutil.which("tesseract")

# INITIALISE VARIABLES #################################################################################################

st.set_page_config(layout="wide")

# pytesseract
pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
if not pytesseract.pytesseract.tesseract_cmd:
    st.error("Tesseract binary not found in PATH. Please install Tesseract.")

# firestore database
db = firestore.client()
bucket = storage.bucket('elmento-ru.appspot.com')

# logged in parameter
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


# INITIALISE FUNCTIONS #################################################################################################

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def save_uploaded_file(uploaded_file, target_path):
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

def send_image_to_openai(image_bytes, api_key, key):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    payload = {
              "model": "gpt-4-vision-preview",
              "messages": [
                {
                  "role": "user",
                  "content": [
                    {
                      "type": "text",
                      "text": "What’s in this image? Explain the image content"
                    },
                    {
                      "type": "image_url",
                      "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}"
                      }
                    }
                  ]
                }
              ],
              "max_tokens": 1000
            }
    if st.button("Get Explanation", key = key, use_container_width=True):
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            print(response.json())
            st.success("Explanation: {}".format(response.json()['choices'][0]['message']['content']))
        except Exception as e:
            st.error(f"Error: {e}")

def send_text_to_openai(text_content, file_id):
    headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {api_key}"
    }

    payload = {
              "model": f"gpt-3.5-turbo-0125",
              "messages": [
                {
                    "role": "user",
                    "content": f"Having the output only in grammatically correct Russian language, summarise this text for me: ... {text_content}"
                }
              ],
              "max_tokens": 1000
            }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        explanation = response.json()['choices'][0]['message']['content']
        st.success(f"Explanation: {explanation}")
        doc_ref = db.collection('users').document(username).collection('documents').document(file_id)
        doc_ref.update({
            'summary': explanation
        })
    except Exception as e:
        st.error(f"Error: {e}")

def chat_to_ai(file_name):
    # Functionality to chat about the specific PDF
    st.write(f"Chatting about {file_name}...")

def get_summary(pdf_bytes, file_name, language, file_id):
    st.write(f"Getting summary for {file_id}...")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_images = []
    pdf_texts = []  # List to store text from all pages

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_data = pix.tobytes()
        pdf_image = Image.open(io.BytesIO(image_data))
        pdf_images.append(pdf_image)

        if language == 'Русский':
            lang = 'rus'
        elif language == 'Английский':
            lang = 'eng'

        text = pytesseract.image_to_string(pdf_image, lang= lang)
        # lang = detect(text)
        # st.write(lang)
        pdf_texts.append(text)

    send_text_to_openai(pdf_texts, file_id)


def nav_page(page_name, name_page, timeout_secs=3):
    page_name_lower = page_name.lower()
    nav_script = f"""
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {{
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {{
                    var href = decodeURIComponent(links[i].href);
                    if (href.toLowerCase().endsWith("/" + page_name)) {{
                        links[i].click();
                        return;
                    }}
                }}
                var elapsed = new Date() - start_time;
                if (elapsed < timeout_secs * 1000) {{
                    setTimeout(function() {{
                        attempt_nav_page(page_name, start_time, timeout_secs);
                    }}, 100);
                }} else {{
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }}
            }}
            window.addEventListener("load", function() {{
                attempt_nav_page("{page_name_lower}", new Date(), {timeout_secs});
            }});
        </script>
    """
    st.session_state.selected_chat_name = name_page
    html(nav_script)



def get_existing_files():
    docs_ref = db.collection('users').document(username).collection('documents')
    docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    return files


def get_existing_file_names():
    names = []
    docs_ref = db.collection('users').document(username).collection('documents')
    docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    for file in files:
        filename = file['filename']
        names.append(filename)
    return names


def get_last_file():
    docs_ref = db.collection('users').document(username).collection('documents')
    query = docs_ref.order_by('uploaded_at', direction=firestore.Query.DESCENDING).limit(1)
    docs = query.stream()
    # docs = docs_ref.get()
    files = [doc.to_dict() for doc in docs]
    file = files[len(files)-1]
    return file


def check_file(file):
    response = requests.get(file['url'])
    response_url = file['url']
    response_filename = file['filename']
    if response.status_code == 200:
        st.markdown(f"[{response_filename}]({response_url})")
    else:
        st.write(f"Failed: {response.status_code} file name: {file['filename']}")


def create_thumbnail(image_stream, format):
    size = (128, 128)
    image = Image.open(image_stream)
    image.thumbnail(size)

    thumb_io = io.BytesIO()
    image.save(thumb_io, format, quality=95)
    thumb_io.seek(0)
    return thumb_io


def display_file_with_thumbnail(file):
    if file.get('thumbnail_url'):
        link = f"[![Thumbnail]({file['thumbnail_url']})]({file['url']})"
        st.markdown(link, unsafe_allow_html=True)
    else:
        st.markdown(f"[{file['filename']}]({file['url']})")


def parse_text():
    st.write('parsing...')


def pdf_page_to_image(pdf_stream):
    doc = fitz.open("pdf", pdf_stream)
    page = doc.load_page(0)

    pix = page.get_pixmap(matrix=fitz.Matrix(72 / 72, 72 / 72))

    img_bytes = io.BytesIO()
    img_bytes.write(pix.tobytes("png"))
    img_bytes.seek(0)

    doc.close()
    return img_bytes


def doc_page_to_image(pdf_stream):
    doc = fitz.open("pdf", pdf_stream)
    page = doc.load_page(0)

    pix = page.get_pixmap(matrix=fitz.Matrix(72 / 72, 72 / 72))

    img_bytes = io.BytesIO()
    img_bytes.write(pix.tobytes("png"))
    img_bytes.seek(0)

    doc.close()
    return img_bytes


def pdf_parse_content(pdf_bytes, language):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_images = []
    pdf_texts = []  # List to store text from all pages

    for page_index in range(len(doc)):
        page = doc[page_index]
        pix = page.get_pixmap()
        image_data = pix.tobytes()
        pdf_image = Image.open(io.BytesIO(image_data))
        pdf_images.append(pdf_image)

        if language == 'Русский':
            lang = 'rus'
        elif language == 'Английский':
            lang = 'eng'

        text = pytesseract.image_to_string(pdf_image, lang = lang)
        pdf_texts.append(text)

    st.session_state['username'] = username
    st.session_state['pdf_images'] = pdf_images
    st.session_state['pdf_texts'] = pdf_texts
    st.session_state['file_name'] = file['filename']
    st.session_state['chat_file_name'] = file['filename']
    st.session_state['doc_id'] = file['doc_id']

    chat_id = file['doc_id']

    #adding chat to db
    doc_ref = db.collection('users').document(username).collection('chats').document(chat_id)
    doc_ref.set({
        'filename': file['filename'],
        'pdf_text': pdf_texts,
        'chat_id' : chat_id,
        'file_id' : file['doc_id']
    })

    nav_page("Чат_с_ИИ", file['filename'])


def upload_file(uploaded_file, thumbnail_stream):
    blob = bucket.blob(f"{username}/{uuid.uuid4()}_{uploaded_file.name}")
    blob.upload_from_string(uploaded_file.getvalue(), content_type=uploaded_file.type)

    # Prepare the thumbnail
    if thumbnail_stream:
        thumb_blob = bucket.blob(f"{username}/{uuid.uuid4()}_thumb_{uploaded_file.name}")
        thumb_blob.upload_from_string(thumbnail_stream.getvalue(), content_type='image/png')

        thumb_url = thumb_blob.generate_signed_url(version="v4", expiration=timedelta(minutes=10000),
                                                   method='GET')
    else:
        thumb_url = None

    url = blob.generate_signed_url(version="v4", expiration=timedelta(minutes=10000), method='GET')

    doc_ref = db.collection('users').document(username).collection('documents').document()
    doc_ref.set({
        'filename': uploaded_file.name,
        'content_type': uploaded_file.type,
        'url': url,
        'blob': str(blob),
        'thumbnail_url': thumb_url,
        'uploaded_at': firestore.SERVER_TIMESTAMP,
        'doc_id': doc_ref.id,
        'summary': None
    })

    return doc_ref.get().to_dict()

def delete_file(username, file_id):
    st.write(f"Trying to delete...")
    try:
        # Document reference
        doc_ref = db.collection('users').document(username).collection('documents').document(file_id)
        # the file id here needs to be replaced by the chat_id
        chats_ref = db.collection('users').document(username).collection('chats').document(file_id)
        chats_ref.delete()
        doc_ref.delete()
        st.write('Deleted successfully')
    except Exception as e:
        st.write(f"An error occurred while trying to delete the file: {e}")

def display_file_with_thumbnail(file):
    if file.get('thumbnail_url'):
        st.image(file['thumbnail_url'], caption=file['filename'], width=200)
    else:
        st.markdown(f"[{file['filename']}]({file['url']})")

def store_file_in_tempdir(tmpdirname, uploaded_file):
    # Create a temporary file path
    tmpfile = os.path.join(tmpdirname, uploaded_file.name)
    with open(tmpfile, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return tmpfile

def convert_doc_to_pdf_native(doc_file, output_dir=".", timeout=60):
    """Converts a doc file to pdf using libreoffice without msoffice2pdf.
    Calls libreoffice (soffice) directly in headless mode.
    params: doc_file: Path to doc file
            output_dir: Path to output dir
            timeout: timeout for subprocess in seconds
    returns: (output, exception)
            output: Path to converted file
            exception: Exception if conversion failed
    """
    exception = None
    output = None
    try:
        process = run(['soffice', '--headless', '--convert-to',
            'pdf:writer_pdf_Export', '--outdir', os.path.abspath(output_dir), os.path.abspath(doc_file)],
            stdout=PIPE, stderr=PIPE,
            timeout=timeout, check=True)
        stdout = process.stdout.decode("utf-8")
        re_filename = re.search(r'-> (.*?) using filter', stdout)
        if re_filename:
            output = os.path.abspath(re_filename[1])
    except Exception as e:
        exception = e
    return (output, exception)

def upload_single_file(uploaded_file, tmpdirname):
    print('Uploading new file...')
    thumbnail_stream = None
    if uploaded_file.type.startswith('image/'):
        thumbnail_stream = create_thumbnail(uploaded_file, uploaded_file.type.split('/')[-1])
    elif uploaded_file.type.startswith('application/pdf'):
        thumbnail_stream = pdf_page_to_image(uploaded_file.getvalue())
    elif uploaded_file.type.startswith('application/vnd.openxmlformats-officedocument.wordprocessingml.document'):
        try:
            # Store the uploaded file in the temp directory
            tmpfile = store_file_in_tempdir(tmpdirname, uploaded_file)

            with st.spinner('Converting file...'):
                pdf_file, exception = convert_doc_to_pdf_native(doc_file=tmpfile, output_dir=tmpdirname)

            if exception is not None:
                st.exception('Exception occurred during conversion.')
                st.exception(exception)
                st.stop()

            elif pdf_file is None:
                st.error('Conversion failed. No PDF file was created.')
                st.stop()

            elif os.path.exists(pdf_file):
                st.success(f"Conversion successful: {os.path.basename(pdf_file)}")

                # Read the content of the PDF file into a BytesIO stream
                with open(pdf_file, "rb") as f:
                    pdf_bytes = f.read()
                pdf_stream = io.BytesIO(pdf_bytes)
                thumbnail_stream = pdf_page_to_image(pdf_stream)

        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

    upload_file(uploaded_file, thumbnail_stream)
    if thumbnail_stream is not None:
        with contextlib.closing(thumbnail_stream):
            pass

    # st.write(f'Current document is:')
    file = get_last_file()
    return file

def get_img_blob(file):
    blob_path = file['blob']
    parts = blob_path.split(',')
    blob_path = parts[1].strip()
    blob = bucket.blob(blob_path)
    image_bytes = blob.download_as_bytes()
    return image_bytes

def make_tempdir():
    if 'tempfiledir' not in st.session_state:
        tempfiledir = tempfile.gettempdir()
        unique_dir = os.path.join(tempfiledir, str(uuid.uuid4()))  # Make unique subdir
        os.makedirs(unique_dir, exist_ok=True)  # Make dir if not exists
        st.session_state['tempfiledir'] = unique_dir
    return st.session_state['tempfiledir']

# @st.cache_resource(ttl=60*60*24)
# def cleanup_tempdir() -> None:
#     '''Cleanup temp dir for all user sessions.
#     Filters the temp dir for uuid4 subdirs.
#     Deletes them if they exist and are older than 1 day.
#     '''
#     deleteTime = datetime.now() - timedelta(days=1)
#     # compile regex for uuid4
#     uuid4_regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
#     uuid4_regex = re.compile(uuid4_regex)
#     tempfiledir = Path(tempfile.gettempdir())
#     if tempfiledir.exists():
#         subdirs = [x for x in tempfiledir.iterdir() if x.is_dir()]
#         subdirs_match = [x for x in subdirs if uuid4_regex.match(x.name)]
#         for subdir in subdirs_match:
#             itemTime = datetime.fromtimestamp(subdir.stat().st_mtime)
#             if itemTime < deleteTime:
#                 shutil.rmtree(subdir)

st.title("Мои документы")

if st.session_state.logged_in:
    secrets = st.secrets['openai-api-key']
    api_key = secrets["OPEN_AI_KEY"]
    #cleanup_tempdir()  # cleanup temp dir from previous user sessions
    tmpdirname = make_tempdir()  # make temp dir for each user session

    #api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")
    username = st.session_state.username

    files = get_existing_files()
    existing_file_names = [file['filename'] for file in files]  # List of existing file names

    with st.form("my-form", clear_on_submit=True):
        uploaded_file = st.file_uploader("")
        submitted = st.form_submit_button("Добавить в галерею")

        if submitted and not uploaded_file:
            st.error("Пожалуйста, загрузите файл перед нажатием кнопки 'Загрузите ваши файлы'")
        elif uploaded_file and uploaded_file.name not in existing_file_names:
            file = upload_single_file(uploaded_file, tmpdirname)
            uploaded_file = None  # Clear the uploaded file after handling
            st.experimental_rerun()


    controls = st.columns(2)
    with controls[0]:
        batch_size = st.select_slider("Кол-во документов на странице:", range(10, 110, 10))
    row_size = 3
    num_batches = ceil(len(files) / batch_size)
    with controls[1]:
        page = st.selectbox("Страница", range(1, num_batches + 1))

    # Sort the entire list of files based on the 'timestamp' key
    files.sort(key=lambda x: x['uploaded_at'], reverse=True)
    # Now slice the sorted list for the current page
    batch = files[(page - 1) * batch_size: page * batch_size]

    grid = st.columns(row_size)
    col = 0

    max_heights = [0] * row_size


    for file in batch:
        with grid[col]:
            with st.container(height = 900):
                if st.button("🗑️", key=f"delete_{file['url']}", type="secondary"):
                    delete_file(username, file['doc_id'])  # Function to delete the file
                # Row for the image
                image_row = st.empty()

                # Display the image in the image row
                image_row.image(file['thumbnail_url'], caption=file['filename'])
                # Create an empty slot
                uploaded_at_slot = st.empty()

                # Fill the slot with markdown representation of the text
                uploaded_at_slot.markdown(file['uploaded_at'])
                uploaded_at_slot.markdown(f"<span style='background-color: transparent;'>{file['uploaded_at']}</span>",
                                          unsafe_allow_html=True)


                # Place buttons in the button row
                file_extension = file['filename'].split(".")[-1].lower()

                if file_extension in ["jpg", "jpeg", "png"]:
                    image_bytes = get_img_blob(file)
                    send_image_to_openai(image_bytes, api_key, key=f"chat_{file['url']}")

                elif file_extension == "pdf":
                    pdf_bytes = get_img_blob(file)
                    language = st.selectbox(
                        "Выберите язык разговора:",
                        ["Английский", "Русский"],
                        key=f"supfile_{file['url']}"
                    )
                    if st.button("Общение с ИИ", key=f"chat_{file['url']}", use_container_width=True):
                        pdf_parse_content(pdf_bytes, language)
                    if st.button("Получить сводку", key=f"chat_summary_{file['url']}", use_container_width=True):
                        get_summary(pdf_bytes, file['filename'], language, file['doc_id'])

                elif file_extension == "docx":
                    pdf_bytes = get_img_blob(file)
                    language = st.selectbox(
                        "Выберите язык разговора:",
                        ["Английский", "Русский"],
                        key=f"supfile_{file['url']}"
                    )
                    if st.button("Общение с ИИ", key=f"chat_{file['url']}", use_container_width=True):
                        pdf_parse_content(pdf_bytes, language)
                    if st.button("Получить сводку", key=f"chat_summary_{file['url']}", use_container_width=True):
                        get_summary(pdf_bytes, file['filename'], language, file['doc_id'])

                summary = file['summary']
                if summary:
                    st.write(summary)
                else:
                    st.write("")

        col = (col + 1) % row_size

else:
    st.write('Пожалуйста, войдите в систему или зарегистрируйтесь, чтобы просмотреть эту страницу.')