from pytube import YouTube

url = r'https://www.youtube.com/watch?v=cVsQLlk-T0s'
video = YouTube(url)
streams = video.streams.all()
highest_res = 0
stream = None


for s in streams:
    # find the highest quality 'mp4' file.
    if s.mime_type == 'video/mp4':
        if s.resolution:
            if 'p' in s.resolution:
                res = int(s.resolution.replace('p', ''))
                if res > highest_res:
                    highest_res = res
                    stream = s

print(stream)
# download the video
# video.download('/home/jay/Downloads')
