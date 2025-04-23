#!/usr/bin/env python3
import pyautogui
import time

# Configuration
NUM_FILES = 2  # Number of files to process
DELAY_BETWEEN_ACTIONS = 0.5  # Adjust this value based on the system's performance
DELAY_BETWEEN_ITERATIONS = 2  # Longer delay between file processing cycles

def press_with_delay(keys, delay=DELAY_BETWEEN_ACTIONS):
    """Press the specified keys with a delay afterwards."""
    pyautogui.hotkey(*keys) if isinstance(keys, list) else pyautogui.press(keys)
    time.sleep(delay)

def main():
    # Give the user some time to focus the right window before starting
    print("Starting automation in 5 seconds. Please focus VS Code window...")
    for i in range(5, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("Beginning automation sequence")
    
    for file_num in range(NUM_FILES):
        print(f"Processing file {file_num + 1} of {NUM_FILES}")
        
        # Step 1: Focus on VS Code file explorer
        press_with_delay(['command', 'shift', 'e'])
        
        # Step 2: Select next file (if not the first iteration)
        if file_num > 0:
            press_with_delay('down')
        
        # Step 3: Open the selected file
        press_with_delay(['command', 'down'])
        
        # Step 4: Return focus to editor
        # press_with_delay(['command', '1'])
        
        # Step 5: Select all text
        press_with_delay(['command', 'a'])
        
        # Step 6: Copy text
        press_with_delay(['command', 'c'])
        
        # Step 7: Open Perplexity
        press_with_delay(['command', 'shift', 'k'])
        
        # Step 8: Paste into Perplexity (with a slightly longer delay)
        time.sleep(1)  # Ensure Perplexity is fully loaded
        press_with_delay(['command', 'v'])
        
        # Step 9: Press Return to start search
        press_with_delay('return')
        
        # Additional delay between iterations
        time.sleep(DELAY_BETWEEN_ITERATIONS)
        
        # Step 10: Return to VS Code
        press_with_delay(['command', 'tab'])
    
    print("Automation completed successfully!")

if __name__ == "__main__":
    main()
