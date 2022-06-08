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

# to interpolate coordinates values betweeen points
# `None` to disable
interpolation_freq_in_seconds = 1

output_file = ''

def init():

    global output_file

    try:

        parsed_videos = parse_videos()
        parsed_gpx = parse_gpx()

        for pvideo in parsed_videos:
            collect_srt = []
            for pgpx in parsed_gpx:

                if (pgpx['time'] < pvideo['time_start']):
                    continue                
                
                if (pgpx['time'] <= pvideo['time_end']):
                    collect_srt.append(pgpx)

            points_found = len(collect_srt)

            print(f'Video name: {pvideo["file_name"]}')
            print(f'Duration: {pvideo["duration"]}')
            print(f'Start time: {pvideo["time_start"]}')
            print(f'End time: {pvideo["time_end"]}')

            if (points_found > 0):
                print(f'GPX matched file {pvideo["file_name"]} witch {points_found} points')
                write_srt(collect_srt, pvideo["file_name"])
            else:
                print(f'GPX tracks not synced with the video. Check timezone')

        print('Process was completed')

    except Exception as error:
        print(error)
        print(traceback.format_exc())


def parse_videos():

    parsed_videos = []

    def get_videos():
        types = ('*.mp4', '*.mts', '*.mov', '.*.h264', '*.avi', '*.m2v')
        files_grabbed = []
        for type in types:
            files_grabbed.extend(glob.glob(input_folder + '\movies\\' + type))
        return files_grabbed

    videos = get_videos()

    for video in videos:
        media_info = MediaInfo.parse(video)
        duration_in_s = media_info.tracks[0].duration / 1000
        encoded_date = media_info.tracks[0].encoded_date
        
        encoded_date = datetime.strptime(encoded_date, '%Z %Y-%m-%d %H:%M:%S')

        if time_zone_video:
            encoded_date = encoded_date.astimezone(
                pytz.timezone(time_zone_video))
        else:
            utc=pytz.UTC
            encoded_date = encoded_date.replace(tzinfo=utc)
        
        parsed_videos.append({
            'file_name': os.path.splitext(os.path.basename(video))[0],
            'file_path': video,
            'duration': duration_in_s,
            'time_start': encoded_date - timedelta(0, round(duration_in_s)),
            'time_end': encoded_date
        })

    return parsed_videos


def parse_gpx():

    parsed_gpx_points = []

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

    for subdir, dirs, files in os.walk(input_folder + '\gpx'):
        for file in files:

            filepath = subdir + os.sep + file

            if file.endswith(".gpx"):

                input_file = open(filepath, 'r')
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
