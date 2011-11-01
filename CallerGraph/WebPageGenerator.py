#!/usr/bin/env python

# A python script to generate the documentation
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
import CallerGraphParser
import os
import os.path
import sys
import subprocess
import urllib

from datetime import datetime, date, time

#===============================================================================
# output result to use graphviz to generated the graph
#===============================================================================
class GraphvizRoutineVisit(CallerGraphParser.RoutineVisit):
    def visitRoutine(self, routine, outputDir):
        calledRoutines=routine.getCalledRoutines()
        if not calledRoutines or len(calledRoutines) == 0:
            return
        routineName=routine.getName()
        if not routine.getPackage():
            print "ERROR: routine: %s does not belongs to a package" % routineName
            return
        
        packageName = routine.getPackage().getName()
        if len(calledRoutines) == 0:
            print("No called Routines found! for routine:%s") % (routineName)
            return
        localPackage=dict()
        localPackage[packageName]=set()
        localPackage[packageName].add(routineName)
        for var in calledRoutines:
            if var.getPackage():
                if var.getPackage().getName() not in localPackage.keys():
                    localPackage[var.getPackage().getName()]=set()
                localPackage[var.getPackage().getName()].add(var.getName())
        
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
            output.write("\tsubgraph \"cluster_%s\"{\n" % (var))
            output.write("\t\t%s [style=filled fillcolor=orange];\n" % routineName)
            output.write("\t\tlabel=\"%s\";" % var)
            output.write("\t}\n")
        for var in localPackage.keys():
            output.write("\tsubgraph \"cluster_%s\"{\n" % (var))
            if var == packageName:
                output.write("\t\t%s [style=filled fillcolor=orange];\n" % routineName)
                for val in localPackage[var]:
                    if val != routineName:
                        output.write("\t\t%s [URL=\"%s\"];\n" % (getRoutineHtmlFileName(val), val))
                        output.write("\t\t%s->%s;\n" % (routineName, val))
            else:
                    output.write("\t\t%s [URL=\"%s\"];\n" % (getRoutineHtmlFileName(val), val))
            output.write("\t\tlabel=\"%s\";\n" % var)
            output.write("\t}\n")
            if var != packageName:
                for val in localPackage[var]:
                    output.write("\t" + routineName + "->" + val + ";\n")
        output.write("}\n")
        output.close()

        outputName = os.path.join(dirName,routineName+".gif")
        outputmap=os.path.join(dirName, routineName+".cmapx")
        inputName=os.path.join(dirName,routineName+".dot")
        # this is to generated the image in gif format and also cmapx (client side map) to make sure link
        # embeded in the graph is clickable
        command="dot -Tgif -o\"%s\" -Tcmapx -o\"%s\" \"%s\"" % (outputName, outputmap, inputName)
#        print command
        retCode=subprocess.call(command)
        if retCode != 0:
            print "Error: calling dot with command[%s] returns %d" % (command,retCode)
# utility functions
def getRoutineHtmlFileName(routineName):
    return "Routine_%s.html" % routineName

def getPackageHtmlFileName(packageName):
    return "Package_%s.html" % normalizePackageName(packageName)

def getRoutineHypeLinkByName(routineName):
    return "<a href=\"%s\">%s</a>" % (getRoutineHtmlFileName(routineName), routineName);

def getPackageHypefLinkByName(packageName):
    return "<a href=\"%s\">%s</a>" % (getPackageHtmlFileName(packageName), packageName);

def normalizePackageName(packageName):
    return packageName.replace(' ','_')

class WebPageGenerator:
    def __init__(self, allPackages, outDir):
        self.allPackages=allPackages
        self.outDir=outDir
    def generateWebPage(self):
#        self.generateIndexPage()
#        self.generateCallerGraph(self.outDir)
#        self.generatePackagePage()
#        self.generateIndividualPackagePage()
        self.generateIndividualRoutinePage()
    def generateIndexPage(self):
        pass
    def generateCallerGraph(self, outDir):  
        pass
    def generatePackagePage(self):
        header = open(os.path.join(self.outDir,"header.html"),'r')
        file = open(os.path.join(self.outDir,"packages.html"),'w')
        for line in header:
            file.write(line)
        #write the header
        file.write("<div class=\"header\">\n")
        file.write("<div class=\"headertitle\">")
        file.write("<h1>Package List</h1>\n</div>\n</div>")
        file.write("<div class=\"contents\"><table>\n")
        #generated the table
        for package in sorted(self.allPackages.keys()):
            file.write("<tr><td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a></td><td class=\"indexvalue\"></td></tr>\n" 
                       % (getPackageHtmlFileName(package), package))
        file.write("</table>\n</div>\n")
        file.write("</body>\n</html>\n")
        file.close()
        header.close()
    #generate the individual package pages
    def generateIndividualPackagePage(self):
        header = open(os.path.join(self.outDir,"header.html"),'r')
        headerLines=[]
        for line in header:
            headerLines.append(line)
        header.close()
        for package in sorted(self.allPackages.keys()):
            outputFile = open(os.path.join(self.outDir,getPackageHtmlFileName(package)),'w')
            #write the header part
            for line in headerLines:
                outputFile.write(line)
            outputFile.write("<div class=\"header\">\n")
            outputFile.write("<div class=\"headertitle\">")
            outputFile.write("<h1>Package %s</h1>\n</div>\n</div>" % package)
            outputFile.write("<div class=\"contents\"><table>\n")
            for routine in sorted(self.allPackages[package].getAllRoutines().keys()):
                outputFile.write("<tr><td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a></td><td class=\"indexvalue\"></td></tr>\n" 
                           % (getRoutineHtmlFileName(routine), routine ))
            outputFile.write("</table>\n</div>\n")
            outputFile.write("</body>\n</html>\n")
        outputFile.close()

    def generateIndexBar(self, outputFile, inputList):
        if (not inputList) or len(inputList) == 0:
            return
        outputFile.write("<div class=\"qindex\">\n")
        for i in range(len(inputList)-1):
            outputFile.write("<a class=\"qindex\" href=\"#%s\">%s</a>&nbsp;|&nbsp;\n" % (inputList[i], inputList[i]))
        outputFile.write("<a class=\"qindex\" href=\"#%s\">%s</a></div>\n" % (inputList[-1], inputList[-1]))

    def generateIndividualRoutinePage(self):
        header = open(os.path.join(self.outDir,"header.html"),'r')
        headerLines=[]
        for line in header:
            headerLines.append(line)
        header.close()  
        indexList=["Call Graph", "Called Routines", "Local Variables", "Global Variables", "Naked Globals", "Marked Items"]       
        for package in sorted(self.allPackages.keys()):
            for routineName in sorted(self.allPackages[package].getAllRoutines().keys()):
                routine = self.allPackages[package].getAllRoutines()[routineName]
                outputFile = open(os.path.join(self.outDir,getRoutineHtmlFileName(routineName)),'w')
                # write the same header file
                for line in headerLines:
                    outputFile.write(line)
                # generated the qindex bar
                self.generateIndexBar(outputFile, indexList)
                outputFile.write("<div class=\"header\">\n")
                outputFile.write("<div class=\"headertitle\">")
                outputFile.write("<h1>Package %s</h1>\n</div>\n</div>" % getPackageHypefLinkByName(package))
                outputFile.write("<h1>Routine %s</h1>\n</div>\n</div>" % routineName)
                outputFile.write("<a name=\"Call Graph\"/><h2 align=\"left\">Call Graph</h2>")
                calledRoutines = routine.getCalledRoutines()
                if (calledRoutines and len(calledRoutines) > 0):
                    # write the image of the caller graph
                    try:
                        outputFile.write("<div class=\"contents\">\n")
                        outputFile.write("<img src=\"%s\" border=\"0\" alt=\"Call Graph\" usemap=\"#%s\"/>\n" 
                                   % (package+"/"+routineName+".gif", routineName))
                        #append the content of map outputFile
                        cmapFile = open(os.path.join(self.outDir,package+"/"+routineName+".cmapx"),'r')
                        for line in cmapFile:
                            outputFile.write(line)  
                        outputFile.write("</div>\n")
                    except (IOError):
                        pass
                    outputFile.write("<a name=\"Called Routines\"/><h2 align=\"left\"> Called Routines</h2>\n")
                    outputFile.write("<div class=\"contents\"><table>\n")
                    outputFile.write("<tr><th class=\"indexkey\">Called Routine Name</th><th class=\"indexvalue\">Package</th></tr>\n")
                    for calledRoutine in routine.getCalledRoutines():
                        routinePackageLink=""
                        calledRoutineName=calledRoutine.getName()
                        if (calledRoutine.getPackage()):
                            routinePackageLink = getPackageHypefLinkByName(calledRoutine.getPackage().getName())
                        outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                                   % (getRoutineHypeLinkByName(calledRoutineName), routinePackageLink))
                    outputFile.write("</table>\n</div>\n")

                outputFile.write("<a name=\"Local Variables\"/><h2 align=\"left\"> Local Variables</h2>\n")
                outputFile.write("<div class=\"contents\"><table>\n")
                for localVar in routine.getLocalVariables():
                    outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Local Variable", localVar))
                outputFile.write("</table></div>\n")
                outputFile.write("<a name=\"Global Variables\"/><h2 align=\"left\"> Global Variables</h2>\n")
                outputFile.write("<div class=\"contents\"><table>\n")
                for globalVar in routine.getGlobalVariables():
                    outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Global Variable", globalVar))
                outputFile.write("</table></div>\n")
                outputFile.write("<a name=\"Naked Globals\"/><h2 align=\"left\"> Naked Globals</h2>\n")
                outputFile.write("<div class=\"contents\"><table>\n")                
                for nakedGlobal in routine.getNakedGlobals():
                    outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Naked Global", nakedGlobal))
                outputFile.write("</table></div>\n")
                outputFile.write("<a name=\"Marked Items\"/><h2 align=\"left\"> Marked Items</h2>\n")
                outputFile.write("<div class=\"contents\"><table>\n")
                for markedItem in routine.getMarkedItems():
                    outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Marked Item", markedItem))
                outputFile.write("</table></div>\n")
                
                # generated the index bar at the bottom
                self.generateIndexBar(outputFile, indexList)
                outputFile.write("</body>\n</html>\n")
                outputFile.close()

            
if __name__ == '__main__':   
    logParser = CallerGraphParser.CallerGraphLogFileParser()
    print "Starting parsing package/routine relationship...."
    print "Time is: %s" % datetime.now()
    routineFilePattern = "*/Routines/*.m"
    routineFileDir = "C:/cygwin/home/jason.li/git/VistA-FOIA/Packages/"
    logParser.findPackagesAndRoutinesBySource(routineFileDir, routineFilePattern)
    print "End parsing package/routine relationship...."
    print "Time is: %s" % datetime.now()
    
    print "Starting parsing caller graph log file...."    
    callLogDir = "C:/Users/jason.li/build/VistaCache/Docs/CallerGraph"
    callLogPattern="*.log"
    logParser.parseAllCallerGraphLog(callLogDir, callLogPattern)
    print "End of parsing log file......"
    print "Time is: %s" % datetime.now()         
    # generate all dot file and use dot to generated the image file format
    dotRoutineVisitor = GraphvizRoutineVisit()
    
#    print "Start generating caller graph......"
#    print "Time is: %s" % datetime.now()    
#    for var in logParser.getAllRoutines().values():
#        dotRoutineVisitor.visitRoutine(var, "C:/Temp/VistA")
#    print "Time is: %s" % datetime.now()
#    print "End of generating caller graph......"
    
    print "Starting generating web pages...."
    webPageGen=WebPageGenerator(logParser.getAllPackages(),"C:/Temp/VistA")
    webPageGen.generateWebPage()
    print "End of generating web pages...."