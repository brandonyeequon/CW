import os
import sys
import wave
import struct
import math
import random
import threading
import time

try:
    import pygame
except ImportError:
    print("This application requires pygame. Please install it with 'pip install pygame'.")
    sys.exit(1)

# Morse code mapping: letters and digits
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
SAMPLE_RATE = 44100  # Hz
DOT_DURATION_S = 1.2 / WPM
UNIT_S = DOT_DURATION_S
THRESHOLD_S = UNIT_S * 1.5

TONE_FILENAME = 'tone.wav'

def generate_tone(filename, freq, duration_s, volume=0.5, sample_rate=SAMPLE_RATE):
    n_samples = int(duration_s * sample_rate)
    wavef = wave.open(filename, 'w')
    wavef.setnchannels(1)
    wavef.setsampwidth(2)
    wavef.setframerate(sample_rate)
    max_amp = 32767 * volume
    for i in range(n_samples):
        t = float(i) / sample_rate
        val = int(max_amp * math.sin(2 * math.pi * freq * t))
        wavef.writeframes(struct.pack('<h', val))
    wavef.close()

def ensure_tone():
    if not os.path.exists(TONE_FILENAME):
        generate_tone(TONE_FILENAME, FREQ, 1.0)

def play_dot():
    tone.play(-1)
    time.sleep(UNIT_S)
    tone.stop()
    time.sleep(UNIT_S)

def play_dash():
    tone.play(-1)
    time.sleep(UNIT_S * 3)
    tone.stop()
    time.sleep(UNIT_S)

def play_morse(text):
    # Play morse code for each character in text
    for ch in text:
        code = MORSE_CODE.get(ch.upper())
        if not code:
            continue
        for sym in code:
            if sym == '.':
                play_dot()
            elif sym == '-':
                play_dash()
        # gap between letters: extra 2 units (we already had 1 unit gap after last symbol)
        time.sleep(UNIT_S * 2)

def main():
    ensure_tone()
    pygame.mixer.init(frequency=SAMPLE_RATE)
    pygame.init()
    global tone
    tone = pygame.mixer.Sound(TONE_FILENAME)

    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Morse Code Learning App")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)

    state = 'menu'
    listening_target = ''
    playback_end = 0
    input_text = ''
    reaction_time = 0
    current_seq = ''

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if state == 'menu' and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Listening button
                if 150 < x < 350 and 200 < y < 260:
                    state = 'listening_playback'
                # Sending button
                elif 450 < x < 650 and 200 < y < 260:
                    state = 'sending'
                    current_seq = ''
            elif state == 'listening_input' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif event.key == pygame.K_RETURN:
                    user_time = time.time()
                    reaction_time = user_time - playback_end
                    state = 'listening_result'
                else:
                    char = event.unicode.upper()
                    if char.isalnum() and len(char) == 1:
                        input_text += char
            elif state == 'listening_result' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state = 'listening_playback'
            elif state == 'sending':
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    # Left paddle region
                    if 150 < x < 350 and 400 < y < 550:
                        press_time = time.time()
                        tone.play(-1)
                        holding = True
                        # wait until release
                        while holding:
                            for e in pygame.event.get():
                                if e.type == pygame.MOUSEBUTTONUP:
                                    holding = False
                                    release_time = time.time()
                                    tone.stop()
                                    duration = release_time - press_time
                                    if duration < THRESHOLD_S:
                                        current_seq += '.'
                                    else:
                                        current_seq += '-'
                            clock.tick(60)
                    # Finish button
                    if 450 < x < 650 and 350 < y < 420:
                        state = 'sending_result'
                    # Reset
                    if 450 < x < 650 and 430 < y < 500:
                        current_seq = ''
                    # Back to menu
                    if 10 < x < 110 and 10 < y < 50:
                        state = 'menu'
                        current_seq = ''
            elif state == 'sending_result' and event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                # Back to sending
                if 10 < x < 110 and 10 < y < 50:
                    state = 'sending'
                # Back to menu
                elif 10 < x < 110 and 60 < y < 100:
                    state = 'menu'
            elif state == 'sending_result' and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state = 'sending'
                    current_seq = ''
        # State logic and drawing
        screen.fill((30, 30, 30))
        if state == 'menu':
            # Draw buttons
            pygame.draw.rect(screen, (70, 70, 200), (150, 200, 200, 60))
            pygame.draw.rect(screen, (70, 200, 70), (450, 200, 200, 60))
            screen.blit(font.render("Listen", True, (255, 255, 255)), (200, 215))
            screen.blit(font.render("Send", True, (255, 255, 255)), (510, 215))
        elif state == 'listening_playback':
            listening_target = random.choice(list(MORSE_CODE.keys()))
            input_text = ''
            n_code = MORSE_CODE[listening_target]
            n_dot = n_code.count('.')
            n_dash = n_code.count('-')
            play_time = (n_dot*2 + n_dash*4 + 2) * UNIT_S
            playback_start = time.time()
            threading.Thread(target=play_morse, args=(listening_target,)).start()
            playback_end = playback_start + play_time
            state = 'listening_input'
        elif state == 'listening_input':
            screen.blit(font.render("Type the letter you heard:", True, (255, 255, 255)), (100, 100))
            screen.blit(font.render(input_text, True, (255, 255, 0)), (100, 200))
        elif state == 'listening_result':
            correct = input_text.strip().upper() == listening_target
            msg = "Correct!" if correct else f"Wrong! Was {listening_target}"
            screen.blit(font.render(msg, True, (255, 255, 255)), (100, 100))
            screen.blit(font.render(f"Time: {reaction_time:.2f}s", True, (255, 255, 0)), (100, 200))
            screen.blit(font.render("Press SPACE for next", True, (200, 200, 200)), (100, 300))
        elif state == 'sending':
            # Draw paddle region
            pygame.draw.rect(screen, (200, 200, 70), (150, 400, 200, 150))
            screen.blit(font.render("PADDLE", True, (0, 0, 0)), (180, 530))
            # Current sequence
            screen.blit(font.render("Seq: " + current_seq, True, (255, 255, 0)), (100, 100))
            # Buttons
            pygame.draw.rect(screen, (70, 200, 200), (450, 350, 200, 70))
            pygame.draw.rect(screen, (200, 70, 70), (450, 430, 200, 70))
            screen.blit(font.render("Finish", True, (255, 255, 255)), (510, 365))
            screen.blit(font.render("Reset", True, (255, 255, 255)), (510, 445))
            pygame.draw.rect(screen, (150, 150, 150), (10, 10, 100, 40))
            screen.blit(font.render("Menu", True, (0, 0, 0)), (20, 15))
        elif state == 'sending_result':
            screen.blit(font.render(f"Seq: {current_seq}", True, (255, 255, 0)), (100, 100))
            letter = MORSE_REVERSE.get(current_seq, '?')
            screen.blit(font.render(f"Letter: {letter}", True, (255, 255, 255)), (100, 200))
            screen.blit(font.render("Press SPACE to retry", True, (200, 200, 200)), (100, 300))
            pygame.draw.rect(screen, (150, 150, 150), (10, 10, 100, 40))
            screen.blit(font.render("Back", True, (0, 0, 0)), (20, 15))
            pygame.draw.rect(screen, (150, 150, 150), (10, 60, 100, 40))
            screen.blit(font.render("Menu", True, (0, 0, 0)), (20, 65))
        pygame.display.flip()
        clock.tick(30)

if __name__ == '__main__':
    main()