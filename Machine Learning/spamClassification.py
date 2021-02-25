
import re
import os
import numpy as np
import math
import sys 



# # Words processing
trainSet = sys.argv[1]
testSet = sys.argv[2]
outputSet = sys.argv[3]

entriesNonSpam = os.listdir(trainSet+"notspam")
entriesSpam = os.listdir(trainSet+"spam")


# for item in entriesNonSpam, transfer them to txt file for eaiser word processing
for item in entriesNonSpam:
    itemSource = "train/notspam/"+item
    itemDest = "train/notspam/"+item+".txt"
    os.rename(itemSource, itemDest)

for item in entriesSpam:
    itemSource = "train/spam/"+item
    itemDest = "train/spam/"+item+".txt"
    os.rename(itemSource, itemDest)



nonSpamList = []
spamList = []

allWords = []
documents = [] #lists of list of email words
classes = []

regEx = re.compile('\\W*')
nonScounter = 0
for item in entriesNonSpam:
    f = open(trainSet+"notspam/"+str(item), 'r', errors='ignore').read()
    listWords = regEx.split(f)
    cleanWords = [word.lower() for word in listWords if len(word) > 2 and len(word) < 14]
    while 'tilocblob' in cleanWords: cleanWords.remove('tilocblob')
    documents.append(cleanWords)
    classes.append(0)
    nonSpamList.extend(cleanWords)
    if(nonScounter == 50):
        break
    else:
        nonScounter += 1

allWords.extend(nonSpamList)

sCounter = 0
for item in entriesSpam:
    if not item.startswith('cmds'):
        f = open(trainSet+"spam/"+str(item), 'r', errors='ignore').read()
        listWords = regEx.split(f)
        cleanWords = [word.lower() for word in listWords if len(word) > 2 and len(word)< 14]
        while 'tilocblob' in cleanWords: cleanWords.remove('tilocblob')
        documents.append(cleanWords)
        classes.append(1)
        spamList.extend(cleanWords)
        if(sCounter == 500):
            break
        else:
            sCounter += 1

allWords.extend(spamList) #a single word might appears multi times

allWordsSet = set(allWords)
allWordsList = list(allWordsSet) #all words only appears once





def bagOfWordsVec(inputs):
    wordbagVec = np.ones((1, len(allWordsList)))
    for item in inputs:
        if item in allWordsList:    
            wordbagVec[0][allWordsList.index(item)] += 1
    return wordbagVec




def training(vectors, clesses):
    pSpam = np.sum(classes)/float(len(vectors))
    p0 = np.ones((1, len(allWordsList)))
    p1 = np.ones((1, len(allWordsList)))
    p0D = 2.0
    p1D = 2.0

    for i in range(len(vectors)):
        if classes[i] == 1:
            p1 += vectors[i]
            p1D += np.sum(vectors[i])
        else:
            p0 += vectors[i]
            p0D += np.sum(vectors[i])

    p1V = np.log(p1/p1D)
    p0V = np.log(p0/p0D)

    return p0V, p1V, pSpam


collections = []

def classfication(vector, p0V, p1V, ps):
    p1 = np.sum(vector * p1V) + math.log(ps)
    p0 = np.sum(vector * p0V) + math.log(1.0 - ps)

    comparsion = p1/p0

    if comparsion > 1.007:
        return "spam", comparsion
    else:
        return "notspam", comparsion

#testing words processing:
testingEmails = os.listdir(testSet)
for item in testingEmails:
    itemSource = testSet+item
    itemDest = testSet+item+".txt"
    os.rename(itemSource, itemDest)

testingDocs = []
for item in testingEmails:
    f = open(testSet+"/"+str(item), 'r', errors='ignore').read()
    listWords = regEx.split(f)
    cleanWords = [word.lower() for word in listWords if len(word) > 2 and len(word) < 14]
    while 'tilocblob' in cleanWords: cleanWords.remove('tilocblob')
    testingDocs.append(cleanWords)





def testing():
    trainMatrix = []
    for doc in documents:
        trainMatrix.append(bagOfWordsVec(doc))
    p0v, p1v, ps = training(trainMatrix, classes) #potential problem here "classes"

    for i in range(2554):
        docVector = bagOfWordsVec(testingDocs[i]) 
        fileName = testingEmails[i]
        result, compRatio = classfication(docVector, p0v, p1v, ps)
        output1 = os.path.splitext(fileName)[0]
        output2 = result
        f = open(outputSet, 'a')
        output = output1 + " " + output2 + '\n'
        f.write(output)
        
testing()