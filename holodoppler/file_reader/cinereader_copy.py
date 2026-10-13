import numpy as np
import struct as s
import datetime as dti

class MetaData:
	def __init__(self):
		######CINEFILEHEADER#######
		self.Type = None
		self.HeaderSize = None
		self.Compression = None
		self.Version = None
		self.FirstMovieImage = None
		self.TotalImageCount = None
		self.FirstImageNo = None
		self.ImageCount = None
		self.OffImageHeader = None
		self.OffSetup = None
		self.OffImageOffsets = None
		self.TriggerTime=None
		self.TriggerTime_displ=None
		########BitmapInfoHeade##########
		self.biSize = None
		self.biWidth = None
		self.biHeight = None
		self.biPlanes = None
		self.biBitCount = None
		self.biCompression = None
		self.biSizeImage = None
		self.biXPelsPerMeter = None
		self.biYPelsPerMeter = None
		self.biClrUsed = None
		self.biClrImportant = None
		#########SETUPINFO###########     
		self.TrigFrame = None
		self.Mark = None
		self.Length = None
		self.SigOption = None
		self.BinChannels = None
		self.SamplesPerImage = None
		self.BinName = []
		self.AnaOption = None
		self.AnaChannels = None
		self.AnaBoard = None
		self.ChOption = []
		self.AnaGain = []
		self.AnaUnit = []
		self.AnaName = []
		self.lFirstImage = None
		self.dwImageCount = None
		self.nQFactor = None
		self.wCineFileType = None
		self.szCinePath = []
		####### Acquisition. params
		self.ImWidth = None
		self.ImHeight = None
		self.Serial = None
		self.AutoExposure = None 
		self.bFlipH = None
		self.bFlipV = None
		self.Grid = None
		self.FrameRate = None #FrameRate/sec
		self.PostTrigger = None
		self.bEnableColor = None
		self.CameraVersion = None
		self.FirmwareVersion = None
		self.SoftwareVersion = None
		self.RecordingTimeZone = None
		self.CFA = None
		#ImageProces TB
		self.AutoExpLevel = None
		self.AutoExpRect = []
		self.WBGain_R = []
		self.WBGain_B = []
		self.WBGain=[]
		self.RealBPP=None 
		self.Rotate = None
		# self.WBView_R = None
		# self.WBView_B = None
		self.WBView=None
		self.FilterCode = None
		self.FilterParam = None
		self.ImFilter = None
		self.BlackCalSVer = 0
		self.WhiteCalSVer = 0
		self.GrayCalSVer = 0
		self.bStampTime = None
		self.SoundDest = None
		self.MCCnt = None
		self.CICalib = None
		self.CalibWidth = None
		self.CalibHeight = None
		self.CalibRate = None
		self.CalibExp = None
		self.CalibEDR = None
		self.CalibTemp = 0
		self.HeadSerial = None
		self.RangeCode = None
		self.RangeSize = None
		self.Decimation = None
		self.MasterSerial = None
		self.Sensor = None
		self.ExposureTime = None
		self.EDR = None
		self.FrameDelay = None
		self.ImPosXAcq = None
		self.ImPosYAcq = None
		self.ImWidthAcq = None
		self.ImHeightAcq = None
		self.RisingEdge = None
		self.FilterTime = None
		self.LongReady = None
		self.PIV = None
		self.bMetaWB = None
		self.BlackLevel = None
		self.WhiteLevel = None
		self.Bright = None
		self.Contrast = None
		self.Saturation = None
		self.Hue = None
		self.Gamma = None
		self.fGammaR = None
		self.fGammaB = None
		self.fFlare = None
		self.fPedestalR = None
		self.fPedestalG = None
		self.fPedestalB = None
		self.fChroma = None
		self.fTone = None
		self.TonePoints=None
		self.UserMatrixLabel = None
		self.EnableMatrices = None
		self.fUserMatrix = None
		self.EnableCrop = None
		self.CropRect= []
		self.EnableResample = None
		self.ResampleWidth = None
		self.ResampleHeight = None
		self.fGain16_8 = None
		self.TrigTC = None
		self.fPbRate = None
		self.fTcRate = None
		self.fGainR=None
		self.fGainG=None
		self.fGainB=None
		self.cmCalib=[]
		self.fToe=None
		self.CameraModel=None
		self.fWBTemp=None
		self.fWBCc=None
		self.WBType=None
		self.fDecimation=None
		self.SensorMode=None
		self.UndecFirst=None		
		self.SupportsBinning=None
		self.UvSensor=None
		self.AnaDaqDescription=None
		self.BinDaqDescription=None
		self.DaqOptions=None
		self.DecimatedFrameRate=None
		
		# for P10
		self.LUT_P10 = np.array([
			0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 
			8, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 12, 13, 13, 
			13, 13, 14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18,
			18, 19, 19, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 21, 22, 22, 22, 22, 23, 23, 23, 23, 
			23, 24, 24, 24, 24, 25, 25, 25, 25, 26, 26, 26, 26, 27, 27, 27, 27, 27, 28, 28, 28, 28, 
			29, 29, 29, 29, 30, 30, 30, 30, 31, 31, 31, 31, 31, 32, 32, 32, 32, 33, 33, 33, 33, 34, 
			34, 34, 34, 34, 35, 35, 35, 35, 36, 36, 36, 36, 37, 37, 37, 37, 38, 38, 38, 39, 39, 39, 
			39, 40, 40, 40, 40, 41, 41, 41, 42, 42, 42, 42, 43, 43, 43, 44, 44, 44, 44, 45, 45, 45, 
			46, 46, 46, 47, 47, 47, 48, 48, 48, 49, 49, 49, 50, 50, 50, 51, 51, 51, 52, 52, 52, 53, 
			53, 53, 54, 54, 54, 55, 55, 55, 56, 56, 56, 57, 57, 58, 58, 58, 59, 59, 59, 60, 60, 61, 
			61, 61, 62, 62, 63, 63, 63, 64, 64, 65, 65, 65, 66, 66, 67, 67, 67, 68, 68, 69, 69, 70, 
			70, 70, 71, 71, 72, 72, 73, 73, 73, 74, 74, 75, 75, 76, 76, 77, 77, 78, 78, 78, 79, 79, 
			80, 80, 81, 81, 82, 82, 83, 83, 84, 84, 85, 85, 86, 86, 87, 87, 88, 88, 89, 89, 90, 90, 
			91, 91, 92, 92, 93, 93, 94, 94, 95, 95, 96, 96, 97, 97, 98, 99, 99, 100, 100, 101, 101, 
			102, 102, 103, 104, 104, 105, 105, 106, 106, 107, 107, 108, 109, 109, 110, 110, 111, 112, 
			112, 113, 113, 114, 114, 115, 116, 116, 117, 118, 118, 119, 119, 120, 121, 121, 122, 122, 
			123, 124, 124, 125, 126, 126, 127, 127, 128, 129, 129, 130, 131, 131, 132, 133, 133, 134, 
			135, 135, 136, 137, 137, 138, 139, 139, 140, 141, 141, 142, 143, 143, 144, 145, 145, 146, 
			147, 148, 148, 149, 150, 150, 151, 152, 152, 153, 154, 155, 155, 156, 157, 158, 158, 159, 
			160, 160, 161, 162, 163, 163, 164, 165, 166, 166, 167, 168, 169, 169, 170, 171, 172, 172, 
			173, 174, 175, 176, 176, 177, 178, 179, 179, 180, 181, 182, 183, 183, 184, 185, 186, 187, 
			187, 188, 189, 190, 191, 191, 192, 193, 194, 195, 196, 196, 197, 198, 199, 200, 201, 201, 
			202, 203, 204, 205, 206, 207, 207, 208, 209, 210, 211, 212, 213, 213, 214, 215, 216, 217, 
			218, 219, 220, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 229, 230, 231, 232, 233, 
			234, 235, 236, 237, 238, 239, 240, 241, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 
			251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 
			269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 
			287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 300, 301, 302, 303, 304, 305, 
			306, 307, 308, 309, 310, 311, 312, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 325, 
			326, 327, 328, 329, 330, 331, 332, 334, 335, 336, 337, 338, 339, 340, 342, 343, 344, 345, 
			346, 347, 349, 350, 351, 352, 353, 354, 356, 357, 358, 359, 360, 361, 363, 364, 365, 366, 
			367, 369, 370, 371, 372, 373, 375, 376, 377, 378, 380, 381, 382, 383, 384, 386, 387, 388, 
			389, 391, 392, 393, 394, 396, 397, 398, 399, 401, 402, 403, 404, 406, 407, 408, 409, 411, 
			412, 413, 415, 416, 417, 418, 420, 421, 422, 424, 425, 426, 427, 429, 430, 431, 433, 434, 
			435, 437, 438, 439, 441, 442, 443, 445, 446, 447, 449, 450, 451, 453, 454, 455, 457, 458, 
			459, 461, 462, 464, 465, 466, 468, 469, 470, 472, 473, 475, 476, 477, 479, 480, 481, 483, 
			484, 486, 487, 489, 490, 491, 493, 494, 496, 497, 498, 500, 501, 503, 504, 506, 507, 508, 
			510, 511, 513, 514, 516, 517, 519, 520, 521, 523, 524, 526, 527, 529, 530, 532, 533, 535, 
			536, 538, 539, 541, 542, 544, 545, 547, 548, 550, 551, 553, 554, 556, 557, 559, 560, 562, 
			563, 565, 566, 568, 569, 571, 573, 574, 576, 577, 579, 580, 582, 583, 585, 587, 588, 590, 
			591, 593, 594, 596, 598, 599, 601, 602, 604, 605, 607, 609, 610, 612, 613, 615, 617, 618, 
			620, 622, 623, 625, 626, 628, 630, 631, 633, 635, 636, 638, 639, 641, 643, 644, 646, 648, 
			649, 651, 653, 654, 656, 658, 659, 661, 663, 664, 666, 668, 669, 671, 673, 674, 676, 678, 
			680, 681, 683, 685, 686, 688, 690, 691, 693, 695, 697, 698, 700, 702, 704, 705, 707, 709, 
			711, 712, 714, 716, 717, 719, 721, 723, 725, 726, 728, 730, 732, 733, 735, 737, 739, 740, 
			742, 744, 746, 748, 749, 751, 753, 755, 757, 758, 760, 762, 764, 766, 767, 769, 771, 773, 
			775, 777, 778, 780, 782, 784, 786, 788, 789, 791, 793, 795, 797, 799, 801, 802, 804, 806, 
			808, 810, 812, 814, 815, 817, 819, 821, 823, 825, 827, 829, 831, 832, 834, 836, 838, 840, 
			842, 844, 846, 848, 850, 852, 854, 855, 857, 859, 861, 863, 865, 867, 869, 871, 873, 875, 
			877, 879, 881, 883, 885, 887, 889, 891, 893, 895, 897, 899, 901, 903, 905, 907, 909, 911, 
			913, 915, 917, 919, 921, 923, 925, 927, 929, 931, 933, 935, 937, 939, 941, 943, 945, 947, 
			949, 951, 953, 955, 957, 959, 961, 963, 965, 968, 970, 972, 974, 976, 978, 980, 982, 984, 
			986, 988, 990, 993, 995, 997, 999, 1001, 1003, 1005, 1007, 1009, 1012, 1014, 1016, 1023, 
			1023, 1023, 1023, 1023, 1020, 1023, 1023, 1023
			])

		
def read_metadata(cine_path):
	md = MetaData()
	with open(cine_path, mode="rb") as fId:
		######CINEFILEHEADER#######
		md.Type = s.unpack('2s', fId.read(2))[0].decode('utf-8')  # ASCII
		md.HeaderSize = s.unpack('H', fId.read(2))[0] #unpack 2 bytes, H is 16bit int in native byte order
		md.Compression = s.unpack('H', fId.read(2))[0]
		md.Version = s.unpack('H', fId.read(2))[0]
		md.FirstMovieImage = s.unpack('i', fId.read(4))[0] #int32
		md.TotalImageCount = s.unpack('I', fId.read(4))[0]
		md.FirstImageNo = s.unpack('i', fId.read(4))[0]
		md.ImageCount = s.unpack('I', fId.read(4))[0]
		md.OffImageHeader = s.unpack('I', fId.read(4))[0] #44
		md.OffSetup = s.unpack('I', fId.read(4))[0]  #84
		md.OffImageOffsets = s.unpack('I', fId.read(4))[0]  #16710
		md.TriggerTime = s.unpack('Q', fId.read(8))[0]
		md.TriggerTime_displ = f"{dti.datetime.fromtimestamp((md.TriggerTime  >> 32), tz=dti.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}.{int(10**6*(round(float((2**32-1) & md.TriggerTime )/(2**32 ),8)))}"
		########BitmapInfoHeader##########
		md.biSize = s.unpack('I', fId.read(4))[0]
		md.biWidth = s.unpack('i', fId.read(4))[0]
		md.biHeight = s.unpack('i', fId.read(4))[0]
		md.biPlanes = s.unpack('H', fId.read(2))[0]
		md.biBitCount = s.unpack('H', fId.read(2))[0]
		md.biCompression = s.unpack('I', fId.read(4))[0]
		md.biSizeImage = s.unpack('I', fId.read(4))[0]
		md.biXPelsPerMeter = s.unpack('i', fId.read(4))[0]
		md.biYPelsPerMeter = s.unpack('i', fId.read(4))[0]
		md.biClrUsed = s.unpack('I', fId.read(4))[0]
		md.biClrImportant = s.unpack('I', fId.read(4))[0]
		#########SETUPINFO###########
		s.unpack('H', fId.read(2))[0]# FrameRate16 replaced by FrameRate
		s.unpack('H', fId.read(2))[0]# Shutter16 replaced by ShutterNs
		s.unpack('H', fId.read(2))[0]# PostTrigger16, replaced by PostTrigger
		s.unpack('H', fId.read(2))[0]# FrameDelay16;UPDF replaced by FrameDelayNs
		s.unpack('H', fId.read(2))[0]# AspectRatio = UPDF replaced by ImWidth, ImHeight
		s.unpack('H', fId.read(2))[0]# Res7 = Contrast16 TBIs
		s.unpack('H', fId.read(2))[0]# TBI  Res8 = Bright16
		s.unpack('B', fId.read(1))[0]# TBI Res9=Rotate16 #unit8
		s.unpack('B', fId.read(1))[0]# TBI md.Res10 TimeAnnotation
		s.unpack('B', fId.read(1))[0]# TBI Res11 = TrigCine
		md.TrigFrame = s.unpack('B', fId.read(1))[0] #Sync imaging mode 0, 1, 2 = internal, external, locktoirig
		s.unpack('B', fId.read(1))[0] #md.Res12 = TBI ShutterOn (the shutter is always on)
		s.unpack('121s', fId.read(121))[0].decode('ascii', 'ignore').rstrip('\x00') # Replaced md.DescriptionOld =
		md.Mark = s.unpack('2s', fId.read(2))[0].decode('utf-8')
		md.Length = s.unpack('H', fId.read(2))[0]
		s.unpack('H', fId.read(2))[0]# TBI md.Res13 = binning factor
		md.SigOption = s.unpack('H', fId.read(2))[0] #MAXSAMPLE max possible samples
		md.BinChannels = s.unpack('H', fId.read(2))[0] #Number of binary channels read from the SAM
		md.SamplesPerImage = s.unpack('B', fId.read(1))[0]
		##(here is 235)
		for i in range(235, 323, 11):
			bin_name_bytes = s.unpack('11s', fId.read(11))[0]
			bin_name = bin_name_bytes.strip(b'\x00').decode('utf-8', 'ignore')
			md.BinName.append(bin_name)
		md.AnaOption = s.unpack('H', fId.read(2))[0]
		md.AnaChannels = s.unpack('h', fId.read(2))[0]
		s.unpack('B', fId.read(1))[0] #md.Res6 = TBI
		md.AnaBoard = s.unpack('B', fId.read(1))[0]
		for i in range(329, 345, 2):
			ch_option = s.unpack("<h", fId.read(2))[0]  # Read 2 bytes
			md.ChOption.append(ch_option)
		for i in range(345, 377, 4):
			ana_gain = s.unpack("<f", fId.read(4))[0]  #
			md.AnaGain.append(ana_gain)
		for i in range(377, 425, 6):
			ana_unit_bytes = s.unpack("<6s", fId.read(6))[0]
			ana_unit = ana_unit_bytes.strip(b'\x00').decode('utf-8', 'ignore')
			md.AnaUnit.append(ana_unit)
		for i in range(425, 513, 11):
			ana_name_bytes = s.unpack("<11s", fId.read(11))[0]  # Read 11 bytes
			ana_name = ana_name_bytes.strip(b'\x00').decode('utf-8', 'ignore')
			md.AnaName.append(ana_name)
		md.lFirstImage = s.unpack('i', fId.read(4))[0]
		md.dwImageCount = s.unpack('I', fId.read(4))[0]
		md.nQFactor = s.unpack('h', fId.read(2))[0]
		md.wCineFileType = s.unpack('H', fId.read(2))[0]
		for i in range(525, 785, 65):
			sz_cine_path_bytes = s.unpack("<65s", fId.read(65))[0]
			sz_cine_path = sz_cine_path_bytes.strip(b'\x00').decode('utf-8', 'ignore')
			md.szCinePath.append(sz_cine_path)
		s.unpack('H', fId.read(2))[0]#TBI Res14
		s.unpack('B', fId.read(1))[0]#TBI Res15
		s.unpack('B', fId.read(1))[0]#TBI Res16
		s.unpack('H', fId.read(2))[0]#TBI Res17
		s.unpack('d', fId.read(8))[0]#TBI Res18
		s.unpack('d', fId.read(8))[0]#TBI Res19
		s.unpack('H', fId.read(2))[0]#TBI Res20
		s.unpack('i', fId.read(4))[0]#TBI Res1
		s.unpack('i', fId.read(4))[0]#TBI Res2
		s.unpack('i', fId.read(4))[0]#TBI Res3
		###########data acqus. paramas setup#############
		md.ImWidth = s.unpack('H', fId.read(2))[0]
		md.ImHeight = s.unpack('H', fId.read(2))[0]
		s.unpack('H', fId.read(2))[0] #to be Replaced with EDR, EDRShutter16
		md.Serial = s.unpack('I', fId.read(4))[0] #serial number
		s.unpack('i', fId.read(4))[0] #UPDF replaced by fSaturation
		s.unpack('B', fId.read(1))[0]# TBI Res5
		md.AutoExposure = s.unpack('I', fId.read(4))[0] #0=disable, 1=lock at trigger
		md.bFlipH = s.unpack('i', fId.read(4))[0]
		md.bFlipV = s.unpack('i', fId.read(4))[0]
		md.Grid = s.unpack('I', fId.read(4))[0]
		s.unpack('I', fId.read(4))[0] #md.FrameRate =
		s.unpack('I', fId.read(4))[0] #UPDF replaced by ShutterNs
		s.unpack('I', fId.read(4))[0] #UPDF replaced by EDRShutterNs
		md.PostTrigger = s.unpack('I', fId.read(4))[0]
		s.unpack('I', fId.read(4))[0]  #UPDF replaced by FrameDelayNs
		md.bEnableColor = s.unpack('i', fId.read(4))[0]
		md.CameraVersion = s.unpack('I', fId.read(4))[0]
		md.FirmwareVersion = s.unpack('I', fId.read(4))[0]
		md.SoftwareVersion = s.unpack('I', fId.read(4))[0]
		md.RecordingTimeZone = s.unpack('i', fId.read(4))[0]
		md.CFA = s.unpack('I', fId.read(4))[0]
		if  md.CFA==0:
			md.CFA=str('Mono')
		#elif md.CFA==1:                   #NOT USED ANYMORE
		#   md.CFA=str('gbrg/rggb')
		#elif md.CFA==2:                   #NOT USED ANYMORE
		#   md.CFA=str('bggr/grbg')
		elif md.CFA==3:
			md.CFA=str('gb/rg') # BAYER : VEO sensors
		elif md.CFA==4:
			md.CFA=str('rg/gb') # BAYERFLIP : Flex4k Sensor
		elif md.CFA==5:
			md.CFA = str('gr/gb') # BAYERFLIPB : Miro C 
		elif md.CFA==6:
			md.CFA = str('bg/gr') # BAYERFLIPH
		else:
			md.CFA = str('unknown CFA')
		s.unpack('i', fId.read(4))[0] #0??Bright , replaced by fOffset
		s.unpack('i', fId.read(4))[0] #0Contrast =UPDF replaced by fGain
		s.unpack('i', fId.read(4))[0] #PDF replaced by fGamma
		s.unpack('I', fId.read(4))[0] # TBI Res21 =
		md.AutoExpLevel = s.unpack('I', fId.read(4))[0]
		s.unpack('I', fId.read(4))[0] #md.AutoESxpSpeed =
		AutoExpRect_left = s.unpack('i', fId.read(4))[0]
		AutoExpRect_top = s.unpack('i', fId.read(4))[0]
		AutoExpRect_right = s.unpack('i', fId.read(4))[0]
		AutoExpRect_bottom = s.unpack('i', fId.read(4))[0]
		md.AutoExpRect=(AutoExpRect_left,AutoExpRect_top,AutoExpRect_right,AutoExpRect_bottom)
		WBGain1_R = s.unpack('f', fId.read(4))[0]
		WBGain1_B = s.unpack('f', fId.read(4))[0]
		WBGain2_R = s.unpack('f', fId.read(4))[0]
		WBGain2_B = s.unpack('f', fId.read(4))[0]
		WBGain3_R = s.unpack('f', fId.read(4))[0]
		WBGain3_B = s.unpack('f', fId.read(4))[0]
		WBGain4_R = s.unpack('f', fId.read(4))[0]
		WBGain4_B = s.unpack('f', fId.read(4))[0]
		WBGain_R = WBGain1_R   #[WBGain1_R, WBGain2_R, WBGain3_R, WBGain4_R]
		WBGain_B = WBGain1_B   #[WBGain1_B, WBGain2_B, WBGain3_B, WBGain4_B]
		md.WBGain=[round(WBGain_R,2), round(WBGain_B,2)] #[WBGain_R, WBGain_B]
		md.Rotate = s.unpack('i', fId.read(4))[0]
		WBView_R = s.unpack('f', fId.read(4))[0]
		WBView_B = s.unpack('f', fId.read(4))[0]
		md.WBView=(WBView_R,WBView_B)
		md.RealBPP = s.unpack('I', fId.read(4))[0]
		s.unpack('I', fId.read(4))[0] #TBI Conv8Min =
		s.unpack('I', fId.read(4))[0] #UPDF Conv8Max replaced by fGain16_8
		md.FilterCode = s.unpack('i', fId.read(4))[0]
		md.FilterParam = s.unpack('i', fId.read(4))[0]
		#ImFilter params
		UF_dim = s.unpack('i', fId.read(4))[0]
		UF_shifts = s.unpack('i', fId.read(4))[0]
		UF_bias = s.unpack('i', fId.read(4))[0]
		UF_Coef=s.unpack("<25i", fId.read(4*5*5))
		md.ImFilter=(UF_dim,UF_shifts,UF_bias,UF_Coef) 
		########
		md.BlackCalSVer = s.unpack('I', fId.read(4))[0]
		md.WhiteCalSVer = s.unpack('I', fId.read(4))[0]
		md.GrayCalSVer = s.unpack('I', fId.read(4))[0]
		md.bStampTime = s.unpack('i', fId.read(4))[0]
		md.SoundDest = s.unpack('I', fId.read(4))[0]
		#FR profile;here is 1136
		s.unpack('I', fId.read(4))[0]#md.FRPSteps =
		np.frombuffer(fId.read(4 * 16), dtype='i4')#md.FRPImgNr =
		np.frombuffer(fId.read(4 * 16), dtype='i4') # md.FRPRate =
		np.frombuffer(fId.read(4 * 16), dtype='i4')  # md.FRPExp =
		md.MCCnt = s.unpack('i', fId.read(4))[0] #partition count
		np.frombuffer(fId.read(4 * 64), dtype='float32') #md.MCPercent =
		md.CICalib = s.unpack('I', fId.read(4))[0] #CSR
		md.CalibWidth = s.unpack('I', fId.read(4))[0]
		md.CalibHeight = s.unpack('I', fId.read(4))[0]
		md.CalibRate = s.unpack('I', fId.read(4))[0]
		md.CalibExp = s.unpack('I', fId.read(4))[0]
		md.CalibEDR = s.unpack('I', fId.read(4))[0]
		md.CalibTemp = s.unpack('I', fId.read(4))[0]
		md.HeadSerial = np.frombuffer(fId.read(4 * 4), dtype='i4')#4 uint32 = 16 bytes
		md.RangeCode = s.unpack('I', fId.read(4))[0]
		md.RangeSize = s.unpack('I', fId.read(4))[0]
		md.Decimation = s.unpack('I', fId.read(4))[0]
		md.MasterSerial = s.unpack('I', fId.read(4))[0]
		md.Sensor = s.unpack('I', fId.read(4))[0]
		#Acquisition parameters in nanoseconds
		md.ExposureTime = s.unpack('I', fId.read(4))[0] / 1000 #ShutterNs
		md.EDR = s.unpack('I', fId.read(4))[0] / 1000 # EDRShutterNs
		md.FrameDelay = s.unpack('I', fId.read(4))[0]  #FrameDelayNs
		md.ImPosXAcq = s.unpack('I', fId.read(4))[0]
		md.ImPosYAcq = s.unpack('I', fId.read(4))[0]
		md.ImWidthAcq = s.unpack('I', fId.read(4))[0]
		md.ImHeightAcq = s.unpack('I', fId.read(4))[0]
		s.unpack("<4096s", fId.read(4096))[0].rstrip(b'\x00').decode('utf-8', 'ignore')#1680:5776] #md.Description=
		md.RisingEdge = s.unpack('i', fId.read(4))[0]
		md.FilterTime = s.unpack('I', fId.read(4))[0]
		md.LongReady = s.unpack('i', fId.read(4))[0]
		md.PIV = s.unpack('i', fId.read(4))[0]  #  ShutterOff
		np.frombuffer(fId.read(16), dtype='uint8')#TBI md.Res4, 16 bytes
		md.bMetaWB = s.unpack('i', fId.read(4))[0]
		s.unpack('i', fId.read(4))[0] #md.Hue = repaced by fHue
		md.BlackLevel = s.unpack('i', fId.read(4))[0]
		md.WhiteLevel = s.unpack('i', fId.read(4))[0]
		s.unpack("<256s", fId.read(256))[0].rstrip(b'\x00').decode('utf-8', 'ignore')#[5824:6080 %md.LensDescription =
		s.unpack('f', fId.read(4))[0] #md.LensAperture =
		s.unpack('f', fId.read(4))[0] #md.LensFocusDistance =
		s.unpack('f', fId.read(4))[0] #md.LensFocalLength =
		md.Bright = s.unpack('f', fId.read(4))[0]#fOffset
		md.Contrast = s.unpack('f', fId.read(4))[0]#fGain
		md.Saturation= s.unpack('f', fId.read(4))[0]#fSaturation
		md.Hue= s.unpack('f', fId.read(4))[0] #fHue
		md.Gamma = s.unpack('f', fId.read(4))[0]#fGamma
		md.fGammaR = s.unpack('f', fId.read(4))[0]
		md.fGammaB = s.unpack('f', fId.read(4))[0]
		md.fFlare = s.unpack('f', fId.read(4))[0]
		md.fPedestalR = s.unpack('f', fId.read(4))[0]
		md.fPedestalG = s.unpack('f', fId.read(4))[0]
		md.fPedestalB = s.unpack('f', fId.read(4))[0]
		md.fChroma = s.unpack('f', fId.read(4))[0]
		s.unpack("<256s", fId.read(256))[0].strip(b'\x00').decode('utf-8', 'ignore')  # ToneLabel =
		md.TonePoints=s.unpack('i', fId.read(4))[0] #TonePoints =
		md.fTone = np.frombuffer(fId.read(4 * 32 * 2), dtype='f4')
		s.unpack("<256s", fId.read(256))[0].strip(b'\x00').decode('utf-8', 'ignore') # md.UserMatrixLabel
		md.EnableMatrices = s.unpack('i', fId.read(4))[0]
		md.fUserMatrix = np.frombuffer(fId.read(4 * 9), dtype='f4')
		md.EnableCrop = s.unpack('i', fId.read(4))[0]
		CropRect_left = s.unpack('i', fId.read(4))[0]
		CropRect_top = s.unpack('i', fId.read(4))[0]
		CropRect_right = s.unpack('i', fId.read(4))[0]
		CropRect_bottom = s.unpack('i', fId.read(4))[0]
		md.CropRect=(CropRect_left,CropRect_top,CropRect_right,CropRect_bottom)
		md.EnableResample = s.unpack('i', fId.read(4))[0]
		md.ResampleWidth = s.unpack('I', fId.read(4))[0]
		md.ResampleHeight = s.unpack('I', fId.read(4))[0]
		md.fGain16_8 = s.unpack('f', fId.read(4))[0]
		np.frombuffer(fId.read(4 * 16), dtype='i4') # FRPShape =
		md.TrigTC = np.frombuffer(fId.read(8), dtype='uint8') #to do get a correct TC object
		md.fPbRate = s.unpack('f', fId.read(4))[0]
		md.fTcRate = s.unpack('f', fId.read(4))[0]
		s.unpack("<256s", fId.read(256))[0].strip(b'\x00').decode('utf-8', 'ignore')#here is 7068:7324 md.CineName =
		# For the last part, which is a 3180-byte block
		md.fGainR = s.unpack('f', fId.read(4))[0]
		md.fGainG = s.unpack('f', fId.read(4))[0]
		md.fGainB = s.unpack('f', fId.read(4))[0]
		for i in range(7336, 7372, 4):
			cm_Calib = s.unpack("<f",fId.read(4))[0] #cmCalib[9] 9 float = 36 bytes
			md.cmCalib.append(cm_Calib)

		md.fWBTemp= s.unpack('f', fId.read(4))[0]#
		md.fWBCc= s.unpack('f', fId.read(4))[0] #

		s.unpack("<1024s", fId.read(1024))[0]#.strip(b'\x00').decode('utf-8', 'ignore') #md.CalibrationInfo
		s.unpack("<1024s", fId.read(1024))[0]#.strip(b'\x00').decode('utf-8', 'ignore') #md.OpticalFilter
		s.unpack("<256s", fId.read(256))[0]#.strip(b'\x00').decode('utf-8', 'ignore')#md.GpsInfo
		s.unpack("<256s", fId.read(256))[0]#.strip(b'\x00').decode('utf-8', 'ignore')#md.UID
		s.unpack("<256s", fId.read(256))[0]#.strip(b'\x00').decode('utf-8', 'ignore')#md.Created by
		s.unpack("<I", fId.read(4))[0] #md.RecBPP =
		s.unpack("<H", fId.read(2))[0]  #md.LowestFormatBPP =
		s.unpack("<H", fId.read(2))[0]  #md.LowestFormatQ =
		md.fToe = s.unpack("<f", fId.read(4))[0] #Controls the gamma curve in the blacks
		s.unpack("<I", fId.read(4))[0] #md.LogMode =
		md.CameraModel = s.unpack("<256s", fId.read(256))[0].strip(b'\x00').decode('utf-8', 'ignore')  # CameraModel[256] -> MAXSTDSTRSZ = 256
		md.WBType = s.unpack("<I", fId.read(4))[0]
		md.fDecimation = s.unpack("<f", fId.read(4))[0]
		s.unpack("<I", fId.read(4))[0] #md.MagSerial =
		s.unpack("<I", fId.read(4))[0] #md.CSSerial =
		md.FrameRate = s.unpack("<d", fId.read(8))[0]  #High precision acquisition frame rate
		md.SensorMode = s.unpack("<I", fId.read(4))[0]
		md.UndecFirst =s.unpack("<I", fId.read(4))[0]
		md.SupportsBinning=s.unpack("<I", fId.read(4))[0]
		md.UvSensor=s.unpack("<I", fId.read(4))[0]
		md.AnaDaqDescription =s.unpack("<128s", fId.read(128))[0].strip(b'\x00').decode('utf-8', 'ignore')
		md.BinDaqDescription =s.unpack("<128s", fId.read(128))[0].strip(b'\x00').decode('utf-8', 'ignore')
		md.DaqOptions=s.unpack("<I", fId.read(4))[0]
		md.DecimatedFrameRate = md.FrameRate / md.fDecimation

	return md