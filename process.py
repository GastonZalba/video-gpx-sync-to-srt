import os
import glob
import pytz
import gpxpy
import traceback
from colorama import init, Fore, Style
from tzlocal import get_localzone
from pymediainfo import MediaInfo
from datetime import datetime, timedelta

# fix colorama colors in windows console
init(convert=True)

# main
def main():
    import argparse

    # defaults
    time_zone_gpx = str(get_localzone()) # use local time zones
    time_zone_video = str(get_localzone()) # use local time zones
    input_folder_video = 'input'
    input_folder_gpx = 'input'
    output_folder = 'output'
    video_extensions = ['mp4', 'mts', 'mov', 'h264', 'h265', 'avi', 'm2v', 'm4v', 'mxf', 'mkv', 'mpeg', 'mpg', 'insv', 'f4v']
    interpolation_freq_in_seconds = 0 # to temporal interpolate coordinates betweeen existing points in the gpx
    offset_in_seconds = 0
    # date could be the beginning or the end of the file
    stored_date_is_end = False
    stored_discard_elevation = False

    parser = argparse.ArgumentParser(description='Script to sync video and gpx files recorded at the same time, and export a srt file for each video.')
    parser.add_argument('--foldervid', type=str, metavar='Input video folder', default=input_folder_video, help='Folder with the videos files (default: %(default)s)')
    parser.add_argument('--foldergpx', type=str, metavar='Input gpx folder', default=input_folder_gpx, help='Folder with gpx files (default: %(default)s)')
    parser.add_argument('--output', type=str, metavar='Output folder', default=output_folder, help='Folder to export the srt files (default: %(default)s)')
    parser.add_argument('--tzvideo', default=time_zone_gpx, metavar='Video Time Zone', help='Pass a timezone string or float hour values (Ex. -3.5). 0 to disable (default is current localzone: %(default)s)')
    parser.add_argument('--tzgpx', default=time_zone_video, metavar='GPX Time Zone', help='Pass a timezone string or float hour values (Ex. -3.5). 0 to disable (default is current localzone: %(default)s)')
    parser.add_argument('--interpolation', type=int, default=interpolation_freq_in_seconds, help='Interpolation frequency (in seconds) to create points between the existing gpx coordinates. 0 to disable (default: %(default)s)')
    parser.add_argument('--dateisout', action='store_true', help='Stored metadata date match the end of the recording (default: %(default)s)')
    parser.add_argument('--offset', type=float, metavar='Offset video', default=offset_in_seconds, help='Seconds to offset the video date (default: %(default)s)')
    parser.add_argument('--discardelevation', action='store_true', help='Discard elevation values (default: %(default)s)')
    parser.add_argument('--videoext', action="append", default=video_extensions, metavar='Video extension', help='Add custom video extensions. (default is: %(default)s)')

    args = parser.parse_args()

    try:

        print('--> PROCESS STARTED <--')

        print('\t')

        interpolation_freq_in_seconds = args.interpolation
        time_zone_video = string_to_num(args.tzvideo)
        time_zone_gpx = string_to_num(args.tzgpx)
        stored_date_is_end = args.dateisout
        input_folder_video = args.foldervid
        input_folder_gpx = args.foldergpx
        offset_in_seconds = args.offset
        stored_discard_elevation = args.discardelevation
        video_extensions = args.videoext

        output_folder = args.output

        # check if output folder exists
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        parsed_videos = parse_videos(input_folder_video, video_extensions, time_zone_video, offset_in_seconds, stored_date_is_end)
        parsed_gpx = parse_gpx(input_folder_gpx, time_zone_gpx, interpolation_freq_in_seconds, stored_discard_elevation)

        # if not videos or not gps are found, abort the process
        if not parsed_videos or not parsed_gpx:
            print('\t')
            print(f'{Fore.RED}--> PROCESS WAS ABORTED WITH ERRORS <--{Style.RESET_ALL}')
            return

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
                print(f'{Fore.GREEN}-> Synced {points_found} GPX points with this video{Style.RESET_ALL}')
                write_srt(collect_srt, pvideo["file_name"], output_folder)
                synced += 1
            else:
                print(f'{Fore.YELLOW}-> WARNING: GPX tracks not synced with the video. Correct the offset or check the time zones to adjust overlapping.{Style.RESET_ALL}')
                print('\t')

        not_synced = len(parsed_videos)-synced

        print('\t')
        print('--> PROCESS WAS COMPLETED <--')
        print('------------------------------')
        print(f'-> Time zone GPX: {time_zone_gpx}')
        print(f'-> Time zone Video: {time_zone_video}')
        print(f'-> Interpolation frequency (sec): {interpolation_freq_in_seconds}')
        print(f'-> Offset time (sec): {offset_in_seconds}')
        print(f'-> Stored date match the end of the recording: {stored_date_is_end}')

        if synced:
            print(f'{Fore.GREEN}-> {synced} videos synced{Style.RESET_ALL}')

        if not_synced:
            print(f'{Fore.YELLOW}-> {(not_synced)} videos not synced{Style.RESET_ALL}')

        print('------------------------------')
        
    except Exception as error:
        print(f'{Fore.RED}{error}{Style.RESET_ALL}')
        print(traceback.format_exc())


def parse_videos(input_folder_video, video_extensions, time_zone_video, offset_in_seconds, stored_date_is_end):

    def date_string_to_datetime(dt, format):
        try:
            return datetime.strptime(dt, format)
        except:
            return False
    
    datetime_formats = [
        '%Z %Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S%z',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%S %Z'
    ]

    parsed_videos = []

    def get_videos():
        
        types = [('*.'+ v) for v in video_extensions]

        files_grabbed = []
        for type in types:
            files_grabbed.extend(glob.glob(f'{input_folder_video}/{type}'))
        return files_grabbed

    videos = get_videos()

    if len(videos):
        print(f'{Fore.GREEN}{len(videos)} videos have been found.{Style.RESET_ALL}')    
    else:
        print(f'{Fore.RED}No videos have been found in folder "{input_folder_video}"{Style.RESET_ALL}')        

    for video in videos:

        # To solve some errors on sequentials mts        
        mediainfo_opts = {'File_TestContinuousFileNames' : '0'}

        media_info = MediaInfo.parse(video, mediainfo_options=mediainfo_opts)
        
        video_track = media_info.tracks[0]

        duration_in_s = int(float(video_track.duration)) / 1000

        # canon, phones, insta and others saves the date on this field
        # datetime of the end of the file
        stored_date = video_track.encoded_date
        
        if not stored_date:
            # sony and panasonic cameras
            stored_date = video_track.recorded_date
        
        if not stored_date:
            # last attempt to catch a date, use the creation date...
            stored_date = video_track.file_creation_date__local
            
        for df in datetime_formats:
            conversion = date_string_to_datetime(stored_date, df)
            if conversion:
                stored_date = conversion
                break

        if not stored_date:
            print(f'{Fore.RED}{video} has no date information and cannot be used{Style.RESET_ALL}')
            continue

        if isinstance(stored_date, str):
            print(f'{Fore.RED}{video} has an unrecognized date format {stored_date} and cannot be used{Style.RESET_ALL}')
            continue
        
        if time_zone_video:
            if isinstance(time_zone_video, float):
                tz_offset = timedelta(0, round(time_zone_video * 60 * 60))
                stored_date = stored_date + tz_offset
            else:
                stored_date = stored_date.astimezone(
                    pytz.timezone(time_zone_video))

        # add timezone if empty            
        if stored_date.tzinfo is None or stored_date.tzinfo.utcoffset(stored_date) is None:
            utc = pytz.UTC
            stored_date = stored_date.replace(tzinfo=utc)

        if offset_in_seconds:
            stored_date = stored_date + timedelta(0, offset_in_seconds)

        if stored_date_is_end == True:
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


def parse_gpx(input_folder_gpx, time_zone_gpx, interpolation_freq_in_seconds, stored_discard_elevation):

    parsed_gpx_points = []

    def get_gpx():
        return glob.glob(f'{input_folder_gpx}/*.gpx')

    def store_point_track(point, prev_point, start_time, time_diff_seconds):
        parsed_gpx_points.append({
            "time": point.time,
            "start_time": prev_point.time - start_time,
            "end_time": point.time - start_time,
            "diff_time": time_diff_seconds*1000,
            "latitude": point.latitude,
            "longitude": point.longitude,
            "elevation": None if stored_discard_elevation else point.elevation
        })

    gpxs = get_gpx()

    if len(gpxs):
        print(f'{Fore.GREEN}{len(gpxs)} gpx have been found.{Style.RESET_ALL}')    
    else:
        print(f'{Fore.RED}No .gpx files have been found in folder "{input_folder_gpx}"{Style.RESET_ALL}')     

    for gpx_path in gpxs:

        print('\t')
        print(f'GPX name: {gpx_path}')

        input_file = open(gpx_path, 'r')
        gpx = gpxpy.parse(input_file)
        input_file.close()

        if len(gpx.tracks) == 0:
            print(f'{Fore.RED}{input_file} has no tracks and cannot be used{Style.RESET_ALL}')
            continue

        print(f'Tracks found: {len(gpx.tracks)}')

        for track in gpx.tracks:
            prev_point = None
            start_time = None
            
            print(f'-> Track name: {track.name}')
            print(f'-> Segments found: {len(track.segments)}')

            for i, segment in enumerate(track.segments):
                len_points = len(segment.points)

                print('\t')
                print(f'--> Segment Nº{i+1}')
                print(f'---> Points: {len_points}')           

                if len_points:
                    start_time = segment.points[0].time
                    end_time = segment.points[len_points-1].time
                    print(f'---> Start time: {start_time}')
                    print(f'---> End time: {end_time}')
                    print(f'---> Duration: {end_time - start_time}')

                for point in segment.points:
                    # maybe correct the gpx timezone
                    if time_zone_gpx:       
                        if isinstance(time_zone_gpx, float):
                            offset = timedelta(0, time_zone_gpx * 60 * 60)
                            corrected_date = point.time + offset
                        else:      
                            corrected_date = point.time.astimezone(
                                pytz.timezone(time_zone_gpx))
                    else:
                        corrected_date = point.time
                    
                    # add timezone if empty
                    if corrected_date.tzinfo is None or corrected_date.tzinfo.utcoffset(corrected_date) is None:
                        utc = pytz.UTC
                        corrected_date = corrected_date.replace(tzinfo=utc)

                    point.time = corrected_date

                    if not start_time:
                        start_time = point.time              

                    if prev_point:

                        time_diff = point.time - prev_point.time
                        time_diff_seconds = time_diff.total_seconds()
                        
                        # if difference is bigger than x hours, don't interpolate
                        max_hours_diff = 12
                        if time_diff_seconds > max_hours_diff * 60 * 60:
                            prev_point = point
                            start_time = point.time
                            continue

                        if interpolation_freq_in_seconds:
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

def write_srt(points, file_name, output_folder):

    line_counter = 1

    output_filename = f'{file_name}.srt'

    output_file = open( f'{output_folder}/{output_filename}', 'w')

    base_time = points[0]['start_time']
    
    for point in points:
        output_file.write('{0}\n'.format(line_counter))
        
        num_in = (point['start_time'] - base_time)
        num_out = (point['end_time'] - base_time)

        num_in = str(num_in).split('.')
        num_out = str(num_out).split('.')

        num_in_decimals = num_in[1] if (len(num_in) > 1) else '000'
        num_in = num_in[0]

        num_out_decimals = num_out[1] if (len(num_out) > 1) else '000'
        num_out = num_out[0]

        # Use mavic 2 srt format
        output_file.write(
            '0{0},{1:.3} --> 0{2},{3:.3}\n'.format(num_in, num_in_decimals, num_out, num_out_decimals)
        )
        output_file.write(
            '<font size="36">FrameCnt : n/a, DiffTime : {:.0f}ms\n'.format(point['diff_time']))
        output_file.write(f'{point["time"]}\n')
        altitude = f'[altitude: {point["elevation"]}]' if point['elevation'] else ''
        output_file.write(
            f'[latitude : {point["latitude"]}] [longitude : {point["longitude"]}] {altitude}</font>\n')
        output_file.write('\n')

        line_counter += 1

    output_file.close()


def string_to_num(string):
    try:
        return float(string)
    except:
        return string

def intermediates(p1, p2, nb_points=8):
    '''
    Interpolate position values beteween existing coordinates
    '''
    x_spacing = (p2.latitude - p1.latitude) / (nb_points + 1)
    y_spacing = (p2.longitude - p1.longitude) / (nb_points + 1)   
    z_spacing = None

    z_spacing = (p2.elevation - p1.elevation) / (nb_points + 1) if p1.elevation and p2.elevation else None

    t_spacing = (p2.time - p1.time) / (nb_points + 1)
    
    DECIMALS = 11

    return [
        gpxpy.gpx.GPXTrackPoint(
            round(p1.latitude + i * x_spacing, DECIMALS),
            round( p1.longitude + i * y_spacing, DECIMALS),
            elevation=None if not z_spacing else round(p1.elevation + i * z_spacing, 2),
            time=p1.time + i * t_spacing
        )
        for i in range(1, nb_points+1)
    ]


if __name__ == '__main__':
    main()
