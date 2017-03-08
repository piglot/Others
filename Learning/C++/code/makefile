# Master makefile for "Thinking in C++, 2nd Edition, 
# Volume 1, Annotated Solutions Guide" by Chuck Allison
# at http://www.BruceEckel.com
# (c)2001 MindView Inc. Copyright notice in Copyright.txt
# Compiles all the code in the book

help: 
	@echo To compile all programs from 
	@echo "Thinking in C++, 2nd Edition, Volume 1, Annotated Solutions Guide"
	@echo type one of the following commands, according to your platform:
	@echo make borland
	@echo make g++
	@echo make microsoft



borland: 
	cd S02
	make
	cd ..


g++: 
	cd S02; make CPP=g++ EXEFLAG=-o OBJEXT=o


microsoft: 
	cd S02
	make microsoft CPP='cl -GX -GR"" -Dfor="if(0);else for"' EXEFLAG=-Fe OBJEXT=obj
	cd ..


clean: 
	cd S02
	del *.obj
	del *.exe
	del *.tds
	cd ..


cleanLinux: 
	cd S02; rm -f *.o; rm -f *.exe
