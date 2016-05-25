#!/usr/local/bin/python
from __future__ import print_function

import argparse
import os
import platform
import re
import subprocess
import sys

from pprint import pprint

class RunCmdResult(object):
    def __init__(self):
        self.retCode = 0;
        self.stdout = [];
        self.stderr = [];
    def addStdOut(self,lines,echo):
        if (len(lines)==0):
            return;
        lines = map(lambda line: line.rstrip('\n'),lines)
        if (echo):
            print("\n".join(lines), file=sys.stdout)
        self.stdout.extend(lines)
    def addStdErr(self,lines,echo):
        if (len(lines)==0):
            return;
        lines = map(lambda line: line.rstrip('\n'),lines)
        if (echo):
            print("\n".join(lines), file=sys.stderr)
        self.stderr.extend(lines)


def execute(args,echo=True):
    if echo:
        print(" ".join(args));
    sys.stdout.flush();
    result = RunCmdResult();

    # set the use show window flag, might make conditional on being in Windows:
    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        startupinfo = None
    # pass as the startupinfo keyword argument:
    p=subprocess.Popen(args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             stdin=open(os.devnull), # subprocess.PIPE,
                             startupinfo=startupinfo)

    for line in p.stdout:
        result.addStdOut([line],echo)
    result.retCode = p.returncode
    return result

def split_path(path):
    result=[]
    while True:
        dirname,leaf = os.path.split(path)
        if leaf:
            result[:0] = [leaf]
        else:
            #if dirname:
            #    result[:0] = [dirname]
            break;
        path=dirname
    return result

def main(argv):
    # provide argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-g','--groupId',dest='groupId',default='na',help='Group Id');
    parser.add_argument('-a','--artifactId',dest='artifactId',default="-".join(split_path(os.getcwd())),help='Artficat Id');
    parser.add_argument('-pv','--pom-version',dest='version',default='0.0.1-SNAPSHOT',help='Version to put in the pom');
    parser.add_argument('-x','--excludes',dest='excludes',nargs='+',default=[],help='Directories to exclude');
    parser.add_argument('-f','--file',dest='file',default='.pom.xml',help='Name of pom file');
    parser.add_argument('mvn_args',metavar='M',nargs='*',action='append',help='Arguments for maven. Prepend with " -- " if you have any maven arguments starting with "-", or just make a habit of doing so. Example: mvn-container-build -- clean install');
    args = vars(parser.parse_args(argv))

    # interpret parsed args
    excludes = args['excludes']
    excludes.extend(['^\\.'])
    exclusion_re = "(" + ")|(".join(excludes) + ")"

    mvn_args = args['mvn_args']
    if not( mvn_args == None) and len(mvn_args):
        mvn_args = [item for sublist in mvn_args for item in sublist]
    else:
        mvn_args = ['clean','install']
    mvn_args[:0] = ['mvn','-f',args['file']]

    # Find the modules
    modules=[];
    for item in os.listdir("."):
        if not re.match(exclusion_re ,item) and os.path.isdir(item) and os.path.isfile(item + "/pom.xml"):
            modules.append(item)
    print( "## Modules found:\n" )
    pprint(modules)
            
    # Now generate the pom
    pom_xml = ( "<?xml version='1.0' encoding='UTF-8'?>\n"
                "<project xmlns='http://maven.apache.org/POM/4.0.0' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'\n"
                "    xsi:schemaLocation='http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd'>\n"
                "  <modelVersion>4.0.0</modelVersion>\n"
                "  <prerequisites>\n"
                "    <maven>3.0.0</maven>\n"
                "  </prerequisites>\n"
                "  <packaging>pom</packaging>\n"
                "  <groupId>" + args['groupId'] + "</groupId>\n"
                "  <artifactId>" + args['artifactId'] + "</artifactId>\n"
                "  <version>" + args['version'] + "</version>\n"
                "  <modules>\n"
                "    <!-- exclusions: " + exclusion_re + " -->\n" )
    for item in modules:
        pom_xml += "    <module>" + item + "</module>\n"
    pom_xml += ( "  </modules>\n"
                 "</project>\n" )

    with(open(args['file'],"w")) as pom_file:
        pom_file.write(pom_xml)

    print( "## Generated pom xml file: " + args['file'] + " ##" )
    print( "```\n" + pom_xml + "\n```" )

    # Finally, run maven.
    execute(mvn_args)

if __name__ == "__main__":
    main(sys.argv[1:])

