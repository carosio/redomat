#!/usr/bin/python -u
"""
service_url='unix://var/run/docker.sock'
service_version = "1.15"
dclient = docker.Client(base_url=service_url,version=service_version,timeout=2400)

cid = '574db76e4ac0'
cmd = 'bash -c "echo hello world ; date ; sleep 1 ; date ; false"'

strm,rc = docker_call(cmd, dclient, cid)
print "docker_call return"

print "==[output]============="
for chunk in strm: print chunk
print "======================="

print "return code:", rc()
"""

import six, docker, shlex
import io
import socket

# http://stackoverflow.com/questions/6657820/python-convert-an-iterable-to-a-stream
def iterable_to_stream(iterable, buffer_size=io.DEFAULT_BUFFER_SIZE):
    """
    Lets you use an iterable (e.g. a generator) that yields bytestrings as a read-only
    input stream.

    The stream implements Python 3's newer I/O API (available in Python 2's io module).
    For efficiency, the stream is buffered.
    """
    class IterStream(io.RawIOBase):
        def __init__(self):
            self.leftover = None
        def readable(self):
            return True
        def readinto(self, b):
            try:
                l = len(b)  # We're supposed to return at most this much
                chunk = self.leftover or next(iterable)
                output, self.leftover = chunk[:l], chunk[l:]
                b[:len(output)] = output
                return len(output)
            except StopIteration:
                return 0    # indicate EOF
    return io.BufferedReader(IterStream(), buffer_size=buffer_size)

def better_docker_execute(self_dc, container, cmd, linebased=True, attach_stdin=False):
    if isinstance(cmd, six.string_types):
        cmd = shlex.split(str(cmd))
    data = {
        'Privileged':True,
        #'Tty': False,
        'AttachStdin': attach_stdin,
        'AttachStdout': True,
        'AttachStderr': True,
        'Cmd': cmd
    }

    url = self_dc._url('/containers/{0}/exec'.format(container))
    res = self_dc._post_json(url, data=data)
    self_dc._raise_for_status(res)
    exec_id = res.json().get('Id')

    res = self_dc._post_json(self_dc._url('/exec/{0}/start'.format(exec_id)),
            data={'Detach': False}, stream=True)
    stream_gen = self_dc._multiplexed_buffer_helper(res) # keep for output generator
    self_dc._raise_for_status(res)
    raw = self_dc._get_raw_response_socket(res)


    def close_write_half():
        raw.shutdown(socket.SHUT_WR)

    if not attach_stdin:
        close_write_half()

    if linebased:
        stream_gen = iterable_to_stream(stream_gen)

    class ExecResult:
        output_gen = stream_gen
        @staticmethod
        def exit_code():
            close_write_half()
            # drop all non-consumed output
            for chunk in stream_gen: pass

            # query for ExitCode
            url = self_dc._url('/exec/{0}/json'.format(exec_id))
            res = self_dc._get(url)
            self_dc._raise_for_status(res)
            return res.json().get("ExitCode")
        
        @staticmethod
        def input_sock():
            return raw

        @staticmethod
        def close_input():
            close_write_half()

            
    return ExecResult
# vim:expandtab
