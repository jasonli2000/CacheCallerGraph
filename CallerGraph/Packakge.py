#!/usr/bin/env python

# A Wrapper around all the routine in a package
#---------------------------------------------------------------------------
# Copyright 2011 The Open Source Electronic Health Record Agent
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#----------------------------------------------------------------

import glob
import re
import os
import os.path

#Routines starts with A followed by a number
ARoutineEx=re.compile("^A[0-9]+$") 

nameValuePair=re.compile("^[ >]+ +(?P<name>[^ ]+) +(?P<value>[^ ]+)$")
RoutineStart=re.compile("^Routine: (?P<name>[^ ]+)$")
localVarStart=re.compile("^Local Variables +Routines")
globalVarStart=re.compile("^Global Variables")
nakedGlobalStart=re.compile("^Naked Globals")
markedItemStart=re.compile("^Marked Items")
routineInvokesStart=re.compile('Routine +Invokes')
calledRoutineStart=re.compile("^Routine +is Invoked by:")
RoutineEnd=re.compile("-+ END -+")

class Routine:
    #constructor
    def __init__(self, routineName, package=None):
        self.name=routineName
        self.localVariables=[]
        self.globalVariables=[]
        self.nakedGlobals=[]
        self.markedItems=[]
        self.calledRoutines=set()
        self.package=package
    def setName(self, routineName):
        self.name=routineName
    def getName(self):
        return self.name
    def addLocalVariables(self, localVariables):
        self.localVariables.append(localVariables)
    def getLocalVariables(self):
        return self.localVariables
    def addGlobalVariables(self, globalVariables):
        self.globalVariables.append(globalVariables)
    def getGlobalVaribales(self):
        return self.globalVariables
    def addNakedGlobals(self, globals):
        self.nakedGlobals.append(globals)
    def getNakedGlobals(self):
        return self.nakedGlobals
    def addMarkedItem(self, markedItem):
        self.markedItems.append(markedItem)
    def getMarkedItem(self):
        return self.markedItems
    def addCalledRoutines(self, Routine):
        self.calledRoutines.add(Routine)
    def getCalledRoutines(self):
        return self.calledRoutines
    def setPackage(self, package):
        self.package = package
    def printResult(self):
        print "Routine Name: %s" % (self.name)
        for var in self.localVariables:
            print "Local Vars: %s " % var
        for var in self.globalVariables:
            print "Global Vars: %s " % var
        for var in self.nakedGlobals:
            print "Naked Globals: %s " % var
        for var in self.markedItems:
            print "Marked Items: %s" % var
        for var in self.calledRoutines:
            print "Called Routines: %s " % var
        
class Package:
    #constructor
    def __init__(self, packageName):
        self.name=packageName
        self.routines=dict()
    def addToPackage(self,Routine):
        self.routines[Routine.getName()] = Routine
        Routine.setPackage(self)
    def getAllRoutines(self):
        return self.routines
    def getRoutine(self, routineName):
        return self.routines[routineName]
    def hasRoutine(self, routineName):
        return routineName is self.routines.keys
    def getName(self):
        return self.name

class AbstractSectionParse:       
    def parseLine(self, line):
        pass
    def setRoutine(self, routine):
        pass

class LocalVarSectionParse (AbstractSectionParse):
    def __init__(self):
        self.routine=None
    def parseLine(self, line):
        result = nameValuePair.search(line)
        if (result):
                self.routine.addLocalVariables(result.group('name'))
    def setRoutine(self, routine):
        self.routine=routine

class GlobalVarSectionParse (AbstractSectionParse):
    def __init__(self):
        self.routine=None
    def parseLine(self, line):
        result = nameValuePair.search(line)
        if (result):
                self.routine.addGlobalVariables(result.group('name'))
    def setRoutine(self, routine):
        self.routine=routine

class NakedGlobalsSectionParser (AbstractSectionParse):
    def __init__(self):
        self.routine=None
    def parseLine(self, line):
        result = nameValuePair.search(line)
        if (result):
                self.routine.addNakedGlobals(result.group('name'))
    def setRoutine(self, routine):
        self.routine=routine    

class MarkedItemsSectionParser (AbstractSectionParse):
    def __init__(self):
        self.routine=None
    def parseLine(self, line):
        result = nameValuePair.search(line)
        if (result):
                self.routine.addMarkedItem(result.group('name'))
    def setRoutine(self, routine):
        self.routine=routine
                        
class CalledRoutineSectionParser (AbstractSectionParse):
    def __init__(self):
        self.routine=None
    def parseLine(self, line):
        result = nameValuePair.search(line)
        if (result):
            routineDetail=result.group('name').split('^')
            self.routine.addCalledRoutines(routineDetail[len(routineDetail)-1])
    def setRoutine(self, routine):
        self.routine=routine    
# global one 
localVarParser=LocalVarSectionParse()
globalVarParser=GlobalVarSectionParse()
nakedGlobalParser=NakedGlobalsSectionParser()
markedItemsParser=MarkedItemsSectionParser()
calledRoutineParser=CalledRoutineSectionParser()


class CallerGraphLogFileParser:
    def __init__(self):
        self.allRoutines = dict()
        self.currentRoutine=None
        self.parser=None
        
    def onNewRoutineStart(self, routineName):
        if not self.currentRoutine:
            self.currentRoutine = Routine(routineName)
        if (routineName != self.currentRoutine):
            self.currentRoutine = Routine(routineName)
        
    def onNewRoutineEnd(self, routineName):
        self.allRoutines[routineName] = self.currentRoutine
        self.currentRoutine = None
        
    def onLocalVariablesStart(self, line):
        self.parser=localVarParser
        self.parser.setRoutine(self.currentRoutine)
    def onGlobaleVariables(self, line):
        self.parser=globalVarParser
        self.parser.setRoutine(self.currentRoutine)
    def onCalledRoutines(self,line):
        self.parser=calledRoutineParser
        self.parser.setRoutine(self.currentRoutine)
    def onNakedGlobals(self, line):
        self.parser=nakedGlobalParser
        self.parser.setRoutine(self.currentRoutine)
    def onMarkedItems(self, line):
        self.parser=markedItemsParser
        self.parser.setRoutine(self.currentRoutine)
    def onRoutineInvokes(self, line):
        self.parser=None
    def parseNameValuePair(self, line):
        if self.parser:
            self.parser.parseLine(line)
    def printResult(self):
        print "Total Routines are %d" % len(self.allRoutines)  
    def printRoutine(self, routineName): 
        if routineName in self.allRoutines.keys():
            self.allRoutines[routineName].printResult()
        else:
            print "Routine: %s Not Found!" % routineName

def findPackagesAndRoutinesBySource(dirName, pattern):
    searchFiles = glob.glob(os.path.join(dirName, pattern))
    print "Total Search Files are %d " % len(searchFiles)
    AllRoutines=dict()
    AllPackages=dict()
    for file in searchFiles:
        routineName = os.path.basename(file).split(".")[0]
        packageName = os.path.dirname(file)
        packageName = packageName[packageName.index("Packages")+9:packageName.index("Routines")-1]
        if packageName not in AllPackages.keys():
            AllPackages[packageName]= Package(packageName)
        if routineName not in AllRoutines:
            AllRoutines[routineName]=Routine(routineName,AllPackages[packageName])
        else:
            print ("Duplicated Routine name")
        if ARoutineEx.search(routineName):
            print "A Routines %s should be exempted" % routineName
    print "Total package is %d and Total Routines are %d" % (len(AllPackages), len(AllRoutines))  

def parseAllCallerGraphLog(dirName, pattern): 
    callerGraphLogFile = os.path.join(dirName, pattern)
    logParser = CallerGraphLogFileParser()
    allFiles=glob.glob(callerGraphLogFile)
    for logFile in allFiles:
        file = open(logFile,'r')
        for line in file:
            #strip the newline
            line = line.rstrip(os.linesep)
            if (line.strip() == ''):
                continue
            result = RoutineStart.search(line)
            if result:
                routineName = result.group('name')
    #            print "routine %s Started:" % routineName
                logParser.onNewRoutineStart(routineName)
                continue
            if localVarStart.search(line):
    #            print "localVar Started:"
                logParser.onLocalVariablesStart(line)
                continue
            if globalVarStart.search(line):
    #            print "global started:"
                logParser.onGlobaleVariables(line)
                continue
            if nakedGlobalStart.search(line):
    #            print "naked global started"
                logParser.onNakedGlobals(line)
                continue
            if markedItemStart.search(line):
    #            print "marked Item started"
                logParser.onMarkedItems(line)
                continue
            if calledRoutineStart.search(line):
    #            print "called routine started"
                logParser.onCalledRoutines(line)
                continue
            if RoutineEnd.search(line):
    #            print "routine End called"
                logParser.onNewRoutineEnd(routineName)
                continue
            if routineInvokesStart.search(line):
                logParser.onRoutineInvokes(line)
                continue
            result=nameValuePair.search(line)
            if result:
    #            print "Name: %s Value=%s" % (result.group("name"), result.group("value"))
                logParser.parseNameValuePair(line)
                continue
    logParser.printResult()
    logParser.printRoutine('A7RDUP')
    logParser.printRoutine('A7RUCH04')         
if __name__ == '__main__':
    # the step to parse the log file
    #parse the log file
    callLogDir = "C:/Users/jason.li/build/VistaCache/Docs/CallerGraph"
    callLogPattern="*.log"
#    parseAllCallerGraphLog(callLogDir, callLogPattern)
    routineFilePattern = "*/Routines/*.m"
    routineFileDir = "C:/cygwin/home/jason.li/git/VistA-FOIA/Packages/"
    findPackagesAndRoutinesBySource(routineFileDir, routineFilePattern)