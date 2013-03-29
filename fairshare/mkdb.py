#! /usr/bin/env python

import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from cx_Oracle import connect, DatabaseError

def mktables(args):
    connection = connect(args.username,
                         open(args.password).read().strip(),
                         args.dsn)
    c = connection.cursor()

    def execcreate(cursor, sql):
        try:
            cursor.execute(sql)
        except DatabaseError, e:
            if e.args[0].code == 955: # Object already exists
                pass
            else:
                raise

    # Auto increment sequence
    create = "CREATE SEQUENCE seq_users"
    seq = " MINVALUE 1 START WITH 1 INCREMENT BY 1 CACHE 1000"
    sql = create + seq
    execcreate(c, sql)

    # users table
    cols = 'id NUMBER(7)', 'username VARCHAR2(256)', \
           'CONSTRAINT pk_users_id PRIMARY KEY (id)', \
           'CONSTRAINT un_users_username UNIQUE (username)'
    sql = "CREATE TABLE users (%s)" % ', '.join(cols)
    execcreate(c, sql)

    # shares table
    cols = 'id NUMBER(7)', 'timestamp DATE', 'shares NUMBER(7)', \
           'priority NUMBER(9,3)', 'started NUMBER(7)', 'cpu NUMBER(12,1)', \
           'wall NUMBER(11)', \
           'CONSTRAINT pk_shares_id_timestamp PRIMARY KEY (id, timestamp)'
    sql = "CREATE TABLE shares (%s)" % ', '.join(cols)
    execcreate(c, sql)

    # shares indices
    sql = "CREATE INDEX ix_shares_timestamp ON shares (timestamp)"
    execcreate(c, sql)

    # Procedures
    sql = '''\
CREATE PROCEDURE findusers (u VARCHAR2, c OUT sys_refcursor)
IS
BEGIN
    OPEN c FOR SELECT username FROM users WHERE username LIKE '%' || u;
END;'''
    execcreate(c, sql)

    sql = '''\
CREATE PROCEDURE findshares (u VARCHAR2, t DATE, c OUT sys_refcursor)
IS
BEGIN
    OPEN c FOR SELECT timestamp, priority, started, cpu FROM shares
    WHERE id = (SELECT id FROM users WHERE username = u)
    AND timestamp > t ORDER BY timestamp;
END;'''
    execcreate(c, sql)

def main():
    p = ArgumentParser(description="Modify fairshare DB",
                       formatter_class=ArgumentDefaultsHelpFormatter)
    p.add_argument('-u', '--username', help="username")
    p.add_argument('-p', '--password', help="password file",
                   default='/etc/fairshare')
    p.add_argument('-t', '--dsn', help="DSN")
    s = p.add_subparsers()
    pmk = s.add_parser('mktables', help="Make tables")
    pmk.set_defaults(func=mktables)
    args = p.parse_args()

    try:
        args.func(args)
    except (IOError, DatabaseError), e:
        print >>sys.stderr, str(e).strip()
        return 1

if __name__ == '__main__':
    sys.exit(main())
