# base Docker image that we will build on
FROM python:3.13.11-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# set up the working directory inside the container
WORKDIR /code

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/code/.venv/bin:$PATH"

# set up our image by installing prerequisites; pandas in this case
# RUN pip install pandas pyarrow

# Copy dependency files first (better layer caching) to teh current directory
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Install dependencies from uv.lock file (ensures reproducible builds)
RUN uv sync --locked

# copy the script from the host system to the container (to Docker image). 1st name is source file, 2nd is destination
COPY ingest_data.py .

# define what to do first when the container runs
# in this example, we will just run the script
# ENTRYPOINT ["python", "pipeline.py"]

# Set entry point
ENTRYPOINT ["python", "ingest_data.py"]