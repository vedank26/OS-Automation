import speech_recognition as sr

def listen():
    """Full listen for main commands"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening for command...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
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
            print(f"⚠️ An unexpected error occurred: {e}")
            return None


def listen_short():
    """Short listen for number selection — faster, captures single words"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\n🎤 Listening for selection...")
        recognizer.adjust_for_ambient_noise(source, duration=0.2)  # shorter noise adjust
        
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=3)  # ✅ short limit
            print("🔊 Processing selection...")
            command = recognizer.recognize_google(audio)
            return command
            
        except sr.WaitTimeoutError:
            print("⏳ No selection heard.")
            return None
        except sr.UnknownValueError:
            print("❓ Couldn't understand. Try saying 'play 1' or 'first'")
            return None
        except sr.RequestError as e:
            print(f"🛑 Service error; {e}")
            return None
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
            return None