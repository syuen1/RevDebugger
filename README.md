# RevDebugger

## Debugger is still under development (Mar 4, 2022)
 
How to use Parser:

[Compile a sorce code to a forward byte code]
-----------------------------
command: 
javacc parser.jj

javac *.java

java Parser "sorce code name"
------------------------------

This command outputs a forward byte code, parallel table files, and a contract table.
Its forward byte code name is code.txt.



______________


How to use vm_CUI.py:

[convert a forward byte code to a backward byte code]
---------------------------
command:
python vm_CUI.py code.txt c
---------------------------
This command outputs a backward byte code(inv_code.txt). 
You need to run this command before you start execution.

[execute in debug mode]
----------------------------
command:
python vm_CUI.py code.txt df
----------------------------
You select detail mode(1) or rough mode(2).
Detail mode is used to analyze the execution in detail.
Rough mode is used to analyze while viewing the overall flow.
Mainly use the detailed mode.

If the ensures is violated, start backward execution from the ensures to the exepcts.
Start forward execution again in step mode from the expects.
If the scope of re-execution is large, rewrite the expects, and start forward execution again.
Repeat the above to analyze the execution. 



