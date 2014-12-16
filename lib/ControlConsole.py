__author__ = 'linh'
import sys
import os
import traceback

from twisted.web import xmlrpc
from twisted.web import server
from twisted.python import log

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.join(BASE_DIR, '..'))

from lib.ProcessUtil import ProcessUtil

IDLE = 0
BUSY = 1

SUCCESS = 0
ERR_ERROR = 1
ERR_BUSY = 2
ERR_TIMEOUT = 3

class ControlConsole(xmlrpc.XMLRPC):
    """
    Console used to control station PC
    """
    def __init__(self, host='localhost', port=1000, info={}):
        self.allowNone = True
        self.useDateTime = True
        self.allowedMethods = True
        self._port = port
        self._host = host
        self._info = info
        self._status = IDLE

    def xmlrpc_ping(self, **kargs):
        """
        Check the connection
        """
        return True

    def xmlrpc_get_status(self, **kargs):
        '''
        Get current status of station
        '''
        return self._status

    def xmlrpc_run_cmd(self, info={}):
        """
        Run command on station PC

        require info:
        active_dir - the directory that command win run from
        command - the command that station will be run
        timeout - the maximum time in (s) that station will wait before kill the process,
                    if timeout is 0 the process will be started then return immediately
        isshell - indicate the command run in shell or not
        output - where the output is writen (file, or return to server)
        error - where the error is writen (file, or return to server)

        return:
        (return_code, output_string, error_string)
        """
        return_code = 1
        output_string = ''
        error_string = ''
        isshell = False
        output = ''
        error = ''
        active_dir = ''
        command = ''
        timeout = 0
        if self._status != IDLE:
            return (ERR_BUSY, '', None)
        self._status = BUSY

        if 'active_dir' in info.keys():
            active_dir = info['active_dir']
        if 'command' in info.keys():
            command = info['command']
        if 'timeout' in info.keys():
            timeout = info['timeout']
        if 'isshell' in info.keys():
            isshell = info['isshell']
        if 'output' in info.keys():
            output = info['output']
        if 'error' in info.keys():
            error = info['error']

        try:
            if active_dir:
                # Change to active dir if available
                curdir = os.getcwd()
                if os.path.exists(active_dir) and os.path.isdir(active_dir):
                    os.chdir(active_dir)

            cmd = []
            if isinstance(command, list) or isinstance(command, tuple):
                cmd.extend(command)
            else:
                cmd.append(command)
            (return_code, is_timeout, output_string, error_string) = ProcessUtil.run_job(cmd, timeout, is_shell=isshell, output=output, error=error)

            if active_dir:
                # Change back to previous dir
                os.chdir(curdir)
        except:
            error_string = traceback.format_exc()
            return_code = ERR_ERROR
        finally:
            self._status = IDLE

        return (return_code, output_string, error_string,)

def main():
    from twisted.internet import reactor
    log.startLogging(sys.stdout)
    r = ControlConsole('localhost', 1099)
    reactor.listenTCP(1099, server.Site(r))
    reactor.run()

if __name__ == '__main__':
    main()
