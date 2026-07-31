from holodoppler.utils import create_holo
from holodoppler.file_reader import HoloFileReader
from pathlib import Path


DATA_PATH = Path(r"Z:\260316_ABERRATIONS\260316_AUZ0752_1.holo")

NFRAMES = 512

EXPORT_FOLDER = Path(r"./debug_outputs")

reader = HoloFileReader(DATA_PATH)

fr = reader.read_frames(0, NFRAMES)

create_holo(EXPORT_FOLDER/DATA_PATH.name,fr,version=777,bit_depth=8,footer=reader.footer)