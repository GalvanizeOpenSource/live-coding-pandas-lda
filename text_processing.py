import sys,re
import pandas as pd
import numpy as np
import spacy
from sklearn.feature_extraction.stop_words import ENGLISH_STOP_WORDS
from string import punctuation,printable
nlp = spacy.load('en')




if not sys.version_info.major == 3:
    raise Exception("Need to run with Python 3")

# Load the spacy.en module if it hasn't been loaded already
if not 'nlp' in locals():
    print("Loading English Module...")
    nlp = spacy.load('en')

def clean_article(doc, stop_words,punct_dict,entities=True):
    """
    generalized function to lemmatize string
    """

    # Remove punctuation form string
    doc = doc.translate(punct_dict)
    
    # remove unicode
    clean_doc = "".join([char for char in doc if char in printable])
            
    # Run the doc through spaCy
    doc = nlp(clean_doc)

    # Keep entities like 'the New York Times' from getting dropped
    if entities:
        for ent in doc.ents:
            if ent.root.tag_ != 'DT':
                ent.merge(ent.root.tag_, ent.text, ent.label_)
            else:
                ent.merge(ent[-1].tag_, ent.text, ent.label_)

    ## specify the parts of speech to keep            
    pos_lst = ['ADJ', 'ADV', 'NOUN', 'PROPN', 'VERB'] # NUM?

    def clean_token(token):
        ## check that token is in parts of speech list
        if token.pos_ not in pos_lst:
            return None
        # check that we have valid word characters in token
        elif not re.search("\w",token.text):
            return None
        
        ## handle how white space looks
        token = re.sub(" +","_",token.lemma_.lower())
        token = re.sub("\W+","",token)
        return(token)
    
    tokens = [clean_token(token) for token in doc if clean_token(token)]
    
    # Lemmatize and lower text
    return ' '.join(w for w in tokens if w not in stop_words)


if __name__=='__main__':
    ## define stoplist and punc
    STOPLIST = set(list(ENGLISH_STOP_WORDS) + ["n't", "'s", "'m", "ca", "'", "'re",'pron'])
    PUNCT_DICT = {ord(punc): None for punc in punctuation if punc not in ['_', '*']}

    print("...reading articles")
    df = pd.read_csv('npr_articles.csv', parse_dates=['date_published'])
    print("...cleaning articles")
    df['processed_text'] = df['article_text'].apply(lambda x: clean_article(x,STOPLIST, PUNCT_DICT,entities=True))
    df.to_csv('npr_articles_clean.csv', index=False)
