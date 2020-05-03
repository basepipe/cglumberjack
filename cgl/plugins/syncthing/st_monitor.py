import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cgl.plugins.syncthing.utils import get_config_path

# I wonder if this could be running as a seperate program within the lumbermill toolset.  Sort of a Daemon that's
# always running in the background.  We could add other things like message listeners to it as well.  Probably the
# way to go.


class SyncthingMonitor(FileSystemEventHandler):
    def on_modified(self, event):
        print("SyncThing Config File Changed!")


if __name__ == "__main__":
    event_handler = SyncthingMonitor()
    observer = Observer()
    observer.schedule(event_handler, path=get_config_path(), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
