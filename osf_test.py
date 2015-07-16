# osf

import sys
import csv
import datetime
import re

# example usage python ./osf_test.py data_file medications_file


def main():
    params = []

    for arg in sys.argv[1:]:
        params.append(arg)
    print('Parameters:', params)

    if params != []:
        filename = params[0]
        medications = params[1]
        print(filename, medications)

        recordList = read_file(filename)
        medDict = read_meds(medications)

        check_eligibility(recordList, medDict)

    else:
        #filename = ''
        print('No file specified')


def read_file(filename):
    """
    docstring
    :rtype : list of lists (records)
    """
    print('read_file module:', filename)
    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    tempList = []
    for record in csv_reader:
        #print('record:', record)
        tempList.append(record)
    #print('tempList:', tempList)
    f.close()

    return tempList


def read_meds(medications):

    print('read_file module:', medications)
    f = open(medications, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    medDict = {}
    for key, value in csv_reader:
        medDict[key] = value
    #print('medDict:', medDict)
    f.close()

    return medDict


def check_eligibility(records, meds):

    #record_test = records[0]
    tracking = {}
    tracking['ineligible'] = 0
    tracking['eligible'] = 0

    for record in records:
        #if p01(record) == 0:
        ineligible = p01(record, meds)
        if ineligible != []:
            tracking['ineligible'] += 1
            print(ineligible)
            print("record", record[0], "- ineligible")
        else:
            tracking['eligible'] += 1
            print("record", record[0], "- looks eligible -> phone screen")
    print(tracking)

def p01(record, meds):

   # eligible = 1
    ineligible = []

    if record[6] != '':
        dob = datetime.datetime.strptime(record[6], "%m/%d/%Y").date()
        #print(dob)
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        #print("age =", today.year, "-", dob.year, "- ((",today.month,",", today.day,") < (",dob.month,",", dob.day,")))")
        #print("=", today.year, "-", dob.year, "-", ((today.month, today.day) < (dob.month, dob.day)))
        #print(age)

        if age > 13 and age < 21:
            print("age")
            #eligible = 0
            ineligible.append("age < 21")
        elif age > 65: #dob
            print("age")
            #eligible = 0
            ineligible.append("age > 65")

    if record[26] == '2': #handedness (not currently excluding ambidextrous)
        print("left handed")
        #eligible = 0
        ineligible.append("left handed")

    if record[27] == '0': #current pain -- SHOULD WE BE HOLDING THIS RATHER THAN MAKING INELIGIBLE?
        print("healthy volunteer")
        #eligible = 0
        ineligible.append("healthy volunteer")

    pain_loc_male = 0
    pain_loc_female = 0
    for i in range(28,102): #27,99
        if record[7] == '1': #male
            pain_loc_male += int(record[i])
        else:
            pain_loc_female += int(record[i+74])
        #print(i, i+74, pain_loc_male, pain_loc_female)

    #if sum of all pain locations are >0
    if (record[7] == '1' and pain_loc_male > 0) or (record[7] == '2' and pain_loc_female > 0):
        #if lower back not checked
        if (int(record[81]) + int(record[82]) + int(record[155]) + int(record[156])) == 0:
            #if pain disorder 3 not checked
            if record[179] == '0':
                #if other checkbox not checked
                if record[183] =='0':
                    print("if - not low back pain")
                    #eligible = 0
                    ineligible.append("not low back pain")
                #else if othe checkbox check and "back" not in sentence
                elif "back" not in record[185]: #doesn't have "back"
                    print("elif - 'back' not listed in other,", record[185])
                    #eligible = 0
                    ineligible.append("not low back pain")


    if record[176] == '1': #pain duration (not currently excluding intermittent)
        print("pain duration")
        #eligible = 0
        ineligible.append("pain < 3 months")

    if record[178] == '1': #other pain disorder (FM)
        print("FM")
        #eligible = 0
        ineligible.append("other pain condition - FM")

    if record[180] == '1': #other pain disorder (CRPS)
        print("CRPS")
        #eligible = 0
        ineligible.append("other pain condition - CRPS")

    if record[181] == '1': #other pain disorder (PP)
        print("PP")
        #eligible = 0
        ineligible.append("other pain condition - PP")

    if record[182] == '1': #other pain disorder (Migraine)
        print("Migraine")
        #eligible = 0
        ineligible.append("other pain condition - migraine")

    if record[188] != '':
        if int(record[188]) < 4: #NRS
            print("NRS")
            #eligible = 0
            ineligible.append("NRS < 4")

    if record[190] != '':
        med_ineligible = check_meds(record, meds)
        if med_ineligible != []:
            print("Medications")
            ineligible.extend(med_ineligible)


    return ineligible


def check_meds(record, meds):

    ineligible = []
    if record[190] != '':
        #extract medications as a list?
        med_list = re.split(r'[,.\s]\s*', record[190])

        for i in med_list:
            if i in meds.keys():
                reason = i + " - " + meds[i]
                ineligible.append(reason)
        #print("Medications:", ineligible)

    return ineligible





if __name__ == '__main__':
   main()