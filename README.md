# 🚀 Capstone Project - AI BOOTCAMP

This capstone project is a **full-stack AI appllication** built as a part of the AI Bootcamp: From RAG to Agents. The primary utility of this project is to be able to interact with the arxiv research repository through natural language using AI agents. The project succesfully **searches**, **indexes**, and **summarizes** its findings from arxiv's api based on the user's query. 


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
        ├── evals
        ├── monitoring


</details>

## Set-up Instructions:

### Follow the below noted steps to run this application locally

1. Make sure you have an openai account with an api key set up and accessible for this code. This project has access to openai credentials through git hub codespace secrets. You can attempt to do the same. 
- Creating openai API key: https://www.youtube.com/watch?v=Lj43aSwNpog
- Adding api key to github codespaces: https://www.youtube.com/watch?v=Ekkn7y3QPIY
2. Install python 3.12 or higher
3. Install docker https://docs.docker.com/desktop/
4. Install uv, set up the virtual environment and activate it
- `python3 -m pip install uv`
- ```uv init```
- ```uv add openai messages pydantic pydantic_ai toyaikit jaxn elasticsearch streamlit feedparser```
- ```source .venv/bin/activate (MacOS)```

5. To run elasticsearch

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


- To delete the arxiv_chunks search index (in case you want to reset the index and start fresh)
```curl -X DELETE "http://localhost:9200/arxiv_chunks"```

6. To run the backend
```uvicorn backend.app:app --reload --port 8001```

- Testing the fastapi
```curl -X POST http://localhost:8001/chat      -H "Content-Type: application/json"      -d '{"messages":[{"role":"user","content":"pre-puberty associated stress disorders"}]}'```


7. To run the streamlit frontend
 ```streamlit run ui/app.py```

## Testing Agents
There are pytests present inside the tests folder. 
The `test_agent.py` contains tests to check for proper tool calls and ooutput formats
The `test_llm_judge.py` evaluates other difficult to catch edge cases such as if search_quality_check tool gets called everytime the search tool is called. 

To test them you can run: ```uv run pytest```

## Monitoring
All interactions with the tool are automatically monitored. The logs are stored within the logs folder.

## Self-evaluation using Agents:
This is done within the evals.py script built on top of the groud truth data present in `questions_dataset.csv`
The results can be found in `evals.csv` and `metrics. csv` under latest_evals or ground_truth folders.

### How you can run your own evaluations:
To run your own evaluations, you can do as follows:
- Run elasticsearch, backend and the streamlit frontend
- Have conversations with the chat interface. These conversations will be logged as json files inside `monitoring/logs` folder
- You can move your desired logs into the `evals/<your-folder-name>/eval_logs` folder and run the evaluator.py script by updating the directory names
- This will generate evals.csv and metrics.csv where you get metadata and scores for various model performance metrics of your logs
- You can then play around with the agent prompts, chunking strategy or model preference using these scores as benchmarks

This is exactly how the model prompts were tuned and chunking strategy were adopted for this project
The `evals/questions_dataset.csv` consists of the ground_truth questions set against which evals were set-up. 

Originally when running evals over the ground truth data, the evals were pretty bad. This can be noticed from the scores inside the `evals/ground_truth/ground_truth_all_metrics.csv`
This prompted me to dive deeper into the methodology and add an extra agent/tool to check the quality of search once search results were retreived. The addition of this tool improved the
quality of the final answers, which can be observed in the scores in `evals/latest_evals/all_metrics.csv`

The `questions_dataset.csv` also contains a more direct comparison of the final answers under both scenarios for direct human verification. 
Although the evaluation scores have improved with the addition of the search_quality_check tool, it is not a monumental improvement in the completeness of the final result. 
Further improvements that can be considered for the furture could be:
- Look deeper into the quality of searching the index, perhaps experiment with others search indices like Qdrant for better search and retreival quality
- Experiment further with the chunking strategy to indirectly improve search and retreival quality
- Experiment with other openai models 

### Ground Truth Eval Scores 

| Metric | Score |
|------|------|
| instructions_follow | 0.1 |
| instructions_avoid | 0.5 |
| answer_relevant | 0.7 |
| answer_clear | 0.4 |
| answer_citations | 0.0 |
| completeness | 0.0 |
| tool_call_search | 1.0 |                       

### Latest Eval Scores

| Metric | Score |
|------|------|
| instructions_follow | 0.2 |
| instructions_avoid | 0.9 |
| answer_relevant | 0.7 |
| answer_clear | 0.5 |
| answer_citations | 0.2 |
| completeness | 0.1 |
| tool_call_search | 1.0 |


## Demo 
Watch the demo here: https://github.com/sanjana14srini/capstone_project_ai-bootcamp/blob/main/output.mp4

![alt text](demo.gif)