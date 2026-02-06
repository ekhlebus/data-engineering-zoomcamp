#!/usr/bin/env python
# coding: utf-8

import pandas as pd

prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
url = f'{prefix}/yellow_tripdata_2021-01.csv.gz'
df = pd.read_csv(url) # we using only 100 rows since total dataset is 1369765 rows



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
   # nrows=100,
    dtype=dtype,
    parse_dates=parse_dates
)



get_ipython().system('uv add sqlalchemy psycopg2-binary')


# After installation we can check our `pyproject.toml` and see that `sqlalchemy` is added.

# Now we want to specify how we want to connect to our database.

from sqlalchemy import create_engine
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')


# First of all let's get schema from our table (df) for the database we want to create.
# 
# Let's see what we are going to create.
# We will create a table named "yellow_taxi_data" with next columns:


print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))



df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')


# To quickly check if database was created run `pgcli` in pipeline directory in terminal:
# 
# ```bash
# uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
# ```
# There we can use `\dt` and see that databases created.

# ## Insert data in batches
# 
# Since our table is very big we don't want to insert all the data at once. Let's do it in batches and use an **iterator** for that.



# Create iterator when we read the data
df_iter = pd.read_csv(
    url,
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=100000,
)



get_ipython().system('uv add tqdm')



from tqdm.auto import tqdm



for df_chunk in tqdm(df_iter):
    df_chunk.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')





