
import os
import json
import pyDes
import hashlib
from random import randint
import couchdb
import datetime
import base64


from flask import Flask, render_template, request, make_response
import swiftclient.client as swiftclient


PORT = int(os.getenv('PORT', 80))
app = Flask(__name__)

if 'VCAP_SERVICES' in os.environ:
    cred = json.loads(os.environ['VCAP_SERVICES'])['Object-Storage'][0]
    credinfo=cred['credentials']
    authurl = credinfo['auth_url'] + '/v3'
    projectId = credinfo['projectId']
    region = credinfo['region']
    userId = credinfo['userId']
    password = credinfo['password']
    projectname = credinfo['project']
    domainName = credinfo['domainId']
    conn = swiftclient.Connection(key=password, authurl=authurl, auth_version='3',
                                  os_options={"project_id": projectId, "user_id": userId, "region_name": region})

# couchDB/Cloudant-related global variables
couchInfo = ''
couchServer = ''
couch = ''

# get service information if on Bluemix
if 'VCAP_SERVICES' in os.environ:
    couchInfo = json.loads(os.environ['VCAP_SERVICES'])['cloudantNoSQLDB'][0]
    couchServer = couchInfo["credentials"]["url"]
    couch = couchdb.Server(couchServer)

@app.route('/',methods=['GET','POST'])
def root():
    return render_template("index.html")

db=couch['test1']

@app.route('/couchdb', methods=["GET","POST"])
def dbupload():
  
    f=request.files['file']
    filecontent=f.stream.read()
    get_filename=[]
    get_hash=[]
    get_version=[]
    now=datetime.datetime.utcnow()
    cal_hash = hashlib.md5(filecontent).hexdigest()

    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        get_filename.append(doc["filename"])
        get_hash.append(doc['hash'])
        get_version.append(doc['version'])
        

    if f.filename not in get_filename :

        doc={"AUTHOR":"Adarsh",}
        doc["filename"]=f.filename
        doc["content"]=base64.b64encode(filecontent)
        doc["hash"]=cal_hash
        doc["version"]=0
        doc["time"]=str(now)
        db.save(doc)
        return render_template("index.html", msg="File uploaded successfully")

    elif cal_hash not in get_hash and f.filename in get_filename :
        ver_pos=get_filename.index(f.filename)
        current_version=int(get_version[ver_pos])
        updateversion=current_version+1
        doc = {"AUTHOR": "Adarsh", }
        doc["filename"] = f.filename
        doc["content"] = base64.b64encode(filecontent)
        doc["hash"] = cal_hash
        doc["version"] = updateversion
        doc["time"] =str(now)
        db.save(doc)

        return render_template("index.html", msg="File uploaded successfully")
    else :
        return render_template("index.html",msg="File already exits")




@app.route('/downloaddb', methods=["GET","POST"])
def dbdownoad():

    filename=request.form['downloadfilename']

    for docs in db.view('_all_docs'):
        doc = db.get(docs.id)

        if doc["filename"] == filename:

            actual_file=base64.b64decode(doc["content"])

            verify_hash=doc["hash"]
            calculate_hash=hashlib.md5(actual_file).hexdigest()
            print("check")
            if verify_hash==calculate_hash:
                print("res")
                response = make_response(actual_file)
                response.headers["Content-Disposition"] = "attachment; filename=%s"%filename
                print("done")
                return response
            else :
                return render_template("index.html")

        else :
            continue

@app.route('/listfiles',methods=['GET','POST'])
def listallfiles():
    print("l")
    filenames_list = []

    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        filename=doc['filename']
        filenames_list.append(filename)

    return render_template("index.html",filenames_list=filenames_list)

@app.route('/deletefiles',methods=['GET','POST'])
def deletefiles():
    print("d")
    filenametodelete=request.form['filename']
    for docs in db.view('_all_docs'):
        doc=db.get(docs.id)
        if doc['filename']==filenametodelete:
            db.delete(doc)

    return render_template("index.html")





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(PORT), threaded=True, debug=False)


