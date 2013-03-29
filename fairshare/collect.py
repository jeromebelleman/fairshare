#! /usr/bin/env python

import sys
from os.path import expanduser
from time import time
from datetime import datetime, timedelta
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging

import pylsf
from cx_Oracle import connect, DatabaseError

PART = 'SHARE'
USERDATALEN = 7
DEL = 10

class Output:
    def __init__(self, f):
        self.f = f
        self.buf = ''

    def write(self, s):
        if s == '\n':
            self.f(self.buf)
        else:
            self.buf += s

def collect(username, password, dsn, log, delete=DEL):
    # Set up logging
    logging.basicConfig(filename=expanduser(log), level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    sys.stdout = Output(logging.warning)
    sys.stderr = Output(logging.error)

    try:
        # Connect to DB
        connection = connect(username,
                             open(expanduser(password)).read().strip(),
                             dsn)
        c = connection.cursor()

        # Run PyLSF 
        rc = pylsf.lsb_init()
        if rc != 0:
            logging.error(pylsf.lsb_sysmsg())
            return 1

        t0 = time()
        (_, _, userdata), = pylsf.lsb_hostpartinfo([PART])
        logging.info("Retrieved %d groups from LSF in %.2f s" % \
                     (len(userdata) / 7, time() - t0))

        t = datetime.now()
        users = []
        try:
            i = 0
            while True:
                # Not using reserved and adjust is missing
                user, shares, priority, started, cpu, reserved, wall = \
                    userdata[USERDATALEN * i + 0:USERDATALEN * i + 7]

                # Collect data
                d = {'u': user, 't': t, 'shares': shares, 'priority': priority,
                     'started': started, 'cpu': cpu, 'wall': wall}
                users.append(d)

                i += 1
        except ValueError:
            # need more than 0 values to unpack
            pass

        # Insert new share values
        insert = '''\
        INSERT INTO shares (id, timestamp, shares, priority, started, cpu, wall)
        VALUES (id, :t, :shares, :priority, :started, :cpu, :wall);'''

        # http://guyharrison.squarespace.com/blog/2010/1/1/the-11gr2-ignore_row_on_dupkey_index-hint.html
        # Reuse nextval: http://dba.stackexchange.com/questions/2978
        sql = '''\
DECLARE
    id NUMBER(7);
BEGIN
    SELECT id INTO id FROM users WHERE username = :u;

%s
EXCEPTION WHEN no_data_found THEN
    id := seq_users.nextval;

    INSERT INTO users (id, username) VALUES (id, :u);

%s
END;''' % ((insert,) * 2)

        t0 = time()
        c.executemany(sql, users)
        logging.info("Inserted records to DB in %.2f s" % (time() - t0))

        # Clean up old data
        sql = 'DELETE FROM shares WHERE timestamp < :t'
        t0 = time()
        c.execute(sql, [datetime.now() - timedelta(delete)])
        logging.info("Deleted %d records from DB in %.2f s" % \
                     (c.rowcount, time() - t0))

        # Commit
        t0 = time()
        connection.commit() # Yes, needed
        logging.info("Committed changes to DB in %.2f s" % (time() - t0))
    except (IOError, DatabaseError), e:
        logging.error(str(e).strip())
        return 1

def main():
    p = ArgumentParser(description="Modify fairshare DB",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-u', '--username', help="username")
    p.add_argument('-p', '--password', help="password file",
                   default='/etc/fairshare')
    p.add_argument('-t', '--dsn', help="DSN")
    p.add_argument('-l', '--log', help="log file",
                   default='/var/log/fairshare.log')
    p.add_argument('-d', '--delete', metavar='N',
                   help="delete data older than N days", type=int, default=DEL)
    args = p.parse_args()

    # Run command
    return collect(args.username, args.password, args.dsn,
                   args.log, args.delete)

if __name__ == '__main__':
    sys.exit(main())
