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
import sys
import subprocess

from datetime import datetime, date, time

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

routinePackageMap=dict()
packageSet=set()
write=sys.stdout.write

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
        print "Routine Name: %s " % (self.name)
        if self.name in routinePackageMap.keys():
            write("Package Name: %s" % routinePackageMap[self.name])
        write("\n")
        write("Local Vars: \n")
        for var in self.localVariables:
            write(" %s " % var)
        write("\n")
        write("Global Vars: \n")
        for var in self.globalVariables:
            write( " %s " % var)
        write("\n")
        write("Naked Globals: \n")
        for var in self.nakedGlobals:
            write( " %s " % var)
        write("\n")
        write("Marked Items: \n")
        for var in self.markedItems:
            write( " %s " % var)
        write("\n")
        write("Called Routines: \n")
        for var in self.calledRoutines:
            write( " %s " % var)
            if var in routinePackageMap:
                write ("Package: %s \n" % routinePackageMap[var])
            else:
                write("\n")
    def printResultInC(self):
        try:
            dirName=("c:/temp/VistA/%s/") % routinePackageMap[self.name]
            if not os.path.exists(dirName):
                os.makedirs(dirName)
        except OSError:
            print "Error making dir %s : Error: %s"  % (dirName, OSError)
            return
        
        file = open(("%s/%s.cpp") % (dirName, self.name), 'w')
        if self.name in routinePackageMap.keys():
            file.write(("/*! \\namespace %s \n") % (routinePackageMap[self.name]))
            file.write("*/\n")
            file.write("namespace %s {" % routinePackageMap[self.name])

#        file.write("/* Global Vars: */\n")            
#        for var in self.globalVariables:
#            file.write( " int %s;\n" % var)
#        file.write("\n")   
#        file.write("/* Naked Globals: */\n")
#        for var in self.nakedGlobals:
#            file.write( " int %s;\n" % var)
#        file.write("\n")
#        file.write("/* Marked Items: */\n")
#        for var in self.markedItems:
#            file.write( " int %s;\n" % var)
        file.write("\n")     
        file.write("/*! \callgraph\n")
        file.write("*/\n")
        file.write ("void " + self.name+ "(){\n")
#        if self.name in routinePackageMap.keys():
#            write("Package Name: %s" % routinePackageMap[self.name])
#        write("\n")
        
#        file.write("/* Local Vars: */\n")
#        for var in self.localVariables:
#            file.write(" int %s; \n" % var)


        file.write("/* Called Routines: */\n")
        for var in self.calledRoutines:
            file.write( "  %s ();\n" % var)
#            if var in routinePackageMap:
#                write ("Package: %s \n" % routinePackageMap[var])
#            else:
        file.write("}\n")        
        file.write("}// end of namespace")
        file.close()    
        #subprocess to write to the ps file

    
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
            routineName = routineDetail[len(routineDetail)-1]
            if routineName.startswith('%'):
                routineName=routineName[1:]
            self.routine.addCalledRoutines(routineName)
    def setRoutine(self, routine):
        self.routine=routine    
# global one 
localVarParser=LocalVarSectionParse()
globalVarParser=GlobalVarSectionParse()
nakedGlobalParser=NakedGlobalsSectionParser()
markedItemsParser=MarkedItemsSectionParser()
calledRoutineParser=CalledRoutineSectionParser()
#===============================================================================
# interface to generated the output based on a routine
#===============================================================================
class RoutineVisit:
    def visitRoutine(self, routine, outputDir):
        pass
#===============================================================================
# Default implementation of the routine 
#===============================================================================    
class DefaultRoutineVisit:
    def visitRoutine(self, routine,outputDir):
        routine.printResult()
#===============================================================================
# output result to use graphviz to generated the graph
#===============================================================================
class GraphvizRoutineVisit(RoutineVisit):
    def visitRoutine(self,routine, outputDir):
        routineName=routine.getName()
        calledRoutines=routine.getCalledRoutines()
        packageName = routinePackageMap[routineName]
        if len(calledRoutines) == 0:
            print("No called Routines found! for routine:%s") % (routineName)
            return
        localPackage=dict()
        localPackage[routinePackageMap[routineName]]=set()
        localPackage[routinePackageMap[routineName]].add(routineName)
        for var in calledRoutines:
            if var in routinePackageMap.keys():
                if routinePackageMap[var] not in localPackage.keys():
                    localPackage[routinePackageMap[var]]=set()
                localPackage[routinePackageMap[var]].add(var)
        
        try:
            dirName=os.path.join(outputDir,packageName)
            if not os.path.exists(dirName):
                os.makedirs(dirName)
        except OSError:
            print "Error making dir %s : Error: %s"  % (dirName, OSError)
            return
        output=open(os.path.join(dirName,routineName+".dot"),'w')
        output.write("digraph %s {\n" % routineName)
        if packageName not in localPackage.keys():
            output.write("\tsubgraph %s{\n" % (var.replace(' ','_').replace('-','_')))
            output.write("\t\t" + routineName + ";\n")
            output.write("\t\tlabel=\"%s\";" % var)
            output.write("\t}\n")
        for var in localPackage.keys():
            output.write("\tsubgraph %s{\n" % (var.replace(' ','_').replace('-','_')))
            if var == packageName:
                output.write("\t\t%s->{" % routineName)
                for val in localPackage[var]:
                    if val != routineName:
                        output.write(val + ";")
                output.write("}\n")
            else:
                for val in localPackage[var]:
                    output.write("\t\t" + val+";\n")
            output.write("\t\tlabel=\"%s\";\n" % var)
            output.write("\t}\n")
            if var != packageName:
                for val in localPackage[var]:
                    output.write("\t" + routineName + "->" + val + ";\n")
        output.write("}\n")
        output.close()

        outputName = os.path.join(dirName,routineName+".png")
        inputName=os.path.join(dirName,routineName+".dot")
        command="dot -Tpng -o \"%s\" \"%s\"" % (outputName, inputName)
#        print command
        retCode=subprocess.call(command)
        if retCode != 0:
            print "calling dot returns %d" % retCode
                
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
    def printRoutine(self, routineName, visitor=DefaultRoutineVisit()): 
        if routineName in self.allRoutines.keys():
#            self.allRoutines[routineName].printResult()
#            self.allRoutines[routineName].printResultInC()
            routine=self.allRoutines[routineName]
            visitor.visitRoutine(routine,"C:/Temp/VistA/")
        else:
            pass
#            print "Routine: %s Not Found!" % routineName


def findPackagesAndRoutinesBySource(dirName, pattern):
    searchFiles = glob.glob(os.path.join(dirName, pattern))
    print "Total Search Files are %d " % len(searchFiles)
    for file in searchFiles:
        routineName = os.path.basename(file).split(".")[0]
        packageName = os.path.dirname(file)
        packageName = packageName[packageName.index("Packages")+9:packageName.index("Routines")-1]
        if packageName not in packageSet:
            packageSet.add(packageName)
        if routineName not in routinePackageMap.keys():
            routinePackageMap[routineName]=packageName
        else:
            print ("Duplicated Routine name")
        if ARoutineEx.search(routineName):
            print "A Routines %s should be exempted" % routineName
        
    print "Total package is %d and Total Routines are %d" % (len(packageSet), len(routinePackageMap))  

logParser = CallerGraphLogFileParser()
def parseAllCallerGraphLog(dirName, pattern): 
    callerGraphLogFile = os.path.join(dirName, pattern)

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
                logParser.onNewRoutineStart(routineName)
                continue
            if localVarStart.search(line):
                logParser.onLocalVariablesStart(line)
                continue
            if globalVarStart.search(line):
                logParser.onGlobaleVariables(line)
                continue
            if nakedGlobalStart.search(line):
                logParser.onNakedGlobals(line)
                continue
            if markedItemStart.search(line):
                logParser.onMarkedItems(line)
                continue
            if calledRoutineStart.search(line):
                logParser.onCalledRoutines(line)
                continue
            if RoutineEnd.search(line):
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
    
def testDotCall():
    packageName="Nursing Service"
    routineName="NURA6F1"
    dirName = os.path.join("c:/temp/VistA/", packageName);
    outputName = os.path.join(dirName,routineName+".png")
    inputName=os.path.join(dirName,routineName+".dot")
    command="dot -Tpng -o \"%s\" \"%s\"" % (outputName, inputName)
    retCode=subprocess.call(command)
    print "calling dot returns %d" % retCode
      
if __name__ == '__main__':
    # the step to parse the log file
    #parse the log file
#    testDotCall()
#    exit()
    callLogDir = "C:/Users/jason.li/build/VistaCache/Docs/CallerGraph"
    callLogPattern="Nursing_Service.log"
    print "Starting Parsing all files...."
    print "Time is: %s" % datetime.now()
    parseAllCallerGraphLog(callLogDir, callLogPattern)
    print "End of parsing all files......"
    print "Time is: %s" % datetime.now()
    routineFilePattern = "*/Routines/*.m"
    routineFileDir = "C:/cygwin/home/jason.li/git/VistA-FOIA/Packages/"
    findPackagesAndRoutinesBySource(routineFileDir, routineFilePattern)
    for var in routinePackageMap.keys():
        logParser.printRoutine(var, GraphvizRoutineVisit())
    # read the user input from the terminal
    isExit=False
    while not isExit:
        var = raw_input("Please enter the routine Name:")
        if (var == 'quit'):
            isExit=True
            break
        else:
            if var in routinePackageMap.keys():
                logParser.printRoutine(var)
            else:
                print "Routine: %s NOT FOUND!" % var          
