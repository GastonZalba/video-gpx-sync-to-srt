# video-gpx-sync-to-srt
Script to sync video and gpx files (using the date and time metadata), to export a srt file for each video, including the gps information extracted from the gpx (latitude, longitude and elevation) and matching the in/out extension. The srt format is similar to some dji srt, so these can be parsed using an existing [srt parser](https://github.com/JuanIrache/DJI_SRT_Parser) to read the data. Also, this process allows you to edit the videos and srt files inside a editing software like Adobe Premiere Pro, and then re-export the edited video/srt version.

## Instructions
- Place the video files inside the input folder `input/videos` and the gpx files in `input/gpx`
- Adjust time zone (gpx and video files separatly)
- Adjust or disable the interpolation frequency (this add extra points betweeen the original on the gpx tracks)
- Run `python process.py`
- Check the console, check the `output` folder fo the srt files

# @TODO
- Improve README
- Improve comments
- Add console prompts or/and a separate file for parameters