
# dracscan

dracscan.py is a simple program for gathering DRAC version, DRAC class and
host name from a list of Dell DRAC devices.  It reads a list of IP address
from a file named "dracscan_input" in the present working directory.  It
prints diagnostic information on stdout and also creates a CSV file named
"dracscan.csv" also in PWD.

## Example Execution / stdout

```
% python dracscan.py 
DEBUG:root:Starting
10.2.2.11: DRAC version 7, class exp, hostname WDCTEST
10.2.2.38: DRAC version 7, class ent, hostname NS1
10.2.2.105: Error interrogating: ('The read operation timed out',)
10.2.2.106: DRAC version 6, class ent, hostname None
10.2.2.217: DRAC version 7, class ent, hostname wwwtest
```

## Example Input File (dracscan_input)

```
10.2.2.11
10.2.2.38
10.2.2.105
10.2.2.106
10.2.2.217
```

## Example CSV output

```
10.2.2.11,7,exp,WDCTEST4
10.2.2.38,7,ent,NS1
10.2.2.106,6,ent,?
10.2.2.217,7,ent,wwwtest
```
