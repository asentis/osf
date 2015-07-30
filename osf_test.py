# osf

import sys
import csv
import datetime
import re

# example usage python ./osf_test.py data_file ineligiblity_file


def main():
    params = []

    for arg in sys.argv[1:]:
        params.append(arg)
    print('Parameters:', params)

    if params != []:
        filename = params[0]
        reasons = params[1]
        medications = params[2]
        print(filename, reasons, medications)

        recordList = read_file(filename)
        ineligibilityDict = read_to_dict(reasons)
        medDict = read_to_dict(medications)

        check_eligibility(recordList, medDict)

    else:
        #filename = ''
        print('No file specified')


def read_file(filename):
    """
    docstring
    :rtype : list of lists (records)
    """
    #print('read_file module:', filename)
    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    tempList = []
    for record in csv_reader:
        #print('record:', record)
        tempList.append(record)
    #print('tempList:', tempList)
    f.close()

    return tempList


"""
def read_ineligibility(reasons):

    # read into a dict with the key = ineligibility reason and value = column in phone screen failure section to mark
    print('read_ineligibility module:', reasons)
    f = open(reasons, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    ineligibilityList = []
    for reason in csv_reader:
        ineligibilityList += reason
    print('ineligibilityList:', ineligibilityList)
    f.close()

    return ineligibilityList
"""

def read_to_dict(filename):

    #print('read_to_dict module:', filename)
    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    newDict = {}
    for key, value in csv_reader:
        newDict[key] = value
    #print('newDict:', newDict)
    f.close()

    return newDict


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
            # call to mark as ineligible function here - update admin panel, "phone screened by" section with 'program' and current date/time\
            #update_record(ineligible)
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
            ineligible.append("Age < 21 years old")
            # call to mark as ineligible function here - update phone screen

        elif age > 65: #dob
            print("age")
            #eligible = 0
            ineligible.append("Age > 65 years old")
           # call to mark as ineligible function here - update phone screen

    if record[26] == '2': #handedness (not currently excluding ambidextrous)
        print("left handed")
        #eligible = 0
        ineligible.append("Left-handed")
       # call to mark as ineligible function here - update phone screen

    if record[27] == '0': #current pain -- SHOULD WE BE HOLDING THIS RATHER THAN MAKING INELIGIBLE?
        print("healthy volunteer")
        #eligible = 0
        ineligible.append("Healthy Control")
       # call to mark as ineligible function here - update phone screen

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
                    ineligible.append("Not Low Back Pain")
                    # call to mark as ineligible function here - update phone screen
                #else if othe checkbox check and "back" not in sentence
                elif "back" not in record[185]: #doesn't have "back"
                    print("elif - 'back' not listed in other,", record[185])
                    #eligible = 0
                    ineligible.append("Not Low Back Pain")
                   # call to mark as ineligible function here - update phone screen


    if record[176] == '1': #pain duration (not currently excluding intermittent)
        print("pain duration < 3 months")
        #eligible = 0
        ineligible.append("No Chronic Pain")
       # call to mark as ineligible function here - update phone screen

    if record[178] == '1': #other pain disorder (FM)
        print("FM")
        #eligible = 0
        ineligible.append("Other Pain Condition: FM")
       # call to mark as ineligible function here - update phone screen

    if record[180] == '1': #other pain disorder (CRPS)
        print("CRPS")
        #eligible = 0
        ineligible.append("Other Pain Condition: CRPS")
       # call to mark as ineligible function here - update phone screen

    if record[181] == '1': #other pain disorder (PP)
        print("PP")
        #eligible = 0
        ineligible.append("Other Pain Condition: PP")
       # call to mark as ineligible function here - update phone screen --> Other pain: pelvic? (no other pain condition: PP option)

    if record[182] == '1': #other pain disorder (Migraine)
        print("Migraine")
        #eligible = 0
        ineligible.append("Other Pain Condition: Migraines")
       # call to mark as ineligible function here - update phone screen

    if record[188] != '': #NRS
        nrs = record[188]
        if int(nrs) < 4:
            print("NRS")
            #eligible = 0
            ineligible.append("NRS: " + nrs)
           # call to mark as ineligible function here - update phone screen

    if record[190] != '':
        med_ineligible = check_meds(record, meds)
        if med_ineligible != []:
            print("Medications")
            ineligible.extend(med_ineligible)
           # call to mark as ineligible function here - update phone screen


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


#def update_record(ineglible):

   # for reason in ineligible:
      #  if reason



if __name__ == '__main__':
   main()