#!/usr/bin/env python

import sys
import csv
import datetime
import re
from redcap import Project

# example usage: python ./osf.py ineligiblity_file medications_file
# usage in osf directory: python ./osf.py ../../../Desktop/P01_IneligibilityReasons2.csv ../../../Desktop/P01_Medications.csv ../../../Desktop/RecordIDs.csv


def main():
    params = []

    for arg in sys.argv[1:]:
        params.append(arg)
    print('Parameters:', params)

    if params != []:
        
        reasons_file = params[0]
        medications_file = params[1]
        records_file = params[2]
        
        recordsList = read_file(records_file)
        
        #api_url = 'https://redcap-demo.stanford.edu/api/'
        #api_key = 'key'
        
        api_url = 'https://redcap.stanford.edu/api/'
        api_key = 'key'
        project = Project(api_url, api_key)
        records = export_record(project, recordsList)
        #print(record)
        #print("sorted", sorted(records[0].keys()))
        
        ineligibilityDict = read_to_dict(reasons_file)
        medDict = read_to_dict(medications_file)
        

        newRecords = check_eligibility(records, ineligibilityDict, medDict)
        #print("sorted newRecords", sorted(newRecords[0].keys()))
        import_record(newRecords, project)

    else:
        #filename = ''
        print('No file specified')

       
def read_file(filename):
    
    print('read_file module:', filename)
    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    recordList = []
    for record in csv_reader:
        #print('record:', record)
        recordList.append(record[0])
    print('recordList:', recordList)
    f.close()

    return recordList

    
def export_record(project, recordsList):
    
    #print("FORMS:", project.forms)
    #id = ['2', '3', '9']
    
    #forms_subset = ['online_screening_form', 'p01_cam_center_phone_screen']
    forms_subset = ['online_screening_form', 'cbp_phone_screen']
    
    records = project.export_records(records=recordsList, forms=forms_subset)
    #print("record exported, # of keys:", len(record[0].keys()))
	
    return records # return dict of single record (last record)
    
    
def read_to_dict(filename):

    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    newDict = {}
    for key, value in csv_reader:
        newDict[key] = value
    #print('newDict:', newDict)
    f.close()

    return newDict


def check_eligibility(records, ineligibilityDict, meds):

    newRecordList = []
    num_inelig = 0
    num_hold = 0
    num_elig = 0
    
    for record in records:
        
        #record = check_data(record)
        
        ineligible, hold, problem_meds = p01(record, meds)
        if ineligible != []:
            print(ineligible)
            print("record", record['record_id'], "- ineligible")
            newRecord = update_ps_inelig(record, ineligible, ineligibilityDict, problem_meds)
            num_inelig += 1
        elif hold != []:
            print(hold)
            print("record", record['record_id'], "- on hold")
            newRecord = update_ps_hold(record, hold)
            num_hold += 1
        else:
            print("record", record['record_id'], "- looks eligible -> phone screen")
            #newRecord = record
            newRecord = update_ps_elig(record)
            num_elig += 1
        
        newRecordList.append(newRecord)
    
    print("ineligible: ", num_inelig, "hold: ", num_hold, "eligible: ", num_elig)
    return newRecordList

'''
def check_data(record):

    digits = len(record['contact_phone'])
    if digits > 10:
        if digits == 11 and record['contact_phone'][0] == '1':
            print("phone", record['contact_phone'])
            new_phone = record['contact_phone'][1:]
            print("new phone", new_phone)
            record['contact_phone'] = new_phone
        else:
            print("phone", record['contact_phone'])
            new_phone = record['contact_phone'][-10:]
            print("new phone", new_phone)
            record['contact_phone'] = new_phone
    elif digits < 10:
        print("phone", record['contact_phone'])
        padding = ''
        for i in range(0,10-digits):
            padding += '0'
        new_phone = record['contact_phone'] + padding
        print("new phone", new_phone)
        record['contact_phone'] = new_phone
    
    return record
'''

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
            #print("age")
            ineligible.append("Age < 21 years old")
        elif age > 65: #dob
            #print("age")
            ineligible.append("Age > 65 years old")
    
    if record['gender'] == '3' or record['gender'] == '4':
        #print("Gender")
        ineligible.append("Gender Variant")
    else:
        pain_loc_male = 0
        pain_loc_female = 0

        for i in range(1,10): 
            if record['gender'] == '1': #male
                fkey = 'painlocation_male___f0' + str(i)
                #print("fkey", fkey)
                pain_loc_male += int(record[fkey])
                bkey = 'painlocation_male___b0' + str(i)
                #print("bkey", bkey)
                pain_loc_male += int(record[bkey])
            else:
                fkey = 'painlocation_female___f0' + str(i)
                #print("fkey", fkey)
                pain_loc_female += int(record[fkey])
                bkey = 'painlocation_female___b0' + str(i)
                #print("bkey", bkey)
                pain_loc_female += int(record[bkey])
        for i in range(10,37): # checks up to 36, there are 37 and 38 for male/female back or front (i.e. some aren't checked)
            if record['gender'] == '1': #male
                fkey = 'painlocation_male___f' + str(i)
                #print("fkey", fkey)
                pain_loc_male += int(record[fkey])
                bkey = 'painlocation_male___b' + str(i)
                #print("bkey", bkey)
                pain_loc_male += int(record[bkey])
            else:
                fkey = 'painlocation_female___f' + str(i)
                #print("fkey", fkey)
                pain_loc_female += int(record[fkey])
                bkey = 'painlocation_female___b' + str(i)
                #print("bkey", bkey)
                pain_loc_female += int(record[bkey])
        #print(pain_loc_male, pain_loc_female)
	
    #if sum of all pain locations are >0
    if (record['gender'] == '1' and pain_loc_male > 0) or (record['gender'] == '2' and pain_loc_female > 0):
        #if lower back not checked
        if (int(record['painlocation_male___b18']) + int(record['painlocation_male___b19']) + int(record['painlocation_female___b18']) + int(record['painlocation_female___b19'])) == 0:
            #if pain disorder 3 not checked
            if record['paindisorder___3'] == '0':
                #if other checkbox not checked
                if record['paindisorder___7'] =='0':
                    #print("if - not low back pain")
                    ineligible.append("Not Low Back Pain")
                #else if other checkbox checked and "back" not in sentence
                else:
                    count = 0
                    words_to_check = ['back', 'spine', 'disc']
                    for word in words_to_check:
                        if word not in record['paindisorder_other']:
                            count += 1
                            #print("elif: doesn't contain ", word)
                    #print("count: ", count)
                    if count == len(words_to_check):
                        #print("other check box")
                        ineligible.append("Not Low Back Pain")
 
    if record['painduration'] == '5': #intermittent pain duration
        #print("not chronic pain")
        ineligible.append("No Chronic Pain")
    
    ''' %removing ineligibility based on other pain conditions as of 10/27/2015
    if record['paindisorder___1'] == '1': #recent surgery
        #print("recent surgery")
        ineligible.append("Other Pain: Recent Surgery")
		
    if record['paindisorder___2'] == '1': #other pain disorder (FM)
        #print("FM")
        ineligible.append("Other Pain Condition: FM")

    if record['paindisorder___4'] == '1': #other pain disorder (CRPS)
        #print("CRPS")
        ineligible.append("Other Pain Condition: CRPS")

    if record['paindisorder___5'] == '1': #other pain disorder (PP)
        #print("PP")
        #ineligible.append("Other Pain Condition: PP")
        ineligible.append("Other Pain: Pelvic")

    if record['paindisorder___6'] == '1': #other pain disorder (Migraine)
        #print("Migraine")
        ineligible.append("Other Pain Condition: Migraines")
    '''
    
    if record['painscore_avg'] != '': #NRS
        nrs = record['painscore_avg']
        if (int(nrs) < 4) and (int(nrs) > 0):
            #print("NRS")
            ineligible.append("NRS: " + nrs)
    
    problem_meds = []
    if record['medication_list'] != '':
        med_ineligible, problem_meds = check_meds(record['medication_list'], meds)
        if med_ineligible != []:
            #print("Medications")
            ineligible.extend(med_ineligible)

    if record['pregnancy'] == 1: #pregnant/breastfeeding
        #print("pregnant/breastfeeding")
        ineligible.append("MRI: Currently pregnant or breastfeeding")

    hold = []

    if record['handedness'] == '2': #handedness 
        #print("left handed")
        hold.append("Left-Handed")
    elif record['handedness'] == '3':
        hold.append("Ambidextrous")

    if record['currentpain'] == '0': #current pain
        #print("healthy volunteer")
        hold.append("Healthy Control")
    
    if record['painduration'] == '1': #pain < 3 months
        #print("pain duration")
        hold.append("Pain < 3 months")
    
	
    return ineligible, hold, problem_meds


def check_meds(record_meds, meds):

    ineligible = []
    med_list = re.split(r'[;,.\s]\s*', record_meds)
    print("med list", med_list)
    problem_meds = []

    for i in med_list:
        print("listed med", i)
        i = i.lower()
        if i in meds.keys():
            print("problem med", i)
            ineligible.append(meds[i])
            problem_meds.append(i)
    print("Medications:", ineligible)
    
    return ineligible, problem_meds


def update_ps_inelig(record, ineligible, ineligibilityDict, problem_meds):

    record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_cbp_email_screen'] = 0 # mark as ineligible for email screen
    record['admin_panel_complete'] = 2 # mark admin panel as complete

    #record['cmtps_date'] = str(datetime.datetime.now()) #raises error
    record['cmtps_conductedby'] = 'Automatic screen program 1'
    record['cmtps_eligstatus'] = 2 # mark phone screen as failure
    #record['p01_cam_center_phone_screen_complete'] = 2 # mark phone screen as complete
    record['cbp_email_screen_complete'] = 2 # mark email screen as complete
    record['cbp_phone_screen_complete'] = 2 # mark phone screen as complete

    for reason in ineligible: # update failure reasons
        i = ineligibilityDict[reason]
        key = 'cmtps_noteligreasons___' + i
        record[key] = 1

    if problem_meds != []:
        med_string = ''
        for med in problem_meds:
            med_string += (med + " ")
        record['cmtps_eligstatusnotes'] = med_string

    return record


def update_ps_hold(record, hold):

    record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_cbp_email_screen'] = 1 # mark as eligible for email screen
    record['admin_panel_complete'] = 2 # mark admin panel as complete

    record['cmtps_conductedby'] = 'Automatic screen program 1'
    record['cmtps_eligstatus'] = 3 # mark phone screen as hold
    #record['p01_cam_center_phone_screen_complete'] = 2 # mark phone screen as complete
    record['cbp_email_screen_complete'] = 2 # mark email screen as complete
    record['cbp_phone_screen_complete'] = 2 # mark phone screen as complete

    if "Pain < 3 months" in hold:
        record['cmtps_holdreason___0'] = 1 
    if "Healthy Control" in hold:
        record['cmtps_holdreason___1'] = 1 
    if "Left-Handed" in hold:
        record['cmtps_holdreason___2'] = 1 
    if "Ambidextrous" in hold:
        record['cmtps_holdreason___8'] = 1
        record['cmtps_holdother'] = "ambidextrous"
        
    return record
    
    
def update_ps_elig(record):

    record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_cbp_email_screen'] = 1 # mark as eligible for email screen
    record['admin_panel_complete'] = 0 # mark admin panel as incomplete
    
    #record['p01_cam_center_phone_screen_complete'] = 0 # mark phone screen as incomplete
    record['cbp_email_screen_complete'] = 0 # mark email screen as incomplete

    return record
    

def import_record(records, project):

    #to_import = []
    #to_import.append(records)
    #response = project.import_records(to_import)
    response = project.import_records(records)
    print("response", response)
    return response



if __name__ == '__main__':
   main()
