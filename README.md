# video-gpx-sync-to-srt
Script to sync video and gpx files (using the datetime metadata), to export a srt file for each video, including the gps information extracted from the gpx (latitude, longitude and elevation) and matching the in/out extension. The srt format is similar to some dji srt, so these can be parsed using an existing [srt parser](https://github.com/JuanIrache/DJI_SRT_Parser) to read the data. Also, this process allows you to edit later the videos and srt files inside an editing software like Adobe Premiere Pro, and then re-export the edited video/srt version.

## Instructions
- Place the video files inside the input folder `input/videos` and the gpx files in `input/gpx`
- Adjust time zone (gpx and video files separatly)
- Adjust `stored_date_is_out`
- Adjust or disable the interpolation frequency (this add extra coordinates betweeen the existing points on the gpx tracks)
- Run `python process.py`
- Check the console, check the `output` folder for the srt files

## Limitations / Known problems
- Timezones: some cameras store wrong information. Adjust this manually if you have problems syncing the files.
- Encoded/recorded date: some cameras store the start of the recording as the datetime, and others stores the end of it. Change this if yoy have problems syncing.
- This two problems can be easely be solved adjusting these two parameters, but in the other hand, this can prevent bulk processing of mixed video formats. If this is your case, process each format in a separate instance setting properly each case.

## @TODO
- Improve README
- Improve comments
- Add console prompts or/and a separate file for parameters
- Add option to offset the srt or the video in x seconds