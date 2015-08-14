#!/usr/bin/env python

import sys
import csv
import datetime
import re
from redcap import Project

# example usage: python ./osf.py ineligiblity_file medications_file
# usage in osf directory: python ./osf.py ../../../Desktop/P01_IneligibilityReasons2.csv ../../../Desktop/P01_Medications.csv


def main():
    params = []

    for arg in sys.argv[1:]:
        params.append(arg)
    print('Parameters:', params)

    if params != []:
        
        reasons = params[0]
        medications = params[1]
        #print(reasons, medications)
        
        api_url = 'https://redcap-demo.stanford.edu/api/'
        api_key = 'B2586BF6214D752F17ADF208244EFAE4'
        project = Project(api_url, api_key)
        record = export_record(project)
        print("finished with record export module")
        #print(record)
        #print("sorted", sorted(record.keys()))
        ineligibilityDict = read_to_dict(reasons)
        medDict = read_to_dict(medications)

        newRecord = check_eligibility(record, ineligibilityDict, medDict)
        #print("new record:", newRecord)
        import_record(newRecord, project)

    else:
        #filename = ''
        print('No file specified')


def export_record(project):

    print('export_record module:')
    '''
    api_url = 'https://redcap-demo.stanford.edu/api/'
    api_key = 'B2586BF6214D752F17ADF208244EFAE4'
	
    project = Project(api_url, api_key)
    '''
    print("FORMS:", project.forms)
    forms_subset = ['online_screening_form', 'p01_cam_center_phone_screen']
    #forms = project.forms[0]
    #forms_subset = project.export_records(forms=forms)
    record = project.export_records(forms=forms_subset)
    #record = project.export_records()
    print("record exported, # of keys:", len(record[0].keys()))
    #record = []
    return record[0] # return dict of single record


def read_to_dict(filename):

    print('read_to_dict module:', filename)
    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    newDict = {}
    for key, value in csv_reader:
        newDict[key] = value
    print('newDict:', newDict)
    f.close()

    return newDict


def check_eligibility(record, ineligibilityDict, meds):

    ineligible = p01(record, meds)
    if ineligible != []:
        print(ineligible)
        print("record", record['record_id'], "- ineligible")
        newRecord = update_phone_screen(record, ineligible, ineligibilityDict)
    else:
        print("record", record['record_id'], "- looks eligible -> phone screen")
        newRecord = record
    #print("newRecord:", newRecord)

    return newRecord


def p01(record, meds):

    ineligible = []

    if record['dob'] != '':
        dob = datetime.datetime.strptime(record['dob'], "%Y-%m-%d").date()
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

    if record['handedness'] == '2': #handedness (not currently excluding ambidextrous)
        print("left handed")
        #eligible = 0
        ineligible.append("MRI: Left-handed")
       # call to mark as ineligible function here - update phone screen

    if record['currentpain'] == '0': #current pain -- SHOULD WE BE HOLDING THIS RATHER THAN MAKING INELIGIBLE?
        print("healthy volunteer")
        #eligible = 0
        ineligible.append("Healthy Control")
       # call to mark as ineligible function here - update phone screen

    pain_loc_male = 0
    pain_loc_female = 0
	
	#### BELOW LOGIC DOESN'T WORK ANYMORE 
    '''
	for i in range(28,102): #27,99
        if record['gender'] == '1': #male
            pain_loc_male += int(record[i])
        else:
            pain_loc_female += int(record[i+74])
        #print(i, i+74, pain_loc_male, pain_loc_female)
	'''
	
	#CHECK NEW LOGIC
    for i in range(1,10): 
        if record['gender'] == '1': #male
            fkey = 'painlocation_male___f0' + str(i)
            print("fkey", fkey)
            pain_loc_male += int(record[fkey])
            bkey = 'painlocation_male___b0' + str(i)
            print("bkey", bkey)
            pain_loc_male += int(record[bkey])
        else:
            fkey = 'painlocation_female___f0' + str(i)
            print("fkey", fkey)
            pain_loc_female += int(record[fkey])
            bkey = 'painlocation_female___b0' + str(i)
            print("bkey", bkey)
            pain_loc_female += int(record[bkey])
    for i in range(10,37): # checks up to 36, there are 37 and 38 for male/female back or front (i.e. some aren't checked)
        if record['gender'] == '1': #male
            fkey = 'painlocation_male___f' + str(i)
            print("fkey", fkey)
            pain_loc_male += int(record[fkey])
            bkey = 'painlocation_male___b' + str(i)
            print("bkey", bkey)
            pain_loc_male += int(record[bkey])
        else:
            fkey = 'painlocation_female___f' + str(i)
            print("fkey", fkey)
            pain_loc_female += int(record[fkey])
            bkey = 'painlocation_female___b' + str(i)
            print("bkey", bkey)
            pain_loc_female += int(record[bkey])
    print(pain_loc_male, pain_loc_female)
    #if sum of all pain locations are >0
    if (record['gender'] == '1' and pain_loc_male > 0) or (record['gender'] == '2' and pain_loc_female > 0):
        #if lower back not checked
        if (int(record['painlocation_male___b18']) + int(record['painlocation_male___b19']) + int(record['painlocation_female___b18']) + int(record['painlocation_female___b19'])) == 0:
            #if pain disorder 3 not checked
            if record['paindisorder___3'] == '0':
                #if other checkbox not checked
                if record['paindisorder___7'] =='0':
                    print("if - not low back pain")
                    #eligible = 0
                    ineligible.append("Not Low Back Pain")
                    # call to mark as ineligible function here - update phone screen
                #else if other checkbox checked and "back" not in sentence
                elif "back" not in record['paindisorder_other']: #doesn't have "back"
                    print("elif - 'back' not listed in other,", record[185])
                    #eligible = 0
                    ineligible.append("Not Low Back Pain")
                   # call to mark as ineligible function here - update phone screen


    if record['painduration'] == '1': #pain duration (not currently excluding intermittent)
        print("pain duration < 3 months")
        #eligible = 0
        ineligible.append("No Chronic Pain")
       # call to mark as ineligible function here - update phone screen
    
    if record['paindisorder___1'] == '1': #recent surgery
        print("recent surgery")
        ineligible.append("Other Pain: Recent Surgery")
		
    if record['paindisorder___2'] == '1': #other pain disorder (FM)
        print("FM")
        #eligible = 0
        ineligible.append("Other Pain Condition: FM")
       # call to mark as ineligible function here - update phone screen

    if record['paindisorder___4'] == '1': #other pain disorder (CRPS)
        print("CRPS")
        #eligible = 0
        ineligible.append("Other Pain Condition: CRPS")
       # call to mark as ineligible function here - update phone screen

    if record['paindisorder___5'] == '1': #other pain disorder (PP)
        print("PP")
        #eligible = 0
        #ineligible.append("Other Pain Condition: PP")
        ineligible.append("Other Pain: Pelvic")
       # call to mark as ineligible function here - update phone screen --> Other pain: pelvic? (no other pain condition: PP option)

    if record['paindisorder___6'] == '1': #other pain disorder (Migraine)
        print("Migraine")
        #eligible = 0
        ineligible.append("Other Pain Condition: Migraines")
       # call to mark as ineligible function here - update phone screen

    if record['painscore_avg'] != '': #NRS
        nrs = record['painscore_avg']
        if (int(nrs) < 4) and (int(nrs) > 0):
            print("NRS")
            #eligible = 0
            ineligible.append("NRS: " + nrs)
           # call to mark as ineligible function here - update phone screen

    if record['medication_list'] != '':
        med_ineligible = check_meds(record['medication_list'], meds)
        if med_ineligible != []:
            print("Medications")
            ineligible.extend(med_ineligible)
           # call to mark as ineligible function here - update phone screen


    return ineligible


def check_meds(record_meds, meds):

    ineligible = []
    #if record[190] != '':
    #extract medications as a list?
    med_list = re.split(r'[,.\s]\s*', record_meds)
    print("med list", med_list)

    for i in med_list:
        #print("listed med", i)
        i = i.lower()
        #print("lowercase", i)
        if i in meds.keys():
            #reason = i + " - " + meds[i]
            #ineligible.append(reason)
            #print("problem med", i)
            ineligible.append(meds[i])
    #print("Medications:", ineligible)

    return ineligible


def update_phone_screen(record, ineligible, ineligibilityDict):

    #record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    
	### CAN THE BELOW BE DONE WITH A DICT EXPORT?????
	#record[225] = 2 # mark admin panel as complete

    #record['cmtps_date'] = str(datetime.datetime.now())
    record['cmtps_conductedby'] = 'Automatic screen program'
    record['cmtps_eligstatus'] = 2 # mark phone screen as failure
    
	
	### CAN THE BELOW BE DONE WITH A DICT EXPORT?????
    record['p01_cam_center_phone_screen_complete'] = 2 # mark phone screen as complete

	#### CHECK NEW LOGIC BELOW
    for reason in ineligible: # update failure reasons
        i = ineligibilityDict[reason]
        key = 'cmtps_noteligreasons___' + i
        #print("error:", i)
        record[key] = 1
        # NOTE: not currently including list of medications provided in OSF (could put this in eligibility notes)

    return record
    # write and save to a new csv file

'''
def write_file(records):

    with open('../../../Desktop/output.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(records)

'''

def import_record(record, project):
    #forms_subset = ['online_screening_form', 'p01_cam_center_phone_screen']
    to_import = []
    to_import.append(record)
    response = project.import_records(to_import)
    print("response", response)
    return response



if __name__ == '__main__':
   main()