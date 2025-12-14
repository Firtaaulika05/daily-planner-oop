import tkinter as tk  # Library utama untuk membuat GUI (tampilan aplikasi)
from tkinter import messagebox  # Untuk menampilkan pop-up pesan error atau konfirmasi
import math  # Digunakan untuk rumus matematika (Sin/Cos) saat menggambar jam
import json  # Untuk menyimpan data jadwal ke file (agar tidak hilang saat ditutup)
import os  # Untuk mengecek keberadaan file database di komputer
from datetime import datetime  # Untuk mengambil waktu jam/menit/detik real-time
from abc import ABC, abstractmethod  # Modul wajib untuk menerapkan konsep ABSTRACTION

# --- KONFIGURASI TEMA ---
THEME = {
    "bg_app": "#FDFcf0",        
    "bg_panel": "#FFF8E7",      
    "fg_text": "#5D5C61",       
    "accent_1": "#B2AB8C",      
    "btn_add": "#D4E2D4",       
    "btn_del": "#FFC6C6",
    "btn_reset": "#E0BBE4",
    "clock_face": "#FFFFFF",    
    "clock_ring": "#555555",
    "pie_colors": ['#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#FFB7B2', '#E0BBE4']
}

DATA_FILE = "firta_plan.json"

# 1. ABSTRACTION & INHERITANCE (DATA LAYER)
class BaseScheduleItem(ABC):
    def __init__(self, start_h, start_m, end_h, end_m, desc, color):
        self._start_h = start_h
        self._start_m = start_m
        self._end_h = end_h
        self._end_m = end_m
        self._desc = desc
        self.color = color

    @abstractmethod
    def get_display_text(self):
        pass

    def get_start_h(self): return self._start_h
    def get_start_m(self): return self._start_m
    def get_end_h(self): return self._end_h
    def get_end_m(self): return self._end_m
    def get_desc(self): return self._desc
    
    def get_start_total_minutes(self):
        return self._start_h * 60 + self._start_m

    def get_end_total_minutes(self):
        return self._end_h * 60 + self._end_m

class Activity(BaseScheduleItem):
    def to_dict(self):
        return {
            "start_h": self._start_h,
            "start_m": self._start_m,
            "end_h": self._end_h,
            "end_m": self._end_m,
            "desc": self._desc,
            "color": self.color
        }

    def get_display_text(self):
        return f"{self._start_h:02d}:{self._start_m:02d} - {self._end_h:02d}:{self._end_m:02d} : {self._desc}"

# 2. ABSTRACTION & VISUAL LAYER (JARUM JAM)
class BaseClockHand(ABC):
    def __init__(self, canvas, center_x, center_y, length, color, width):
        self.canvas = canvas
        self.cx = center_x
        self.cy = center_y
        self.length = length
        self.color = color
        self.width = width

    @abstractmethod
    def calculate_angle(self, now):
        pass

    def draw(self, now):
        angle_degrees = self.calculate_angle(now)
        angle_rad = math.radians(angle_degrees)
        end_x = self.cx + self.length * math.sin(angle_rad)
        end_y = self.cy - self.length * math.cos(angle_rad)
        self.canvas.create_line(self.cx, self.cy, end_x, end_y, 
                                width=self.width, fill=self.color, tags="hands", capstyle=tk.ROUND)

# --- Concrete Classes ---

class HourHand(BaseClockHand):
    def calculate_angle(self, now):
        return (now.hour * 15) + (now.minute * 0.25)

class MinuteHand(BaseClockHand):
    def calculate_angle(self, now):
        return now.minute * 6 + (now.second * 0.1)

class SecondHand(BaseClockHand):
    def calculate_angle(self, now):
        return now.second * 6

# 3. COMPONENT VISUAL UTAMA (JAM KANVAS)
class ScheduleClock(tk.Canvas):
    def __init__(self, parent, size=400):
        super().__init__(parent, width=size, height=size, bg=THEME["bg_app"], highlightthickness=0)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2 + 20 
        self.radius_ring = size // 2 - 80 
        
        self.hands = [
            HourHand(self, self.cx, self.cy, self.radius_ring - 60, "#4A4A4A", 6),
            MinuteHand(self, self.cx, self.cy, self.radius_ring - 20, "#4A4A4A", 3),
            SecondHand(self, self.cx, self.cy, self.radius_ring - 10, "#D96C6C", 1)
        ]

        self.draw_static_elements()
        self.update_clock()

    def draw_static_elements(self):
        self.delete("bg_layer")
        self.create_text(self.cx, 40, text="TODAY'S TIME TABLE", 
                         font=("Georgia", 20, "bold"), fill=THEME["fg_text"], tags="bg_layer")
        self.create_line(self.cx - 100, 60, self.cx + 100, 60, fill=THEME["accent_1"], width=2, tags="bg_layer")

        self.create_oval(self.cx - self.radius_ring, self.cy - self.radius_ring,
                         self.cx + self.radius_ring, self.cy + self.radius_ring, 
                         fill=THEME["clock_face"], outline=THEME["clock_ring"], width=2, tags="bg_face")
        self.draw_overlay_elements()

    def draw_overlay_elements(self):
        self.delete("static_overlay")
        for i in range(24):
            hour_val = i 
            display_num = str(hour_val) if hour_val != 0 else "24"
            angle_rad = math.radians(i * 15)
            label_r = self.radius_ring + 20 
            x = self.cx + label_r * math.sin(angle_rad)
            y = self.cy - label_r * math.cos(angle_rad)
            self.create_text(x, y, text=display_num, font=("Verdana", 9, "bold"), 
                             fill=THEME["fg_text"], tags="static_overlay")
            
            x1 = self.cx + self.radius_ring * math.sin(angle_rad)
            y1 = self.cy - self.radius_ring * math.cos(angle_rad)
            x2 = self.cx + (self.radius_ring - 8) * math.sin(angle_rad)
            y2 = self.cy - (self.radius_ring - 8) * math.cos(angle_rad)
            self.create_line(x1, y1, x2, y2, width=2, fill="#333333", tags="static_overlay")

        for i in range(5, 65, 5):
            if i == 60: continue
            angle_rad = math.radians(i * 6)
            label_r = self.radius_ring + 40
            x = self.cx + label_r * math.sin(angle_rad)
            y = self.cy - label_r * math.cos(angle_rad)
            self.create_text(x, y, text=str(i), font=("Verdana", 7), fill="#999999", tags="static_overlay")

    def refresh_activities(self, activity_list):
        self.delete("activity_visual") 
        
        for activity in activity_list:
            sh = activity.get_start_h()
            sm = activity.get_start_m()
            eh = activity.get_end_h()
            em = activity.get_end_m()
            desc = activity.get_desc()
            color = activity.color 
            
            start_val = sh + (sm / 60.0)
            end_val = eh + (em / 60.0)

            duration = end_val - start_val
            if duration <= 0: duration += 24
            
            start_angle_tk = 90 - (start_val * 15)
            extent_angle = - (duration * 15)

            self.create_arc(self.cx - self.radius_ring, self.cy - self.radius_ring,
                            self.cx + self.radius_ring, self.cy + self.radius_ring,
                            start=start_angle_tk, extent=extent_angle,
                            fill=color, outline="", width=0, tags="activity_visual")

            mid_val = start_val + (duration / 2)
            mid_angle_rad = math.radians(mid_val * 15)
            text_dist = self.radius_ring * 0.7 
            tx = self.cx + text_dist * math.sin(mid_angle_rad)
            ty = self.cy - text_dist * math.cos(mid_angle_rad)
            
            display_text = desc[:22] + "..." if len(desc) > 25 else desc
            self.create_text(tx, ty, text=display_text, font=("Verdana", 8, "bold"), 
                             fill="#444444", angle=0, width=80, justify="center", tags="activity_visual")
        
        self.tag_lower("bg_face") 
        self.tag_raise("activity_visual", "bg_face")
        self.tag_raise("static_overlay") 
        self.tag_raise("hands")
        self.tag_raise("center_dot")

    def update_clock(self):
        now = datetime.now()
        self.delete("hands") 
        self.delete("center_dot")

        for hand in self.hands:
            hand.draw(now)
        
        self.create_oval(self.cx-6, self.cy-6, self.cx+6, self.cy+6, fill="#D4AF37", outline="#4A4A4A", tags="center_dot")
        self.after(1000, self.update_clock)

# 4. APLIKASI UTAMA (CONTROLLER)
class DailyPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firta's Daily Plan")
        self.root.configure(bg=THEME["bg_app"]) 
        
        self.tasks = []
        self.color_index = 0
        
        self.left_panel = tk.Frame(root, padx=25, pady=25, bg=THEME["bg_panel"])
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        self.right_panel = tk.Frame(root, padx=20, pady=20, bg=THEME["bg_app"])
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_input_widgets()
        self.clock = ScheduleClock(self.right_panel, size=600)
        self.clock.pack()
        self.load_data()

    def create_input_widgets(self):
        tk.Label(self.left_panel, text="Planner", font=("Georgia", 18, "bold"), 
                 bg=THEME["bg_panel"], fg=THEME["fg_text"]).pack(pady=(0, 20), anchor="w")
        label_font = ("Verdana", 9)
        
        # --- INPUT JAM MULAI ---
        tk.Label(self.left_panel, text="Start Time (HH : MM):", font=label_font, bg=THEME["bg_panel"], fg=THEME["fg_text"]).pack(anchor="w")
        
        frame_start = tk.Frame(self.left_panel, bg=THEME["bg_panel"])
        frame_start.pack(fill=tk.X, pady=(2, 10))
        
        self.entry_start_h = tk.Entry(frame_start, width=5, justify="center") 
        self.entry_start_h.pack(side=tk.LEFT, ipady=3)
        
        tk.Label(frame_start, text=":", bg=THEME["bg_panel"]).pack(side=tk.LEFT, padx=5) 
        
        self.entry_start_m = tk.Entry(frame_start, width=5, justify="center") 
        self.entry_start_m.pack(side=tk.LEFT, ipady=3)

        # --- INPUT JAM SELESAI ---
        tk.Label(self.left_panel, text="End Time (HH : MM):", font=label_font, bg=THEME["bg_panel"], fg=THEME["fg_text"]).pack(anchor="w")
        
        frame_end = tk.Frame(self.left_panel, bg=THEME["bg_panel"])
        frame_end.pack(fill=tk.X, pady=(2, 10))
        
        self.entry_end_h = tk.Entry(frame_end, width=5, justify="center")
        self.entry_end_h.pack(side=tk.LEFT, ipady=3)
        
        tk.Label(frame_end, text=":", bg=THEME["bg_panel"]).pack(side=tk.LEFT, padx=5)
        
        self.entry_end_m = tk.Entry(frame_end, width=5, justify="center")
        self.entry_end_m.pack(side=tk.LEFT, ipady=3)

        # --- INPUT KEGIATAN ---
        tk.Label(self.left_panel, text="Activity Name:", font=label_font, bg=THEME["bg_panel"], fg=THEME["fg_text"]).pack(anchor="w")
        self.entry_desc = tk.Entry(self.left_panel, relief=tk.FLAT, bg="white", highlightthickness=1, highlightcolor=THEME["accent_1"])
        self.entry_desc.pack(fill=tk.X, pady=(2, 20), ipady=3)

        # Tombol-tombol
        btn_add = tk.Button(self.left_panel, text="Add to Schedule", command=self.add_task, 
                            bg=THEME["btn_add"], fg="#444", font=("Verdana", 9, "bold"),
                            relief=tk.FLAT, cursor="hand2", pady=5)
        btn_add.pack(fill=tk.X, pady=5)

        btn_del = tk.Button(self.left_panel, text="Delete Selected", command=self.delete_task, 
                            bg=THEME["btn_del"], fg="#444", font=("Verdana", 9),
                            relief=tk.FLAT, cursor="hand2", pady=5)
        btn_del.pack(fill=tk.X, pady=5)
        
        btn_reset = tk.Button(self.left_panel, text="Reset All", command=self.reset_all, 
                            bg=THEME["btn_reset"], fg="#444", font=("Verdana", 9),
                            relief=tk.FLAT, cursor="hand2", pady=5)
        btn_reset.pack(fill=tk.X, pady=5)

        tk.Label(self.left_panel, text="Your List:", font=("Georgia", 11, "italic"), 
                 bg=THEME["bg_panel"], fg=THEME["fg_text"]).pack(pady=(20, 5), anchor="w")
        
        self.listbox = tk.Listbox(self.left_panel, height=15, relief=tk.FLAT, 
                                  bg="white", fg="#555", font=("Verdana", 9),
                                  highlightthickness=0, activestyle='none')
        self.listbox.pack(fill=tk.BOTH, expand=True)

    # [LOGIC] Deteksi Tabrakan Jadwal
    def is_overlapping(self, new_start_min, new_end_min):
        for task in self.tasks:
            t_start = task.get_start_total_minutes()
            t_end = task.get_end_total_minutes()
            
            if (new_start_min < t_end) and (new_end_min > t_start):
                return True
        return False

    def add_task(self):
        try:
            # [LOGIC] Ambil input. Gunakan `or "0"` agar jika KOSONG dianggap 0.
            # mencegah error jika user membiarkan kolom kosong.
            sh = int(self.entry_start_h.get() or "0")
            sm = int(self.entry_start_m.get() or "0")
            eh = int(self.entry_end_h.get() or "0")
            em = int(self.entry_end_m.get() or "0")
            desc = self.entry_desc.get()

            # Validasi
            if not (0 <= sh <= 23) or not (0 <= eh <= 23): raise ValueError
            if not (0 <= sm <= 59) or not (0 <= em <= 59): raise ValueError
            
            start_total = sh * 60 + sm
            end_total = eh * 60 + em
            
            if start_total == end_total:
                messagebox.showwarning("Oops", "Start and End time cannot be the same.")
                return
                
            if not desc: 
                messagebox.showwarning("Oops", "Please enter activity name.")
                return
            
            if self.is_overlapping(start_total, end_total):
                messagebox.showerror("Conflict", "Time overlaps with another task!")
                return

            colors = THEME["pie_colors"]
            current_color = colors[self.color_index % len(colors)]
            self.color_index += 1

            new_task = Activity(sh, sm, eh, em, desc, current_color)
            self.tasks.append(new_task)
            self.tasks.sort(key=lambda x: x.get_start_total_minutes())
            
            self.refresh_ui_list()
            self.save_data()
            
            # [UPDATE] Bersihkan form tanpa mengisi "00" lagi
            self.entry_start_h.delete(0, tk.END)
            self.entry_start_m.delete(0, tk.END) 
            self.entry_end_h.delete(0, tk.END)
            self.entry_end_m.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)

        except ValueError:
            messagebox.showerror("Error", "Check inputs (Hour 0-23, Min 0-59).")

    def refresh_ui_list(self):
        self.listbox.delete(0, tk.END)
        for task in self.tasks:
             self.listbox.insert(tk.END, f" {task.get_display_text()}")
        self.clock.refresh_activities(self.tasks)

    def delete_task(self):
        selection = self.listbox.curselection()
        if not selection: return
        index = selection[0]
        del self.tasks[index]
        self.refresh_ui_list()
        self.save_data()

    def reset_all(self):
        if messagebox.askyesno("Reset", "Delete all schedules?"):
            self.tasks.clear()
            self.refresh_ui_list()
            self.save_data()

    def save_data(self):
        data = [task.to_dict() for task in self.tasks]
        try:
            with open(DATA_FILE, 'w') as f: json.dump(data, f)
        except: pass

    def load_data(self):
        if not os.path.exists(DATA_FILE): return
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.tasks = []
                for item in data:
                    sh = item.get('start_h', item.get('start', 0))
                    sm = item.get('start_m', 0)
                    eh = item.get('end_h', item.get('end', 0))
                    em = item.get('end_m', 0)
                    
                    self.tasks.append(Activity(sh, sm, eh, em, item['desc'], item['color']))
                self.color_index = len(self.tasks)
                self.refresh_ui_list()
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except: pass
    
    app = DailyPlannerApp(root)
    root.mainloop()