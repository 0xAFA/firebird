# -----------------------------------------------------------------------------
# Importar librerías y credenciales
# -----------------------------------------------------------------------------

try:
    import tweepy
    from firebase_admin import credentials, firestore, initialize_app
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
except ImportError:
    raise ImportError("La aplicación requiere las librerías tweepy, firebase_admin y transformers.")    

try:
    import keys
except ImportError:
    raise ImportError("No se encuentra el archivo 'keys.py' con las credenciales de la API de Twitter.")

import logging
import datetime, os


# -----------------------------------------------------------------------------
# Descargar modelo (sólo si no se ha descargado previamente)
# -----------------------------------------------------------------------------

model_path = 'models/transformers/' 

if not os.path.exists('./models/transformers'):
    
    model_name = "nlptown/bert-base-multilingual-uncased-sentiment"

    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
    classifier.save_pretrained(model_path)

    logging.INFO("Modelo descargado.")

# -----------------------------------------------------------------------------
# Inicializar servicios
# -----------------------------------------------------------------------------

logging.INFO("Inicializando servicios...")

# Firestore
cred = credentials.Certificate('service-acc-key.json')
initialize_app(cred)
db = firestore.client()
logging.INFO("Firestore inicializado.")

# Tweepy
client = tweepy.Client(bearer_token=keys.bearer, access_token=keys.access_token, access_token_secret=keys.access_token_secret)
logging.INFO("Tweepy inicializado.")

# Clasificador
model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
classifier = pipeline('sentiment-analysis', model=model, tokenizer=tokenizer)
logging.INFO("Modelo NLP inicializado.")

currentTime = datetime.datetime.now()
currentDay = datetime.datetime(currentTime.year, currentTime.month, currentTime.day)

# -----------------------------------------------------------------------------
# Realizar análisis
# -----------------------------------------------------------------------------

# Cargar lista de colecciones
# to_dict nos da el documento y sus campos, pero no las sub-colecciones
campaigns = db.collection('campaigns').stream()

for doc in campaigns:

    campaign = doc.to_dict()

    # Ejemplo de formato:
    # Campaign atleti: 
    # {'track': '#atleti', 
    # 'isActive': True, 
    # 'tweet_limit': 1000, 
    # 'duration': 100, 
    # 'start': DatetimeWithNanoseconds(2022, 4, 19, 22, 0, tzinfo=datetime.timezone.utc)}

    if campaign['isActive']:

        # Comprobar que la campaña sigue estando activa
        # En caso contrario, marcarla como inactiva y pasar a la siguiente

        if campaign['start'] + datetime.timedelta(days = campaign['duration']) > datetime.datetime.now():
            doc.update({'isActive': False})
            continue

        query = campaign['track']
        limit = campaign['tweet_limit']

        # Obtener los tweets del último día, analizarlos, y subir los resultados

        # TODO: comprobar que los datos correspondientes a este día no están ya en Firestore

        # La lista completa de tweets es:
        tweets = tweepy.Paginator(client.search_recent_tweets, query=query, max_results=limit, start=currentDay).flatten(limit=limit)

        # TODO: Añadir información de localización a cada tweet, para poder sacar el mapa

        # Es más eficiente pasárselos todos de golpe a la pipeline
        results = classifier(tweets)

        # Por último, contamos los resultados

        (countPos, countNeg, countNeut) = (0, 0, 0)

        for result in results:
            score = int(result.label[0])        # label = '5 stars', p.ej.; el [0] es el número
            if score > 3:
                countPos += 1	
            elif score < 3:
                countNeg += 1
            else:
                countNeut += 1

        # TODO: multiplicar por tweet_counts si tweet_counts > limit
        # (usar API tweetCounts de tweepy)

        print("f Resultados del análisis para la campaña {query}: {countPos} positivos, {countNeg} negativos, {countNeut} neutros.")
        # TODO: Subir resultados a Firestore



            
