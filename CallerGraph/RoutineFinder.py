import CallerGraphParser
from datetime import datetime, date, time
if __name__ == '__main__':
#    CallerGraphParser.testDotCall()
#    exit()
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
    # read the user input from the terminal
    isExit=False
    while not isExit:
        var = raw_input("Please enter the routine Name:")
        if (var == 'quit'):
            isExit=True
            break
        else:
            logParser.printRoutine(var)