#!/usr/bin/python
# coding: utf-8
import mechanize
import cookielib
import sys
import ConfigParser
import base64
import uuid
from hashlib import sha256
from time import strptime

doc=""" 
%prog [report] [output] 
report is the name of the Amp report we want to retrieve. Retrieve from AMP.
Outputfile should include path, will be created if not existing and clobbered if existing
"""
def hash_uid(uname, salt=None):
    if salt is None:
        salt = uuid.uuid4().hex
    hashed_uid = sha256(uname + salt).hexdigest()
    return (hashed_uid)

def verify_password(uid, hashed_uid, salt):
    re_hashed, salt = hash_uid(uid, salt)
    return re_hashed == hashed_uid

def getdate24Time(dateString):
	try:
		datelisted = strptime(dateString.strip('"'),"%m/%d/%Y %I:%M %p")
	except ValueError:
		datelisted = []
	return datelisted

def setupBrowser():
	# Set up a web Browser to login to AMP and download the dataset(s)
	mechBr = mechanize.Browser()
	# Cookie Jar
	cj = cookielib.LWPCookieJar()
	mechBr.set_cookiejar(cj)
	# Browser options
	mechBr.set_handle_equiv(True)
	#mechBr.set_handle_gzip(True)
	mechBr.set_handle_redirect(True)
	mechBr.set_handle_referer(True)
	mechBr.set_handle_robots(False)
	# Follows refresh 0 but not hangs on refresh > 0
	mechBr.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	# Want debugging messages?
	#mechBr.set_debug_http(True)
	#mechBr.set_debug_redirects(True)
	#mechBr.set_debug_responses(True)
	# User-Agent (this is cheating, ok?)
	mechBr.addheaders = [('User-agent', UA)]
	return mechBr
config = ConfigParser.RawConfigParser()# get salt, login deets
config.read('scrapeAmp.cfg')
# Current report ID
reportID=sys.argv[1] 
outputfile = sys.argv[2]
# User agent
UA = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'
#URL = 'https://amp.pomona.edu/nf/csv_export.csv?csv_export_uri=\x2Freport_detail&csv_export_list_namespace=pickled_client_aggregate_data&csv_export_list_args=id\x3D%s' % (reportID)
URL = 'https://amp.pomona.edu/nf/csv_export.csv?csv_export_uri=\x2Freport_detail&csv_export_list_namespace=session_list&csv_export_list_args=id\x3D%s' % (reportID)
UNAME = config.get('Auth','uname')
UPASS = config.get('Auth','pwd')
UNAMESALT = config.get('Auth', 'salt')
newLine=[]
AMPUnameField = 'credential_0'
AMPPassField = 'credential_1'
if __name__ == '__main__':
	# Get a web browser
	br = setupBrowser() 
	# open the  URL given for downloading the CSV. Note: Typically throws a survivable 403 error
	print "Contacting the wireless controller"
	try:
		filer = br.open(URL) # site redirects to a permitted page
	except:
		print 'Controller responding.'
	# That action will result in a form, select it:
	br.select_form(nr=0)
	# fulfill the form:
	br.form[AMPUnameField] = UNAME
	br.form[AMPPassField] = UPASS
	# submit the form:
	print "Downloading the {} report...".format(reportID)
	br.submit()
	#Receive and parse the resulting mess of string data
	ampCSVData = br.response().read().split('\n') #raw csv text
	print "Processing {} logfile lines...".format(len(ampCSVData))
	#output the text to the local file after getting the campus and hashing the username 
	with open (outputfile,'w') as csvOut:
		#step through by line, ignore the first header line
		for line in ampCSVData[1:]:
			pline = line.split(',')
			macid = sha256(pline[0]).hexdigest()
			campus = '-' #default value for invalid data errors
			try:
				#parse apart the username into uname (hashed) and campus
				uname = pline[1].split('@')[0]
				if uname not in ['-','Username']: #hash it
					uname = hash_uid(uname, UNAMESALT) 
					campus = pline[1].split('@')[1] #campus depends on uname
			except IndexError:
				uname = 'ERROR' 
			newLine = [macid,uname,campus]
			try:
				#parse apart the datetime from connectime, field 8					
				dateTimeList = getdate24Time(pline[7])
			except IndexError:
				dateTimeList = [0,0,0,0,0,0,0,0,0]
			for item in pline[2:7]: 
				newLine.append(item)
			for item in dateTimeList:
				newLine.append(str(item))
			for item in pline[8:]:
				newLine.append(item)
			print>>csvOut, ','.join(newLine)

	print "Data retrieved and written to {}. Exiting.".format(outputfile)

