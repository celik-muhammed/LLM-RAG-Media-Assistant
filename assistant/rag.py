import os
import json
from time import time

import logging
# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# ---------------- Config ----------------
from config import SETTINGS

import ingest
index = ingest.load_index()


# ---------------- OpenAI ----------------
from openai import OpenAI

if SETTINGS.LLM_PROVIDER in ['OLLAMA', 'HF']:
    client = OpenAI(
        base_url=SETTINGS.BASE_URL,  # Ollama API endpoint
        api_key=SETTINGS.API_KEY,  # dummy key (ignored by Ollama)
    )
else:
    client = OpenAI(api_key=SETTINGS.API_KEY)


def search(query):
    boost = {'intent': 0.022894885883346205,
        'question': 5.120311766582832,
        'response': 5.035355456071596,
        'category': 9.847893877170346}

    results = index.search(
        query=query,
        filter_dict={'category': 'CONTENT'},
        boost_dict=boost,
        num_results=5
    )

    return results


PROMPT_TEMPLATE = """
You are a customer support assistant specialized in the Media domain.
Your task is to answer the QUESTION strictly using the information provided in the CONTEXT.

Rules of conduct:
1. Only use facts explicitly present in the CONTEXT. Do not rely on external knowledge.
2. If the CONTEXT contains partial information, base your answer only on what is given.
3. If the CONTEXT does not contain the required information, respond exactly with:
   "I don’t have that information."
4. Keep answers clear, concise, and factual. Avoid speculation, assumptions, or subjective language.
5. Do not rephrase or fabricate details not present in the CONTEXT.
6. Do not merge or infer facts across unrelated sections of the CONTEXT unless explicitly stated.
7. Preserve numerical values, names, and terminology exactly as they appear in the CONTEXT.
8. Do not output meta-comments about your limitations or process (e.g., “As an AI…”).

QUESTION: {instruction}

CONTEXT: '''
{context}
'''
""".strip()
def build_prompt(query, search_results):
    context = ""
    for doc in search_results:
        context += (
            f"intent: {doc['intent']}\n"
            f"question: {doc['question']}\n"
            f"answer: {doc['response']}\n\n"
        )

    # Add to template instruction and context
    prompt = PROMPT_TEMPLATE.format(instruction=query, context=context).strip()
    return prompt


def llm(prompt):
    response = client.chat.completions.create(
        # model='gpt-4o-mini',  # OpenAI
        # model="gpt-oss:20b",   # Ollama "llama3" or any model available in your Ollama
        model=SETTINGS.MODEL_CHAT,  # huggingface
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


EVAL_PROMPT_TEMPLATE = """
You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
Your task is to assess the **relevance** of the generated answer to the given question.

Evaluation Guidelines:
1. Judge only on relevance between the QUESTION and the GENERATED ANSWER.
2. Ignore style, grammar, tone, and fluency. They are not part of this evaluation.
3. Choose exactly one of the following labels:
   - "NON_RELEVANT": The answer does not address the question at all.
   - "PARTLY_RELEVANT": The answer addresses the question partially OR mixes relevant and irrelevant content.
   - "RELEVANT": The answer fully and directly answers the question with no irrelevant content.
4. Provide a short, factual explanation (maximum 2 sentences).
5. The output must be strictly valid JSON, without code fences, without extra text, and without additional commentary.

Evaluation Data:
- Question: {question}
- Generated Answer: '''
{answer_llm}
'''

Output format:
{{
  "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
  "Explanation": "[Your brief explanation here]"
}}
""".strip()
def evaluate_relevance(question, answer):
    prompt = EVAL_PROMPT_TEMPLATE.format(question=question, answer=answer)
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
        "model_used": SETTINGS.MODEL_CHAT,
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
