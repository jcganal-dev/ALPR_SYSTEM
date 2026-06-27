@echo off
@REM if not "%1" == "max" start /MAX cmd /c %0 max & exit/b
uvicorn --log-level warning main:app --reload