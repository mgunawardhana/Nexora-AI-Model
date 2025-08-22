# project_root/huggingface/question_answering.py

from transformers import pipeline

def get_question_answer(question: str, context: str):
    """
    Answers a question based on a given context using a Hugging Face model.

    Args:
        question (str): The question to be answered.
        context (str): The context to find the answer from.

    Returns:
        dict: A dictionary containing the answer.
    """
    pipe = pipeline("question-answering", model="distilbert/distilbert-base-cased-distilled-squad")
    result = pipe(question=question, context=context)
    return result