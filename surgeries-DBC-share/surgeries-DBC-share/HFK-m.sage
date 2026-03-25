from tqdm import tqdm
import snappy

f = open("numDTList.txt", "r")
numDTList = f.readlines()
f.close()

mList=[]
tauList=[]
epsilonList=[]
HFKrankList=[]

for k in tqdm(range(0,len(numDTList))):
    K=snappy.Link('DT: [('+numDTList[k].strip("\n")+')]')
    S=K.knot_floer_homology()
    tau = S['tau']
    epsilon = S['epsilon']
    HFKrank = S['total_rank']
    m = 2*tau - epsilon
    mList.append(str(m))
    tauList.append(str(tau))
    epsilonList.append(str(epsilon))
    HFKrankList.append(str(HFKrank))

with open('mList.txt','w') as outfile: 
    outfile.write('\n'.join(mList))  

with open('tauList.txt','w') as outfile: 
    outfile.write('\n'.join(tauList)) 

with open('epsilonList.txt','w') as outfile: 
    outfile.write('\n'.join(epsilonList))    

with open('HFboundList.txt','w') as outfile: 
    outfile.write('\n'.join(HFKrankList))