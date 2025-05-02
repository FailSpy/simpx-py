# simpx-py

![Logo of SimpX with a Pythonic colored version of the SimpleX symbol, further reading "a Python module for easy development of SimpleX bots"](https://repository-images.githubusercontent.com/958886714/2cf76236-f6a6-4ea9-8a0f-3256d4349eb4)

An _unstable_ (for now) Python framework for creating bots on the [SimpleX chat platform](https://simplex.chat/).

This library was initially created as a somewhat direct port of TypeScript structures, but aims to provide a decorator-based interface familiar to users of libraries like `discord.py`.

**Note:** While functional, being a relatively direct conversion from the TypeScript structures means this does not always follow Python best practices and would benefit from further refinement

## Join the SimpleX group!

[SimpX group](https://simplex.chat/contact#/?v=2-7&smp=smp%3A%2F%2FjA736UwbVG_LKSQyi9tr8LZOxgqBIQTJgbi7jgAGJhM%3D%40thebunny.zone%2Fr0S1zLSurZViaMtrK_BXeo_Vf7UIP1ce%23%2F%3Fv%3D1-3%26dh%3DMCowBQYDK2VuAyEA53LohGQGd_7rmltrzZtFagwM2s6CQk0XDeqQLMKtmhk%253D%26srv%3Dbunnysmppnjrd7f4saxjcewlnf3jxyvyjjmtsvdz7cnpxpt5y4mqnoyd.onion&data=%7B%22groupLinkId%22%3A%22rCjlKF_XB4fZFujtiOChlg%3D%3D%22%7D)

Come chat about bot development, the project, or even SimpleX in general. 


## Features

*   Decorator-based handlers for commands (`@bot.command`) and events (`@bot.event`).
*   Profile management (`BotProfile`, `ProfileManager`) to handle bot identity.
*   Built-in, customizable help command (`!help`).
*   Optional automatic welcome message for new contacts.
*   Extension classes (`SimpleXBotExtensions`) providing wrapper objects (ContactWrapper, GroupWrapper, ChatWrapper etc.) for more Pythonic interaction with the SimpleX API.
*   Basic task scheduling.
*   Support for sending and updating live messages.
*   Automatic message reading.

## Installation

```bash
git clone https://github.com/FailSpy/simpx-py
cd simpx-py
# Optional: Create and activate a virtual environment
# python -m venv venv
# source venv/bin/activate  # or venv\Scripts\activate on Windows

pip install .
```

### Getting simplex-chat client

You'll need the Terminal CLI to work with it. **Presently, there is no interfacing that allows the Python code to run the daemon itself.** You will need to implement this yourself for now.

You can get the simplex-chat CLI release here: https://github.com/simplex-chat/simplex-chat/releases/latest

You will want a non-"desktop" tagged version (desktop is a GUI on top)

To run the daemon for Python, use the port operator to tell it to operate in WebSockets mode:
```bash
./simplex-chat-ubuntu-22_04-x86-64 -p 5225
```

This will open a websocket on port 5225 which Python can access. If you want to use a different port, see `BotProfile` to configure the Python side of things.

## TODOS:
- [ ] Improve profiles (allowing for multiple profiles at once)
- [ ] Improve typing and wrappers
  - [ ] Port all SimpleX haskell message types
  - [ ] File handling
- [ ] Directly integrate w/ CLI binary?
- [ ] Privacy configuration
- [ ] Exception handling
- [ ] Logging
- [ ] Always: documentation

## Getting Started

See also example\_bot.py

Here's a commented example of how to create and run a bot:

```python
import asyncio
from simpx import BotProfile, SimpleXBot

# 1. Create a bot profile (can be saved/loaded)
# If a profile with this name exists, it will be loaded.
# Otherwise, a new one is created on the server.
profile = BotProfile(
    display_name="MySimpleBot",
    full_name="My Simple Bot",
    description="A bot built with simpx-py",
    # Optional: Welcome message for new contacts
    welcome_message="Hi {name}! Welcome to my bot.",
    # Optional: Set command prefix (default is "!")
    command_prefix="!"
)

# 2. Create the bot instance
# You can pass the profile directly or let the bot handle loading/creation
bot = SimpleXBot(profile)

# 3. Define commands using decorators
@bot.command(name="hello", help="Says hello back to you")
async def hello_command(chat_info):
    """A simple command that sends a greeting."""
    # Use bot.send_message to reply in the same chat
    await bot.send_message(chat_info, "Hello there!")

@bot.command(name="echo", help="Repeats your message")
async def echo_command(chat_info, args: str):
    """Echoes the arguments provided"""
    if args:
        await bot.send_message(chat_info, f"You said: {args}")
    else:
        await bot.send_message(chat_info, "You didn't say anything to echo!")

# 4. Define event handlers (optional)
@bot.event("contactConnected")
async def handle_connection(response):
  """Handles new contact connections (alternative to welcome_message)."""
  contact = response.get("contact", {})
  display_name = contact.get("profile", {}).get("displayName", "Unknown")
  print(f"{display_name} connected!")

# 5. Start the bot
if __name__ == "__main__":
    print("Starting bot...")
    # Ensure your SimpleX Chat Console (simplex-chat) backend is running
    # The bot will connect via WebSocket (default: ws://127.0.0.1:5225)
    # You can specify a different server_url in SimpleXBot constructor if needed
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("Bot stopped.")
    finally:
        # Optional cleanup
        asyncio.run(bot.close())

```

## Running the Example Bot in `example-bot.py`

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/FailSpy/simpx-py
    cd simpx-py
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    NOTE: If you want to use  `!msg` with an LLM provider:
        - Install `openai` as well
        - Configure API Key: Open `example-bot.py` and replace `<API_KEY_HERE>` with your actual OpenRouter API key (or adapt for a different LLM provider).
3.  **Ensure SimpleX Chat Console is running:** The bot needs to connect to a running `simplex-chat` instance via its WebSocket interface (launch with arg i.e. `-p 5225`).
5.  **Run the bot:**
    ```bash
    python example-bot.py
    ```
6.  **Connect to your bot:** Use the bot's address (printed to the console as plaintext and QR code on run) in your SimpleX Chat client to connect and try the commands (`!help`, `!info`, `!echo`, `!square`, `!add`, `!msg`).

## Contributing

Feel free to open issues or pull requests. Given the origin of the library as a direct port, contributions focused on making the codebase more Pythonic, improving error handling, adding tests, or enhancing documentation are particularly welcome.
