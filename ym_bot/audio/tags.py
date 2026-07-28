from mutagen.id3 import APIC, ID3, TIT2, TPE1
from mutagen.mp3 import MP3


class TagManager:
    @staticmethod
    def set_tags(file_path, title=None, artist=None):
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            if title:
                audio.tags['TIT2'] = TIT2(encoding=3, text=title)
            if artist:
                audio.tags['TPE1'] = TPE1(encoding=3, text=artist)
            audio.save()
            return True
        except:
            return False

    @staticmethod
    def set_cover(file_path, cover_data):
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags.delall('APIC')
            audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=cover_data))
            audio.save()
            return True
        except:
            return False
