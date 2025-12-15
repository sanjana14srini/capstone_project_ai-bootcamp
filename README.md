# 🚀 Capstone Project - AI BOOTCAMP

This capstone project is a full-stack AI appllication built as a part of the AI Bootcamp: From RAG to Agents. The primary utility of this project is to be able to query the arxiv research repository through natural language using AI agents. 


## The project leverages:

**FastAPI**: Serves as the backend API for AI-powered operations.

**Streamlit**: Provides an interactive frontend for users to interact with the AI models.

**Elasticsearch**: Stores and indexes textual data for efficient retrieval and search.

**OpenAI GPT models**: Powers text summarization, question-answering, and structured output generation.



## ⚙️ Features:

- **Search and Summarization**: Users can query a document corpus and receive AI-generated summaries.

- **Structured Outputs**: AI responses are returned in a predefined structured format for consistency.

- **Interactive Frontend**: Streamlit frontend allows users to input queries and view results dynamically.


## Architecture: 
```markdown
```plaintext
+----------------+       +-----------------+       +------------------+
|                |       |                 |       |                  |
|  Streamlit     | <-->  |  FastAPI backend| <-->  |  Elasticsearch   |
|  Frontend      |       |  (Uvicorn)      |       |  (Data storage)  |
|                |       |                 |       |                  |
+----------------+       +-----------------+       +------------------+
```
- **Frontend**: Provides user interface for inputting queries and displaying results.

- **Backend**: Handles AI processing, structured output generation, and communication with Elasticsearch.

- **Elasticsearch**: Stores document chunks and enables fast, full-text search.

```` ``` ````


## Project Structure:
<details>
<summary>Click to expand</summary>
```markdown
``` plaintext
capstone_project_ai-bootcamp/
├── backend/
│    ├── app
├── ui/
│    ├── app
├── tests/
├── agents
├── agent_logging
├── tools
├── helper_functions
├── main
├── requirements.txt
├── evals

</details>

```` ``` ````
## Set-up Instructions:
### Follow the below noted steps to run this application locally

### 1. make sure you have an openai account with an api key set up and accessible for this code
### 2. install python 3.12 or higher
### 3. install docker https://docs.docker.com/desktop/
### 4. install uv, set up the virtual environment and activate it
    - `python3 -m pip install uv`
    - ```uv init```
    - ```uv add -r requirements.txt```
    - ```source .venv/bin/activate (MacOS)```

### 5. To run elasticsearch
```docker run -it \
    --rm \
    --name elasticsearch \
    -m 4GB \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -v es9_data:/usr/share/elasticsearch/data \
    docker.elastic.co/elasticsearch/elasticsearch:9.1.1```


### To delete the arxiv_chunks search index (in case you want to reset the index and start fresh)
```curl -X DELETE "http://localhost:9200/arxiv_chunks"```

### 6. To run the backend
```uvicorn backend.app:app --reload --port 8001```

### Testing the fastapi
c```url -X POST http://localhost:8001/chat      -H "Content-Type: application/json"      -d '{"messages":[{"role":"user","content":"top 10 research articles on archaeological findings in the harrapan civilization"}]}'```


### 6. To run the streamlit frontend
 ```streamlit run capstone_project/ui/app.py```


