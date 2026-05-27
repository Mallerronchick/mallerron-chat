import streamlit as st
import json, os, uuid
from datetime import datetime
from PIL import Image, ImageFile
from streamlit_mic_recorder import mic_recorder

ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- ВЕРСИЯ 17.0 ---
st.set_page_config(page_title="Mallerron Messenger", layout="wide")

# Стиль Телеграма (Исправлен цвет меню)
st.markdown("""
    <style>
    [data-testid="stVideo"] { border-radius: 50%; width: 200px !important; height: 200px !important; object-fit: cover; border: 3px solid #00E676; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    section[data-testid="stSidebar"] { min-width: 350px !important; }
    </style>
    """, unsafe_allow_html=True)

# Папки
for f in ["avatars", "media", "storage"]:
    if not os.path.exists(f): os.makedirs(f)

# База аккаунтов
ACCOUNTS = {
    "mallerron": ["20142014", "Mallerron"],
    "leha": ["leha777", "Лиха чичиниц"],
    "mertbers": ["tema01", "MertBers"],
    "usman": ["usman77", "Усман"],
    "tamerlan": ["tamerlan1", "Тамерлан"],
    "fedya": ["fedya777", "Федя"]
}

def load_j(n, d):
    p = f"storage/{n}.json"
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f: return json.load(f)
        except: return d
    return d

def save_j(n, d):
    with open(f"storage/{n}.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

if "all_msgs" not in st.session_state: st.session_state.all_msgs = load_j("msgs", [])

# Инициализация и проверка участников Общего чата
if "groups" not in st.session_state: 
    st.session_state.groups = load_j("grps", [{"id": "gen", "name": "🌍 Общий чат", "members": list(ACCOUNTS.keys()), "creator": "system"}])

# СИНХРОНИЗАЦИЯ: Добавляем новых людей (Федю) в Общий чат, если их там нет
for g in st.session_state.groups:
    if g["id"] == "gen":
        for acc_id in ACCOUNTS.keys():
            if acc_id not in g["members"]:
                g["members"].append(acc_id)
save_j("grps", st.session_state.groups)

if "user_id" not in st.session_state: st.session_state.user_id = None

# --- ВХОД ---
if st.session_state.user_id is None:
    st.title("🚀 Mallerron Messenger")
    u = st.text_input("Логин").lower().strip()
    p = st.text_input("Пароль", type="password")
    if st.button("ВОЙТИ"):
        if u in ACCOUNTS and ACCOUNTS[u][0] == p:
            st.session_state.user_id = u
            st.rerun()
        else: st.error("Неверный логин или пароль")
else:
    my_id = st.session_state.user_id
    my_name = ACCOUNTS[my_id][1]
    is_admin = (my_id == "mallerron")

    # --- ЛЕВАЯ ПАНЕЛЬ (SIDEBAR) ---
    with st.sidebar:
        st.header(f"{'👑' if is_admin else '👤'} {my_name}")
        ava_p = f"avatars/{my_id}.png"
        if os.path.exists(ava_p): st.image(ava_p, width=120)
        
        with st.expander("📷 Профиль"):
            up_a = st.file_uploader("Сменить фото", type=["jpg", "png"], key="ava_up")
            if st.button("Сохранить фото"):
                if up_a: Image.open(up_a).save(ava_p); st.rerun()
            if st.button("🚪 Выйти"):
                st.session_state.user_id = None
                st.rerun()

        st.divider()
        st.subheader("💬 Мои чаты")
        friends = {k: v[1] for k, v in ACCOUNTS.items() if k != my_id}
        my_grps = [g for g in st.session_state.groups if my_id in g["members"]]
        chat_labels = [g["name"] for g in my_grps] + [f"🤝 ЛС: {n}" for n in friends.values()]
        sel_chat = st.selectbox("Перейти в чат:", chat_labels)
        
        if "🤝 ЛС: " in sel_chat:
            f_name = sel_chat.replace("🤝 ЛС: ", "")
            f_id = [k for k, v in friends.items() if v == f_name][0]
            cur_chat = f"dm_{min(my_id, f_id)}_{max(my_id, f_id)}"
        else:
            g_obj = next(g for g in my_grps if g["name"] == sel_chat)
            cur_chat = g_obj["id"]

        st.divider()
        st.subheader("🛠️ Инструменты")
        audio = mic_recorder(start_prompt="🎙️ Голос", stop_prompt="🛑 Стоп", key='voice')
        if audio and st.button("✅ Отправить ГС"):
            path = f"media/v_{uuid.uuid4()}.wav"
            with open(path, "wb") as f: f.write(audio['bytes'])
            m = {"mid": str(uuid.uuid4()), "gid": cur_chat, "uid": my_id, "name": my_name, "type": "audio", "file": path, "time": datetime.now().strftime("%H:%M")}
            st.session_state.all_msgs.append(m); save_j("msgs", st.session_state.all_msgs); st.rerun()

        with st.popover("📎 Файлы"):
            up_f = st.file_uploader("Фото/Видео", type=["jpg", "png", "mp4"])
            if st.button("🚀 Отправить"):
                if up_f:
                    tp = "img" if up_f.type.startswith("image") else "vid"
                    path = f"media/{uuid.uuid4()}.{'png' if tp=='img' else 'mp4'}"
                    if tp == "img": Image.open(up_f).save(path)
                    else: 
                        with open(path, "wb") as f: f.write(up_f.read())
                    m = {"mid": str(uuid.uuid4()), "gid": cur_chat, "uid": my_id, "name": my_name, "type": tp, "file": path, "time": datetime.now().strftime("%H:%M")}
                    st.session_state.all_msgs.append(m); save_j("msgs", st.session_state.all_msgs); st.rerun()

        st.divider()
        with st.expander("👥 Группы / Настройки"):
            gn = st.text_input("Имя группы")
            ms = st.multiselect("Участники", list(friends.values()))
            if st.button("Создать группу"):
                if gn:
                    mids = [my_id] + [k for k, v in friends.items() if v in ms]
                    new_g = {"id": f"g_{uuid.uuid4().hex}", "name": f"👥 {gn}", "members": mids, "creator": my_id}
                    st.session_state.groups.append(new_g); save_j("grps", st.session_state.groups); st.rerun()
            st.write("---")
            cur_g_obj = next((g for g in st.session_state.groups if g["id"] == cur_chat), None)
            if is_admin or (cur_g_obj and cur_g_obj.get("creator") == my_id):
                if st.button("🧹 Очистить чат"):
                    st.session_state.all_msgs = [m for m in st.session_state.all_msgs if m.get("gid") != cur_chat]
                    save_j("msgs", st.session_state.all_msgs); st.rerun()
                if cur_chat.startswith("g_") and cur_chat != "gen":
                    if st.button("🗑️ Удалить группу"):
                        st.session_state.groups = [g for g in st.session_state.groups if g["id"] != cur_chat]
                        save_j("grps", st.session_state.groups); st.rerun()

    # --- ЧАТ ---
    st.subheader(sel_chat)
    for m in reversed(st.session_state.all_msgs):
        if m.get("gid") == cur_chat:
            u_uid = m.get("uid", "unknown")
            with st.chat_message(m["name"], avatar=f"avatars/{u_uid}.png" if os.path.exists(f"avatars/{u_uid}.png") else None):
                c_txt, c_del = st.columns([12, 1])
                with c_txt:
                    st.write(f"**{m['name']}** <small style='color:gray'>{m['time']}</small>", unsafe_allow_html=True)
                    if m.get("text"): st.write(m["text"])
                    fp = m.get("file", "")
                    if fp and os.path.exists(fp):
                        if m["type"] == "img": st.image(fp, width=300)
                        if m["type"] == "vid": st.video(fp)
                        if m["type"] == "audio": st.audio(fp)
                with c_del:
                    if is_admin or u_uid == my_id:
                        if st.button("🗑️", key=f"d_{m['mid']}"):
                            st.session_state.all_msgs = [msg for msg in st.session_state.all_msgs if msg["mid"] != m["mid"]]
                            save_j("msgs", st.session_state.all_msgs); st.rerun()

    txt = st.chat_input("Напиши сообщение...")
    if txt:
        m = {"mid": str(uuid.uuid4()), "gid": cur_chat, "uid": my_id, "name": my_name, "text": txt, "type": "text", "time": datetime.now().strftime("%H:%M")}
        st.session_state.all_msgs.append(m); save_j("msgs", st.session_state.all_msgs); st.rerun()