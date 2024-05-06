from tika import parser
import time
from nltk.corpus import treebank_chunk
from nltk.chunk import RegexpParser
#from chunkers import sub_leaves

chunker = RegexpParser(r'''   
                       NAME: 
                       {<NNP>+} 
                       ''')


def extract_text_by_page(pdf_path):
    texts = []
    start_time = time.time()
    parsed = parser.from_file(pdf_path)
    pages = parsed['content'].split('\n\n\n')  # Split by page

    for page_number, page_text in enumerate(pages):
        #print(f"Page {page_number + 1}:\n{page_text.strip()}\n")
        text = page_text.strip()
        texts.append(text)

    end_time = time.time()  # End the timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print("Elapsed Time:", elapsed_time, "seconds")
    return texts

pdf_path = r'C:\Users\sasha\Desktop\Elmento-Materials\war-and-peace.pdf'

# NAMEPARSER
# from nameparser import HumanName
texts = extract_text_by_page(pdf_path)
# for text in texts:
#     name = HumanName(text)
#     print(name.last)

from nltk import pos_tag, ne_chunk, tree
from nltk.tokenize import SpaceTokenizer
import nltk
nltk.download('maxent_ne_chunker')
nltk.download('words')
from collections import Counter

names = []

for text in texts:
    tokenizer = SpaceTokenizer()
    toks = tokenizer.tokenize(text)
    pos = pos_tag(toks)
    chunked_nes = ne_chunk(pos)

    nes = [' '.join(map(lambda x: x[0], ne.leaves())) for ne in chunked_nes if isinstance(ne, tree.Tree)]
    for n in nes:
        names.append(n)

# Use Counter to create a dictionary of names and their counts
names_count = Counter(names)

sorted_names_count = sorted(names_count.items(), key=lambda item: item[1], reverse=True)

# Print each name and its count, now sorted by count
for name, count in sorted_names_count:
    print(f"{name}: {count}")