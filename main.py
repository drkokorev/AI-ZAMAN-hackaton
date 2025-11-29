from openai import OpenAI
import csv
import re

API_KEY = "YOUR_API_KEY"
INPUT_FILE = "dev_inputs.tsv"
OUTPUT_FILE = "inputs_updated.tsv"

client = OpenAI(api_key="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", base_url="https://openrouter.ai/api/v1")


# --- Словарь мягких замен токсичных слов ---
BAD_TO_NEUTRAL = {
    "тиле": "ялгышучы",
    "тилә": "ялгышучы",
    "ахмак": "дөрес аңламаучы",
    "мәхлук": "начар кеше",
    "җүләр": "адашкан кеше",
    "надан": "тәҗрибәсез",
    "дурак": "ялгышучы",
    "тупас": "киресенчә сөйләүче",
    "пычрак": "начар",
    "хайван": "кеше",
    "терлек": "кеше",
    "дуңгыз": "кешеләр",
    "идиот": "ялгышучы",
    "дебил": "ялгышучы",
    "скотина": "начар кеше",
    "урод": "кеше",
    "кутак" : "әгъза",
    "кутакбаш" : "начарлык",
    "кут" : "арт",
    "жопа" : "арт",
    "бля" : "әй",
    "сука" : "явыз",
    "ангыра" : "тәҗрибәсез",
    "тиле" : "аңгырарак",
    "ахуел" : "шаккаттым",
    "охуел" : "аптырадым",
    "маржа" : "рус",
    "мал" : "кеше",
    "козёл" : "тупас",
    "дебил" : "аңсыз",
    "дурак" : "аңламаучан",
    "сволочь" : "явыз",
    "хуйня" : "бушлык",
    "бамбук" : "игътибарсыз",
    "тормоз" : "әкрен",
    "шакшы" : "ямьсез",
    "корт" : "сәер",
    "черек" : "зәгыйфь",
    "ятим" : "мескен",
    "шайтан" : "начар",
    "кәкре" : "туры",
    "сукыр" : "күрми",
    "саңгырау" : "ишетми",
    "сасы" : "начар",
    "әтәч" : "данбел",
    "пычрак" : "чиста түгел",
    "яртыакыл" : "аңсыз",
    "наглый" : "үзсүзле",
    "долбоёб" : "аңгыра",
    "тырнак" : "бәләкәй",
    }

# ——— Функция словарной замены ———
def apply_dictionary_replacement(text):
    lowered = text.lower()
    for bad, good in BAD_TO_NEUTRAL.items():
        lowered = re.sub(rf"\b{bad}\b", good, lowered)
    return lowered


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
            preclean = apply_dictionary_replacement(toxic)

            # 2) отправка в ChatGPT
            clean = detoxify_with_chatgpt(preclean)

            row["tat_detox1"] = clean
        else:
            row["tat_detox1"] = ""

        writer.writerow(row)

print("Готово! Файл сохранён как:", OUTPUT_FILE)
