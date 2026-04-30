import sys
import queue
import sounddevice as sd
import numpy as np
import speech_recognition as sr

q = queue.Queue()
def callback(indata, frames, time, status):
    q.put(indata.copy())

def main():
    print("__JARVIS_READY__es-ES", flush=True)
    recognizer = sr.Recognizer()
    samplerate = 16000
    blocksize = 4000
    threshold = 0.015
    
    try:
        stream = sd.InputStream(samplerate=samplerate, blocksize=blocksize, channels=1, callback=callback, dtype='float32')
        stream.start()
    except Exception as e:
        print("__JARVIS_MIC_ERROR__", flush=True)
        print(str(e), flush=True)
        return

    while True:
        audio_buffer = []
        recording = False
        silence_chunks = 0
        
        while True:
            chunk = q.get()
            rms = np.sqrt(np.mean(chunk**2))
            
            if not recording:
                if rms > threshold:
                    recording = True
                    audio_buffer.append(chunk)
            else:
                audio_buffer.append(chunk)
                if rms < threshold:
                    silence_chunks += 1
                    # 4000 frames @ 16000Hz = 0.25s per chunk. 6 chunks = 1.5 seconds
                    if silence_chunks > 6:
                        break
                else:
                    silence_chunks = 0
        
        if len(audio_buffer) < 4:  # Too short to be words
            continue
            
        # Audio recorded, process it
        audio_data = np.concatenate(audio_buffer)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        audio_obj = sr.AudioData(audio_int16.tobytes(), samplerate, 2)
        
        try:
            text = recognizer.recognize_google(audio_obj, language="es-ES")
            if text:
                print(text, flush=True)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
