import speech_recognition as sr
import time

def listen():
    """
    Listens to microphone input and converts speech to text using Google Speech Recognition.
    Returns the recognized text as a string, or None if nothing was understood or an error occurred.
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening for command...")
        # Adjust for ambient noise to improve accuracy
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            # timeout: how long to wait for speech to start
            # phrase_time_limit: maximum duration of the speech phrase
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
            print("🔊 Processing audio...")
            
            command = recognizer.recognize_google(audio)
            return command
            
        except sr.WaitTimeoutError:
            print("⏳ Listening timed out (no speech detected).")
            return None
        except sr.UnknownValueError:
            print("❓ Sorry, I couldn't understand the speech.")
            return None
        except sr.RequestError as e:
            print(f"🛑 Could not request results from service; {e}")
            return None
        except Exception as e:
            print(f"⚠️ An unexpected error occurred in speech_engine: {e}")
            return None
