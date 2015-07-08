# osf

import sys
import csv
import datetime

# example usage ./osf_test.py

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
        print('record:', record)
        tempList.append(record)
    print('tempList:', tempList)
    f.close()
    return tempList


def check_eligibility(records):

    #record_test = records[0]
    for record in records:
        if p01(record) == 0:
            print("record", record[0], "- ineligible")
        else:
            print("record", record[0], "- looks eligible -> phone screen")


def p01(record):

    eligible = 1

    dob = datetime.datetime.strptime(record[6], "%m/%d/%Y").date()
    #print(dob)
    today = datetime.date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    #print("age =", today.year, "-", dob.year, "- ((",today.month,",", today.day,") < (",dob.month,",", dob.day,")))")
    #print("=", today.year, "-", dob.year, "-", ((today.month, today.day) < (dob.month, dob.day)))
    #print(age)

    if (age > 13 and age < 21) or (age > 65): #dob
        print("age")
        eligible = 0

    if record[26] == '2': #handedness (not currently excluding ambidextrous)
        print("handedness")
        eligible = 0

    if record[27] == '0': #current pain
        print("current pain")
        eligible = 0

    pain_loc_male = 0
    pain_loc_female = 0
    for i in range(28,102): #27,99
        if record[7] == '1': #male
            pain_loc_male += int(record[i])
        else:
            pain_loc_female += int(record[i+74])
        print(i, i+74, pain_loc_male, pain_loc_female)

    #if sum of all pain locations are >0
    if (record[7] == '1' and pain_loc_male > 0) or (record[7] == '2' and pain_loc_female > 0):
        #if lower back not checked
        if (int(record[81]) + int(record[82]) + int(record[155]) + int(record[156])) == 0:
            #if pain disorder 3 not checked
            if record[179] == '0':
                #if other checkbox not checked
                if record[183] =='0':
                    print("if - not low back pain")
                    eligible = 0
                #else if othe checkbox check and "back" not in sentence
                elif "back" not in record[185]: #doesn't have "back"
                    print("elif - 'back' not listed in other,", record[185])
                    eligible = 0



    if record[176] == '1': #pain duration (not currently excluding intermittent)
        print("pain duration")
        eligible = 0

    if record[178] == '1': #other pain disorder (FM)
        print("FM")
        eligible = 0

    if record[180] == '1': #other pain disorder (CRPS)
        print("CRPS")
        eligible = 0

    if record[181] == '1': #other pain disorder (PP)
        print("PP")
        eligible = 0

    if record[182] == '1': #other pain disorder (Migraine)
        print("Migraine")
        eligible = 0

    if record[188] != '':
        if int(record[188]) < 4: #NRS
            print("NRS")
            eligible = 0

    return eligible


def main():
    params = []

    for arg in sys.argv[1:]:
        params.append(arg)
    print('Parameters:', params)

    if params != []:
        filename = params[0]
        print(filename)

        recordList = read_file(filename)

        check_eligibility(recordList)

    else:
        #filename = ''
        print('No file specified')

if __name__ == '__main__':
   main()