import os

os.environ.setdefault("SUPPORT_JOBS_QUEUE_URL", "https://example.com/support-jobs")
os.environ.setdefault("BEDROCK_MODEL_ID", "amazon.nova-micro-v1:0")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")
