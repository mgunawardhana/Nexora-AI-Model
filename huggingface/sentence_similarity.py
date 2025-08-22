# project_root/huggingface/sentence_similarity.py

import os
from huggingface_hub import InferenceClient


def get_sentence_similarity(source_sentence: str, sentences: list):
    """
    Calculates sentence similarity using Hugging Face Inference API.

    Args:
        source_sentence (str): The source sentence to compare against.
        sentences (list): A list of sentences to compare.

    Returns:
        dict: The similarity scores from the API.
    """
    client = InferenceClient(
        provider="hf-inference",
        api_key=os.environ.get("HF_TOKEN"),
    )

    payload = {
        "source_sentence": source_sentence,
        "sentences": sentences,
    }

    result = client.sentence_similarity(
        payload,
        model="shawhin/distilroberta-ai-job-embeddings",
    )

    return result