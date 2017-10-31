#!/usr/bin/python
# -*- coding: utf-8 -*-
import StringIO
import subprocess
import os
import time
from datetime import datetime
from PIL import Image

# Motion detection indstillinger:
# Threshold (Hvor meget skal en enkelt pixel ændres før den markeres som "changed"). Specielt i lavt lys er der en del støj.
# Sensitivity (Hvor mange pixels skal ialt være ændret, før bevægelse er detekteret og et billede tages)
# ForceCapture (Hvis True vil et billede tages hvert forceCaptureTime sekund uanset om der er detekteret bevægelse)

threshold = 20
sensitivity = 40
forceCapture = False
forceCaptureTime = 3600 # En gang i timen

# File settings
saveWidth = 3280
saveHeight = 2464
diskSpaceToReserve = 100 * 1024 * 1024 # Mindst 100 MB skal være fri på disk.

# Tag et billede i lav opløsning, til detektion af bevægelse.
# Billedet gemmes i RAM for at undgå slid på flashdisken.
def captureTestImage():
    command = "raspistill -w %s -h %s -t 5 -e bmp -o -" % (100, 75)
    imageData = StringIO.StringIO()
    imageData.write(subprocess.check_output(command, shell=True))
    imageData.seek(0)
    im = Image.open(imageData)
    buffer = im.load()
    imageData.close()
    return im, buffer

# Gem billede i fuld opløsning på disk
def saveImage(width, height, diskSpaceToReserve):
    keepDiskSpaceFree(diskSpaceToReserve)
    time = datetime.now()
    filename = "capture-%04d%02d%02d-%02d%02d%02d.jpg" % (time.year, time.month, time.day, time.hour, time.minute, time.second)
    subprocess.call("raspistill -w %s -h %s -t 5 -e jpg -q 15 -o %s" % (saveWidth, saveHeight, filename), shell=True)
    print "Billede %s er gemt på disk" % filename

# Funktion til at undgå at disken bliver fyldt. Sletter ældste billeder.
def keepDiskSpaceFree(bytesToReserve):
    if (getFreeSpace() < bytesToReserve):
        for filename in sorted(os.listdir(".")):
            if filename.startswith("capture") and filename.endswith(".jpg"):
                os.remove(filename)
                print "Deleted %s to avoid filling disk" % filename
                if (getFreeSpace() > bytesToReserve):
                    return
                
# Find ledig diskplads
def getFreeSpace():
    st = os.statvfs(".")
    du = st.f_bavail * st.f_frsize
    return du
            
# Tag første billede.
image1, buffer1 = captureTestImage()
        
# Reset last capture time
lastCapture = time.time()
        
while (True):
            
    # Tag billede til sammenligning
    image2, buffer2 = captureTestImage()
            
    # tæl hvor mange pixels der er ændret ved at loope gennem alle pixels i billedet
    changedPixels = 0
    for x in xrange(0, 100):
        for y in xrange(0, 75):
            # Vi nøjes med at tjekke den grønne kanal.
            pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
            if pixdiff > threshold:
                changedPixels += 1
                        
    # Er forcecapture True, og er der gået "forceCaptureTime" sekunder, så tag et billede
    if forceCapture:
        if time.time() - lastCapture > forceCaptureTime:
            changedPixels = sensitivity + 1 # Dette beytyder at bevægelse detekteret trigges
                                
    # Hvis der er detekteret en bevægelse, så tag et billede
    if changedPixels > sensitivity:
        print "Bevægelse detekteret, tager billede!"
        lastCapture = time.time()
        saveImage(saveWidth, saveHeight, diskSpaceToReserve)
                                    
    # Swap buffere til sammenligning
    image1 = image2
    buffer1 = buffer2


