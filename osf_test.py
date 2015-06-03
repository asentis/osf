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
        eligible = 0

    if record[23] == '2': #handedness (not currently excluding ambidextrous)
        eligible = 0

    if record[24] == '0': #current pain
        eligible = 0

    if record[173] == '1': #pain duration (not currently excluding intermittent)
        eligible = 0

    if record[175] == '1': #other pain disorder (FM)
        eligible = 0

    if record[177] == '1': #other pain disorder (CRPS)
        eligible = 0

    if record[178] == '1': #other pain disorder (PP)
        eligible = 0

    if record[179] == '1': #other pain disorder (Migraine)
        eligible = 0

    if record[184] != '':
        if int(record[184]) < 4: #NRS
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