import tkinter as tk

def main():
    root = tk.Tk()
    root.title("HelloApp")
    label = tk.Label(root, text="Hello from GUI 👋", padx=20, pady=20)
    label.pack()
    root.mainloop()

if __name__ == "__main__":
    main()
