import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import vlc
import time
import random
import math

class DualMP3Player:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual DJ Mixer")
        try:
            self.root.state("zoomed")  # Windows full screen
        except Exception:
            try:
                self.root.attributes('-zoomed', True)  # Linux/macOS fallback
            except Exception:
                pass

        # Theme colors
        self.bg_color = "#1e90ff"     # Background color for the root window
        self.frame_color = "#2c2c2c"  # Frame or panel color
        self.fg_color = "#ffffff"     # Foreground color
        self.accent_color = "#00bfff" # Accent color for buttons/highlights
        self.root.configure(bg=self.bg_color) # Apply background color to root window

        # VLC
        self.instance = vlc.Instance()
        self.players = {
            1: self.instance.media_player_new(),  # Player 1
            2: self.instance.media_player_new()   # Player 2
        }
        # Equalizers (if available)
        try:
            self.equalizers = {1: vlc.AudioEqualizer(), 2: vlc.AudioEqualizer()}
        except Exception:
            # Fallback if AudioEqualizer isn't available
            self.equalizers = {1: None, 2: None}

        # Playback state
        self.playlists = {1: [], 2: []}  # Playlists for each playe
        self.current_index = {1: 0, 2: 0}  # Current track index in each playlist
        self.playing = {1: False, 2: False}  # Whether each player is actively playing
        self.paused = {1: False, 2: False}  # Whether each player is paused
        self.user_seeking = {1: False, 2: False}  # Whether the user is manually seeking in the track
        self.end_triggered = {1: False, 2: False}  # Flags to detect if end-of-track event has been triggered
        self.updating_progress = {1: False, 2: False}  # Flags to avoid conflict during progress bar update
        self.repeat = False
        self.shuffle = False

        # EQ Presets (kept your presets)
        self.presets = {
            "Flat":         {"bass": 0, "mid": 0, "treble": 0},
            "Pop":          {"bass": 12, "mid": 5, "treble": 10},
            "Hip-Hop":      {"bass": 18, "mid": -3, "treble": 8},
            "Classical":    {"bass": 5, "mid": 12, "treble": 6},
            "Rock":         {"bass": 10, "mid": 8, "treble": 12},
            "EDM":          {"bass": 20, "mid": 0, "treble": 15},
            "Jazz":         {"bass": 8, "mid": 10, "treble": 8},
            "Techno Night": {"bass": 15, "mid": -5, "treble": 8},
            "Trap Drop":    {"bass": 25, "mid": -6, "treble": 10},
            "Festival Set": {"bass": 20, "mid": 0, "treble": 12},
            "Dance":        {"bass": 15, "mid": 3, "treble": 12},
            "Vocal":        {"bass": 2, "mid": 15, "treble": 10},
            "Acoustic":     {"bass": 5, "mid": 10, "treble": 7},
            "Loudness":     {"bass": 20, "mid": -5, "treble": 15},
            "Full Bass":    {"bass": 20, "mid": -5, "treble": 0},
            "Full Treble":  {"bass": 0, "mid": -5, "treble": 20},
            "Balanced B&T": {"bass": 25, "mid": 0, "treble": 25},
            "V-Shape":      {"bass": 15, "mid": -10, "treble": 15},
            "3D Surround":  {"bass": 6, "mid": 3, "treble": 9},
            "Club":         {"bass": 20, "mid": -5, "treble": 10},
            "Flat + Boost": {"bass": 5, "mid": 5, "treble": 5},
            "Cinematic":    {"bass": 18, "mid": 4, "treble": 12},
            "Reverb":       {"bass": -3, "mid": 10, "treble": 15},
            "Reggae":       {"bass": 15, "mid": 2, "treble": 6},
            "Blues":        {"bass": 8, "mid": 5, "treble": 7},
            "Funk":         {"bass": 14, "mid": 3, "treble": 10},
            "Soul":         {"bass": 10, "mid": 6, "treble": 8},
            "Metal":        {"bass": 20, "mid": 4, "treble": 10},
            "R&B":          {"bass": 16, "mid": 4, "treble": 9},
            "Indie":        {"bass": 6, "mid": 7, "treble": 8},
            "Trance":       {"bass": 18, "mid": 0, "treble": 14},
            "Lo-fi":        {"bass": 8, "mid": 3, "treble": 5},
            "Dubstep":      {"bass": 22, "mid": -2, "treble": 12},
            "Custom":       {"bass": 0, "mid": 0, "treble": 0},
        }

        # Build UI (single, unified)
        self.build_ui()

        # Start loops
        self.update_progress_loop()
        self.update_vu_loop()

    def build_ui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)  # Crossfader row
        self.root.columnconfigure(0, weight=1)

        for i in (1, 2):
            frame = tk.LabelFrame(self.root, text=f"Player {i}", padx=10, pady=10,
                                  bg=self.frame_color, fg=self.fg_color)
            frame.grid(row=i - 1, column=0, sticky="nsew", padx=10, pady=5)

            for r in range(7):
                frame.rowconfigure(r, weight=1)
            for c in range(7):
                frame.columnconfigure(c, weight=1)

            # Left VU Meter
            vu_canvasL = tk.Canvas(frame, width=40, height=120, bg="#000000", highlightthickness=0)
            vu_canvasL.grid(row=0, column=0, rowspan=6, sticky="ns", padx=(0, 6))
            barL_L = vu_canvasL.create_rectangle(5, 120, 15, 120, fill="red")
            barR_L = vu_canvasL.create_rectangle(25, 120, 35, 120, fill="lime")
            setattr(self, f"vu_canvasL_{i}", vu_canvasL)
            setattr(self, f"vu_barL_L_{i}", barL_L)
            setattr(self, f"vu_barR_L_{i}", barR_L)

            # Right VU Meter
            vu_canvasR = tk.Canvas(frame, width=40, height=120, bg="#000000", highlightthickness=0)
            vu_canvasR.grid(row=0, column=6, rowspan=6, sticky="ns", padx=(6, 0))
            barL_R = vu_canvasR.create_rectangle(5, 120, 15, 120, fill="lime")

            barR_R = vu_canvasR.create_rectangle(25, 120, 35, 120, fill="blue")
            setattr(self, f"vu_canvasR_{i}", vu_canvasR)
            setattr(self, f"vu_barL_R_{i}", barL_R)
            setattr(self, f"vu_barR_R_{i}", barR_R)

            # Listbox
            listbox = tk.Listbox(frame, height=8, bg="#121212", fg=self.fg_color,
                                 selectbackground=self.accent_color, selectforeground="#ffffff")
            listbox.grid(row=0, column=1, columnspan=5, sticky="nsew")
            setattr(self, f"listbox_{i}", listbox)
            listbox.bind("<Double-Button-1>", lambda e, n=i: self._on_list_double(n))

            # Load button
            load_btn = tk.Button(frame, text="Load Songs",
                                 bg="#00ff00", fg="#000000",
                                 activebackground="#1976d2", activeforeground="#ffffff",
                                 command=lambda n=i: self.load_songs(n))
            load_btn.grid(row=1, column=1, sticky="ew")

            # Play button
            play_btn = tk.Button(frame, text="▶️ Play", state='disabled',
                                 bg=self.accent_color, fg="#000000",
                                 activebackground="#1976d2", activeforeground="#ffffff",
                                 command=lambda n=i: self.play_pause(n))
            play_btn.grid(row=1, column=2, sticky="ew")
            setattr(self, f"play_btn_{i}", play_btn)

            # Previous button
            prev_btn = tk.Button(frame, text="⏮️ Previous", state='disabled',
                                 bg="#9d00ff", fg="#000000",
                                 command=lambda n=i: self.prev_song(n))
            prev_btn.grid(row=1, column=3, sticky="ew")
            setattr(self, f"prev_btn_{i}", prev_btn)

            # Next button
            next_btn = tk.Button(frame, text="⏭️ Next", state='disabled',
                                 bg="#ff10f0", fg="#000000",
                                 command=lambda n=i: self.next_song(n))
            next_btn.grid(row=1, column=4, sticky="ew")
            setattr(self, f"next_btn_{i}", next_btn)

            # Progress Scale
            scale = tk.Scale(frame, from_=0, to=1000, orient='horizontal',
                             bg=self.frame_color, fg=self.fg_color,
                             highlightbackground=self.frame_color,
                             command=lambda val, n=i: self.seek(n, val))
            scale.grid(row=2, column=1, columnspan=5, sticky="ew", pady=5)
            scale.config(state='disabled')
            setattr(self, f"progress_{i}", scale)
            scale.bind("<ButtonPress-1>", lambda e, n=i: self.start_seek(n))
            scale.bind("<ButtonRelease-1>", lambda e, n=i: self.end_seek(n))

            # Volume slider
            tk.Label(frame, text="Volume", bg=self.frame_color, fg=self.fg_color).grid(row=3, column=1, sticky="e")
            vol_slider = tk.Scale(frame, from_=0, to=100, orient='horizontal',
                                  bg="#0000ff", fg="#ffffff",
                                  highlightbackground=self.frame_color,
                                  command=lambda val, n=i: self.set_volume(n, val))
            vol_slider.set(100)
            vol_slider.grid(row=3, column=2, sticky="ew")
            setattr(self, f"volume_{i}", vol_slider)

            # Time Label
            time_label = tk.Label(frame, text="00:00 / 00:00", bg=self.frame_color, fg=self.fg_color)
            time_label.grid(row=3, column=4, columnspan=2, sticky="ew")
            setattr(self, f"time_label_{i}", time_label)

            # Bass slider
            tk.Label(frame, text="Bass", bg=self.frame_color, fg=self.fg_color).grid(row=4, column=1, sticky="e")
            bass_slider = tk.Scale(frame, from_=-30, to=30, orient='horizontal',
                                   bg="#4b0082", fg=self.fg_color,
                                   highlightbackground=self.frame_color,
                                   command=lambda val, n=i: self.change_bass(n, val))
            bass_slider.set(0)
            bass_slider.grid(row=4, column=2, sticky="ew")
            setattr(self, f"bass_{i}", bass_slider)

            # Mid slider
            tk.Label(frame, text="Mid", bg=self.frame_color, fg=self.fg_color).grid(row=4, column=3, sticky="e")
            mid_slider = tk.Scale(frame, from_=-30, to=30, orient='horizontal',
                                  bg="#00ffff", fg="#000000",
                                  highlightbackground=self.frame_color,
                                  command=lambda val, n=i: self.change_mid(n, val))
            mid_slider.set(0)
            mid_slider.grid(row=4, column=4, sticky="ew")
            setattr(self, f"mid_{i}", mid_slider)

            # Treble slider
            tk.Label(frame, text="Treble", bg=self.frame_color, fg=self.fg_color).grid(row=5, column=1, sticky="e")
            treble_slider = tk.Scale(frame, from_=-30, to=30, orient='horizontal',
                                     bg="#ff0000", fg=self.fg_color,
                                     highlightbackground=self.frame_color,
                                     command=lambda val, n=i: self.change_treble(n, val))
            treble_slider.set(0)
            treble_slider.grid(row=5, column=2, sticky="ew")
            setattr(self, f"treble_{i}", treble_slider)

            # Preset dropdown
            tk.Label(frame, text="Preset", bg=self.frame_color, fg=self.fg_color).grid(row=5, column=3, sticky="e")
            preset_box = ttk.Combobox(frame, values=list(self.presets.keys()), state="readonly")
            preset_box.set("Flat")
            preset_box.grid(row=5, column=4, sticky="ew")
            preset_box.bind("<<ComboboxSelected>>", lambda e, n=i, box=preset_box: self.apply_preset(n, box.get()))

        crossfader_frame = tk.Frame(self.root, bg=self.bg_color)
        crossfader_frame.grid(row=2, column=0, pady=10)

        # Label on the left
        tk.Label(crossfader_frame, text="Crossfader", bg=self.bg_color, fg="#000000").pack(side=tk.LEFT, padx=(0, 5))

        # Horizontal slider
        self.crossfader = tk.Scale(
            crossfader_frame,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient=tk.HORIZONTAL,
            length=500,
            command=self.update_crossfader,
            bg="#00ff00",
            fg="#000000",
            showvalue=False  # hide default value display
        )
        self.crossfader.set(0.5)
        self.crossfader.pack(side=tk.LEFT)

    # ----------------- LIST / LOAD / PLAY -----------------
    def _on_list_double(self, player_num):
        # Double tap to play
        lb = getattr(self, f"listbox_{player_num}")
        sel = lb.curselection()
        if not sel:
            return
        self.current_index[player_num] = sel[0]
        self.play_song_at_index(player_num)

    def load_songs(self, player_num):
        # Load songs
        files = filedialog.askopenfilenames(filetypes=[("MP3 Files", "*.mp3"), ("All files", "*.*")])
        if files:
            playlist = list(files)
            self.playlists[player_num] = playlist
            self.current_index[player_num] = 0
            listbox = getattr(self, f"listbox_{player_num}")
            listbox.delete(0, tk.END)
            for f in playlist:
                listbox.insert(tk.END, f.split("/")[-1] or f)
            self.playing[player_num] = False
            self.paused[player_num] = False

            getattr(self, f"play_btn_{player_num}").config(state='normal', text="▶️ Play")
            getattr(self, f"prev_btn_{player_num}").config(state='normal')
            getattr(self, f"next_btn_{player_num}").config(state='normal')
            getattr(self, f"progress_{player_num}").config(state='normal')

            self.set_media(player_num, playlist[0])

    def set_media(self, player_num, filepath):
        media = self.instance.media_new(filepath)
        player = self.players[player_num]
        player.set_media(media)
        # apply equalizer if present
        eq = self.equalizers.get(player_num)
        if eq:
            self.apply_equalizer_to_player(player, eq)

     # Play/pause
    def play_pause(self, player_num):
        # Play/Pause
        other_num = 2 if player_num == 1 else 1
        # stop the other player first (keeps single channel behavior if desired)
        try:
            self.stop(other_num)
        except Exception:
            pass

        player = self.players[player_num]
        if not self.playlists[player_num]:
            messagebox.showwarning("No songs", f"No songs loaded in Player {player_num}")
            return
        if self.playing[player_num]:
            player.pause()
            self.paused[player_num] = True
            self.playing[player_num] = False
            getattr(self, f"play_btn_{player_num}").config(text="▶️ Play")
        else:
            if self.paused[player_num]:
                player.play()
                self.root.after(200, lambda: self.safe_set_rate(player, 1.0))
            else:
                path = self.playlists[player_num][self.current_index[player_num]]
                self.set_media(player_num, path)
                player.play()
                self.root.after(200, lambda: self.safe_set_rate(player, 1.0))
                try:
                    vol = getattr(self, f"volume_{player_num}").get()
                    player.audio_set_volume(int(vol))
                except Exception:
                    pass
                eq = self.equalizers.get(player_num)
                try:
                    if eq:
                        eq.set_preamp(0.0)
                except Exception:
                    pass
                if eq:
                    self.apply_equalizer_to_player(player, eq)

            self.paused[player_num] = False
            self.playing[player_num] = True
            getattr(self, f"play_btn_{player_num}").config(text="⏸️ Pause")

    def safe_set_rate(self, player, rate):
        try:
            player.set_rate(rate)
        except Exception:
            pass

     # Next song
    def next_song(self, player_num):
        if not self.playlists[player_num]:
            return
        if self.shuffle:
            self.current_index[player_num] = random.randint(0, len(self.playlists[player_num]) - 1)
        else:
            self.current_index[player_num] += 1
            if self.current_index[player_num] >= len(self.playlists[player_num]):
                if self.repeat:
                    self.current_index[player_num] = 0
                else:
                    self.current_index[player_num] = len(self.playlists[player_num]) - 1
                    self.stop(player_num)
                    return
        self.play_song_at_index(player_num)

     # Previous song
    def prev_song(self, player_num):
        if not self.playlists[player_num]:
            return
        if self.shuffle:
            self.current_index[player_num] = random.randint(0, len(self.playlists[player_num]) - 1)
        else:
            self.current_index[player_num] -= 1
            if self.current_index[player_num] < 0:
                if self.repeat:
                    self.current_index[player_num] = len(self.playlists[player_num]) - 1
                else:
                    self.current_index[player_num] = 0
        # Play the selected song
        self.play_song_at_index(player_num)

    def play_song_at_index(self, player_num):
        path = self.playlists[player_num][self.current_index[player_num]]
        self.set_media(player_num, path)  # Set media file to player
        player = self.players[player_num]
        player.play()  # Play the selected song
        self.root.after(200, lambda: self.safe_set_rate(player, 1.0))
        try:
            vol = getattr(self, f"volume_{player_num}").get()
            player.audio_set_volume(int(vol))
        except Exception:
            pass
        # Reset equalizer preamp
        eq = self.equalizers.get(player_num)
        try:
            if eq:
                eq.set_preamp(0.0)
        except Exception:
            pass
        # Apply equalizer settings to player
        if eq:
            self.apply_equalizer_to_player(player, eq)

        self.paused[player_num] = False
        self.playing[player_num] = True
        # Update play button to "Pause"
        getattr(self, f"play_btn_{player_num}").config(text="⏸️ Pause")

        # Highlight the current track in the playlist UI
        listbox = getattr(self, f"listbox_{player_num}")
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(self.current_index[player_num])
        listbox.activate(self.current_index[player_num])

        # Update time display (00:00 / total duration)
        try:
            length = player.get_length()
            time_label = getattr(self, f"time_label_{player_num}")
            if length and length > 0:
                time_label.config(text=f"00:00 / {self.ms_to_time(length)}")
        except Exception:
            pass

    def stop(self, player_num):
        player = self.players[player_num]
        try:
            player.stop()  # Stop media player
        except Exception:
            pass
        # Reset player state
        self.playing[player_num] = False
        self.paused[player_num] = False
        # Update play button to "Play"
        try:
            getattr(self, f"play_btn_{player_num}").config(text="▶️ Play")
        except Exception:
            pass

    # ----------------- EQUALIZER CONTROL -----------------
    # Change Bass level
    def change_bass(self, player_num, val, boost_mode=False):
        try:
            bass_val = float(val)
            if boost_mode:
                bass_val *= 3.0 # Optional boost mode to double bass
        except Exception:
            bass_val = 0.0

        eq = self.equalizers.get(player_num)
        if eq:
            for band in [0, 1, 2, 3]:
                try:
                    eq.set_amp_at_index(bass_val, band)
                except Exception:
                    pass
            self.apply_equalizer(player_num)

     # Change Mid level
    def change_mid(self, player_num, val):
        try:
            mid_val = float(val)
        except Exception:
            mid_val = 0.0
        eq = self.equalizers.get(player_num)
        if eq:
            for band in [4, 5]:
                try:
                    eq.set_amp_at_index(mid_val, band)
                except Exception:
                    pass
            self.apply_equalizer(player_num)

    # Change Treble level
    def change_treble(self, player_num, val):
        try:
            treble_val = float(val)
        except Exception:
            treble_val = 0.0
        eq = self.equalizers.get(player_num)
        if eq:
            for band in [6, 7, 8, 9]:
                try:
                    eq.set_amp_at_index(treble_val, band)
                except Exception:
                    pass
            self.apply_equalizer(player_num)

    # Apply Equalizer to Player
    def apply_equalizer(self, player_num):
        player = self.players[player_num]
        eq = self.equalizers.get(player_num)
        if eq:
            self.apply_equalizer_to_player(player, eq)

    def apply_equalizer_to_player(self, player, eq):
        try:
            if hasattr(player, "set_equalizer"):
                player.set_equalizer(eq)
                return
        except Exception:
            pass
        try:
            if hasattr(player, "audio_set_equalizer"):
                player.audio_set_equalizer(eq)
                return
        except Exception:
            pass
        return

    # Apply EQ Preset
    def apply_preset(self, player_num, preset_name):
        preset = self.presets.get(preset_name, {"bass": 0, "mid": 0, "treble": 0})
        getattr(self, f"bass_{player_num}").set(preset["bass"])
        getattr(self, f"mid_{player_num}").set(preset["mid"])
        getattr(self, f"treble_{player_num}").set(preset["treble"])

        # Apply values to equalizer
        self.change_bass(player_num, preset["bass"])
        self.change_mid(player_num, preset["mid"])
        self.change_treble(player_num, preset["treble"])

    # ----------------- SEEK / VOLUME -----------------
    def start_seek(self, player_num):
        self.user_seeking[player_num] = True

    def end_seek(self, player_num):
        self.user_seeking[player_num] = False

    def seek(self, player_num, val):
        # handle only while user is dragging
        if not self.user_seeking[player_num]:
            return
        player = self.players[player_num]
        try:
            length = player.get_length()
            if length and length > 0:
                new_time = int((float(val) / 1000.0) * length)
                player.set_time(new_time)
        except Exception:
            pass

    def set_volume(self, player_num, val):
        player = self.players[player_num]
        try:
            player.audio_set_volume(int(val))
        except Exception:
            pass

    # ----------------- PROGRESS LOOP -----------------
    def update_progress_loop(self):
        for i in (1, 2):
            player = self.players[i]
            scale = getattr(self, f"progress_{i}")
            time_label = getattr(self, f"time_label_{i}")
            try:
                is_playing = player.is_playing()
            except Exception:
                is_playing = False

            if is_playing and not self.user_seeking[i]:
                try:
                    length = player.get_length()
                    pos = player.get_time()
                except Exception:
                    length = -1
                    pos = -1

                if length and length > 0 and pos is not None and pos >= 0:
                    val = int((pos / length) * 1000)
                    self.updating_progress[i] = True
                    try:
                        if abs(val - scale.get()) > 2:
                            scale.set(val)
                    except Exception:
                        pass
                    self.updating_progress[i] = False
                    time_label.config(text=f"{self.ms_to_time(pos)} / {self.ms_to_time(length)}")
                    # end-of-track detection
                    try:
                        if length - pos < 1000 and not self.end_triggered[i]:
                            self.end_triggered[i] = True
                            self.next_song(i)
                        elif length - pos > 1000:
                            self.end_triggered[i] = False
                    except Exception:
                        pass
            else:
                try:
                    length = player.get_length()
                    pos = player.get_time()
                except Exception:
                    length = -1
                    pos = -1
                if (not self.playlists[i]) and not self.playing[i]:
                    try:
                        scale.set(0)
                    except Exception:
                        pass
                    time_label.config(text="00:00 / 00:00")
                else:
                    if length and length > 0 and pos is not None and pos >= 0:
                        time_label.config(text=f"{self.ms_to_time(pos)} / {self.ms_to_time(length)}")

        self.root.after(500, self.update_progress_loop)

    # ----------------- VU METERS -----------------
    def update_vu_loop(self):
        for i in (1, 2):
            try:
                player = self.players[i]
                is_playing = False
                try:
                    is_playing = player.is_playing()
                except Exception:
                    is_playing = False

                if is_playing:
                    vol = 0
                    try:
                        vol = player.audio_get_volume() or 0
                    except Exception:
                        vol = 0
                    # random proxy for left/right levels (visual only)
                    left_level = random.randint(max(0, int(vol * 0.3)), max(0, vol))
                    right_level = random.randint(max(0, int(vol * 0.3)), max(0, vol))

                    hL = int(120 - (left_level / 100.0) * 120)
                    hR = int(120 - (right_level / 100.0) * 120)

                    # update both canvases safely
                    try:
                        getattr(self, f"vu_canvasL_{i}").coords(getattr(self, f"vu_barL_L_{i}"), 5, hL, 15, 120)
                        getattr(self, f"vu_canvasL_{i}").coords(getattr(self, f"vu_barR_L_{i}"), 25, hR, 35, 120)
                        getattr(self, f"vu_canvasR_{i}").coords(getattr(self, f"vu_barL_R_{i}"), 5, hL, 15, 120)
                        getattr(self, f"vu_canvasR_{i}").coords(getattr(self, f"vu_barR_R_{i}"), 25, hR, 35, 120)
                    except Exception:
                        pass
                else:
                    # reset to zero visually (use the exact attribute names created earlier)
                    try:
                        getattr(self, f"vu_canvasL_{i}").coords(getattr(self, f"vu_barL_L_{i}"), 5, 120, 15, 120)
                        getattr(self, f"vu_canvasL_{i}").coords(getattr(self, f"vu_barR_L_{i}"), 25, 120, 35, 120)
                        getattr(self, f"vu_canvasR_{i}").coords(getattr(self, f"vu_barL_R_{i}"), 5, 120, 15, 120)
                        getattr(self, f"vu_canvasR_{i}").coords(getattr(self, f"vu_barR_R_{i}"), 25, 120, 35, 120)
                    except Exception:
                        pass
            except Exception:
                pass

        self.root.after(100, self.update_vu_loop)

     # Crossfader
    def update_crossfader(self, val):
        try:
            val = float(val)
        except Exception:
            return

        # Clamp 0–1
        val = max(0.0, min(1.0, val))

        # Equal-power curve:
        angle = val * (math.pi / 2.0)
        gain1 = math.cos(angle)  # Deck1
        gain2 = math.sin(angle)  # Deck2

        # Base slider volumes
        base_vol1 = self.volume_1.get()
        base_vol2 = self.volume_2.get()

        # Apply combined volumes
        out1 = int(base_vol1 * gain1)
        out2 = int(base_vol2 * gain2)

        try:
            self.players[1].audio_set_volume(out1)
        except Exception:
            pass
        try:
            self.players[2].audio_set_volume(out2)
        except Exception:
            pass

    # ----------------- UTIL -----------------
    def ms_to_time(self, ms):
        try:
            s = int(ms / 1000)
        except Exception:
            s = 0
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"

# Run the GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = DualMP3Player(root)
    root.mainloop()

