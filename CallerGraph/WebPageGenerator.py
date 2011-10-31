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
            output.write("\t\t" + routineName + ";\n")
            output.write("\t\tlabel=\"%s\";" % var)
            output.write("\t}\n")
        for var in localPackage.keys():
            output.write("\tsubgraph \"cluster_%s\"{\n" % (var))
            if var == packageName:
                output.write("\t\t%s->{" % routineName)
                for val in localPackage[var]:
                    if val != routineName:
                        output.write(val + " ")
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

        outputName = os.path.join(dirName,routineName+".svg")
        inputName=os.path.join(dirName,routineName+".dot")
        command="dot -Tsvg -o \"%s\" \"%s\"" % (outputName, inputName)
#        print command
        retCode=subprocess.call(command)
        if retCode != 0:
            print "calling dot returns %d" % retCode

class WebPageGenerator:
    def __init__(self, allPackages, outDir):
        self.allPackages=allPackages
        self.outDir=outDir
    def generateWebPage(self):
        generateIndexPage();
        generateCallerGraph(self.outDir)
        generatePackagePage()
        generateIndividualPackagePage()
        generateIndividualRoutinePage()
    def generateIndexPage(self):
        pass
    def generateCallerGraph(self, outDir):  
        pass
    def generatePackagePage(self):
        header = open(os.path.join(outDir,"header.html"),'r')
        file = open(os.path.join(outDir,"packages.html"),'w')
        for line in header:
            file.write(line)
        #write the header
        file.write("<div class=\"header\">\n")
        file.write("<div class=\"headertitle\">")
        file.write("<h1>Package List</h1>\n</div>\n</div>")
        file.write("<div class=\"contents\"><table>\n")
        #generated the table
        for package in self.allPackages.keys():
            file.write("<tr><td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a></td><td class=\"indexvalue\"></td></tr>\n" 
                       % ("Package_" + package.replace(' ','_')+".html", package))
        file.write("</table>\n</div>\n")
        file.write("</body>\n</html>\n")
        file.close()
        header.close()
    #generate the individual package pages
    def generateIndividualPackagePage(self):
        header = open(os.path.join(outDir,"header.html"),'r')
        for package in self.allPackages.keys():
            file = open(os.path.join(outDir,"Package_%s.html" % package.replace(' ','_')),'w')
            for line in header:
                file.write(line)
            file.write("<div class=\"header\">\n")
            file.write("<div class=\"headertitle\">")
            file.write("<h1>Package %s</h1>\n</div>\n</div>" % package)
            file.write("<div class=\"contents\"><table>\n")
            for routine in package.getAllRoutines().keys():
                file.write("<tr><td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a></td><td class=\"indexvalue\"></td></tr>\n" 
                           % ("Routine_"+ routine+".html", routine ))
            file.write("</table>\n</div>\n")
            file.write("</body>\n</html>\n")
        file.close()
        header.close()
    def generateIndividualRoutinePage(self):  
        header = open(os.path.join(outDir,"header.html"),'r')
        for package in self.allPackages.keys():
            for routine in package.getAllRoutines().keys():
                file = open(os.path.join(outDir,"Routine_%s.html" % routine),'w')
                for line in header:
                    file.write(line)
                file.write("<div class=\"header\">\n")
                file.write("<div class=\"headertitle\">")
                file.write("<h1>Routine %s</h1>\n</div>\n</div>" % routine)
                file.write("<div class=\"contents\"><table>\n")
                for localVar in routine.getLocalVariables():
                    file.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Local Variables", localVar))
                for globalVar in routine.getGlobalVariables():
                    file.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Global Variables", gloablVar))
                for nakedGlobal in routine.getNakedGlobals():
                    file.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Naked Global", nakedGlobal))
                for markedItem in routine.getMarkedItems():
                    file.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Marked Items", nakedGlobal))
                for calledRoutine in routine.getCalledRoutines():
                    file.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                               % ("Called Routines", calledRoutine))
                # write the image of the caller graph
                file.write("<div class=\"left\"><img src=\"%s\" border=\"0\" alt=\"Call Graph\">\n" 
                           % (package+"/"+routine))


            
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
    # generate all dot file and use dot to generated the svg file format
    dotRoutineVisitor = GraphvizRoutineVisit()
    
    print "Start generating caller graph......"
    print "Time is: %s" % datetime.now()    
    for var in logParser.getAllRoutines().values():
#        dotRoutineVisitor.visitRoutine(var, "C:/Temp/VistA")
        print
    print "End of generating caller graph......"
    webPageGen=WebPageGenerator(logParse.getAllPackages(),"C:/Temp/VistA")
    webPageGen.generateWebPage()