import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.simpledialog import askstring
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import threading
import os
import json
import time

# Import scripts
import photo_scan
import cross_pic_organizer
import scanned_album
import clean_upload

class PhotoToolsApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Tools")
        self.geometry("1100x750")
        self.configure(bg="lightgray")
        
        self.logo_photos = {}
        self.dropped_paths = {}
        self.create_widgets()
        
        
    def create_widgets(self):
        # --- Tab control (top) ---
        self.tab_control = ttk.Notebook(self)
        self.tabs = {}
        
        for name in ["Media Discovery", "Media Organizer", "Scanned Albums", "Clean Upload"]:
            frame = tk.Frame(self.tab_control, bg="lightgray")
            self.tabs[name] = frame
            self.tab_control.add(frame, text=name)
            
        self.tab_control.pack(fill="both", expand=True)
        
        # --- Drop area and logo ---
        for tab_name, tab in self.tabs.items():
            drop_frame = tk.Frame(tab, bg="lightgray", pady=10)
            drop_frame.pack(pady=10)
            
            drop_label = tk.Label(drop_frame, text="Drop folder here.", relief="groove", width=40, height=3)
            drop_label.pack()
            
            # Enable drag and drop only on media discovery 
            if tab_name in ["Media Discovery", "Scanned Albums", "Clean Upload"]:
                drop_label.drop_target_register(DND_FILES)
                drop_label.dnd_bind("<<Drop>>", lambda e, tab=tab_name: self.handle_drop(e, tab))
                
            # Logo Area
            logo_frame = tk.Frame(tab, bg="lightgray")
            logo_frame.pack()
            
            logo_path = os.path.join("assets", "logo.png")
            if os.path.exists(logo_path):
                try:
                    logo_img = Image.open(logo_path)
                    logo_img = logo_img.resize((600, 300), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(logo_img)
                
                    self.logo_photos[tab_name] = photo # Store it so it doesn't get garbage
                
                    logo_label = tk.Label(logo_frame, image=photo, bg="lightgray")
                    logo_label.pack(pady=10)
                except Exception as e:
                    print(f"[ERROR] Failed to load logo: {e}")
                    logo_label = tk.Label(logo_frame, text="[Logo error]", bg="lightgray")
                    logo_label.pack(pady=10)
            else:
                logo_label = tk.Label(logo_frame, text="[Logo not loaded]", bg="lightgray")
                logo_label.pack(pady=10)
        
        # --- Right Panel for Tool Controls ---
        self.control_panel = tk.Frame(self, width=600, bg="white", relief="sunken", borderwidth=1)
        self.control_panel.place(relx=1.0, y=40, anchor="ne", relheight=0.85)
        
        self.update_controls("Media Discovery")
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # --- Console at bottom ---
        self.console = tk.Text(self, height=25, bg="black", fg="lime", insertbackground="white")
        self.console.pack(fill="x", side="bottom")
        self.log_console("[Console Ready]\n")
        
        # --- Progress Bar ---
        self.progress_frame = tk.Frame(self, bg="lightgray")
        self.progress_frame.pack(fill="x", pady=(2, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.pack(fill="x", padx=10)
        
        self.progress_label = tk.Label(self.progress_frame, text="0%", bg="lightgray")
        self.progress_label.pack(pady=5)
        
        
    def update_controls(self, tab_name):
        for widget in self.control_panel.winfo_children():
            widget.destroy()
        
        if tab_name == "Clean Upload":
            tk.Label(self.control_panel, text="No JSON loaded.", bg="white").pack(pady=5)
            tk.Button(self.control_panel, text="Load JSON", command=self.load_json).pack(pady=5)
            tk.Button(self.control_panel, text="Run Clean Upload", command=self.run_upload).pack(pady=5)
        
        elif tab_name == "Media Discovery":
            tk.Button(self.control_panel, text="Scan Media", command=self.scan_media).pack(pady=5)
        
        elif tab_name == "Media Organizer":
            tk.Button(self.control_panel, text="Organize Media", command=self.organize_media).pack(pady=5)
        
        elif tab_name == "Scanned Albums":
            tk.Button(self.control_panel, text="Load Scanned", command=self.load_scanned).pack(pady=5)
            tk.Button(self.control_panel, text="Move Albums", command=self.move_albums).pack(pady=5)
            
    def on_tab_change(self, event):
        tab_name = event.widget.tab(event.widget.select(), "text")
        self.update_controls(tab_name)
    
    def handle_drop(self, event, tab_name):
        dropped_path = event.data.strip("{}")
        if os.path.isdir(dropped_path):
            self.dropped_paths[tab_name] = dropped_path # store only latest
            self.log_console(f"[{tab_name}] Folder dropped: {dropped_path}")
        else:
            self.log_console(f"[{tab_name}] Invalid drop: Not a folder - {dropped_path}")
            
    def log_console(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        
    def update_progress(self, percent):
        try:
            self.progress_var.set(percent)
            self.progress_label.config(text=f"{percent:.1f}%")
            self.progress_frame.update_idletasks()
        except Exception as e:
            self.log_console(f"[Progress Error] {e}")    
    
    def load_json(self):
        self.log_console("Load JSON clicked.")
            
    def run_upload(self):
        source_folder = self.dropped_paths.get("Clean Upload")
        if not source_folder:
            self.log_console("[Clean Upload] No folder dropped.")
            return
        
        self.log_console("Select destination folder for cleaned upload...")
        dest = filedialog.askdirectory(title="Select destination folder")
        if not dest:
            self.log_console("[Clean Upload] No destination selected.")
            return
        
        self.log_console(f"[Clean Upload] Copying from: {source_folder}")
        self.log_console(f"[Clean Upload] To: {dest}")
        
        threading.Thread(
            target=self.run_upload_thread,
            args=(source_folder, dest),
            daemon=True
        ).start()
        
    def run_upload_thread(self, source_folder, target_folder):
        try:
            clean_upload.run_clean_upload(source_folder, target_folder, log=self.log_console)
            self.log_console("[Clean Upload] Upload complete.")
        except Exception as e:
            self.log_console(f"[Clean Upload] Error: {str(e)}")
        
    def scan_media(self):
        folder = self.dropped_paths.get("Media Discovery", [None])[-1]
        if not folder:
            self.log_console("No folder dropped for Media Discovery.")
            return
        self.log_console(f"Scanning media in: {folder}")
        
        threading.Thread(
            target=photo_scan.run_photo_scan,
            args=(folder,),
            kwargs={
                "log": self.log_console,
                "progress_callback": self.update_progress
            },
            daemon=True
        ).start()
    
    def organize_media(self):
        self.log_console("[Media Organizer] Starting input collection...")
        self.after(0, self.collect_organize_inputs)
        
    def collect_organize_inputs(self):
        json_path = filedialog.askopenfilename(
            title="Select media JSON file.",
            filetypes=[("JSON files", ".json")]
        )
        if not json_path:
            self.log_console("[Media Organizer] No JSON selected.")
            return
        
        base_path = filedialog.askdirectory(
            title="Select destination base folder."
        )
        if not base_path:
            self.log_console("[Media Organizer] No destination folder selected.")
            return
        
        folder_name = askstring(
            "Organized Album",
            "Enter a name for the organized folder (e.g., 'Family_Album'):"
        )
        if not folder_name:
            self.log_console("[Media Organizer] Folder name required.")
            return
        
        # All inputs collected safely - run background logic
        threading.Thread(
            target=self.organize_media_thread,
            args=(json_path, base_path, folder_name),
            daemon=True
        ).start()
    
    def organize_media_thread(self, json_path, base_path, folder_name):    
        try:
            start_time = time.time()
            
            media_dict = cross_pic_organizer.load_media_json(json_path, log=self.log_console)
            if not media_dict:
                self.log_console("[Media Organizer] Failed to load or empty JSON.")
                return
            
            cross_pic_organizer.organize_media(
                media_dict, 
                base_path, 
                folder_name, 
                log=self.log_console,
                progress_callback=self.update_progress
            )
            self.update_progress(100)
            self.log_console(f"[Media Organizer] Media organized into: {os.path.join(base_path, folder_name)}")
            
            # Calculate elapsed time
            elapsed = time.time() - start_time
            h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
            self.log_console(f"[Media Organizer] Total runtime: {h:02}:{m:02}:{s:02}")
            
        except Exception as e:
            self.log_console(f"[Media Organizer] Error: {str(e)}")
                    
    def load_scanned(self):
        folder = self.dropped_paths.get("Scanned Albums", [None])[-1]
        if not folder:
            self.log_console("[Scanned Albums] No scanned folders dropped.")
            return
        self.log_console(f"[Scanned Albums] Organizing: {folder}")
        
        # Optional: prompt for album name and tags
        album_name = askstring("Default Album", "Enter default album name:")
        if not album_name:
            self.log_console("[Scanned Albums] No album name provided.")
            return

        tags_input = askstring("Tags", "Enter tags (comma separated):")
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        
        date_start = askstring("Start Date", "Enter start date (e.g., 8-4-25 or Aug 4 2025):")
        date_end = askstring("End Date", "Enter end date (e.g., 8-9-25 or Aug 9 2025):")
        if not date_start or not date_end:
            self.log_console("[Scanned Albums] Start and end dates are required.")
            return
        
        self.log_console(f"[Scanned Albums] Filtering by date: {date_start} to {date_end}")
        
        threading.Thread(
            target=scanned_album.scan_scanned_photos,
            args=(folder,),
            kwargs={
                "batch_mode": True,
                "default_album": album_name,
                "default_tags": tags,
                "date_start": date_start,
                "date_end": date_end,
                "log": self.log_console
            },
            daemon=True
        ).start()
        
    def move_albums(self):
        self.log_console("Moving scanned albums...")        
        
        
            
if __name__ == "__main__":
    app = PhotoToolsApp()
    app.mainloop()