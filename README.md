# video-gpx-sync-to-srt
Script to sync video and gpx files recorded at the same time, exporting a srt file for each video as result, including the gps information extracted from the gpx (latitude, longitude and elevation) and matching the in/out extension. The srt format is similar to some dji srt, so these can be parsed using an existing [srt parser](https://github.com/JuanIrache/DJI_SRT_Parser) to read the data. Also, this process allows you to edit the videos and srt files inside an editing software like Adobe Premiere Pro, and then re-export the edited video/srt version.

## Installation
- Install using `pip install -r requirements.txt` in a local enviroment

## Instructions
- Run `python process.py --help` to show all options and available arguments
- By default, place the videos and gpx files inside the input folder `/input` (or use custom locations passing the arguments `--foldervid path_to_videos/input` and `--foldergpx path_to_gpx/input`)
- `python process.py` to run the script
- Check the console for details and the `/output` folder (by default) for the exported srt files
- If the files are not syncing, check (and maybe correct) the timezones using `--tzgpx` and `--tzvideo`. Also check passing the argument `--stored_date_is_end` to use the metadata date of the videos as the end of the file and not the start (the default behavior).

## Limitations / Walkarounds
- Timezones: some cameras store wrong information. Adjust this manually if you have problems syncing the files.
- Encoded/recorded date: some cameras store the start of the recording as the datetime, and others stores the end of it. Change this if you have problems syncing.
- This two problems can be easely be solved adjusting these two parameters, but in the other hand, this can prevent bulk processing of mixed video formats. If this is your case, process each format in a separate instance setting properly each case.

## @TODO
- Add option to offset the srt or the video in -+ seconds