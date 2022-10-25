#!/usr/bin/python3
#
# DESCRIPTION: This script has been designed to help with the VM provisioning task.
#
# AUTHOR: Victor Hernando
# DATE: 2020-11-13

import sys
import getopt
import subprocess
import os.path
import shlex
import shutil
import wget
import tarfile
from decimal import Decimal, ROUND_HALF_EVEN

# VARS
VM_HOME = '/home/VMs/'
WEB_SERVER_HOME = '/www'
TFTP_HOME = '/var/lib/tftpboot/pxelinux.cfg'
# END VARS

global vm

def logger(lvl, msg):
  print(lvl + ': ' + msg)
  
def help():
  print('\n***                       ***')
  print('*** OCP 4 UPI provisioner ***')
  print('***                       ***')
  print('\nThis script has been designed to deploy automatically an OCP4 cluster with the following specifications and requirements:')
  print('\__ 1. Libvirt has to be installed, VMs are deployed with virt-install tool.')
  print('\__ 2. Tftp has to be installed, VMs are deployed automatically with pxeboot.')
  print('\__ 3. A webserver is required to serve bootstrap files and images required for the installation.')
  print('\__ 4. Set ${VM_HOME} ${WEB_SERVER_HOME} and ${TFTP_HOME} in the VARS section.')
  print('\__ 5. A mac address pattern has been defined, if you want to choose another set of mac address, feel free to do it.')
  print('\__ 6. You can choose any OpenShift minor version, the installer will deploy the latest minor available, no option to choose any "4.y.Z"')
  print('\__ 7. The pull secret available to download from cloud.redhat.com (pull-secret.txt) must be located in the same dir where the installer is executed.')
  print('\__ 8. The ssh key used to be able to connect to RHCOS nodes must be located in the same dir where the installer is executed, as a ssh-key.txt file\n')
  print('Options:')
  print('  -m, --masters <NUM_MASTERS>      | Number of masters to deploy')
  print('  -w, --workers <NUM_WORKERS>      | Number of workers to deploy')
  print('  -s, --disksize <DISK_SIZE>       | Virtual disk size')
  print('  -r, --ram <RAM_SIZE>             | Ram size')
  print('  -c, --cpus <NUM_CPUs>            | Number of CPUs per VM')
  print('  -p, --prefix <clustername>       | Name of the cluster')
  print('  -P, --path <ocp4configpath>      | Path where manifests, ignition, auth configs will be saved')
  print('  -v, --version <ocp4_version>     | OCP4 version to deploy')
  print('  -D, --destroy                    | Destroy the cluster')
  print('\n\nTo create a New Environment:')
  print('Usage: ' + sys.argv[0] + ' -m <NUM_MASTERS> -w <NUM_WORKERS> -s <DISK_SIZE_GB> -r <RAM_GB> -c <NUM_CPUS> -p <PREFIX> -P <ocp4_config_path> -v <OCP4_version>')
  print('Example: ')
  print('         \_' + sys.argv[0] + ' -m 3 -w 2 -s 25GB -r 8G -c 4 -p ocp46 -P /home/user/ocp4/ocp46.openshift.local -v 4.6')
  print('         \_' + sys.argv[0] + ' --masters 3 --workers 2 --disksize 25GB --ram 8G --cpus 4 --prefix ocp46 --path=/home/user/ocp4/ocp46.openshift.local --version=4.6')
  print('')
  print('To destroy an existing Environment:')
  print('Usage: ' + sys.argv[0] + ' -m <NUM_MASTERS> -w <NUM_WORKERS> -s <DISK_SIZE_GB> -r <RAM_GB> -c <NUM_CPUS> -p <PREFIX> -P <ocp4_config_path> -v 4.6 -D')
  print('Example: ')
  print('         \_' + sys.argv[0] + ' -m 3 -w 2 -s 25GB -r 8G -c 4 -p ocp46 -P /home/user/ocp4/ocp46.openshift.local -v 4.6 -D')
  print('         \_' + sys.argv[0] + ' --masters 3 --workers 2 --disksize 25GB --ram 8G --cpus 4 --prefix ocp46 --path=/home/user/ocp4/ocp46.openshift.local --version=4.6 -D')
  print('')

def check_ocp4path(ocp4path):
  logger('INFO', 'Checking whether the OCP4 config path exists or not...')
  if os.path.isdir(ocp4path):
    logger('WARNING', 'Path ' + ocp4path + ' exists!!, you might run into cert issues while using a pre created config path from previous installations.')
    inp = input('Do you want to continue?')
    if inp.lower() == 'yes' or inp.lower() == 'y' :
      logger('INFO', 'OK, validated, proceeding...')
    else:
      sys.exit(3)
  else:
    logger('INFO', 'Creating a new OCP4 config path...')
    os.makedirs(ocp4path)

def createocp4config(ocp4path,prefix,version):
  urlinst = 'https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest-' + str(version) + '/openshift-install-linux.tar.gz'
  urlcli = 'https://mirror.openshift.com/pub/openshift-v4/clients/ocp/latest-' + str(version) + '/openshift-client-linux.tar.gz'
  
  if version.compare(Decimal(4.5).quantize(Decimal('.1'), rounding=ROUND_HALF_EVEN)) > 0 :
    urlrhcosiram = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-live-initramfs.x86_64.img'
    urlrhcosker = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-live-kernel-x86_64'
    urlrhcosroot = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-live-rootfs.x86_64.img'
  else:
    urlrhcosiram = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-installer-initramfs.x86_64.img'
    urlrhcosker = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-installer-kernel-x86_64'
    urlrhcosroot = 'https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/' + str(version) + '/latest/rhcos-metal.x86_64.raw.gz'
    
  for url in urlinst,urlcli:
    filename = os.path.basename(url)
    if os.path.exists(filename):
      logger('INFO', 'File ' + filename + ' exists, removing...')
      os.remove(filename)
  logger('\nINFO', 'Downloading OpenShift4 installer... [' + urlinst + ']')
  installertar = wget.download(urlinst)
  logger('\nINFO', 'Downloading OpenShift4 CLI... [' + urlcli + ']')
  clitar = wget.download(urlcli)
  logger('\nINFO', 'Downloading OpenShift4 Live Initramfs... [' + urlrhcosiram + ']')
  wget.download(urlrhcosiram)
  logger('\nINFO', 'Downloading OpenShift4 Live Kernel... [' + urlrhcosker + ']')
  wget.download(urlrhcosker)
  logger('\nINFO', 'Downloading OpenShift4 Live rootfs... [' + urlrhcosroot + ']')
  wget.download(urlrhcosroot)
  
  logger('\nINFO', 'Copy OpenShift4 Images into the webserver dir...')
  initram = os.path.basename(urlrhcosiram)
  kernel = os.path.basename(urlrhcosker)
  rootfs = os.path.basename(urlrhcosroot)
  for imageFile in initram,kernel,rootfs:
    try:
      shutil.copyfile(imageFile, '/www/' + imageFile )
      os.remove(imageFile)
    except:
      logger('\nINFO', 'Error making copy of ' + imageFile )
      sys.exit(2)
  
  logger('INFO', 'Extracting OpenShift4 installer...')
  with tarfile.open(installertar, 'r') as archive:
    def is_within_directory(directory, target):
        
        abs_directory = os.path.abspath(directory)
        abs_target = os.path.abspath(target)
    
        prefix = os.path.commonprefix([abs_directory, abs_target])
        
        return prefix == abs_directory
    
    def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    
        for member in tar.getmembers():
            member_path = os.path.join(path, member.name)
            if not is_within_directory(path, member_path):
                raise Exception("Attempted Path Traversal in Tar File")
    
        tar.extractall(path, members, numeric_owner=numeric_owner) 
        
    
    safe_extract(archive)
  
  logger('INFO', 'Extracting OpenShift4 CLI...')
  with tarfile.open(clitar, 'r') as archive:
    def is_within_directory(directory, target):
        
        abs_directory = os.path.abspath(directory)
        abs_target = os.path.abspath(target)
    
        prefix = os.path.commonprefix([abs_directory, abs_target])
        
        return prefix == abs_directory
    
    def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
    
        for member in tar.getmembers():
            member_path = os.path.join(path, member.name)
            if not is_within_directory(path, member_path):
                raise Exception("Attempted Path Traversal in Tar File")
    
        tar.extractall(path, members, numeric_owner=numeric_owner) 
        
    
    safe_extract(archive)
  logger('INFO', 'Copying the OpenShift4 CLI to /usr/local/bin...')
  subprocess.call(["/usr/bin/sudo","/usr/bin/cp", "oc", "/usr/local/bin/oc"])
  
  # Get the pull-secret from pull-secret.txt
  with open('pull-secret.txt', 'r') as psfile:
    pullsecret = psfile.read().replace('\n','')
  # Get the ssh-key frile from ssh-key.txt
  with open('ssh-key.txt', 'r') as skfile:
    sshkey = skfile.read().replace('\n','')
  # pull-secret and ssh key file must be in place to continue
  for file in ('pull-secret.txt','ssh-key.txt'):
    if os.path.isfile(file):
      logger('INFO', 'File ' + file + ' is in place, ready to continue...')
    else:
      sys.exit(1)
  
  # Insert the pull-secret and the ssk-key into the install-config-template
  logger('INFO', 'Adding pull-secret and ssh key into the install-config file...')
  shutil.copyfile('install-config-template.yaml','install-config.yaml')
  fin = open("install-config.yaml","rt")
  data = fin.read()
  data = data.replace('pullSecret:','pullSecret: ' + '\'' + pullsecret + '\'')
  data = data.replace('sshKey:','sshKey: ' + '\'' + sshkey + '\'')
  data = data.replace('name: cluster_name','name: ' + prefix)
  fin.close()
  fin = open("install-config.yaml","wt")
  fin.write(data)
  fin.close()
  
  shutil.copyfile('install-config.yaml', ocp4path + '/install-config.yaml')
  # running openshift-install create manifests
  logger('\nINFO', 'Creating manifests...')
  subprocess.call(["./openshift-install", "create", "manifests", "--dir=" + ocp4path])
  
  # Replacing mastersSchedulable from true to false
  logger('\nINFO', 'Replacing mastersSchedulable from true to false...')
  fin = open(ocp4path + "/manifests/cluster-scheduler-02-config.yml","rt")
  data = fin.read()
  data = data.replace('mastersSchedulable: true','mastersSchedulable: false')
  fin.close()
  fin = open(ocp4path + "/manifests/cluster-scheduler-02-config.yml","wt")
  fin.write(data)
  fin.close()
  
  # running openshift-install create ignition-configs
  logger('\nINFO', 'Creating Ignition configs...')
  subprocess.call(["./openshift-install", "create", "ignition-configs", "--dir=" + ocp4path])
  
  # Copy bootstrap files to webserver dir
  logger('\nINFO', 'Copy Ignition configs to the webserver dir...')
  subprocess.call(["/usr/bin/sudo","/usr/bin/cp", ocp4path + "/bootstrap.ign", "/www/bootstrap.ign"])
  subprocess.call(["/usr/bin/sudo","/usr/bin/cp", ocp4path + "/worker.ign", "/www/worker.ign"])
  subprocess.call(["/usr/bin/sudo","/usr/bin/cp", ocp4path + "/master.ign", "/www/master.ign"])
  
def checkdisks(diskpath):
  logger('\nINFO', 'Checking whether disks already exists or not...')
  if os.path.isfile(diskpath):
    logger('WARNING', 'File ' + diskpath + ' exists!!')
    inp = input('Do you want to continue? This operation will destroy your data!!!')
    if inp.lower() == 'yes' or inp.lower() == 'y' :
      logger('INFO', 'OK, validated, proceeding...')
    else:
      sys.exit(3)
  else:
    logger('INFO', 'File ' + diskpath + ' does not exist, proceeding...')

def diskprovisioner(masters,workers,disksize,prefix):
  vm = []
  dp = []
  vmdp = []
  logger('\nINFO', 'Provisioning disks...')
  
  # Bootstrap first
  vmname = prefix + 'bs'
  diskProvisionerExec(vm,dp,vmdp,vmname,disksize)
  
  for master in ( number+1 for number in range(int(masters))):
    master = str(master)
    vmname = prefix + 'm' + master
    diskProvisionerExec(vm,dp,vmdp,vmname,disksize)
    
  for worker in ( number+1 for number in range(int(workers))):
    worker = str(worker)
    vmname = prefix + 'w' + worker
    diskProvisionerExec(vm,dp,vmdp,vmname,disksize)

  return(vm,dp)
  
def diskProvisionerExec(vm,dp,vmdp,vmname,disksize):
  vm.append(vmname)
  vmdiskpath = VM_HOME + vmname
  vmdp.append(vmdiskpath)
  diskpath = VM_HOME + vmname + '/' + vmname + '-disk1.qcow2'
  dp.append(diskpath)
  checkdisks(diskpath)
  logger('INFO', 'Creating ' + vmname + ' disk in ' + diskpath)
  qemuprovisioner(vmdiskpath,diskpath, disksize)
  
def qemuprovisioner(vmdiskpath,diskpath, disksize):
  if os.path.isdir(vmdiskpath):
    logger('INFO', 'Path ' + vmdiskpath + ' exists')
  else:
    logger('WARNING', 'Path ' + vmdiskpath + ' does not exists, creating path...')
    subprocess.call(["/usr/bin/sudo","/usr/bin/mkdir", vmdiskpath])
  
  subprocess.call(["/usr/bin/sudo","/usr/bin/qemu-img", "create", "-f", "qcow2", "-o", "preallocation=metadata", diskpath , disksize + "G"])

def virtInstall(vm,ram,cpus,diskpath,version):
  num = 0
  for server in vm:
    if version.compare(Decimal(4.5).quantize(Decimal('.1'), rounding=ROUND_HALF_EVEN)) > 0 :
      macFile = '01-00-17-a4-77-0' + str(num) + '-45'
      macAddress = '00:17:a4:77:0' + str(num) + ':45'
    else:
      macFile = '01-10-17-a4-77-0' + str(num) + '-45'
      macAddress = '10:17:a4:77:0' + str(num) + ':45'
    
    logger('INFO', 'Installing ' + server + ' ...')
    configTftpFiles(macFile,server)
    s = "/usr/bin/sudo /usr/bin/virt-install --pxe -n " + server + " --os-type=Linux --ram " + str(int(ram)*1024) + " --vcpus " + str(cpus) + " --disk=" + diskpath[num] + ",bus=virtio,size=10 --network bridge=virbr0,mac=" + macAddress
    task = shlex.split(s)
    subprocess.call(task)
    rollbackTftpFiles(macFile,server)
    
    num += 1

def configTftpFiles(macFile,server):
  # Replacing version in tftpboot files
  logger('INFO', 'Replacing version in tftpboot files...')
  fin = open(TFTP_HOME + "/" + macFile,"rt")
  data = fin.read()
  data = data.replace('VERSION',server)
  fin.close()
  fin = open(TFTP_HOME + "/" + macFile,"wt")
  fin.write(data)
  fin.close()
  
def rollbackTftpFiles(macFile,server):
  # Replacing version in tftpboot files
  logger('INFO', 'Replacing version in tftpboot files...')
  fin = open(TFTP_HOME + "/" + macFile,"rt")
  data = fin.read()
  data = data.replace(server,'VERSION')
  fin.close()
  fin = open(TFTP_HOME + "/" + macFile,"wt")
  fin.write(data)
  fin.close()
  
def destroyenv(masters,workers,prefix,ocp4path):
  vmname = prefix + 'bs'
  destroyEnvExec(vmname,ocp4path)
  
  for master in ( number+1 for number in range(int(masters))):
    master = str(master)
    vmname = prefix + 'm' + master
    destroyEnvExec(vmname,ocp4path)
    
  for worker in ( number+1 for number in range(int(workers))):
    worker = str(worker)
    vmname = prefix + 'w' + worker
    destroyEnvExec(vmname,ocp4path)

  logger('INFO', 'Removing OCP4 config files...')
  shutil.rmtree(ocp4path)

def destroyEnvExec(vmname,ocp4path):
  diskpath = VM_HOME + vmname + '/' + vmname + '-disk1.qcow2'
  logger('INFO', 'Destroying, undefining server ' + vmname + ' , and removing disks...')
  destroy = "/usr/bin/sudo /usr/bin/virsh destroy " + vmname
  undefine = "/usr/bin/sudo /usr/bin/virsh undefine " + vmname
  removedisk = "/usr/bin/sudo /usr/bin/rm " + diskpath
  destroytask = shlex.split(destroy)
  subprocess.call(destroytask)
  undefinetask = shlex.split(undefine)
  subprocess.call(undefinetask)
  removetask = shlex.split(removedisk)
  subprocess.call(removetask)

def precheck_services():
  logger('INFO', 'Checking whether HTTPD service is up...')
  stat = os.system('/usr/bin/sudo systemctl status httpd')
  if stat == 0:
    logger('INFO', 'HTTPD is running, going ahead')
  else:
    logger('WARNING', 'HTTPD is dead, starting the service...')
    os.system('/usr/bin/sudo systemctl start httpd')
    
  logger('INFO', 'Checking whether TFTP service is up...')
  stat = os.system('/usr/bin/sudo systemctl status tftp')
  if stat == 0:
    logger('INFO', 'TFTP is running, going ahead')
  else:
    logger('WARNING', 'TFTP is dead, starting the service...')
    os.system('/usr/bin/sudo systemctl start tftp')

def waitForBootstrap(ocp4path):
  logger('\nINFO', 'Waiting for Bootstrap...')
  try:
    subprocess.call(["./openshift-install", "--dir=" + ocp4path, "wait-for", "bootstrap-complete", "--log-level=info"])
    logger('\nINFO', 'Time to remove the bootstrap server from the Load Balancer! Check for any csr pending in your cluster, the workers are waiting for that approval to join the cluster!')
  except:
    logger('\nWARNING', 'Something went wrong, check for errors in bootstrap and master servers...')
    sys.exit(2)
    
def pendingTasks(ocp4path):
  logger('\nINFO', 'The cluster is up & running!')
  logger('INFO', 'There are two additional steps pending though, it is required manual intervention!')
  logger('INFO', '\__ 0.- Log in your cluster.')
  logger('INFO', '\____-> export KUBECONFIG=$' + ocp4path + '/auth/kubeconfig')
  logger('INFO', '\__ 1.- Approve the csr from the worker nodes that should pop up soon.')
  logger('INFO', '\____-> oc get csr -o go-template=\'{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}\' | xargs oc adm certificate approve')
  logger('INFO', '\__ 2.- The registry is not deployed by default, it is required to set up the registry by hand.')
  logger('INFO', '\____-> Verify that there is not any registry pod running')
  logger('INFO', '\_______-> $ oc get pod -n openshift-image-registry')
  logger('INFO', '\____-> Set the operator to Managed, it is Removed by default')
  logger('INFO', '\_______-> $ oc edit configs.imageregistry/cluster')
  logger('INFO', '\_______-> Change: managementState: Removed -> managementState: Managed')
  logger('INFO', '\____-> Configure the storage to an empty Directory (only for NON-PRODUCTION clusters)')
  logger('INFO', '\_______-> $ oc patch configs.imageregistry.operator.openshift.io cluster --type merge --patch \'{"spec":{"storage":{"emptyDir":{}}}}\'')
  logger('INFO', '\__ 3.- Wait till all the cluster operators are AVAILABLE.')
  logger('INFO', '\____-> $ oc get clusteroperator')

def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], "hm:w:s:r:c:p:P:v:D", ["help", "masters=", "workers=", "disksize=", "ram=", "cpus=", "prefix=", "path=", "version=", "destroy"])
    if not opts:
      print('No options provided')
      help()
      sys.exit(1)
  except getopt.GetoptError as err:
    print(err)
    help()
    sys.exit(2)
  for opt, arg in opts:
    if opt in ("-h", "--help"):
      help()
      sys.exit(0)
    elif len(opts) < 8:
      logger('ERROR', 'MISSING REQUIRED ARGUMENTS')
      sys.exit(2)
    elif opt in ("-m", "--masters"):
      masters = arg
    elif opt in ("-w", "--workers"):
      workers = arg
    elif opt in ("-s", "--disksize"):
      disksize = arg.split("GB")[0]
    elif opt in ("-r", "--ram"):
      ram = arg.split("G")[0]
    elif opt in ("-c", "--cpus"):
      cpus = arg
    elif opt in ("-p", "--prefix"):
      prefix = arg
    elif opt in ("-P", "--path"):
      ocp4path = arg
    elif opt in ("-v", "--version"):
      version = Decimal(arg).quantize(Decimal('.1'), rounding=ROUND_HALF_EVEN)
    elif opt in ("-D", "--destroy"):
      destroyenv(masters,workers,prefix,ocp4path)
      sys.exit(0)
  
  # VM = function to get the server names
  precheck_services()
  check_ocp4path(ocp4path)
  createocp4config(ocp4path,prefix,version)
  vm, dp = diskprovisioner(masters,workers,disksize,prefix)
  virtInstall(vm,ram,cpus,dp,version)
  waitForBootstrap(ocp4path)
  pendingTasks(ocp4path)
  
## MAIN ##
if __name__=='__main__':
  main()
## END MAIN ##
