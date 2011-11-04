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
import string
import bisect

from datetime import datetime, date, time

#===============================================================================
# output result to use graphviz to generated the graph
#===============================================================================
class GraphvizRoutineVisit(CallerGraphParser.RoutineVisit):
    def visitRoutine(self, routine, outputDir):
        if not routine.getPackage():
            print "ERROR: Routine: %s does not belongs to a package" % routineName
            return
        routineName=routine.getName()
        packageName = routine.getPackage().getName()
        calledRoutines=routine.getCalledRoutines()
        if not calledRoutines or len(calledRoutines) == 0:
            print("No called Routines found! for routine:%s package:%s") % (routineName, packageName)
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
                        output.write("\t\t%s [URL=\"%s\"];\n" % (val, getRoutineHtmlFileName(val)))
                        output.write("\t\t%s->%s;\n" % (routineName, val))
            else:
                for val in localPackage[var]:
                    output.write("\t\t%s [URL=\"%s\"];\n" % (val, getRoutineHtmlFileName(val)))
            output.write("\t\tlabel=\"Package\\n%s\";\n" % var)
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

class GraphvizPackageVisit(CallerGraphParser.PackageVisit):
    def visitPackage(self, package, outputDir):
        packageDependencies=package.getPackageDependencies()
        packageName=package.getName()
        normalizedName = normalizePackageName(packageName)
        if not packageDependencies or len(packageDependencies) == 0:
            print("No dependent Packages found! for package:%s") % (packageName)
            return                
        try:
            dirName=os.path.join(outputDir,packageName)
            if not os.path.exists(dirName):
                os.makedirs(dirName)
        except OSError:
            print "Error making dir %s : Error: %s"  % (dirName, OSError)
            return
        
        output=open(os.path.join(dirName,normalizedName+".dot"),'w')
        output.write("digraph %s {\n" % normalizedName)
        output.write("\tnode [shape=box];\n") # set the node shape to be box
        output.write("\tedge [labelfloat=true fontsize=12];\n") # set the edge label and size props
        output.write("\t%s [style=filled fillcolor=orange label=\"Package\\n%s\"];\n" % (normalizedName, packageName))
        for package in packageDependencies:
            output.write("\t%s [label=\"Package\\n%s\" URL=\"%s\"];\n" % (normalizePackageName(package.getName()), package.getName(), getPackageHtmlFileName(package.getName())))
#            output.write("\t%s->%s [label=\"depends\"];\n" % (normalizedName, normalizePackageName(package.getName())))
            output.write("\t%s->%s;\n" % (normalizedName, normalizePackageName(package.getName())))
        output.write("}\n")
        output.close()
        
        # use dot tools to generated the image and client side mapping
        outputName = os.path.join(dirName,normalizedName+".gif")
        outputmap=os.path.join(dirName, normalizedName+".cmapx")
        inputName=os.path.join(dirName,normalizedName+".dot")
        # this is to generated the image in gif format and also cmapx (client side map) to make sure link
        # embeded in the graph is clickable
        command="dot -Tgif -o\"%s\" -Tcmapx -o\"%s\" \"%s\"" % (outputName, outputmap, inputName)
#        print command
        retCode=subprocess.call(command)
        if retCode != 0:
            print "Error: calling dot with command[%s] returns %d" % (command,retCode)
            
class CplusRoutineVisit(CallerGraphParser.RoutineVisit):
    def visitRoutine(self, routine, outputDir):
        calledRoutines=routine.getCalledRoutines()
        if not calledRoutines or len(calledRoutines) == 0:
            print("No called Routines found! for package:%s") % (routineName)
            return
        routineName=routine.getName()
        if not routine.getPackage():
            print "ERROR: package: %s does not belongs to a package" % routineName
            return
        
        packageName = routine.getPackage().getName()
        try:
            dirName=os.path.join(outputDir, packageName)
            if not os.path.exists(dirName):
                os.makedirs(dirName)
        except OSError:
            print "Error making dir %s : Error: %s"  % (dirName, OSError)
            return
        
        outputFile = open(os.path.join(dirName,routineName), 'w')
        outputFile.write(("/*! \\namespace %s \n") % (packageName))
        outputFile.write("*/\n")
        outputFile.write("namespace %s {" % packageName)

        outputFile.write("/* Global Vars: */\n")            
        for var in routine.getGlobalVariables():
            outputFile.write( " int %s;\n" % var)
        outputFile.write("\n")   
        outputFile.write("/* Naked Globals: */\n")
        for var in routine.getNakeGlobals:
            outputFile.write( " int %s;\n" % var)
        outputFile.write("\n")
        outputFile.write("/* Marked Items: */\n")
        for var in routine.getMarkedItems():
            outputFile.write( " int %s;\n" % var)
        outputFile.write("\n")     
        outputFile.write("/*! \callgraph\n")
        outputFile.write("*/\n")
        outputFile.write ("void " + self.name+ "(){\n")
        
        outputFile.write("/* Local Vars: */\n")
        for var in routine.getLocalVariables():
            outputFile.write(" int %s; \n" % var)


        outputFile.write("/* Called Routines: */\n")
        for var in calledRoutines:
            outputFile.write( "  %s ();\n" % var)
        outputFile.write("}\n")        
        outputFile.write("}// end of namespace")
        outputFile.close()    
        
# utility functions
def getRoutineHtmlFileName(routineName):
    return "Routine_%s.html" % routineName

def getPackageHtmlFileName(packageName):
    return "Package_%s.html" % normalizePackageName(packageName)

def getRoutineHypeLinkByName(routineName):
    return "<a href=\"%s\">%s</a>" % (getRoutineHtmlFileName(routineName), routineName);

def getPackageHyperLinkByName(packageName):
    return "<a href=\"%s\">%s</a>" % (getPackageHtmlFileName(packageName), packageName);

def normalizePackageName(packageName):
    newName = packageName.replace(' ','_')
    return newName.replace('-',"_")
    

# generate index bar based on input list
def generateIndexBar(outputFile, inputList):
    if (not inputList) or len(inputList) == 0:
        return
    outputFile.write("<div class=\"qindex\">\n")
    for i in range(len(inputList)-1):
        outputFile.write("<a class=\"qindex\" href=\"#%s\">%s</a>&nbsp;|&nbsp;\n" % (inputList[i], inputList[i]))
    outputFile.write("<a class=\"qindex\" href=\"#%s\">%s</a></div>\n" % (inputList[-1], inputList[-1]))

# generated 
def generateIndexedPackageTableRow(outputFile, inputList):
    if not inputList or len(inputList) == 0:
        return
    outputFile.write("<tr>")
    for item in inputList:
        if item in string.uppercase:
            outputFile.write("<td><a name=\"%s\"></a><table border=\"0\" cellspacing=\"0\" cellpadding=\"0\"><tr><td><div class=\"ah\">&nbsp;&nbsp;%s&nbsp;&nbsp;</div></td></tr></table></td>" % (item, item))
        else:
            outputFile.write("<td><a class=\"el\" href=\"%s\">%s</a>&nbsp;&nbsp;&nbsp;</td>" % (getPackageHtmlFileName(item), item))
    outputFile.write("</tr>\n")

def generateIndexedRoutineTableRow(outputFile, inputList):
    if not inputList or len(inputList) == 0:
        return
    outputFile.write("<tr>")
    for item in inputList:
        if item in string.uppercase:
            outputFile.write("<td><a name=\"%s\"></a><table border=\"0\" cellspacing=\"0\" cellpadding=\"0\"><tr><td><div class=\"ah\">&nbsp;&nbsp;%s&nbsp;&nbsp;</div></td></tr></table></td>" % (item, item))
        else:
            outputFile.write("<td><a class=\"el\" href=\"%s\">%s</a>&nbsp;&nbsp;&nbsp;</td>" % (getRoutineHtmlFileName(item), item))
    outputFile.write("</tr>\n")

# class to generate the web page based on input
class WebPageGenerator:
    def __init__(self, allPackages, allRoutines, outDir):
        self.allPackages=allPackages
        self.allRoutines=allRoutines
        self.outDir=outDir
        self.header=[]
        self.footer=[]
        self.source_header=[]
        #load header and footer 
        header = open(os.path.join(self.outDir,"header.html"),'r')
        footer = open(os.path.join(self.outDir,"footer.html"),'r')
        source_header = open(os.path.join(self.outDir,"source_header.html"),'r')
        for line in header:
            self.header.append(line)
        for line in footer:
            self.footer.append(line)
        for line in source_header:
            self.source_header.append(line)
        header.close()
        footer.close()
        source_header.close()
        
    def includeHeader(self, outputFile):
        for line in self.header:
            outputFile.write(line)
            
    def includeFooter(self, outputFile):
        for line in self.footer:
            outputFile.write(line)
    
    def inlcudeSourceHeader(self, outputFile):   
        for line in self.source_header:
            outputFile.write(line)
                             
    def generateWebPage(self):
        self.generatePackageDependencies()
        self.generateRoutineIndexPage()
        self.generateCallerGraph()
        self.generatePackagePage()
        self.generateIndividualPackagePage()
        self.generateIndividualRoutinePage()
        
    # inputDir should be 
    def generateSourceCodePage(self, inputDir):
        for routineName in self.allRoutines.keys():
            packageName = self.allRoutines[routineName].getPackage().getName()
            sourcePath=os.path.join(inputDir, "Packages"+os.path.sep+packageName+os.path.sep+"Routines"+os.path.sep+routineName+".m")
            if not os.path.exists(sourcePath):
                print "Error:Souce file:[%s] does not exit\n" % sourcePath
                continue
            sourceFile=open(sourcePath,'r')
            outputFile=open(os.path.join(self.outDir, "Routine_%s_source.html" % routineName),'w')
            self.inlcudeSourceHeader(outputFile)
            outputFile.write("<div><h1>%s.m</h1></div>\n" % routineName)
            outputFile.write("<a href=\"%s\">Go to the documentation of this file.</a>" % getRoutineHtmlFileName(routineName))
            outputFile.write("<pre class=\"prettyprint lang-mumps linenums:1\">\n")
            for line in sourceFile:
                outputFile.write(line)
            outputFile.write("</pre>\n")
            self.includeFooter(outputFile)
            sourceFile.close()
            outputFile.close()
            
    
    def generateRoutineIndexPage(self):
        outputFile = open(os.path.join(self.outDir,"routines.html"),'w')  
        self.includeHeader(outputFile)
        outputFile.write("<div class=\"header\">\n")
        outputFile.write("<div class=\"headertitle\">")
        outputFile.write("<h1>Routine Index List</h1>\n</div>\n</div>")
        generateIndexBar(outputFile, string.uppercase)
        outputFile.write("<div class=\"contents\">\n")
        sortedRoutines=sorted(self.allRoutines.keys())
        for letter in string.uppercase:
            bisect.insort_left(sortedRoutines,letter)
        totalRoutines=len(sortedRoutines)
        totalCol=4
        numPerCol=totalRoutines/totalCol+1
        outputFile.write("<table align=\"center\" width=\"95%\" border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n")
        for i in range(numPerCol):
            itemsPerRow=[];
            for j in range(totalCol):
                if (i+numPerCol*j)<totalRoutines:
                    itemsPerRow.append(sortedRoutines[i+numPerCol*j]);
            generateIndexedRoutineTableRow(outputFile,itemsPerRow)        
        outputFile.write("</table>\n</div>\n")
        generateIndexBar(outputFile, string.uppercase)
        self.includeFooter(outputFile)
        outputFile.close()
        
    def generateCallerGraph(self):  
        # generate all dot file and use dot to generated the image file format
        dotRoutineVisitor = GraphvizRoutineVisit()
        print "Start generating caller graph......"
        print "Time is: %s" % datetime.now()    
        for var in self.allRoutines.values():
            dotRoutineVisitor.visitRoutine(var,self.outDir)
        print "Time is: %s" % datetime.now()
        print "End of generating caller graph......"

    def generatePackageDependencies(self):  
        # generate all dot file and use dot to generated the image file format
        dotPackageVisitor = GraphvizPackageVisit()
        print "Start generating package dependencies......"
        print "Time is: %s" % datetime.now()
        print "Total Packages: %d" % len(self.allPackages.values())  
        for package in self.allPackages.values():
            dotPackageVisitor.visitPackage(package,self.outDir)
        print "Time is: %s" % datetime.now()
        print "End of generating package dependencies......"

    def generatePackagePage(self):
        outputFile = open(os.path.join(self.outDir,"packages.html"),'w')
        self.includeHeader(outputFile)
        #write the header
        outputFile.write("<div class=\"header\">\n")
        outputFile.write("<div class=\"headertitle\">")
        outputFile.write("<h1>Package List</h1>\n</div>\n</div>")
        generateIndexBar(outputFile, string.uppercase)
        outputFile.write("<div class=\"contents\">\n")
        #generated the table
        totalNumPackages=len(self.allPackages) + len(string.uppercase)
        totalCol=3
        # list in three columns
        numPerCol=totalNumPackages/totalCol+1
        sortedPackages = sorted(self.allPackages.keys())
        for letter in string.uppercase:
            bisect.insort_left(sortedPackages,letter)
        # write the table first
        outputFile.write("<table align=\"center\" width=\"95%\" border=\"0\" cellspacing=\"0\" cellpadding=\"0\">\n")
        for i in range(numPerCol):
            itemsPerRow=[];
            for j in range(totalCol):
                if (i+numPerCol*j)<totalNumPackages:
                    itemsPerRow.append(sortedPackages[i+j*numPerCol]);
            generateIndexedPackageTableRow(outputFile,itemsPerRow)
        outputFile.write("</table>\n</div>\n")
        generateIndexBar(outputFile, string.uppercase)
        self.includeFooter(outputFile)
        outputFile.close()
    #generate the individual package pages
    def generateIndividualPackagePage(self):
        indexList=["Dependency Graph", "Package Dependencies List", "All Routines"]
        for package in sorted(self.allPackages.keys()):
            outputFile = open(os.path.join(self.outDir,getPackageHtmlFileName(package)),'w')
            #write the header part
            self.includeHeader(outputFile)
            generateIndexBar(outputFile, indexList)
            outputFile.write("<div class=\"header\">\n")
            outputFile.write("<div class=\"headertitle\">")
            outputFile.write("<h1>Package %s</h1>\n</div>\n</div>" % package)
            outputFile.write("<a name=\"Dependency Graph\"/><h2 align=\"left\">Dependency Graph</h2>")
            # write the image of the dependency graph
            try:
                cmapFile = open(os.path.join(self.outDir,package+"/"+normalizePackageName(package)+".cmapx"),'r')
                outputFile.write("<div class=\"contents\">\n")
                outputFile.write("<img src=\"%s\" border=\"0\" alt=\"Call Graph\" usemap=\"#%s\"/>\n" 
                           % (package+"/"+normalizePackageName(package)+".gif", normalizePackageName(package)))
                #append the content of map outputFile
                for line in cmapFile:
                    outputFile.write(line)  
                outputFile.write("</div>\n")
            except (IOError):
                pass         
            # write the list of the package dependency list   
            outputFile.write("<a name=\"Package Dependencies List\"/><h2 align=\"left\">Package Dependencies List</h2>\n")
            dependencyPackage=self.allPackages[package].getPackageDependencies()
            if dependencyPackage and len(dependencyPackage) > 0:
                outputFile.write("<div class=\"contents\"><table>\n")
                totalPackages=len(dependencyPackage)
                numOfCol=6
                numOfRow=totalPackages/numOfCol+1
                for index in range(numOfRow):
                    outputFile.write("<tr>")
                    for j in range(numOfCol):
                        if (index*numOfCol + j) < totalPackages:
                            outputFile.write("<td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a>&nbsp;&nbsp;&nbsp</td>" 
                                       % (getPackageHtmlFileName(dependencyPackage[index*numOfCol + j].getName()), dependencyPackage[index*numOfCol + j].getName() ))
                    outputFile.write("</tr>\n")
                outputFile.write("</table></div>\n")
            outputFile.write("<a name=\"All Routines\"/><h2 align=\"left\">All Routines</h2>\n")
            outputFile.write("<div class=\"contents\"><table>\n")
            sortedRoutines=sorted(self.allPackages[package].getAllRoutines().keys())
            totalNumRoutine = len(sortedRoutines)
            totalCol=8
            numOfRow = totalNumRoutine/totalCol+1
            if totalNumRoutine > 0:
                for index in range(numOfRow):
                    outputFile.write("<tr>")
                    for i in range(totalCol):
                        if (index*totalCol+i) < totalNumRoutine:
                            outputFile.write("<td class=\"indexkey\"><a class=\"e1\" href=\"%s\">%s</a>&nbsp;&nbsp;&nbsp;&nbsp;</td>" 
                                       % (getRoutineHtmlFileName(sortedRoutines[index*totalCol+i]), sortedRoutines[index*totalCol+i] ))
                    outputFile.write("</tr>\n")
            outputFile.write("</table>\n</div>\n<br/>")
            generateIndexBar(outputFile, indexList)
            self.includeFooter(outputFile)
            outputFile.close()

    def generateIndividualRoutinePage(self):
        print "Start generating individual Routines......"
        print "Time is: %s" % datetime.now()    
        indexList=["Source Code", "Call Graph", "Called Routines", "Local Variables", "Global Variables", "Naked Globals", "Marked Items"]       
        for package in sorted(self.allPackages.keys()):
            for routineName in sorted(self.allPackages[package].getAllRoutines().keys()):
                routine = self.allPackages[package].getAllRoutines()[routineName]
                outputFile = open(os.path.join(self.outDir,getRoutineHtmlFileName(routineName)),'w')
                # write the same header file
                self.includeHeader(outputFile)
                # generated the qindex bar
                generateIndexBar(outputFile, indexList)
                outputFile.write("<div class=\"header\">\n")
                outputFile.write("<div class=\"headertitle\">")
                outputFile.write("<h4>Package %s</h4>\n</div>\n</div>" % getPackageHyperLinkByName(package))
                outputFile.write("<h1>Routine %s</h1>\n</div>\n</div><br/>\n" % routineName)
                outputFile.write("<a name=\"Source Code\"/><h2 align=\"left\">Source Code</h2>\n")
                outputFile.write("<p><code>Source file &lt;<a class=\"el\" href=\"Routine_%s_source.html\">%s.m</a>&gt;</code></p>\n" % (routineName, routineName))
                outputFile.write("<a name=\"Call Graph\"/><h2 align=\"left\">Call Graph</h2>\n")
                calledRoutines = routine.getCalledRoutines()
                if (calledRoutines and len(calledRoutines) > 0):
                    # write the image of the caller graph
                    try:
                        cmapFile = open(os.path.join(self.outDir,package+"/"+routineName+".cmapx"),'r')
                        outputFile.write("<div class=\"contents\">\n")
                        outputFile.write("<img src=\"%s\" border=\"0\" alt=\"Call Graph\" usemap=\"#%s\"/>\n" 
                                   % (package+"/"+routineName+".gif", routineName))
                        #append the content of map outputFile
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
                        calledRoutineNameLink=calledRoutine.getName()
                        if (calledRoutine.getPackage()):
                            routinePackageLink = getPackageHyperLinkByName(calledRoutine.getPackage().getName())
                            calledRoutineNameLink = getRoutineHypeLinkByName(calledRoutineNameLink)
                        outputFile.write("<tr><td class=\"indexkey\">%s</td><td class=\"indexvalue\">%s</td></tr>\n" 
                                   % (calledRoutineNameLink, routinePackageLink))
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
                generateIndexBar(outputFile, indexList)
                self.includeFooter(outputFile)
                outputFile.close()
        print "Time is: %s" % datetime.now()
        print "End of generating individual routines......"    

def testGenerateIndexBar(inputList):
    outputFile=open("C:/Temp/VistA/Test.html", 'w')
    outputFile.write("<html><head>Test</head><body>\n")
    generateIndexBar(outputFile, inputList)
    outputFile.write("</body></html>")
    outputFile.close()

#test to play around the Dot            
def testDotCall():
    packageName="Nursing Service"
    routineName="NURA6F1"
    dirName = os.path.join("c:/temp/VistA/", packageName);
    outputName = os.path.join(dirName,routineName+".svg")
    inputName=os.path.join(dirName,routineName+".dot")
    command="dot -Tsvg -o \"%s\" \"%s\"" % (outputName, inputName)
    print "command is [%s]" % command
    retCode=subprocess.call(command)
    print "calling dot returns %d" % retCode
      
if __name__ == '__main__':
    logParser = CallerGraphParser.CallerGraphLogFileParser()
    print "Starting parsing package/package relationship...."
    print "Time is: %s" % datetime.now()
    routineFilePattern = "*/Routines/*.m"
    routineFileDir = "C:/cygwin/home/jason.li/git/VistA-FOIA/Packages/"
    logParser.findPackagesAndRoutinesBySource(routineFileDir, routineFilePattern)
    print "End parsing package/package relationship...."
    print "Time is: %s" % datetime.now()
    
    print "Starting parsing caller graph log file...."    
    callLogDir = "C:/Users/jason.li/build/VistaCache/Docs/CallerGraph"
    callLogPattern="*.log"
    logParser.parseAllCallerGraphLog(callLogDir, callLogPattern)
    print "End of parsing log file......"
    print "Time is: %s" % datetime.now()         
       
    print "Starting generating web pages...."
    print "Time is: %s" % datetime.now()
    webPageGen=WebPageGenerator(logParser.getAllPackages(), logParser.getAllRoutines(),"C:/Temp/VistA")
    sourceFileDir = "C:/cygwin/home/jason.li/git/VistA-FOIA/"
    webPageGen.generateSourceCodePage(sourceFileDir)
    webPageGen.generateWebPage()
    print "Time is: %s" % datetime.now()
    print "End of generating web pages...."