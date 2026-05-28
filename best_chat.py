import streamlit as st
import json, os, uuid, requests
from datetime import datetime
from PIL import Image, ImageFile
from streamlit_mic_recorder import mic_recorder
from streamlit_autorefresh import st_autorefresh # Новая библиотека

ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- ТВОИ ДАННЫЕ (ВСТАВЬ СВОИ КЛЮЧИ ТУТ) ---
SUPABASE_URL = "ЗДЕСЬ_ТВОЙ_URL"
SUPABASE_KEY = "ЗДЕСЬ_ТВОЙ_KEY_ANON_PUBLIC"

st.set_page_config(page_title="Mallerron Messenger 22.0", layout="wide")

# АВТООБНОВЛЕНИЕ: Чат будет сам обновляться каждые 5 секунд
st_autorefresh(interval=5000, key="datarefresh")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# --- ФУНКЦИИ БАЗЫ ДАННЫХ ---
def save_msg_to_db(gid, uid, name, text=None, f_path=None, m_type="text"):
    url = f"{SUPABASE_URL}/rest/v1/messages"
    data = {"gid": gid, "uid": uid, "name": name, "text": text, "file_path": f_path, "msg_type": m_type}
    try: requests.post(url, headers=HEADERS, json=data)
    except: pass

def load_msgs_from_db(gid):
    url = f"{SUPABASE_URL}/rest/v1/messages?select=*&gid=eq.{gid}&order=created_at.desc"
    try:
        r = requests.get(url, headers=HEADERS)
        return r.json()
    except: return []

def delete_msg_from_db(m_id):
    url = f"{SUPABASE_URL}/rest/v1/messages?id=eq.{m_id}"
    requests.delete(url, headers=HEADERS)

# Аккаунты
ACCOUNTS = {
    "mallerron": ["20142014", "Mallerron"],
    "leha": ["72632", "Лиха чичиниц"],
    "mertbers": ["26321", "MertBers"],
    "usman": ["83392", "Усман"],
    "tamerlan": ["73641", "Тамерлан"],
    "fedya": ["03924", "Федя"]
}

if "user_id" not in st.session_state: st.session_state.user_id = None

# --- ИНТЕРФЕЙС ---
if st.session_state.user_id is None:
    st.title("🚀 Mallerron Messenger")
    u = st.text_input("Логин").lower().strip()
    p = st.text_input("Пароль", type="password")
    if st.button("ВОЙТИ"):
        if u in ACCOUNTS and ACCOUNTS[u][0] == p:
            st.session_state.user_id = u
            st.rerun()
        else: st.error("Неверно!")
else:
    my_id = st.session_state.user_id
    my_name = ACCOUNTS[my_id][1]
    is_admin = (my_id == "mallerron")

    with st.sidebar:
        st.header(f"{'👑' if is_admin else '👤'} {my_name}")
        ava_p = f"avatars/{my_id}.png"
        if os.path.exists(ava_p): st.image(ava_p, width=120)
        
        with st.expander("📷 Профиль"):
            up_a = st.file_uploader("Сменить фото", type=["jpg", "png"])
            if st.button("Сохранить"):
                if up_a:
                    if not os.path.exists("avatars"): os.makedirs("avatars")
                    Image.open(up_a).save(ava_p); st.rerun()
            st.button("🚪 Выйти", on_click=lambda: st.session_state.update({"user_id": None}))

        st.divider()
        friends = {k: v[1] for k, v in ACCOUNTS.items() if k != my_id}
        # Загрузка групп (упрощенно)
        cur_chat = st.selectbox("Куда зайти?", ["🌍 Общий чат"] + [f"🤝 ЛС: {n}" for n in friends.values()])
        
        if "ЛС: " in cur_chat:
            f_name = cur_chat.replace("🤝 ЛС: ", "")
            f_id = [k for k, v in friends.items() if v == f_name][0]
            gid = f"dm_{min(my_id, f_id)}_{max(my_id, f_id)}"
        else:
            gid = "gen"

        st.divider()
        audio = mic_recorder(start_prompt="🎙️ Голос", stop_prompt="🛑 Стоп", key='voice')
        if audio and st.button("✅ Отправить ГС"):
            path = f"media/v_{uuid.uuid4()}.wav"
            if not os.path.exists("media"): os.makedirs(media)
            with open(path, "wb") as f: f.write(audio['bytes'])
            save_msg_to_db(gid, my_id, my_name, f_path=path, m_type="audio")
            st.rerun()

    st.subheader(f"Чат: {cur_chat}")
    
    msgs = load_msgs_from_db(gid)
    for m in msgs:
        with st.chat_message(m["name"], avatar=f"avatars/{m['uid']}.png" if os.path.exists(f"avatars/{m['uid']}.png") else None):
            col_msg, col_del = st.columns([12, 1])
            with col_msg:
                st.write(f"**{m['name']}** <small>{m['created_at'][11:16]}</small>", unsafe_allow_html=True)
                if m.get("text"): st.write(m["text"])
                fp = m.get("file_path", "")
                if fp and os.path.exists(fp):
                    if m["msg_type"] == "img": st.image(fp, width=300)
                    if m["msg_type"] == "vid": st.video(fp)
                    if m["msg_type"] == "audio": st.audio(fp)
            with col_del:
                if is_admin or m["uid"] == my_id:
                    if st.button("🗑️", key=f"d_{m['id']}"):
                        delete_msg_from_db(m["id"])
                        st.rerun()

    txt = st.chat_input("Напиши сообщение...")
    if txt:
        save_msg_to_db(gid, my_id, my_name, text=txt)
        st.rerun()