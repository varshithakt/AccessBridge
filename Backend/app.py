import io, os, re, uuid
from datetime import datetime, timedelta, timezone, date
from functools import wraps
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import bcrypt, jwt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

load_dotenv(); app = Flask(__name__); CORS(app)
SECRET = os.getenv('JWT_SECRET', 'accessbridge-development-secret')
memory = {'users': [], 'applications': []}
try:
 from pymongo import MongoClient
 uri=os.getenv('MONGO_URI'); db=MongoClient(uri,serverSelectionTimeoutMS=1500).accessbridge if uri else None
 if db: db.command('ping')
except Exception: db=None

SERVICES=[
 {'id':'income-certificate','name':'Income Certificate','category':'Certificates','time':'8–10 minutes','description':'Proof of household income for benefits and public schemes.','requiredInformation':['Identity details','Address','Annual income','Supporting document'],'fields':[{'id':'fullName','question':'What is your full name?','simpleQuestion':'Your name as it appears on official records.','type':'text','required':True},{'id':'dateOfBirth','question':'What is your date of birth?','type':'date','required':True},{'id':'phone','question':'What is your 10-digit phone number?','type':'tel','required':True},{'id':'address','question':'What is your current address?','type':'textarea','required':True},{'id':'annualIncome','question':'Please state your annual income.','simpleQuestion':'How much do you earn in a year?','type':'number','prefix':'₹','required':True},{'id':'employmentStatus','question':'What is your employment status?','type':'select','options':['Employed','Self-employed','Student','Unemployed','Retired'],'required':True},{'id':'purpose','question':'Why do you need this certificate?','type':'textarea','required':True},{'id':'supportingDocument','question':'Which supporting document will you provide?','type':'select','options':['Salary slip','Bank statement','Income tax return','Employer certificate','Other'],'required':True}]},
 {'id':'residence-certificate','name':'Residence Certificate','category':'Certificates','time':'6–8 minutes','description':'Evidence of your place and duration of residence.','requiredInformation':['Identity details','Address','District and state','Residence duration'],'fields':[{'id':'fullName','question':'What is your full name?','type':'text','required':True},{'id':'dateOfBirth','question':'What is your date of birth?','type':'date','required':True},{'id':'address','question':'What is your current address?','type':'textarea','required':True},{'id':'district','question':'Which district do you live in?','type':'text','required':True},{'id':'state','question':'Which state do you live in?','type':'text','required':True},{'id':'durationOfResidence','question':'How long have you lived there?','type':'text','required':True},{'id':'phone','question':'What is your 10-digit phone number?','type':'tel','required':True}]},
 {'id':'scholarship-application','name':'Scholarship Application','category':'Education','time':'10–12 minutes','description':'Apply for educational financial support.','requiredInformation':['Student details','Institution and course','Income','Academic record','Bank account'],'fields':[{'id':'fullName','question':'What is your full name?','type':'text','required':True},{'id':'dateOfBirth','question':'What is your date of birth?','type':'date','required':True},{'id':'institution','question':'What is your institution name?','type':'text','required':True},{'id':'course','question':'What course are you studying?','type':'text','required':True},{'id':'annualFamilyIncome','question':'What is your annual family income?','type':'number','prefix':'₹','required':True},{'id':'category','question':'What is your category?','type':'select','options':['General','OBC','SC','ST','EWS'],'required':True},{'id':'academicPercentage','question':'What was your academic percentage?','type':'number','required':True},{'id':'bankAccount','question':'What is your bank account number?','type':'text','required':True},{'id':'phone','question':'What is your 10-digit phone number?','type':'tel','required':True}]}
]
def get_service(sid): return next((s for s in SERVICES if s['id']==sid),None)
def public(u): return {'id':str(u.get('_id',u.get('id'))),'name':u['name'],'email':u['email'],'accessibilityPreferences':u.get('accessibilityPreferences',[]),'language':u.get('language','en')}
def user_by_email(email): return db.users.find_one({'email':email}) if db is not None else next((u for u in memory['users'] if u['email']==email),None)
def issue(u): return jwt.encode({'sub':str(u.get('_id',u.get('id'))),'exp':datetime.now(timezone.utc)+timedelta(days=7)},SECRET,algorithm='HS256')
def auth(fn):
 @wraps(fn)
 def wrapped(*args,**kwargs):
  try: uid=jwt.decode(request.headers.get('Authorization','').replace('Bearer ',''),SECRET,algorithms=['HS256'])['sub']
  except Exception: return jsonify(error='Authentication required.'),401
  u=db.users.find_one({'_id':__import__('bson').ObjectId(uid)}) if db is not None else next((x for x in memory['users'] if x['id']==uid),None)
  return fn(u,*args,**kwargs) if u else (jsonify(error='User not found.'),401)
 return wrapped
def validate(s,a):
 errors={}
 for f in s['fields']:
  v=str(a.get(f['id'], '')).strip()
  if f.get('required') and not v: errors[f['id']]='This field is required.'
  elif f['id']=='phone' and not re.fullmatch(r'\d{10}',v): errors[f['id']]='Please enter a valid 10-digit phone number.'
  elif f['id'] in ('annualIncome','annualFamilyIncome') and (not re.fullmatch(r'\d+(\.\d+)?',v) or float(v)<0): errors[f['id']]='Annual income cannot be negative.'
  elif f['id']=='academicPercentage' and (not re.fullmatch(r'\d+(\.\d+)?',v) or not 0<=float(v)<=100): errors[f['id']]='Percentage must be between 0 and 100.'
  elif f['id']=='dateOfBirth':
   try:
    if date.fromisoformat(v)>date.today(): errors[f['id']]='Date of birth cannot be in the future.'
   except ValueError: errors[f['id']]='Please enter a valid date.'
 return errors

@app.post('/api/auth/register')
def register():
 d=request.get_json() or {}; name=d.get('name','').strip(); email=d.get('email','').lower().strip(); password=d.get('password','')
 if not name or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',email) or len(password)<8:return jsonify(error='Enter a name, valid email, and password of at least 8 characters.'),400
 if user_by_email(email): return jsonify(error='An account already exists for this email.'),409
 u={'id':str(uuid.uuid4()),'name':name,'email':email,'passwordHash':bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode(),'accessibilityPreferences':d.get('accessibilityPreferences',[]),'language':d.get('language','en'),'createdAt':datetime.now(timezone.utc)}
 if db is not None: u.pop('id'); r=db.users.insert_one(u); u['_id']=r.inserted_id
 else: memory['users'].append(u)
 return jsonify(user=public(u),token=issue(u)),201
@app.post('/api/auth/login')
def login():
 d=request.get_json() or {}; u=user_by_email(d.get('email','').lower().strip())
 if not u or not bcrypt.checkpw(d.get('password','').encode(),u['passwordHash'].encode()):return jsonify(error='Invalid email or password.'),401
 return jsonify(user=public(u),token=issue(u))
@app.get('/api/services')
def services(): return jsonify(services=SERVICES)
@app.get('/api/services/<sid>')
def service_route(sid):
 s=get_service(sid); return (jsonify(service=s),200) if s else (jsonify(error='Service not found.'),404)
def serialize(doc):
 d=dict(doc); d['id']=str(d.pop('_id',d.get('id'))); d['userId']=str(d['userId']); return d
def own_app(uid,aid):
 return db.applications.find_one({'_id':__import__('bson').ObjectId(aid),'userId':uid}) if db is not None else next((x for x in memory['applications'] if x['id']==aid and x['userId']==uid),None)
@app.get('/api/applications')
@auth
def list_apps(u):
 uid=str(u.get('_id',u.get('id'))); rows=list(db.applications.find({'userId':uid}).sort('updatedAt',-1)) if db is not None else [x for x in memory['applications'] if x['userId']==uid]
 return jsonify(applications=[serialize(x) for x in rows])
@app.post('/api/applications')
@auth
def create_app(u):
 d=request.get_json() or {}; s=get_service(d.get('serviceId')); answers=d.get('answers',{})
 if not s:return jsonify(error='Choose a valid service.'),400
 errors=validate(s,answers)
 if d.get('status')=='completed' and errors:return jsonify(error='Please correct the highlighted fields.',errors=errors),422
 doc={'id':str(uuid.uuid4()),'userId':str(u.get('_id',u.get('id'))),'serviceId':s['id'],'answers':answers,'status':d.get('status','draft'),'referenceNumber':'AB-'+uuid.uuid4().hex[:8].upper(),'createdAt':datetime.now(timezone.utc),'updatedAt':datetime.now(timezone.utc)}
 if db is not None:doc.pop('id');r=db.applications.insert_one(doc);doc['_id']=r.inserted_id
 else:memory['applications'].append(doc)
 return jsonify(application=serialize(doc)),201
@app.get('/api/applications/<aid>')
@auth
def read_app(u,aid):
 doc=own_app(str(u.get('_id',u.get('id'))),aid); return (jsonify(application=serialize(doc)),200) if doc else (jsonify(error='Application not found.'),404)
@app.put('/api/applications/<aid>')
@auth
def update_app(u,aid):
 d=request.get_json() or {}; doc=own_app(str(u.get('_id',u.get('id'))),aid)
 if not doc:return jsonify(error='Application not found.'),404
 answers=d.get('answers',doc['answers']); status=d.get('status',doc['status']); errors=validate(get_service(doc['serviceId']),answers)
 if status=='completed' and errors:return jsonify(error='Please correct the highlighted fields.',errors=errors),422
 updates={'answers':answers,'status':status,'updatedAt':datetime.now(timezone.utc)}
 if db is not None:db.applications.update_one({'_id':doc['_id']},{'$set':updates})
 doc.update(updates);return jsonify(application=serialize(doc))
@app.post('/api/applications/<aid>/complete')
@auth
def complete(u,aid):
 doc=own_app(str(u.get('_id',u.get('id'))),aid)
 if not doc:return jsonify(error='Application not found.'),404
 answers=(request.get_json() or {}).get('answers',doc['answers']); errors=validate(get_service(doc['serviceId']),answers)
 if errors:return jsonify(error='Please correct the highlighted fields.',errors=errors),422
 updates={'answers':answers,'status':'completed','updatedAt':datetime.now(timezone.utc)}
 if db is not None:db.applications.update_one({'_id':doc['_id']},{'$set':updates})
 doc.update(updates);return jsonify(application=serialize(doc))
@app.post('/api/ai/<action>')
@auth
def ai(u,action):
 d=request.get_json() or {}; q=d.get('question','this field'); lang=d.get('language','en')
 text={'hi':'कृपया सही जानकारी दें। यह आपके आवेदन को पूरा करने में मदद करती है।','kn':'ದಯವಿಟ್ಟು ಸರಿಯಾದ ಮಾಹಿತಿಯನ್ನು ನೀಡಿ. ಇದು ನಿಮ್ಮ ಅರ್ಜಿಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತದೆ.'}.get(lang,f"This asks for {q.lower().rstrip('?')}. Give the information accurately; it helps process your application.")
 return jsonify(response=text,source='fallback',action=action)
@app.post('/api/applications/<aid>/generate-pdf')
@auth
def generate_pdf(u,aid):
 doc=own_app(str(u.get('_id',u.get('id'))),aid)
 if not doc:return jsonify(error='Application not found.'),404
 s=get_service(doc['serviceId']); out=io.BytesIO(); c=canvas.Canvas(out,pagesize=A4); y=800
 lines=['AccessBridge','One service. Every ability.','',f"Service: {s['name']}",f"Application Reference: {doc['referenceNumber']}",f"Status: {doc['status'].title()}",'','Applicant information and answers:']+[f"{f['question']} {doc['answers'].get(f['id'],'—')}" for f in s['fields']]
 for line in lines:
  c.drawString(54,y,line[:110]); y-=22
  if y<60:c.showPage();y=800
 c.save();out.seek(0);return send_file(out,mimetype='application/pdf',as_attachment=True,download_name=f"{doc['referenceNumber']}.pdf")
@app.post('/api/documents/upload')
@auth
def upload(u):
 f=request.files.get('file')
 if not f:return jsonify(error='Choose a PDF or image to upload.'),400
 if f.mimetype not in ('application/pdf','image/png','image/jpeg'):return jsonify(error='Only PDF, PNG, and JPG files are supported.'),415
 return jsonify(message='File received. Automatic field extraction is not enabled in this MVP yet.',filename=f.filename,status='received'),202
@app.get('/api/health')
def health():return jsonify(status='ok',database='mongodb' if db is not None else 'in-memory demo fallback')
if __name__=='__main__':app.run(port=int(os.getenv('PORT',5000)),debug=True)
