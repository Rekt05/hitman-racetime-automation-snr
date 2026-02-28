## This readme is a copy of the SN race app and was only quickly scanned through and edited so not all information may be accurate but it should mostly be ok

This app takes a racetime.gg link and automatically adds the player streams to an obs layout specifically made for hitman SN Races

The OBS Scene Collection this entire app was based on was made by the awesome [ThatObserver](https://www.youtube.com/channel/UCY6kHCCKxcVRcMVf9PBtz6w)

[Linux install video](https://youtu.be/cg9OBavoEqw) - VERY OUTDATED, refer to basically all the text below for a more comprehensive overview, ESPECIALLY FOR SNR

Windows video coming eventually when linux is confirmed to be working

Currently this comes with 2 JSON file presets:
- SNR.json

You can go through the import process with any combination of presets of your choosing and the app will work for the scene collection you are currently using.
If you have a preset you would like to add refer to the very bottom of the readme

Usage Instructions/Notes:
- Import the scene to obs with Scene Collection -> Import -> Browse -> SNR.json in the SNR folder, use the same folder when it asks you to locate the missing images.
- For the OBS password go to Tools -> WebSocket Server Settings -> Show Connect Info -> Server Password. Make sure that Enable WebSocket server under Tools -> WebSocket Server Settings is also enabled. 
- Paste in the racetime link or click the "Find Current Race" button.
- Use the arrow buttons to move the players up/down the list and use the trash can button to remove them from the list, you can add them back using the + button in the Removed Players section.
- Ensure that your mic and any other applicable audio sources are configured properly.
- Double click in the .ttf font and click install, restart your pc/obs for the font to apply.
- You can freely move and resize things like "Steamer Name X" and the stream itself and the program will still work as intended, to move the names click on the source in the appropriate folder, to move/resize the stream just click on it in the preview.
- If you want to move the name to be on top of the video player, remember to drag it above the stream source in the folder.
- The reset stream positions button resets the streams position and size to the 2x3 layout

Ideas:
- Add functionality to auto resize streams accoring to the amount of people per page

if you have any ideas for features or if you have a preset you would like to add open a *pr or dm me on discord @Rekt05

*for Preset PR's you can make sure to find and replace you computer name from the file path to potentially avoid leaking personal information.