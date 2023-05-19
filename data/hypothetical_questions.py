from transformers import pipeline

# MODEL_ID = "declare-lab/flan-alpaca-gpt4-xl"
MODEL_ID = "declare-lab/flan-alpaca-xxl"

prompt = "Write an email about an alpaca that likes flan"
model = pipeline(model=MODEL_ID)
model(prompt, max_length=128, do_sample=True)