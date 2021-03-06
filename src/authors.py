# Author: Krists Kreics
import sys
import csv
import operator
import gensim
from collections import defaultdict
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer
from stop_words import get_stop_words

q = 'Michael I. Jordan'


# Check for numbers in text
def is_number(n):
  try:
    float(n)
    return True
  except:
    return False


def process_authors(name):
  """
  Returns
  -------
  (relevant_authors, author_variety) - tuple where:
    - relevant_authors: TODO
    - author_variety: TODO
  """
  relevant_authors = []
  author_variety = set()
  # Get all authors that match the name passed
  with open('../nips-data/authors.csv', 'r') as csv_file:
    authors = csv.DictReader(csv_file)
    for author in authors:
      if author.get('name').find(name) != -1:
        relevant_authors.append(author.get('id'))
        author_variety.add(author.get('name'))

  return (relevant_authors, author_variety)


def check_author_validity(author_variety,  author_name):
  """
  Make sure that only one author is matched.
  """
  if len(author_variety) == 0:
    sys.exit('Could not find any author named "{}"'.format(author_name))
  if len(author_variety) > 1:
    potential_authors = ', '.join(author_variety)
    sys.exit('Different authors found. Did you mean one of these: ' + potential_authors)


def get_relevant_papers(relevant_authors):
  relevant_papers = []

  for relevant_author in relevant_authors:
    with open('../nips-data/paper_authors.csv', 'r') as csv_file:
      paper_authors = csv.DictReader(csv_file)
      for paper_author in paper_authors:
        if paper_author.get('author_id') == str(relevant_author):
          relevant_papers.append(paper_author.get('paper_id'))

  return relevant_papers

def get_coauthors(relevant_papers, relevant_authors):
  # Get co-authors
  coauthors = defaultdict(lambda: 0)

  with open('../nips-data/paper_authors.csv', 'r') as csv_file:
    paper_authors = csv.DictReader(csv_file)
    for paper_author in paper_authors:
      for relevant_paper in relevant_papers:
        if str(relevant_paper) == paper_author.get('paper_id'):
          if paper_author.get('author_id') not in relevant_authors:
            author = paper_author.get('author_id')
            coauthors[author] += 1

  return coauthors

def get_author_texts_and_years(relevant_papers):
  author_texts = []
  years = defaultdict(lambda: 0)

  with open('../nips-data/papers.csv', 'r') as csv_file:
    papers = csv.DictReader(csv_file)
    # Get paper-year allocation
    for paper in papers:
      for relevant_paper in relevant_papers:
        if paper.get('id') == relevant_paper:
          author_texts.append(paper.get('abstract'))
          year = paper.get('year')
          years[year] += 1

  return (author_texts, years)

def get_text_keywords_sanitized(author_texts):
  texts = []
  tokenizer = RegexpTokenizer(r'\w+')
  en_stop = get_stop_words('en')

  # LDA topic extraction
  # Remove stop words and stem
  for text in author_texts:
    raw = text.lower()
    tokens = tokenizer.tokenize(raw)
    stopped_tokens = [i for i in tokens if not i in en_stop]
    # p_stemmer = PorterStemmer()
    # stemmed_tokens = [p_stemmer.stem(i) for i in stopped_tokens]
    terms = filter(lambda x: len(x) > 2 and not is_number(x), stopped_tokens)
    texts.append(list(terms))

  return texts


def build_models(texts):
  # Build models
  dictionary = gensim.corpora.Dictionary(texts)
  corpus = [dictionary.doc2bow(text) for text in texts]
  ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=5, id2word=dictionary, passes=20)
  lsimodel = gensim.models.lsimodel.LsiModel(corpus, id2word=dictionary, num_topics=5)

  # Print results of topic modeling
  print('LDA:')
  print(ldamodel.show_topics(10, 7))
  print('LSI:')
  print(lsimodel.print_topics(5))

  return ldamodel, lsimodel


def author_query(author_name):
  relevant_authors, author_variety = process_authors(author_name)

  check_author_validity(author_variety, author_name)

  relevant_papers = get_relevant_papers(relevant_authors)

  coauthors = get_coauthors(relevant_papers, relevant_authors)

  sorted_coauthors = sorted(coauthors, key=operator.itemgetter(1), reverse=True)

  # Print some information
  print('List of common co-authors:')
  with open('../nips-data/authors.csv', 'r') as csv_file:
    authors = csv.DictReader(csv_file)
    for author in authors:
      for coauthor in sorted_coauthors[:5]:
        if author.get('id') == coauthor:
          print(author.get('name'))

  author_texts, years = get_author_texts_and_years(relevant_papers)

  # Print some information
  sorted_years = sorted(years)
  print('Count of papers by year:')
  for year in range(int(sorted_years[0]), int(sorted_years[-1])):
    year_str = str(year)
    if year_str in years:
      print(year_str + ': ' + str(years[year_str]))

  texts = get_text_keywords_sanitized(author_texts)

  lsa_model, lsi_model = build_models(texts)

  return lsa_model, lsi_model

if __name__ == '__main__':
  lsa_model, lsmi_model = author_query(q)
  # lsa_model.
