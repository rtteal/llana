# Import necessary libraries
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader

# Load environment variables
load_dotenv()

# Load documents from a directory (you can change this path as needed)
documents = SimpleDirectoryReader("data").load_data()

from openai import OpenAI
import json

client = OpenAI()

# Function to generate questions and answers
def generate_qa(prompt, text, temperature=0.2):    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}],
        temperature=temperature,
    )
    
    print(response.choices[0].message.content)

    # Strip extraneous symbols from the response content
    content = response.choices[0].message.content.strip()
    
    # Remove potential JSON code block markers
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1]
    if content.endswith('```'):
        content = content.rsplit('\n', 1)[0]
    content = content.strip()
    
    # Attempt to parse the cleaned content as JSON
    try:
        parsed_content = json.loads(content.strip())
        return parsed_content
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON. Raw content:")
        print(content)
        return []

factual_prompt = """
You are an expert educational content creator tasked with generating factual questions and answers based on the following document excerpt. These questions should focus on retrieving specific details, figures, definitions, and key facts from the text.

Instructions:

- Generate **5** factual questions, each with a corresponding **expected_output**.
- Ensure all questions are directly related to the document excerpt.
- Present the output in the following structured JSON format:

[
  {
    "question": "Why are researchers shifting to smaller, locally-run AI models on personal computers?",
    "expected_output": "For privacy (keeping sensitive data local), cost savings (no cloud subscriptions), reproducibility (consistent outputs), and customization (tailoring models to specific needs)."
  },
  {
    "question": "What advancements enable small AI models to run efficiently on consumer hardware, and what tools assist this process?",
    "expected_output": "Advancements in training techniques (using rich, reasoning-focused datasets) and open-source development have made smaller models efficient. Tools like Ollama, GPT4All, and Llamafile help users run AI models locally."
  }
]
"""

# Generate dataset
import os
import json

dataset_file = 'lex_fridman_qa_dataset.json'

if os.path.exists(dataset_file):
    # Load dataset from local file if it exists
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
else:
    # Generate dataset if local file doesn't exist
    dataset = []
    for doc in documents:
        qa_pairs = generate_qa(factual_prompt, doc.text, temperature=0.2)
        dataset.extend(qa_pairs)
    
    # Write dataset to local file
    with open(dataset_file, 'w') as f:
        json.dump(dataset, f)


from langfuse import Langfuse
langfuse = Langfuse()

dataset_name = "lex_fridman_qa_pairs"
langfuse.create_dataset(name=dataset_name);

for item in dataset:
  langfuse.create_dataset_item(
      dataset_name=dataset_name,
      input=item["question"],
      expected_output=item["expected_output"]
)
