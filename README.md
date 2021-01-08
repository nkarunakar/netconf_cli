# Command line tool to execute NETCONF get calls using ncclient. 

An automated python script for execution of NETCONF get/getconfig calls (on specified yangs, All yangs, ROOT node),collect all supported YANG files & print capabilities.

## REQUIREMENTS:
***
ncclient==0.6.7

lxml==4.5.2

## Usage is as below
---
```>python netconf_cli.py -h
usage: netconf_cli [-h] [-A | -F {get,getconfig}] [--port PORT] [-p <<C:\Yangfile\example.yang>> or <<C:\YangDir\>>]
                   [-m {get,getconfig}]
                   nchost username password

Make NETCONF get or getconfig calls to NETCONF supported device

optional arguments:
  -h, --help            show this help message and exit
  -A, --allyang         Collect All YANG files
  -F {get,getconfig}, --fullconfig {get,getconfig}
                        Collect FULL configuration in an XML, GET/GETCONFIG oN ROOT XML node

  nchost                IP address of the NETCONF device
  username              Username of the device
  password              Password of the device
  --port PORT           NETCONF port, Default is 830 when not specified

  -p <<C:\Yangfile\example.yang>> or <<C:\YangDir\>>, --path <<C:\Yangfile\example.yang>> or <<C:\YangDir\>>
                        Absolute path to a specific YANG file or folder containing YANGs
  -m {get,getconfig}, --method {get,getconfig}
                        Specify get or getconfig calls
 ```
 
 ### Various options supported:
 ---

#### -A & -m or –-method options:

-A -> Option when used will download All yangs from NETCONF supported node, yangs will be placed in a folder with name same as Node IP address.

For example:
```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -A```

Above command will download supported yangs from NE & place it in a folder called C:\NETCONF\10.100.179.	

Also, we can use -m option along with -A to perform either get/getconfig operation on all the available YANGS.
For example: 
---
```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -A -m get```

Above command will download supported yangs from NE in C:\NETCONF\172.16.14.34 folder & perform a GET operation on the same, if data is available the same will be placed in a XML file in C:\NETCONF\172.16.14.34 folder.

```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -A -m getconfig```

Above command will download supported yangs from NE in C:\NETCONF\172.16.14.34 folder & perform a GET-CONFIG operation on the same, if data is available the same will be placed in a XML file in C:\NETCONF\172.16.14.34 folder.

#### -p or --path option & -m or –-method options:

We can also use -p option to specify a single yang file & perform either get or getconfig operation.

For example:
---
```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -p C:\MyYang\sample.yang -m get```

Above command will perform a GET operation for sample.yang & place results in working folder in form of XML

```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -p C:\MyYang\sample.yang -m getconfig```

Above command will perform a GET-CONFIG operation for sample.yang & place results in working folder in form of XML

Alternatively, when a directory is passed to -p or –path option, then any operation specified by -m or --method option will be performed on all available yangs in the directory  
For example:
---
 ```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -p C:\MyYang\ -m get```
 
Above command will perform a GET operation for all available YANGS in C:\MyYang\ folder & place results in working folder in form of XML in same folder.

 ```C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123 -p C:\MyYang\ -m getconfig```
 
Above command will perform a GETCONFIG operation for all available YANGS in C:\MyYang\ folder & place results in working folder in form of XML in same folder.

#### -F or --fullconfig options:

We can use -F option to perform ROOT level get/get-config operation NETCONF supported nodes.

For example:
---
```C:\New folder\NETCONF>python netconf_cli.py 172.16.14.34 adminuser adminpassword123 -F get```

Above command will perform get/get-config operation on ROOT node of device & place results in working folder in form of XML file.

### No options specified:
---

When no options is provided, it connects to given node & prints capabilities only.

For example:
---
C:\NETCONF>python netconf_cli.py 172.16.14.34 adminuser admin123

Above command will connect to device & prints capabilities only.


All operations will be logged in file ncrun.log in working directory, please check this file for any errors/exceptions or more details.
