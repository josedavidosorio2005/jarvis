import sys
import argparse
from collections import deque
import queue
import socket
import sounddevice as sd
import numpy as np
import speech_recognition as sr

q = queue.Queue()
def callback(indata, frames, time, status):
    q.put(indata.copy())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--culture", default="es-ES")
    parser.add_argument("--threshold", type=float, default=0.0)
    args = parser.parse_args()
    socket.setdefaulttimeout(8)

    print(f"__JARVIS_READY__{args.culture}", flush=True)
    recognizer = sr.Recognizer()
    samplerate = 16000
    blocksize = 4000
    min_threshold = args.threshold or 0.006
    noise_floor = min_threshold / 3
    pre_roll = deque(maxlen=4)
    
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
            threshold = max(min_threshold, noise_floor * 3.0)
            
            if not recording:
                pre_roll.append(chunk)
                noise_floor = (noise_floor * 0.96) + (rms * 0.04)
                if rms > threshold:
                    recording = True
                    audio_buffer.extend(pre_roll)
                    silence_chunks = 0
            else:
                audio_buffer.append(chunk)
                if rms < threshold:
                    silence_chunks += 1
                    # 4000 frames @ 16000Hz = 0.25s per chunk. 4 chunks = 1 second
                    if silence_chunks > 4:
                        break
                else:
                    silence_chunks = 0
        
        if len(audio_buffer) < 3:  # Too short to be words
            continue
            
        # Audio recorded, process it
        audio_data = np.concatenate(audio_buffer)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        audio_obj = sr.AudioData(audio_int16.tobytes(), samplerate, 2)
        
        try:
            text = recognizer.recognize_google(audio_obj, language=args.culture)
            if text:
                print(text, flush=True)
        except sr.UnknownValueError:
            pass
        except Exception as e:
            pass
        finally:
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

if __name__ == "__main__":
    main()
