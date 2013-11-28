import os
import math
import logging
import Image
import ImageDraw
import ImageFont
from math import pow, ceil, log, sqrt

class MapFile():
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        
    def writeimg(self,in_file, out_file):
        file = open(in_file, 'rb')
        buffer = file.read(-1)
        buffer_len = len(buffer)
        n = sqrt(buffer_len)
        size = int(pow(2, ceil(log(n, 2))))  # Next square with enough pix in it
        usefull_lines = int(ceil(float(buffer_len)/float(size)))
        padding = size * usefull_lines - len(buffer)
        logging.debug("file is %s bytes long, image size %s (%s), usefull_lines : %s (%s), padding : %s" % (buffer_len, size,size*size, usefull_lines,usefull_lines*size, padding))
        buffer += " " * padding
        im = Image.fromstring("L",(size,usefull_lines),buffer,"raw")
        #im = im.convert("RGB")
        #print im
        #for p in range(padding):
        #    x = size - p -1
            #print "%s %s"%(x,usefull_lines-1)
        #    im.putpixel((x, usefull_lines-1),(0,255,0))
        if size > 1024:
            logging.warning("Image is too large, downsampling img...")
            im.thumbnail((1024,usefull_lines))
        im.save(out_file)

class Entropy():
    def __init__(self, file):
        self.file = file
        self.occurences = None

    def meanstdv(self, x):
        from math import sqrt
        n, mean, std = len(x), 0, 0
        for a in x:
            mean = mean + a
        mean = mean / float(n)
        for a in x:
            std = std + (a - mean)**2
        std = sqrt(std / float(n-1))
        return mean, std

    def writeimg(self, outfile):
        img_size = (800,400) #  765 minimum
        im = Image.new("RGB", img_size, "white")
        draw = ImageDraw.Draw(im)
        max_value = max(self.occurences.values())
        amp_factor = img_size[1] / max_value
        for i, o in enumerate(self.occurences):
            p1 = (i * 3, img_size[1] - 1)
            p2 = (i * 3, 400 - self.occurences[o] * amp_factor)
            # print "%s %s"%(p1,p2)
            draw.line([p1, p2], fill="black")
        # font = ImageFont.truetype('Roboto-Thin.ttf',20)
        txt = u'Entropy = %s  -  Mean = %s  -  MaxDev = %s  - StdDev =  %s  - %s' % (self.entropy, self.mean, self.max_dev, self.stdv , self.FileTypeText())
        draw.text((10, 10), txt, fill="black")
        im.save(outfile)
        
    def analyze(self):
        file = self.file
        occurences = {}
        with open(file, 'rb') as f:
            while True:
                buffer = f.read(32 * 1024 * 1024)
                if not buffer:
                    break
                for c in buffer:
                    b = ord(c)
                    if b not in occurences:
                        occurences[b] = 1
                    else:
                        occurences[b] += 1
        sum_o = sum(occurences.values())
        occurences_rel = {}
        for i in range(256):
            if i not in occurences:
                occurences[i] = 0
            occurences_rel[i] = occurences[i] * 1.0 / sum_o
#            print "%i|" % i + "-" * int(occurences_rel[i] * 1000)
        self.occurences = occurences_rel
        entropy = 0
        for i in range(256):
            Pi = occurences_rel[i]
            if Pi != 0:
                entropy += Pi * math.log(1 / Pi, 2)
        mean, stdv = self.meanstdv(occurences_rel.values())
        max_dev = max([abs(occ - mean) for occ in occurences_rel.values()])
        self.entropy = entropy
        self.mean = mean * 100
        self.max_dev = max_dev * 100
        self.stdv = stdv * 100
        return entropy, mean * 100, stdv * 100, max_dev * 100

    def FileTypeText(self):
        (r, n, n ,n) = self.FileType()
        if  r == -1:
            return "Too small to tell"
        elif r == 1:
            return "Not encrypted and not compressed"
        elif r == 2:
            return "Compressed or packed file"
        elif r == 3:
            return "?Encryped file?"
        elif r == 4:
            return "Encryped file"
    
    def FileType(self):
        """
        -2 -> File not readable
        -1 -> File too small
        1 -> Not compressed or encrypted
        2 -> Compressed
        3 -> Suspicious encrypted or highly compressed
        4 -> Encrypted
        """
        file = self.file
        f_size = os.path.getsize(file)
        if f_size < 4 *1024:
            return (-1, 0, 0, 0)
        # ent_c = Entropy()
        entropy, mean, stdv, maxdev = self.entropy, self.mean, self.stdv, self.max_dev
        if entropy < 5:
            logging.debug("Entropy %s - seems to be a text file" % entropy)
            return (1, entropy, mean, stdv)
        elif entropy < 7.7:
            logging.debug("Entropy %s - seems to be an uncompressed binary file" % entropy)
            return (1, entropy, mean, stdv)
        elif entropy < 7.99:
            logging.debug("Entropy %s - seems to be a compressed file (or encrypted with a weak/faulty encryption or packed)" % entropy)
            return (2, entropy, mean, stdv)
        else:
            logging.debug("Entropy %s - seems to be an encrypted or well compressed or packed file" % entropy)
            delta_m = 0.02
            mean_test = False
            stdv_test = False
            maxdev_test = False
            if (mean < (100.0/255 + delta_m)) and (mean > (100.0/255 - delta_m)):
                logging.debug("    mean seems to indicate encrypted file (%s)" % mean)
                mean_test = True
            if stdv < 0.05:
                logging.debug("    stdv seems to indicate encrypted file (%s)" % stdv)
                stdv_test = True
            if maxdev < 0.02: #0.02% deviation indicated no encryption
                logging.debug("    maxdev seems to indicate encrypted file (%s)" % stdv)
                maxdev_test = True
            if mean_test and stdv_test and maxdev_test:
                return (4, entropy, mean, stdv)
            else:
                return (3, entropy, mean, stdv)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    a = Entropy().analyze("D:\\Public\\encrypted.zip")
    b = detectEncrypted().analyze("D:\\Public\\encrypted.zip")
    print b
    for root, dirs, files in os.walk("D:\\Public"):
        for file in files:
            f = os.path.join(root, file)
            print f
            print "    %s %s %s %s" % detectEncrypted().analyze(f)
