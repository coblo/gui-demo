rem Example Windows batch file to launch blockchain node
rem Update path to chain exexutable and connection string and rename this file to runchain.bat
rem Testchain Seed Nodes are: 89.163.206.83:8375 and 85.197.78.50:8375

%~dp0/app/bin/multichaind.exe coblo@89.163.206.83:8375 ^
-printtoconsole ^
-server=1 ^
-daemon ^
-autosubscribe=assets,streams ^
-autocombineminconf=4294967294 ^
-rpcbind=127.0.0.1 ^
-rpcallowip=127.0.0.1 ^
-rpcport=8374 ^
