# SNR Racetime Automation

This app takes a racetime.gg link and automatically adds the player streams to an obs layout specifically made for hitman SN Races

The OBS Scene Collection this entire app was based on was made by the awesome [ThatObserver](https://www.youtube.com/channel/UCY6kHCCKxcVRcMVf9PBtz6w)

## Installation Guide:
- Go to the [releases](https://github.com/Rekt05/hitman-racetime-automation-snr/releases) and download the latest version that corresponds to your os - for windows download SNR-Windows.zip and for linux download SNR-Linux.zip
- Extract the folder wherever
- This folder contains 2 items namely a folder called "SNR" and an executable called "SNR_Hitman_Racetime_Automation.exe" (or just SNR_Hitman_Racetime_Automation on linux), the SNR folder contains all the things OBS needs and the executable is the app itself
- Go to OBS (probably recommended that you use the latest version)
- Import the scene to OBS with Scene Collection -> Import -> Browse -> SNR.json in the SNR folder, use the same folder when it asks you to locate the missing images.
- Enable the OBS WebSocket server under Tools -> WebSocket Server Settings
- Ensure that your port number is the default (4455)
- Copy your OBS WebSocket Server Password under Tools -> WebSocket Server Settings -> Show Connect Info -> Server Password
- Open the app and insert your now copied OBS password in the box on top
### Misc
- If you want to use the intended font, open the SNR folder and double click on the .ttf font and click install, restart your pc/obs for the font to apply.
- Ensure that your mic and any other applicable audio sources are configured properly by going to said sources and checking that your devices are selected there.
- If you are using this with a co caster you need to make an application audio capture for discord and copy and paste it onto each scene [(see detailed)](#obs-application-audio-capture-setup)

## Usage Guide
- Start the app by clicking the "Start" button after you have entered your OBS password
- Click the "Find Current Race" button to automatically find the currently open/active hitman race or paste in the link to a racetime room yourself.
- For descriptions of the rest of the Race Configuration Buttons see below:
    - Aspect Ratio: Click either 16:9 or 16:10 to select said aspect ratio, these ratios are not applied from that button press, but rather if you use another feature that changes the display of streams (ex. "Reset All Positions", "6P/4P/2P/1P") this aspect ratio will be used
    - Finished Timer: This sets the timer for how long the program should wait before auto removing players from the racetime lobby (0-45s) - this is only applicable if you have the setting below toggled on
    - Auto Remove Finished: When toggled on this will initiate a timer (specified above) to remove players who have either clicked done or dnf on racetime - this feature could be weird for casting so i would probably recommend to leave it off and remove the players yourself
    - Auto Resize Streams: This automates the manual resizing of streams based on the amount of players per screen, ex. if streams 7-12 has 2 players it will automatically resize said 2 streams to take up more screen space
    - Reset All Positions: When clicked it resets all the streams to their 6 stream state
    - Refresh All Streams: When clicked it refreshes all of the streams, this is useful when ex. you want to refresh multiple people who are offline but have since gone live
- For descriptions of the Player Slots Section see below:
    - 6P/4P/2P/1P: Clicking these buttons will resize the streams to fit the amount of players left on each screen, if you do not have "Auto Resize Streams" toggled on you can manually do it here
    - Up/Down: Moves the stream up or down a slot
    - Remove: Removes the stream and adds them to the "Removed Players" section
    - Refresh: Refreshes the individual stream
- Removed players get added to the "Removed Players" section, you can add them back if you so wish by clicking the + button next to their names
### Misc
- Place the spin images in the "Spins" Folder so that they are present on all 3 stream scenes
- If you encounter any unexpected errors mid race just restart the app and it will fix it most of the time
- Remember that the name should appear above the stream in the sources list otherwise the name will not display on top
- The very bottom bar displays updates when you do actions in the app if you needed to see that for some reason

## Update Guide
- Go to the [releases](https://github.com/Rekt05/hitman-racetime-automation-snr/releases) and download the latest version that corresponds to your os - for windows download SNR-Windows.zip and for linux download SNR-Linux.zip
- Extract the folder wherever
- This folder contains 2 items namely a folder called "SNR" and an executable called "SNR_Hitman_Racetime_Automation.exe" (or just SNR_Hitman_Racetime_Automation on linux), the SNR folder contains all the things OBS needs and the executable is the app itself
- Go to your old SNR-OS (SNR -Windows/-Linux) folder and copy and paste the config.ini over to your new SNR-OS
- On the release I will have indicated whether the update is a large or small update compared to the previous release, if it is indicated as a large update follow the OBS Scene Collection install instructions again:
    - Go to OBS (probably recommended that you use the latest version)
    - If you want to remove the old SNR scene collection you can delete it or rename it as such
    - Import the scene to OBS with Scene Collection -> Import -> Browse -> SNR.json in the SNR folder, use the same folder when it asks you to locate the missing images.

### OBS Application Audio capture setup
- you will have to create an application audio capture or the linux equivalent of a application audio capture for discord in any scene -> name it whatever you want (i used "Discord Audio") 
- for "Window" select the one that says discord.exe 
- for "Window Match Priority" select "Match title, otherwise find window of same __executable__"
- copy the new source (ctrl c/right click copy)
- paste the new source in all other scenes as a reference (ctrl v/right click paste (reference) - the only option should be reference and duplicate should be greyed out)
- you can confirm this worked if it now falls under the audio mixer for each scene and if you change the volume on one scene it also changes on the other

## To Do:
- Add SNSASO toggle, will make things easier to only have to maintain 1 app and snsaso app is lacking a lot on functionality
- Add options to configure the height of names in app much like the timer duration
- Store many options in the cfg .ini (ex. above mentioned snsaso toggle, timer duration, toggled options)
- Potentially look into a better way to display 4p screens (SNR - idk if there is one)
- Record video guide for install + usage
- Automate the Stream (Zoom) scene if anyone cares about it
- Add a way to swap players around directly so that only 1 position has to change to make the position of a given player more uniform across a race
- Look at a way to not have to refresh streams when moved (this is probably completely unfeasible without having all 18 streams on 1 scene though)
- Look at resolutions, does a 480p player look any worse for 6p/4p?
  
For and issues or suggestions dm me on discord @Rekt05
