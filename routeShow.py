##########################
# 
# Get prefix and Argument
#
##########################

# Main 

if __name__ == "__main__":


		''' Import Module : Pyez / Yaml / Getpass (Password) / SYS / Paramiko (for SSH) / OS (for path ssh)'''
		import yaml
		import sys
		import paramiko 
		import os
		import re
		from pprint import pprint
		from jnpr.junos import Device
		from jnpr.junos.factory import loadyaml


		# Import bgpRoutes & bgpView
		mydefs = loadyaml('bgpRoutes.yml')
		globals().update(mydefs)

		#We take the first argument of the prompt data. Put the Prefix Here
		URL = (sys.argv)
    
		# Use .ssh/config file
		config_file = os.path.join(os.getenv('HOME'),'.ssh/config')
		ssh_config = paramiko.SSHConfig()
		ssh_config.parse(open(config_file,'r'))
		got_lkup = ssh_config.lookup( "your device" )

		# Connect to the device
		dev = Device(host=got_lkup['hostname'], user="xxx", password="xxx", gather_facts=False)
		dev.open()
		
		# Obtain bgpView for the prefix x.x.x.x/x
		
		routeBgpTable = bgpRoutes(dev).get("%s" % str(URL[1]))
		# Print Information on the prefix 
		for item in routeBgpTable:
				print ("Route To : "+item.rt_destination+"/"+item.rt_prefix_length)
        
				# We transform as_path into string and take only the originator id 
				as_path = str(item.as_path[0])
				originator_id = [re.findall(r'Originator ID: ([^ ]+)', p) for p in [as_path]]
        
        # Check If there ise an originator ID else then dont print it !
				if originator_id != [[]]:
						originator_id = sum(originator_id,[])[0]
						print (" Originator ID :"+originator_id)
						i=0
						for j in item.community:
								print (" Community :"+str(item.community[i]))
								i+=1
				else:
						as_path = [re.findall(r'AS path: ([0-9 ]+I)', p) for p in [as_path]]
						print (" AS Path: "+str(as_path[0][0]))
						i=0
						for j in item.community:
								print (" Community :"+str(item.community[i]))
								i+=1
		
		# Close the connection 

		dev.close()

