"""Procedural score + SFX for the Workiom sales-playbook training film.
96 BPM (beat 0.625 s, bar 2.5 s). Deterministic: fixed seed, no external samples."""
import numpy as np, wave, sys
SR = 44100
DUR = 150.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
BEAT = 0.625; BAR = 2.5

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
def env(n, a=0.005, d=0.3, curve=4.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-curve * t / max(d, 1e-4))
    return e
def lp(x, cut):
    a = np.exp(-2 * np.pi * cut / SR); y = np.empty_like(x); z = 0.0
    for i in range(len(x)):
        z = (1 - a) * x[i] + a * z; y[i] = z
    return y
def lp_fast(x, cut, passes=2):
    # cheap smoothing via moving average approximation of LP (vectorised)
    k = max(1, int(SR / cut / 2))
    ker = np.ones(k) / k
    for _ in range(passes): x = np.convolve(x, ker, mode="same")
    return x
def add(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf): return
    sig = sig[: len(buf) - i]
    l = np.cos((pan + 1) * np.pi / 4); r = np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(sig), 0] += sig * gain * l * 1.414
    buf[i:i + len(sig), 1] += sig * gain * r * 1.414

# ---------------- instruments ----------------
def rhodes(f, dur=2.4, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    trem = 1 + 0.08 * np.sin(2 * np.pi * 4.2 * t)
    s = (np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t)*np.exp(-3*t) + 0.12*np.sin(2*np.pi*3.01*f*t)*np.exp(-6*t)
         + 0.05*np.sin(2*np.pi*7*f*t)*np.exp(-30*t))
    return s * env(n, 0.004, dur * 0.55, 2.2) * trem * vel
def bass(f, dur=1.2, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2*np.pi*f*t) + 0.25*np.sin(2*np.pi*2*f*t) * np.exp(-4*t)
    return s * env(n, 0.01, dur * 0.6, 2.5) * vel
def pluck(f, dur=0.9, vel=1.0, bright=0.996):
    n = int(dur * SR); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = bright * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return lp_fast(out, 5000, 1) * env(n, 0.002, dur, 3.0) * vel
def kick(vel=1.0):
    n = int(0.32 * SR); t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 11) * vel
def hat(vel=1.0):
    n = int(0.06 * SR); x = rng.uniform(-1, 1, n)
    x = x - lp_fast(x, 6000, 1)
    return x * np.exp(-np.arange(n) / SR * 70) * vel
def rim(vel=1.0):
    n = int(0.12 * SR); t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n); x = lp_fast(x, 3500, 1) - lp_fast(x, 900, 1)
    return (x * 1.6 + 0.4 * np.sin(2*np.pi*330*t)) * np.exp(-t * 38) * vel

# ---------------- SFX ----------------
def s_pop(f=880, vel=1.0):
    n = int(0.18 * SR); t = np.arange(n) / SR
    fr = f * (1 + 0.5 * np.exp(-t * 60))
    return np.sin(2*np.pi*np.cumsum(fr)/SR) * env(n, 0.002, 0.09, 1.0) * vel
def s_whoosh(dur=0.6, up=True, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; x = rng.uniform(-1, 1, n)
    lo = lp_fast(x, 700, 2); hi = lp_fast(x, 3000, 2)
    mix = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    y = lo * (1 - mix) + hi * mix
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
    return y * shape * 2.2 * vel
def s_thud(vel=1.0):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 70 + 90 * np.exp(-t * 25)
    b = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t * 14)
    x = lp_fast(rng.uniform(-1, 1, n), 1500, 1) * np.exp(-t * 45) * 0.6
    return (b + x) * vel
def s_chime(f=1320, vel=1.0, dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2*np.pi*f*t) + 0.4*np.sin(2*np.pi*2.76*f*t)*np.exp(-5*t) + 0.2*np.sin(2*np.pi*5.4*f*t)*np.exp(-9*t)
    return s * env(n, 0.002, dur * 0.5, 2.5) * vel
def s_tick(hi=True, vel=1.0):
    n = int(0.05 * SR); t = np.arange(n) / SR
    f = 2400 if hi else 1800
    return np.sin(2*np.pi*f*t) * np.exp(-t * 140) * vel
def s_ring(dur=1.2, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = 0.5 * (np.sin(2*np.pi*660*t) + np.sin(2*np.pi*830*t))
    gate = (np.sin(2*np.pi*14*t) > 0).astype(float)
    gate = lp_fast(gate, 200, 1)
    return lp_fast(s, 3000, 1) * gate * env(n, 0.01, dur, 0.6) * vel
def s_swell(dur=1.0, vel=1.0, f=349.2):
    n = int(dur * SR); t = np.arange(n) / SR
    s = sum(np.sin(2*np.pi*f*k*t) / k for k in (1, 1.5, 2, 3))
    x = lp_fast(rng.uniform(-1, 1, n), 1800, 2)
    shape = (t / dur) ** 2 * np.exp(-((t - dur) ** 2) / 0.02)
    shape = np.clip(np.where(t < dur * 0.85, (t / dur) ** 2, np.cos((t - dur * 0.85) / (dur * 0.15) * np.pi / 2) * 0.72), 0, 1)
    return (0.6 * s + 0.8 * x) * shape * vel
def s_flap(vel=1.0):
    n = int(0.07 * SR); t = np.arange(n) / SR
    x = lp_fast(rng.uniform(-1, 1, n), 2500, 1)
    return x * np.exp(-t * 60) * 1.4 * vel
def s_scratch(dur=0.4, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.uniform(-1, 1, n); x = lp_fast(x, 5000, 1) - lp_fast(x, 1500, 1)
    am = 0.6 + 0.4 * np.sin(2*np.pi*38*t)
    return x * am * np.sin(np.pi * t / dur) * 1.5 * vel

# ================= MUSIC =================
music = np.zeros((N, 2))
# F major: Fmaj9 | Dm9 | Bbmaj9 | C6/9
CH = [[53, 57, 60, 64, 67], [50, 53, 57, 60, 64], [46, 50, 53, 57, 60], [48, 52, 55, 57, 62]]
BS = [41, 38, 34, 36]
nbars = int(DUR / BAR)
def section_level(t):
    # arrangement: soft intro, groove, breakdown at S6, outro
    if t < 10: return dict(keys=0.75, bass=0.0, drums=0.0, arp=0.0)
    if 67.5 <= t < 72.5: return dict(keys=0.85, bass=0.6, drums=0.0, arp=0.5)
    if t >= 145: return dict(keys=0.8, bass=0.5, drums=0.0, arp=0.0)
    return dict(keys=0.7, bass=0.85, drums=1.0, arp=0.35 if t >= 47.5 else 0.0)
for b in range(nbars):
    t0 = b * BAR; lvl = section_level(t0); ch = CH[b % 4]
    if t0 >= 147.5: break
    for i, m in enumerate(ch):
        add(music, rhodes(midi(m), 2.6, 0.16 * lvl["keys"]), t0 + i * 0.012, pan=-0.3 + 0.15 * i)
        add(music, rhodes(midi(m), 1.2, 0.06 * lvl["keys"]), t0 + BEAT * 2.5, pan=0.3 - 0.15 * i)
    if lvl["bass"]:
        add(music, bass(midi(BS[b % 4]), 1.15, 0.42 * lvl["bass"]), t0)
        add(music, bass(midi(BS[b % 4]), 0.55, 0.28 * lvl["bass"]), t0 + BEAT * 2.5)
        add(music, bass(midi(BS[b % 4] + 7), 0.5, 0.22 * lvl["bass"]), t0 + BEAT * 3.5)
    if lvl["drums"]:
        for k in range(4):
            add(music, kick(0.55), t0 + k * BEAT) if k in (0, 2) else add(music, rim(0.16), t0 + k * BEAT, pan=0.1)
            add(music, hat(0.10), t0 + k * BEAT + BEAT / 2, pan=0.35)
            add(music, hat(0.05), t0 + k * BEAT + BEAT * 0.75, pan=0.4)
    if lvl["arp"]:
        pent = [72, 74, 77, 79, 81, 84]
        for k in range(8):
            if (k + b) % 3 == 1: continue
            note = pent[(k * 2 + b) % len(pent)]
            add(music, pluck(midi(note), 0.6, 0.13 * lvl["arp"]), t0 + k * BEAT / 2, pan=0.5 if k % 2 else -0.5)
# final chord
for i, m in enumerate([41, 53, 57, 60, 64, 67, 72]):
    add(music, rhodes(midi(m), 4.6, 0.15), 145.0 + i * 0.03, pan=-0.4 + 0.13 * i)
# vinyl air
air = lp_fast(rng.uniform(-1, 1, N), 2500, 1) * 0.006
music[:, 0] += air; music[:, 1] += np.roll(air, 333)
# fades
fi = int(1.2 * SR); music[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(3.0 * SR); music[-fo:] *= np.linspace(1, 0, fo)[:, None]

# ================= SFX =================
sfx = np.zeros((N, 2))
P = [midi(m) for m in (77, 79, 81, 84, 86, 89, 91, 93)]  # warm pentatonic ladder (F)
def ladder(times, start=0, vel=0.5, pan0=-0.3):
    for i, t in enumerate(times): add(sfx, s_pop(P[(start + i) % len(P)], vel), t, pan=pan0 + 0.15 * i)
# S1
add(sfx, s_whoosh(1.0, True, 0.25), 0.3, pan=-0.4)
ladder([1.5, 1.78], 0, 0.35)
ladder([3.4, 4.15, 4.9], 2, 0.35, 0.3)
add(sfx, s_whoosh(0.7, False, 0.2), 5.6, pan=0.4); add(sfx, s_thud(0.45), 6.3, pan=0.4)
add(sfx, s_whoosh(2.6, True, 0.12), 7.1, pan=0.5)
add(sfx, s_whoosh(0.9, True, 0.5), 9.3)
# S2
ladder([11.0, 11.22, 11.44], 0, 0.45)
add(sfx, s_thud(0.25), 12.4); add(sfx, s_pop(P[3], 0.25), 13.0, -0.4); add(sfx, s_pop(P[4], 0.25), 13.3)
add(sfx, s_thud(0.5), 14.65)
add(sfx, s_pop(P[5], 0.4), 16.2, 0.3)
add(sfx, s_scratch(0.5, 0.18), 17.4, 0.2)
add(sfx, s_flap(0.5), 17.9, 0.2); add(sfx, s_chime(P[2] * 2, 0.18), 18.1, 0.2)
# swap disc
add(sfx, s_swell(0.55, 0.35), 21.98); add(sfx, s_thud(0.5), 22.5)
# S3 tick-tock while hand sweeps
for k, t in enumerate(np.arange(23.7, 27.9, 0.3125)): add(sfx, s_tick(k % 2 == 0, 0.22), t, pan=-0.3)
add(sfx, s_ring(1.4, 0.2), 28.3, pan=0.3)
ladder([30.1, 30.25, 30.4], 3, 0.3, 0.2)
add(sfx, s_whoosh(0.75, True, 0.5), 34.55)
# S4
for i, t in enumerate([35.95, 36.85, 38.6, 40.35]): add(sfx, s_pop(P[i + 1], 0.32), t, pan=-0.5 + 0.3 * i)
add(sfx, s_pop(P[2], 0.3), 42.4); add(sfx, s_pop(P[3], 0.3), 42.6)
add(sfx, s_flap(0.5), 43.7); add(sfx, s_chime(midi(84), 0.25), 43.82)
add(sfx, s_scratch(0.45, 0.25), 45.1)
add(sfx, s_swell(0.9, 0.22, 261.6), 46.95)
# S5 knots ladder + bubbles + pans
for i, t in enumerate([48.7, 50.0, 51.9, 53.2, 55.2]): add(sfx, s_pop(P[i], 0.5), t, pan=-0.4 + 0.2 * i)
for t in (49.4, 52.7, 55.8): add(sfx, s_pop(P[6], 0.25), t, 0.2); add(sfx, s_pop(P[7], 0.18), t + 0.07, 0.25)
add(sfx, s_whoosh(1.3, True, 0.18), 51.1); add(sfx, s_whoosh(1.3, True, 0.18), 54.3)
add(sfx, s_whoosh(0.7, False, 0.2), 56.4, 0.4); add(sfx, s_thud(0.25), 56.95, 0.4)
add(sfx, s_swell(1.4, 0.18), 58.4)
for i in range(5): add(sfx, s_tick(True, 0.18), 60.25 + 0.75 * i, pan=-0.6 + 0.3 * i)
add(sfx, s_chime(midi(81), 0.3), 61.1)
add(sfx, s_swell(1.0, 0.28, 220.0), 66.9)
# S6 growth
add(sfx, s_thud(0.45), 67.5)
for i, t in enumerate(np.linspace(68.75, 69.75, 5)): add(sfx, s_pop(P[i], 0.18), t)
add(sfx, s_chime(midi(77), 0.3), 69.9)
add(sfx, s_chime(midi(81), 0.25), 73.1, -0.3); add(sfx, s_chime(midi(84), 0.25), 73.3, 0.3)
add(sfx, s_chime(midi(86), 0.2), 76.3, -0.4); add(sfx, s_chime(midi(89), 0.2), 76.5, 0.4); add(sfx, s_chime(midi(91), 0.2), 76.7)
add(sfx, s_thud(0.7), 78.82)
add(sfx, s_whoosh(0.8, True, 0.3), 84.55)
# S7
add(sfx, s_whoosh(0.8, True, 0.22), 86.65)
for i in range(6): add(sfx, s_pop(P[i % 4 + 2], 0.16), 87.4 + 0.08 * i, pan=-0.3 + 0.1 * i)
for i, t in enumerate([89.9, 90.6, 91.3]): add(sfx, s_chime(midi(81 + 3 * i), 0.24), t, 0.3)
add(sfx, s_thud(0.7), 92.5)
for i, m in enumerate([65, 69, 72, 76]): add(sfx, rhodes(midi(m), 1.6, 0.08), 92.55 + 0.02 * i)
# blinds
for k in range(6): add(sfx, s_flap(0.32), 96.95 + 0.05 * k + 0.25, pan=-0.5 + 0.2 * k)
for k in range(6): add(sfx, s_flap(0.25), 97.52 + 0.05 * k + 0.1, pan=0.5 - 0.2 * k)
# S8
for i, t in enumerate([98.6, 99.1, 100.05, 100.55, 101.9]): add(sfx, s_pop(P[i + 1], 0.38), t, pan=-0.5 + 0.25 * i)
add(sfx, s_swell(0.6, 0.15, 349.2), 102.2)
add(sfx, s_pop(P[5], 0.25), 103.1); add(sfx, s_pop(P[6], 0.25), 103.35)
add(sfx, s_chime(midi(84), 0.18), 105.5, 0.5)
add(sfx, s_pop(P[2], 0.4), 108.4, -0.2)
for i in range(3): add(sfx, s_pop(P[3 + i], 0.2), 108.9 + 0.18 * i)
add(sfx, s_whoosh(1.0, False, 0.16), 110.0); add(sfx, s_whoosh(1.1, True, 0.16), 111.95)
add(sfx, s_chime(midi(86), 0.3), 113.2, 0.6)
add(sfx, s_whoosh(0.9, True, 0.35), 116.95, -0.5)
# S9
add(sfx, s_whoosh(0.9, True, 0.25), 118.0)
add(sfx, s_thud(0.65), 120.3)
add(sfx, s_chime(2637, 0.14, 0.9), 120.75, 0.3)
add(sfx, s_tick(True, 0.25), 122.7, 0.3); add(sfx, s_tick(True, 0.25), 124.15, 0.3)
for i, t in enumerate(np.linspace(122.8, 124.8, 4)): add(sfx, s_pop(P[5 - i], 0.12), t, 0.3)
add(sfx, s_pop(P[4], 0.4), 126.1, 0.5)
for i, t in enumerate(np.linspace(126.8, 127.4, 4)): add(sfx, s_pop(P[2 + i], 0.18), t, 0.3)
add(sfx, s_whoosh(0.9, False, 0.4), 131.95)
# S10
for t in (132.98, 133.83, 134.68): add(sfx, s_thud(0.65), t)
add(sfx, s_swell(2.4, 0.22, 174.6), 137.1)
for i in range(8): add(sfx, s_pop(P[i], 0.22), 137.8 + 0.22 * i, pan=-0.6 + 0.17 * i)
add(sfx, s_chime(midi(89), 0.28), 145.2)

def write(name, x, peak):
    m = np.max(np.abs(x)); x = x / m * peak if m > 0 else x
    x = np.tanh(x * 1.2) / np.tanh(1.2)
    data = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(name, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
write("assets/audio/music.wav", music, 0.8)
write("assets/audio/sfx.wav", sfx, 0.85)
# then: ffmpeg -i assets/audio/<name>.wav -c:a libmp3lame -b:a 192k assets/audio/<name>.mp3
print("ok")
