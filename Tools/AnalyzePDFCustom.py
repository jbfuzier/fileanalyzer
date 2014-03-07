import os
from Tools.pdfid import PDFiD, PDFiD2String, PDFiD2JSON
import json
import re
import logging
from decimal import Decimal
import yara


class AnalyzePDF():
    def __init__(self, path, toolpath=""):
        self.toolpath=toolpath
        self.path = path
        self.anomalies = []
        self.yscore = []
        self.extra_text = {}

    @property
    def anomalies_string(self):
        txt = ""
        for a in self.anomalies:
            if a == "header":
                txt += "Invalid PDF version number\n"
            elif a == "js":
                txt += "/!\\ JavaScript code detected inside the PDF\n"
            elif a == "mucho_javascript":
                txt += "/!\\ LOT of JavaScript code detected inside the PDF\n"
            elif a == "acroform":
                txt += "(?) This PDF document contains AcroForm objects. AcroForm Objects can specify and launch scripts or actions, that is why they are often abused by attackers.\n"
            elif a == "aa":
                txt += "/!\\ This PDF document contains a AA object - additional actions dictionary defining a fields behavior in response to trigger events\n"
            elif a == "oa":
                txt += "/!\\ This PDF document contains openactions\n"
            elif a == "launch":
                txt += "/!\\ This PDF document contains Launch objects\n"
            elif a == "embed":
                txt += "This PDF document contains embeded objects\n"
            elif a == "entropy":
                txt += self.extra_text["entropy"] + "\n"
            elif a == "page":
                txt += self.extra_text["page"] + "\n"
        return txt

    def analyze(self):
        self._pdfid()
        self._yarascan()
        return self._eval()
        
    def _eval(self):
        """
        Evaluate the discovered contents of the PDF and assign a severity rating
        based on the conditions configured below.

        Rating system: 0 (benign), >=2 (sketchy), >=3 (medium), >=5 (high)
        """
        ytotal = sum(self.yscore)
        logging.debug("[-] Total YARA score.......: %s" % ytotal)
        sev = 0

        # Below are various combinations used to add some intelligence and help evaluate if a file is malicious or benign.
        # This is where you can add your own thoughts or modify existing checks.

        # HIGH
        if "page" in self.anomalies and "launch" in self.anomalies and "js" in self.anomalies: sev = 5
        elif "page" in self.anomalies and "xref" in self.anomalies: sev += 5
        elif "page" in self.anomalies and "aa" in self.anomalies and "js" in self.anomalies: sev += 5
        elif "page" in self.anomalies and "oa" in self.anomalies and "js" in self.anomalies: sev += 5

        # MEDIUM
        if "header" in self.anomalies and "xref" in self.anomalies: sev += 3
        elif "header" in self.anomalies and "js" in self.anomalies and "page" in self.anomalies: sev += 3
        elif "header" in self.anomalies and "launch" in self.anomalies and "page" in self.anomalies: sev += 3
        elif "header" in self.anomalies and "aa" in self.anomalies and "page" in self.anomalies: sev += 3

        if "page" in self.anomalies and "mucho_javascript" in self.anomalies: sev += 3
        elif "page" in self.anomalies and "acroform" in self.anomalies and "embed" in self.anomalies: sev += 3
        elif "page" in self.anomalies and "acroform" in self.anomalies and "js" in self.anomalies: sev += 3

        if "entropy" in self.anomalies and "page" in self.anomalies: sev += 3
        elif "entropy" in self.anomalies and "aa" in self.anomalies: sev += 3
        elif "entropy" in self.anomalies and "oa" in self.anomalies: sev += 3
        elif "entropy" in self.anomalies and "js" in self.anomalies: sev += 3

        if "oa" in self.anomalies and "js" in self.anomalies: sev += 3
        if "aa" in self.anomalies and "mucho_javascript" in self.anomalies: sev += 3

        # Heuristically sketchy
        if "page" in self.anomalies and "js" in self.anomalies: sev += 2
        if "sketchy" in self.anomalies and "page" in self.anomalies: sev += 2
        elif "sketchy" in self.anomalies and "aa" in self.anomalies: sev += 2
        elif "sketchy" in self.anomalies and "oa" in self.anomalies: sev += 2
        elif "sketchy" in self.anomalies and "launch" in  self.anomalies: sev += 2
        elif "sketchy" in self.anomalies and "eof" in self.anomalies: sev += 1

        if "page" in self.anomalies and "aa" in self.anomalies: sev += 1
        if "page" in self.anomalies and "header" in self.anomalies: sev += 1
        if "header" in self.anomalies and "embed" in self.anomalies: sev += 1

        logging.debug("[-] Total severity score...: %s" % sev)
        sev = (ytotal + sev)
        logging.debug("[-] Overall score..........: %s" % sev)

        if sev >= 5: verdict = "[!] HIGH probability of being malicious"
        elif sev >= 3: verdict = "[!] MEDIUM probability of being malicious"
        elif sev >= 2: verdict = "[!] Heuristically sketchy"
        elif sev >= 0: verdict = "[-] Scanning didn't determine anything warranting suspicion"
        logging.debug("Verdict : %s"%(verdict))
        return (sev, verdict)

    def fileID(self):
        """
        Generally the PDF header will be within the first (4) bytes but since the PDF specs say it 
        can be within the first (1024) bytes I'd rather check for atleast (1) instance 
        of it within that large range.  This limits the chance of the PDF using a header 
        evasion trick and then won't end up getting analyzed.  This evasion behavior could later 
        be detected with a YARA rule.
        """
        f = open(self.path,'rb')
        s = f.read(1024)
        if '\x25\x50\x44\x46' in s:
            print "\n" + trailer
            print "[+] Analyzing: %s" % pdf
            print filler
            print "[-] Sha256: %s" % sha256(pdf)
            info(pdf)
        f.close()
    
    def q(self, s):
        quote = "\""
        s = quote + s + quote
        return s
    
    # def _pdfinfo(self):
    #     pdf = self.path
    #     command = os.path.join(self.toolpath,"pdfinfo ") + self.q(pdf)
    #     try:
    #         p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    #         #for line in p.stdout:
    #         #    if re.match('Pages:\s+(0|1)$', line):
    #         #        counter.append("pages")
    #         #         print "[-] (1) page PDF"
    #         for line in p.stderr:
    #             if re.search('Unterminated hex string|Loop in Pages tree|Illegal digit in hex char in name', line):
    #                 counter.append("sketchy")
    #                 print "[-] Sketchyness detected"
    #             elif re.search('Unexpected end of file in flate stream|End of file inside array', line):
    #                 counter.append("eof")
    #                 print "[-] EoF problem"
    #             elif re.search('Couldn\'t find trailer dictionary', line):
    #                 counter.append("trailer")
    #             elif re.search('Invalid XRef entry|No valid XRef size in trailer|Invalid XRef entry|Couldn\'t read xref table', line):
    #                 counter.append("xref")
    #                 print "[-] Invalid XREF"
    #                 break
    #     except Exception, msg:
    #         print "[!] pdfinfo error: %s" % msg
    #         pass

    def _getKeywordCountFromPdfidDict(self, keyword, pdfid_dict):
        kw_list = pdfid_dict['keywords']['keyword']
        try:
            result = [kw_value for kw_value in kw_list if kw_value['name'] == keyword][0]
            return result['count']
        except:
            return None

    def _pdfid(self):
        pdf = self.path
        try:
            # (dir, allNames, extraData, disarm, force), force)
            pdfid_rawxmlresult = PDFiD(file=pdf, allNames=True, extraData=True, disarm=False, force=True)
            extra = True
        except Exception:
            # I've observed some files raising errors with the 'extraData' switch
            pdfid_rawxmlresult = PDFiD(file=pdf, allNames=True, extraData=False, disarm=False, force=True)
            print "[!] PDFiD couldn\'t parse extra data"
            extra = False

        pdfid_json = PDFiD2JSON(pdfid_rawxmlresult, False)
        pdfid_str = PDFiD2String(pdfid_rawxmlresult, False)
        pdfid_dict = json.loads(pdfid_json)[0]['pdfid']

        self.pdfid_json = pdfid_json
        self.pdfid_str = pdfid_str
        self.pdfid_dict = pdfid_dict

        header = pdfid_dict['header']
        is_header_valid = re.match('%PDF-1\.\d', header) is not None
        if not is_header_valid:
            logging.debug("[-] Invalid version number : \"%s\"" % header)
            self.anomalies.append('header')
        page = self._getKeywordCountFromPdfidDict('/Page', pdfid_dict)
        pages = self._getKeywordCountFromPdfidDict('/Pages', pdfid_dict)
        page_counter = []
        if page is not None:
            page_counter.append(page)
        if pages is not None:
            page_counter.append(pages)


        js = self._getKeywordCountFromPdfidDict('/JS', pdfid_dict)
        if js is not None and js != 0:
            self.anomalies.append('js')
            logging.debug("JS count %s" % js)
            if js > 1:
                self.anomalies.append('mucho_javascript')

        af = self._getKeywordCountFromPdfidDict('/AcroForm', pdfid_dict)
        if af is not None and af != 0:
            self.anomalies.append('acroform')
            logging.debug("acroform count %s" % af)

        aa = self._getKeywordCountFromPdfidDict('/AA', pdfid_dict)
        if aa is not None and aa != 0:
            self.anomalies.append('aa')
            logging.debug("Additional Action count %s" % aa)

        oa = self._getKeywordCountFromPdfidDict('/OpenAction', pdfid_dict)
        if oa is not None and oa != 0:
            self.anomalies.append('oa')
            logging.debug("OpenAction count %s" % oa)

        launch = self._getKeywordCountFromPdfidDict('/Launch', pdfid_dict)
        if launch is not None and launch != 0:
            self.anomalies.append('launch')
            logging.debug("Launch count %s" % launch)

        ef = self._getKeywordCountFromPdfidDict('/EmbeddedFiles', pdfid_dict)
        if ef is not None and ef != 0:
            self.anomalies.append('embed')
            logging.debug("Embed count %s" % ef)

        tentropy = pdfid_dict['totalEntropy']
        ientropy = pdfid_dict['streamEntropy']
        oentropy = pdfid_dict['nonStreamEntropy']


        """
        Entropy levels:
        0 = orderly, 8 = random
        ASCII text file = ~2/4
        ZIP archive = ~ 7/8
        PDF Malicious
                - total   : 6.3
                - inside  : 6.6
                - outside : 4.9
        PDF Benign
                - total   : 6.7
                - inside  : 7.2
                - outside : 5.1
        Determine if Total Entropy & Entropy Inside Stream are significantly different than Entropy Outside Streams -> i.e. might indicate a payload w/ long, uncompressed NOP-sled
        ref = http://blog.didierstevens.com/2009/05/14/malformed-pdf-documents
        """		
        if extra is True:
            te_long = Decimal(tentropy)
            te_short = Decimal(tentropy[0:3])
            ie_long = Decimal(ientropy)	
            ie_short = Decimal(ientropy[0:3])	
            oe_long = Decimal(oentropy)	
            oe_short = Decimal(oentropy[0:3])	
            ent = (te_short + ie_short) / 2
            # I know 'entropy' might get added twice to the counter (doesn't matter) but I wanted to separate these to be alerted on them individually
            togo = (8 - oe_long) # Don't want to apply this if it goes over the max of 8
            if togo > 2:
                if oe_long + 2 > te_long:
                    self.anomalies.append("entropy")
                    txt = "Entropy of outside stream is questionable: Outside (%s) +2 (%s) > Total (%s)"% (oe_long,oe_long +2,te_long)
                    logging.debug(txt)
                    self.extra_text['entropy'] = txt
            elif oe_long > te_long:
                self.anomalies.append("entropy")
                txt = "Entropy of outside stream is questionable: Outside (%s) > Total (%s)" % (oe_long, te_long)
                logging.debug(txt)
                self.extra_text['entropy'] = txt
            if str(te_short) <= "2.0" or str(ie_short) <= "2.0":
                self.anomalies.append("entropy")
                txt = "LOW entropy detected: Total (%s) or Inside (%s) <= 2.0" % (te_short, ie_short)
                logging.debug(txt)
                if 'entropy' in self.extra_text:
                    txt += " %s" % self.extra_text['entropy']
                self.extra_text['entropy'] = txt


        # Process the /Page(s) results here just to make sure they were both read
        if (page_counter[0] == 0) and (page_counter[1] == 0):
            self.anomalies.append("page")
            txt = "Page count suspicious: Both /Page (%s) and /Pages (%s) = 0" % (page_counter[0],page_counter[1])
            logging.debug(txt)
            self.extra_text['page'] = txt
        elif (page_counter[0] == 0) and (page_counter[1] != 0):
            self.anomalies.append("page")
            txt = "Page count suspicious, no individual pages defined: /Page = (%s) , /Pages = (%s)" % (page_counter[0],page_counter[1])
            logging.debug(txt)
            self.extra_text['page'] = txt
        elif page_counter[0] == 1:
            self.anomalies.append("page")
            txt = " (1) page PDF"
            logging.debug(txt)
            self.extra_text['page'] = txt
            
    def __yara_init(self):
        rules = os.path.join(self.toolpath, "pdf_rules.yara")
        try:
            self.yara_rules = yara.compile(rules)
        except Exception, msg:
            logging.error("[!] YARA compile error: %s" % msg)

    def _yarascan(self):
        pdf = self.path
        self.__yara_init()
        try:
            ymatch = self.yara_rules.match(pdf)

            if len(ymatch):
                txt = ("[-] YARA hit(s): %s" % ymatch)
                logging.debug(txt)
                self.extra_text['yara'] = txt
                for rule in ymatch:
                    meta = rule.meta
                    for key, value in meta.iteritems():
                        # If the YARA rule has a weight in it's metadata then parse that for later calculation
                        if "weight" in key:
                            self.yscore.append(value)
        except Exception, msg:
            logging.error(msg)



if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    a = AnalyzePDF("Vincent Ho-tin-noe  Disclosure.pdf")
    a.analyze()