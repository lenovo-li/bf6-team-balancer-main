@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cd /d "C:\Users\liyc44\Project\VC\BFTeams\BFStats"
cl /nologo /EHsc /utf-8 /std:c++20 /I include test\demo.cpp /Fe:x64\Debug\demo.exe /Fo:x64\Debug\ /link /LIBPATH:x64\Debug BFStats.lib
echo COMPILE_EXIT=%ERRORLEVEL%
