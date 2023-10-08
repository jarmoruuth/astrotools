# This tool needs Python 3
# Other requirements:
#   NumPy - pip install numpy
#   AstroPy - pip install astropy --no-deps
#
# Args:
#   list, l - list some interesting FITS header info
#   move, m - move files to XRESxYRES directory, directory is created automatically
#   header, h - print all FITS heeader values
#   coordinates, c - recursively find coordinates from FITS file names
#   filter, f - print just FILTER keyword
#   summary, s - generate summary information from FITS files like telescopes, filters and exposure times
#   unprocessed, u - find directories which are unprocessed
#   decompress, d - decompress FITS images so they can be loaded into PixInsight
#
# Example:
#   python fitspy.py list *.fit
#   python fitspy.py move *.fit
#   python fitspy.py header *.fit
#   python fitspy.py coordinates
#   python fitspy.py filter *.fit
#   python fitspy.py summary *.fit
#   python fitspy.py unprocessed
#   python fitspy.py decompress *.fit
#

import glob
import os
import sys
from glob import iglob
from astropy.io import fits
from datetime import datetime

class Exptime:
    def __init__(self):
        self.exp = []
        self.cnt = []

class Datefilters:
    def __init__(self):
        self.date = ''
        self.filter = ''
        self.exptime = []
        self.cnt = []

# Astrobin filter ids: H 4499, OIII 4505, SII 4511, L 4544, R 4549, G 4537, B 4531
def filter_id(filter):
    filter = filter[0:1].upper()
    if filter == 'L':
        return 4544
    elif filter == 'R':
        return 4549
    elif filter == 'G':
        return 4537
    elif filter == 'B':
        return 4531
    elif filter == 'H':
        return 4499
    elif filter == 'O':
        return 4505
    elif filter == 'S':
        return 4511
    else:
        return 0

def find_in_list(list, val):
    index = 0
    found = False
    for x in list:
        if x == val:
            found = True
            break
        index = index + 1
    if found:
        return index
    else:
        return -1

def format_time(num):
    return str(num)

def secs_to_time(seconds):
    h = seconds//3600
    m = (seconds%3600)//60
    s = (seconds%3600)%60
    d = ''
    if h > 0:
        d = d + format_time(h) + 'h '
    if m > 0:
        d = d + format_time(m) + 'm '
    if s > 0:
        d = d + format_time(s) + 's '
    return d.strip()

telescopes = [ 
    [ "AUS-2", "Takahashi FSQ-106ED", "FLI PL16803", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "Heaven's Mirror Observatory, Australia" ],
    [ "SPA-1", "Takahashi FSQ-106ED", "FLI PL16083", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "IC Astronomy Observatory, Spain" ],
    [ "SPA-2", "Officina Stellare ProRC 700", "FLI PL16803", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "IC Astronomy Observatory, Spain" ],
    [ "SPA-3", "Takahashi FSQ-106EDX4", "FLI PL16083", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "IC Astronomy Observatory, Spain" ],
    [ "CHI-1", "Planewave CDK24", "FLI ProLine PL9000", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "El Sauce Observatory, Chile" ],
    [ "CHI-2", "ASA 500N", "FLI PL16803", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-3", "ASA RC-1000AZ", "FLI PL16803", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "El Sauce Observatory, Chile"  ],
    [ "CHI-4", "ASA 500N", "FLI PL16803", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-5", "Nikon 200 F/2", "FLI ML16200", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-6", "Officina Stellare RH200", "FLI ML16200", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],

    [ "AUS-2-CMOS", "Takahashi FSQ-106ED", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "Heaven's Mirror Observatory, Australia", "El Sauce Observatory, Chile"  ],
    [ "SPA-1-CMOS", "Takahashi FSQ-106ED", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "IC Astronomy Observatory, Spain", "El Sauce Observatory, Chile"  ],
    [ "SPA-2-CMOS", "Officina Stellare ProRC 700", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "IC Astronomy Observatory, Spain", "El Sauce Observatory, Chile"  ],
    [ "SPA-3-CMOS", "Takahashi FSQ-106EDX4", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "IC Astronomy Observatory, Spain", "El Sauce Observatory, Chile"  ],
    [ "CHI-1-CMOS", "Planewave CDK24", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "El Sauce Observatory, Chile"  ],
    [ "CHI-2-CMOS", "ASA 500N", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-3-CMOS", "ASA RC-1000AZ", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm), Sloan r, Sloan g, Sloan i", "El Sauce Observatory, Chile"  ],
    [ "CHI-4-CMOS", "ASA 500N", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-5-CMOS", "Nikon 200 F/2", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ],
    [ "CHI-6-CMOS", "Officina Stellare RH200", "QHY 600M", "Astrodon LRGB 2GEN, Ha (3nm), SII (3nm), OIII (3nm)", "El Sauce Observatory, Chile"  ]
]

def get_telescope(txt):
    for x in telescopes:
        if x[0] == txt:
            return x[1] + ' (' + txt + ') ' + x[4]
    return txt

if len(sys.argv) < 2:
    print ("Usage: python fitspy.py {list|move|header|coordinates} [file]")
    print ("  list - list some interesting FITS header info")
    print ("  move - move files to XRESxYRES directory, directory is created automatically")
    print ("  header - print all FITS heeader values")
    print ("  coordinates - recursively find coordinates from FITS file names")
    print ("  filter - print just FILTER keyword")
    print ("  summary - generate summary information from FITS files like telescopes, filters and exposure times")
    print ("  unprocessed - find directories which are unprocessed")
    sys.exit()

#
# list
#
if sys.argv[1] == 'list' or sys.argv[1] == 'l':
    if len(sys.argv) == 2:
        imgpath = "*.fit"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    imglist = []
    for img in imgfiles:
        hdul = fits.open(img)
        print (img + '  ' +
            str(hdul[0].header['NAXIS1']) + ' ' + 
            str(hdul[0].header['NAXIS2']) + ' ' +
            str(hdul[0].header['TELESCOP'])[10:12] + ' ' +
            str(hdul[0].header['FILTER']) + ' ' +
            #str(hdul[0].header['FOCALLEN']) + ' ' +
            #str(hdul[0].header['APTDIA']) + ' ' +
            '')

#
# filter
#
elif sys.argv[1] == 'filter' or sys.argv[1] == 'f':
    if len(sys.argv) == 2:
        imgpath = "*.fit"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    imglist = []
    for img in imgfiles:
        hdul = fits.open(img)
        print (img + '  ' + str(hdul[0].header['FILTER']))

#
# move
#
elif sys.argv[1] == 'move' or sys.argv[1] == 'm':
    if len(sys.argv) == 2:
        imgpath = "*.fit"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    imglist = []
    for img in imgfiles:
        hdul = fits.open(img)
        resol = str(hdul[0].header['NAXIS1']) + 'x' + str(hdul[0].header['NAXIS2'])
        hdul.close()
        if not os.path.exists(resol):
            print ('mkdir ' + resol)
            os.mkdir(resol)
        target_file = resol+'\\'+img
        if not os.path.exists(target_file):
            os.rename(img, target_file)
            print ('move ' + img + ' to ' + resol)
        else:
            print ('file ' + img + ' already exists in ' + resol)

#
# header
#
elif sys.argv[1] == 'header' or sys.argv[1] == 'h':
    if len(sys.argv) == 2:
        imgpath = "*.fit"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    imglist = []
    for img in imgfiles:
        hdul = fits.open(img)
        k = list(hdul[0].header.keys())
        for x in k:
            print (x + '=' + str(hdul[0].header[x]))

#
# coordinates
#
elif sys.argv[1] == 'coordinates' or sys.argv[1] == 'c':
    if len(sys.argv) == 2:
        globdir = "."
    else:
        globdir = sys.argv[2]
    rootdirs = glob.glob(globdir)
    coords = []
    for rootdir in rootdirs:
        if os.path.isdir(rootdir):
            file_list = [f for f in iglob(os.path.join(rootdir, '**/*.fit'), recursive=True) if os.path.isfile(f)]
            for file in file_list:
                fname = os.path.basename(file)
                if fname[0:1].isdigit():
                    coords.append(fname[0:13])
    coords = list(set(coords))
    for c in coords:
        if c[6:7] == 'm':
            sign = '-'
        else:
            sign = ''
        print(c[0:6] + ' ' + sign + c[7:] + ',', end='')

#
# summary
#
elif sys.argv[1] == 'summary' or sys.argv[1] == 's':
    if len(sys.argv) == 2:
        imgpath = "*.fit*"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    datetimelist = []
    datelist = []
    telescop = []
    instrume = []
    location = []
    filter = []
    exptime = []
    datefilters = []
    totalcnt = 0
    for img in imgfiles:
        hdul = fits.open(img)
        # collect all different dates
        datetimeobs = str(hdul[0].header['DATE-OBS'][0:19])
        dateobs = str(hdul[0].header['DATE-OBS'][0:10])
        datetimeobsindex = find_in_list(datetimelist, datetimeobs)
        if datetimeobsindex == -1:
            datetimelist.append(datetimeobs)
        # collect telecopes and instruments
        try:
            val = str(hdul[0].header['TELESCOP'])
        except:
            val = 'TELESCOP unknown'
        index = find_in_list(telescop, val)
        if index == -1:
            index = len(telescop)
            telescop.append(val)
            try:
                instrume.append(str(hdul[0].header['INSTRUME']))
            except:
                instrume.append('INSTRUME unknown')
            print ("Add telescope " + telescop[index] + " and instrument " + instrume[index])
        # collect filters
        filterval = str(hdul[0].header['FILTER'])
        index = find_in_list(filter, filterval)
        if index == -1:
            index = len(filter)
            filter.append(filterval)
            exptime.append(Exptime())
            print ("Add filter " + filter[index])
        # collect exposure time for each filter
        # different exposure times are collected separately
        exptimeval = int(float(str(hdul[0].header['EXPTIME'])))
        et = exptime[index]
        index2 = find_in_list(et.exp, exptimeval)
        if index2 == -1:
            index2 = len(et.exp)
            et.exp.append(exptimeval)
            et.cnt.append(0)
            print ("Add exptime " + str(exptimeval) + " for filter " + filter[index])
        et.cnt[index2] = et.cnt[index2] + 1
        # collect exptime for each date and filter
        dateobsindex = find_in_list(datelist, dateobs)
        if dateobsindex == -1:
            datelist.append(dateobs)
            datefilters.append([])
        # find filter in datefilters
        df = datefilters[dateobsindex]
        index = 0
        for x in df:
            if x.filter == filterval:
                break
            index = index + 1
        if index == len(df):
            df.append(Datefilters())
            df[index].filter = filterval
            df[index].exptime = []
            df[index].cnt = []
        # record exposure time for this filter
        index2 = find_in_list(df[index].exptime, exptimeval)
        if index2 == -1:
            index2 = len(df[index].exptime)
            df[index].exptime.append(exptimeval)
            df[index].cnt.append(0)
        df[index].cnt[index2] = df[index].cnt[index2] + 1
        hdul.close()
        totalcnt = totalcnt + 1
    print ("Dates:")
    datetimelist.sort()
    datelist = []
    index = 0
    for x in datetimelist:
        dt = datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
        if index == 0:
            datelist.append(x[0:10])
        else:
            diff_dt = dt - prev_dt
            diff_secs = diff_dt.total_seconds()
            if diff_secs > 12 * 60 * 60 and find_in_list(datelist, x[0:10]) == -1:
                datelist.append(x[0:10])
        prev_dt = dt
        index = index + 1
    index = 0
    for x in datelist:
        print (x)
        index = index + 1
    print ("--")
    print ("Filter exposure times for each day:")
    index = 0
    for x in datelist:
        print (x + ' ', end='')
        df = datefilters[index]
        index2 = 0
        for y in df:
            print (y.filter + ' ', end='')
            index3 = 0
            for z in y.exptime:
                print (str(y.cnt[index3]) + 'x' + str(z) + 's ', end='')
                index3 = index3 + 1
            index2 = index2 + 1
        print ('')
        index = index + 1
    print ("--")
    # Astrobin .csv format output
    index = 0
    print ("date,filter,number,duration")
    for x in datelist:
        df = datefilters[index]
        index2 = 0
        for y in df:
            index3 = 0
            for z in y.exptime:
                print (x + ',' + str(filter_id(y.filter)) + ',' + str(y.cnt[index3]) + ',' + str(z))
                index3 = index3 + 1
            index2 = index2 + 1
        index = index + 1
    print ("--")
    print ("Data from Telescope Live OneClick Observations")
    print ("Processing: PixInsight (with AutoIntegrate.js), Photoshop, RC Astro tools")
    if len(datelist) == 1:
        print ("Images are taken at " + datelist[0])
    else:
        print ("Images are taken at " + str(index) + " different nights between " +
                datelist[0] + " and " + datelist[len(datelist)-1])
    print ("Telescope:")
    index = 0
    for x in telescop:
        print(get_telescope(x))
        index = index + 1
    print ("Camera:")
    index = 0
    for x in telescop:
        print(instrume[index])
        index = index + 1
    print ("Filters:")
    index = 0
    totalexptime = 0
    for x in filter:
        et = exptime[index]
        index2 = 0
        filterexptime = 0
        filtercnt = 0
        for y in et.exp:
            subexptime = et.cnt[index2] * y
            filtercnt = filtercnt + et.cnt[index2]
            filterexptime = filterexptime + subexptime
            totalexptime = totalexptime + subexptime
            print(x + ' ' + str(et.cnt[index2]) + ' x ' + str(y) + 's (' + secs_to_time(subexptime) + ')')
            index2 = index2 + 1
        if len(et.exp) > 1:
            print(x + ' ' + str(filtercnt) + ' images ' + secs_to_time(filterexptime))
        index = index + 1
    print ("Total " + str(totalcnt) + " images, exposure time " + secs_to_time(totalexptime))
    print ("--")
    print (str(int(totalexptime/300)) + "x300s, " + str(int(totalexptime/600)) + "x600s")

#
# unprocessed
#
elif sys.argv[1] == 'unprocessed' or sys.argv[1] == 'u':
    if len(sys.argv) == 2:
        globdir = "."
        startpos = 2
    else:
        globdir = sys.argv[2]
        startpos = 0
    rootdirs = glob.glob(globdir + '/*')
    nofits_list = []
    nojpg_someprocessing_list = []
    nojpg_list = []
    jpg_list = []
    for rootdir in rootdirs:
        if os.path.isdir(rootdir):
            fits = glob.glob(rootdir + "/*.fit*")
            if len(fits) == 0:
                nofits_list.append(rootdir)
                continue
            jpgs = glob.glob(rootdir + "/*.jpg")
            if len(jpgs) == 0:
                processed = glob.glob(rootdir + "/AutoProcessed")
                if len(processed) > 0:
                    nojpg_someprocessing_list.append(rootdir)
                    continue
                processed = glob.glob(rootdir + "/*.tif*")
                if len(processed) > 0:
                    nojpg_someprocessing_list.append(rootdir)
                    continue
                processed = glob.glob(rootdir + "/*.xisf")
                if len(processed) > 0:
                    nojpg_someprocessing_list.append(rootdir)
                    continue
                nojpg_list.append(rootdir)
            else:
                jpg_list.append(rootdir)
    print("JPG files:")
    for x in jpg_list:
        print ('  ' + x[startpos:])
    print("No FITS files:")
    for x in nofits_list:
        print ('  ' + x[startpos:])
    print("No JPG files but some processing done:")
    for x in nojpg_someprocessing_list:
        print ('  ' + x[startpos:])
    print("No JPG files or processing:")
    for x in nojpg_list:
        print ('  ' + x[startpos:])

#
# decompress fits files
#
elif sys.argv[1] == 'decompress' or sys.argv[1] == 'd':
    if len(sys.argv) == 2:
        imgpath = "*.fit*"
    else:
        imgpath = sys.argv[2]
    imgfiles = glob.glob(imgpath)
    for img in imgfiles:
        # skip if image name starts with dc_
        if img[0:3] == 'dc_':
            continue
        # check if file alread exists
        if os.path.isfile('dc_'+ img):
            print ("File " + 'dc_'+ img + " already exists")
        else:
            print ("Open " + img)
            hdul = fits.open(img)
            # Extract the compressed data
            compressed_data = hdul[1].data
            # Decompress the data
            decompressed_data = fits.CompImageHDU(compressed_data).data
            # Save the decompressed data to a new FITS file
            hdu = fits.PrimaryHDU(decompressed_data)
            hdu.writeto('dc_'+ img)
            hdul.close()
            print ("Decompressed to " + 'dc_'+ img)

else:
    print ("Bad argument " + str(sys.argv[1]))
    print ("Usage: python fitspy.py {list|move|header|coordinates} [file]")
    sys.exit()
