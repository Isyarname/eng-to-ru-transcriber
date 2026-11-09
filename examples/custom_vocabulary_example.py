from eng_to_ru_transcriber import Transcriber

custom_vocabulary = {
    "python": "пайтон",
    "kubernetes": "ˌkjuːbəˈnɛtɪs"
}

t = Transcriber(custom_vocabulary=custom_vocabulary)
print(t.transcribe("I love Python and Kubernetes"))