COMPILER_D=ldc2
start: start.d
	$(COMPILER_D) -O $<
