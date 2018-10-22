# http://docs.openstack.org/developer/python-novaclient/ref/v2/servers.html
import time, os, sys
import inspect
from os import environ as env

from  novaclient import client
import keystoneclient.v3.client as ksclient
from keystoneauth1 import loading
from keystoneauth1 import session
import json

def create_ansible_vm(vm_name):
	flavor = "ACCHT18.large" 
	private_net = "SNIC 2018/10-30 Internal IPv4 Network"
	floating_ip_pool_name = "Public External IPv4 network"
	image_name = "Ubuntu 16.04 LTS (Xenial Xerus) - latest"
	keypair_name = "keypairc1"

	loader = loading.get_plugin_loader('password')

	auth = loader.load_from_options(auth_url=env['OS_AUTH_URL'],
		                        username=env['OS_USERNAME'],
		                        password=env['OS_PASSWORD'],
		                        project_name=env['OS_PROJECT_NAME'],
		                        project_domain_name=env['OS_USER_DOMAIN_NAME'],
		                        project_id=env['OS_PROJECT_ID'],
		                        user_domain_name=env['OS_USER_DOMAIN_NAME'])

	sess = session.Session(auth=auth)
	nova = client.Client('2.1', session=sess)
	print "user authorization completed."

	image = nova.glance.find_image(image_name)

	flavor = nova.flavors.find(name=flavor)
	
	try:
		nova.floating_ip_pools.list()
		floating_ip = nova.floating_ips.create(nova.floating_ip_pools.list()[0].name)
	except Exception as e:
		return json.dumps({"success": False, 'message': e.message})

	if private_net != None:
	    net = nova.neutron.find_network(private_net)
	    nics = [{'net-id': net.id}]
	else:
	    sys.exit("private-net not defined.")

	#print("Path at terminal when executing this file")
	#print(os.getcwd() + "\n")
	cfg_file_path =  os.getcwd()+'/ansible_cloud-cfg.txt'
	if os.path.isfile(cfg_file_path):
	    userdata = open(cfg_file_path)
	else:
		return json.dumps({"success": False, 'message': 'Cannot find cloud-cfg.txt'})

	secgroups = ['default', 'hungphan_security_c1']

	print "Creating instance ... "
	instance = nova.servers.create(name=vm_name, 
					image=image, 
					flavor=flavor, 
					userdata=userdata, 
					nics=nics,
					security_groups=secgroups,
					key_name = keypair_name)


	inst_status = instance.status

	print "waiting for 10 seconds.. "
	time.sleep(10)

	while inst_status == 'BUILD':
	    print "Instance: "+instance.name+" is in "+inst_status+" state, sleeping for 5 seconds more..."
	    time.sleep(5)
	    instance = nova.servers.get(instance.id)
	    inst_status = instance.status

	#add floating IP to instane
	instance.add_floating_ip(floating_ip)

	return json.dumps({'success': True,
						'id': instance.id,
						'name': instance.name,
						'floating_ip': floating_ip.ip,
						'private_ip': instance.networks[private_net][0],
						'status': inst_status
	})

print create_ansible_vm('www_acc17_ansible_1_IMPORTANT')
