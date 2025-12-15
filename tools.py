import os
import sys
import requests
from typing import Any, Dict, Iterable, List
from tqdm.auto import tqdm
import logging
from pydantic import BaseModel


# setting up the arxiv api
import urllib, urllib.request
import feedparser
from arxiv2text import arxiv_to_text
# from helper_functions import sliding_window

from elasticsearch import Elasticsearch

# Turn off all logging
logging.disable(logging.CRITICAL)

def sliding_window(
        seq: Iterable[Any],
        size: int,
        step: int
    ) -> List[Dict[str, Any]]:
    """
    Create overlapping chunks from a sequence using a sliding window approach.

    Args:
        seq: The input sequence (string or list) to be chunked.
        size (int): The size of each chunk/window.
        step (int): The step size between consecutive windows.

    Returns:
        list: A list of dictionaries, each containing:
            - 'start': The starting position of the chunk in the original sequence
            - 'content': The chunk content

    Raises:
        ValueError: If size or step are not positive integers.

    Example:
        >>> sliding_window("hello world", size=5, step=3)
        [{'start': 0, 'content': 'hello'}, {'start': 3, 'content': 'lo wo'}]
    """
    if size <= 0 or step <= 0:
        raise ValueError("size and step must be positive")

    n = len(seq)
    result = []
    for i in range(0, n, step):
        batch = seq[i:i+size]
        result.append({'start': i, 'content': batch})
        if i + size > n:
            break

    return result


class FetchQuery(BaseModel):
    query: str
    paper_name: str



class Agent_Tools():

    def __init__(self, es_index, max_results=None):
        self.index_name = "arxiv_chunks"
        if max_results is None:
            self.max_results = 5
        else:
            self.max_results = max_results
        self.index = es_index
        self.index_settings = {
            "mappings": {
                "properties": {
                        "id": {"type": "text"},
                        "title": {"type": "text"},
                        "authors": {"type": "keyword"},
                        "published": {"type": "text"},
                        "summary": {"type": "text"},
                        "content": {"type": "text"},
                }
            }
        }


    def get_metadata(self, paper_name="electron"):

        paper_name = paper_name.replace(" ", "+")

        url = f'http://export.arxiv.org/api/query?search_query=all:{paper_name}&max_results={self.max_results}'
        data = urllib.request.urlopen(url).read()
        feed = feedparser.parse(data)

        return feed


    def extract_data(self, feed):
        doc = []
        
        for entry in feed.entries:
            entry_id_url = entry.id
            arxiv_id = entry_id_url.split('/')[-1]

            #TODO: this pdf_url is not always yielding correct links.
            # it breaks the tool call. fix it.
            pdf_url = entry["links"][1]["href"]
            paper_data = arxiv_to_text(pdf_url)

            if paper_data is not None:
                chunks = sliding_window(paper_data, 5000, 1000)
                for chunk in chunks:
                    entry_dict = { 
                        "id": arxiv_id,
                        "title": entry.title,
                        "authors": [auth['name'] for auth in entry.authors],
                        "published": entry.published,
                        "summary": entry.summary,
                        "content": chunk["content"],

                    }
                    doc.append(entry_dict)
                # print(f"successfully extracted the pdf {pdf_url}")
            else:
                # print(f"pdf not found for {pdf_url}")
                continue
        
        return doc


    def create_elasticsearch_index(self, doc):
        if self.index.ping():
            print("✅ Connected to Elasticsearch")
        else:
            print("❌ Connection failed")

        if not self.index.indices.exists(index=self.index_name):
            self.index.indices.create(index=self.index_name, body=self.index_settings)
            print(f"✅ Created index: {self.index_name}")

        for chunks in tqdm(doc):        
            self.index.index(index=self.index_name, document=chunks)
   

    def get_data_to_index(self, param: FetchQuery):
        feed = self.get_metadata(param.paper_name)
        doc = self.extract_data(feed)
        self.create_elasticsearch_index(doc)


    def search(self, param: FetchQuery):

        es_query = {
            "size": self.max_results,
            "query": {
                "multi_match": {
                    "query": param.query,
                    "type": "best_fields",
                    "fields": ["content", "filename", "title", "description"],
                }
            }
        }
        
        if not self.index.indices.exists(index=self.index_name):
            self.index.indices.create(index=self.index_name, body=self.index_settings)

        response = self.index.search(index=self.index_name, body=es_query)

        result_docs = []
        
        for hit in response['hits']['hits']:
            result_docs.append(hit['_source'])
        
        return result_docs


# es = Elasticsearch("http://localhost:9200")

# agent_class = Agent_Tools(es_index=es)
# feed = agent_class.get_metadata("LoRA", 5)
# doc = agent_class.extract_data(feed)

# es_index = agent_class.create_elasticsearch_index(doc)
# r = agent_class.search(es_index, "arxiv_chunks", "what is LoRA?")
# print(r)
