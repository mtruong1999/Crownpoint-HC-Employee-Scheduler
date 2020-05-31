########################################################
## algorithm.py
##
## This file implements the algorithm for generating the
## best schedule possible given employees and their
## preferences as well as locations and their
## requirements.
########################################################
## License Info: n/a
########################################################
## Author: Michael Truong
## Copyright: Copyright 2020, ECE 435 Employee Scheduler
## Credits: [Michael Truong]
## License: n/a
## Version: 1.0.0
## Maintainer: Michael Truong
## Email: n/a
########################################################
from pulp import *
import pandas as pd
import sys
import json # delete
# TODO: Probably change shifts to be only for 1 week, and just run generateSchedule
# 4 times in main (for 2 pay periods) as this is easier to implement
shifts = ['M1','T1','W1','R1','F1','M2','T2','W2','R2','F2']

validLocations = ["CHCF", "THS", "PPHC"]
maxLimits = {"CHCF" : 5, "THS" : 3, "PPHC" : 3} # Hardcoded maxes, ideally in future get this from GUI

listOfVariables = []
allEmployees = {}
allLocations = {}

def preference(instance):
	"""
	Given a shift instance, returns the weight of the preference
	based on the parameters of the instance.
	
	Currently, weight should be -10000 if employee requests a day off, -5 if they
	are not available, 1 if they are available
	
	Aforementioned values are subject to change.
	
	See coefficients() for description of the input variable "instance"
	"""
	weight = 0
	employee = instance[0]
	day = instance[1]
	location = instance[2]
	global allEmployees
	# TODO: account for federal holidays, idea: create a dictionary mapping day in shifts
	# to its real data. May have to do remove those days AFTER the schedule is generated
	# however this wont be able to account for shifting people days to 'make-up' hours missed
	# unless they do paid holidays... then were good.

	
	if day not in allEmployees[employee]['Availability']:
		weight -= 5 # Experiment, should it be -5 or -1? or -10?
	else:
		weight += 5
	if location not in allEmployees[employee]['PreferredLocationOfWork']:
		weight -= 5
	else:
		weight+= 5

	return weight
	# TODO: Use date dictionary mentioned above, check if a day is requested off and set 
	# weight for that day to -10000 or -15 or -10 or -5, etc depending on order of who requested first
	
	# TODO: Look into whether or not we should allow weights to be 0, might affect 'seniority'	
		
def seniority(instance):
	"""
	TODO: Function to return weight for 'weighted alternates'
	
	See coefficients() for description of the input variable "instance"
	"""
	return 1
	
def coefficients(instance):
	'''
	Given a shift instance, calculates the coefficient (i.e. weights) of the instance.
	A shift instance is a tuple in the form (employeeName, shift day, location, role).
	'''
	return seniority(instance) * preference(instance)

def locationRequirements(location):
	'''
	Returns tuple (x,y) where x is the list of all requirements
	per location and y is a list of unique elements in x.

	Assumes that if, for example, two pediatricians are
	required, then the list of AgeRequired would be:
	['Pediatric', 'Pediatric'].

	'''
	age_ = ['pediatric', 'adult','geriatric', 'family']
	specialty_ = ['emergency', 'urgent care', 'primary care', 'obstetrics']
	license_ = ['physician','nurse midwife', 'nurse practitioner']

	specReq = location['SpecialtyRequired']
	ageReq = location['AgeRequired']
	licReq = location['LicenseRequired']
	allReqs = []
	for elem in specReq:
		if elem == '':
			continue
		elif elem.lower().strip() not in specialty_:
			sys.exit("ERROR: Invalid input in location specialty requirement- {}\n must be either '' or in {}".format(elem, specialty_))
		else:
			allReqs.append(elem.lower().strip())
	for elem in ageReq:
		if elem == '':
			continue
		elif elem.lower().strip() not in age_:
			sys.exit("ERROR: Invalid input in location age requirement- {}\n must be either '' or in {}".format(elem, age_))
		else:
			allReqs.append(elem.lower().strip())
	for elem in licReq:
		if elem == '':
			continue
		elif elem.lower().strip() not in license_:
			sys.exit("ERROR: Invalid input in location age requirement- {}\n must be either '' or in {}".format(elem, license_))
		else:
			allReqs.append(elem.lower().strip())
	return (allReqs, list(set(allReqs)))

def checkSpecInput(specialty, validSpecialties):
	'''
	Checks for valid input in employee specialties
	'''
	if specialty not in validSpecialties:
		sys.exit("\nERROR: The input '{}' is NOT a valid input from {}\n".format(specialty, validSpecialties))
	return True
def maxNumEmployeesPerDay(location):
	'''
	Returns max number of employees allowed per day at a facility
	Values are currently hardcoded, in the future it would be ideal
	to take in this number through the GUI
	'''
	if location not in validLocations:
		sys.exit("ERROR: Invalid location name given. Given {}, expected one of {}".format(location, validLocations))
	return maxLimits[location]

def formatOutputSchedule(allEmployees, scheduleResult):
	"""
	Formats final schedule according to the CrownPoint's example
	schedule
	"""
	columns = list(allEmployees.keys())
	names = list(allEmployees.keys())
	indexes = shifts
	for i in range(len(columns)):
		columns[i] = columns[i] + ", " + allEmployees[columns[i]]["Age"]
	finalProduct = pd.DataFrame(columns = columns, index = indexes)
	g = 0
	for emp in names:
		#scheduledDays = []
		empdf = scheduleResult[scheduleResult["Employee Name"] == emp]
		tempDict = {}
		for d in indexes:
			tempDict[d] = ''
		for i in empdf.index:
			temp = empdf.loc[i]
			tempDict[temp["Day"]] = temp["Location"]
			
			# create list of loc names them add it to final product
		if emp in columns[g]:
			finalProduct[columns[g]] = pd.Series(tempDict)
		else:
			sys.exit("ERROR: Hmm... Something fishy happened.. Check alignment of columns and names in function formatOutputSchedule()")

		g += 1
		# finalProduct[emp] = scheduledDays
	finalProduct.to_csv('output_schedule.csv', index=True)	
def generateSchedule():
	'''
	Creates and solves LP problem, generating an optimal schedule
	'''
	
	# TODO: Avoid hard coding this, this is to generate all possible roles
	# Beware: case and spelling matters... thus need to avoid hard coding
	age_ = ['pediatric', 'adult','geriatric', 'family']
	specialty_ = ['emergency', 'urgent care', 'primary care', 'obstetrics']
	license_ = ['physician','nurse midwife', 'nurse practitioner']
	roles = []
	
	roles = [','.join([a,s,l]) for a in age_ for s in specialty_ for l in license_ ]
	
	data = getJSON()
	global allEmployees
	allEmployees = data['Employees']

	global allLocations
	allLocations = data['Locations']

	for employee in allEmployees.keys():
	
		specialty = []
		# Input error checking
		if(checkSpecInput(allEmployees[employee]['Age'].lower(), age_)):
			specialty.append(allEmployees[employee]['Age'].lower())
		if(checkSpecInput(allEmployees[employee]['Specialty'].lower(), specialty_)):
			specialty.append(allEmployees[employee]['Specialty'].lower())
		if(checkSpecInput(allEmployees[employee]['License'].lower(), license_)):
			specialty.append(allEmployees[employee]['License'].lower())
		
		specialtyString = ','.join(specialty)
		#TODO: Implement weighted alternates...
		
		for day in shifts:
			# Include all locations, set preferred location coefficient to 10 and non preferred to 1?
			for location in allLocations.keys():
				# In coefficients, set days not in preference to 1, all preferred dates to 10
				listOfVariables.append((employee, day, location, specialtyString))
	
	# create binary to state that a shift setting is used
	x = LpVariable.dicts('shift', listOfVariables, lowBound = 0, upBound = 1, cat = LpInteger)

	shift_model = LpProblem("Employee_Scheduling_Model" , LpMaximize)
	shift_model += lpSum([coefficients(shift_instance) * x[shift_instance] for shift_instance \
					in listOfVariables])
	
	# prefilter dictionary for efficiency
	x_dlr={}
	for (e, d, l, r), _x in x.items():
		_tup = d, l, r
		if _tup not in x_dlr:
			x_dlr[_tup] = []
		x_dlr[_tup].append(_x)

	# Add Constraint limiting the min number of possible employees of a specific role to schedule on a given day at a given location
	#for day in shifts: # for each day in pay period
		#for location in allLocations.keys(): # for each clinic
			#for role in roles: # for each role
				#_tup = day, location, role
				#if(x_dlr.get(_tup, []) == []):
					#continue
				#shift_model += lpSum(x_dlr.get(_tup, [])) >=minnum_(*_tup), "Min employees for {} {} {}".format(day,location,role)
	
	'''
				shift_model+= sum([x[shift_instance] for shift_instance in listOfVariables \
								if (day in shift_instance) and (location in shift_instance) \
									and (role in shift_instance)]) >= minnum_(day, location, role), "Min employees for {} {} {}".format(day,location,role)
	'''
	'''
	for day in shifts: # for each day in pay period
		for location in allLocations.keys(): # for each clinic
			for role in roles: # for each role
				_tup = day, location, role
				#shift_model += lpSum(x_dlr.get(_tup, [])) <= maxnum_(*_tup), "Max employees for {} {} {}".format(day,location,role)
				shift_model += lpSum(x_dlr.get(_tup, [])) == 2, "Max employees for {} {} {}".format(day,location,role)
	'''
	# Constraint for min number of employees of a required role per facility
	for location in allLocations.keys():
		locationReqs = locationRequirements(allLocations[location])
		for day in shifts:
			for req in locationReqs[1]:
				reqCount = locationReqs[0].count(req)
				shift_model += lpSum([x[shift_instance] for shift_instance in listOfVariables if req in shift_instance[3] and day in shift_instance and location in shift_instance]) >= reqCount, \
					"Min number of {} at {} on {} needed is {}".format(req,  location, day, reqCount)
	
	# Constraint to limit number of employees per day at a facility
	x_dl={}
	for (e, d, l, r), _x in x.items():
		_tup = d, l
		if _tup not in x_dl:
			x_dl[_tup] = []
		x_dl[_tup].append(_x)
	for location in allLocations.keys():
		for day in shifts:
			#shift_model += lpSum([x[instance] for instance in listOfVariables if location in instance and day in instance]) <= maxNumEmployeesPerDay(location),\
				#"Limit {} employees on {} at {}".format(maxNumEmployeesPerDay(location), day, location)
			_tup = day, location
			shift_model += lpSum(x_dl.get(_tup, [])) <= maxNumEmployeesPerDay(location), "Limit {} employees on {} at {}".format(maxNumEmployeesPerDay(location), day, location)
	
	
	# Constraint to limiting at most 1 shift per employee per day
	for employee in allEmployees.keys():
		for day in shifts:
			shift_model+= lpSum([x[shift_instance] for shift_instance in listOfVariables if day in shift_instance and employee in shift_instance]) <= 1, "Limit {} to 1 shift on day {}".format(employee, day)
	# Constrain number of shifts an employee can work per week
	# TODO: Change 3 to days function
	shifts_week1 = ['M1','T1','W1','R1','F1']
	shifts_week2 = ['M2','T2','W2','R2','F2']
	for employee in allEmployees.keys():
		limitDaysPerWeek = int(allEmployees[employee]["PreferredWorkingDays"])
		shift_model += lpSum([x[shift_instance] for shift_instance in listOfVariables if employee in shift_instance and shift_instance[1] in shifts_week1]) <= limitDaysPerWeek, "Limit {} to 3 shifts per week 1".format(employee)
	for employee in allEmployees.keys():
		limitDaysPerWeek = int(allEmployees[employee]["PreferredWorkingDays"])
		shift_model += lpSum([x[shift_instance] for shift_instance in listOfVariables if employee in shift_instance and shift_instance[1] in shifts_week2]) <= limitDaysPerWeek, "Limit {} to 3 shifts per week 2".format(employee)
	
	status = shift_model.solve()
	
	if(status == 1):
		print("\n\nAn optimal solution was found!\n\n")
	else:
		print("\n\n---AN OPTIMAL SOLUTION WAS NOT FOUND---\n\nSolution status:\n\t{}".format(LpStatus[status]))

	shift_model.writeLP("linear_model_log.lp")
	schedule = {'Employee Name': [], 'Day': [], 'Location': [], 'Role': []}
	for shift_instance in listOfVariables:
		if x[shift_instance].value() == 1.0:
			schedule['Employee Name'].append(shift_instance[0])
			schedule['Day'].append(shift_instance[1])
			schedule['Location'].append(shift_instance[2])
			schedule['Role'].append(shift_instance[3])
	#return pd.DataFrame(schedule, columns = ['Employee Name', 'Day', 'Location','Role'])
	#print(pd.DataFrame(schedule, columns = ['Employee Name', 'Day', 'Location','Role']))
	solution = pd.DataFrame(schedule, columns = ['Employee Name', 'Day', 'Location','Role'])
	#solution.to_csv('final_schedule.csv', index=False)
	formatOutputSchedule(allEmployees, solution)

def getJSON(): # delete
	File_Path=str(os.getcwd())
	#try_File_Path=File_Path[:-3]+'files/employeeInfo.json'
	try_File_Path=File_Path[:-3]+'\\data_converted.json'

	try:
		with open(try_File_Path) as f:
			data=json.load(f)
	except:
		File_Path=File_Path+'\\data_converted.json'
		#print(File_Path)
		with open(File_Path) as f:
			data=json.load(f)
	return data




#generateSchedule()