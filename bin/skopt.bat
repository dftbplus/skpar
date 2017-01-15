@echo off
rem Use python to execute the python script having the same name as this batch
rem file, but without any extension, located in the same directory as this
rem batch file
rem #!/usr/bin/env python3 "%~dpn0" %*
\Users\admin\anaconda3\python.exe "%~dpn0" %*
