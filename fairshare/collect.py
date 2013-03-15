#! /usr/bin/env python

import sys
from time import time
from datetime import datetime, timedelta
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import logging

import pylsf
import cx_Oracle
import fairshare

PART = 'SHARE'
USERDATALEN = 7

def collect(args):
    # Set up logging
    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    # Connect to DB
    try:
        connection = fairshare.connect(args.config)
    except cx_Oracle.DatabaseError, e:
        logging.error(str(e)[:-1])
        return 1
    c = connection.cursor()

    # Run PyLSF 
    rc = pylsf.lsb_init()
    if rc != 0:
        raise Exception(pylsf.lsb_sysmsg())

    t0 = time()
    (_, _, userdata), = pylsf.lsb_hostpartinfo([PART])
    logging.info("Queried from LSF in %.2f s" % (time() - t0))

    users = []
    try:
        i = 0
        while True:
            # Not using reserved and adjust is missing
            user, shares, priority, started, cpu, reserved, wall = \
                userdata[USERDATALEN * i + 0:USERDATALEN * i + 7]

            # Collect data
            d = {'u': user, 't': datetime.now(), 'shares': shares,
                 'priority': priority, 'started': started, 'cpu': cpu,
                 'wall': wall}
            users.append(d)

            i += 1
    except ValueError:
        # need more than 0 values to unpack
        pass

    # Insert new share values
    # http://guyharrison.squarespace.com/blog/2010/1/1/the-11gr2-ignore_row_on_dupkey_index-hint.html
    # Reuse nextval: http://dba.stackexchange.com/questions/2978
    insert = '''\
    INSERT INTO shares (id, timestamp, shares, priority, started, cpu, wall)
    VALUES (id, :t, :shares, :priority, :started, :cpu, :wall);'''


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
    logging.info("Inserted %d records to DB in %.2f s" % \
        (c.rowcount, time() - t0))

    # Clean up old data
    sql = 'DELETE FROM shares WHERE timestamp < :t'
    t0 = time()
    c.execute(sql, [datetime.now() - timedelta(10)])
    logging.info("Deleted %d records from DB in %.2f s" % \
        (c.rowcount, time() - t0))

    # Commit
    t0 = time()
    connection.commit() # Yes, needed
    logging.info("Committed changes in DB in %.2f s" % (time() - t0))

def main():
    p = ArgumentParser(description="Modify fairshare DB",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-c', '--config', help="config file",
                   default='/etc/fairshare')
    p.add_argument('-l', '--log', help="log file",
                   default='/var/log/fairshare.log')
    s = p.add_subparsers()
    pmk = s.add_parser('collect', help="Collect users and their stats")
    pmk.set_defaults(func=collect)
    args = p.parse_args()

    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
