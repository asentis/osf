#!/usr/bin/env python

import sys
import csv
import re
from redcap import Project

# usage in osf directory: python ./email_screen.py ../../../Desktop/P01_IneligibilityReasons2.csv ../../../Desktop/P01_Medications.csv ../../../Desktop/RecordIDs.csv


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
        
        api_url = 'https://redcap.stanford.edu/api/'
        api_key = 'your key here'
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
    
    forms_subset = ['cbp_email_screen', 'cbp_phone_screen']
    fields_subset = ['record_id']
    
    records = project.export_records(records=recordsList, forms=forms_subset, fields=fields_subset)
    #print("record exported, # of keys:", len(record[0].keys()))
	
    return records # return dict of records
    
    
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
    num_elig = 0
    
    for record in records:
        #print("record", record)
        ineligible, failure_notes, problem_meds = p01(record, meds)
        if ineligible != []:
            print(ineligible)
            print("record", record['record_id'], "- ineligible")
            newRecord = update_ps_inelig(record, ineligible, failure_notes, ineligibilityDict, problem_meds)
            num_inelig += 1
        else:
            print("record", record['record_id'], "- looks eligible -> phone screen")
            #newRecord = record
            newRecord = update_ps_elig(record)
            num_elig += 1
        
        newRecordList.append(newRecord)
    
    print("ineligible:", num_inelig, "eligible:", num_elig)
    return newRecordList

    
def p01(record, meds):

    #ineligible = []
    ineligible = set()
    failure_notes = []
    
    # calculate BMI
    if record['cmtps_height'] != '' and record['cmtps_weight'] != '':
        if record['cmtps_height'].isdigit(): #height in inches
            height = int(record['cmtps_height'])
            print("height", height)
        else:
            #convert to inches
            conversion = re.split(r'[\'"\s]\s*', record['cmtps_height'])
            print("conversion", conversion)
            feet = int(conversion[0])
            inches = float(conversion[1])
            height = (feet*12)+inches
        weight = int(record['cmtps_weight'])
        print("weight", weight)
        bmi = (weight/(height*height))*703
        print("bmi", bmi)
        if bmi > 31:
            ineligible.add("MRI: BMI")
    
    # pain scores
    if record['cmtps_avgpaindays2'] != '' and record['cmtps_avgpainmonth2'] != '': #NRS
        nrs_days = record['cmtps_avgpaindays2']
        nrs_month = record['cmtps_avgpainmonth2']
        if (int(nrs_days) < 4) and (int(nrs_month) < 4):
            print("NRS")
            ineligible.add("NRS: " + nrs_days)
            ineligible.add("NRS: " + nrs_month)
    
    # radiculopathy
    if record['cmtps_radicularpain'] == '1':
        if record['cmtps_radicularsympy'] == '1' and record['cmtps_radicularsympy2'] == '1':
            print("radiculopathy")
            ineligible.add("Radicular Symptoms")
    
    # worst pain not low back
    worst_pain = 0
    for i in range(1,8): 
        key = 'cmtps_worstpainareas___' + str(i)
        worst_pain += int(record[key])
           
    if worst_pain > 0: # if checked off any worst pain areas
        if record['cmtps_worstpainareas___4'] != '1':
            print("Not Low Back Pain")
            ineligible.add("Not Low Back Pain")
    
    # other medical conditions
    if record['cmtps_othermedcond'] == '1' and record['cmtps_othermedcondy'] != '':
        if 'diabetes' in record['cmtps_othermedcondy'].lower():
            print("Other Medical Condition: Diabetes")
            ineligible.add("Other Medical Condition: Diabetes")
        if 'costochondritis' in record['cmtps_othermedcondy'].lower():
            print("Other Medical Condition: Costochondritis")
            ineligible.add("Other Medical Condition: Costochondritis")
        if 'sjogren' in record['cmtps_othermedcondy'].lower():
            print("Other Medical Condition: Sjogren's Syndrome")
            ineligible.add("Other Medical Condition: Sjogren's Syndrome")
 
    # seizures/neuro
    if record['cmtps_seizuresneuro'] == '1':
        print("MRI: Seizure")
        ineligible.add("MRI: Seizure")
        
    # legal action
    if record['cmtps_legal'] == '1':
        print("Legal action")
        ineligible.add("Other")
        failure_notes.append("Legal action")
    
    # disability claim
    if record['cmtps_disabilityclaim'] == '1':
        print("Disability claim")
        ineligible.add("Other")
        failure_notes.append("Disability claim")
    
    # substance abuse
    if record['cmtps_abuseproblem'] == '1':
        print("Substance abuse")
        ineligible.add("Other")
        failure_notes.append("Substance abuse")
    
    # bleeding disorder
    if record['cmtps_bleeding'] == '1':
        print("Bleeding disorder")
        ineligible.add("Other")
        failure_notes.append("Bleeding disorder")
    
    # pregnancy
    if record['cmtps_pregnant'] == '1':
        print("MRI: Currently pregnant or breastfeeding")
        ineligible.add("MRI: Currently pregnant or breastfeeding")
    
    # MRI screening
    mri_list = []
    vars = [3,4]
    vars.extend(list(range(6,18)))
    vars.extend([20,27,28,33,45])
    count = 0
    for j in vars:
        key = 'cmtps_nc' + str(j)
        if record[key] != '':
            count += int(record[key])
    if count > 0:
        print("MRI Safety Screen")
        ineligible.add("MRI Safety Screen")
        
    ineligible_list = list(ineligible)
    
    # medications (do last)
    medication_list = ''
    for i in range(1,21):
        key = 'cmtps_med' + str(i) + 'name'
        if record[key] != '':
            medication_list += (record[key] + ',')
    problem_meds = []
    if medication_list != '':
        med_ineligible, problem_meds = check_meds(medication_list, meds)
        if med_ineligible != []:
            print("Medications")
            ineligible_list.extend(med_ineligible)

    
	
    return ineligible_list, failure_notes, problem_meds


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


def update_ps_inelig(record, ineligible, failure_notes, ineligibilityDict, problem_meds):

    #record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    #record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_cbp_phone_screen'] = 0 # mark as ineligible for phone screen
    record['admin_panel_complete'] = 2 # mark admin panel as complete

    record['cmtps_conductedby'] = 'Automatic screen program 2'
    record['cmtps_eligstatus'] = 2 # mark phone screen as failure
    record['cbp_phone_screen_complete'] = 2 # mark phone screen as complete

    for reason in ineligible: # update failure reasons
        i = ineligibilityDict[reason]
        key = 'cmtps_noteligreasons___' + i
        record[key] = 1
        
    note = ''
    for failure in failure_notes: # add to additional eligibility notes
        note += (failure + '. ')
    #print("additional eligibility notes:", note)
    record['cmtps_noteligreasonsother'] = note

    if problem_meds != []:
        med_string = ''
        for med in problem_meds:
            med_string += (med + " ")
        record['cmtps_eligstatusnotes'] = med_string

    return record
    
    
def update_ps_elig(record):

    #record['admin_relevantstudies___6'] = 1 # mark admin panel as considered for P01
    #record['admin_ra_exclude'] = 0 # mark admin panel as appropriate for research
    record['admin_cbp_phone_screen'] = 1 # mark as eligible for phone screen
    record['admin_panel_complete'] = 0 # mark admin panel as incomplete


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
