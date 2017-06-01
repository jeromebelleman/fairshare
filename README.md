# NAME

fairshare – Query LSF fairshare information

# SYNOPSIS

```
fairshare [-h] [-c CONFIG] {find,shares} ...
fairshare find [-h] user
fairshare shares [-h] [-r] [-a N] group
```

# EXAMPLE

You would typically find out about a given user's charged groups first:

```
% fairshare find fred
SHARE/XX/foo/fred
SHARE/XX/bar/fred
```

You could then list his share values over time for one of his groups:

```
% fairshare shares SHARE/XX/bar/fred

SHARE/XX/bar/fred:

    TIMESTAMP            PRIORITY    STARTED  CPU           
    1984-06-04 13:20:00  0.333       0        0.0           
    1984-06-04 13:30:00  0.333       0        0.0           
    1984-06-04 13:40:00  0.333       0        0.0           
    1984-06-04 13:50:00  0.047       6        622.0         
    1984-06-04 14:00:00  0.312       0        1029.7        
    1984-06-04 14:10:00  0.312       0        1029.7        
    1984-06-04 14:20:00  0.313       0        1006.2        
    1984-06-04 14:30:00  0.313       0        982.3         
    1984-06-04 14:40:00  0.313       0        982.3         
    1984-06-04 14:50:00  0.314       0        959.0         
    1984-06-04 15:00:00  0.314       0        936.3
    TIMESTAMP            PRIORITY    STARTED  CPU           
```

Here, the user didn't have any jobs dispatched until 13:50 when 6 started. His 
priority consequently decreased and his cumulative CPU usage increased. At 
14:00, all of his jobs finished and his cumulative CPU usage, which had reached 
a certain amount, subsequently started to decrease and his priority increased 
again. 

# COMMON OPTIONS

- `-h`, `--help`
  Show a help message and exit.

- `-c CONFIG`, `--config CONFIG`
  Use `CONFIG` as a config file which, for the time being, is only supposed
  to be a single line specifying an Oracle connection string along the lines
  of `username/password@dsn`.

# FIND SUB-COMMAND

Find the charged groups a given `user` belongs to:

```
fairshare find [-h] user
```

# SHARES SUB-COMMAND

Print the share values of a user's charged `group` over time:

```
fairshare shares [-h] [-r] [-a N] group
```

- `-r`, `--recursive`
  Recursively print all the share values of the user's parent groups. Sometimes, 
  users don't see their jobs dispatched not because their priority is too low, 
  but because the priority of one of the groups they belong to (directly or 
  indirectly) is too low. This options helps identify these cases. 
- `-a N`, `--ago N`
  Display share values after N hours ago (default: 2).

# AUTHOR

Jérôme Belleman <Jerome.Belleman@cern.ch>
