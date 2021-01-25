# ocp4-VM-upi-wrapper

## Description
This Install wrapper will help you to deploy new OpenShift 4 UPI clusters on top of VMs.
This wrapper can be used to deploy any OpenShift 4 minor version, the installer and the images that will be deployed will correspond to the latest ".Z" available.

## Pre-requisites
* libvirt is required, this wrapper leverages virsh and virt-install tools to deploy OS.
* tftp server is required since the servers are deployed with a specific mac.
* Webserver is required, pxe files needs some accessible path to download the required OpenShift 4 images.
* Python3 is the version being used in this wrapper.
* Python modules required to make this work:
  * sys
  * getopt
  * subprocess
  * os
  * shlex
  * shutil
  * wget
  * tarfile
  * decimal
* The pull secret available at cloud.redhat.com and your ssh id_rsa.pub key, must be located in the same dir where the wrapper is executed.

## Usage
```
./openshift4-install-wrapper-UPI.py --help
Options:
  -m, --masters <NUM_MASTERS>      | Number of masters to deploy
  -w, --workers <NUM_WORKERS>      | Number of workers to deploy
  -s, --disksize <DISK_SIZE>       | Virtual disk size
  -r, --ram <RAM_SIZE>             | Ram size
  -c, --cpus <NUM_CPUs>            | Number of CPUs per VM
  -p, --prefix <clustername>       | Name of the cluster
  -P, --path <ocp4configpath>      | Path where manifests, ignition, auth configs will be saved
  -v, --version <ocp4_version>     | OCP4 version to deploy
  -D, --destroy                    | Destroy the cluster


To create a New Environment:
Usage: ./openshift4-install-wrapper-UPI.py -m <NUM_MASTERS> -w <NUM_WORKERS> -s <DISK_SIZE_GB> -r <RAM_GB> -c <NUM_CPUS> -p <PREFIX> -P <ocp4_config_path> -v <OCP4_version>
Example: 
         \_./openshift4-install-wrapper-UPI.py -m 3 -w 2 -s 25GB -r 8G -c 4 -p ocp46 -P /home/user/ocp4/ocp46.openshift.local -v 4.6
         \_./openshift4-install-wrapper-UPI.py --masters 3 --workers 2 --disksize 25GB --ram 8G --cpus 4 --prefix ocp46 --path=/home/user/ocp4/ocp46.openshift.local --version=4.6

To destroy an existing Environment:
Usage: ./openshift4-install-wrapper-UPI.py -m <NUM_MASTERS> -w <NUM_WORKERS> -s <DISK_SIZE_GB> -r <RAM_GB> -c <NUM_CPUS> -p <PREFIX> -P <ocp4_config_path> -v 4.6 -D
Example: 
         \_./openshift4-install-wrapper-UPI.py -m 3 -w 2 -s 25GB -r 8G -c 4 -p ocp46 -P /home/user/ocp4/ocp46.openshift.local -v 4.6 -D
         \_./openshift4-install-wrapper-UPI.py --masters 3 --workers 2 --disksize 25GB --ram 8G --cpus 4 --prefix ocp46 --path=/home/user/ocp4/ocp46.openshift.local --version=4.6 -D

```
## Env VARS 
First of all, set to your custom values the following variables available at the top.
ENV | Description
----|--------------------------------------
VM_HOME | Path where VMs data will be stored
WEB_SERVER_HOME | VirtualHost Path
TFTP_HOME | Path where pxe files are placed
## Other resources
### tftpboot pxe files
Since it seems the way to deploy RHCOS has changed from OCP4.6 there are two different templates, the first is for deployments > 4.6, the second one for < 4.6.

**VERSION** string will be replaced automatically with the cluster name set as <prefix> option. Once the cluster is deployed the **VERSION** string is set back again.
```
# cat 01-00-17-a4-77-00-45

DEFAULT pxeboot
TIMEOUT 20
PROMPT 0
LABEL pxeboot
    KERNEL http://<YOUR_WEBSERVER>/rhcos-live-kernel-x86_64
    APPEND ip=192.168.122.40::192.168.122.1:255.255.255.0:VERSION.openshift.local:ens3:none nameserver=192.168.122.200 rd.neednet=1 initrd=http://<YOUR_WEBSERVER>/rhcos-live-initramfs.x86_64.img console=tty0 coreos.inst=yes coreos.inst.install_dev=vda coreos.live.rootfs_url=http://<YOUR_WEBSERVER>/rhcos-live-rootfs.x86_64.img coreos.inst.ignition_url=http://<YOUR_WEBSERVER>/bootstrap.ign
```

```
# cat 01-10-17-a4-77-00-45
DEFAULT pxeboot
TIMEOUT 20
PROMPT 0
LABEL pxeboot
    KERNEL http://<YOUR_WEBSERVER>/rhcos-installer-kernel-x86_64
    APPEND ip=192.168.122.40::192.168.122.1:255.255.255.0:VERSION.openshift.local:ens3:none nameserver=192.168.122.200 rd.neednet=1 initrd=http://<YOUR_WEBSERVER>/rhcos-installer-initramfs.x86_64.img console=tty0 coreos.inst=yes coreos.inst.install_dev=vda coreos.inst.image_url=http://<YOUR_WEBSERVER>/rhcos-metal.x86_64.raw.gz coreos.inst.ignition_url=http://<YOUR_WEBSERVER>/bootstrap.ign
```
