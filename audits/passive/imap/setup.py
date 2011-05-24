#!/usr/bin/env python
# This file is auto generated by setup-autogen.py

from umit.pm.gui.plugins.containers import setup

setup(
    name='IMAPDissector',
    version='1.0',
    author=['Francesco Piccinno'],
    license=['GPL'],
    copyright=['2009 Adriano Monteiro Marques'],
    url='http://blog.archpwn.org',
    scripts=['sources/main.py'],
    start_file='main',
    data_files=[],
    need=['TCPDecoder'],
    provide=['IMAPDissector-0.4'],
    conflict=[],
    description='IMAPDissector plugin.',
    output='imapdissector.ump',
    audit_type=0,
    protocols=(('tcp', 143), ('imap', None)),
    vulnerabilities=(('IMAP dissector', {'references': ((None, 'http://en.wikipedia.org/wiki/Internet_Message_Access_Protocol'),), 'description': 'The Internet Message Access Protocol (commonly known as IMAP) is an Application Layer Internet protocol that allows an e-mail client to access e-mail on a remote mail server'}),),
)