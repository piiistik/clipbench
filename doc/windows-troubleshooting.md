# Windows Troubleshooting

## `clipbench` Command Not Found

If the `clipbench` command is not found on Windows, use one of these options:

1. **Add Python Scripts to PATH** (recommended):
   - Find your Python installation directory (example: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311`)
   - Add the `Scripts` subdirectory to your system PATH:
     - Open System Properties -> Environment Variables
     - Edit the `PATH` variable and add: `C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\Scripts`
     - Restart your terminal

2. **Call CLIPBench by full path:**
   ```bash
   C:\Users\<YourUsername>\AppData\Local\Programs\Python\Python311\Scripts\clipbench.exe
   ```
