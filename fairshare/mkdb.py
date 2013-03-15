#! /usr/bin/env python

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import cx_Oracle
import fairshare

def mktables(args):
    connection = fairshare.connect(args.rcfile)
    c = connection.cursor()

    def execcreate(cursor, sql):
        try:
            cursor.execute(sql)
        except cx_Oracle.DatabaseError, e:
            if e.args[0].code == 955: # Table already exists
                pass
            else:
                raise

    # Auto increment
    create = "CREATE SEQUENCE seq_users"
    seq = " MINVALUE 1 START WITH 1 INCREMENT BY 1 CACHE 100"
    sql = create + seq
    execcreate(c, sql)

    # User tables
    # Maybe I want a PK on id and an INDEX/UNIQQUE on username
    cols = 'id NUMBER(7) UNIQUE', 'username VARCHAR2(256)', \
           'CONSTRAINT pk_users_username PRIMARY KEY (username)'
    sql = "CREATE TABLE users (%s)" % ', '.join(cols)
    execcreate(c, sql)

    # Stat tables
    cols = 'id NUMBER(7)', 'timestamp DATE', 'shares NUMBER(7)', \
           'priority NUMBER(9,3)', 'started NUMBER(7)', 'cpu NUMBER(12,1)', \
           'wall NUMBER(11)', \
           'CONSTRAINT pk_shares_id_timestamp PRIMARY KEY (id, timestamp)'
    sql = "CREATE TABLE shares (%s)" % ', '.join(cols)
    execcreate(c, sql)

def main():
    p = ArgumentParser(description="Modify fairshare DB",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-f', '--file', metavar='FILE', dest='rcfile',
                   help="config file", default='/etc/fairshare')
    s = p.add_subparsers()
    pmk = s.add_parser('mktables', help="Make tables")
    pmk.set_defaults(func=mktables)
    args = p.parse_args()

    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
