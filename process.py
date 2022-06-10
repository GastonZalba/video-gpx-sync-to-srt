import os
import glob
import pytz
import gpxpy
import traceback
from pymediainfo import MediaInfo
from datetime import datetime, timedelta

input_folder = 'input'
output_folder = 'output'

time_zone_gpx = 'America/Argentina/Buenos_Aires'
time_zone_video = None

# to interpolate coordinates betweeen existing points in the gpx
# `None` to disable
interpolation_freq_in_seconds = 1

# date could be the beggining or the end of the file
stored_date_is_out = True

output_file = ''

def init():

    global output_file

    try:

        print('--> PROCESS STARTED <--')

        print('\t')

        parsed_videos = parse_videos()
        parsed_gpx = parse_gpx()

        synced = 0

        for pvideo in parsed_videos:
            collect_srt = []
            for pgpx in parsed_gpx:

                if (pgpx['time'] < pvideo['time_start']):
                    continue                
                
                if (pgpx['time'] <= pvideo['time_end']):
                    collect_srt.append(pgpx)

            points_found = len(collect_srt)

            print('\t')

            print(f'Video name: {pvideo["file_name"]}{pvideo["extension"]}')
            print(f'Duration (sec): {pvideo["duration"]}')
            print(f'Start time: {pvideo["time_start"]}')
            print(f'End time: {pvideo["time_end"]}')

            if (points_found > 0):
                print(f'-> GPX matched file {pvideo["file_name"]} witch {points_found} points')
                write_srt(collect_srt, pvideo["file_name"])
                synced += 1
            else:
                print(f'-> WARNING: GPX tracks not synced with the video. Check the time zones.')
        
        print('\t')
        print('--> PROCESS WAS COMPLETED <--')
        print('\t')
        print('------------------------------')
        print(f'-> {synced} videos synced')
        print(f'-> {(len(parsed_videos)-synced)} videos not synced')
        print('------------------------------')
        
    except Exception as error:
        print(error)
        print(traceback.format_exc())


def parse_videos():

    def date_string_to_datetime(dt, format):
        try:
            return datetime.strptime(dt, format)
        except:
            return False
        
    datetime_formats = [
        '%Z %Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S.%f'
    ]

    parsed_videos = []

    def get_videos():
        types = ('*.mp4', '*.mts', '*.mov', '.*.h264', '*.avi', '*.m2v', '*.mxf')
        files_grabbed = []
        for type in types:
            files_grabbed.extend(glob.glob(input_folder + '/videos/' + type))
        return files_grabbed

    videos = get_videos()

    print(f'{len(videos)} videos have been found.')    

    for video in videos:
        media_info = MediaInfo.parse(video)
        duration_in_s = int(float(media_info.tracks[0].duration)) / 1000

        video_track = media_info.tracks[0]

        # canon, phones, insta and others saves the date on this field
        # datetime of the end of the file
        stored_date = video_track.encoded_date
        
        if not stored_date:
            # sony and panasonic cameras
            stored_date = video_track.recorded_date

        for df in datetime_formats:
            conversion = date_string_to_datetime(stored_date, df)
            if conversion:
                stored_date = conversion
                break

        if not stored_date:
            print(f'{video} has no date information and cannot be used')
            continue

        if isinstance(stored_date, str):
            print(f'{video} has unrecognized date format {stored_date} and cannot be used')
            continue
            
        if time_zone_video:
            stored_date = stored_date.astimezone(
                pytz.timezone(time_zone_video))
        else:
            utc = pytz.UTC
            stored_date = stored_date.replace(tzinfo=utc)

        if stored_date_is_out == True:
            time_start = stored_date - timedelta(0, round(duration_in_s))         
            time_end = stored_date 
        else:
            time_start = stored_date
            time_end = stored_date + timedelta(0, round(duration_in_s))        

        parsed_videos.append({
            'file_name': os.path.splitext(os.path.basename(video))[0],
            'extension': os.path.splitext(os.path.basename(video))[1],
            'file_path': video,
            'duration': duration_in_s,
            'time_start': time_start,
            'time_end': time_end
        })

    return parsed_videos


def parse_gpx():

    parsed_gpx_points = []

    def get_gpx():
        return glob.glob(input_folder + '/gpx/' + '*.gpx')

    def store_point_track(point, prev_point, start_time, time_diff_seconds):
        parsed_gpx_points.append({
            "time": point.time,
            "start_time": prev_point.time - start_time,
            "end_time": point.time - start_time,
            "diff_time": time_diff_seconds*1000,
            "latitude": point.latitude,
            "longitude": point.longitude,
            "elevation": point.elevation
        })

    gpxs = get_gpx()

    print(f'{len(gpxs)} gpx have been found.')    

    for gpx_path in gpxs:

        input_file = open(gpx_path, 'r')
        gpx = gpxpy.parse(input_file)
        input_file.close()

        if len(gpx.tracks) == 0:
            raise Exception('File has no tracks')

        for track in gpx.tracks:

            for segment in track.segments:
                prev_point = None
                start_time = None

                for point in segment.points:

                    # maybe correct the gpx timezone
                    if time_zone_gpx:
                        point.time = point.time.astimezone(
                            pytz.timezone(time_zone_gpx))

                    if not start_time:
                        start_time = point.time

                    if prev_point:

                        time_diff = point.time - prev_point.time
                        time_diff_seconds = time_diff.total_seconds()

                        if interpolation_freq_in_seconds != None:
                            intermediate_points = []
                            if round(time_diff_seconds) > interpolation_freq_in_seconds:
                                extra_points = round(
                                    time_diff_seconds / interpolation_freq_in_seconds) - 1
                                intermediate_points = intermediates(
                                    prev_point, point, extra_points)

                                if len(intermediate_points):
                                    for ipoint in intermediate_points:
                                        time_diff = ipoint.time - prev_point.time
                                        time_diff_seconds = time_diff.total_seconds()
                                        store_point_track(
                                            ipoint, prev_point, start_time, time_diff_seconds)
                                        prev_point = ipoint

                        store_point_track(
                            point, prev_point, start_time, time_diff_seconds)

                    prev_point = point

    return parsed_gpx_points


def write_srt(points, file_name):

    line_counter = 1

    output_filename = f'{file_name}.srt'

    output_file = open( f'{output_folder}/{output_filename}', 'w')

    base_time = points[0]['start_time']
    
    for point in points:
        output_file.write('{0}\n'.format(line_counter))

        # Use mavic 2 srt format
        output_file.write(
            '0{0},000 --> 0{1},000\n'.format((point['start_time'] - base_time), (point['end_time'] - base_time)))
        output_file.write(
            '<font size="36">FrameCnt : n/a, DiffTime : {:.0f}ms\n'.format(point['diff_time']))
        output_file.write(f'{point["time"]}\n')
        output_file.write(
            f'[latitude : {point["latitude"]}] [longitude : {point["longitude"]}] [altitude: {point["elevation"]}] </font>\n')
        output_file.write('\n')

        line_counter += 1

    output_file.close()


def intermediates(p1, p2, nb_points=8):
    x_spacing = (p2.latitude - p1.latitude) / (nb_points + 1)
    y_spacing = (p2.longitude - p1.longitude) / (nb_points + 1)
    z_spacing = (p2.elevation - p1.elevation) / (nb_points + 1)
    t_spacing = (p2.time - p1.time) / (nb_points + 1)

    return [
        gpxpy.gpx.GPXTrackPoint(
            p1.latitude + i * x_spacing,
            p1.longitude + i * y_spacing,
            elevation=round(p1.elevation + i * z_spacing, 2),
            time=p1.time + i * t_spacing
        )
        for i in range(1, nb_points+1)
    ]


init()
