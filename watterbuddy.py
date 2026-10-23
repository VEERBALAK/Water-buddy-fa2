import hashlib
import json
import os
from datetime import date, timedelta

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="WaterBuddy", page_icon="💧", layout="centered")

DONE_KEY = "waterbuddy_reminderSetupDone"
USERS_KEY = "waterbuddy_users"
PROFILE_KEY = "waterbuddy_profile"
HISTORY_KEY = "waterbuddy_history"
INTERVALS = [30, 45, 60, 90, 120]
DEFAULT_GOAL_ML = 2200
DEFAULT_GLASS_ML = 250
REMIND_FROM, REMIND_TO = "8:00", "22:00"
STORE_FILE = "waterbuddy_state.json"  # stands in for window.localStorage

PAGES = [("Home", "🏠"), ("Tips", "💡"), ("Board", "🏆"), ("Profile", "👤")]
LEVELS = [
    (0, "Sipper"),
    (5000, "Splasher"),
    (15000, "Wave Rider"),
    (40000, "Hydro Hero"),
    (100000, "Aqua Legend"),
]
TIPS = [
    ("🌅", "Start your day with a glass", "Drink a glass of water right after you wake up."),
    ("🍽️", "Drink before meals", "A glass before eating helps you stay on track."),
    ("📱", "Let reminders do the work", "Keep WaterBuddy open and sip when it nudges you."),
    ("🍋", "Make it tasty", "Add lemon, mint or cucumber if plain water gets boring."),
    ("🎒", "Keep a bottle nearby", "If it's within reach, you'll drink more."),
    ("🏃", "Drink more when active", "Add an extra glass when you exercise or it's hot."),
]

_HAS_DIALOG = hasattr(st, "dialog") or hasattr(st, "experimental_dialog")


# ---------- helpers ----------
def _html(s):
    # Strip leading spaces so Markdown never treats the HTML as a code block
    return "\n".join(line.strip() for line in s.splitlines())


def inject_css():
    st.markdown(
        _html(
            """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, .stApp, button, input { font-family: 'Space Grotesk', sans-serif !important; }
.stApp { background: #050b16; color: #e6f1ff; }
.stApp, .stApp label, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li,
.stApp [data-testid="stCaptionContainer"] { color: #e6f1ff !important; }
header[data-testid="stHeader"], footer, #MainMenu,
[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
.block-container { max-width: 460px !important; padding: 1.2rem 1rem 7rem !important; }

/* inputs */
input, textarea, [data-baseweb="select"] > div {
  background: #0b1626 !important; color: #e6f1ff !important; border-color: #17324d !important;
}
div[role="dialog"] { background: #08121f !important; border: 1px solid rgba(0,212,255,.35); }
button[role="tab"] { color: #8fa7c2 !important; }
button[role="tab"][aria-selected="true"] { color: #00d4ff !important; }

/* buttons: default = dark card, primary = neon cyan */
.stButton > button, .stFormSubmitButton > button {
  background: #0b1626; color: #cfe8ff; border: 1px solid #17324d;
  border-radius: 14px; font-weight: 600;
}
.stButton > button:hover { border-color: #00d4ff; color: #00d4ff; }
button[kind="primary"], button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
  background: #00d4ff !important; color: #04202b !important; border: none !important;
  box-shadow: 0 0 24px rgba(0,212,255,.35);
}
button[kind="primary"] p, button[data-testid="stBaseButton-primary"] p { color: #04202b !important; }

/* header */
.wb-head { display: flex; align-items: center; gap: 12px; }
.wb-logo {
  width: 54px; height: 54px; border-radius: 16px; background: #00d4ff;
  display: flex; align-items: center; justify-content: center; font-size: 26px;
  box-shadow: 0 0 22px rgba(0,212,255,.45);
}
.wb-title { font-size: 20px; font-weight: 700; color: #fff; line-height: 1.1; }
.wb-sub { font-size: 13px; color: #8fa7c2; display: flex; gap: 8px; align-items: center; margin-top: 3px; }
.wb-badge {
  border: 1px solid #e6d84a; color: #f5e960; border-radius: 999px;
  padding: 1px 9px; font-size: 12px; font-weight: 700;
}

/* main card */
.wb-card {
  position: relative; text-align: center; margin-top: 10px; padding: 26px 16px 22px;
  border: 1px solid rgba(0,212,255,.4); border-radius: 30px;
  background: linear-gradient(180deg, #07162a 0%, #050f1d 100%);
  box-shadow: 0 0 40px rgba(0,212,255,.12), inset 0 0 40px rgba(0,212,255,.04);
}
.wb-mascot { position: absolute; top: 18px; right: 20px; filter: drop-shadow(0 0 12px rgba(0,212,255,.6)); }
.wb-ring { position: relative; width: 310px; max-width: 100%; margin: 8px auto 14px; }
.wb-ring svg { width: 100%; height: auto; display: block; }
.wb-ring-text {
  position: absolute; inset: 0; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.wb-big { font-size: 52px; font-weight: 700; color: #fff; line-height: 1; }
.wb-big span { font-size: 22px; color: #8fa7c2; margin-left: 4px; }
.wb-of { font-size: 17px; color: #8fa7c2; margin-top: 8px; }
.wb-pct { font-size: 15px; color: #00d4ff; font-weight: 700; margin-top: 8px; letter-spacing: 2px; }
.wb-hey { font-size: 22px; font-weight: 700; color: #fff; margin-top: 6px; }
.wb-msg { font-size: 18px; font-weight: 600; color: #00d4ff; margin-top: 6px; }

.wb-remind { text-align: center; color: #8fa7c2; font-size: 14px; margin: 12px 0 14px; }

/* stat cards */
.wb-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.wb-stat {
  border: 1px solid #12304a; border-radius: 18px; background: #07142a;
  padding: 12px 6px; text-align: center;
}
.wb-stat .ic { font-size: 18px; }
.wb-stat b { display: block; color: #fff; font-size: 18px; margin-top: 2px; }
.wb-stat small { color: #8fa7c2; font-size: 11px; font-weight: 700; letter-spacing: 1px; }

/* list rows (tips / board) */
.wb-row {
  display: flex; align-items: center; gap: 12px; margin-bottom: 10px; padding: 12px 14px;
  border: 1px solid #12304a; border-radius: 18px; background: #07142a;
}
.wb-row .ic { font-size: 24px; }
.wb-row b { color: #fff; display: block; }
.wb-row span { color: #8fa7c2; font-size: 13px; }
.wb-row .end { margin-left: auto; color: #00d4ff; font-weight: 700; white-space: nowrap; }
.wb-h2 { font-size: 22px; font-weight: 700; color: #fff; margin: 6px 0 12px; }

/* bottom navigation */
.st-key-bottomnav {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 999;
  background: #07111f; border-top: 1px solid #12304a; padding: .4rem 0 .7rem;
}
.st-key-bottomnav > div { max-width: 460px; margin: 0 auto; padding: 0 .5rem; }
.st-key-bottomnav [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .2rem !important; }
.st-key-bottomnav [data-testid="stColumn"], .st-key-bottomnav [data-testid="column"] {
  min-width: 0 !important; flex: 1 1 0 !important; width: auto !important;
}
.st-key-bottomnav button, .st-key-bottomnav button[kind="primary"],
.st-key-bottomnav button[data-testid="stBaseButton-primary"] {
  background: transparent !important; border: none !important; box-shadow: none !important;
  color: #8fa7c2 !important; font-size: 13px; padding: .3rem 0;
}
.st-key-bottomnav button p { color: #8fa7c2 !important; font-size: 13px; }
.st-key-bottomnav button[kind="primary"] p,
.st-key-bottomnav button[data-testid="stBaseButton-primary"] p { color: #00d4ff !important; }

/* big Log Water button */
.st-key-logwater button { height: 66px; font-size: 20px; border-radius: 20px; }
.st-key-logwater button p { font-size: 20px; font-weight: 700; }
.st-key-soundbtn button { border-radius: 999px; width: 54px; height: 54px; padding: 0; }
</style>
"""
        ),
        unsafe_allow_html=True,
    )


def keyed_container(key):
    # container(key=...) needs a recent Streamlit; fall back to a plain container
    try:
        return st.container(key=key)
    except TypeError:
        return st.container()


# ---------- stand-ins for the imports used in the React version ----------

# window.localStorage
def _load_store():
    store = dict(st.session_state.get("_local_storage", {}))
    if not store and os.path.exists(STORE_FILE):
        try:
            with open(STORE_FILE, "r") as f:
                store = json.load(f)
        except (json.JSONDecodeError, OSError):
            store = {}
    return store


class local_storage:
    @staticmethod
    def get_item(key):
        return _load_store().get(key)

    @staticmethod
    def set_item(key, value):
        store = _load_store()
        store[key] = value
        st.session_state["_local_storage"] = store
        try:
            with open(STORE_FILE, "w") as f:
                json.dump(store, f)
        except OSError:
            pass  # file system not writable (e.g. in-browser sandbox)


# @/hooks/useReminders
def use_reminders():
    reminders = st.session_state.setdefault(
        "reminders", local_storage.get_item("waterbuddy_reminders") or {}
    )

    def update(changes):
        reminders.update(changes)
        local_storage.set_item("waterbuddy_reminders", reminders)

    return reminders, update


# @/lib/AuthContext  (demo auth: accounts are kept in local_storage)
def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def use_auth():
    user = st.session_state.get("user")
    is_loading_auth = False
    return user, is_loading_auth


def logout():
    st.session_state["user"] = None
    st.session_state["open"] = False
    st.session_state["askedFor"] = None
    st.session_state["tab"] = "Home"
    st.rerun()


# @/lib/sounds
class sounds:
    @staticmethod
    def blip():
        if not st.session_state.get("sound_on", True):
            return
        components.html(
            """
            <script>
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const o = ctx.createOscillator();
            const g = ctx.createGain();
            o.connect(g); g.connect(ctx.destination);
            o.frequency.value = 880; g.gain.value = 0.08;
            o.start(); o.stop(ctx.currentTime + 0.12);
            </script>
            """,
            height=0,
        )


def speak(text):
    if not st.session_state.get("sound_on", True):
        return
    safe = json.dumps(text)
    components.html(
        f"""
        <script>
        const u = new SpeechSynthesisUtterance({safe});
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
        </script>
        """,
        height=0,
    )


# Use st.dialog if this Streamlit version has it, otherwise fall back to an inline box
def _dialog(title):
    dlg = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)
    if dlg is not None:
        return dlg(title)

    def passthrough(fn):
        def wrapper(*args, **kwargs):
            with st.container(border=True):
                st.subheader(title)
                return fn(*args, **kwargs)
        return wrapper

    return passthrough


# ---------- Login page ----------
def LoginPage():
    st.title("WaterBuddy 💧")
    st.caption("Log in or create an account to continue.")

    users = local_storage.get_item(USERS_KEY) or {}
    login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Log in", type="primary", use_container_width=True
            )
        if submitted:
            uid = username.strip().lower()
            if uid in users and users[uid]["password"] == _hash(password):
                st.session_state["user"] = {"id": uid, "name": users[uid]["name"]}
                st.rerun()
            else:
                st.error("Wrong username or password.")

    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("Your name")
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            created = st.form_submit_button(
                "Create account", type="primary", use_container_width=True
            )
        if created:
            uid = new_username.strip().lower()
            if not name.strip() or not uid or not new_password:
                st.error("Please fill in all fields.")
            elif uid in users:
                st.error("That username is already taken.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                users[uid] = {"name": name.strip(), "password": _hash(new_password)}
                local_storage.set_item(USERS_KEY, users)
                st.session_state["user"] = {"id": uid, "name": name.strip()}
                st.rerun()


# ---------- Age page ----------
def get_profile(user):
    return local_storage.get_item(f"{PROFILE_KEY}_{user['id']}") or {}


def save_profile(user, **changes):
    profile = get_profile(user)
    profile.update(changes)
    local_storage.set_item(f"{PROFILE_KEY}_{user['id']}", profile)


def get_age(user):
    return get_profile(user).get("age")


def AgePage(user):
    st.title("WaterBuddy 💧")
    st.subheader(f"Welcome, {user['name']}!")
    st.caption("Tell us your age so WaterBuddy can personalise your experience.")

    with st.form("age_form"):
        age = st.number_input("Your age", min_value=5, max_value=120, value=18, step=1)
        saved = st.form_submit_button(
            "Continue", type="primary", use_container_width=True
        )
    if saved:
        save_profile(user, age=int(age))
        st.rerun()

    if st.button("Log out"):
        logout()


# ---------- water data ----------
def get_goal(user):
    return get_profile(user).get("goal", DEFAULT_GOAL_ML)


def get_glass(user):
    return get_profile(user).get("glass", DEFAULT_GLASS_ML)


def get_history(user):
    return local_storage.get_item(f"{HISTORY_KEY}_{user['id']}") or {}


def get_today_ml(user):
    return get_history(user).get(date.today().isoformat(), 0)


def add_water(user, ml):
    history = get_history(user)
    today = date.today().isoformat()
    history[today] = max(0, history.get(today, 0) + ml)
    local_storage.set_item(f"{HISTORY_KEY}_{user['id']}", history)


def calc_streak(history, goal):
    d = date.today()
    if history.get(d.isoformat(), 0) < goal:
        d -= timedelta(days=1)
    streak = 0
    while history.get(d.isoformat(), 0) >= goal:
        streak += 1
        d -= timedelta(days=1)
    return streak


def calc_stars(history, goal):
    return sum(1 for ml in history.values() if ml >= goal)


def calc_level(history):
    total = sum(history.values())
    level, title = 1, LEVELS[0][1]
    for i, (need, name) in enumerate(LEVELS, start=1):
        if total >= need:
            level, title = i, name
    return level, title


def mascot_svg(pct):
    if pct == 0:
        face = (
            '<path d="M18 50 q5 4 10 0" stroke="#06364a" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
            '<path d="M36 50 q5 4 10 0" stroke="#06364a" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
            '<path d="M26 63 q6 -4 12 0" stroke="#06364a" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
        )
    else:
        face = (
            '<circle cx="23" cy="50" r="3.5" fill="#06364a"/><circle cx="41" cy="50" r="3.5" fill="#06364a"/>'
            '<path d="M24 60 q8 9 16 0" stroke="#06364a" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
        )
    return (
        '<svg viewBox="0 0 64 80" width="64" height="80">'
        '<path d="M32 4 C32 4 6 36 6 54 a26 26 0 0 0 52 0 C58 36 32 4 32 4z" fill="#22b8dc"/>'
        '<path d="M16 46 C16 38 22 30 28 22" stroke="#7fe3ff" stroke-width="3" fill="none" stroke-linecap="round" opacity=".6"/>'
        + face
        + "</svg>"
    )


def ring_svg(pct):
    radius = 134
    circ = 2 * 3.14159265 * radius
    offset = circ * (1 - min(pct, 100) / 100)
    return (
        '<svg viewBox="0 0 310 310">'
        '<defs><linearGradient id="wbg" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#00d4ff"/><stop offset="1" stop-color="#3b82f6"/>'
        "</linearGradient></defs>"
        f'<circle cx="155" cy="155" r="{radius}" fill="none" stroke="#0e1b2e" stroke-width="20"/>'
        f'<circle cx="155" cy="155" r="{radius}" fill="none" stroke="url(#wbg)" stroke-width="20" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}" '
        'transform="rotate(-90 155 155)"/>'
        "</svg>"
    )


# ---------- Header ----------
def toggle_sound():
    st.session_state["sound_on"] = not st.session_state.get("sound_on", True)


def Header(user):
    history = get_history(user)
    level, title = calc_level(history)
    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            _html(
                f"""
<div class="wb-head">
<div class="wb-logo">💧</div>
<div>
<div class="wb-title">WaterBuddy</div>
<div class="wb-sub">{date.today().strftime("%A, %b %d")}
<span class="wb-badge">Lv {level} · {title}</span></div>
</div>
</div>
"""
            ),
            unsafe_allow_html=True,
        )
    with right:
        with keyed_container("soundbtn"):
            st.button(
                "🔊" if st.session_state.get("sound_on", True) else "🔇",
                key="sound_toggle",
                on_click=toggle_sound,
            )


# ---------- Pages ----------
def HomePage(user):
    goal = get_goal(user)
    glass = get_glass(user)
    history = get_history(user)
    ml = get_today_ml(user)
    pct = min(int(ml / goal * 100), 100) if goal else 0
    remaining = max(goal - ml, 0)

    if pct == 0:
        msg = "💧 Time to start sipping!"
    elif pct < 50:
        msg = "💦 Nice start, keep sipping!"
    elif pct < 100:
        msg = "🌊 Over halfway there!"
    else:
        msg = "🎉 Goal smashed. Great job!"

    st.markdown(
        _html(
            f"""
<div class="wb-card">
<div class="wb-mascot">{mascot_svg(pct)}</div>
<div class="wb-ring">
{ring_svg(pct)}
<div class="wb-ring-text">
<div class="wb-big">{ml}<span>ml</span></div>
<div class="wb-of">of {goal} ml</div>
<div class="wb-pct">{pct}%</div>
</div>
</div>
<div class="wb-hey">Hey {user['name']}! 👋</div>
<div class="wb-msg">{msg}</div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )

    st.write("")
    with keyed_container("logwater"):
        if st.button("💧  Log Water", type="primary", use_container_width=True):
            add_water(user, glass)
            sounds.blip()
            st.toast(f"+{glass} ml logged", icon="💧")
            st.rerun()

    reminders = st.session_state.get("reminders", {})
    if reminders.get("enabled"):
        remind_text = (
            f"🔔 Reminders on · every {reminders['intervalMinutes']} min · "
            f"{REMIND_FROM}-{REMIND_TO}"
        )
    else:
        remind_text = "🔕 Reminders off · set them in the Profile tab"
    st.markdown(f'<div class="wb-remind">{remind_text}</div>', unsafe_allow_html=True)

    st.markdown(
        _html(
            f"""
<div class="wb-stats">
<div class="wb-stat"><div class="ic">🎯</div><b>{remaining} ml</b><small>REMAINING</small></div>
<div class="wb-stat"><div class="ic">🔥</div><b>{calc_streak(history, goal)} days</b><small>STREAK</small></div>
<div class="wb-stat"><div class="ic">⭐</div><b>{calc_stars(history, goal)}</b><small>STARS</small></div>
</div>
"""
        ),
        unsafe_allow_html=True,
    )

    if st.button("↩️ Undo last glass", use_container_width=True):
        add_water(user, -glass)
        st.rerun()


def TipsPage():
    st.markdown('<div class="wb-h2">💡 Hydration tips</div>', unsafe_allow_html=True)
    for icon, title, text in TIPS:
        st.markdown(
            _html(
                f"""
<div class="wb-row"><div class="ic">{icon}</div>
<div><b>{title}</b><span>{text}</span></div></div>
"""
            ),
            unsafe_allow_html=True,
        )


def BoardPage(user):
    st.markdown('<div class="wb-h2">🏆 Leaderboard</div>', unsafe_allow_html=True)
    st.caption("Today's water intake of everyone on this device.")
    users = local_storage.get_item(USERS_KEY) or {}
    rows = []
    for uid, info in users.items():
        other = {"id": uid}
        rows.append((get_today_ml(other), info["name"], uid))
    rows.sort(reverse=True)
    medals = ["🥇", "🥈", "🥉"]
    for i, (ml, name, uid) in enumerate(rows):
        icon = medals[i] if i < 3 else f"#{i + 1}"
        you = " (you)" if uid == user["id"] else ""
        st.markdown(
            _html(
                f"""
<div class="wb-row"><div class="ic">{icon}</div>
<div><b>{name}{you}</b></div><div class="end">{ml} ml</div></div>
"""
            ),
            unsafe_allow_html=True,
        )


def ProfilePage(user):
    st.markdown('<div class="wb-h2">👤 Profile</div>', unsafe_allow_html=True)
    profile = get_profile(user)
    history = get_history(user)
    level, title = calc_level(history)
    st.markdown(
        _html(
            f"""
<div class="wb-row"><div class="ic">💧</div>
<div><b>{user['name']}</b><span>Age {profile.get('age', '-')} · Lv {level} · {title}</span></div></div>
"""
        ),
        unsafe_allow_html=True,
    )

    with st.form("goal_form"):
        goal = st.number_input(
            "Daily goal (ml)", min_value=500, max_value=6000, step=100, value=get_goal(user)
        )
        glass = st.select_slider(
            "Glass size (ml)", options=[100, 150, 200, 250, 300, 350, 500], value=get_glass(user)
        )
        if st.form_submit_button("Save", type="primary", use_container_width=True):
            save_profile(user, goal=int(goal), glass=int(glass))
            st.toast("Saved", icon="✅")
            st.rerun()

    if st.button("🔔 Change reminder interval", use_container_width=True):
        st.session_state["open"] = True
    if st.button("Log out", use_container_width=True):
        logout()


# One-time prompt per user (new and existing): pick how often WaterBuddy should remind you.
def ReminderSetup():
    _, update = use_reminders()
    user, is_loading_auth = use_auth()

    # useState equivalents
    st.session_state.setdefault("askedFor", None)
    st.session_state.setdefault("open", False)
    st.session_state.setdefault("minutes", 30)

    # Play sound + speech + toast after "Set reminders" was clicked
    line = st.session_state.pop("_pending_line", None)
    if line:
        sounds.blip()
        speak(line)
        st.toast(line, icon="✅")

    # Ask once per account, so existing users get the prompt too.
    if not is_loading_auth and user and user.get("id"):
        key = f"{DONE_KEY}_{user['id']}"
        if st.session_state["askedFor"] != key:
            st.session_state["askedFor"] = key
            if not local_storage.get_item(key):
                st.session_state["open"] = True

    if not st.session_state["open"]:
        return None

    def mark_done():
        local_storage.set_item(f"{DONE_KEY}_{user['id']}", "1")

    def confirm():
        minutes = st.session_state["minutes"]
        update({"enabled": True, "intervalMinutes": minutes})
        mark_done()
        st.session_state["open"] = False
        st.session_state["_pending_line"] = (
            f"Reminder set for every {minutes} minutes. "
            "You can change it anytime in the Profile tab."
        )

    def later():
        mark_done()
        st.session_state["open"] = False

    def set_minutes(m):
        st.session_state["minutes"] = m

    @_dialog("How often should I remind you?")
    def modal():
        # BellRing icon
        st.markdown(
            "<div style='text-align:center;font-size:2.5rem;'>🔔</div>",
            unsafe_allow_html=True,
        )
        # Description
        st.caption("A gentle spoken nudge to drink water while the app is open.")

        # Interval buttons (grid of 5)
        cols = st.columns(len(INTERVALS))
        for col, m in zip(cols, INTERVALS):
            with col:
                st.button(
                    f"{m}m",
                    key=f"interval_{m}",
                    type="primary" if st.session_state["minutes"] == m else "secondary",
                    use_container_width=True,
                    on_click=set_minutes,
                    args=(m,),
                )

        # Set reminders
        if st.button("Set reminders", type="primary", use_container_width=True):
            confirm()
            st.rerun()

        # Decide later
        if st.button("Decide later", use_container_width=True):
            later()
            st.rerun()

    # With a real dialog, closing it with the X must not bring it back on the next rerun
    if _HAS_DIALOG:
        st.session_state["open"] = False
    modal()


# ---------- bottom navigation ----------
def set_tab(name):
    st.session_state["tab"] = name


def BottomNav():
    with keyed_container("bottomnav"):
        cols = st.columns(len(PAGES))
        for col, (name, icon) in zip(cols, PAGES):
            with col:
                st.button(
                    f"{icon} {name}",
                    key=f"nav_{name}",
                    type="primary" if st.session_state["tab"] == name else "secondary",
                    use_container_width=True,
                    on_click=set_tab,
                    args=(name,),
                )


# ---------- app flow: login -> age -> WaterBuddy ----------
inject_css()
st.session_state.setdefault("tab", "Home")
st.session_state.setdefault("sound_on", True)

user, is_loading_auth = use_auth()

if not user:
    LoginPage()
    st.stop()

if get_age(user) is None:
    AgePage(user)
    st.stop()

Header(user)

tab = st.session_state["tab"]
if tab == "Home":
    HomePage(user)
elif tab == "Tips":
    TipsPage()
elif tab == "Board":
    BoardPage(user)
else:
    ProfilePage(user)

ReminderSetup()
BottomNav()