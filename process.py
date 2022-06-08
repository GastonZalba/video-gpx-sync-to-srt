import os
import glob
import gpxpy
import traceback

input_folder = 'input'
output_folder = 'output'

# to interpolaate coordinates values betweeen points
# `None` to disable
interpolate_every_seconds = 1

output_file = ''

line_counter = 1

def init():

    global output_file, line_counter

    try:

        for subdir, dirs, files in os.walk(input_folder + '\gpx'):
            for file in files:

                filepath = subdir + os.sep + file

                # remove extension
                file_name = os.path.splitext(file)[0]

                if file.endswith(".gpx"):

                    input_file = open(filepath, 'r')
                    gpx = gpxpy.parse(input_file)
                    input_file.close()

                    track_number = 0

                    if len(gpx.tracks) == 0:
                        raise Exception('File has no tracks')

                    for track in gpx.tracks:

                        segment_number = 0

                        for segment in track.segments:
                            prev_point = None
                            start_time = None
                            line_counter = 1
                                                            
                            output_filename = f'{file_name}_{track_number}_{segment_number}.srt'

                            output_file = open(f'{output_folder}/{output_filename}', 'w')

                            for point in segment.points:

                                if not start_time:
                                    start_time = point.time

                                if prev_point:

                                    time_diff = point.time - prev_point.time
                                    time_diff_seconds = time_diff.total_seconds()

                                    intermediate_points = []

                                    if interpolate_every_seconds != None:
                                        if round(time_diff_seconds) > interpolate_every_seconds:
                                            extra_points = round(
                                                time_diff_seconds / interpolate_every_seconds) - 1
                                            intermediate_points = intermediates(
                                                prev_point, point, extra_points)

                                    if len(intermediate_points):
                                        for ipoint in intermediate_points:
                                            # print(ipoint)
                                            time_diff = ipoint.time - prev_point.time
                                            time_diff_seconds = time_diff.total_seconds()
                                            write_srt_line(
                                                ipoint, prev_point, start_time, time_diff_seconds)
                                            prev_point = ipoint

                                    write_srt_line(
                                        point, prev_point, start_time, time_diff_seconds)

                                prev_point = point
                            output_file.close()
                            segment_number = segment_number + 1
                        track_number = track_number + 1

        print('Process was completed successfully')

    except Exception as error:
        print(error)
        print(traceback.format_exc())


def write_srt_line(point, prev_point, start_time, time_diff_seconds):

    global line_counter

    output_file.write('{0}\n'.format(line_counter))

    # Use mavic 2 srt format
    output_file.write(
        '{0},000 --> {1},000\n'.format((prev_point.time - start_time), (point.time - start_time)))
    output_file.write(
        '<font size="36">FrameCnt : n/a, DiffTime : {:.0f}ms\n'.format(time_diff_seconds*1000))
    output_file.write(f'{point.time}\n')
    output_file.write(
        f'[iso : n/a] [shutter : n/a] [fnum : n/a] [ev : n/a] [ct : n/a] [color_md : n/a] [focal_len : n/a] [latitude : {point.latitude}] [longtitude : {point.longitude}] [altitude: {point.elevation}] </font>\n')
    output_file.write('\n')

    line_counter += 1


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


def get_movies():
    types = ('*.mp4', '*.MP4', '*.mts', '*.mov', '*.MOV')
    files_grabbed = []
    for type in types:
        files_grabbed.extend(glob.glob(input_folder + type))
    return files_grabbed


init()