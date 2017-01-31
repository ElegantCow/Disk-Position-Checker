import datetime


def convertTime(time): # takes a string of time as input and converts it into a time obj
    
    dateObj = datetime.datetime.strptime(time, '%j.%H:%M:%S') #%j represents zero padded day of year
    return dateObj 

def extractData(line):
	# input is of the format 2016.315.18:12:52.15/disk_pos/288460800,256409600,288460800
	line = line.split(',') #split the string based on commas
	dateTime_data = line[0] # first element contaisn the datetime and the data 
	data = dateTime_data.split('/')[-1] #last element when split with '/' contains the needed data.
	return data


def findErrors(logFilePath):   # reads the log files return the stow times and the day of the year
	########## Lets declare some index locations specific to the log file###########
	dayStart = 5
	dayEnd = 8
	timestart = 5    # index of the string where time starts (from 0) 5 if including day
	timeend = 16
	disk_pos = []   #array to store stow engage and release times
	disk_posTime = None
	disk_pos = None
	stowed = False   # antenna is not stowed by default
	try:
		logfile = open(logFilePath,'r') # Read the log file
	except IOError:
		print "Cannot open " +logFilePath
	for counter,line in enumerate(logfile):    # for each line
	    	

			
	    	if line[21:29] == 'disk_pos' and len(line) > 30: #look for mention of 7mautostow
			doy = int(line[dayStart:dayEnd]) # note down the day of the year
			disk_posTime =line[timestart:timeend +1]  #if you find it, save the time
			disk_pos = extractData(line)
	    	
	
	logfile.close() # close I/O stream to free up resources
	return disk_posTime, disk_pos, doy #output the array of times and the day of the year

def findScansAffected (sumFilePath,disk_posTime,doyRange,telescopeSlew,station):
	dataStart = 19 # line number in the sum file where scan data starts
	scanStartIndexStart = 39
	scanStartIndexEnd =47
	scanEndIndexStart = 49
	scanEndIndexEnd =57
	slewTime = telescopeSlew  # time it takes the telescope to move in seconds
	stowTimes = []
	stowTimes.append(disk_posTime)	
	scansAffected = []
	prevScanEnd = None
	if station == 'ho':
		scansAffected.append('Error')
	else:

		try:
			sumFile = open(sumFilePath,'r')
		except IOError:
			print "Cannot open " + sumFilePath
		for count, line in enumerate(sumFile):
			if count >dataStart-1:
				#print '1'
				#print line[2:4]
				if line[1:4] in doyRange : #check if line starts with doy
					#print '2'
					scanName = line[1:9]
					scanDoy = line[1:4]
					scanStart = line[1:4]+'.'+line[scanStartIndexStart:scanStartIndexEnd]
					scanEnd = line[1:4]+'.'+line[scanEndIndexStart:scanEndIndexEnd]
					scanStart = convertTime(scanStart) - datetime.timedelta(0,slewTime)
					scanEnd = convertTime(scanEnd) + datetime.timedelta(0,slewTime)
			   		for time in stowTimes:
						formattedTime = convertTime(time) # convert stow time to a datetime obj
						#print formattedTime.time(),scanStart.time(),scanEnd.time()
						if scanDoy == formattedTime.strftime('%j'):
							#print '3'
				   			if formattedTime.time() >= scanStart.time() and formattedTime.time() <= scanEnd.time():
								#print '4'				   			
								scansAffected.append(line[67:73]) #store the scan name
							if prevScanEnd != None:
								#print '5'
								if formattedTime.time() >= prevScanEnd.time() and formattedTime.time() <= scanStart.time():
									#print '6'
									scansAffected.append(line[67:73]) #store the scan name
							
					prevScanEnd = scanEnd
	
	
		sumFile.close()
	if len(scansAffected)==0: # if it is empty for some reason
		#print '7'
		scansAffected.append('Error')
	return scansAffected


def diskUsage(disk_pos, disk_posBenchmark,offset):
	#print disk_pos
	dataRecorded = 	(float(disk_pos)/float(1E+9)) - float(offset)
	if disk_posBenchmark == 'Error':
		difference = 'Error'
	else:
		difference =  dataRecorded - float(disk_posBenchmark)
	return dataRecorded,difference
def formatData(inNum):
	#print inNum
	if inNum == 'Error':
		return 'Error'
	
	else:
		return str(round(float(inNum),2))[1:]
		

def printData(dataRec, dataExp, dataDiff, stations,time,logfileName,experiment,offset):
	stationName = [] #full name of the sation
	dataRecMod  = []
	dataExpMod  = []
	dataDiffMod = []
	timeMod = []
	logMod = []
	sumFileMod =[]
	offsetMod =[]
	for stn in range (len(stations)):
		if stations[stn] == 'hb':
			station = 'Hobart 12m'
		elif stations[stn] =='ke':
			station = 'Katherine 12m'
		elif stations[stn] =='yg':
			station = 'Yarragadee 12m' 
		elif stations[stn] =='ho':
			station = 'Hobart 26m'
		stationName.append(station)
		dataRecMod.append( 'Recorded = '+str(round(dataRec[stn],1))+ ' GB')
		dataExpMod.append( 'Expected = '+str(dataExp[stn])+ ' GB')
		dataDiffMod.append('Difference = '+formatData(dataDiff[stn])+ ' GB')	
		timeMod.append('Time = '+time[stn]+ ' UT')
		logMod.append('Log file = '+logfileName[stn])
		sumFileMod.append('Sum file = ' +experiment+stations[stn]+'.sum')
		offsetMod.append('Offset = ' +str(offset[stn])+ ' GB')
	newData = []
	newData.append(stationName)
	newData.append(timeMod)
	newData.append(logMod)
	newData.append(sumFileMod)
	newData.append(offsetMod)
	newData.append(dataRecMod)
	newData.append(dataExpMod)
	newData.append(dataDiffMod)

	col_width = max(len(word) for row in newData for word in row) + 5
 	print '  \n'
	print '  \n'
	for row in newData:
		print "".join(word.ljust(col_width) for word in row)
	print '  \n'
	print '  \n'

def fetchlog(station, experiment):
    import os
    print('Retrieving %s%s.log from pcfs%s' %(experiment,station,station))
    os.system('scp oper@pcfs%s:/usr2/log/%s%s.log /vlbobs/ivs/logs/' %(station,experiment,station))

def main():
	experiment = 'r1777' # change this
	stations = ['hb','ke','yg'] #make sure this is okay
	logfileName =['r1777_hb_erc.log','r1777_ke_erc.log','r1777_yg_erc.log'] # these are the log monitor files
	offset =[0.353, 0.865, 0.321] # offsets in order of stations hb, ke, yg, ho     
	dataRec = []
	dataDiff = []
	dataExp =[]
	time =[]
	
        for sn,stan in enumerate(stations): # more pythonic than for stns in range(len(stations)):

		logFilePath = '/vlbobs/ivs/logs/'+ logfileName[sn] 
                #logFilePath = '/tmp/'+ logfileName[sn]
	#	fetchlog(stn,experiment)
                sumFilePath = '/vlbobs/ivs/sched/'+ experiment + stan +'.sum'

		disk_posTime, disk_pos,doy = findErrors(logFilePath)
		#print 'day is', doy
		if doy <100:
			doyRange = ['0'+str(doy-1),'0'+str(doy),'0'+str(doy+1)]
		else:
			doyRange = [str(doy-1),str(doy),str(doy+1)]
		#print doyRange
		disk_posBenchmark= findScansAffected (sumFilePath, disk_posTime,doyRange,0,stan)
		#print stan,disk_posTime, disk_pos, disk_posBenchmark,offset[sn]
		dataRecorded,diff = diskUsage(disk_pos, disk_posBenchmark[0], offset[sn])
		dataRec.append(dataRecorded)
		dataDiff.append(diff)
		dataExp.append(disk_posBenchmark[0])
		time.append(disk_posTime[4:])
	printData(dataRec, dataExp, dataDiff, stations, time,logfileName,experiment,offset)
	
      	
	
main() # 
