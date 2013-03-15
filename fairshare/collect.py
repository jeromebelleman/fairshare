#! /usr/bin/env python

import sys
import pylsf
from datetime import datetime
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import fairshare

PART = 'SHARE'
USERDATALEN = 7

def collect(args):
    connection = fairshare.connect(args.rcfile)
    c = connection.cursor()

    rc = pylsf.lsb_init()
    if rc != 0:
        raise Exception(pylsf.lsb_sysmsg())

    (_, _, userdata), = pylsf.lsb_hostpartinfo([PART])

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

    # DB statement
    # IGNORE_ROW_ON_DUPKEY_INDEX not particularly quick:
    # http://guyharrison.squarespace.com/blog/2010/1/1/the-11gr2-ignore_row_on_dupkey_index-hint.html
    # Reuse nextval: http://dba.stackexchange.com/questions/2978
    sql = '''\
DECLARE
    id NUMBER(7);
BEGIN
    id := seq_users.nextval;
    INSERT /*+ IGNORE_ROW_ON_DUPKEY_INDEX(users, pk_users_username) */
    INTO users (id, username) VALUES (id, :u);

    INSERT INTO shares (id, timestamp, shares, priority, started, cpu, wall)
    VALUES (id, :t, :shares, :priority, :started, :cpu, :wall);
END;'''

    c.executemany(sql, users)
    connection.commit() # Yes, needed

def main():
    p = ArgumentParser(description="Modify fairshare DB",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-f', '--file', metavar='FILE', dest='rcfile',
                   help="config file", default='/etc/fairshare')
    s = p.add_subparsers()
    pmk = s.add_parser('collect', help="Collect users and their stats")
    pmk.set_defaults(func=collect)
    args = p.parse_args()

    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
