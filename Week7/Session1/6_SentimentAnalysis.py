
import os
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()
language_endpoint = os.getenv("LANGUAGE_ENDPOINT")
language_key = os.getenv("LANGUAGE_KEY")

# Authenticate the client using your key and endpoint 
def authenticate_client():
    ta_credential = AzureKeyCredential(language_key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=language_endpoint, 
            credential=ta_credential)
    return text_analytics_client

client = authenticate_client()

# Example method for detecting sentiment and opinions in text 
def sentiment_analysis_with_opinion_mining_example(client):

    documents = [
        #"I often enjoy this movie, but I'm finding it boring now"
        #"I enjoy cooking and I like feeding people but I hate doing the dishes."
        "I love to learn new things and I enjoy learning about AI, but I hate doing the dishes."
    ]

    result = client.analyze_sentiment(documents, show_opinion_mining=True) #analyze_sentiment method of the client, show_opinion_mining is optional, if not provided it will be set to false by default
    doc_result = [doc for doc in result if not doc.is_error]

    positive_reviews = [doc for doc in doc_result if doc.sentiment == "positive"]
    negative_reviews = [doc for doc in doc_result if doc.sentiment == "negative"]

    positive_mined_opinions = []
    mixed_mined_opinions = []
    negative_mined_opinions = []

    for document in doc_result:
        print("Document Sentiment: {}".format(document.sentiment)) #this is the overall sentiment of the document, it can be positive, negative or neutral
        print("Overall scores: positive={0:.2f}; neutral={1:.2f}; negative={2:.2f} \n".format(
            document.confidence_scores.positive,
            document.confidence_scores.neutral,
            document.confidence_scores.negative,
        ))
        for sentence in document.sentences:
            print("Sentence: {}".format(sentence.text)) #this is the sentence text
            print("Sentence sentiment: {}".format(sentence.sentiment))#this is the sentence sentiment, it can be positive, negative or neutral
            print("Sentence score:\nPositive={0:.2f}\nNeutral={1:.2f}\nNegative={2:.2f}\n".format(
                sentence.confidence_scores.positive,
                sentence.confidence_scores.neutral,
                sentence.confidence_scores.negative,
            ))
            for mined_opinion in sentence.mined_opinions: #this is the mined opinion, it contains the target and assessments, target is the main opinionated phrase in the sentence, and assessments are the phrases that describe the target
                target = mined_opinion.target #target is the main opinionated phrase in the sentence, and assessments are the phrases that describe the target
                print("......'{}' target '{}'".format(target.sentiment, target.text))
                print("......Target score:\n......Positive={0:.2f}\n......Negative={1:.2f}\n".format(
                    target.confidence_scores.positive,
                    target.confidence_scores.negative,
                ))
                for assessment in mined_opinion.assessments:
                    print("......'{}' assessment '{}'".format(assessment.sentiment, assessment.text)) #this is the assessment phrase that describes the target, it can be positive, negative or neutral
                    print("......Assessment score:\n......Positive={0:.2f}\n......Negative={1:.2f}\n".format(
                        assessment.confidence_scores.positive,
                        assessment.confidence_scores.negative,
                    ))
            print("\n")
        print("\n")
          
sentiment_analysis_with_opinion_mining_example(client)