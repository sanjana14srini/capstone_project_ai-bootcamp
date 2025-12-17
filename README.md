# 🚀 Capstone Project - AI BOOTCAMP

This capstone project is a **full-stack AI appllication** built as a part of the AI Bootcamp: From RAG to Agents. The primary utility of this project is to be able to interact with the arxiv research repository through natural language using AI agents. The project succesfully **searches**, **indexes**, and **summarizes** its findings based on the user's query. 


## The project leverages:

**FastAPI**: Serves as the backend API for AI-powered operations.

**Streamlit**: Provides an interactive frontend for users to interact with the AI models.

**Elasticsearch**: Stores and indexes textual data for efficient retrieval and search.

**OpenAI GPT models**: Powers text summarization, question-answering, and structured output generation. We work with gpt-40-mini for summarizing, whereas got-5-nano for evaluation.



## ⚙️ Features:

- **Search and Summarization**: Users can query a document corpus and receive AI-generated summaries.

- **Structured Outputs**: AI responses are returned in a predefined structured format for consistency.

- **Interactive Frontend**: Streamlit frontend allows users to input queries and view results dynamically.


## Architecture: 

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

## Set-up Instructions:

### Follow the below noted steps to run this application locally

### 1. make sure you have an openai account with an api key set up and accessible for this code
### 2. install python 3.12 or higher
### 3. install docker https://docs.docker.com/desktop/
### 4. install uv, set up the virtual environment and activate it
- `python3 -m pip install uv`
- ```uv init```
- ```uv add openai messages pydantic pydantic_ai toyaikit jaxn elasticsearch streamlit feedparser```
- ```source .venv/bin/activate (MacOS)```

### 5. To run elasticsearch
```
docker run -it \
--rm \
--name elasticsearch \
-m 2GB \
-p 9200:9200 \
-p 9300:9300 \
-e "discovery.type=single-node" \
-e "xpack.security.enabled=false" \
-v es9_data:/usr/share/elasticsearch/data \
docker.elastic.co/elasticsearch/elasticsearch:9.1.1
```


### To delete the arxiv_chunks search index (in case you want to reset the index and start fresh)
```curl -X DELETE "http://localhost:9200/arxiv_chunks"```

### 6. To run the backend
```uvicorn backend.app:app --reload --port 8001```

### Testing the fastapi
```curl -X POST http://localhost:8001/chat      -H "Content-Type: application/json"      -d '{"messages":[{"role":"user","content":"top 10 research articles on archaeological findings in the harrapan civilization"}]}'```


### 6. To run the streamlit frontend
 ```streamlit run ui/app.py```


## Self-evaluation using Agents:
This is done within the evals.py script built on top of the groud truth data present in `questions_dataset.csv`
The results can be found in `evals.csv` and `metrics. csv`

- How you can run your own evaluations:
To run your own evaluations, you can do as follows:
- Run elasticsearch, backend and the streamlit frontend
- Have conversations with the chat interface. These conversations will be logged as json files inside monitoring/logs folder
- You can move your desired logs into the evals/eval_logs folder and run the evaluator.py script
- This will generate evals.csv and metrics.csv where you get metadata and scores for various model performance metrics of your logs
- You can then play around with the agent prompts, chunking strategy or model preference using these scores as benchmarks

This is exactly how the model prompts were tuned and chunking strategy were adopted for this project
The evals/questions_dataset.csv consists of the ground_truth questions set against which evals were set-up. 