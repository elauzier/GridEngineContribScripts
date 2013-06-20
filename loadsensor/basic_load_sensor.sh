#!/bin/sh
#http://docs.oracle.com/cd/E19080-01/n1.grid.eng6/817-5677/chp8-1524/index.html

myhost=`uname -n`

while [ 1 ]; do
     # wait for input
     read input
     result=$?
     if [ $result != 0 ]; then
          exit 1
     fi
     if [ $input = quit ]; then
          exit 0
     fi	
     #send users logged in
     logins=`who | cut -f1 -d" " | sort | uniq | wc -l | sed "s/^ *//"`
     echo begin
     echo "$myhost:logins:$logins"
     echo end
done

# we never get here

exit 0