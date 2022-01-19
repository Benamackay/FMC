#!/usr/bin/python3

import getpass
import csv
import os
import argparse
import requests
import json
import base64
import datetime

def printJSON(jsontxt):
	jsonresp=json.loads(jsontxt)
	print(json.dumps(jsonresp,sort_keys=True,indent=4,separators=(',',': ')))
	input("Press enter to continue")

def getMenu0Choice():
	def printMenu():
		print(30 * "-"," Main Menu ",30*"-")
		print("1. Deployment services")
		print("2. Object services")
		print()
		print("0. Exit")
	loop = True
	choice=-1

	while loop:
		printMenu()
		choice=input("Enter choice : ")

		if choice =='1':
			choice=1
			loop=False
		elif choice == '2':
			choice=2
			loop=False
		elif choice == '0':
			loop=False
			choice=0
		else:
			input("Incorrect selection")
	return(choice)

def getMenu1Choice(fmc,APItoken):
	def printMenu():
		print(30 * "-"," Deployment Menu ",30*"-")
		print("1. List network devices")
		print("2. List devices with undeployed changes")
		print("3. Deploy outstanding changes")
		print()
		print("0. Exit")
	loop = True
	choice=-1

	while loop:
		printMenu()
		choice=input("Enter choice : ")

		if choice == '1':
			txt=""
			if debuglvl>0:
				debug("Obtaining network device list")
			rslt=getAPIData(fmc,'/devices/devicerecords',APItoken)
			rsltjson=json.loads(rslt.text)
			for i in rsltjson["items"]:
				txt=txt+i["name"]+"\n"
			displayResults(txt)
			if debuglvl>1:
				printJSON(rslt.text)
		elif choice =='2':
			txt=""
			if debuglvl >0:
				debug("Obtaining network device list with undeployed changes")
			rslt=getAPIData(fmc,'/deployment/deployabledevices?expanded=true',APItoken)
			rsltjson=json.loads(rslt.text)
			if rsltjson["paging"]["count"]>0:
				for i in rsltjson["items"]:
					txt=txt + i["name"] + " has {} changes undeployed".format(getChangeCount(fmc,i["device"]["id"],APItoken)) + "\n"
			else:
				txt="No network devices found with undeployed changes"
			displayResults(txt)
			if debuglvl >1:
				printJSON(rslt.text)
		elif choice == '3':
			if debuglvl >0:
				debug("Obtaining network device list of undeployed changes")
			rslt=getAPIData(fmc,'/deployment/deployabledevices?expanded=true',APItoken)
			rsltjson=json.loads(rslt.text)
			if rsltjson["paging"]["count"]>0:
				postdata={"type": "DeploymentRequest","version": int(datetime.datetime.now().timestamp()*1000),"forceDeploy": False,"ignoreWarning": True}
				devicelist=[]
				for i in rsltjson["items"]:
					devicelist.append(i["device"]["id"])
				postdata['deviceList']=devicelist
			else:
				txt="No network devices found with undeployed changes"
			if debuglvl >0:
				debug("Deploying changes to device")
			rslt=postAPIData(fmc,'/deployment/deploymentrequests',postdata,APItoken)
			if debuglvl>1:
				printJSON(rslt.text)
		elif choice == '0':
			loop=False
			choice=0
		else:
			input("Incorrect selection")
	return(choice)

def getMenu2Choice(fmc,APItoken):
	def printMenu():
		print(30 * "-"," Object Menu ",30*"-")
		print("1.  List host objects")
		print("2.  Add host object")
		print("3.  Delete host object")
		print("4.  List network object")
		print("5.  Add network object")
		print("6.  Delete network object")
		print("7.  List network group objects")
		print("8.  Create network group object")
		print("9.  Add network objects to network object groups")
		print("10. Delete network object from network group object")
		print("11. Delete network group object")
		print()
		print("0. Exit")
	loop = True
	choice=-1

	while loop:
		printMenu()
		choice=input("Enter choice : ")

		if choice == '1':
                        txt=""
                        if debuglvl>0:
                                debug("Obtaining host object list")
                        rslt=getAPIData(fmc,'/object/hosts',APItoken)
                        rsltjson=json.loads(rslt.text)
                        for i in rsltjson["items"]:
                                txt=txt+i["name"]+" - " + i["id"] + "\n"
                        displayResults(txt)
                        if debuglvl>1:
                                printJSON(rslt.text)

		elif choice == '2':
			host={}
			postdata=[]
			csvfile=input("Enter path of CSV file for host import : ")
			if os.path.exists(csvfile):
				if debuglvl>0:
					debug("Reading CSV file")
				with open(csvfile) as csvfile:
					reader = csv.DictReader(csvfile)
					for row in reader:
						host['name']=row['name']
						host['type']='Host'
						host['value']=row['value']
						host['description']=row['description']
						postdata.append(host)
						host={}
				if debuglvl>0:
					debug("Uploading CSV data")
				rslt=postAPIData(fmc,'/object/hosts?bulk=true',postdata,APItoken)
				if debuglvl>1:
					printJSON(rslt.text)
			else:
				print("CSV file does not exist")

		elif choice == '3':
			objid=input("Enter object ID (use list host objects to get ID) : ")
			if debuglvl>0:
				debug("Deleting object")
			rslt=delAPIData(fmc,'/object/hosts/'+objid,APItoken)
			if debuglvl>1:
				printJSON(rslt.text)

		elif choice == '0':
			loop=False
			choice=0
		else:
			input("Incorrect selection")
	return(choice)

def debug(msg):
	print("[+] {}".format(msg))

def displayResults(txt):
	print()
	print(30 * "-"," Results ",30*"-")
	print(txt)
	print(30 * "-"," Results ",30*"-")
	print()
	input("Press enter to continue")

def getToken(fmc,username,password):
	URL = fmc + "/api/fmc_platform/v1/auth/generatetoken"
	b64login=base64.b64encode('{}:{}'.format(username.replace('\n',''),password.replace('\n','')).encode('ascii')).decode('ascii')
	authstring=("Basic {}".format(b64login))
	headers={'Authorization':authstring}
	try:
		resp = requests.post(URL,headers=headers,verify=False,proxies=proxies)
		if resp==None:
			print("Undefined response from FMC")
		if resp.status_code != 204:
			print("Error code {} received from FMC".format(resp.status_code))
			print(resp.text)
	except Exception as e:
		print("Error {}".format(e))
	return(resp.headers['X-auth-access-token'])

def getAPIData(fmc,URIpath,APItoken):
	URL=fmc+baseURIpath+URIpath
	headers={'X-auth-access-token':APItoken}
	try:
		resp=requests.get(URL,headers=headers,verify=False,proxies=proxies)
	except Exception as e:
		print("Error {}".format(e))
	return(resp)

def postAPIData(fmc,URIpath,postdata,APItoken):
	URL=fmc+baseURIpath+URIpath
	headers={'X-auth-access-token':APItoken,'Content-Type':'application/json'}
	postdata=json.dumps(postdata)
	try:
		resp=requests.post(URL,headers=headers,data=postdata,verify=False,proxies=proxies)
	except Exception as e:
		print("Error {}".format(e))
	return(resp)

def delAPIData(fmc,URIpath,APItoken):
	URL=fmc+baseURIpath+URIpath
	headers={'X-auth-access-token':APItoken}
	try:
		resp=requests.delete(URL,headers=headers,verify=False,proxies=proxies)
	except Exception as e:
		print("Error {}".format(e))
	return(resp)

def getChangeCount(fmc,deviceID,APItoken):
	URL = fmc + baseURIpath + '/deployment/deployabledevices/' + deviceID + '/pendingchanges'
	headers={'X-auth-access-token':APItoken}
	try:
		resp=requests.get(URL,headers=headers,verify=False,proxies=proxies)
	except Exception as e:
		print("Error {}".format(e))
	return json.loads(resp.text)["paging"]["count"]

def main():

	print("Obtaining API token")
	APItoken=getToken(fmc,username,password)
	loop=True
	while loop:
		rslt1=getMenu0Choice()
		if rslt1==1:
			rslt2=getMenu1Choice(fmc,APItoken)
		elif rslt1==2:
			rslt2=getMenu2Choice(fmc,APItoken)
		else:
			loop=False

baseURIpath="/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f"
requests.packages.urllib3.disable_warnings()
parser=argparse.ArgumentParser()
parser.add_argument('-d','--debug',help='debug level',required=False)
parser.add_argument('-f','--fmc',help='URL of FMC',required=False)
parser.add_argument('-u','--username',help='Username',required=False)
parser.add_argument('-p','--password',help='Password',required=False)
parser.add_argument('-P','--proxy',help='Proxy server URL',required=False)
args=parser.parse_args()

if args.fmc:
	fmc=args.fmc
else:
	fmc=input("Please enter FMC URL : ")

if args.username:
	username=args.username
else:
	username=input("Please enter username for FMC : ")

if args.password:
	password=args.password
else:
	password=getpass.getpass("Please enter password for FMC : ")

if args.proxy:
	proxies={"https":args.proxy}
else:
	proxies={}

if args.debug:
	debuglvl=int(args.debug)
else:
	debuglvl=0

if __name__ == '__main__':
	main()
