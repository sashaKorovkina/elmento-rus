from tika import parser
import time

def extract_text_by_page(pdf_path):
    start_time = time.time()
    parsed = parser.from_file(pdf_path)
    pages = parsed['content'].split('\n\n\n')  # Split by page

    for page_number, page_text in enumerate(pages):
        print(f"Page {page_number + 1}:\n{page_text.strip()}\n")

    end_time = time.time()  # End the timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print("Elapsed Time:", elapsed_time, "seconds")

pdf_path = r'C:\Users\sasha\Desktop\Elmento-Materials\war-and-peace.pdf'
extract_text_by_page(pdf_path)
