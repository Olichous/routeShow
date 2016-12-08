#! /usr/bin/python

##########################
#
# Get prefix and Argument
#
##########################

# Main

if __name__ == "__main__":


  ''' Import Module : Pyez / Yaml / Getpass (Password) / SYS / Paramiko (for SSH) / OS (for path ssh) / Requests (HTTP requests) / Json for transformation in dictionary'''
  import yaml
  import sys
  import paramiko
  import os
  import re
  import requests
  import json
  import community
  import routers
  from pprint import pprint
  from jnpr.junos import Device
  from jnpr.junos.factory import loadyaml
  from termcolor import colored


  # Import bgpRoutes & bgpView
  mydefs = loadyaml('bgpRoutes.yml')
  globals().update(mydefs)


  # Import allRoutes & allView
  mysecddefs = loadyaml('allRoutes.yml')
  globals().update(mysecddefs)

  # Import ifDescription & ifView
  mythirdddefs = loadyaml('ifDescription.yml')
  globals().update(mythirdddefs)

  #We take the first argument of the prompt data. Put the Prefix Here
  URL = (sys.argv)
#  print str(URL[1])

  # Use .ssh/config file
  config_file = os.path.join(os.getenv('HOME'),'.ssh/config')
  ssh_config = paramiko.SSHConfig()
  ssh_config.parse(open(config_file,'r'))
  got_lkup = ssh_config.lookup( "Your Device" )

  # Connect to the device
  dev = Device(host=got_lkup['hostname'], user="xxxx", password="xxxx", gather_facts=False)
  dev.open()

  # Obtain bgpView for the prefix x.x.x.x/x

  routeBgpTable = bgpRoutes(dev).get("%s" % str(URL[1]))

  #Save the prefix for futur usage
  prefix = str(URL[1])
  # Print Information on the p)refix
  for item in routeBgpTable:
   # Print the Route To :
   print (colored( "Route To : "+item.rt_destination+"/"+item.rt_prefix_length, 'red', attrs=['bold', 'underline']))

   # We transform as_path into string and take only the originator id
   as_path = str(item.as_path)
   originator_id = [re.findall(r'Originator ID: ([^ ]+)', p) for p in [as_path]]

   # If the prefix is learned in eBGP
   if item.bgp_type == "Active Ext":

    # If it is an IP from YOUR-AS 
    if item.protcol_nh is not None :
     print (colored( "Learn from : "+routers.routerYourCommunity[item.protcol_nh[0]]+" via "+routers.routerYourCommunity[item.gateway], 'green', attrs=['blink']))
    # Else if it is not
    else:
     print (colored( "Learn from : local via "+item.gateway, 'green', attrs=['blink']))
     # Verify that the interface next-hop exist
     if (item.nh_via is not None):
      # Make a "show interface [ge|xe]-x/x/x description" to obtain the description of the interface
      src_local_ifTable = ifDescription(dev).get("%s" %item.nh_via)
      for iface in src_local_ifTable:
        if iface.description != [[]]:
         print (" The Client is " +iface.description)

    # If there is an Originator ID
    if originator_id != [[]]:
     # Print the originator id
     originator_id = sum(originator_id,[])[0]
     print (" Originator ID :"+originator_id)

    as_path = [re.findall(r'AS path: ([0-9 ]+[I|?])', p) for p in [as_path]]
    # If the AS_PATH exist get the AS_PATH and print
    if as_path != [[]]:
     as_path = str(as_path[0][0])
     as_path_split = as_path.split(" ")
     print (" AS Path: "+as_path)
     # Initiate a variable for the loop
     p=0
     # Associate the AS number with the AS Name Human Readable
     for t in as_path_split:
      if t not in ("I","?"):
       r = requests.get("http://api.moocher.io/as/num/%s" % str(t))
       as_dict = json.loads(r.text)
       print (" Hop "+str(p)+" : "+as_dict["as"]["name"])
       p+=1

    # Try to associate community with dictionnary community YourCommunity
    i=0
    for j in item.community:
     # If community appear in communityYourCommunity print it
     if community.communityYourCommunity.has_key(j) is True:
      print (colored(" Community : " +community.communityYourCommunity.get(j), 'cyan'))
     else:
      # If is does not appear print the value xxxx:xxxx
      print (colored(" Community : "+str(item.community[i]), 'cyan'))
     i+=1
    # Print the Local preference
    if item.local_preference is not None :
     print (colored(" Local Preference is "+item.local_preference, 'magenta'))
    else:
     print (colored(" No Local Pref", 'magenta'))

    # Print the MED
    if item.med is not None :
     print (colored (" MED is "+item.med, 'magenta'))
    else:
     print (colored (" No MED", 'magenta'))

   # If the prefix is learn in iBGP
   else:

    # If it is an IP from YOUR-AS
    if (item.protcol_nh is not None):
      print (colored( "Learn from : "+routers.routerYourCommunity[item.protcol_nh[0]]+" via "+routers.routerYourCommunity[item.gateway], 'green', attrs=['blink']))

      # Let's find from wich interface it's come from
      # Connect to the source router that announce this prefix
      router_source = str(routers.routerYourCommunity[item.protcol_nh[0]])
      router_source_got_lkup = ssh_config.lookup(router_source)
      dev_source_route = Device(host=router_source_got_lkup["hostname"], user="xxxx", password="xxxx", gather_facts=False)
      dev_source_route.open()

      # Obtain the next-hop of the "show route x.x.x.x/x"
      src_router_routeTable = allRoutes(dev_source_route).get(""+item.rt_destination+"/"+item.rt_prefix_length)
      # Look in the answer to find the interface next-hop
      for pref in src_router_routeTable:
       if_nh = pref.nh_via
       # Verify that the interface next-hop exist
       if (if_nh is not None) and (pref.rt_destination+"/"+pref.rt_prefix_length == ""+item.rt_destination+"/"+item.rt_prefix_length):
        # Make a "show interface [ge|xe]-x/x/x description" to obtain the description of the interface
        src_router_ifTable = ifDescription(dev_source_route).get("%s" %if_nh)
        for interface in src_router_ifTable:
         if interface.description != [[]]:
          print (" The Client is " +interface.description)
      # Close the connection to the router that origin the route
      dev_source_route.close()
    # Else if it is not
    else:
     if item.gateway is not None:
      print (colored( "Learn from : local via "+item.gateway, 'green', attrs=['blink']))

    # If there is an Originator ID
    if originator_id != [[]]:
     # Print the originator id
     originator_id = sum(originator_id,[])[0]
     print (" Originator ID :"+originator_id)

    as_path = [re.findall(r'AS path: ([0-9 ]+[I|?])', p) for p in [as_path]]
    # If the AS_PATH exist get the AS_PATH and print
    if as_path != [[]]:
     as_path = str(as_path[0][0])
     as_path_split = as_path.split(" ")
     print (" AS Path: "+as_path)
     # Initiate a variable for the loop
     p=0
     # Associate the AS number with the AS Name Human Readable
     for t in as_path_split:
      if t not in ("I","?"):
       r = requests.get("http://api.moocher.io/as/num/%s" % str(t))
       as_dict = json.loads(r.text)
       print (" Hop "+str(p)+" : "+as_dict["as"]["name"])
       p+=1

    # Try to associate community with dictionnary community 8218
    i=0
    for j in item.community:
     # If community appear in communityYourCommunity print it
     if community.communityYourCommunity.has_key(j) is True:
      print (colored(" Community : " +community.communityYourCommunity.get(j), 'cyan'))
     else:
      # If is does not appear print the value xxxx:xxxx
      print (colored(" Community : "+str(item.community[i]), 'cyan'))
     i+=1
    # Print the Local preference
    if item.local_preference is not None :
     print (colored(" Local Preference is "+item.local_preference, 'magenta'))
    else:
     print (colored(" No Local Pref", 'magenta'))

    # Print the MED
    if item.med is not None :
     print (colored (" MED is "+item.med, 'magenta'))
    else:
     print (colored (" No MED", 'magenta'))

    # Name of the interface where the prefix was learned


  # Close the connection

  dev.close()
