
''' 
dracscan.py is a simple program for gathering DRAC version, DRAC class and
host name from a list of Dell DRAC devices.  It reads a list of IP address
from a file named "dracscan_input" in the present working directory.  It
prints diagnostic information on stdout and also creates a CSV file named
"dracscan.csv" also in PWD.
'''

import csv
import simplejson
import logging
import sys
import ssl
import httplib
import re

class DracScanResultError:
	def __init__(self, addr, origExc):	
		self.addr = addr
		self.origExc = origExc
	
	@property
	def success(self):
		return False
	
	def __str__(self):
		return '%s: Error interrogating: %s' % (self.addr, self.origExc)

class DracScanResult:
	def __init__(self, addr, version, prodClass, hostname):
		self.addr = addr
		self.version = version
		self.prodClass = prodClass
		self.hostname = hostname

	@property
	def success(self):
		return True

	@property
	def versionPretty(self):
		if self.version != None:
			return self.version
		else:
			return '?'

	@property
	def prodClassPretty(self):
		if self.prodClass != None:
			return self.prodClass
		else:
			return '?'

	@property
	def hostnamePretty(self):
		return self.hostname if self.hostname!=None else '?'
	
	def __str__(self):
		return '%s: DRAC version %s, class %s, hostname %s' % (
			self.addr, self.version, self.prodClass, self.hostname)

class DracScanResultUnknown:
	def __init__(self, addr):
		self.addr = addr
	
	def __str__(self):
		return '%s: Unknown DRAC' % self.addr

def checkLogin(addr):
	'''Try to determine the DRAC version from GET /login.html.'''
	headers = {
		'Host': addr,
		'Accept-Encoding': 'gzip, deflate'
	}
	c = httplib.HTTPSConnection(addr, timeout=5, context=ssl._create_unverified_context())
	c.request('GET', '/login.html', None, headers)
	r = c.getresponse()
	if r.status!=200:
		raise Exception('status %s in GET /login.html on %s' % (r.status, addr))
	content = r.read()
	if '<title>Integrated Dell Remote Access Controller 6 - Enterprise</title>' in content:
		return (6, 'ent')
	else:
		return (None,None)

def getAimGetProp(addr):
	'''Obtain the attached server's hostname from GET /session.'''
	headers = {
		'Host': addr
	}
	c = httplib.HTTPSConnection(addr, timeout=5, context=ssl._create_unverified_context())
	# All of this stuff MUST be in the query string
	# even though we aren't interested. Without it the DRAC returns 
	# a 302 to /start.html. I have no idea why.
	uri = '/session?aimGetProp=hostname,gui_str_title_bar,OEMHostName,fwVersion,sysDesc'
	c.request('GET', uri, None, headers)
	r = c.getresponse()
	if r.status!=200:
		logging.debug('%s: GET %s returned %s status.' % (
			addr, uri, r.status
		))
		return None
	body = r.read()
	try:
		json = simplejson.loads(body)
	except Exception, e:
		logging.debug('%s: GET %s returned unparseable JSON: %s. reason: %s' % (
			addr, uri, repr(body), e
		))
		return None

	if json.has_key('aimGetProp') and json['aimGetProp'].has_key('OEMHostName'):
		return json['aimGetProp']['OEMHostName']
	else:
		logging.debug('%s: GET /session?aimGetProp=hostname,gui_str_title_bar,OEMHostName returned JSON with no aimGetProp.OEMHostName attribute:' % (
			addr, repr(body)
		))
		return None

def checkProdClassName(addr):
	'''Obtain the DRAC class (enterprise, express, etc) from GET /data.'''

	headers = {
		'Host': addr
	}

	c = httplib.HTTPSConnection(addr, timeout=5, context=ssl._create_unverified_context())
	c.request('GET', '/data?get=prodClassName', None, headers)
	r = c.getresponse()
	
	if r.status!=200:
		logging.debug('%s: GET /data?get=prodClassName returned status %s.' % (
			addr, r.status
		))
		return None
	
	body = r.read()
	if body=='<root><prodClassName>Enterprise</prodClassName>\n<status>ok</status>\n</root>\n':
		return 'ent'
	elif body=='<root><prodClassName>Express</prodClassName>\n<status>ok</status>\n</root>\n':
		return 'exp'
	elif body=='<root><prodClassName>Basic Management</prodClassName>\n<status>ok</status>\n</root>\n':
		return 'basic'
	else:
		logging.debug('%s: GET /data?get=prodClassName return unexpected string %s.' % (
			addr, repr(body)
		))
		return None

def getInfo(addr):
	(version, prodClass) = checkLogin(addr)
	if version!=None:
		# probably pre version 7
		return DracScanResult(addr, version, prodClass, None)

	hostname = getAimGetProp(addr)
	
	prodClass = checkProdClassName(addr)
	if prodClass!=None:
		return DracScanResult(addr, 7, prodClass, hostname)
	
	return DracScanUnknown(addr)


def getInfoOuter(addr):
	try:	
		return getInfo(addr)
	except Exception, e:
		return DracScanResultError(addr, e)

def main():
	logging.basicConfig(level=logging.DEBUG)
	logging.debug('Starting')

	csvout = csv.writer(open('dracscan.csv','wb'))

	for line in open('dracscan_input'):
		addr = line.strip()
		result = getInfoOuter(addr)
		print result
		if result.success:
			csvout.writerow([
				result.addr,
				result.versionPretty,
				result.prodClassPretty,
				result.hostnamePretty
			])

if __name__ == '__main__':
	main()

	