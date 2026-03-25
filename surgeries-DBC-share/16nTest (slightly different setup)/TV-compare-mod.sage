# This should live in a directory with the supporting data files (mainly "failList.txt"). 

maxtime = 1.4   # This limits the amount of time the script is allowed to spend calculating the Turaev-Viro invariants of the double branched cover of a knot K. (There is some seemingly random variability in this calculation time, even when inputting the same knot repeatedly. The time taken for the subsequent calculations of T-V invariants for surgeries on K seems to scale with the calculation time for the branched cover.)

import snappy
import regina
import math
import os.path
import copy
import time

knotList = []
DTList = []
pList = []
qList = []


# Check if there's a working list of knots and slopes. If not, generate this working list based on the list of failed slopes (in "failList.txt") from HF-Casson-compare.

if (os.path.exists("whatsLeft.txt") == False):
    with open('failList.txt', 'r') as firstfile, open('whatsLeft.txt', 'w') as secondfile:
        for line in firstfile:
            secondfile.write(line)

if (os.path.exists("exceptions.txt") == False):
    f = open('exceptions.txt', 'w')
    f.close()

# Load the (existing) working list.

f = open('whatsLeft.txt', 'r')
whatsLeftPrevious = f.readlines()
f.close()

f = open('exceptions.txt', 'r')
exceptions = f.readlines()
f.close()

# Now we'll make a new working list that eliminates any cases completed by a previous iteration of this script.

whatsLeft = []

for x in whatsLeftPrevious:
    if (x != "Done!\n"):
        whatsLeft.append(copy.deepcopy(x))
        data = x.strip("\n").split(";")
        knotList.append(data[0].strip(" "))
        DTList.append(data[1].strip(" "))
        pList.append(int(data[2].strip(" p = ")))
        qstrings = data[3].strip(" q = ").strip("[").strip("]").split(',')
        qvals = []
        for i in range(0,len(qstrings)):
            qvals.append(int(qstrings[i]))
        qList.append(qvals)

with open('whatsLeft.txt', 'w') as outfile:
    outfile.writelines(whatsLeft)

progress_report = []
output_log = []



if (os.path.exists('progress.txt') == False):
    with open('progress.txt', 'w') as outfile:
        outfile.write("Preparing to compare Turaev-Viro invariants of DBC's and surgeries for the given knots.")

f = open('progress.txt', 'r')
progressLines = f.readlines()
f.close()

# [Explain what's happening here.]

state1 = "[working on T-V invariant of DBC]"
state2 = "[working on T-V invariant of surgery]"
state0 = "[moving on to next knot]"

state = 0

if state1 in progressLines[-1]:
    state = 1

if state2 in progressLines[-1]:
    state = 2
    del progressLines[-1]

with open('progress.txt', 'w') as outfile:
    outfile.writelines(progressLines)

newqList = copy.deepcopy(qList)

# [put comments in below to indicate when a progress update is happening.]

for k in range(0,len(knotList)):
    fail = 0
    p = pList[k]
    turaevViroCalculated = 0
    print(knotList[k])
    comment = "\n"+"Calculating Turaev-Viro invariants for K = "+str(knotList[k])
    progress_report.append(comment)
    if (state == 0):
        progressLines.append(comment+"\n")
        state = 1
        progressLines.append(state1)
        with open('progress.txt', 'w') as outfile:
            outfile.writelines(progressLines)            
#    K=snappy.Manifold(DTList[k])
    K=snappy.Manifold(knotList[k])
    if (turaevViroCalculated == 0):
        C=K.covers(2)[0]
        C.dehn_fill((1,0),0)
        C.simplify()
        Cfill=C.filled_triangulation()
        Cfill.simplify()
        isosigCover=Cfill.triangulation_isosig()
        CoverTri=regina.Triangulation3.fromIsoSig(isosigCover)
        CoverTri.intelligentSimplify()
        starttime=time.time()
        tvCover = CoverTri.turaevViro(5,alg=regina.ALG_TREEWIDTH)
        turaevViroCalculated = 1
        print(tvCover)
        endtime = time.time()
        runtime = endtime - starttime
        print(runtime)
        if runtime > maxtime:
            print("Too slow! Restarting.") #A slow computation of the cover's TV-invariant is a bad sign, so we throw it out and start again.
            break
        comment = "T-V of DBC is "+str(tvCover)
        progress_report.append(comment)
        if (state == 1):
            progressLines[-1] = comment+"\n"
            state = 2
            with open('progress.txt', 'w') as outfile:
                outfile.writelines(progressLines)            
    for q in qList[k]:
        progressLines.append(state2)
        with open('progress.txt', 'w') as outfile:
            outfile.writelines(progressLines)
        state = 2
        Y=K
        Y.dehn_fill((p,q),0)
        Y.simplify()
        Yfill=Y.filled_triangulation()
        Yfill.simplify()
        isosigSurgery=Yfill.triangulation_isosig()
        SurgeryTri=regina.Triangulation3.fromIsoSig(isosigSurgery)
        SurgeryTri.intelligentSimplify()
        SurgeryTri.intelligentSimplify()
        SurgeryTri.intelligentSimplify()
        tvSurgery = SurgeryTri.turaevViro(5,alg=regina.ALG_TREEWIDTH)
        print(tvSurgery)
        comment = "T-V of surgery with q = "+str(q)+" is "+str(tvSurgery)
        progress_report.append(comment)
        progressLines[-1] = comment+"\n"
        with open('progress.txt', 'w') as outfile:
            outfile.writelines(progressLines)
        if (tvSurgery == tvCover):
            if fail == 0:
                fail_values = []
                fail = 1
            temp='Failed to distinguish using Turaev-Viro invariants; for q = '+str(q)+'; both Turaev-Viro invariants equal'+str(tvSurgery)
            output_log.append(temp)
            with open('progress.txt', 'a') as outfile:
                outfile.write("\n")
                outfile.write(temp)
            exceptions.append(str(knotList[k])+"; "+DTList[k]+"; p = "+str(p)+"; q = "+str(q)+"\n")
            with open('exceptions.txt', 'w') as outfile:
                outfile.writelines(exceptions)
            fail = 1
            fail_values.append(q)
            newqList[k].remove(q)
            whatsLeft[k] = str(knotList[k])+"; "+DTList[k]+"; p = "+str(p)+"; q = "+str(newqList[k])+"\n"
            with open('whatsLeft.txt', 'w') as outfile:
                outfile.writelines(whatsLeft)
        else:
            newqList[k].remove(q)
            whatsLeft[k] = str(knotList[k])+"; "+DTList[k]+"; p = "+str(p)+"; q = "+str(newqList[k])+"\n"
            with open('whatsLeft.txt', 'w') as outfile:
                outfile.writelines(whatsLeft)
        if newqList[k] == []:
            whatsLeft[k] = "Done!"+"\n"
            with open('whatsLeft.txt', 'w') as outfile:
                outfile.writelines(whatsLeft)
    if fail == 0:
        progressLines.append("Successfully distinguished remaining surgeries from DBC."+"\n")
        with open('progress.txt', 'w') as outfile:
            outfile.writelines(progressLines)
    state = 0


quit