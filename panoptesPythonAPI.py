#!/usr/bin/python

import urllib2 
import cookielib
import json
import re
import string
import requests
import csv
import math

# Remote host set to the panoptes staging API
global host,hostapi
host = "https://panoptes-staging.zooniverse.org/"
hostapi = "https://panoptes-staging.zooniverse.org/api/"
#host = "http://172.17.2.87:3000/"
#hostapi = "http://172.17.2.87:3000/api/"

def get_bearer_token(user_name,password):
    "Logs user in and gets a bearer token for the given user"

    # look like you're a zooniverse front end client
    app_client_id="535759b966935c297be11913acee7a9ca17c025f9f15520e7504728e71110a27"
    #app_client_id="05fd85e729327b2f71cda394d8e87e042e0b77b05e05280e8246e8bdb05d54ed"
    #app_client_id="05fd85e729327b2f71cda394d8e87e042e0b77b05e05280e8246e8bdb05d54ed"
    #0. Establish a cookie jar
    cj = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    #1. get the csrf token
    request = urllib2.Request(host+"users/sign_in",None)
    response = opener.open(request)

    body = response.read()

    # grep for csrf-token
    csrf_line = re.findall(".+csrf-token.+",body)[0]
    # and extract it
    first = string.find(csrf_line,'"')
    second = string.find(csrf_line,'"',first+1)
    csrf_token = csrf_line[first+1:second]

    #2. use the token to get a devise session via JSON stored in a cookie
    devise_login_data=("{\"user\": {\"display_name\":\""+user_name+"\",\"password\":\""+password+
                       "\"}, \"authenticity_token\": \""+csrf_token+"\"}")
    request = urllib2.Request(host+"users/sign_in",data=devise_login_data)
    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/json")

    try:
        response = opener.open(request)
    except urllib2.HTTPError as e:
        print 'In get_bearer_token, stage 2:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    #3. use the devise session to get a bearer token for API access
    bearer_req_data=("{\"grant_type\":\"password\",\"client_id\":\"" +
                     app_client_id + "\"}")
    request = urllib2.Request(host+"oauth/token",bearer_req_data)
    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/json")

    try:
        response = opener.open(request)
    except urllib2.HTTPError as e:
        print 'In get_bearer_token, stage 3:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # extract the bearer token
    json_data = json.loads(body)
    bearer_token = json_data["access_token"]
    
    return bearer_token

def get_userid_from_username(user_name,token):
    "Gets a user's ID from a username; returns -1 if none"

    head = {'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
    response = requests.get(hostapi+'users?login='+user_name,headers=head)
 
    userid = -1
    data = response.json()
    if len(data["users"])>0:
        userid = data["users"][0]["id"]

    return userid

# depricated. Ooh la la requests, I think I'm in love...
def get_userid_from_username_old(user_name,token):
    "Gets a user's ID from a username; returns -1 if none"

    # info
    request = urllib2.Request(hostapi+"users?login="+user_name,None)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    userid = -1
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'In get_userid_from_username:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

        # put it in json structure and extract id
        data = json.loads(body)
        if len(data["users"])>0:
            userid = data["users"][0]["id"]
    
    return userid

def get_groupid_from_groupname(group_name,token):
    "Gets a group's ID from a group name; returns -1 if none"

    # info
    request = urllib2.Request(hostapi+"groups?name="+group_name,None)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    groupid = -1
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'In get_groupid_from_groupname:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

        # put it in json structure and extract id
        data = json.loads(body)
        if len(data["user_groups"])>0:
            groupid = data["user_groups"][0]["id"]
        
    return groupid

def create_group(group_name,token):
    "Create a user group with just a group name"

    values = """
        {
            "user_groups": {
                "name": \"""" + group_name + """\"
            }
        }
        """
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
    response = requests.post(hostapi+'groups',headers=head,data=values)
    
    data = response.json()
    groupid = data["user_groups"][0]["id"]

    return groupid


# depricated
def create_group_old(group_name,token):
    "Create a user group with just a group name"
    
    values = """
        {
            "user_groups": {
                "name": \"""" + group_name + """\"
            }
        }
        """
    request = urllib2.Request(hostapi+"groups",values)

    # add headers
    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)
    
   # request
    groupid = -1
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

        # put it in json structure and extract id
        data = json.loads(body)
        groupid = data["user_groups"][0]["id"]

    return groupid

def add_user_to_group(groupid,userid,token):
    "Add the given user to the given group"

    values = """
      {
        "users": [
          \"""" + str(userid) + """\"
        ]
      }
    """

    request = urllib2.Request(hostapi+"groups/"+str(groupid)+
                              "/links/users", data=values)

    # add headers
    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    return

def get_group_info(groupid,token):
    "Get all the data for a group given its ID"

    request = urllib2.Request(hostapi+"groups/"+str(groupid),None)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)
  
    return data

def get_membership_info(memid,token):
    "Get membership info for one user in one group"

    request = urllib2.Request(hostapi+"memberships/"+str(memid),None)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)
  
    return data    

def get_membership_info_for_group(groupid,token):
    "Get membership information for all group members"

    groupinfo = get_group_info(groupid,token)
    mems = groupinfo["user_groups"][0]["links"]["memberships"]

    mem_info = []
    for mem in mems:
        print mem
        info = get_membership_info(mem,token)
        print info
        mem_info.append(info["memberships"][0])

    return mem_info

def get_login_user_info(token):
    request = urllib2.Request(hostapi+"me/")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    return data

def create_group_project(groupid,projname,projdesc,token):
    "Create a project owned by a group"

    # project request
    values = """
    {
        "projects": {
            "name": \"""" + projname + """\",
            "description": \"""" + projdesc + """\",
            "primary_language": "en-us",
            "links": {
                "owner": {
                    "id": \""""+ str(groupid) + """\",
                    "type": "user_groups"
                }
            }
        }
    }"""

    request = urllib2.Request(hostapi+"projects",data=values)

    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    projid = data["projects"][0]["id"]
     
    return projid    

def create_user_project(projname,projdesc,token):
    "Create a project owned by self"

    values = """
    {
        "projects": {
            "name": \"""" + projname + """\",
            "description": \"""" + projdesc + """\",
            "primary_language": "en-us"
        }
    }"""
    
    request = urllib2.Request(hostapi+"projects",data=values)

    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'In create_user_project:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    projid = data["projects"][0]["id"]
     
    return projid    


## NOT YET
def get_projectid_from_projectname(groupid,project_name,token):
    "Gets a project's ID from a project name; returns -1 if none"
    return

## NOT YET
def create_workflow(token):
    "Creates a workflow"

    values = """
    {
        "workflows": {
            "display_name": "Do some round stuff",
            "tasks":  {
                "roundness": {
                    "type": "single",
                    "question": "How round is it?",
                    "answers": [
                        {"value": "very", "label": "Very"},
                        {"value": "sorta", "label": "In between"},
                        {"value": "not", "label": "Cigar shaped"}
                    ],
                    "next": null
                }
            },
            "primary_language": "en-us",
            "links": {
                "project": "60"
            }
        }
    }"""


    request = urllib2.Request(hostapi+"workflow",data=values)

    request.add_header("Content-Type","application/json")
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    print body
    #projid = data["projects"][0]["id"]
     
    return 0


def create_subject(project_id,meta,filename,token):
    "Create a subject and return its ID"

    values = """
    {
        "subjects": {
            "locations": [
                "image/jpeg"
            ],
            "metadata": {
            """ + meta + """
            },
            "links": {
                "project": \"""" + str(project_id) + """\"
            }
        }
    }"""
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
    response = requests.post(hostapi+'subjects',headers=head,data=values)

    # put it in json structure and extract id
    data = response.json()
    subjid = data["subjects"][0]["id"]
    signed_urls = data["subjects"][0]["locations"][0]["image/jpeg"]

    # -----------
    # now that we have the signed URL, we can upload the file
    # -----------

    head = {'Content-Type':'image/jpeg'}
    with open(filename,'rb') as fp:
        response = requests.put(signed_urls,headers=head,data=fp)
    
    return subjid


def create_subject_set(project_id,display_name,subject_list,token):
    "Create a Subject Set given a list of subject IDs"

    values = """
        {
            "subject_sets": {
                "display_name": \"""" + display_name + """\",
                "links": {
                    "project": \"""" + str(project_id) + """\",
                    "subjects": """ + str(subject_list) + """
                }
            }
        }
        """
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
   
    response = requests.post(hostapi+'subject_sets',headers=head,data=values)   
    data = response.json()
    subsetid = data["subject_sets"][0]["id"]

    return subsetid


def create_subject_set_from_manifest(project_id,display_name,
                                     img_path,manifest_name,token):
    "Create a Subject Set from a manifest of images and metadata"

    # list of ids
    subject_list = []

    # read in from a file a set of subjects
    with open(img_path+manifest_name,'rb') as csvfile:
        freader = csv.reader(csvfile,delimiter=',')
        # header row
        headrow = freader.next()
        for row in freader:
            # file is first
            image_file = img_path+row[0]
            # rest is metadata
            meta_temp = ""
            for label,meta in zip(headrow[1:],row[1:]):
                meta_temp = meta_temp+"\""+label+"\":\""+meta+"\","
            # remove last comma
            meta_str = meta_temp[:-1]

            # create the subject, upload the image, and save the id
            subjid = create_subject(project_id,meta_str,image_file,token)
            subject_list.append(int(subjid))
    
            print "uploaded: "+image_file

    # now we have a list of subject ids; create the subject set
    subj_set_id = create_subject_set(project_id,display_name,subject_list,token)
    return subj_set_id

                                     
def create_workflow(workflow,token):
    "Create a Workflow, given the json content"
    
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
   
    response = requests.post(hostapi+'workflows',headers=head,data=workflow)   

    print "----"
    print response.request.headers
    print workflow
    print "----"
    print response
    print response.status_code
    print response.text
    print "----"
    
    data = response.json()

    workflowid = data["workflows"][0]["id"]

    return workflowid

def get_project_id(project_name,token):
    request = urllib2.Request(hostapi+"projects?owner=zooniverse-beta&display_name="+project_name)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    return data["projects"][0]["id"]

def get_workflow_id(project_id,token):
    request = urllib2.Request(hostapi+"workflows?project_id="+project_id)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

    # put it in json structure and extract id
    data = json.loads(body)

    return data["workflows"][0]['version']

#https://panoptes-staging.zooniverse.org/api/projects?owner=zooniverse-beta&display_name=Supernovae

def create_aggregation(workflow_id,subject_id,token,aggregation):
    assert type(aggregation) is dict
    aggregation["workflow_version"] = "1.1"

    json_values = { "admin": 1,
                    'aggregations': {
                                        'aggregation': aggregation,
                                        'links': {
                                            "workflow": str(workflow_id),
                                            "subject":str(subject_id)
                                        }
                                    }
    }
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}
    response = requests.post(hostapi+'aggregations',headers=head,data=json.dumps(json_values))
    #print hostapi+'aggregations'
    return response.status_code,response.text


def update_aggregation(workflow_id,workflow_version,subject_id,token,aggregation,etag):
    assert type(aggregation) is dict
    aggregation["workflow_version"] = str(workflow_version)

    json_values = { "admin": 1,
                    'aggregations': {
                                        'aggregation': aggregation,
                                        'links': {
                                            "workflow": str(workflow_id),
                                            "subject":str(subject_id)
                                        }
                                    }
    }
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token,
            'If-Match': etag }

    #print hostapi+'aggregations/1'
    print hostapi+'aggregations/'+str(subject_id)
    print etag
    response = requests.put(hostapi+'aggregations/'+str(subject_id),headers=head,data=json.dumps(json_values))
    #print hostapi+'aggregations'
    #print
    print "==---"
    print response.status_code
    print response.text
    print head

def find_aggregation_etag(workflow_id,subject_id,token):
    head = {'Content-Type':'application/json',
            'Accept':'application/vnd.api+json; version=1',
            'Authorization':'Bearer '+token}


    #print hostapi+"aggregations?subject_id="+str(subject_id)+"&workflow_id="+str(workflow_id)+"&admin=1"
    response = requests.get(hostapi+"aggregations?subject_id="+str(subject_id)+"&workflow_id="+str(workflow_id)+"&admin=1",headers=head)
    print response.text
    #print response.headers
    body = response.text

    # put it in json structure and extract id
    data = json.loads(response.text)
    print data
    #print
    resource_id= data["aggregations"][0]["id"]
    #print

    print hostapi+"aggregations/"+str(resource_id)+"?admin=1"
    assert False
    response = requests.head(hostapi+"aggregations/"+str(resource_id)+"?admin=1",headers=head)
    etag = response.headers['etag']
    print etag

    #
    # #response = requests.get(hostapi+"aggregations?subject_id="+str(subject_id)+"&workflow_id="+str(workflow_id)+"&admin=1",headers=head)
    # print response.headers
    #
    #
    # print response.headers

    return etag



def get_classifications(project_id,token,page=1,per_page=20):
    """ Read in the annotations for the given project
    :param project_id: the corresponding project id
    :param token:
    :return:
    """

    request = urllib2.Request(hostapi+"classifications?project_id="+str(project_id)+"&admin=1&page="+str(page)+"&per_page"+str(per_page),None)
    request.add_header("Accept","application/vnd.api+json; version=1")
    request.add_header("Authorization","Bearer "+token)

    # request
    classifications = None
    try:
        response = urllib2.urlopen(request)
    except urllib2.HTTPError as e:
        print 'In get_userid_from_username:'
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
        print 'Error response body: ', e.read()
    except urllib2.URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        # everything is fine
        body = response.read()

        # put it in json structure and extract id
        classifications = json.loads(body)
    return classifications
  
def get_all_classifications(project_id,token,page=1,per_page=20):
    classification_page = get_classifications(project_id,token,page,per_page)
    
    num_classifications = classification_page["meta"]["classifications"]["count"]
    num_pages = int(math.ceil(num_classifications/float(per_page)))
    
    classification_list = classification_page["classifications"]
    for i in range(2,num_pages+1):
      classification_page = get_classifications(project_id,token,i,per_page)
      classification_list.extend(classification_page["classifications"])
    return classification_list
  
