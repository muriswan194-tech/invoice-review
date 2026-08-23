import os

from dotenv import load_dotenv
from openai import OpenAI

# 1. Load local environment variables for this smoke test.
load_dotenv()
endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]

# 2. Foundry project endpoints use the OpenAI v1 API surface.
client = OpenAI(base_url=endpoint, api_key=api_key)

# 3. Execute a minimal request to verify the deployment and credentials.
response = client.chat.completions.create(
    model=deployment_name,
    messages=[{"role": "user", "content": "What is the capital of France?"}]
)

print(f"Answer: {response.choices[0].message.content}")
