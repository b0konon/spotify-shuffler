import customtkinter as ctk
from spotify_client import SpotifyClient
import threading

def run():
    spotify_client = SpotifyClient()

    root = ctk.CTk()
    root.title("Spotify Playlist Search")
    root.geometry("400x300")

    def on_search():
        search_button.configure(state="disabled")
        thread = threading.Thread(target=lambda: search_thread(search_entry.get()))
        thread.daemon = True
        thread.start()

    def search_thread(query):
        spotify_client.search_for_playlists(query)
        
        # Schedule the UI update on the main thread
        root.after(0, update_playlist_display)

    def update_playlist_display():
        # Clear existing playlists from the frame
        for widget in playlist_frame.winfo_children():
            widget.destroy()
            
        # Display new filtered playlists
        for playlist in spotify_client.filtered_playlists:
            try:
                playlist_label = ctk.CTkLabel(playlist_frame, text=playlist['name'])
                playlist_label.pack(pady=2)
            except Exception as e:
                print(f"Error displaying playlist: {e}")

        # Re-enable search button
        search_button.configure(state="normal")

    def shuffle_thread(query):
        spotify_client.shuffle_playlist(query)
        # Re-enable button on the main thread
        root.after(0, lambda: search_button.configure(state="normal"))

    # Create a frame to hold the entry and button
    input_frame = ctk.CTkFrame(root)
    input_frame.pack(pady=20)

    search_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter playlist name...")
    search_entry.pack(side="left", padx=5)

    search_button = ctk.CTkButton(input_frame, text="Search", command=on_search)
    search_button.pack(side="left", padx=5)

    # Create a scrollable frame to hold the playlists
    playlist_frame = ctk.CTkScrollableFrame(root)
    playlist_frame.pack(pady=10, fill="both", expand=True)

    # Display initial playlists, each entry should be clickable and run a function called on_playlist_click with the playlist name as an argument
    for playlist in spotify_client.filtered_playlists:
        try:
            playlist_label = ctk.CTkLabel(playlist_frame, text=playlist['name'])
            playlist_label.pack(pady=2)
            playlist_label.bind("<Button-1>", lambda event, playlist_name=playlist['name']: shuffle_thread(playlist_name))
        except Exception as e:
            print(f"Error displaying playlist: {e}")

    root.mainloop()

if __name__ == "__main__":
    run()
