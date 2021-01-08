##############################################################################
#                                                                            #
#  netconf_cap.py                                                            #
#                                                                            #
#  Objective:                                                                #
#                                                                            #
#    Testing tool for the NETCONF interface in Python #
#                                                                            #
#  Features supported:                                                       #
#                                                                            #
#    - get/get-config/get-schema                                             #
#                                                                            #
#  Pre-requisite before running this script:                                 #
#                                                                            #
#   - NCCLIENT                                                               #
#   - Added support for all variants                                         #
#
#
#  Sample usage:
#
#    - C:>> python netconf_cap.py <IP_ADDRESS> <USERNAME> <PASSWORD>          #
#
#  Author: Nithin K                                                           #
#    mail: nithinkshetty@gmail.com                                            #
#    date:09/25/2020 - Fixed RE bugs for container & best effort for
#    getschema                                                                #
##############################################################################

##############################################################################
import sys, os, warnings, re, time, argparse, traceback, logging
warnings.simplefilter("ignore", DeprecationWarning)
from ncclient import manager
from lxml import etree
from ncclient.operations.errors import OperationError, TimeoutExpiredError, MissingCapabilityError
from ncclient.operations.rpc import RPCError


def processYang (yang):
    MyPrefix=None
    MyNameSpace=None
    MyContainer=[]
    MyList=[]
    content=""
    logger.debug ("Processing yang file %s" %yang)

    #namespacere=re.compile("^[\s]*namespace[\s]*\"([\S]*?)\";")
    namespaceremultiline=re.compile("[\s]+namespace[\s]*\"([\S]+?)\";")
    prefixre=re.compile("[\s]+prefix[\s]*[\"]{0,1}([\S]+?)[\"]{0,1};")
    containerre=re.compile("[\s]+container[\s]+([\S]+?)[\s]*{")
    #groupingre=re.compile("^[\s]*grouping[\s]*([\S]*?)[\s]")
    listre=re.compile("[\s]+list[\s]+([\S]+?)[\s]*{")

    enc='utf-8'
    for line in open(yang,encoding=enc):
        content=content+"\n"+line

    if MyNameSpace is None:
        MyNameSpace = namespaceremultiline.search(content).group(1)
        MyNameSpace = MyNameSpace.replace("{", "")
        MyNameSpace = MyNameSpace.replace("}", "")
        MyNameSpace = MyNameSpace.replace("\"", "")
        MyNameSpace = MyNameSpace.replace("\"", "")

    if MyPrefix is None:
        MyPrefix = prefixre.search(content).group(1)
        MyPrefix = MyPrefix.replace("{", "")
        MyPrefix = MyPrefix.replace("}", "")
        MyPrefix = MyPrefix.replace("\"", "")
        MyPrefix = MyPrefix.replace("\"", "")

    MyContainer=containerre.findall(content)
    MyList=listre.findall(content)

    if not MyContainer and MyList:
        MyContainer=MyList

    if MyNameSpace is None or MyPrefix is None:
        print ("Unable to find one of below values \n Please check yang file %s  \n Namespace = %s \n Prefix = %s \n" %(yang,MyNameSpace, MyPrefix))
        logger.error("Please check yang file: %s" %yang)
        logger.error("Namespace = %s" %MyNameSpace)
        logger.error("Prefix = %s" %MyPrefix)

        MyFilter="skip"
        return (MyFilter, MyPrefix)

    if not MyContainer:
        print ("No container/lists found \n")
        logger.warning("No container/lists found")
        MyFilter="skip"
        return (MyFilter, MyPrefix)

    #print ("Container is %s" %MyContainer)
    logger.debug ("Container is %s" %MyContainer)
    logger.debug ("Prefix is %s" %MyPrefix)
    logger.debug ("NameSpace is %s" %MyNameSpace)

    MyFilter = "<filter> \n"
    for c in MyContainer:
        c = c.replace("{", "")
        c = c.replace("}", "")
        c = c.replace("\"", "")
        c = c.replace("\"", "")
        if "config" == c or "state" == c or "changed" == c:
            continue
        MyFilter = MyFilter + '    <{}:{} xmlns:{}="{}"/>'.format(MyPrefix, c, MyPrefix, MyNameSpace) + "\n"
    MyFilter = MyFilter + "</filter>\n"

    logger.debug ("My filter for %s is %s" % (yang,MyFilter))

    return (MyFilter,MyPrefix)


def collectAllYang(host, user, password, ncport,collectstatus):
    logger.debug("Called collect yang function")
    if os.path.isdir(host):
        if collectstatus:
            print ("Please remove folder %s before proceeding \n" %host)
            logger.warning("Folder %s already exists, Exiting" %host)
            raise SystemExit
    else:
        if collectstatus:
            os.mkdir(host)

    modulere=re.compile(".*module=(.*?)&")
    modulere2=re.compile(".*module=(.*)")
    try:
        with manager.connect(host=host, port=ncport, username=user, password=password,hostkey_verify=False,manager_params={'timeout': 600}) as m:
            print ("Connected to %s" %host)
            logger.info ("Connected to %s" %host)
            for c in m.server_capabilities:
                try:
                    print (c)
                    if collectstatus:
                        if modulere.match(c):
                          MyModule=modulere.search(c).group(1)
                          data = m.get_schema(identifier=MyModule)
                          data = str(data).replace('encoding="UTF-8"', '')
                        #logger.debug ("For yang %s  -> %s" %(MyModule,data))
                          getMyYang(str(data),MyModule,dir=host)
                        elif modulere2.match(c):
                           MyModule = modulere2.search(c).group(1)
                           data = m.get_schema(identifier=MyModule)
                           data = str(data).replace('encoding="UTF-8"','')
                            #logger.debug ("For yang %s  -> %s" %(MyModule,data))
                           getMyYang(str(data),MyModule,dir=host)
                except Exception as e:
                    print("Error while collecting %s file for device %s \n" %(MyModule, host))
                    logger.error("Error scenario encountered while collecting %s yang for %s device" %(MyModule, host))
                    logger.exception("Error scenario encountered while collecting %s yang for %s device" %(MyModule, host), exc_info=True)
                    repr(e)
                    print(e)
            print ("done")
            logger.info("completed successfully")
    except Exception as e:
        print ("Error while connecting to device %s \n" %host)
        logger.error("Error while connecting to device %s" %host)
        logger.exception("Error while connecting to device %s" %host, exc_info=True)
        repr(e)
        print (e)
        raise SystemExit



def getMyYang(CONTENT,YangFile,dir=None):
    #CONTENT = CONTENT.decode('utf-8').encode('ascii')
    root = etree.fromstring(CONTENT)
    print ("Collecting yang for %s" %YangFile)
    logger.info ("Collecting yang for %s" %YangFile)
    FullYangFile=YangFile
    if dir is not None:
        FullYangFile=os.path.join(dir,YangFile)
    for log in root:
        with open("%s.yang" %FullYangFile,"wb") as f:
            f.write(log.text.encode('utf-8'))
    print ("done \n")
    logger.info ("Collected yang for %s \n" %YangFile)


def makeNetconfCall(host, user, password, ncport, mode, path):
    EXCEPTION_COUNT = 0
    logger.debug("Preparing %s NETCONF Calls for %s" %(mode,host))
    xmln = re.compile("<.*xmlns.*/>")
    container = re.compile("<.*?:([\S]*) ")

    try:
        with manager.connect(host=host, port=ncport, username=user, password=password,hostkey_verify=False,manager_params={'timeout': 600}) as m:
            print ("Connected to device %s \n" %host)
            logger.info("Connected to device %s" %host)
            m.raise_mode = 0
            if os.path.isfile(path):
                (MeFilter,prefix) = processYang(path)
                if MeFilter == "skip":
                    print ("Skipping %s as no containers are found \n" % path)
                    logger.warning("Skipping %s as no containers are found" % path)
                    c = "No data available for " + path
                    logger.warning("Exiting")
                    raise SystemExit
                logger.debug("Executing %s calls" %mode)
                FLAG=0
                for x in xmln.findall(MeFilter):
                    filepart=container.search(x).group(1)
                    MyFilter = "<filter>\n" + "    " + x + "\n</filter>"
                    if mode == "getconfig":
                        logger.debug("Reconstructed filter for %s - %s" %(mode,MyFilter))
                        c = m.get_config(source='running',filter=MyFilter).data_xml
                    else:
                        logger.debug("Reconstructed filter for %s - %s" %(mode,MyFilter))
                        c = m.get(filter=MyFilter).data_xml
                    logger.debug("For yang %s - %s" %(path,c))
                    logger.debug("OKAY WITH PRINT")
                    starttag="<"+filepart+" "
                    endtag="</"+filepart+">"
                    logger.debug("Checking output with %s and %s tags" % (starttag, endtag))
                    if c.strip().endswith("</data>") and c.find(starttag) > 0 and c.find(endtag) > 0:
                        with open("%s_%s_%s_%s.xml" % (host,prefix,filepart,mode), 'w') as f:
                            f.write(c)
                        c=None
                        print ("done \n Output available in %s_%s_%s_%s.xml \n" % (host,prefix,filepart,mode))
                        FLAG=1
                        logger.info("Output available in %s_%s_%s_%s.xml" % (host,prefix,filepart,mode))
                    else:
                        c='No data available for "%s"\n' %prefix
                        #logger.info("Data unavailable for %s" %prefix)
                        logger.debug("No data available for %s & %s\n" %(prefix,filepart))
                        #print ("%s" %c)
                if FLAG == 0:
                    print ("No data found for %s \n" %prefix)
                    logger.info("Data unavailable for %s" %prefix)
            else:
                temp=os.path.join(path, host)
                for yfile in os.listdir(path):
                    FLAG=0
                    if yfile.endswith("yang"):
                        print ("Processing YANG file %s... " %yfile)
                        logger.info("Processing YANG file %s..." %yfile)

                        tempyfile=os.path.join(path,yfile)
                        (MeFilter, prefix) = processYang(tempyfile)

                        if MeFilter == "skip":
                            print ("Skipping %s as no containers are found \n" % yfile)
                            logger.warning ("Skipping %s as no containers are found" % yfile)
                            c = "No data available for " + yfile
                        else:
                            for x in xmln.findall(MeFilter):
                                filepart = container.search(x).group(1)
                                logger.debug ("Processing %s now" %filepart)
                                MyFilter = "<filter>\n" + "    " + x + "\n</filter>"
                                try:
                                    if mode == "getconfig":
                                        logger.debug("Reconstructed filter for %s - %s" % (mode, MyFilter))
                                        c = m.get_config(source='running', filter=MyFilter).data_xml
                                    else:
                                        logger.debug("Reconstructed filter for %s - %s" % (mode, MyFilter))
                                        c = m.get(filter=MyFilter).data_xml
                                        logger.debug("%s" %c)
                                    starttag = "<" + filepart + " "
                                    endtag = "</" + filepart + ">"
                                    logger.debug("Checking output with %s and %s tags" %(starttag,endtag))
                                    if c.strip().endswith("</data>") and c.find(starttag) > 0 and c.find(endtag) > 0:
                                        with open("%s_%s_%s_%s.xml" % (temp, prefix,filepart,mode), 'w') as f:
                                            f.write(c)
                                        FLAG=1
                                        c=None
                                        logger.debug("Resetting output for as %s" %c)
                                        print ("Output available in %s_%s_%s_%s.xml \n" % (temp, prefix,filepart,mode))
                                        logger.info("Output available in %s_%s_%s_%s.xml" % (temp, prefix,filepart,mode))
                                    else:
                                        c='No data available for "%s" container/list object \n' %filepart
                                        logger.debug("%s" %c)
                                except Exception as e:
                                    EXCEPTION_COUNT += 1
                                    print ("No data available for %s \n" % yfile)
                                    logger.error ("No data available for %s" % yfile)
                                    logger.exception("Exception encountered for %s" %yfile,exc_info=True)
                                    logger.warning("Ignoring exception & continuing with execution")
                                    c = "No data available for" + yfile
                                    repr(e)
                                    print (e)
                            if FLAG==0:
                                print ("No data available for %s \n" %yfile)
                                logger.info("No data available for %s" %yfile)
    except Exception as e:
        print ("Error encountered for %s" %host)
        logger.error ("Error encountered for %s" %host)
        logger.exception("Exception encountered", exc_info=True)
        repr(e)
        print (e)
        traceback.print_exc(file=sys.stdout)
        raise SystemExit
    if EXCEPTION_COUNT > 0:
        print ("Total no of %d exceptions were seen & ignored during the call. \n Please check ncrun.log for more details\n" %EXCEPTION_COUNT)
        logger.error("Total exceptions seen & ignored - %d" %EXCEPTION_COUNT)
#        collectALL(args.nchost,args.username,args.password,args.port,args.fullconfig)

def collectALL(host, user, password, ncport, mode):
    try:
        with manager.connect(host=host, port=ncport, username=user, password=password, hostkey_verify=False,manager_params={'timeout': 600}) as m:
            print("Connected to %s and executing, please wait as it may take some time..." % host)
            logger.info("Connected to %s and executing, please wait as it may take some time..." % host)
            if mode == "getconfig":
                c = m.get_config(source='running').data_xml
            else:
                c = m.get().data_xml
            with open("%s_%s.xml" % (host,mode), 'w') as f:
                f.write(str(c))
            print ("\n Output available in %s_%s.xml \n" % (host,mode))
            logger.info ("Output available in %s_%s.xml" % (host,mode))

    except Exception as e:
        print ("Error encountered for %s" %host)
        logger.error ("Error encountered for %s" %host)
        logger.exception("Exception encountered", exc_info=True)
        repr(e)
        print (e)
        raise SystemExit


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(prog='netconf_cli',description='Make NETCONF get or getconfig calls to NETCONF supported device')
    my_parser._positionals.title = "Mandatory arguments (Required)"
    my_parser.add_argument('-l', '--log',action='store_true',help=argparse.SUPPRESS)
    group=my_parser.add_mutually_exclusive_group()
    group.add_argument('-A', '--allyang',action='store_true',help="Collect All YANG files")
    group.add_argument('-F', '--fullconfig',choices=['get', 'getconfig'],type=str,help="Collect FULL configuration in an XML, GET/GETCONFIG oN ROOT XML node")

    group=my_parser.add_argument_group()
    group.add_argument('nchost',action='store',type=str,help="IP address of the NETCONF device")
    group.add_argument('username',action='store',type=str,help="Username of the device")
    group.add_argument('password',action='store',type=str,help="Password of the device")
    group.add_argument('--port',action='store',type=int,help="NETCONF port, Default is 830 when not specified",default=830)

    group=my_parser.add_argument_group()
    group.add_argument('-p', '--path',action='store',type=str,help="Absolute path to a specific YANG file or folder containing YANGs",metavar='<<C:\Yangfile\example.yang>> or <<C:\YangDir\>>')
    group.add_argument('-m', '--method',choices=['get', 'getconfig'],type=str,help="Specify get or getconfig calls")

    args = my_parser.parse_args()
    logger = logging.getLogger(__name__)
    if args.log:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logfile_handle = logging.FileHandler('ncrun.log')
    formatter = logging.Formatter('%(asctime)s : %(levelname)s  : %(message)s')
    logfile_handle.setFormatter(formatter)

    logger.addHandler(logfile_handle)

    logger.info("\n############################# Started script execution ######################### \n")
    print ("\n")
    password=args.password
    args.password="########"
    logger.info("SCRIPT called with arguments %s" %args)
    args.password = password
    if not args.path and not args.method and not args.fullconfig and not args.allyang:
        print ("Connecting to device to print capabilities... \n")
        logger.info("Connecting to device %s to print capabilities..." %args.nchost)
        collectAllYang(args.nchost, args.username, args.password, args.port,False)
        raise SystemExit

    if args.path and args.method and args.allyang and args.fullconfig:
        print ("ALLYANG or -A option not supported with path argument and FULL GET/GETCONFIG Argument\n")
        logger.warning ("ALLYANG or -A option not supported with path argument and FULL GET/GETCONFIG Argument")
    elif args.path and args.method and args.allyang:
        print ("ALLYANG or -A option not supported with path argument\n")
        logger.warning ("ALLYANG or -A option not supported with path argument")
    elif args.path and args.method and args.fullconfig:
        print ("Path & method option should not contain standalone Fullconfig call \n")
        logger.warning ("Path & method option should not contain standalone Fullconfig call")
    elif args.path and args.allyang and args.fullconfig:
        print ("ALLYANG or -A option not supported for this scenario \n")
        logger.warning ("ALLYANG or -A option not supported for this scenario")
    elif args.method and args.allyang and args.fullconfig:
        print ("ALLYANG or -A option not supported for this scenario \n")
        logger.warning ("ALLYANG or -A option not supported for this scenario")
    elif args.path and args.method:
        if os.path.isfile(args.path) or os.path.isdir(args.path):
            print ("\n Calling %s for %s \n" %(args.method, args.path))
            logger.info("Calling %s for %s" %(args.method, args.path))
            makeNetconfCall(args.nchost,args.username,args.password,args.port,args.method,args.path)
        else:
            print ("%s is not available or doesnt exist" %args.path)
            logger.warning("%s is not available or doesnt exist" %args.path)
    elif args.path and args.allyang:
        print ("ALLYANG or -A option not supported for this scenario \n")
        logger.warning ("ALLYANG or -A option not supported for this scenario")
    elif args.allyang and args.method:
        Wdir = os.getcwd()
        WPath = os.path.join(Wdir, args.nchost)
        print ("Executing %s for all available yang files \n" % args.method)
        logger.info("Executing %s for all available yang files" % args.method)
        collectAllYang(args.nchost, args.username, args.password, args.port,True)
        makeNetconfCall(args.nchost, args.username, args.password,args.port, args.method, WPath)
    elif args.allyang and args.fullconfig:
        print ("Incomplete arguments AllYANG & Full Config cant be combined \n")
        logger.warning ("Incomplete arguments AllYANG & Full Config cant be combined")
    elif args.allyang and args.path:
        print ("Incomplete arguments a method option must always be associated with a path or AllYANG option \n")
        logger.warning ("Incomplete arguments a method option must always be associated with a path or AllYANG option")
    elif args.path or args.method:
        print ("Incomplete arguments a method option must always be associated with a path or ALLYANG option \n")
        logger.warning ("Incomplete arguments a method option must always be associated with a path or ALLYANG option \n")
    elif args.allyang:
        print ("Collecting all YANG files for host %s  \n" %args.nchost)
        logger.info("Collecting all YANG files for host %s" %args.nchost)
        collectAllYang(args.nchost,args.username,args.password,args.port,True)
    elif args.fullconfig:
        #collectAllYang(args.nchost,args.username,args.password,args.port,False)
        print ("\n Please wait when we collect full details\n")
        print ("Performing %s for ROOT node on %s  \n" %(args.fullconfig,args.nchost))
        logger.info("Performing %s for ROOT node on %s" %(args.fullconfig,args.nchost))
        collectALL(args.nchost,args.username,args.password,args.port,args.fullconfig)
    else:
        print ("\n Please provide proper arguments, Please check help menu \n")
        logger.warning ("Please provide proper arguments, Please check help menu")
        raise SystemExit

    print ("Exiting with status - 0 \n")
    logger.info("Exiting - status - 0")