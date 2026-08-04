from types import SimpleNamespace

from src.functions.salute.handler import lambda_handler

response = lambda_handler({"name": "Gustavo"}, SimpleNamespace(aws_request_id="local-request-id"))
print(response)