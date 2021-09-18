# Module imports
from logging import error, warning
from tkinter import *
import tkinter as tk
from tkinter import ttk
import tkinter.font
from tkinter.ttk import Style
from datetime import datetime
import os
from os import path
from urllib.request import urlopen
import io
from PIL import Image, ImageTk
import sys
import ctypes
import pyglet
import random
import spotipy_ross_edited as spotipy
from spotipy_ross_edited.oauth2 import SpotifyPKCE
import sys
import threading
import queue

# Control pyinstaller splashscreen
try:
    import pyi_splash
    pyi_splash.update_text("Loading")
except:
    pass

# Fix blurryness  
if 'win' in sys.platform:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

class SpotifyAdder:

    # Function to initialise everything
    def __init__(self, master):

        # Remove splashscreen
        try: 
            pyi_splash.close()
        except:
            pass

        # Set up master window dimensions
        self.master = master
        self.master.title("ROSSpotify")
        #self.master.config(background="white")
        #self.master.option_add("*background", "white")
        self.master.columnconfigure(0, minsize=300)
        self.master.columnconfigure(1, minsize=300)
        self.padx = 7
        self.pady = 7

        # Font
        self.font_family = "Courier Prime"
        self.font_weight = "bold"
        pyglet.font.add_file('./program_files/font/CourierPrime-Regular.ttf')
        pyglet.font.add_file('./program_files/font/CourierPrime-bold.ttf')
        pyglet.font.add_file('./program_files/font/GothamBold.ttf')
        pyglet.font.add_file('./program_files/font/GothamMedium.ttf')
        for named_font in ["TkDefaultFont"]:
            temp_font = tkinter.font.nametofont(named_font)
            temp_font.config(family=self.font_family, weight=self.font_weight)
            self.master.option_add("*Font", temp_font)

        # Set style
        self.master.call("source", "./program_files/theme/forest-dark.tcl")
        style = Style(self.master)
        style.theme_use("forest-dark")
        style.configure("TButton", font=(self.font_family, 9, self.font_weight), padding=(8,4,8,4))
        style.configure("Small.Accent.TButton", font=(self.font_family, 9, self.font_weight), padding=(0,0,0,0))
        style.configure("TLabelframe.Label", font=(self.font_family, 9, self.font_weight))
        style.configure("TOptionMenu.Button", font=(self.font_family, 9, self.font_weight))
        style.configure("TNotebook.Tab", font=(self.font_family, 9, self.font_weight))
        style.configure("TMenubutton", font=(self.font_family, 9, self.font_weight))
        #element = "TMenubutton.Label"
        #print(style.layout(element))
        #print(style.element_options(element))

        # Icon
        ico = Image.open("./program_files/images/icon.ico")
        self.icon = ImageTk.PhotoImage(ico)
        self.master.iconphoto(False, self.icon)

        # Dummy image
        self.dummy_image = tk.PhotoImage(file="./program_files/images/dummy_image.png")
        self.small_dummy_image = tk.PhotoImage(file="./program_files/images/small_dummy_image.png")

        # Add image
        self.add_image = tk.PhotoImage(file="./program_files/images/add_image.png")

        # Limit for song attributes length
        self.entry_limit=30

        # Authentication url and queue
        self.url = StringVar(value="Paste redirect URL")
        self.q = queue.Queue()

        # Add Notebook widget
        self.notebook = ttk.Notebook(height=100)
        self.notebook.grid(column=1, row=0, rowspan=3, sticky=N+S+E+W, padx=self.padx, pady=self.pady)

        # Set up LabelFrame widgets
        self.playlist_frame = ttk.LabelFrame(self.master, text="Playlist")
        self.playlist_frame.grid(column=0, row=1, sticky=N+S+E+W, padx=self.padx, pady=self.pady)
        self.log_frame = ttk.LabelFrame(self.master, text="Log")
        self.log_frame.grid(column=0, row=2, sticky=N+S+E+W, padx=self.padx, pady=self.pady)
        self.search_tracks_frame = ttk.Frame(self.notebook)
        self.search_results_frame = ttk.LabelFrame(self.search_tracks_frame, text="Search Results")
        self.search_results_frame.grid(row=1, column=0, columnspan=2, sticky=N+S+W+E, padx=self.padx, pady=self.pady)
        self.add_track_by_link_frame = ttk.Frame(self.notebook)
        self.added_tracks_frame = ttk.Frame(self.notebook)
        self.width_controller = ttk.Frame(self.notebook)
        #self.added_tracks_frame.grid(column=1, row=0, rowspan=3, sticky=N+S+E+W, padx=self.padx, pady=self.pady)

        # Add frames to notebook
        self.notebook.add(self.added_tracks_frame, sticky=N+E+S+W, text="Added Tracks")
        self.notebook.add(self.search_tracks_frame, sticky=N+E+S+W, text="Add Tracks by Search")
        self.notebook.add(self.add_track_by_link_frame, sticky=N+E+S+W, text="Add Tracks by Link")
        self.notebook.add(self.width_controller, sticky=N+E+S+W, text="Width Controller")
        self.notebook.hide(self.width_controller)

        # Set up playlist_frame contents
        self.playlists = {}
        self.username = ""
        self.selected_playlist = StringVar(value="Select playlist")
        self.playlist_optionmenu = ttk.OptionMenu(self.playlist_frame, variable=self.selected_playlist, default="Select playlist", command=lambda x: self.load_playlist())
        self.playlist_optionmenu.grid(row=3, column=0, sticky=N+S+E+W, padx=self.padx, pady=self.pady, rowspan=2, columnspan=2)
        self.playlist_optionmenu.config(width=25)
        self.playlist_label = ttk.Label(self.playlist_frame, text="Playlist size:", anchor=CENTER)
        self.playlist_label.grid(row=3, column=2, sticky=N+S+W+E, padx=self.padx)
        self.playlist_size_label = ttk.Label(self.playlist_frame, text="0", anchor=CENTER)
        self.playlist_size_label.grid(row=4, column=2, sticky=N+S+E+W, padx=self.padx)
        self.token_button = ttk.Button(self.playlist_frame, text="Authenticate/load token", style="Accent.TButton", command=self.load_token)
        self.token_button.grid(row=0, column=0, sticky=N+S+W+E, padx=self.padx, pady=self.pady, columnspan=2, rowspan=2)
        self.delete_token_button = ttk.Button(self.playlist_frame, text="Delete token", style="Accent.TButton", command=lambda: self.load_token(delete=True))
        self.delete_token_button.grid(row=2, column=0, sticky=N+S+W+E, padx=self.padx, pady=self.pady, columnspan=2)
        self.token_label = ttk.Label(self.playlist_frame, text="Current token:", anchor=CENTER)
        self.token_label.grid(row=0, column=2, sticky=S+W+E, padx=self.padx)
        self.current_token_label = ttk.Label(self.playlist_frame, text="none", anchor=CENTER)
        self.current_token_label.grid(row=1, column=2, sticky=N+E+W, padx=self.padx, rowspan=2)

        # set up log_frame contents
        self.log_listbox_width = 44
        self.log_listbox_height = 15
        self.log_listbox = Listbox(self.log_frame, state=NORMAL, width=self.log_listbox_width, relief=FLAT, height=self.log_listbox_height, selectbackground=None, selectborderwidth=0, activestyle="none", selectforeground="white", highlightthickness=0)
        self.log_listbox.grid(sticky=N+S+E+W, pady=self.pady, padx=self.padx)

        # Set up added_tracks_frame contents
        self.new_album_images = []
        self.old_album_images = []
        self.added_tracks = {}
        self.added_tracks_length = 10
        #self.added_tracks_frame.columnconfigure(0, weight=1, minsize=40)
        self.added_tracks_frame.columnconfigure(1, weight=1)
        self.added_tracks_frame.columnconfigure(2, weight=1)
        #self.added_tracks_frame.columnconfigure(3, weight=1, minsize=40)
        self.cover_art_labels = []
        self.title_labels = []
        self.artist_album_labels = []
        self.remove_buttons = []
        for i in range(self.added_tracks_length):
            if i < 9:
                number_spacing = "  "
            else:
                number_spacing = " "
            # Column
            self.added_tracks_frame.rowconfigure(i, weight=1)
            # Cover art
            cover_art_label = ttk.Label(self.added_tracks_frame, image=self.dummy_image, text=str(i+1)+number_spacing, compound=RIGHT)
            cover_art_label.grid(row=i, column=0, sticky=N+S+E+W, padx=self.padx*3)
            self.cover_art_labels.append(cover_art_label)
            # Title
            title_label = ttk.Label(self.added_tracks_frame, text=self.entry_limit*" ")
            title_label.grid(row=i, column=1, sticky=N+S+E+W, padx=self.padx)
            self.title_labels.append(title_label)
            # Artist/album
            artist_album_label = ttk.Label(self.added_tracks_frame, text=(self.entry_limit+8)*" "+"\n")
            artist_album_label.grid(row=i, column=2, sticky=N+S+E+W, padx=self.padx)
            self.artist_album_labels.append(artist_album_label)
            # Remove button
            remove_button = ttk.Button(self.added_tracks_frame, text="Remove", style="Accent.TButton")
            remove_button.grid(row=0, column=3, padx=self.padx*3, sticky=W+E)
            remove_button.grid_forget()
            self.remove_buttons.append(remove_button)
        
        # Set up search_tracks_frame
        self.search_tracks_frame.columnconfigure(0, weight=2)
        self.search_tracks_frame.columnconfigure(1, weight=1)
        self.search_tracks_frame.rowconfigure(0, weight=1)
        self.search_tracks_frame.rowconfigure(1, weight=10)
        self.searched_tracks = {}
        self.searched_tracks_length = 10
        # Search bar
        self.searched_text = StringVar(value="Search for track")
        self.search_bar = ttk.Entry(self.search_tracks_frame, textvariable=self.searched_text, width=40)
        self.search_bar.grid(row=0, column=0, padx=self.padx, pady=self.pady, sticky=W+E)
        # Search button
        self.search_button = ttk.Button(self.search_tracks_frame, text="Search", style="Accent.TButton", command=self.search_spotify)
        self.search_button.grid(row=0, column=1, padx=self.padx*3, pady=self.pady, sticky=W+E)
        # Search results frame
        self.search_results_frame.columnconfigure(1, weight=1)
        self.search_results_frame.columnconfigure(2, weight=1)
        self.search_cover_art_labels = []
        self.search_title_labels = []
        self.search_artist_album_labels = []
        self.search_add_buttons = []
        for i in range(self.searched_tracks_length):
            # Column
            self.search_results_frame.rowconfigure(i, weight=1)
            # Cover art
            cover_art_label = ttk.Label(self.search_results_frame, image=self.small_dummy_image, text="   ", compound=RIGHT)
            cover_art_label.grid(row=i, column=0, sticky=N+S+E+W, padx=self.padx*3)
            self.search_cover_art_labels.append(cover_art_label)
            # Title
            title_label = ttk.Label(self.search_results_frame, text=self.entry_limit*" ")
            title_label.grid(row=i, column=1, sticky=N+S+E+W, padx=self.padx)
            self.search_title_labels.append(title_label)
            # Artist/album
            artist_album_label = ttk.Label(self.search_results_frame, text=self.entry_limit*" ")
            artist_album_label.grid(row=i, column=2, sticky=N+S+E+W, padx=self.padx)
            self.search_artist_album_labels.append(artist_album_label)
            # Remove button
            add_button = ttk.Button(self.search_results_frame, image=self.add_image, style="Small.Accent.TButton")
            self.search_add_buttons.append(add_button)
        
        # Set up width controller
        self.width_controller.columnconfigure(1, weight=1)
        self.width_controller.columnconfigure(2, weight=1)
        number_spacing = "  "
        # Column
        self.width_controller.rowconfigure(0, weight=1)
        # Cover art
        cover_art_label = ttk.Label(self.width_controller, image=self.dummy_image, text=str(i+1)+number_spacing, compound=RIGHT)
        cover_art_label.grid(row=0, column=0, sticky=N+S+E+W, padx=self.padx*3)
        # Title
        title_label = ttk.Label(self.width_controller, text=self.entry_limit*" ")
        title_label.grid(row=0, column=1, sticky=N+S+E+W, padx=self.padx)
        # Artist/album
        artist_album_label = ttk.Label(self.width_controller, text=(self.entry_limit+8)*" "+"\n")
        artist_album_label.grid(row=0, column=2, sticky=N+S+E+W, padx=self.padx)
        # Remove button
        remove_button = ttk.Button(self.width_controller, text="Remove", style="Accent.TButton")
        remove_button.grid(row=0, column=3, padx=self.padx*3, sticky=W+E)

        # Set up add_track_by_link frame
        self.add_track_by_link_frame.columnconfigure(0, weight=2)
        self.add_track_by_link_frame.columnconfigure(1, weight=1)
        # Search bar
        self.searched_link = StringVar(value="Paste link")
        self.link_search_bar = ttk.Entry(self.add_track_by_link_frame, textvariable=self.searched_link, width=40)
        self.link_search_bar.grid(row=0, column=0, padx=self.padx, pady=self.pady, sticky=W+E)
        # Find button
        self.find_button = ttk.Button(self.add_track_by_link_frame, text="Add", style="Accent.TButton", command=self.add_remove_track)
        self.find_button.grid(row=0, column=1, padx=self.padx*3, pady=self.pady, sticky=W+E)

        # Set up loading bar
        self.loading_bar_value = IntVar()
        self.loading_bar = ttk.Progressbar(self.master, variable=self.loading_bar_value)
        self.loading_bar.grid(row=3, column=0, columnspan=2, sticky=N+S+E+W)

        # Disable input
        self.disable_input()

        # Define error_code variable
        self.error_code = 0

        # Logo, which resizes itself to fit space
        self.master.update_idletasks()
        width = self.playlist_frame.winfo_width()
        height = width*94/417
        #self.logo_image = ImageTk.PhotoImage(file="./program_files/images/Logo05.png")
        self.logo_image = Image.open("./program_files/images/Logo05.png")
        self.logo_image = self.logo_image.resize((int(width), int(height)), Image.ANTIALIAS)
        self.logo_image = ImageTk.PhotoImage(self.logo_image)
        #self.logo_canvas = Canvas(self.master, height=height-self.pady, width=width-self.padx)
        #self.logo_canvas.grid(row=0, column=0, sticky=N+E+S+W, pady=self.pady, padx=self.padx)
        #self.logo_canvas.create_image(0, 0, image=self.logo_image, anchor=NW)
        ttk.Label(self.master, image=self.logo_image).grid(row=0, column=0, padx=self.padx, pady=self.pady)

        # Fix window size
        self.master.update_idletasks()
        self.master.maxsize(self.master.winfo_width(), self.master.winfo_height())
        self.master.minsize(self.master.winfo_width(), self.master.winfo_height())

        # Window position
        #x_pos = int(self.master.winfo_screenwidth()/2 - self.master.winfo_width()/2)
        #y_pos = int(self.master.winfo_screenheight()/2 - self.master.winfo_height()/2)
        #self.master.geometry(f'+{x_pos}+{y_pos}')
    
    # Function to disable frame
    def disable_frame(self, frame):
        for child in frame.winfo_children():
            try:
                child.config(state=DISABLED)
            except:
                self.disable_frame(child)
    
    # Function to enable frame
    def enable_frame(self, frame):
        for child in frame.winfo_children():
            try:
                child.config(state=NORMAL)
            except:
                self.enable_frame(child)
    
    # Function to disable input
    def disable_input(self, all=False):
        self.disable_frame(self.added_tracks_frame)
        self.disable_frame(self.search_tracks_frame)
        self.disable_frame(self.add_track_by_link_frame)
        self.playlist_optionmenu.config(state=DISABLED)
        if all:
            self.disable_frame(self.playlist_frame)
        self.add_to_log("App input disabled")

    # Function to enable input
    def enable_input(self):
        # Does not enable self.search_tracks_frame, self.added_tracks_frame or self.add_track_by_link_frame. These are enabled in self.load_playlist()
        self.playlist_optionmenu.config(state=NORMAL)
        self.add_to_log("App input enabled")
    
    # Function to reset interface
    def reset_interface(self):
        self.add_to_log("Resetting interface")
        self.selected_playlist.set(value="Select playlist")
        self.searched_text.set(value="Search for track")
        self.playlist_size_label.config(text="0")
        self.token_button.config(text="Authenticate/load token")
        self.current_token_label.config(text="none")
        self.new_album_images = []
        self.old_album_images = []
        self.playlists = {}
        self.added_tracks = {}
        self.searched_tracks = {}
        self.username = ""
        self.url.set("Paste redirect URL")
        self.build_added_tracks_panel()
        self.build_searched_tracks_panel()
        self.disable_input()
    
    # Function to make loading bar look nicer
    def increment_loading_bar(self, inc):
        if inc == "end":
            self.increment_loading_bar(100 - self.loading_bar_value.get())
        else:
            for n in range(inc):
                self.loading_bar.step()
                if n % 5 == 0:
                    self.master.update_idletasks()
    
    # Function to save added tracks to cache
    def save_tracks_to_cache(self):
        name = self.selected_playlist.get() 
        playlist = self.playlists[name]
        cache_path = playlist["id"] + ".txt"
        with open(cache_path, "w") as open_file:
            for track in self.added_tracks:
                open_file.write(track + "\n")
        self.add_to_log("Added tracks saved to cache")
    
    # Function to find track data from link
    def find_track_from_link(self):
        track = self.searched_link.get().split("/")[-1].split("?")[0]
        self.add_to_log("Track ID \"{}\" parsed from Spotify link".format(track))
        return(track)

    # Function to retrieve song data and return dictionary
    def get_track_data(self, id, small_cover_art=False):
        track = self.sp.track(id)
        title = track["name"]
        artists = ""
        for artist in track["artists"]:
            artists += artist["name"] + ", "
        artists = artists[:-2]
        album = track["album"]["name"]
        if small_cover_art:
            photo_image = self.small_dummy_image
        else:
            cover_art_url = track['album']['images'][0]['url']
            my_page = urlopen(cover_art_url)
            my_picture = io.BytesIO(my_page.read())
            pil_img = Image.open(my_picture)
            pil_img = pil_img.resize((50, 50), Image.ANTIALIAS)
            photo_image = ImageTk.PhotoImage(pil_img)
        temp_dict = {"title": title, "artists": artists, "album": album, "photo_image": photo_image}
        # Trim entry lengths
        for entry in temp_dict:
            if (entry != "photo_image") and (len(temp_dict[entry]) > self.entry_limit):
                temp_dict[entry] = temp_dict[entry][:self.entry_limit-3] + "..."
        return(temp_dict)

    # Function to load token and print user
    def load_token(self, delete=False):
        self.error_code = 0
        try:
            # Reset variables and disable input
            self.reset_interface()
            self.error_code = 1
            # Get token
            if not path.exists(".cache"):
                self.error_code = 5
                raise RuntimeError
            if delete:
                self.error_code = 6
                os.remove(".cache")
                self.add_to_log("Authentication token deleted")
            else:
                self.error_code = 1
                token = spotipy.util.prompt_for_user_token(client_id="eca85ec5b16f4d68bee4d4837b1e5a7a", client_secret="aba697f50375423099a18bfb3d6987e4", redirect_uri="https://i.pinimg.com/originals/b4/6d/e7/b46de7a28f5d449c679ed8fc629c7a95.png")
                self.add_to_log("Authentication token loaded from cache")
                self.error_code = 2
                self.increment_loading_bar(25)
                # Get account access
                self.sp = spotipy.Spotify(auth=token)
                self.add_to_log("Gained account access")
                self.error_code = 3
                self.increment_loading_bar(25)
                # Populate playlist dict and get account name
                self.username = self.sp.current_user()["display_name"]
                playlist_names = self.populate_playlist_dict()
                if len(self.username) > 11:
                    self.username = self.username[:11] + "..."
                self.current_token_label.config(text=self.username)
                self.error_code = 4
                self.increment_loading_bar(25)
                # Destroy and rebuild playlist_optionmenu
                self.playlist_optionmenu.destroy()
                self.playlist_optionmenu = ttk.OptionMenu(self.playlist_frame, self.selected_playlist, "Select playlist", *playlist_names, command=lambda x: self.load_playlist())
                self.playlist_optionmenu.grid(row=3, column=0, sticky=N+S+E+W, padx=self.padx, pady=self.pady, rowspan=2, columnspan=2)
                self.playlist_optionmenu.config(width=25)
                self.add_to_log("Refreshed OptionMenu")
                self.enable_input()
                self.increment_loading_bar(25)
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to reset interface", warning=True)
            elif self.error_code == 1:
                self.add_to_log("Authentication token was located, but could not be loaded from cache", warning=True)
            elif self.error_code == 2:
                self.add_to_log("Failed to access account using authentication token", warning=True)
            elif self.error_code == 3:
                self.add_to_log("Failed to retrieve playlist and user data from account", warning=True)
            elif self.error_code == 4:
                self.add_to_log("Failed to refresh OptionMenu", warning=True)
            elif self.error_code == 5:
                self.add_to_log("Failed to locate authentication token", warning=True)
            elif self.error_code == 6:
                self.add_to_log("Failed to remove authentication token")
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
            self.increment_loading_bar("end")
            if (self.error_code == 5) and (not delete):
                self.authenticate_token()
    
    # Function to lauch new window and authenticate token
    def authenticate_token(self):
        self.error_code = 1
        self.add_to_log("Launching authentication window")
        try:
            while not self.q.empty():
                    self.q.get(block=False)
            self.auth_window = Toplevel(takefocus=True)
            x_pos = int(self.master.winfo_rootx() + self.master.winfo_width()/2 - 457/2)
            y_pos = int(self.master.winfo_rooty() + self.master.winfo_height()/2 - 256/2)
            self.auth_window.geometry(f'+{x_pos}+{y_pos}')
            self.auth_window.transient(self.master)
            self.auth_window.title("Authentication window")
            self.auth_window.iconphoto(False, self.icon)
            self.auth_window.protocol('WM_DELETE_WINDOW', lambda: self.add_url_to_q(spoil=True))
            ttk.Label(self.auth_window, text="Please follow the instructions below to generate\na new authentication token.\n\n1. Log in to Spotify using the button below.\n\n2. Copy and paste the URL of the webpage you are\n   redirected to into the box, and press \"Submit\".").grid(row=0, column=0, columnspan=2, sticky=N+E+S+W, padx=self.padx, pady=self.pady)
            self.login_button = ttk.Button(self.auth_window, text="Log in to Spotify account", style="Accent.TButton", command=self.authenticate)
            self.login_button.grid(row=1, column=0, columnspan=2, sticky=N+S+E+W, pady=self.pady, padx=self.padx)
            ttk.Entry(self.auth_window, textvariable=self.url, width=25).grid(row=2, column=0, padx=self.padx, pady=self.pady, sticky=W+E)
            ttk.Button(self.auth_window, text="Submit", style="Accent.TButton", command=self.add_url_to_q).grid(row=2, column=1, pady=self.padx, padx=self.pady, sticky=N+E+S+W)
            self.auth_window.grab_set()
            self.auth_window.update_idletasks()
            self.auth_window.minsize(self.auth_window.winfo_width(), self.auth_window.winfo_height())
            self.auth_window.maxsize(self.auth_window.winfo_width(), self.auth_window.winfo_height())
        except:
            # Log error
            if self.error_code == 1:
                self.add_to_log("Failed to launch authentication window", warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)

    # Function to get authentication token
    def authenticate(self):
        self.error_code = 0
        try:
            auth_manager = SpotifyPKCE("eca85ec5b16f4d68bee4d4837b1e5a7a", "https://i.pinimg.com/originals/b4/6d/e7/b46de7a28f5d449c679ed8fc629c7a95.png", None, "playlist-modify-public", self.q)
            self.error_code = 1
            self.add_to_log("Prompted user to login to Spotify")
            self.auth_thread = threading.Thread(target=auth_manager.get_access_token)
            self.auth_thread.start()
            self.add_to_log("Started authentication package thread")
            self.login_button.config(state=DISABLED)
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to prompt user to login to Spotify", warning=True)
            elif self.error_code == 1:
                self.add_to_log("Failed to start authentication package thread", warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
    
    # Function to pass url to spotipy thread
    def add_url_to_q(self, spoil=False):
        self.error_code = 2
        status = "NOT RETRIEVED"
        try:
            self.auth_window.destroy()
            self.add_to_log("Destroyed authentication window")
            if not self.auth_thread.is_alive():
                raise RuntimeError
            self.error_code = 0
            try:
                status = self.q.get(block=False)
            except:
                pass
            if status == "FAILURE":
                raise RuntimeError
            if spoil:
                self.q.put("spoil")
            else:
                self.q.put(self.url.get())
            self.add_to_log("Sent URL to authentication package thread")
            self.auth_thread.join()
            self.add_to_log("Merged threads")
            self.error_code = 1
            try:
                status = self.q.get(block=False)
            except:
                status = "EMPTY"
            if (status == "FAILURE") or (status == "EMPTY"):
                raise RuntimeError
            self.add_to_log("Successfully generated authentication token")
            self.load_token()
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to merge threads (q status: {})".format(status), warning=True)
            elif self.error_code == 1:
                self.add_to_log("Authentication package thread failed to generate token (q status: {})".format(status), warning=True)
            elif self.error_code == 2:
                self.add_to_log("Authentication package thread was not started (q status: {})".format(status), warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
    
    # Function which attemps to destroy thread
    def destroy_thread(self):
        pass

        
    # Function to call when playlist is selected
    def load_playlist(self):
        self.error_code = 0
        try:
            self.added_tracks = {}
            name = self.selected_playlist.get() 
            playlist = self.playlists[name]
            # Change size label
            self.playlist_size_label.config(text=str(len(playlist["tracks"])))
            self.add_to_log("Accessed playlist dictionary")
            self.increment_loading_bar(10)
            # Load playlist track cache
            cache_path = playlist["id"] + ".txt"
            if path.exists(cache_path):
                self.error_code = 1
                with open(cache_path, "r") as open_file:
                    self.add_to_log("Track cache accessed for playlist \"{}\"".format(name))
                    # Add track ids to list
                    track_ids = open_file.readlines()
                    for id in track_ids:
                        id = id.strip()
                        # Perform checks
                        track_data = self.get_track_data(id)
                        if id in self.added_tracks:
                            self.add_to_log("Failed check: duplicate of \"{}\" found in cache and deleted".format(track_data["title"]), warning=True)
                        elif id not in playlist["tracks"]:
                            self.add_to_log("Failed check: deleted \"{}\" as it is not present in playlist".format(track_data["title"]), warning=True)
                        else:
                            self.added_tracks[id] = track_data
                        self.increment_loading_bar(5)
                self.save_tracks_to_cache()
                self.add_to_log("Track data for {} track(s) retrieved from Spotify and added to added tracks dictionary".format(len(self.added_tracks)))
            else:
                self.error_code = 2
                self.add_to_log("Track cache not found for playlist \"{}\"".format(name), warning=True)
                with open(cache_path, "w") as open_file:
                    self.add_to_log("New track cache created for playlist \"{}\"".format(name))
            self.error_code = 3
            self.increment_loading_bar(10)
            self.enable_frame(self.added_tracks_frame)
            self.enable_frame(self.search_tracks_frame)
            self.enable_frame(self.add_track_by_link_frame)
            self.add_to_log("Enabled Notebook frames")
            self.error_code = 4
            self.increment_loading_bar(15)
            self.build_added_tracks_panel()
            self.increment_loading_bar("end")
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to access playlist dictionary", warning=True)
            elif self.error_code == 1:
                self.add_to_log("Failed to retrieve track data from Spotify", warning=True)
            elif self.error_code == 2:
                self.add_to_log("Failed to create new track cache", warning=True)
            elif self.error_code == 3:
                self.add_to_log("Failed to enable Notebook frames", warning=True)
            elif self.error_code == 4:
                self.add_to_log("Failed to build added tracks frame", warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
            self.increment_loading_bar("end")
    
    # Function to build added tracks panel
    def build_added_tracks_panel(self):
        # Get indexes to reset
        indexes_to_reset = []
        for i in range(self.added_tracks_length):
            if i >= len(self.added_tracks):
                indexes_to_reset.append(i)
        # Reset contents
        for index in indexes_to_reset:
            self.remove_buttons[index].grid_forget()
            self.title_labels[index].config(text=self.entry_limit*" ")
            self.artist_album_labels[index].config(text=(self.entry_limit+8)*" "+"\n")
            # Add dummy images back
            self.cover_art_labels[index].config(image=self.dummy_image)
        # Add track cards
        track_counter = 0
        for track in self.added_tracks:
            track_data = self.added_tracks[track]
            # Cover art
            self.new_album_images.append(track_data["photo_image"])
            self.cover_art_labels[track_counter].config(image=self.new_album_images[-1])
            # Title
            self.title_labels[track_counter].config(text=track_data["title"])
            # Artist/album
            self.artist_album_labels[track_counter].config(text="Artist: {}\nAlbum: {}".format(track_data["artists"], track_data["album"]))
            # Remove button
            self.remove_buttons[track_counter].grid(row=track_counter, column=3, padx=self.padx*3, sticky=W+E)
            self.remove_buttons[track_counter].config(command=lambda track=track: self.add_remove_track(track, action="remove"))
            track_counter += 1
        self.old_album_images = self.new_album_images.copy()
        self.new_album_images = []
        self.add_to_log("Refreshed added tracks frame")

    # Function to search spotify and make self.searched_tracks
    def search_spotify(self):
        self.error_code = -1
        try:
            self.searched_tracks = {}
            self.build_searched_tracks_panel()
            self.error_code = 0
            search_query = self.searched_text.get().strip().replace(" ", "+")
            self.add_to_log("Using search query \"{}\"".format(search_query))
            search_results = self.sp.search(search_query, limit=self.searched_tracks_length)["tracks"]["items"]
            self.add_to_log("Search yielded {} result(s)".format(len(search_results)))
            self.error_code = 1
            self.increment_loading_bar(10)
            # Get track data and add to searched tracks dictionary
            for track in search_results:
                id = track["id"].strip()
                self.searched_tracks[id] = self.get_track_data(id, small_cover_art=True)
                self.increment_loading_bar(5)
            self.add_to_log("Track data for {} track(s) retrieved from Spotify".format(len(search_results)))
            self.error_code = 2
            self.increment_loading_bar(5)
            self.build_searched_tracks_panel()
            self.increment_loading_bar("end")
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to access search results", warning=True)
            elif self.error_code == 1:
                self.add_to_log("Failed to retrieve track data from Spotify", warning=True)
            elif self.error_code == 2:
                self.add_to_log("Failed to build searched tracks frame", warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
            self.increment_loading_bar("end")

    # Function to build the searched tracks panel
    def build_searched_tracks_panel(self):
        # Get indexes to reset
        indexes_to_reset = []
        for i in range(self.searched_tracks_length):
            if i >= len(self.searched_tracks):
                indexes_to_reset.append(i)
        # Reset contents
        for index in indexes_to_reset:
            self.search_add_buttons[index].grid_forget()
            self.search_title_labels[index].config(text=self.entry_limit*" ")
            self.search_artist_album_labels[index].config(text=self.entry_limit*" ")
            # Add dummy images back
            self.search_cover_art_labels[index].config(image=self.small_dummy_image, text="   ")
        # Add track cards
        track_counter = 0
        for track in self.searched_tracks:
            if track_counter < 9:
                number_spacing = "  "
            else:
                number_spacing = " "
            track_data = self.searched_tracks[track]
            # Cover art
            self.search_cover_art_labels[track_counter].config(image=track_data["photo_image"], text=str(track_counter+1)+number_spacing)
            # Title
            self.search_title_labels[track_counter].config(text=track_data["title"])
            # Artist/album
            self.search_artist_album_labels[track_counter].config(text=track_data["artists"])
            # Add button
            self.search_add_buttons[track_counter].grid(row=track_counter, column=3, padx=self.padx*3, sticky=W+E)
            self.search_add_buttons[track_counter].config(command=lambda track=track: self.add_remove_track(track, action="add"))
            track_counter += 1
        self.add_to_log("Refreshed searched tracks frame")
    
    # Function to add or remove track
    def add_remove_track(self, track=None, action="add"):
        self.error_code = 0
        try:
            # Check if track is being added from link
            if track == None:
                track = self.find_track_from_link()
            # Get track data and perform checks
            if action=="add":
                self.error_code = 1
                track_data = self.get_track_data(track)
                self.add_to_log("Track data for \"{}\" retrieved from Spotify".format(track_data["title"]))
                if track in self.added_tracks:
                    self.error_code = 2
                    raise RuntimeError
                if len(self.added_tracks) == self.added_tracks_length:
                    self.error_code = 3
                    raise RuntimeError
            self.error_code = 4
            self.increment_loading_bar(15)
            # Retrieve playlist data
            self.populate_playlist_dict()
            self.error_code = 5
            self.increment_loading_bar(15)
            playlist = self.playlists[self.selected_playlist.get()]
            # Add or remove track from playlists
            if action=="add":
                playlist["tracks"].append(track)
                self.add_to_log("Track added to playlist dictionary")
            elif action=="remove":
                playlist["tracks"].remove(track)
                self.add_to_log("Track removed from playlist dictionary")
            self.error_code = 6
            self.increment_loading_bar(15)
            # Shuffle tracks
            random.shuffle(playlist["tracks"])
            # Add tracks
            self.sp.playlist_replace_items(playlist["id"], [])
            self.sp.playlist_add_items(playlist["id"], playlist["tracks"])
            self.add_to_log("Shuffled playlist tracks uploaded to Spotify")
            self.error_code = 7
            self.increment_loading_bar(15)
            # Add or remove track from added tracks
            if action=="add":
                self.added_tracks[track] = track_data
                self.add_to_log("Track added to added tracks dictionary")
            elif action=="remove":
                del self.added_tracks[track]
                self.add_to_log("Track removed from added tracks dictionary")
            self.error_code = 8
            self.increment_loading_bar(15)
            # Save tracks to cache
            self.save_tracks_to_cache()
            self.error_code = 9
            self.increment_loading_bar(15)
            # Change size label
            self.playlist_size_label.config(text=str(len(playlist["tracks"])))
            # Rebuild panel
            self.build_added_tracks_panel()
            self.increment_loading_bar(10)
        except:
            # Log error
            if self.error_code == 0:
                self.add_to_log("Failed to parse track ID from Spotify link", warning=True)
            elif self.error_code == 1:
                self.add_to_log("Failed to retrieve track data from Spotify", warning=True)
            elif self.error_code == 2:
                self.add_to_log("Failed check: \"{}\" is already in your added tracks".format(track_data["title"]), warning=True)
            elif self.error_code == 3:
                self.add_to_log("Failed check: you have already added the maximum number of tracks ({})".format(self.added_tracks_length), warning=True)
            elif self.error_code == 4:
                self.add_to_log("Failed to retrieve playlist data from account", warning=True)
            elif self.error_code == 5:
                self.add_to_log("Failed to add/remove track from playlist dictionary", warning=True)
            elif self.error_code == 6:
                self.add_to_log("Failed to upload shuffled playlist tracks to Spotify", warning=True)
            elif self.error_code == 7:
                self.add_to_log("Failed to add/remove track from added tracks dictionary (Spotify playlist has already been updated)", warning=True)
            elif self.error_code == 8:
                self.add_to_log("Failed to save added tracks to cache (Spotify playlist has already been updated)", warning=True)
            elif self.error_code == 9:
                self.add_to_log("Failed to build added tracks frame", warning=True)
            else:
                self.add_to_log("An unknown error has occurred", warning=True)
            self.increment_loading_bar("end")

    # Function to populate self.playlists
    def populate_playlist_dict(self):
        # Get playlists
        all_playlists = self.sp.current_user_playlists()
        playlist_names = []
        # Add playlist data to dictionary
        for playlist in all_playlists["items"]:
            name = playlist["name"]
            self.playlists[name] = {"id": playlist["id"]}
            playlist_names.append(name)
            playlist_tracks = self.sp.playlist_items(playlist["id"])["items"]
            # Add song ids to playlist dictionary
            self.playlists[name]["tracks"] = []
            for track in playlist_tracks:
                self.playlists[name]["tracks"].append(track["track"]["id"])
        self.add_to_log("Retrieved playlist data from account")
        return(playlist_names)
        
    # Function to add a line to the log, deleting a line if it is too long
    def add_to_log(self, message, warning=False, time=True):
        time_length = 9
        # Remove words which are too long
        message_list = message.split(" ")
        for i in range(len(message_list)):
            if len(message_list[i]) > (self.log_listbox_width - time_length):
                message_list[i] = "<string too long>"
        message = " ".join(message_list)
        if self.log_listbox.size() == self.log_listbox_height:
            self.log_listbox.delete(0)
        now = datetime.now()
        if time:
            current_time = now.strftime("%H:%M:%S")
        else:
            current_time = " "*8
        if len(message) > (self.log_listbox_width - time_length):
            next_line = []
            this_line = message.split(" ")
            length_counter = len(message)
            while length_counter > (self.log_listbox_width - time_length):
                current_word = this_line[-1]
                next_line.append(current_word)
                this_line = this_line[:-1]
                length_counter -= len(current_word)
            this_line = " ".join(this_line)
            next_line = " ".join(next_line[::-1])
            self.log_listbox.insert(END, current_time+" "+this_line)
            if warning:
                self.log_listbox.itemconfig(END, foreground="red")
            self.add_to_log(next_line, warning=warning, time=False)
        else:
            self.log_listbox.insert(END, current_time+" "+message)
            if warning:
                self.log_listbox.itemconfig(END, foreground="red")

# Start GUI
root = Tk()
gui = SpotifyAdder(root)
root.mainloop()