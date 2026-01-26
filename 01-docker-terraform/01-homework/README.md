# Module 1 Homework: Docker & SQL

Questions with full description are [here]().

## Question 1. Understanding Docker images
Run docker with the `python:3.13` image. Use an entrypoint `bash` to interact with the container.
What's the version of `pip` in the image?

```bash
docker run -it \
    --rm \
    --entrypoint=bash \
    python:3.13-slim

pip --version
pip 25.3 from /usr/local/lib/python3.13/site-packages/pip (python 3.13)
```
**Answer:** pip 25.3

## Question 2. Understanding Docker networking and docker-compose
Given the following `docker-compose.yaml`, what is the `hostname` and `port` that pgadmin should use to connect to the postgres database?