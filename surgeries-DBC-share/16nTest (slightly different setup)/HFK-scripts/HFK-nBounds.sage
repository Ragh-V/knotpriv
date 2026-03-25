f = open('mList.txt', 'r')
mList = f.readlines()
f.close()

f = open('HFKrankList.txt', 'r')
HFKrankList = f.readlines()
f.close()

nBoundList = []

#for k in range(0,len(HFKlines)):
#    if (k % 100000 == 0):
#        print(k/23432930)
#    if HFKlines[k].startswith("Total rank : "):
#        HFKrankList.append(HFKlines[k].replace("Total rank : ","").strip("\n"))

#for k in range(0,2000+0*len(HFKlines)):
#if HFKlines[k].startswith("Total rank : "):
#HFKrankList.append(HFKlines[k].replace("Total rank : ","").strip("\n"))

#with open('HFKrankList.txt', 'w') as outfile:
#    outfile.write("\n".join(HFKrankList))



for k in range(0,len(HFKrankList)):
    m = int(mList[k].strip("\n"))
    if abs(m) > 1:
        nBound = floor((int(HFKrankList[k])+abs(m)-2)/2)
    else:
        nBound = floor((int(HFKrankList[k])-1)/2)
    nBoundList.append(str(nBound))

#for k in range(0,len(HFKrankList)):
#m = int(mList[k].strip("\n"))
#nBound = floor((int(HFKrankList[k])-1)/2)
#if abs(m) > 1:
#nBound = floor((int(HFKrankList[k])+abs(m)-2)/2)
#nBoundList.append(str(nBound))

with open('nBoundList.txt', 'w') as outfile:
    outfile.write("\n".join(nBoundList))
