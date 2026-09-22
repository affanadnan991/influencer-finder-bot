import os
import sys
from playwright.sync_api import sync_playwright

# Add current directory to path just in case
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import INSTAGRAM_SESSION_FILE

def main():
    print("====================================================")
    print("         INSTAGRAM BOT LOGIN HELPER")
    print("====================================================")
    print("This helper will open a browser window so you can log in")
    print("to the Instagram account you want to link with the bot.")
    print("\nStarting browser...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            page.goto("https://www.instagram.com/accounts/login/")
            
            print("\n👉 ACTION REQUIRED:")
            print("1. Log in to your Instagram account in the opened browser window.")
            print("2. If asked, complete any 2-Factor Authentication (2FA) or security checks.")
            print("3. Once you are successfully logged in and see your home feed,")
            print("   press ENTER in this terminal to save the session and close the browser.")
            
            # Wait for user input in terminal
            input("\nPress ENTER here once you have logged in and want to save the session...")
            
            # Save session
            try:
                context.storage_state(path=INSTAGRAM_SESSION_FILE)
                print(f"\n✅ SUCCESS: Session cookies saved to: {INSTAGRAM_SESSION_FILE}")
                print("Now the bot will run using this new logged-in account!")
            except Exception as e:
                print(f"\n❌ Error saving session: {e}")
            
            browser.close()
    except Exception as e:
        print(f"\n❌ Failed to run login helper: {e}")
        print("Please make sure you have activated the virtual environment and installed Playwright:")
        print("   source venv/bin/activate  (or venv\\Scripts\\activate on Windows)")
        print("   playwright install chromium")

if __name__ == "__main__":
    main()
