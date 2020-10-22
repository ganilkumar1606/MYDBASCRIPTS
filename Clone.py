#!/usr/bin/env python
#title           :clone.py
#description     :Script creates new PDB from GOLD PDB to onboard new project
#author          :Anil Guttala
#date            :12-May-2020
#version         :1
#usage           :python clone.py <New PDB name> <C##CLONE_USER password>
#notes           :
#python_version  : 3.7.6

import random
import string
from subprocess import Popen, PIPE
#import datetime
import time
import os
import sys
import getpass
import ast
import paramiko
import cx_Oracle
import linecache

#password function
def password_func(username):
	'''
	This function generates password for passed username
	'''
	num = list('0123456789')
	#print(num)
	#print(type(num))
	name = list(username)
	#print(name)
	#print(type(name))
	password = random.choice(string.ascii_letters).upper()+random.choice(name).lower()+random.choice(name).lower()+random.choice(name).lower()+random.choice(name).lower()+random.choice(name).lower()+'#'+random.choice(num)+random.choice(num)+random.choice(num)
	#+random.randint(num)+random.randint(num)+random.randint(num)+random.randint(num)
	return password

def password_map(dict1):
	'''
	This function maps users with passwords
	'''
	Dict1_Val = list(dict1.values())
	Dict1_Val_List = list()
	dictp = {}
	for name in Dict1_Val:
		for s_name in name:
			Dict1_Val_List.append(s_name)
	
	for name in Dict1_Val_List:
		if name=='Y' or name=='N' or name=='NA':
			pass
		elif name in dictp.values():
			pass
		else:
			pas=password_func(name)
			dictp[name]=pas
	return dictp


def sqlheader(Pdbname):
	'''
	This function writes spool lines into sqlfile
	'''
	with open('pdb.sql',mode='w') as f:
		f.write('set echo on\n')
		f.write('set time on\n')
		f.write('spool PDB_creation_log_{}.log\n'.format(Pdbname))
		f.write('sho con_name\n')




def runSqlQuery(sqlCommand, connectString):
	'''
	function that takes the sqlcommand and connectstring and returns the queryResult and errorMesage (if any)
	'''
	#session = Popen(['sqlplus', '-S', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	session = Popen(['sqlplus', connectString], stdin=PIPE, stdout=PIPE, stderr=PIPE)
	session.stdin.write(sqlCommand)
	return session.communicate()

def replace_str(env,reexecute_env):
	'''
	replace environment spool
	'''
	var1 = open('sqlfile.sql','rt')
	var2 = var1.read()
	var2 = var2.replace('spool user_creation_log_{}.log\n'.format(env),'spool user_creation_log_{}.log\n'.format(reexecute_env))
	var1.close()
	var1 = open('sqlfile.sql','wt')
	var1.write(var2)
	var1.close()

def CreatePDB_Write(Pdbname):
	'''
	This function writes create workspace commands to sqlfile
	'''
	with open('pdb.sql',mode='a') as f:
		f.write('alter pluggable database DFTEGOLD close immediate;\n')
		f.write("alter pluggable database DFTEGOLD open read only;\n")
		f.write("create pluggable database {} from DFTEGOLD keystore identified by {};\n".format(Pdbname,DB_password))
		f.write("alter pluggable database {} open read write;\n".format(Pdbname))

def wallet_key_check(DB_password,service_name):
	con = cx_Oracle.connect('<username >/{}@<IP Address>/{}'.format(DB_password,service_name))
	cur = con.cursor()
	cur.execute("select status from v$encryption_wallet")
	res2 = cur.fetchall()[0][0]
	#print(res[0][0])
	cur.close()
	con.close()
	return res2

def sqlheader_passreset(Pdbname,):
	'''
	This function writes spool lines into sqlfile
	'''
	with open('schemareset.sql',mode='w') as f:
		f.write('set echo on\n')
		f.write('set time on\n')
		f.write('spool Schema_pass_reset_log_{}.log\n'.format(Pdbname))
		f.write('sho con_name\n')

def schema_passreset_write(user,password):
	'''
	This function writes create schema commands to sqlfile
	'''
	with open('schemareset.sql',mode='a') as f:
		f.write('alter user {} identified by {};\n'.format(user,password))

def Keys_write(Pdbname,):
	'''
	This function writes spool lines into sqlfile
	'''
	with open('keys.txt',mode='w') as f:
		f.write('PROJECT --> {}\n'.format(Pdbname))
		f.write('=========\n')
		f.write('        ID NAME                     CLIENT_ID                      CLIENT_SECRET\n')
		f.write('---------- ------------------------ ------------------------------ ------------------------------\n')



if len(sys.argv)-1 !=2:
	print('usage:\npython clone.py <New PDB name> <C##CLONE_USER password>')
	sys.exit()

Pdbname=sys.argv[1]
DB_password=sys.argv[2]
#ords_port=sys.argv[3]
service_name=Pdbname + '.dftepublicsubne.dftevcn.oraclevcn.com'
sqlheader(Pdbname)
CreatePDB_Write(Pdbname)




connectString = '<username>/{}@<IP Address>:1521/<service_name>'.format(DB_password)

print('\n(1/5) PDB {} creation in progress......\n'.format(Pdbname))
sqlCommand = b'@pdb.sql'
queryResult, errorMessage = runSqlQuery(sqlCommand, connectString)


#with open('PDB_creation_log_{}.log'.format(Pdbname),mode='r') as f:
#	print(f.read())
con = cx_Oracle.connect('system/{}@<IP address>/<service_name>'.format(DB_password))
cur = con.cursor()
cur.execute("select open_mode from v$pdbs where name='{}'".format(Pdbname))
res = cur.fetchall()[0][0]
#print(res[0][0])
cur.close()
con.close()
if res != 'READ WRITE':
	print('Looks PDB {} failed, please check manually or contact DBA\n'.format(Pdbname))
	sys.exit()

print('\tPDB {} successfully created and is open in read-write mode \n'.format(Pdbname))

print('(2/5) Executing root scripts now...\n')
print('\tTDE key update script is running...\n')


ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('<IP Address>', username='opc', key_filename='DFTESSH.key')
stdin, stdout, stderr = ssh.exec_command('sudo sh /u01/dbcli_remote.sh {}'.format(Pdbname))
output_ssh = stdout.readlines()
#print(output_ssh)
ssh.close()

res2=wallet_key_check(DB_password,service_name)

x=1

while res2!='OPEN' and x<11:
	time.sleep(10)
	res2=wallet_key_check(DB_password,service_name)
	x+=1

if x==11 and res2!='OPEN':
	print('\nTDE KEY is not imported after 100sec, please check manually')
	sys.exit()

print ('\n\tPDB {} creation successful\n\tservice name is : {}'.format(Pdbname,service_name))


print('\n(3/5) PDB {} Schema password reset in progress......\n'.format(Pdbname))

SCHEMA_list1=['SCHEMA1','SCHEMA2']

dictp = {}

for name in SCHEMA_list1:
	pas=password_func(name)
	dictp[name]=pas

#print (dictp)

sqlheader_passreset(Pdbname)

for schema in SCHEMA_list1:
	pass1=dictp[schema]
	schema_passreset_write(schema,pass1)



connectString2 = 'system/{}@<ipaddress>:1521/{}'.format(DB_password,service_name)

sqlCommand2 = b'@schemareset.sql'

queryResult, errorMessage = runSqlQuery(sqlCommand2, connectString2)

print('\n\tPDB {} Schema password reset complete......\n'.format(Pdbname))


#print('\n(4/5) PDB {} ORDS setup and parameter file creation in progress......\n'.format(Pdbname))

#ssh = paramiko.SSHClient()
#ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#ssh.connect('<IP>', username='opc', key_filename='DFTESSH.key')
#stdin, stdout, stderr = ssh.exec_command("sudo -H -u oracle bash -c 'sh /home/oracle/ords_auto.sh {} {} {} {}'".format(Pdbname,DB_password,service_name,ords_port))
#output_ssh = stdout.readlines()
#print(output_ssh)
#ssh.close()

#print('\n\tORDS steps complete')

# print('\n(4/5) CLIENT_ID and CLIENT_SECRET Generation\n')

# print ('\n\tGenerating CLIENT_ID and CLIENT_SECRET for all DFTE SCHEMAS\n')

# for name in SCHEMA_list1:
# 	passw=dictp[name]
# 	connectString3='{}/{}@<IP address>:1521/{}'.format(name,passw,service_name)
# 	with open('Client.sql',mode='w') as f:
# 		f.write('set echo on\n')
# 		f.write('set time on\n')
# 		f.write('spool Client_{}_{}.log\n'.format(name,Pdbname))
# 		f.write('sho con_name\n')
# 		f.write('sho user\n')
# 		f.write('BEGIN\n')
# 		f.write('  OAUTH.create_client(\n')
# 		f.write("    p_name            => '{}',\n".format(name))
# 		f.write("    p_grant_type      => 'client_credentials',\n")
# 		f.write("    p_owner           => '{}',\n".format(name))
# 		f.write("    p_description     => 'Client for DFTE',\n")
# 		f.write("    p_support_email   => 'usindiaoracledfteplatformsecurity@deloitte.com',\n")
# 		f.write("    p_privilege_names => 'oracle.dbtools.autorest.privilege.{}'\n".format(name))
# 		f.write('  );\n')
# 		f.write('  COMMIT;\n')
# 		f.write('END;\n')
# 		f.write('/\n')
# 		f.write('BEGIN\n')
# 		f.write('  OAUTH.grant_client_role(\n')
# 		f.write("    p_client_name => '{}',\n".format(name))
# 		f.write("    p_role_name   => 'oracle.dbtools.role.autorest.{}'\n".format(name))
# 		f.write('  );\n')
# 		f.write('  COMMIT;\n')
# 		f.write('END;\n')
# 		f.write('/\n')
# 		f.write('set lines 200\n')
# 		f.write('set trimspool on\n')
# 		f.write('col client_id for a30\n')
# 		f.write('col client_secret for a30\n')
# 		f.write('col name for a24\n')
# 		f.write('SELECT id, name, client_id, client_secret FROM   user_ords_clients;\n')
# 	print('\n\t\tGenerating CLIENT_ID,CLIENT_SECRET for {}.....\n'.format(name))
# 	sqlCommand3 = b'@Client.sql'
# 	queryResult, errorMessage = runSqlQuery(sqlCommand3, connectString3)

# print ('\n\tGenerating CLIENT_ID and CLIENT_SECRET for all DFTE SCHEMAS in DFTE_PLATFORM_HOME_APPS workspace\n')

# with open('ClientHOME.sql',mode='w') as f:
# 			f.write('set echo on\n')
# 			f.write('set time on\n')
# 			f.write('spool ClientHome_{}.log\n'.format(Pdbname))
# 			f.write('sho con_name\n')
# 			f.write('sho user\n')


# for name in SCHEMA_list1:
# 	if name == 'DFTE_PLATFORM_HOME_APPS':
# 		pass
# 	else:
# 		passw=dictp['DFTE_PLATFORM_HOME_APPS']
# 		connectString4='DFTE_PLATFORM_HOME_APPS/{}@<IPadd:1521/{}'.format(passw,service_name)
# 		with open('ClientHOME.sql',mode='a') as f:
# 			f.write('BEGIN\n')
# 			f.write('  OAUTH.create_client(\n')
# 			f.write("    p_name            => '{}',\n".format(name))
# 			f.write("    p_grant_type      => 'client_credentials',\n")
# 			f.write("    p_owner           => '{}',\n".format(name))
# 			f.write("    p_description     => 'Client for DFTE',\n")
# 			f.write("    p_support_email   => 'usindiaoracledfteplatformsecurity@deloitte.com',\n")
# 			f.write("    p_privilege_names => 'oracle.dbtools.autorest.privilege.DFTE_PLATFORM_HOME_APPS'\n")
# 			f.write('  );\n')
# 			f.write('  COMMIT;\n')
# 			f.write('END;\n')
# 			f.write('/\n')
# 			f.write('BEGIN\n')
# 			f.write('  OAUTH.grant_client_role(\n')
# 			f.write("    p_client_name => '{}',\n".format(name))
# 			f.write("    p_role_name   => 'oracle.dbtools.role.autorest.DFTE_PLATFORM_HOME_APPS'\n")
# 			f.write('  );\n')
# 			f.write('  COMMIT;\n')
# 			f.write('END;\n')
# 			f.write('/\n')

# with open('ClientHOME.sql',mode='a') as f:
# 	f.write('set lines 200\n')
# 	f.write('set trimspool on\n')
# 	f.write('col client_id for a30\n')
# 	f.write('col client_secret for a30\n')
# 	f.write('col name for a24\n')
# 	f.write('SELECT id, name, client_id, client_secret FROM   user_ords_clients;\n')

# sqlCommand4 = b'@ClientHOME.sql'
# queryResult, errorMessage = runSqlQuery(sqlCommand4, connectString4)


# print('\n(5/5) Generating keys.txt file \n')

# Keys_write(Pdbname)
# for doc in SCHEMA_list1:
# 	file = 'Client_'+doc+'_'+Pdbname+'.log'
# 	line_write=linecache.getline(file,43)
# 	#print(line_write)
# 	with open('keys.txt',mode='a') as f:
# 		f.write('{}\n'.format(line_write))

print('keys.txt generated \n')
print('Service   name is ---> {}\n'.format(service_name))
print('Apex/ORDS url  is ---> https://qa-myapex-oracleofferringdfte.deloitte.com/ords/{}'.format(Pdbname))

