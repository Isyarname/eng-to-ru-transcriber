from eng_to_ru_transcriber import Transcriber

# Заменяем только "docker".
# Слов "dockerizer" и "dockerizing" в базовом словаре нет,
# поэтому движок разобьет их на корень + суффикс.
custom_vocabulary = {
    "docker": "докер",
}

text = "The dockerizer is dockerizing the docker image."

print("Без словаря:")
t1 = Transcriber()
print(t1.transcribe(text))

print("\nС кастомным словарем (только 'docker'):")
t2 = Transcriber(custom_vocabulary=custom_vocabulary)
print(t2.transcribe(text))
