from flask import Flask, render_template, session, redirect, url_for, request, flash
import random
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'change_this_to_a_secret_key'
app.permanent_session_lifetime = timedelta(days=365)

# Morse code mapping
MORSE_CODE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----','1': '.----','2': '..---','3': '...--',
    '4': '....-','5': '.....','6': '-....','7': '--...',
    '8': '---..','9': '----.'
}
MORSE_REVERSE = {v: k for k, v in MORSE_CODE.items()}

# Settings
WPM = 20
FREQ = 600  # Hz
UNIT_S = 1.2 / WPM
THRESHOLD_S = UNIT_S * 1.5

# Frequency-based levels (letters only)
FREQUENCY_ORDER = list('ETAOINSHRDLCUMWFGYPBVKJXQZ')
LEVELS = [
    FREQUENCY_ORDER[0:2],    # E, T
    FREQUENCY_ORDER[2:6],    # A, O, I, N
    FREQUENCY_ORDER[6:10],   # S, H, R, D
    FREQUENCY_ORDER[10:15],  # L, C, U, M, W
    FREQUENCY_ORDER[15:20],  # F, G, Y, P, B
    FREQUENCY_ORDER[20:26],  # V, K, J, X, Q, Z
]

# Helpers
def get_available_letters():
    level = session.get('level', 1)
    letters = []
    for lvl in LEVELS[:level]:
        letters.extend(lvl)
    return letters

@app.before_request
def ensure_session_defaults():
    session.permanent = True
    if 'level' not in session:
        session['level'] = 1
        session['correct'] = 0

@app.route('/')
def index():
    max_level = len(LEVELS)
    return render_template('index.html', level=session['level'], max_level=max_level)

@app.route('/listen', methods=['GET', 'POST'])
def listen():
    available = get_available_letters()
    max_level = len(LEVELS)
    if request.method == 'POST':
        target = request.form.get('target', '')
        guess = request.form.get('guess', '').strip().upper()
        reaction_time = float(request.form.get('reaction_time', '0') or 0)
        correct = (guess == target)
        # Update progression
        if correct:
            session['correct'] = session.get('correct', 0) + 1
            # threshold to advance
            threshold = 5
            if session['correct'] >= threshold and session['level'] < max_level:
                session['level'] += 1
                session['correct'] = 0
                flash(f'Congrats! You reached Level {session["level"]}.')
        else:
            session['correct'] = 0
        result = {
            'correct': correct,
            'target': target,
            'reaction_time': reaction_time
        }
        return render_template('listen.html',
                               wpm=WPM, freq=FREQ,
                               morse_code=MORSE_CODE,
                               target=target,
                               result=result)
    # GET
    target = random.choice(available)
    return render_template('listen.html',
                           wpm=WPM, freq=FREQ,
                           morse_code=MORSE_CODE,
                           target=target)

@app.route('/send')
def send():
    available = get_available_letters()
    return render_template('send.html',
                           wpm=WPM, freq=FREQ,
                           morse_code=MORSE_CODE,
                           available=available)

if __name__ == '__main__':
    app.run(debug=True)