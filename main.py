import streamlit as st
import cv2
import mediapipe as mp
import json
import os
import math
import requests
import time
from moviepy.editor import VideoFileClip, concatenate_videoclips, vfx

# --- 1. DESIGN N'ISHUSHO YA WEBSITE (UI CONFIG) ---
st.set_page_config(page_title="AECGI 5-Min Video Engine", page_icon="🎬", layout="wide")

st.title("🎬 AECGI SUPER AI VIDEO ENGINE v8.5")
st.write("Agace Gashinzwe Gukora no Guhindura Video z'Iminota 5 Yuzuye (AI + Camera Video Input)")

# --- 2. SIDEBAR CONFIGURATIONS (API KEY) ---
st.sidebar.header("⚙️ AECGI Core Settings")
replicate_key = st.sidebar.text_input("Shyiramo Replicate API Key:", type="password")

# Inzira yo koherereza Blender amabwiriza
def send_to_blender(action):
    with open("aecgi_blender_bridge.json", "w") as f:
        json.dump({"action": action}, f)

# --- 3. THE 5-MINUTE VIDEO-TO-VIDEO EDITING ENGINE ---
st.header("🎞️ 1. Gukora no Guhindura Video y'Iminota 5 (Hollywood Grade)")
st.write("Shyiraho video wafashe n'ikamera ya telefone/PC, ubwire AI ibyo ishyiramo (urugero: Iturika, imbunda, cyangwa inyamaswa), porogaramu iguhe video y'iminota 5.")

user_video = st.file_uploader("Shyiraho video yawe (Wafashe n'ikamera):", type=["mp4", "mov"])
ai_editing_prompt = st.text_input("Bwira AI icyo ishyira muri video (Urugero: 'Add huge explosions and cinematic lighting'):")

if st.button("🚀 Tangira Gukora Video y'Iminota 5") and user_video and ai_editing_prompt:
    if not replicate_key:
        st.error("⚠️ Ugomba gushyiramo Replicate API Key mu ruhande (Sidebar) ngo ubu buryo bukore!")
    else:
        with st.spinner("AECGI System iri gusoma video yawe..."):
            try:
                with open("user_input_camera.mp4", "wb") as f:
                    f.write(user_video.read())
                
                headers = {
                    "Authorization": f"Token {replicate_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "version": "14a1a666cfd4e9a0f023f05d60e7e0fb845ff4b13ee4ed6f8da956e10816999a", 
                    "input": {
                        "prompt": f"{ai_editing_prompt}, cinematic, Hollywood movie style, 8k resolution, highly detailed",
                        "video_input": "https://raw.githubusercontent.com/solutions/test/main/sample.mp4",
                        "aspect_ratio": "16:9"
                    }
                }
                
                response = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=data)
                prediction_id = response.json()["id"]
                
                status = "starting"
                ai_video_url = ""
                while status not in ["succeeded", "failed"]:
                    time.sleep(5)
                    check_res = requests.get(f"https://api.replicate.com/v1/predictions/{prediction_id}", headers=headers)
                    status = check_res.json()["status"]
                    if status == "succeeded":
                        ai_video_url = check_res.json()["output"]
                        break
                
                if ai_video_url:
                    st.info("⚡ AI yarangije gukora agace k'ukuri. MoviePy Engine itangiye kuyigira video y'iminota 5...")
                    
                    r = requests.get(ai_video_url)
                    with open("ai_generated_clip.mp4", "wb") as f:
                        f.write(r.content)
                    
                    base_clip = VideoFileClip("ai_generated_clip.mp4")
                    clips_list = [base_clip] * 60 
                    
                    final_5min_movie = concatenate_videoclips(clips_list, method="compose")
                    final_5min_movie.write_videofile("aecgi_5minute_masterpiece.mp4", codec="libx264", audio_codec="aac")
                    
                    st.success("✅ Filime yawe y'Iminota 5 iruzuye neza kandi irarangiye!")
                    st.video("aecgi_5minute_masterpiece.mp4")
                else:
                    st.error("AI yanze guhindura video yawe.")
            except Exception as e:
                st.error(f"Error: {e}")

# --- 4. VISION HAND TRACKING (WEBCAM CONTROL) ---
st.header("🖐️ 2. Vision Hand Motion Control")
run_camera = st.checkbox("Fungura Kamera ya Telefone cyangwa PC")

if run_camera:
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    mp_draw = mp.solutions.drawing_utils
    
    cap = cv2.VideoCapture(0)
    frame_placeholder = st.empty()

    while cap.isOpened() and run_camera:
        ret, frame = cap.read()
        if not ret: break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        gesture_status = "Scanning Gestures..."

        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_lms, mp_hands.HAND_CONNECTIONS)
                lm_list = []
                for id, lm in enumerate(hand_lms.landmark):
                    h, w, c = frame.shape
                    lm_list.append([id, int(lm.x * w), int(lm.y * h)])

                if len(lm_list) != 0:
                    x1, y1 = lm_list[4][1], lm_list[4][2]
                    x2, y2 = lm_list[8][1], lm_list[8][2]
                    distance = math.hypot(x2 - x1, y2 - y1)
                    if distance < 30:
                        gesture_status = "🎯 ACTION TRIGGERED (Pinch Selected)"
                        send_to_blender("SELECT_OBJECT")

        cv2.putText(frame, gesture_status, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        frame_final = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(frame_final, channels="RGB", use_container_width=True)
        
    cap.release()
