from holodoppler.file_reader import FileReaderFactory
from tqdm import tqdm
import numpy as np

FILE_PATH_ON_SSD = r"D:\STAGE\260113_AUZ0752_2.holo"

FILE_PATH_ON_NAS = r"Z:\260701\260701_LEL2266859_L.holo"

batch_size = 256
batch_stride = 256

# -------------------- SSD  ---------------------

reader = FileReaderFactory.create(FILE_PATH_ON_SSD)

print(FILE_PATH_ON_SSD,  reader.file_header)

first_frame = 0
end_frame = -1
if end_frame <= 0:
    end_frame = (
        reader.file_header.num_frames
        if reader.ext == ".holo"
        else reader.TotalImageCount
    )

if batch_stride >= (end_frame - first_frame):
    num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
else:
    num_batch = int((end_frame - first_frame) / batch_stride)
if num_batch <= 0:
    exit()

# for i in tqdm(range(num_batch)):
#     fr = reader.read_frames(first_frame + i * batch_stride, batch_size)
#     fr = np.array(fr)

# -------------------- NAS  ---------------------

reader = FileReaderFactory.create(FILE_PATH_ON_NAS)

print(FILE_PATH_ON_NAS,  reader.file_header)

first_frame = 0
end_frame = -1
if end_frame <= 0:
    end_frame = (
        reader.file_header.num_frames
        if reader.ext == ".holo"
        else reader.TotalImageCount
    )

if batch_stride >= (end_frame - first_frame):
    num_batch = 1 if batch_size <= (end_frame - first_frame) else 0
else:
    num_batch = int((end_frame - first_frame) / batch_stride)
if num_batch <= 0:
    exit()

for i in tqdm(range(num_batch)):
    fr = reader.read_frames(first_frame + i * batch_stride, batch_size)
    fr = np.array(fr)