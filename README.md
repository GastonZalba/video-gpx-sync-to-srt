# video-gpx-sync-to-srt
Script to sync video and gpx files recorded at the same time, exporting a srt file for each video as result, including the gps information extracted from the gpx (latitude, longitude and elevation) and matching the in/out extension. The srt format is similar to some dji srt, so these can be parsed using an existing [srt parser](https://github.com/JuanIrache/DJI_SRT_Parser) to read the data. Also, this process allows you to edit the videos and srt files inside an editing software like Adobe Premiere Pro, and then re-export the edited video/srt version.

## Installation
- Create a local enviroment running `python -m venv .venv` (install [virtualenv](https://virtualenv.pypa.io/en/latest/) if you don't have it)
- Load the local enviroment: `.venv\Scripts\activate`
- Install using `pip install -r requirements.txt`

## Instructions
- Load local enviroment `.venv\Scripts\activate`
- Run `python process.py --help` to show all available options and arguments
- By default, place the videos and gpx files inside the input folder `/input`. Or, use custom locations passing the arguments `--foldervid path_to_videos/input` and `--foldergpx path_to_gpx/input`
- `python process.py` to run the script
- Check the console for details and the `/output` folder (the default) for the exported srt files


## If not syncing
- Check (and maybe correct) the timezones using `--tzgpx` and `--tzvideo`. Some cameras store wrong information, adjust this manually 
- Check passing the argument `--dateisout` to use the date of the videos as the end of the file recording and not the start (the default behavior). Some cameras store the start of the recording as the datetime, and others stores the end of it.

## NOTES
- The script looks for the date in the attributes: `Encoded date`, `Recorded date` and `Creation date` (in that order)