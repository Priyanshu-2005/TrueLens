from transformers import pipeline

models = [
    "roberta-base-openai-detector",
    "Hello-SimpleAI/chatgpt-detector-roberta",
]

text = "In recent years, the rapid advancement of artificial intelligence has transformed various sectors, leading to significant changes in how we live and work."

for model in models:
    try:
        pipe = pipeline("text-classification", model=model, truncation=True, max_length=512)
        print(f"Model: {model}")
        print(pipe(text))
    except Exception as e:
        print(f"Error loading {model}: {e}")

