import os
from dotenv import load_dotenv
#azure.ai.textanalytics is SDK for Azure AI Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential 

#Load environment variables from .env file
load_dotenv()#if override="true", override existing environment variables with values from local .env file
endpoint = os.getenv("LANGUAGE_ENDPOINT")
key = os.getenv("LANGUAGE_KEY")

# Creating and Authenticate the client using your key and endpoint, this is a helper function to create the client
def authenticate_client():
    ta_credential = AzureKeyCredential(key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=endpoint, 
            credential=ta_credential)
    return text_analytics_client

client = authenticate_client()

# Definining Example method for detecting the language of text
def language_detection_example(client): #language detection example method defined by us 
    try:
        documents = ["Me encanta aprender sobre inteligencia artificial.", "Hello, how are you?" ] # can take multiple documents in a list but should be passed as a list of strings only cannot pass file or any other data type, only list of strings
        for doc in documents:
            response = client.detect_language(documents = [doc], country_hint = 'us')[0] #detect_language method of the client, country_hint is optional. 0 because we are passing one document, so we take the first response
            print("Language for document[{}]: ".format(documents.index(doc)), response.primary_language.name)#response.primary_language.name gives the name of the language detected but we can also get the iso6391_name and confidence_score
           
    except Exception as err:
        print("Encountered exception. {}".format(err))
language_detection_example(client)