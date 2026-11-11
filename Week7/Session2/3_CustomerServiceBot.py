from dotenv import load_dotenv
import os
import azure.cognitiveservices.speech as speechsdk

# -------------------------------------------------------
# Demo: TDAI Bank Customer Service Voice Bot
#
# Listens to the user via microphone (Speech-to-Text),
# detects intent, then responds with a synthesized voice
# (Text-to-Speech) using a neural Australian voice.
# -------------------------------------------------------
load_dotenv()
FOUNDRY_KEY = os.getenv("FOUNDRY_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION", "australiaeast")

# Simulated account balance (hardcoded for demo)
ACCOUNT_BALANCE = 1245.50


def create_speech_config():
    speech_config = speechsdk.SpeechConfig(subscription=FOUNDRY_KEY, region=SPEECH_REGION)
    # Australian English neural voice
    speech_config.speech_synthesis_voice_name = "en-AU-NatashaNeural"
    return speech_config


def listen(speech_config):
    """Listen via microphone and return the recognised text."""
    # No audio_config = use default microphone
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config) #this is the speech recognizer object that takes the speech config as input, and it is used to recognize the speech from the microphone

    print("Listening... (speak now)")
    result = recognizer.recognize_once_async().get()#this method takes the audio input and transcribes it to text, and it returns a result object that contains the transcribed text, and we are using .get() to get the result synchronously

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"  You said: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("  (no speech detected)")
    elif result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        print(f"  Recognition canceled: {details.reason}")
        if details.reason == speechsdk.CancellationReason.Error:
            print(f"  Error: {details.error_details}")
    return ""

#function to synthesize a response through the speakers using the speech config and message as input, and it is used to synthesize the speech from text
def speak(speech_config, message):
    """Synthesize a response through the speakers."""
    print(f"  Bot: {message}")
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)#this method takes the speech config as input and it is used to synthesize the speech from text
    result = synthesizer.speak_text_async(message).get()

    if result.reason == speechsdk.ResultReason.Canceled:
        details = result.cancellation_details
        print(f"  Synthesis canceled: {details.reason}")
        if details.reason == speechsdk.CancellationReason.Error:
            print(f"  Error: {details.error_details}")


def get_response(user_text):
    """
    Simple intent detection — check what the user is asking about
    and return the appropriate response.
    """
    text = user_text.lower()
#rule based intent detection, if the user asks about balance, it will return the account balance, if the user says hello, it will return a greeting message, if the user says goodbye, it will return a quit message, otherwise it will return a default message
    if any(word in text for word in ["balance", "how much", "money"]):
        dollars = int(ACCOUNT_BALANCE)
        cents = round((ACCOUNT_BALANCE - dollars) * 100)
        return (
            f"Your current balance is "
            f"{dollars:,} dollars and {cents:02d} cents."
        )

    if any(word in text for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "Hello! Welcome to TDAI Bank. How can I help you today?"

    if any(word in text for word in ["bye", "goodbye", "exit", "quit", "that's all"]):
        return "QUIT"

    return "I'm sorry, I didn't understand that. You can ask me about your balance or say goodbye to exit."


def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 50)
    print("   TDAI Bank Customer Service Bot")
    print("=" * 50)
    print("Say 'What's my balance?' or 'Hello' to start.")
    print("Say 'Goodbye' to exit.\n")

    speech_config = create_speech_config()

    # Greet the customer
    speak(speech_config, "Welcome to TDAI Bank. How can I help you today?") #converts the text to speech and plays it through the speakers using the speech config and message as input, and it is used to synthesize the speech from text

    while True:
        user_text = listen(speech_config) #this method takes the speech config as input and it is used to recognize the speech from the microphone, and it returns the recognized text

        if not user_text:
            continue

        response = get_response(user_text)#this method takes the recognized text as input and it is used to detect the intent of the user, and it returns the appropriate response based on the intent detected

        if response == "QUIT":
            speak(speech_config, "Thank you for calling TDAI Bank. Goodbye!")
            break

        speak(speech_config, response)
        print()


if __name__ == "__main__":
    main()
