import os
import json
import logging
from time import time

import ingest

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# ---------------- Config ----------------
index = ingest.load_index()
BASE_URL=os.getenv("OLLAMA_URL", f"http://{('ollama' if os.path.exists('/.dockerenv') else 'localhost')}:11434/v1")
logger.info(BASE_URL)
API_KEY=os.getenv('OPENAI_API_KEY', 'ollama')
LLM_MODEL=os.getenv("LLM_MODEL", "openai/gpt-oss-120b:fireworks-ai")

# ---------------- OpenAI ----------------
from openai import OpenAI

if API_KEY == 'ollama':
    client = OpenAI(
        base_url=BASE_URL,  # Ollama API endpoint
        api_key=os.getenv('OPENAI_API_KEY', 'ollama'),  # dummy key (ignored by Ollama)
    )
else:
    client = OpenAI(api_key=API_KEY)


def search(query):
    boost = {
        'intent': 4.709344164326785,
        'question': 0.9312117423908761,
        'response': 5.71511647366386,
        'category': 9.689631225548114}

    results = index.search(
        query=query,
        filter_dict={'category': 'CONTENT'},
        boost_dict=boost,
        num_results=5
    )

    return results


def build_prompt(query, search_results):
    prompt_template = """
    You are a customer support assistant for the Media domain.
    Answer the QUESTION using only the information from CONTEXT.

    Rules:
    - Only use facts from CONTEXT.
    - Keep your answer clear, factual and concise.
    - Do not hallucinate or add outside knowledge.
    - Do not invent information not found in CONTEXT.
    - If CONTEXT doesn’t contain the answer, respond: "I don’t have that information."

    QUESTION: {instruction}

    CONTEXT:
    {context}
    """.strip()

    context = ""
    for doc in search_results:
        context += (
            f"intent: {doc['intent']}\n"
            f"question: {doc['question']}\n"
            f"answer: {doc['response']}\n\n"
        )

    # Add to template instruction and context
    prompt = prompt_template.format(instruction=query, context=context).strip()
    return prompt


def llm(prompt):
    response = client.chat.completions.create(
        # model='gpt-4o-mini',  # OpenAI
        # model="gpt-oss:20b",   # Ollama "llama3" or any model available in your Ollama
        model=LLM_MODEL,  # huggingface
        messages=[{"role": "user", "content": prompt}],
        # temperature=0.0
    )

    answer = response.choices[0].message.content

    token_stats = {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return answer, token_stats


evaluation_prompt_template = """
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
Your task is to judge the **relevance** of the generated answer to the given question.

Guidelines:
- Focus and analyze only on relevance the content and context of the generated answer in relation to the question, not style, grammar, or tone.
- Use exactly one of the following labels:
  - "NON_RELEVANT": The answer does not address the question.
  - "PARTLY_RELEVANT": The answer addresses the question partially or contains both correct and irrelevant parts.
  - "RELEVANT": The answer fully and directly addresses the question.
- Keep the explanation brief (1-2 sentences).
- Output valid parsable JSON without using code blocks only, no extra text.

Evaluation Data:

Question: {question}
Generated Answer: {answer}

Output format:

{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Provide a brief explanation for your evaluation]"
}}
""".strip()


def evaluate_relevance(question, answer):
    prompt = evaluation_prompt_template.format(question=question, answer=answer)
    evaluation, tokens = llm(prompt) #, model="gpt-4o-mini")

    try:
        json_eval = json.loads(evaluation)
        return json_eval, tokens
    except json.JSONDecodeError:
        result = {"Relevance": "UNKNOWN", "Explanation": "Failed to parse evaluation"}
        return result, tokens


def rag(query):

    t0 = time()

    search_results = search(query)
    prompt = build_prompt(query, search_results)
    answer, token_stats = llm(prompt)

    relevance, rel_token_stats = evaluate_relevance(query, answer)

    t1 = time()
    took = t1 - t0

    answer_data = {
        "answer": answer,
        # "model_used": "gpt-4o-mini",
        "model_used": os.getenv("LLM_MODEL", "openai/gpt-oss-120b:fireworks-ai"),
        "response_time": took,
        "relevance": relevance.get("Relevance", "UNKNOWN"),
        "relevance_explanation": relevance.get(
            "Explanation", "Failed to parse evaluation"
        ),
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "eval_prompt_tokens": rel_token_stats["prompt_tokens"],
        "eval_completion_tokens": rel_token_stats["completion_tokens"],
        "eval_total_tokens": rel_token_stats["total_tokens"],
    }

    return answer_data
