import xml.etree.ElementTree as ET
import subprocess, os, sys, logging

dmefile = 'G:\\Git\\vgstation\\vgstation13.dme'

def checkPathforDMExec():
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, 'dm.exe')
        if os.path.exists(exe_file):
            return exe_file

def GetDMExecPath():
    pathcheck = checkPathforDMExec()
    if pathcheck:
        return pathcheck
    # Windows
    if sys.platform.startswith('win32'):
        folder = os.path.isdir(OS.environ.get('ProgramFiles') + '/BYOND/bin')
        if os.path.isdir(folder):
            fullpath = folder + 'dm.exe'
            if os.path.exists():
                return fullpath
        else:
            folder = os.path.isdir(OS.environ.get('ProgramFiles(x86)') + '/BYOND/bin')
            if os.path.isdir(folder):
                fullpath = folder + 'dm.exe'
                if os.path.exists(fullpath):
                    return fullpath
    else: #*nix
        return # TODO: unix support

def main():
    # tree = ET.parse()
    log = logging
    log.basicConfig(filename='test.log', level=logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    log.debug(dmefile)
    dmexec = GetDMExecPath()
    if not dmexec:
        log.warn("Could not find dm.exe")
    log.debug('Found dm.exe')
    if not os.path.exists(dmefile):
        log.warn("Could not find .dme. Path used: " + dmefile)
        return
    log.debug('Found ' + dmefile)
    DMOutput = subprocess.check_output([dmexec, '-o', dmefile])

    f = open('output.xml', 'w+')
    f.write(DMOutput)
    log.info('OK')


# GetDMXML('vgstation.dme')


if __name__ == '__main__':
	main()
