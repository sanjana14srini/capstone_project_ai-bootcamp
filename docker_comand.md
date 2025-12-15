
# To run elasticsearch
docker run -it \
    --rm \
    --name elasticsearch \
    -m 4GB \
    -p 9200:9200 \
    -p 9300:9300 \
    -e "discovery.type=single-node" \
    -e "xpack.security.enabled=false" \
    -v es9_data:/usr/share/elasticsearch/data \
    docker.elastic.co/elasticsearch/elasticsearch:9.1.1


# To delet the arxiv_chunks search index
curl -X DELETE "http://localhost:9200/arxiv_chunks"







