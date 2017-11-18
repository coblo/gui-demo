# Example Windows batch file to launch blockchain node
# Update path to chain exexutable and connection string and rename this file to runchain.bat

C:\path_to\multichaind.exe coblo@89.163.206.83:8375 ^
-printtoconsole ^
-server=1 ^
-autosubscribe=assets,streams ^
-autocombineminconf=4294967294 ^
-rpcbind=127.0.0.1 ^
-rpcallowip=127.0.0.1 ^
-rpcport=8374 ^
