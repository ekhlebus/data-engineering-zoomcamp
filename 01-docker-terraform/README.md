# Docker and PostgreSQL: Data Engineering Workshop

* Video: [link](https://www.youtube.com/watch?v=lP8xXebHmuE)
* Slides: [link](https://docs.google.com/presentation/d/19pXcInDwBnlvKWCukP5sDoCAb69SPqgIoxJ_0Bikr00/edit?usp=sharing)
* Code: [pipeline/](pipeline/)

In this module, we explore Docker fundamentals and data engineering workflows using Docker containers.

**Data Engineering** is the design and development of systems for collecting, storing and analyzing data at scale.

We will cover:

- Introduction to Docker and containerization
- Running PostgreSQL in a Docker container
- Data ingestion into PostgreSQL
- Working with pgAdmin for database management
- Docker networking and port mapping
- Docker Compose for multi-container applications
- Creating a data ingestion pipeline
- SQL refresher with real-world data
- Best practices for containerized data engineering workflows

## Prerequisites

- Basic understanding of Python
- Basic SQL knowledge (helpful but not required)
- Docker and Python installed on your machine
- Git (optional)


## Preparing the environment 

If working on LINUX working locally should be fine, but if you have Windows using **GitHub codespaces** is more convinient remote environment that already has python and Docker, so we don't need to install them.

To set up terminal in VSCode (and have more space in terminal):
`PS1="> "`

If you don't want to repeat `PS1="> "` every time in each new terminal:
`echo 'PS1="> "' > ~/.bashrc`

## Introduction to Docker

Docker is a _containerization software_ that allows us to isolate software in a similar way to virtual machines but in a much leaner way. What we have inside Docker container is completely isolated from what we have on our host machine. For example if we run `rm -rf` in Docker container it will not effect on our host machine and system on host machine.

A **Docker image** is a _snapshot_ of a container that we can define to run our software, or in this case our data pipelines. By exporting our Docker images to Cloud providers such as Amazon Web Services or Google Cloud Platform we can run our containers there.

**Why Docker?**

Docker provides the following advantages:

- Reproducibility: Same environment everywhere
- Isolation: Applications run independently
- Portability: Run anywhere Docker is installed

They are used in many situations: 

- Integration tests: CI/CD pipelines
- Running pipelines on the cloud: AWS Batch, Kubernetes jobs
- Spark: Analytics engine for large-scale data processing
- Serverless: AWS Lambda, Google Functions


**Basic Docker Commands**

Check Docker version:

```bash
docker --version
```

Run a simple container to see that Docker installation appears to be working correctly.:

```bash
docker run hello-world
```

Run something more complex. Newer image for 'ubuntu:latest' will be downloaded if unable to find image locally:

```bash
docker run ubuntu
```

To see interactive terminal and to go inside Docker container we need to run it in `-it` mode (now it is isolated from host machine):

```bash
docker run -it ubuntu
```

Check if we have `python` there:

```bash
python3
```

We have `python` on host machine, but we don't have it here in Docker container so let's install it:

```bash
apt update && apt install python3
python3 -V
```

To exit container press `ctrl + D`.

Important: Docker containers are stateless - any changes done inside a container will **NOT** be saved when the container is killed and started again.

When you exit the container and use it again like below, the changes are gone:

```bash
docker run -it ubuntu
python3 -V
```

Command not found even if we installed `python` previously. Every time we enter Docker container we create a container from Docker image, and this container is exactly what is described in Docker image. This is good, because it doesn't affect your host system.

Let's say you do something crazy like this:

```bash
docker run -it ubuntu
rm -rf / # don't run it on your computer! 
```

Next time we run it, all the files are back.

But, this is not _completely_ correct. The state is saved somewhere. We can see stopped containers:

```bash
docker ps -a
```

We can restart one of them, but we won't do it, because it's not a good practice. They take space, so let's delete them to clean our environment:

```bash
docker rm `docker ps -aq`
```

Next time we run something, we add `--rm`:

```bash
docker run -it --rm ubuntu
```

There are other base images besides `hello-world` and `ubuntu`. For example, Python:

```bash
docker run -it python:3.13.10
# add -slim to get a smaller version
```
Running this Python image we will get not bash but `python` prompt. If we want bash, we need to overwrite `entrypoint`:

```bash
docker run -it \
    --rm \
    --entrypoint=bash \
    python:3.13.11-slim
```
Now we are in python Docker image but with access to bash.

So, we know that with docker we can restore any container to its initial state in a reproducible manner. How to preserve state and what about data? What if we need to have an access to files from within Docker container or if we want to execute `list_files.py` from Docker container? 

Let's create some data in `test` folder:

```bash
mkdir test
cd test
touch file1.txt file2.txt file3.txt list_files.py
echo "Hello from host" > file1.txt
cd ..
```

To get full path to `/test` directory in our current directory we can run next (we will use it later):

```bash
echo $(pwd)/test
```

Now let's create a simple script `test/list_files.py` that shows the files in the folder and print their content:

```python
from pathlib import Path

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in {current_dir}:")

for filepath in current_dir.iterdir():
    if filepath.name == current_file:
        continue

    print(f"  - {filepath.name}")

    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")
```

How we can execute this script from Docker? One of the option to do that is using _volumes_. In Docker container we can say "Whatever is in this `/test` directory should be available in container too."
Now let's map this to a Python container we used previously using `-v $(pwd)/test:/app/test`:

```bash
docker run -it \
    --rm \
    -v $(pwd)/test:/app/test \
    --entrypoint=bash \
    python:3.13.11-slim
```
**Note:** Run this code from the folder which contains `/test` folder you want to be accessible from container.

Inside the container, run:

```bash
cd /app/test
ls -la
cat file1.txt
python list_files.py
```

You'll see the files from your host machine are accessible in the container! 


## Virtual environment and Data Pipelines

A **data pipeline** is a service that receives data as input and outputs more data. For example, reading a CSV file, transforming the data somehow and storing it as a table in a PostgreSQL database.

```mermaid
graph LR
    A[CSV File] --> B[Data Pipeline]
    B --> C[Parquet File]
    B --> D[PostgreSQL Database]
    B --> E[Data Warehouse]
    style B fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
```

In this workshop, we'll build pipelines that:
- Download CSV data from the web for nyc taxi dataset
- Transform and clean the data with pandas
- Load it into PostgreSQL for querying
- Process data in chunks to handle large files

Let's create a simple example pipeline. First, create a directory `pipeline` and inside, create a file  `pipeline.py`:

```python
import sys
print("arguments", sys.argv) # arguments which we pass to pipeline.py
```

Now run this script with parameters to see if it is working:

```bash
python pipeline.py 12 2738 123
```
As an output you should see: `arguments ['pipeline.py', '12', '2738', '123']`

Let's change our `pipeline.py` script and select first provided argument:

```python
import sys
print("arguments", sys.argv) 

month = int(sys.argv[1])
print(f"Running pipeline for month {month}")
```
This is how we set parameters for our pipelines.

What if we want to do something more fun? Let's add pandas for data processing:

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
print(df.head())

df.to_parquet(f"output_day_{sys.argv[1]}.parquet") # save the dataframe to a parquet binary file
```

We need pandas and other dependencies, but we don't have it. We want to test it before we run things in a container. 

We can install it with `pip`:

```bash
pip install pandas pyarrow
```

But this installs it globally on your system. This can cause conflicts if different projects need different versions of the same package.

Instead, we want to use a **virtual environment** - an isolated Python environment that keeps dependencies for this project separate from other projects and from your system Python.

We'll use `uv` - a modern, fast Python package and project manager written in Rust that can manage virtual environments. It's much faster than pip and handles virtual environments automatically.

```bash
pip install uv
```

Now initialize a Python project with uv:

```bash
uv init --python=3.13
```

This creates a `pyproject.toml` file for managing dependencies and a `.python-version` file. It descibes our project.

Compare the Python versions:

```bash
uv run which python  # Python in the virtual environment
uv run python -V     # Python version in my virtual environment: in my case Python 3.13.11

which python        # System Python
python -V           # In my case Python 3.12.1
```

You'll see they're different - `uv run` uses the isolated environment.

Now we can use this `uv` to install pandas and other dependencies:

```bash
uv add pandas pyarrow
```

This adds pandas and pyarrow to our `pyproject.toml` and installs it in the virtual environment.

We need to say that we want to use python from created virtual environment: `Ctrl + Shift + P` in VSCode, select 'Python: Select Interpreter', select or enter interpreter path (in my case `/workspaces/data-engineering-zoomcamp/01-docker-terraform/pipeline/.venv/bin/python`).

Now we can execute this file:

```bash
uv run python pipeline.py 10
```

We will see:

* `arguments ['pipeline.py', '10']`
* `Running pipeline for month 10`

This script produces a binary (.parquet) file, so let's make sure we don't accidentally commit it to git by adding parquet extensions to `.gitignore`:

```
*.parquet
```

We can see that now in file explorer in .parquet file is grey and we will not commit it to git. Also, it is a good idea to commit everything what we have done already to git:

```
cd ..
git status
git add .
git status
git commit -m 'pipeline'
``` 

## Dockerizing the Pipeline

Now let's containerize the script (put everything in Docker container). Instead of using existing Docker image we can create our own Docker image that has nessesary version of python (3.13.11) and all dependencies we need. To create our own Docker image we need to create the following `Dockerfile` file which describes how exactly we build a Docker container:

```dockerfile
# base Docker image that we will build on
FROM python:3.13.11-slim

# set up our image by installing prerequisites; pandas in this case
RUN pip install pandas pyarrow

# set up the working directory inside the container
WORKDIR /code

# copy the script from the host system to the container (to Docker image). 1st name is source file, 2nd is destination
COPY pipeline.py .

# define what to do first when the container runs
# in this example, we will just run the script
ENTRYPOINT ["python", "pipeline.py"]
```

**Explanation:**

- `FROM`: Base image (Python 3.13)
- `RUN`: What commands to execute during build
- `WORKDIR`: Set working directory
- `COPY`: Copy files into the image
- `ENTRYPOINT`: Default command to run

After preparing Dockerfile we can build Docker container with tag `-t` and base image name `test`, also we need to define directory where we want to build it (in this case in current directory `.`):

```bash
docker build -t test:pandas .
```

* The image name will be `test` and its tag will be `pandas`. If the tag isn't specified it will default to `latest`.

We can now run the container and pass an argument to it, so that our pipeline will receive it:

```bash
docker run -it test:pandas some_number
```

You should get the same output you did when you ran the pipeline script by itself.

Also, we can run the container and run script inside the container. Also, remember that all the things we execute stay in the system unless we delete them using `--rm`, if we include this comand then when we close our Docker container we will not have this state saved somewhere, what is good for our file system (we will not have anything we don't need):

```bash
docker run -it --entrypoint=bash --rm test:pandas 
python pipeline.py 3
```

After running this comand we can see output we saw previously and created .parquet file. This .parquet file stays inside the container, we don't see it in our host system if we not say to uploaded it to some storage.

> Note: these instructions assume that `pipeline.py` and `Dockerfile` are in the same directory. The Docker commands should also be run from the same directory as these files.

What about uv? Let's use it instead of using pip in our Docker image and use all dependencies we used in our virtual environment:

```dockerfile
# Start with slim Python 3.13 image
FROM python:3.13.10-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /code

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/code/.venv/bin:$PATH"

# Copy dependency files first (better layer caching) to teh current directory
COPY "pyproject.toml" "uv.lock" ".python-version" ./

# Install dependencies from uv.lock file (ensures reproducible builds)
RUN uv sync --locked

# Copy application code
COPY pipeline.py .

# Set entry point
# We can use next row if we are using ENV PATH
ENTRYPOINT ["python", "pipeline.py"]
# We can use next row if we are NOT using ENV PATH
# ENTRYPOINT ["uv", "run", "python", "pipeline.py"]
```

Now we can build container using new instructions and run it (building is based on Dockerfile which is in current directory):

```bash
docker build -t test:pandas .
docker run -it --rm test:pandas some_number
```
And see how it works. So, we created our first dokerized data pipeline (even if it is not doing much).

## Running PostgreSQL with Docker
*another useful example of using Dicker run*

Now we want to do real data engineering. Let's use Docker to **run Postgres database** for that. We are running it inside `pipeline` folder.

**PostgreSQL** (often shortened to "Postgres") is an advanced, open-source object-relational database management system.

You can run a containerized version of Postgres that doesn't require any installation steps. You only need to provide a few _environment variables_ to it as well as a _volume_ for storing data.

* A Docker _volume_ is a place where Docker stores data outside of a container. Docker _volumes_ are used for:
    * Saving databases (Postgres, MySQL, etc.)
    * Storing model files, logs, uploads
    * Sharing data between containers

Create a folder anywhere you'd like for Postgres to store data in. We will use the example folder `ny_taxi_postgres_data`. Here's how to **run the Docker container with postgres 18**:

```bash
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

**Explanation of parameters:**

* `-e` sets environment variables (user, password, database name) to configure your application
* `-v ny_taxi_postgres_data:/var/lib/postgresql` creates a **named Docker volume** - internal volume for Docker, that means we will not be able to see what is going on inside and interfere with the content of this files, internal to postgres:
  * Docker manages this volume automatically
  * Data persists even after container is removed
  * Volume is stored in Docker's internal storage
* `-p 5432:5432` maps port 5432 on the host machine to the port 5432 in container, it means that whatever application is running in container it is waiting for request on port 5432 and we want to make it available outside the container, for example from the terminal of host machine.
* `postgres:18` uses PostgreSQL version 18 (latest as of Dec 2025)

After running code above we should see something like:

```
database system is ready to accept connections
```

Now we can create new terminal and in new terminal we want to access this instance of postgres which is running there. In terminal now I see that we are in our virtual environment `pipeline` and go to the folder `pipeline` which contains `pyproject.toml` file:

```
> source /workspaces/data-engineering-zoomcamp/01-docker-terraform/pipeline/.venv/bin/activate
(pipeline) > pwd
/workspaces/data-engineering-zoomcamp
(pipeline) > cd 01-docker-terraform/pipeline/
(pipeline) > ls
Dockerfile  main.py         output_month_10.parquet  pyproject.toml
README.md   notebook.ipynb  pipeline.py              uv.lock
```

**Alternative approach - bind mount:**

First create the directory, then map it:

```bash
mkdir ny_taxi_postgres_data

docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

When you create the directory first, it's owned by your user. If you let Docker create it, it will be owned by the Docker/root user, which can cause permission issues on Linux. On Windows and macOS with Docker Desktop, this is handled automatically.

**Named volume vs Bind mount:**

* **Named volume** (`name:/path`): Managed by Docker, easier
* **Bind mount** (`/host/path:/container/path`): Direct mapping to host filesystem, more control


Once the container with postgres is running in one terminal, we can log into our database in new terminal with [pgcli](https://www.pgcli.com/).

Install pgcli (it should be run in directory where we have `pyproject.toml`):

```bash
uv add --dev pgcli # install pgcli
```

The `--dev` flag marks this as a development dependency (not needed in production). It will be added to the `[dependency-groups]` section of `pyproject.toml` instead of the main `dependencies` section.

Now use it to connect to Postgres, here we are running `pgcli` in virtual environment on our host machine:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

* `uv run` executes a command in the context of the virtual environment
* `-h` is the host. Since we're running locally we can use `localhost`.
* `-p` is the port.
* `-u` is the username.
* `-d` is the database name.
* The password is not provided; it will be requested after running the command.

When prompted, enter the password: `root`

Try some SQL commands. This is how we can interact with our postgress that is running here:

```sql
-- List tables
\dt

-- Create a test table
CREATE TABLE test (id INTEGER, name VARCHAR(50));

-- Insert data
INSERT INTO test VALUES (1, 'Hello Docker');

-- Query data
SELECT * FROM test;

-- Exit
\q
```

## NY Taxi Dataset and Data Ingestion

So now we have postgres and ingestion script already in the container. 

   * An **ingestion script** is a piece of code (often written in Python, SQL, or Bash) designed to automate the process of collecting raw data from various sources and moving it into a centralized destination, such as a data warehouse, data lake, or database. It acts as the "first step" in a data pipeline, acting as the automated bridge that extracts data from applications, APIs, databases, or files, and loads them into a repository for analysis or machine learning. 

Now we want to get ny_taxi .csv data and we want to put it inside postgres. For that we need interactive environment. We will now create a Jupyter Notebook `notebook.ipynb` file which we will use to read a CSV file and export it to Postgres. 

Install Jupyter:

```bash
uv add --dev jupyter
```

Let's create a Jupyter notebook to explore the data:

```bash
uv run jupyter notebook
```

In PORTS in VS Code we can see blue `1`, it means that something was automatically detected at port 8888 and it was automatically forwarded into port 8889. We can open it in browser: click globe symbol in Forwarder port and use token from terminal, for example: `189794c293c47b33ceee9be224b9ca534bed4b8e4cf61235` from `http://localhost:8888/tree?token=189794c293c47b33ceee9be224b9ca534bed4b8e4cf61235`. Click `New` -> `python` -> rename

   * If you don't have port 8888 -> click Add port -> Add 8888

We will use data from the [NYC TLC Trip Record Data website](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page).

Specifically, we will use the [Yellow taxi trip records CSV file for January 2021](https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz).

This data used to be csv, but later they switched to parquet. We want to keep using CSV because we need to do a bit of extra pre-processing (for the purposes of learning it). 

A dictionary to understand each field is available [here](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).


> Note: The CSV data is stored as gzipped files. Pandas can read them directly.


**Explore the Data**

Create a new notebook and run:

```python
import pandas as pd

# Read a sample of the data
prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
url = f'{prefix}/yellow_tripdata_2021-01.csv.gz'
df = pd.read_csv(url, nrows=100)

# Display first rows
df.head()

# Check data types
df.dtypes

# Check data shape
df.shape
```

We have a warning:

```
/tmp/ipykernel_25483/2933316018.py:1: DtypeWarning: Columns (6) have mixed types. Specify dtype option on import or set low_memory=False.
```

So we need to specify the types:

```python
dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

df = pd.read_csv(
    url,
    nrows=100,
    dtype=dtype,
    parse_dates=parse_dates
)
```

## Ingesting Data into Postgres

In the Jupyter notebook, we create code to:

1. Download the CSV file
2. Read it in chunks with pandas
3. Convert datetime columns
4. Insert data into PostgreSQL using SQLAlchemy

First of all for ingesting data into Postgres, we need to install SQLAlchemy, this is what pandas using to interact with different databases:

```bash
uv add sqlalchemy psycopg2-binary
```

After installation we can check our `pyproject.toml` and see that `sqlalchemy` is added.

Create engine:

```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')
```

* `postgresql` database we want to connect
* `root:root` user is root and password is root
* `@localhost:5432` it is running on localhost and the port is 5432 
* `ny_taxi` database is this one


Get DDL schema for the database (this is what we are going to create):

```python
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
```

Output from the previous command:

```sql
CREATE TABLE yellow_taxi_data (
    "VendorID" BIGINT, 
    tpep_pickup_datetime TIMESTAMP WITHOUT TIME ZONE, 
    tpep_dropoff_datetime TIMESTAMP WITHOUT TIME ZONE, 
    passenger_count BIGINT, 
    trip_distance FLOAT(53), 
    "RatecodeID" BIGINT, 
    store_and_fwd_flag TEXT, 
    "PULocationID" BIGINT, 
    "DOLocationID" BIGINT, 
    payment_type BIGINT, 
    fare_amount FLOAT(53), 
    extra FLOAT(53), 
    mta_tax FLOAT(53), 
    tip_amount FLOAT(53), 
    tolls_amount FLOAT(53), 
    improvement_surcharge FLOAT(53), 
    total_amount FLOAT(53), 
    congestion_surcharge FLOAT(53)
)
```

To insert things in database, to create the empty table at first:

```python
df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
```

`head(n=0)` makes sure we only create the table, we don't add any data yet. To quickly check if database was created run `pgcli` again in pipeline directory and check using `\dt`:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```
There we can use `\dt` and see that databases created.

Since our table is very big we don't want to insert all the data at once. Let's do it in batches and use an iterator for that splitting data into chunks and putting chunks in database one by one:


```python
df_iter = pd.read_csv(
    url,
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=100000
)
```

Iterate over it:

```python
for df_chunk in df_iter:
    print(len(df_chunk))
```


Inserting data:

```python
df_chunk.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
```

Putting everything together:

```python
first = True

for df_chunk in df_iter:

    if first:
        # Create table schema (no data)
        df_chunk.head(0).to_sql(
            name="yellow_taxi_data",
            con=engine,
            if_exists="replace"
        )
        first = False
        print("Table created")

    # Insert chunk
    df_chunk.to_sql(
        name="yellow_taxi_data",
        con=engine,
        if_exists="append"
    )

    print("Inserted:", len(df_chunk))
```

If you don't like using the `first` flag:

```python
first_chunk = next(df_iter)

first_chunk.head(0).to_sql(
    name="yellow_taxi_data",
    con=engine,
    if_exists="replace"
)

print("Table created")

first_chunk.to_sql(
    name="yellow_taxi_data",
    con=engine,
    if_exists="append"
)

print("Inserted first chunk:", len(first_chunk))

for df_chunk in df_iter:
    df_chunk.to_sql(
        name="yellow_taxi_data",
        con=engine,
        if_exists="append"
    )
    print("Inserted chunk:", len(df_chunk))
```

Add `tqdm` to see progress:

```bash
uv add tqdm
```

Put it around the iterable:

```python
from tqdm.auto import tqdm

for df_chunk in tqdm(df_iter):
    ...
```

Connect to it using pgcli:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

And explore the data. For example:

```
select count(1) from yellow_taxi_data;
```


## Creating the Data Ingestion Script

Now let's convert the notebook to a Python script:
* create notebook.py from notebook.ipynb
* rename it

```bash
uv run jupyter nbconvert --to=script notebook.ipynb 
mv notebook.py ingest_data.py
```

Then clean up the script:

```python
#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
from tqdm.auto import tqdm

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]


def ingest_data(
        url: str,
        engine,
        target_table: str,
        chunksize: int = 100000,
) -> pd.DataFrame:
    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunksize
    )

    first_chunk = next(df_iter)

    first_chunk.head(0).to_sql(
        name=target_table,
        con=engine,
        if_exists="replace"
    )

    print(f"Table {target_table} created")

    first_chunk.to_sql(
        name=target_table,
        con=engine,
        if_exists="append"
    )

    print(f"Inserted first chunk: {len(first_chunk)}")

    for df_chunk in tqdm(df_iter):
        df_chunk.to_sql(
            name=target_table,
            con=engine,
            if_exists="append"
        )
        print(f"Inserted chunk: {len(df_chunk)}")

    print(f'done ingesting to {target_table}')

def main():
    pg_user = 'root'
    pg_pass = 'root'
    pg_host = 'localhost'
    pg_port = '5432'
    pg_db = 'ny_taxi'
    year = 2021
    month = 1
    chunksize = 100000
    target_table = 'yellow_taxi_data'

    engine = create_engine(f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')
    url_prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow'

    url = f'{url_prefix}/yellow_tripdata_{year:04d}-{month:02d}.csv.gz'

    ingest_data(
        url=url,
        engine=engine,
        target_table=target_table,
        chunksize=chunksize
    )

if __name__ == '__main__':
    main()
```

And to run it:

```
uv run python ingest_data.py 
```

If we want to configure our script through command line interface we can do it like that:

```
uv run python ingest_data.py --year=2022
```

But also we can use copilot and use library `click` for creating command line interface. In copilot write:

```
use click to create cli parameters for this script, parse the arguments. install click with uv 

params are 
    year = 2021
    month = 1

    pg_user = 'root'
    pg_pass = 'root'
    pg_host = 'localhost'
    pg_port = 5432
    pg_db = 'ny_taxi'

    target_table = 'yellow_taxi_data'

    chunksize = 100000
```

Then github copilot will rewrite the code.

The result:

```python
import click

...

@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL username')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default='5432', help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--year', default=2021, type=int, help='Year of the data')
@click.option('--month', default=1, type=int, help='Month of the data')
@click.option('--chunksize', default=100000, type=int, help='Chunk size for ingestion')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
def main(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, chunksize, target_table):
    ...
```

To see the parameters we have:

```
uv run python ingest_data.py --help
```

The script reads data in chunks (100,000 rows at a time) to handle large files efficiently without running out of memory.


Make sure PostgreSQL is running, then execute the ingestion script:

```bash
uv run python ingest_data.py \
  --pg-user=root \
  --pg-pass=root \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --target-table=yellow_taxi_trips_2021_1 \
  --year=2021 \
  --month=1 \
  --chunksize=100000
```

This will download and ingest the data into your PostgreSQL database.

**Verify if Data is in database**

Connect with `pgcli` and query the data to check successful ingestion:

```bash
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

```sql
-- Count records (should return 1,369,765 rows)
SELECT COUNT(*) FROM yellow_taxi_trips;

-- View sample data
SELECT * FROM yellow_taxi_trips LIMIT 10;

-- Basic analytics
SELECT 
    DATE(tpep_pickup_datetime) AS pickup_date,
    COUNT(*) AS trips_count,
    AVG(total_amount) AS avg_amount
FROM yellow_taxi_trips
GROUP BY DATE(tpep_pickup_datetime)
ORDER BY pickup_date;
```

## Dockerizing the Ingestion Script

Let's modify the Dockerfile we created before to include our `ingest_data.py` script:

```dockerfile
# Start with slim Python 3.13 image for smaller size
FROM python:3.13.11-slim

# Copy uv binary from official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory inside container
WORKDIR /app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./
# Install all dependencies (pandas, sqlalchemy, psycopg2)
RUN uv sync --locked

# Copy ingestion script
COPY ingest_data.py ingest_data.py 

# Set entry point to run the ingestion script
ENTRYPOINT [ "python", "ingest_data.py" ]
```

**Explanation:**

- `uv sync --locked` installs exact versions from `uv.lock` for reproducibility
- Dependencies (pandas, sqlalchemy, psycopg2) are already in `pyproject.toml`
- Multi-stage build pattern copies uv from official image
- Copying dependency files before code improves Docker layer caching

**Build the Docker Image**

Create Docker image with ingesting script and name taxi_ingest:v001:

```bash
docker build -t taxi_ingest:v001 .
```

**Run the Containerized Ingestion**

The script will automatically replace the pre-existing table!

Instead of what we did previously executing our script from terminal:

```bash
uv run python ingest_data.py ...
```

Now we are running it from Docker:

```bash
docker run -it --rm \
  --network=pg-network \
  taxi_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=ny_taxi \
    --target-table=yellow_taxi_trips_2021_2 \
    --year=2021 \
    --month=2 \
    --chunksize=100000
```

**Important notes:**

* We need to provide the network for Docker to find the Postgres container. It goes before the name of the image.
* Since Postgres is running on a separate container, the host argument will have to point to the container name of Postgres (`pgdatabase`).
* You can drop the table in pgAdmin beforehand if you want, but the script will automatically replace the pre-existing table.

## Docker Compose

`docker-compose` allows us to launch multiple containers using a single configuration file, so that we don't have to run multiple complex `docker run` commands separately.

Docker compose makes use of YAML files. Here's the `docker-compose.yaml` file for running the Postgres and pgAdmin containers:

```yaml
services:
  pgdatabase:
    image: postgres:18
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "ny_taxi_postgres_data:/var/lib/postgresql:rw"
    ports:
      - "5432:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    volumes:
      - "pgadmin_data:/var/lib/pgadmin"
    ports:
      - "8085:80"

volumes:
  ny_taxi_postgres_data:
  pgadmin_data:
```

* We don't have to specify a network because `docker-compose` takes care of it: every single container (or "service", as the file states) will run within the same network and will be able to find each other according to their names (`pgdatabase` and `pgadmin` in this example).
* All other details from the `docker run` commands (environment variables, volumes and ports) are mentioned accordingly in the file following YAML syntax.

**Start Services with Docker Compose**

We can now run Docker compose by running the following command from the same directory where `docker-compose.yaml` is found. Make sure that all previous containers aren't running anymore:

```bash
docker-compose up
```

>Note: this command assumes that the `ny_taxi_postgres_data` used for mounting the volume is in the same directory as `docker-compose.yaml`.

Since the settings for pgAdmin were stored within the container and we have killed the previous one, you will have to re-create the connection by following the steps in the pgAdmin section.

You will have to press `Ctrl+C` in order to shut down the containers. The proper way of shutting them down is with this command:

```bash
docker-compose down
```

And if you want to run the containers again in the background rather than in the foreground (thus freeing up your terminal), you can run them in detached mode:

```bash
docker-compose up -d
```

Other useful commands:

```bash
# View logs
docker-compose logs

# Stop and remove volumes
docker-compose down -v
```

**Benefits of Docker Compose:**

- Single command to start all services
- Automatic network creation
- Easy configuration management
- Declarative infrastructure

If you want to re-run the dockerized ingest script when you run Postgres and pgAdmin with `docker-compose`, you will have to find the name of the virtual network that Docker compose created for the containers. You can use the command `docker network ls` to find it and then change the `docker run` command for the dockerized script to include the network name.

```bash
# check the network link:
docker network ls 

# it's pipeline_default
# now run the script:
docker run -it \
  --network=pipeline_default \
  taxi_ingest:v001 \
    --pg-user=root \
    --pg-pass=root \
    --pg-host=pgdatabase \
    --pg-port=5432 \
    --pg-db=ny_taxi \
    --target-table=yellow_taxi_trips_2021_2 \
    --year=2021 \
    --month=2 \
    --chunksize=100000
```

## Cleanup

When you're done with the workshop, clean up Docker resources to free up disk space:

**Stop all running containers:**
```bash
docker-compose down
```

**Remove specific containers:**
```bash
# List all containers
docker ps -a

# Remove specific container
docker rm <container_id>

# Remove all stopped containers
docker container prune
```

**Remove Docker images:**
```bash
# List all images
docker images

# Remove specific image
docker rmi taxi_ingest:v001
docker rmi test:pandas

# Remove all unused images
docker image prune -a
```

**Remove Docker volumes:**
```bash
# List volumes
docker volume ls

# Remove specific volumes
docker volume rm ny_taxi_postgres_data
docker volume rm pgadmin_data

# Remove all unused volumes
docker volume prune
```

**Remove Docker networks:**
```bash
# List networks
docker network ls

# Remove specific network
docker network rm pg-network

# Remove all unused networks
docker network prune
```

**Complete cleanup (removes everything):**
```bash
# ⚠️ Warning: This removes ALL Docker resources!
docker system prune -a --volumes
```

**Clean up local files:**
```bash
# Remove parquet files
rm *.parquet

# Remove Python cache
rm -rf __pycache__ .pytest_cache

# Remove virtual environment (if using venv)
rm -rf .venv
```

## pgAdmin - Database Management Tool

`pgcli` is a handy tool but it's cumbersome to use for complex queries and database management. [`pgAdmin` is a web-based tool](https://www.pgadmin.org/) that makes it more convenient to access and manage our databases.

It's possible to run pgAdmin as a container along with the Postgres container, but both containers will have to be in the same _virtual network_ so that they can find each other.

**Run pgAdmin Container**

```bash
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  dpage/pgadmin4
```

The `-v pgadmin_data:/var/lib/pgadmin` volume mapping saves pgAdmin settings (server connections, preferences) so you don't have to reconfigure it every time you restart the container.

* The container needs 2 environment variables: a login email and a password. We use `admin@admin.com` and `root` in this example.
* pgAdmin is a web app and its default port is 80; we map it to 8085 in our localhost to avoid any possible conflicts.
* The actual image name is `dpage/pgadmin4`.

**Note:** This won't work yet because pgAdmin can't see the PostgreSQL container. They need to be on the same Docker network!

**Docker Networks**

Let's create a virtual Docker network called `pg-network`:

```bash
docker network create pg-network
```

> You can remove the network later with the command `docker network rm pg-network`. You can look at the existing networks with `docker network ls`.

Stop both containers and re-run them with the network configuration:

```bash
# Run PostgreSQL on the network
docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  --network=pg-network \
  --name pgdatabase \
  postgres:18

# In another terminal, run pgAdmin on the same network
docker run -it \
  -e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
  -e PGADMIN_DEFAULT_PASSWORD="root" \
  -v pgadmin_data:/var/lib/pgadmin \
  -p 8085:80 \
  --network=pg-network \
  --name pgadmin \
  dpage/pgadmin4
```

* Just like with the Postgres container, we specify a network and a name for pgAdmin.
* The container names (`pgdatabase` and `pgadmin`) allow the containers to find each other within the network.

**Connect pgAdmin to PostgreSQL**

You should now be able to load pgAdmin on a web browser by browsing to `http://localhost:8085`. Use the same email and password you used for running the container to log in.

1. Open browser and go to `http://localhost:8085`
2. Login with email: `admin@admin.com`, password: `root`
3. Right-click "Servers" → Register → Server
4. Configure:
   - **General tab**: Name: `Local Docker`
   - **Connection tab**:
     - Host: `pgdatabase` (the container name)
     - Port: `5432`
     - Username: `root`
     - Password: `root`
5. Save

Now you can explore the database using the pgAdmin interface!

--- 

That's all for today. Happy learning! 🐳📊
