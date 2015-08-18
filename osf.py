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
        
        api_url = 'https://redcap-demo.stanford.edu/api/'
        api_key = 'your key here'
        project = Project(api_url, api_key)
        record = export_record(project)
        #print(record)
        #print("sorted", sorted(record.keys()))
        ineligibilityDict = read_to_dict(reasons)
        medDict = read_to_dict(medications)

        newRecord = check_eligibility(record, ineligibilityDict, medDict)
        import_record(newRecord, project)

    else:
        #filename = ''
        print('No file specified')


def export_record(project):
    
    #print("FORMS:", project.forms)
    forms_subset = ['online_screening_form', 'p01_cam_center_phone_screen']
    record = project.export_records(forms=forms_subset)
    #print("record exported, # of keys:", len(record[0].keys()))
	
    return record[-1] # return dict of single record (last record)


def read_to_dict(filename):

    f = open(filename, 'r')
    csv_reader = csv.reader(f, delimiter=',')
    newDict = {}
    for key, value in csv_reader:
        newDict[key] = value
    #print('newDict:', newDict)
    f.close()

    return newDict


def check_eligibility(record, ineligibilityDict, meds):

    ineligible, hold, problem_meds = p01(record, meds)
    if ineligible != []:
        print(ineligible)
        print("record", record['record_id'], "- ineligible")
        newRecord = update_ps_inelig(record, ineligible, ineligibilityDict, problem_meds)
    elif hold != []:
        print(hold)
        print("record", record['record_id'], "- on hold")
        newRecord = update_ps_hold(record, hold)
    else:
        print("record", record['record_id'], "- looks eligible -> phone screen")
        #newRecord = record
        newRecord = update_ps_elig(record)

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
            #print("age")
            ineligible.append("Age < 21 years old")
        elif age > 65: #dob
            #print("age")
            ineligible.append("Age > 65 years old")
    
    if record['gender'] == '3' or record['gender'] == '4':
        #print("Gender")
        ineligible.append("Gender Ambiguity")
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
                    for word in ['back', 'spine', 'disc']:
                        if word not in record['paindisorder_other']:
                            print("elif", word)
                            ineligible.append("Not Low Back Pain")
 
    if record['painduration'] == '1' or record['painduration'] == '5': #pain duration (not currently excluding intermittent)
        #print("not chronic pain")
        ineligible.append("No Chronic Pain")
    
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
        print("pregnant/breastfeeding")
        ineligible.append("MRI: Currently pregnant or breastfeeding")

    hold = []

    if record['handedness'] == '2': #handedness (not currently excluding ambidextrous)
        #print("left handed")
        hold.append("Left-Handed")

    if record['currentpain'] == '0': #current pain
        #print("healthy volunteer")
        hold.append("Healthy Control")
    
	
    return ineligible, hold, problem_meds


def check_meds(record_meds, meds):

    ineligible = []
    med_list = re.split(r'[,.\s]\s*', record_meds)
    #print("med list", med_list)
    problem_meds = []

    for i in med_list:
        #print("listed med", i)
        i = i.lower()
        if i in meds.keys():
            #print("problem med", i)
            ineligible.append(meds[i])
            problem_meds.append(i)
    #print("Medications:", ineligible)
    
    return ineligible, problem_meds


def update_ps_inelig(record, ineligible, ineligibilityDict, problem_meds):

    record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_panel_complete'] = 2 # mark admin panel as complete

    #record['cmtps_date'] = str(datetime.datetime.now()) #raises error
    record['cmtps_conductedby'] = 'Automatic screen program'
    record['cmtps_eligstatus'] = 2 # mark phone screen as failure
    record['p01_cam_center_phone_screen_complete'] = 2 # mark phone screen as complete

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
    record['admin_panel_complete'] = 2 # mark admin panel as complete

    record['cmtps_eligstatus'] = 3 # mark phone screen as hold
    record['p01_cam_center_phone_screen_complete'] = 2 # mark phone screen as complete

    if "Healthy Control" in hold:
        record['cmtps_holdreason___1'] = 1 
    if "Left-Handed" in hold:
        record['cmtps_holdreason___2'] = 1 
        
    return record
    
    
def update_ps_elig(record):

    record['admin_panel_complete'] = 0 # mark admin panel as incomplete
    record['p01_cam_center_phone_screen_complete'] = 0 # mark phone screen as incomplete

    return record
    

def import_record(record, project):

    to_import = []
    to_import.append(record)
    response = project.import_records(to_import)
    #print("response", response)
    return response



if __name__ == '__main__':
   main()
