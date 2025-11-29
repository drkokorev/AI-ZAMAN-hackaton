from openai import OpenAI
import csv
import re
import json

API_KEY = "your api key"
INPUT_FILE = "dev_inputs.tsv"
OUTPUT_FILE = "inputs_updated.tsv"

client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")


# --- Словарь мягких замен токсичных слов ---
def load_replacements(path="replacements.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ——— Функция словарной замены ———
def apply_replacements(text):
    lowered = text.lower()
    for bad, good in replacements.items():
        lowered = re.sub(rf"\b{bad}\b", good, lowered)
    return lowered

replacements = load_replacements()
# ---- Создание диалоговой сессии ChatGPT ----
messages = [
    {
        "role": "system",
        "content": (
            "You are changing toxic Tatar sentences to neutral forms. "
            "Answer in one sentence only. "
            "No explanations, comments, formatting. "
            "Write only the factually neutral version."
        )
    }
]

def detoxify_with_chatgpt(sentence):
    messages.append({"role": "user", "content": sentence})

    response = client.chat.completions.create(
        model="gpt-5.1", # Changed model name from "gpt-4.1" to "deepseek-chat"
        messages=messages,
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()
    answer = answer.replace("\n", " ")

    messages.append({"role": "assistant", "content": answer})

    return answer


# ---- Основной цикл обработки файла ----
with open(INPUT_FILE, "r", encoding="utf-8") as f_in, \
     open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f_out:

    reader = csv.DictReader(f_in, delimiter="\t")
    fieldnames = reader.fieldnames

    if "tat_detox1" not in fieldnames:
        raise ValueError("В файле должен быть столбец 'tat_detox1'.")

    writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()

    for row in reader:
        toxic = row["tat_toxic"].strip()

        if toxic:
            # 1) локальная словарная замена
            preclean = apply_replacements(toxic)

            # 2) отправка в ChatGPT
            clean = detoxify_with_chatgpt(preclean)

            row["tat_detox1"] = clean
        else:
            row["tat_detox1"] = ""

        writer.writerow(row)

print("Готово! Файл сохранён как:", OUTPUT_FILE)
