import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext

# Note: Even though the Glue script may seem simple in terms of transformations, these steps are fundamental for data preparation and ensuring data quality before further processing or analysis. 

# Parsing and retrieving command-line arguments passed to the job when it is run. Extracts values for the specified argument names and returns a dict called args.
args = getResolvedOptions(sys.argv, ['JOB_NAME','dag_name','task_id','correlation_id'])

s3_bucket = "YOUR_S3_BUCKET"

# Initialize Spark context and Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Get the Glue logger to log messages
logger = glueContext.get_logger()

# Construct a correlation ID using the DAG name, task ID, and correlation ID
correlation_id = args['dag_name'] + "." + args['task_id'] + " " + args['correlation_id']
logger.info("Correlation ID from GLUE job: " + correlation_id)

# Create a dynamic frame by reading data from the Glue Data Catalog
# dynamic frame: distributed collection of data with a schema similar to df in spark. Designed to handle semi-structured and unstructured data sources like JSON and CSV.
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "default", table_name = "green", transformation_ctx = "datasource0")
logger.info("After create_dynamic_frame.from_catalog: " + correlation_id )

# Apply mappings to the dynamic frame to rename and cast columns to the appropriate types
# In the ApplyMapping method, the mappings specify how to transform the input schema (from the data catalog) into a new schema.
applymapping1 = ApplyMapping.apply(frame = datasource0, 
                                   mappings=[
                                            ("vendorid", "long", "vendorid", "long"),
                                            ("lpep_pickup_datetime", "string", "lpep_pickup_datetime", "string"),
                                            ("lpep_dropoff_datetime", "string", "lpep_dropoff_datetime", "string"),
                                            ("store_and_fwd_flag", "string", "store_and_fwd_flag", "string"),
                                            ("ratecodeid", "long", "ratecodeid", "long"),
                                            ("pulocationid", "long", "pulocationid", "long"),
                                            ("dolocationid", "long", "dolocationid", "long"),
                                            ("passenger_count", "long", "passenger_count", "long"),
                                            ("trip_distance", "double", "trip_distance", "double"),
                                            ("fare_amount", "double", "fare_amount", "double"),
                                            ("extra", "double", "extra", "double"),
                                            ("mta_tax", "double", "mta_tax", "double"),
                                            ("tip_amount", "double", "tip_amount", "double"),
                                            ("tolls_amount", "double", "tolls_amount", "double"),
                                            ("ehail_fee", "string", "ehail_fee", "string"),
                                            ("improvement_surcharge", "double", "improvement_surcharge", "double"),
                                            ("total_amount", "double", "total_amount", "double"),
                                            ("payment_type", "long", "payment_type", "long"),
                                            ("trip_type", "long", "trip_type", "long")
                                            ], 
                                    transformation_ctx = "applymapping1")
logger.info("After ApplyMapping: " + correlation_id)

# Resolve choice conflicts, such as handling columns with multiple data types
# When choice is set to "make_struct", it means that the transformation will attempt to create a nested structure for the conflicting columns.
# After the ResolveChoice transformation with choice="make_struct", you may find new columns in your dynamic frame representing the conflicting data in a structured format.
resolvechoice2 = ResolveChoice.apply(frame = applymapping1, choice = "make_struct", transformation_ctx = "resolvechoice2")
logger.info("After ResolveChoice: " + correlation_id)

# Drop any fields that contain null values
# The DropNullFields transformation in AWS Glue is used to remove records (rows) from a dynamic frame where all specified fields (columns) have null values. If there is at least one non-null value in any of the specified fields for a given record, that record is retained in the dynamic frame.
dropnullfields3 = DropNullFields.apply(frame = resolvechoice2, transformation_ctx = "dropnullfields3")
logger.info("After DropNullFields: " + correlation_id)

# Write the transformed data to an S3 bucket in Parquet format
datasink4 = glueContext.write_dynamic_frame.from_options(frame = dropnullfields3, connection_type = "s3", connection_options = {"path": f"s3://{s3_bucket}/data/transformed/green"}, format = "parquet", transformation_ctx = "datasink4")
logger.info("After write_dynamic_frame.from_options: " + correlation_id)

job.commit()