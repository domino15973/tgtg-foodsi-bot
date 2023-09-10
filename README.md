# DISCORD FOOD NOTIFIER BOT

This Python application helps me track of available food deals on TooGoodToGo and Foodsi and notifies me on Discord channel when new deals are found.

## Installation and Setup Instructions

This guide provides step-by-step instructions on how to install and run the application.

## Prerequisites

Before proceeding with the installation, ensure that you have the following:

* Python installed on your system
* 'pip' package manager installed

## Installation

1. Clone the repository from GitHub:
```console
git clone https://github.com/domino15973/tgtg-foodsi-bot
```
2. Navigate to the project directory:
```console
# Remember to replace <project_directory> with the path to your project directory.
cd <project_directory>
```
3. Create and activate a new virtual environment:
```console
# Create a new virtual environment
python3 -m venv venv

# Activate the virtual environment for Windows
venv\Scripts\activate

# Activate the virtual environment for macOS/Linux
source venv/bin/activate
```
4. Install the projects dependencies using 'pip' and the provided 'requirements.txt' file:
```console
pip install -r requirements.txt
```
5. Create config.json file:
```console
cp config.example.json config.json
```
6. Edit config.json file:
* Insert your location info [latlong.net](https://www.latlong.net/)
* Insert your [Discord bot token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) and [channel id](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)

## Running the application
Start the app:
```console
python3 main.py
```
When you first run the application, you will be asked to provide login details for TGTG and Foodsi, which will be saved in the config.json file and everything will work fine the next time you run it.

That's it! You have successfully installed and set up the application. Enjoy using the bot!

## License
This project is licensed under the terms of the MIT license.