 ## Installation Instructions

1. Install `git` and [Python](https://www.python.org/) (version 3.6 or newer compatible) if you don't already have them.
2. Clone this repository. (`git clone https://github.com/Kyuunex/Suwako.git`)
3. Install requirements. (`python3 -m pip install -r requirements.txt`)
4. For your tokens/api keys, create a folder named `data` in the repository folder. Inside it create 4 files:
    + Create `token.txt` and put your bot token in. You can get it by registering an application
    on [Discord's developer site](https://discord.com/developers/applications/) and creating a bot.
    + Create `osu_api_key.txt` and put osu api key in. You can get it [here](https://osu.ppy.sh/p/api/)
5. If you are restoring a backup, just put the database file in the `data` folder.
6. To start the bot, run `suwako.py`. I recommend installing the bot as a `systemd` service though.
7. Figure out the rest yourself.

### If you are SSHing into a GNU/Linux server, you can just type these to achieve the same thing

```sh
cd $HOME
git clone https://github.com/Kyuunex/Suwako.git
cd $HOME/Suwako
python3 -m pip install -r requirements.txt
mkdir -p $HOME/Suwako/data
# wget -O $HOME/Suwako/data/maindb.sqlite3 REPLACE_THIS_WITH_DIRECT_FILE_LINK # only do if you are restoring a backup
echo "REPLACE_THIS_WITH_BOT_TOKEN" | tee $HOME/Suwako/data/token.txt
echo "REPLACE_THIS_WITH_OSU_API_KEY" | tee $HOME/Suwako/data/osu_api_key.txt
echo "REPLACE_THIS_WITH_CLIENT_ID" | tee $HOME/Suwako/data/client_id.txt
echo "REPLACE_THIS_WITH_CLIENT_SECRET" | tee $HOME/Suwako/data/client_secret.txt
```


## Installing the bot as a systemd service

Create the following file: `/lib/systemd/system/suwako.service`  
Inside it, put the following:
```ini
[Unit]
Description=Suwako
After=network.target
StartLimitIntervalSec=0

[Service]
Restart=always
RestartSec=5
User=pi
Type=simple
WorkingDirectory=/home/pi/Suwako/
ExecStart=/usr/bin/python3 /home/pi/Suwako/suwako.py

[Install]
WantedBy=multi-user.target
```

The above assumes `pi` as a username of the user the bot will be run under. Change it if it's different. 
Make sure to change the paths too. The default assumes you just clone the thing in the user's home folder.  
Make sure the requirements are installed under the user the bot will be run under.  
After you are done, type `sudo systemctl enable --now suwako.service` to enable and start the service.
