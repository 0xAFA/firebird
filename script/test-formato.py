from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

model_path = './models/transformers/' 
model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
print("Transformer cargado")
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
print("Tokenizer cargado")
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)


def makecalc():

    data = ["me encanta la tarta de queso de este hotel", "ldnsfklsdnf"]
    print("Analizando peticion ---- > ", data)
    results = classifier(data)
    print("Resultados para peticion ---- > ", results)        

makecalc()

# Los resultados son una lista de diccionarios, aunque sólo hayamos pedido uno

# Para una petición: [{'label': '5 stars', 'score': 0.7727131247520447}]
# Para n peticiones:  [{'label': '5 stars', 'score': 0.7727131247520447}, {'label': '3 stars', 'score': 0.2624354064464569}]