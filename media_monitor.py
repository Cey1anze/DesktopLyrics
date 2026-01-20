import asyncio
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

class MediaMonitor:
    def __init__(self):
        self.manager = None
        self.current_session = None

    async def initialize(self):
        self.manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()

    def update_session(self):
        if not self.manager:
            return None
        
        # Priority:
        # 1. Any session that is currently Playing (4)
        # 2. The system's "Current" session (which might be paused but focused)
        
        sessions = self.manager.get_sessions()
        playing_session = None
        
        if sessions:
            for session in sessions:
                try:
                    info = session.get_playback_info()
                    # 4 = GlobalSystemMediaTransportControlsSessionPlaybackStatus.Playing
                    if info and info.playback_status == 4:
                        playing_session = session
                        break
                except Exception:
                    continue
        
        if playing_session:
            self.current_session = playing_session
        else:
            self.current_session = self.manager.get_current_session()
            
        return self.current_session

    async def get_media_info(self):
        if not self.manager:
            await self.initialize()
        
        session = self.update_session()
        if not session:
            return None

        try:
            props = await session.try_get_media_properties_async()
            timeline = session.get_timeline_properties()
            playback_info = session.get_playback_info()
            
            return {
                'artist': props.artist,
                'title': props.title,
                'album': props.album_title,
                'position': timeline.position.total_seconds() if timeline else 0,
                'duration': timeline.end_time.total_seconds() if timeline else 0,
                'last_updated': timeline.last_updated_time.timestamp() if timeline and timeline.last_updated_time else 0,
                'status': playback_info.playback_status, # 4=Playing, 5=Paused
                'app_id': session.source_app_user_model_id
            }
        except Exception as e:
            print(f"Error getting media info: {e}")
            return None

if __name__ == "__main__":
    async def main():
        monitor = MediaMonitor()
        await monitor.initialize()
        while True:
            info = await monitor.get_media_info()
            if info:
                print(f"Playing: {info['title']} by {info['artist']} (Status: {info['status']}) Position: {info['position']}")
            else:
                print("No active session")
            await asyncio.sleep(1)

    asyncio.run(main())
