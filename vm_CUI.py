import re
import sys
import os
import time
import difflib
from multiprocessing import Process, Value, Array, Lock, Queue, Manager
codes=[]
com=[]
opr=[]
ori_num=[]
back_com=[]
back_opr=[]
back_ori_num=[]
stack=[]
rstack=[]
temp=[]
ldata=[]
rdata=[]
top=-1
count_pc=0
parflag=0
args=sys.argv

#push:
def push(a,stack,top):
    stack.append(a)
    return top+1

#pop1:
def pop1(stack,top):
    #t=stack[top-1]
    t=stack.pop()
    return (t,top-1)

#search variable table, and return variable's address
def search_table(opr,process_path):
    with open("variable_table.txt",'r') as f:
            variable_table=f.read().split('\n')
    t=0
    address=0
    for i in range(0,len(variable_table)-1,1):
        s=re.search(r'\d+',variable_table[i])
        if s.group()==(str)(opr):
            s2=re.search(r'([a-z](\d+).)+E',variable_table[i])
            match_count=0
            temp_path=s2.group()
            if len(process_path)>=len(temp_path):
                for j in reversed(range(0,len(s2.group()),1)):
                    if process_path[j]==temp_path[j]:
                        match_count=match_count+1
                    else:
                        break
                if match_count>=t:
                    address=i
                    t=match_count
    return address
    

#execution of each instruction
def executedcommand(stack,rstack,lstack,com,opr,back_com,back_opr,pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,process_number,process_path,count_pc,process_count,terminate_flag,flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag):
    if com[pc]==1 and (mode.value==0 or mode.value==3 or mode.value==4):#push　push immediate value onto own operation stack
        top=push(opr[pc],stack,top)
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==2 and (mode.value==0 or mode.value==3 or mode.value==4):#load　load value from the variable stack and push its value onto own operation stack
        value.acquire()
        c=value[search_table(opr[pc],process_path)]
        value.release()
        top=push(c,stack,top)
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==3 and (mode.value==0 or mode.value==3 or mode.value==4):#store store variable value to the variable stack and the value stack
        value.acquire()
        with open("value_stack.txt",'a') as f:
            f.write(str(value[search_table(opr[pc],process_path)])+' '+str(process_number)+'.'+process_path+'\n')
        f.close()
        rtop.value=rtop.value+2
        (value[search_table(opr[pc],process_path)],top)=pop1(stack,top)
        value.release()
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==4 and (mode.value==0 or mode.value==3 or mode.value==4):#jpc pop the value at the top of own stack and jumps to the address of the operand if the value is 1
        (c,top)=pop1(stack,top)
        if c==1:
            pre=pc
            pc=opr[pc]-2
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==5 and (mode.value==0 or mode.value==3 or mode.value==4):#jmp　unconditionally jump to the address of the operand value
        pre=pc
        pc=opr[pc]-2
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==6 and (mode.value==0 or mode.value==3 or mode.value==4):#op　perform an operation of the type of the operand
        if (opr[pc])==0:#'+'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(c+d,stack,top)
        elif (opr[pc])==1:#'*'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(c*d,stack,top)
        elif opr[pc]==2:#'-'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(d-c,stack,top)
        elif opr[pc]==3:#'>'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            if d>c:
                top=push(1,stack,top)
            else:
                top=push(0,stack,top)
        elif opr[pc]==4:#'=='
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            if d==c:
                top=push(1,stack,top)
            else:
                top=push(0,stack,top)
        elif opr[pc]==5:#'not'
            (c,top)=pop1(stack,top)
            if c==0:
                top=push(1,stack,top)
            elif c==1:
                top=push(0,stack,top)
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==7 and (mode.value==0 or mode.value==3 or mode.value==4):#label　load the label stack with the value of the PC before the jump and the process number and block path
        if args[2]=='f' or args[2]=='df':
            with open("label_stack.txt",'a') as f:
                f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+'\n')
            f.close()
            ltop.value = ltop.value+2
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==21 and mode.value==1:#rjmp　pop a value from the label stack and jump to its PC
        s2=re.search(r'([a-z]\d+\.)+',lstack[ltop.value+1])
        process_path=s2.group()+"E"
        if process_path[0]=='p':
            s3=re.search(r'(p\d+\.)(c\d+\.)',process_path)
            process_path=process_path[len(s3.group()):len(process_path)]
        a=count_pc-int(lstack[ltop.value])
        ltop.value=ltop.value-2
        pre=pc
        return (a,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==22 and mode.value==1:#restore　pop a value from the value stack and stores it on the variable stack
        s2=re.search(r'([a-z]\d+\.)+',rstack[rtop.value+1])
        process_path=s2.group()+"E"
        value[search_table(back_opr[pc],process_path)]=int(rstack[rtop.value])
        rtop.value=rtop.value-2
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif (com[pc]==19 and (mode.value==0 or mode.value==3 or mode.value==4)) or (back_com[pc]==28  and mode.value==1):#nop　no operation
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif (com[pc]==8  and (mode.value==0 or mode.value==3 or mode.value==4)) or (back_com[pc]==23 and mode.value==1):#par　indicates the start and end of a parallel block
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==9 and (mode.value==0 or mode.value==3 or mode.value==4):#alloc　allocate a new variable address and set its initial value to 0
        if args[2]=='f' or args[2]=='df':
            with open("variable_table.txt",'r') as f:
                t1=f.read().split('\n')
            var_flag=0
            s1=str(opr[pc])+'.'+process_path+'      0'
            for i in range(0,len(t1),1):
                if t1[i]==s1:
                    var_flag=1
            if var_flag==0:
                value[tablecount.value] = 0
                variable_region.append(0)
                with open("variable_table.txt",'a') as f:
                    f.write(str(opr[pc])+'.'+process_path+'      0\n')
                tablecount.value=tablecount.value+1
        elif args[2]=='b' or args[2]=='db':
            variable_path=search_table(opr[pc],process_path)
            variable_region.append(0)
            with open("variable_table.txt",'r') as f:
                variable_table=f.read().split('\n')
            s=re.search(r'\s(-)?(\d+)',variable_table[variable_path])
            variable_value=int(s.group().strip(' '))
            value[search_table(opr[pc],process_path)]=variable_value
            tablecount.value=tablecount.value+1
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==10 and (mode.value==0 or mode.value==3 or mode.value==4):#free　release a variable address and stores the previous value on the value stack
        table_address=search_table(opr[pc],process_path)
        value.acquire()
        with open("value_stack.txt",'a') as f:
            f.write(str(value[search_table(opr[pc],process_path)])+' '+str(process_number)+'.'+process_path+'\n')
        f.close()
        value.release()
        value[table_address]=0
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==11 and (mode.value==0 or mode.value==3 or mode.value==4):#proc　start the procedure, execute the label and block instructions
        process_path='p'+str(opr[pc])+'.'+process_path
        if args[2]=='f' or args[2]=='df':
            with open("label_stack.txt",'a') as f:
                f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+'\n')
            f.close()
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==12 and (mode.value==0 or mode.value==3 or mode.value==4):#ret　end the procedure
        p_lstack=[]
        with open("label_stack.txt",'r') as f:
            p_lstack=f.read().split()
        f.close()
        if process_path[0]!='p':
            process_path='p'+str(opr[pc])+'.'+process_path
        for i in range(0,len(p_lstack),1):
            if (i%2)==1:
                t1=re.search(r'([a-z]\d+\.)+E',p_lstack[i])
                if t1.group()==process_path:
                    c=int(p_lstack[i-1])
                    break
        for i in range(0,len(process_path),1):
            if process_path[i] == '.':
                process_path=process_path[i+1:len(process_path)]
                break
        pre=pc
        return (c,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==13 and (mode.value==0 or mode.value==3 or mode.value==4):#block　add path
        if com[pc+3]==14 and (com[pc+1]==5 or com[pc+1]==8):
            process_path='c'+str(opr[pc])+'.'+process_path
        else:
            if process_path!='E':
                t1=re.search(r'b\d+',process_path)
                if t1.group()=='b'+str(opr[pc]):
                    process_path=process_path
                else:
                    process_path='b'+str(opr[pc])+'.'+process_path 
            else:
                process_path='b'+str(opr[pc])+'.'+process_path
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==14 and (mode.value==0 or mode.value==3 or mode.value==4):#end　delete path
        for i in range(0,len(process_path),1):
            if process_path[i] == '.':
                process_path=process_path[i+1:len(process_path)]
                break
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==15 and (mode.value==0 or mode.value==3 or mode.value==4):#fork generate parallel processes
        lock.release()#lock.release()
        process={}
        start_process_count = process_count.value
        already_terminate = {}
        now_process_count.value=now_process_count.value-1
        f=open('a'+(str)(opr[pc])+'.txt',mode='r')
        tables=f.read()
        #refer to the parallel block table, load the start and end address respectively, and give them to each process to generate a process
        for i in range(0,len(tables),10):
            t1=tables[i:i+4]
            s1=re.search(r'\d+',t1)
            t2=tables[i+5:i+9]
            s2=re.search(r'\d+',t2)
            my_flag_number=process_count.value+1
            print("my_flag_number"+str(my_flag_number))
            terminate_flag[my_flag_number]=0
            process[process_count.value]=Process(target=execution,args=(com,opr,back_com,back_opr,(int)(s1.group())-1,(int)(s2.group()),count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,0,variable_region,lock,process_number + '.' + str(process_count.value-start_process_count+1),process_path,process_count,terminate_flag,my_flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag))
            process_count.value=process_count.value+1
        end_process_count = process_count.value
        for i in range(start_process_count,process_count.value,1):
            process[i].start()
        terminate_count=0
        #Monitors whether the process it generated is terminated or not, if it is terminated, terminate the process completely
        for i in range(0,100,1):
            already_terminate[i]=0
        while True:
            for i in range(start_process_count,end_process_count,1):
                if terminate_flag[i+1]==1 and already_terminate[i]==0:
                    process[i].terminate()
                    process[i].join()
                    already_terminate[i]=1
                    terminate_count=terminate_count+1
                    if not process[i].is_alive():
                        process[i].join()
            if terminate_count==end_process_count-start_process_count:
                pre=pc
                lock.acquire()#lock.acquire()
                now_process_count.value=now_process_count.value+1
                process_count.value=process_count.value-terminate_count
                return (int(s2.group()),pre,stack,top,rtop,tablecount,process_path)
        pre=pc
        lock.acquire()#lock.acquire()
        return (a,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==16 and (mode.value==0 or mode.value==3 or mode.value==4):#merge end the parallel block
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==17 and (mode.value==0 or mode.value==3 or mode.value==4):#func start the function
        process_path='f'+str(opr[pc])+'.'+process_path
        if args[2]=='f' or args[2]=='df':
            with open("label_stack.txt",'a') as f:
                f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+'\n')
            f.close()
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif com[pc]==18 and (mode.value==0 or mode.value==3 or mode.value==4):#f_return end the funtion
        p_lstack=[]
        with open("label_stack.txt",'r') as f:
            p_lstack=f.read().split()
        f.close()
        if process_path[0]!='f':
            process_path='f'+str(opr[pc])+'.'+process_path
        for i in range(0,len(p_lstack),1):
            if (i%2)==1:
                t1=re.search(r'([a-z]\d+\.)+E',p_lstack[i])
                if t1.group()==process_path:
                    c=int(p_lstack[i-1])
                    break
        for i in range(0,len(process_path),1):
            if process_path[i] == '.':
                process_path=process_path[i+1:len(process_path)]
                break
        pre=pc
        return (c,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==24 and mode.value==1:#r_alloc the alloc instruction in the reverse direction, pop a value form the value stack and stores it at the address of the allocated variable stack
        s2=re.search(r'([a-z]\d+\.)+',rstack[rtop.value+1])
        process_path=s2.group()+'E'
        with open("variable_table.txt",'r') as f:
            t1=f.read().split('\n')
        var_flag=0
        s1=str(back_opr[pc])+'.'+process_path+'      0'
        for i in range(0,len(t1),1):
            if t1[i]==s1:
                #print("check")
                var_flag=1
        if var_flag==0:
            with open("variable_table.txt",'a') as f:
                f.write(str(back_opr[pc])+'.'+process_path+'E      0\n')
            tablecount.value=tablecount.value+1
        value[search_table(back_opr[pc],process_path)]=int(rstack[rtop.value])
        rtop.value=rtop.value-2
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==25 and mode.value==1:#r_free free instuctions in the reverse direction
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==26 and mode.value==1:#r_fork fork instructions in the reverse direction
        lock.release()
        process={}
        start_process_count = process_count.value
        now_process_count.value=now_process_count.value-1
        f=open('a'+(str)(back_opr[pc])+'.txt',mode='r')
        already_terminate = {}
        tables=f.read()
        tables_process_number = int(len(tables)/10)
        for i in range(0,len(tables),10):
            t1=tables[i:i+4]
            s1=re.search(r'\d+',t1)
            t2=tables[i+5:i+9]
            s2=re.search(r'\d+',t2)
            my_flag_number=process_count.value+1
            terminate_flag[my_flag_number]=0
            process[process_count.value]=Process(target=execution,args=(com,opr,back_com,back_opr,count_pc-(int)(s2.group()),count_pc-(int)(s1.group())+1,count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,0,variable_region,lock,process_number + '.' + str(process_count.value-start_process_count+1),process_path,process_count,terminate_flag,my_flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag))
            process_count.value=process_count.value+1
        end_process_count = process_count.value
        for i in range(start_process_count,process_count.value,1):
            process[i].start()
        terminate_count=0
        for i in range(0,100,1):
            already_terminate[i]=0
        t3=tables[0:0+4]
        s3=re.search(r'\d+',t3)
        while True:
            for i in range(start_process_count,end_process_count,1):
                if terminate_flag[i+1]==1 and already_terminate[i]==0:
                    process[i].terminate()
                    process[i].join()
                    already_terminate[i]=1
                    terminate_count=terminate_count+1
                    if not process[i].is_alive():
                        process[i].join()
            if terminate_count==end_process_count-start_process_count:
                pre=pc
                lock.acquire()
                now_process_count.value=now_process_count.value+1
                ret_pc=count_pc-int(s3.group())+1
                if (mode.value==3 or mode.value==4) and com[ret_pc]!=16:
                    ret_pc=int(s2.group())
                    t1=tables[0:4]
                    s1=re.search(r'\d+',t1)
                    pre=int(s1.group())-2
                process_count.value=process_count.value-terminate_count
                return (ret_pc,pre,stack,top,rtop,tablecount,process_path)
        for i in range(start_process_count,process_count.value,1):
            process[i].join()
        a=count_pc-int(s3.group())
        pre=pc
        lock.acquire()
        return (a,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc]==27 and mode.value==1:#r_merge merge instruction in the reverse direction
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)

#This function executes bytecodes.
def execution(command,opr,back_com,back_opr,start,end,count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,endflag,variable_region,lock,process_number,process_path,process_count,terminate_flag,flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag):
    pc=start
    pre=pc
    top=len(stack)
    num_variables = tablecount.value
    recovered_statement_flag=0
    now_process_count.value=now_process_count.value+1
    my_terminate_flag=0
    end_skip_flag=0
    path_record='E'
    rough_mode_change=0
    start_exec=0
    #forward
    if args[2]=='df' or args[2]=='f':
        while pc!=end or (pc==end and end_skip_flag==1) or command[pre]==15 or my_terminate_flag==1:
            lock.acquire()
            program_counter.value=pc
            if (command[pc]!=15 and (mode.value==0 or mode.value==3 or mode.value==4)) or (back_com[pc]!=26 and mode.value==1) or mode.value==2:
                mlock.acquire()
            q.put(process_path)
            q2.put(process_number)
            q3.put(flag_number)
            if rough_mode_change==0 and mode.value==5:
                mode.value=4
                rough_mode_change=1
            if mode.value==0:
                if command[pc]==1:
                    command1='   ipush'
                elif command[pc]==2:
                    command1='    load'
                elif command[pc]==3:
                    command1='   store'
                elif command[pc]==4:
                    command1='     jpc'
                elif command[pc]==5:
                    command1='     jmp'
                elif command[pc]==6:
                    command1='      op'
                elif command[pc]==7:
                    command1='   label'
                elif command[pc]==8:
                    command1='     par'
                elif command[pc]==9:
                    command1='   alloc'
                elif command[pc]==10:
                    command1='    free'
                elif command[pc]==11:
                    command1='    proc'
                elif command[pc]==12:
                    command1='p_return'
                elif command[pc]==13:
                    command1='   block'
                elif command[pc]==14:
                    command1='     end'
                elif command[pc]==15:
                    command1='    fork'
                elif command[pc]==16:
                    command1='   merge'
                elif command[pc]==17:
                    command1='    func'
                elif command[pc]==18:
                    command1='f_return'
                elif command[pc]==19:
                    command1='     nop'
                with open("output.txt",'a') as f:
                    f.write("~~~~~~~~Process"+process_number+" execute~~~~~~~~\n")
                    f.write("path : "+process_path+"\n")
                    f.write("pc = "+str(pc+1)+"["+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"\n")
                print("~~~~~~~~Process"+process_number+" execute~~~~~~~~")
                print("path : "+process_path)
                print("pc = "+str(pc+1)+" [line:"+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"")
                #execute each instruction
                (pc,pre,stack,top,rtop,tablecount,process_path)=executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,process_number,process_path,count_pc,process_count,terminate_flag,flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag)
                if command[pre]==15:
                    with open("output.txt",'a') as f:
                        f.write("---fork end--- (process "+process_number+")\n")
                    print("---fork end--- (process "+process_number+")")
                with open("output.txt",'a') as f:
                    f.write("executing stack:       "+str(stack[0:])+"\n")
                    f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n")
                    f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
                print("executing stack:       "+str(stack[0:])+"")
                print("[variable]")
                with open("variable_table.txt",'r') as f:
                    table1=f.read().split()
                with open("table.txt",'r') as f:
                    table2=f.read().split()
                variable_name=[]
                for i in range(0,len(table2),3):
                    variable_name.append(table2[i])
                for i in range(0,tablecount.value,1):
                    t1=re.search(r'\d+',table1[2*i])
                    t2=re.search(r'([a-z]\d+\.)+',table1[2*i])
                    print(t2.group()+'['+variable_name[int(t1.group())]+'] = '+str(value[i]))
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                path_record=process_path
            #backward mode
            elif mode.value ==1:
                if mchange_flag.value==0:
                    mchange_flag.value=1
                    pc = count_pc-pre-1
                    end = count_pc-start-1
                    with open("label_stack.txt",'r') as f:
                        lstack=f.read().split()
                    ltop.value=len(lstack)-2
                    with open("value_stack.txt",'r') as f:
                        rstack=f.read().split()
                    rtop.value=len(rstack)-2
                #backward exec
                if back_com[pc]==21:
                    command1='    rjmp'
                elif back_com[pc]==22:
                    command1='  restore'
                elif back_com[pc]==23:
                    command1='     par'
                elif back_com[pc]==24:
                    command1=' r_alloc'
                elif back_com[pc]==25:
                    command1='  r_free'
                elif back_com[pc]==26:
                    command1='  r_fork'
                elif back_com[pc]==27:
                    command1=' r_merge'
                elif back_com[pc]==28:
                    command1='     nop'
                s=re.search(r'\d(\.\d+)*',lstack[ltop.value+1])
                s2=re.search(r'\d(\.\d+)*',rstack[rtop.value+1])
                with open("endflag.txt",'r') as f:
                    my_endflag=f.read().split(',')
                #check if the process number matches the process number on each value stack and label stack top in rjmp,restore.
                if ((process_number==s2.group() and (back_com[pc]==22 or back_com[pc]==24)) or (process_number==s.group() and back_com[pc]==21) or (back_com[pc]!=21 and back_com[pc]!=22 and back_com[pc]!=24)) and my_terminate_flag==0:
                    with open("process_record.txt",'a') as f:
                        f.write(process_number+",")
                    f.close()
                    with open("reverse_output.txt",'a') as f:
                        f.write("~~~~~~~~Process"+process_number+" execute~~~~~~~~\n")
                        f.write("path : "+process_path+"\n")
                        f.write("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(back_com[pc])+"    operand = "+str(back_opr[pc])+"\n")
                    print("~~~~~~~~Process"+process_number+" execute~~~~~~~~")
                    print("path : "+process_path)
                    print("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(back_com[pc])+"    operand = "+str(back_opr[pc])+"")
                    if my_endflag[0]!='':
                        if my_endflag[flag_number]=='1' and back_com[pc]==23 and back_opr[pc]==1:
                            my_terminate_flag=1
                    if back_com[pc]==26:
                        with open('a'+(str)(back_opr[pc])+'.txt',mode='r') as f:
                            tables=f.read()
                        t3=tables[0:0+4]
                        s3=re.search(r'\d+',t3)
                        if end==count_pc-int(s3.group())+1:
                            end_skip_flag=1
                    #execute each instructions
                    (pc,pre,stack,top,rtop,tablecount,process_path)=executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,process_number,process_path,count_pc,process_count,terminate_flag,flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag)
                    if back_com[pre]==26:
                        with open("reverse_output.txt",'a') as f:
                            f.write("---fork end--- (process "+process_number+")\n")
                        print("---fork end--- (process "+process_number+")")
                    with open("reverse_output.txt",'a') as f:
                        f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n\n")
                    print("shared variable stack: "+str(value[0:tablecount.value])+"\n")
                    if back_com[pre]==27:
                        end_skip_flag=0
            elif mode.value==2 and recovered_statement_flag==0:
                i=0
                while True:
                    if process_back_ori_num[pre+i]==process_back_ori_num[pre]:
                        i=i+1
                    else:
                        break
                pc=count_pc-pre+i-2
                if my_terminate_flag==1:
                    pc=pc-1
                recovered_statement_flag=1
                monitor_process_count.value=monitor_process_count.value+1
                my_terminate_flag=0
            elif mode.value==3 or mode.value==4:
                if True:
                    next_process='-1'
                    if mode.value==3:
                        with open("process_record.txt",'r') as f:
                            process_record=f.read().split(',')
                        next_process=process_record[len(process_record)-step_flag.value-2]
                        print("next_process:"+next_process)
                        print("process_number:"+process_number)
                    if mode.value==4:
                        q.put(process_path)
                        q2.put(process_number)
                        q3.put(flag_number)
                        program_counter.value=pc
                        with open("exp_error_process.txt",'r') as f:
                            t1=f.read()
                    if (next_process==process_number and mode.value==3) or (mode.value==4 and t1!=process_number):
                        if command[pc]==1:
                            command1='   ipush'
                        elif command[pc]==2:
                            command1='    load'
                        elif command[pc]==3:
                            command1='   store'
                        elif command[pc]==4:
                            command1='     jpc'
                        elif command[pc]==5:
                            command1='     jmp'
                        elif command[pc]==6:
                            command1='      op'
                        elif command[pc]==7:
                            command1='   label'
                        elif command[pc]==8:
                            command1='     par'
                        elif command[pc]==9:
                            command1='   alloc'
                        elif command[pc]==10:
                            command1='    free'
                        elif command[pc]==11:
                            command1='    proc'
                        elif command[pc]==12:
                            command1='p_return'
                        elif command[pc]==13:
                            command1='   block'
                        elif command[pc]==14:
                            command1='     end'
                        elif command[pc]==15:
                            command1='    fork'
                        elif command[pc]==16:
                            command1='   merge'
                        elif command[pc]==17:
                            command1='    func'
                        elif command[pc]==18:
                            command1='f_return'
                        elif command[pc]==19:
                            command1='     nop'
                        with open("output.txt",'a') as f:
                            f.write("~~~~~~~~Process"+process_number+" execute~~~~~~~~\n")
                            f.write("path : "+process_path+"\n")
                            f.write("pc = "+str(pc+1)+"   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"\n")
                        print("~~~~~~~~Process"+process_number+" execute~~~~~~~~")
                        print("path : "+process_path)
                        print("pc = "+str(pc+1)+" [line:"+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"")
                        if mode.value==3:
                            step_flag.value=step_flag.value+1
                        #execute each instructions
                        (pc,pre,stack,top,rtop,tablecount,process_path)=executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,process_number,process_path,count_pc,process_count,terminate_flag,flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag)
                        if command[pre]==15:
                            with open("output.txt",'a') as f:
                                f.write("---fork end--- (process "+process_number+")\n")
                            print("---fork end--- (process "+process_number+")")
                        with open("output.txt",'a') as f:
                            f.write("executing stack:       "+str(stack[0:])+"\n")
                            f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n")
                            f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
                        print("executing stack:       "+str(stack[0:])+"")
                        print("[variable]")
                        with open("variable_table.txt",'r') as f:
                            table1=f.read().split()
                        with open("table.txt",'r') as f:
                            table2=f.read().split()
                        variable_name=[]
                        for i in range(0,len(table2),3):
                            variable_name.append(table2[i])
                        for i in range(0,tablecount.value,1):
                            t1=re.search(r'\d+',table1[2*i])
                            t2=re.search(r'([a-z]\d+\.)+',table1[2*i])
                            print(t2.group()+'['+variable_name[int(t1.group())]+'] = '+str(value[i]))
                        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                        if command[pre]==8 and opr[pre]==1 and pc!=end:
                            end=count_pc-start
                        if rough_mode_change==1:
                            pc=pc-1
                            rough_mode_change=0
                            print("rough_mode")
                            start=start-1
                        path_record=process_path
                    recovered_statement_flag=0
            if (command[pre]!=15 and (mode.value==0 or mode.value==3 or mode.value==4)) or (back_com[pre]!=26 and mode.value==1) or mode.value==2: #and mode.value!=3 and mode.value!=4:
                mlock.release()     
            lock.release()
        #set terminate_flag to 1 when the process terminate.
        now_process_count.value=now_process_count.value-1
        terminate_flag[flag_number]=1
        print("terminate execute "+str(flag_number))
    #backward
    if args[2]=='db' or args[2]=='b':
        while pc!=end or command[pre]==26:
            lock.acquire()
            if command[pc]==21:
                command1='    rjmp'
            elif command[pc]==22:
                command1='  restore'
            elif command[pc]==23:
                command1='     par'
            elif command[pc]==24:
                command1=' r_alloc'
            elif command[pc]==25:
                command1='  r_free'
            elif command[pc]==26:
                command1='  r_fork'
            elif command[pc]==27:
                command1=' r_merge'
            elif command[pc]==28:
                command1='     nop'
            s=re.search(r'\d(\.\d+)*',lstack[ltop.value+1])
            s2=re.search(r'\d(\.\d+)*',rstack[rtop.value+1])
            if (process_number==s2.group() and (command[pc]==22 or command[pc]==24)) or (process_number==s.group() and command[pc]==21) or (command[pc]!=21 and command[pc]!=22 and command[pc]!=24):
                with open("reverse_output.txt",'a') as f:
                    f.write("~~~~~~~~Process"+process_number+" execute~~~~~~~~\n")
                    f.write("path : "+process_path+"\n")
                    f.write("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"\n")
                print("~~~~~~~~Process"+process_number+" execute~~~~~~~~")
                #print("path : "+process_path)
                print("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"")
                (pc,pre,stack,top,rtop,tablecount,process_path)=executedcommand(stack,rstack,lstack,command,opr,pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,process_number,process_path,count_pc,process_count,terminate_flag,flag_number)
                if command[pre]==26:
                    with open("reverse_output.txt",'a') as f:
                        f.write("---fork end--- (process "+process_number+")\n")
                    print("---fork end--- (process "+process_number+")")
                with open("reverse_output.txt",'a') as f:
                    f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n\n")
                print("shared variable stack: "+str(value[0:tablecount.value])+"\n")
            lock.release()
        terminate_flag[flag_number]=1
    #return stack        

#read the code for execution and store it in each list
def coderead():
    global codes
    global com
    global opr
    global count_pc
    global parflag
    f=open(args[1],mode='r')
    codes=f.read()
    f.close()
    count_pc=0
    for l in codes[:-1].split("\n"):
        t1=l[0:2]
        s1=re.search(r'\d+',t1)
        t2=l[2:8]
        s2=re.search(r'\d+',t2)
        t3=l[8:14]
        s3=re.search(r'\d+',t3)
        com.append((int)(s1.group()))
        opr.append((int)(s2.group()))
        ori_num.append((int)(s3.group()))
        count_pc=count_pc+1
    f2=open("inv_code.txt",mode='r')
    codes2=f2.read()
    f2.close()
    for l2 in codes2[:-1].split("\n"):
        t1=l2[0:2]
        s1=re.search(r'\d+',t1)
        t2=l2[2:8]
        s2=re.search(r'\d+',t2)
        t3=l2[8:14]
        s3=re.search(r'\d+',t3)
        back_com.append((int)(s1.group()))
        back_opr.append((int)(s2.group()))
        back_ori_num.append((int)(s3.group()))

#clear each list
def coderead_list_clear():
    com.clear()
    opr.clear()
    ori_num.clear()
    back_com.clear()
    back_opr.clear()
    back_ori_num.clear()
    count_pc=0

#convert each instruction in the forward direction to backward instruction
def forward(com,opr,count_pc):
    f2=open("inv_code.txt",mode='w')
    for i in range(0,count_pc,1):
        if com[count_pc-i-1]==7:#label to rjmp
            f2.write("21     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==3:#store to restore
            f2.write("22 "+str(opr[count_pc-i-1]).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==4:#jpc to nop
            f2.write("28     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==5:
            f2.write("28     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")#jmp to nop
        elif com[count_pc-i-1]==8:#par to par
            if opr[count_pc-i-1]==0:
                f2.write("23 "+str(1).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
            elif opr[count_pc-i-1]==1:
                f2.write("23 "+str(0).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==9:#alloc to r_free
            f2.write("25 "+str(opr[count_pc-i-1]).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==10:#free to r_alloc
            f2.write("24 "+str(opr[count_pc-i-1]).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==11:#proc to rjmp
            pname="p"+str(opr[count_pc-i-1])
            f2.write("21 "+pname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==12:#p_return to nop
            pname="p"+str(opr[count_pc-i-1])
            f2.write("28 "+pname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==13:#block to nop
            if com[count_pc-i]==5 and com[count_pc-i+1]==7 and com[count_pc-i+2]==16:
                bname="c"+str(opr[count_pc-i-1])
            else:
                bname="b"+str(opr[count_pc-i-1])
            f2.write("28 "+bname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==14:#end to nop
            if com[count_pc-i-2]==7 and com[count_pc-i-3]==5 and com[count_pc-i-4]==15:
                bname="c"+str(opr[count_pc-i-1])
            else:
                bname="b"+str(opr[count_pc-i-1])
            f2.write("28 "+bname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==15:#fork to r_merge
            aname="a"+str(opr[count_pc-i-1])
            f2.write("27 "+aname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==16:#merge to r_fork
            aname="a"+str(opr[count_pc-i-1])
            f2.write("26 "+aname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==17:#func to rjmp
            fname="f"+str(opr[count_pc-i-1])
            f2.write("21 "+fname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==18:#f_return to nop
            fname="f"+str(opr[count_pc-i-1])
            f2.write("28 "+fname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        else:
            f2.write("28     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
    f2.close()

#read contract table and store each list
def read_contract_table(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath):
    f3=open("contract_table.txt",mode='r')
    table1=f3.read()
    con_table=table1[:-1]
    count_exp=0
    count_ens=0
    bef=0
    if con_table=='':
        exp_PC=100000
        ens_PC=100000
        f3.close()
        return (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
    for l in con_table.split("\n"):
        if l[0]=='{':
            if bef==0:
                i=0
                while l[i+1]!='}':
                    debug_a1=l[i+1:i+4]
                    debug_b1=re.search(r'\d+',debug_a1)
                    exp_com[count_exp].append((int)(debug_b1.group()))
                    debug_a2=l[i+4:i+10]
                    debug_b2=re.search(r'(-)?\d+',debug_a2)
                    exp_opr[count_exp].append((int)(debug_b2.group()))
                    i=i+10
                count_exp=count_exp+1
            elif bef==1:
                i=0
                while l[i+1]!='}':
                    debug_a1=l[i+1:i+4]
                    debug_b1=re.search(r'\d+',debug_a1)
                    ens_com[count_ens].append((int)(debug_b1.group()))
                    debug_a2=l[i+4:i+10]
                    debug_b2=re.search(r'(-)?\d+',debug_a2)
                    ens_opr[count_ens].append((int)(debug_b2.group()))
                    i=i+10
                count_ens=count_ens+1
        else:
            if l[12:15]=='EXP':
                debug_t1=l[0:5]
                debug_s1=re.search(r'\d+',debug_t1)
                debug_t2=l[6:11]
                debug_s2=re.search(r'\d+',debug_t2) 
                exp_name.append((int)(debug_s1.group()))
                exp_PC.append((int)(debug_s2.group()))
                exp_xpath.append(l[17:])
                bef=0
            elif l[12:15]=='ENS':
                debug_t1=l[0:5]
                debug_s1=re.search(r'\d+',debug_t1)
                debug_t2=l[6:11]
                debug_s2=re.search(r'\d+',debug_t2)
                ens_name.append((int)(debug_s1.group()))
                ens_PC.append((int)(debug_s2.group()))
                ens_xpath.append(l[17:])
                bef=1
    f3.close()
    del exp_xpath[0]
    del ens_xpath[0]
    return (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)

#clear each list
def all_contract_list_clear(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath):
    exp_name.clear()
    exp_PC.clear()
    ens_name.clear()
    ens_PC.clear()
    for i in range(0,len(exp_com),1):
        exp_com[i].clear()
    for i in range(0,len(exp_opr),1):
        exp_opr[i].clear()
    for i in range(0,len(ens_com),1):
        ens_com[i].clear()
    for i in range(0,len(ens_opr),1):
        ens_opr[i].clear()
    exp_xpath.clear()
    ens_xpath.clear()
    exp_xpath.append("")
    ens_xpath.append("")    
    return (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)

#monitor executes contract's bytecodes
def monitor_exec_command(stack,top,com,opr,process_path,living_flag):
    if com==1:#push　
        top=push(opr,stack,top)
        return (stack,top)
    elif com==2:#load　
        c=value[search_table(opr,process_path)]
        top=push(c,stack,top)
        return (stack,top)
    elif com==6:#op　
        if (opr)==0:#'+'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(c+d,stack,top)
        elif (opr)==1:#'*'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(c*d,stack,top)
        elif opr==2:#'-'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            top=push(d-c,stack,top)
        elif opr==3:#'>'
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            if d>c:
                top=push(1,stack,top)
            else:
                top=push(0,stack,top)
        elif opr==4:#'=='
            (c,top)=pop1(stack,top)
            (d,top)=pop1(stack,top)
            if d==c:
                top=push(1,stack,top)
            else:
                top=push(0,stack,top)
        elif opr==5:#'not'
            (c,top)=pop1(stack,top)
            if c==0:
                top=push(1,stack,top)
            elif c==1:
                top=push(0,stack,top)
        return (stack,top)
    elif com==30:#terminated
        if living_flag==1:
            top=push(1,stack,top)
        elif living_flag==0:
            top=push(0,stack,top)
        return (stack,top)
    elif com==31:#living
        if living_flag==1:
            top=push(0,stack,top)
        elif living_flag==0:
            top=push(1,stack,top)  
        return (stack,top)

def search_xpath(exp_xpath,xpath_table,xpath_process_number,my_process_number,xpath_flag_number):
    t1=my_process_number.split('.')
    xpath_process_path="E"
    my_flag_number=0
    if exp_xpath=="SELF":
        t2=my_process_number
    elif exp_xpath=="PRECEND":
        t1[-1]=str(int(t1[-1])-1)
        t2='.'.join(t1)
    elif exp_xpath=="FOLLOW":
        t1[-1]=str(int(t1[-1])+1)
        t2='.'.join(t1)
    for i in range(0,len(xpath_table),1):
        if t2==xpath_process_number[i]:
            xpath_process_path=xpath_table[i]
            my_flag_number=xpath_flag_number[i]
    return (xpath_process_path,my_flag_number)

#main function
if __name__ == '__main__':
    manager = Manager()
    start_time = time.time()
    start=[]
    end=[]
    tabledata=[]
    tablecount= Value('i',0)
    address = Array('i',10)
    value = Array('i',100)
    rstack = Array('i',100000)
    lstack = Array('i',100000)
    rtop = Value('i',0)
    ltop = Value('i',0)
    program_counter = Value('i',0)
    endflag= Array('i',100) #{}
    for i in range(0,100,1):
        endflag[i]=0
    endflag0=Value('i',0)
    notlabelflag=0
    lock=Lock()
    variable_region = []
    process_number='0'
    process_path='E'
    process_count = Value('i',0)
    q = manager.Queue()
    q2 = manager.Queue()
    q3 = manager.Queue()
    terminate_flag = Array('i',100)
    mchange_flag = Value('i',0)
    for i in range(0,100,1):
        terminate_flag[i]=0
    exp_name = []
    exp_PC = []
    ens_name = []
    ens_PC = []
    exp_com = [[]*1 for i in range(10)]
    ens_com = [[]*1 for i in range(10)]
    exp_opr = [[]*1 for i in range(10)]
    ens_opr = [[]*1 for i in range(10)]
    exp_xpath = [[]]
    ens_xpath = [[]]
    xpath_table = []
    xpath_process_number = []
    xpath_flag_number = []
    my_flag_number = 0
    path_queue="b1.E"
    path_queue2="0"
    path_queue3=0
    mode4_flag=0
    exp_err_pc=0
    error_pc=0
    latest_pc=0
    record_pc=0
    process_back_ori_num = Array('i',1000)
    mlock = Lock()
    mlock2 = Lock()
    monitor_stack = []
    monitor_process_count = Value('i',0)
    now_process_count = Value('i',0)
    parent_count = Value('i',0)
    step_flag = Value('i',0)
    mode = Value('i',0) #0:forward 1:backward
    process_permission = Array('i',100)
    exp_error_flag=0
    one_time_error_flag=0
    temp_path='0'
    temp_path2='0'
    check_skip=0
    lockfree  = Lock()
    a='1'
    path='table.txt'
    f=open(path,mode='r')
    tabledata=f.read()
    f.close()
    #initialize each file
    if args[2]=='f' or args[2]=='df':
        with open("variable_table.txt",'w') as f:
            f.write("")
        f.close()
        with open("value_stack.txt",'w') as f:
            f.write("")
        f.close()
        with open("label_stack.txt",'w') as f:
            f.write("")
        f.close()
        with open("output.txt",'w') as f:
            f.write("")
        f.close()
        with open("process_record.txt",'w') as f:
            f.write("")
        f.close()
        with open("reverse_output.txt",'w') as f:
            f.write("")
        f.close()
        with open("exp_error_process.txt",'w') as f:
            f.write("")
        f.close()
        with open("endflag.txt",'w') as f:
            f.write("")
        f.close()
        with open("record_contract_table.txt",'w') as f:
            f.write("")
    elif args[2]=='b' or args[2]=='db':
        with open("variable_table.txt",'w') as f:
            f.write("")
        f.close()
        with open("label_stack.txt",'r') as f:
            label_stack=f.read().split()
        ltop.value=len(label_stack)-2
        with open("value_stack.txt",'r') as f:
            value_stack=f.read().split()
        rtop.value=len(value_stack)-2
        with open("reverse_output.txt",'w') as f:
            f.write("")
        f.close()
    k=0
    #read a bytecode
    coderead()
    for i in range(0,len(back_ori_num),1):
        process_back_ori_num[i]=back_ori_num[i]
    (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)=read_contract_table(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
    #forward execution
    if args[2]=='df':
        exec_mode=input("[select mode] 1:detail mode, 2:rough mode")
        process = Process(target=execution,args=(com,opr,back_com,back_opr,0,count_pc,count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,endflag0,variable_region,lock,process_number,process_path,process_count,terminate_flag,0,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,now_process_count,process_back_ori_num,step_flag))
        process.start()
        if exec_mode=='1':
            while program_counter.value+1!=count_pc:
                mlock.acquire()
                if mode.value==0:
                    check_flag=0
                    if not q.empty():
                        path_queue=q.get(block=False)
                    if not q2.empty():
                        path_queue2=q2.get(block=False)
                    if not q3.empty():
                        path_queue3=q3.get(block=False)
                        path_update_flag=1
                    new_number=0
                    for i in range(0,len(xpath_process_number),1):
                        if xpath_process_number[i]!=path_queue2:
                            new_number=new_number+1
                        elif xpath_process_number[i]==path_queue2:
                            xpath_table[i]=path_queue
                            xpath_flag_number[i]=path_queue3
                    if new_number==len(xpath_process_number):
                        xpath_process_number.append(path_queue2)
                        xpath_table.append(path_queue)
                        xpath_flag_number.append(path_queue3)
                    con_number=0
                    i=0
                    for check_PC in exp_PC:
                        if check_PC==program_counter.value:
                            check_flag=1
                            con_number=i
                        i=i+1
                    if check_flag==1:
                        (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                        monitor_top=0
                        i=0
                        for l in exp_com[con_number]:
                            (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                            i=i+1
                        if monitor_stack[-1]==0:
                            print("[error] expects ")
                            str2=input("1:end monitor, enter:continue")
                            if str2=='1':
                                break
                #ensures control
                    check_flag=0
                    i=0
                    for check_PC in ens_PC:
                        if check_PC==program_counter.value:
                            check_flag=1
                            con_number=i
                        i=i+1
                    if check_flag==1:
                        (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                        monitor_top=0
                        i=0
                        for l in ens_com[con_number]:
                            (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                            i=i+1
                        if monitor_stack[-1]==0:
                            print("[error] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                            mode.value=1
                            back_ens_com=ens_com[con_number]
                            back_ens_opr=ens_opr[con_number]
                            back_xpath_process_path=xpath_process_path
                            back_my_flag_number=my_flag_number
                            ens_back_pc=program_counter.value
                            ens_error_check=0
                    #    sys.exit()
                            str2=input("enter: backward mode")
                            if str2=='1':
                                break
                if mode.value==1:
                    check_flag=0
                    i=0
                    con_number=0
                    for l in back_ens_com:
                        (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,back_ens_com[i],back_ens_opr[i],back_xpath_process_path,terminate_flag[back_my_flag_number])
                        i=i+1
                    if monitor_stack[-1]==1 and ens_error_check==0:
                        error_pc=latest_pc
                        ens_error_check=1
                        print("ensures check")
                    latest_pc=program_counter.value
                    i=0
                    for check_PC in exp_PC:
                        if ((count_pc-check_PC)==program_counter.value and mode4_flag==0):
                            check_flag=1
                            con_number=i
                            print("program_counter check")
                        i=i+1
                    if mode4_flag==1 and (count_pc-exp_err_pc)==program_counter.value:
                        mode4_flag=2
                    if mode4_flag==2 and (count_pc-record_pc+1)==program_counter.value:
                        check_flag=1
                        mode4_flag=0
                        print("record_pc "+str(record_pc))
                        print(program_counter.value)
                    if check_flag==1:
                        mode.value=2
                if mode.value==2:#change backward mode to forward step mode 
                    if now_process_count.value==monitor_process_count.value:
                        print("all process got back")
                        print("error line:"+str(back_ori_num[error_pc]))
                        str4=input("1:step mode 2:auto mode 3:compile a program with new contract")
                        if str4=='3':
                            str5=input("input file name : ")
                            os.system('java Parser '+str5)
                            str4=input("1:step mode 2:auto mode ")
                        if str4=='1':
                            mode.value=3
                        elif str4=='2':
                            mode.value=4
                        for i in range(0,100,1):
                            endflag[i]=0
                        step_count=0
                        one_time_error_flag=0
                        print(exp_xpath)
                        coderead_list_clear()
                        coderead()
                        for i in range(0,len(back_ori_num),1):
                            process_back_ori_num[i]=back_ori_num[i]
                        (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)=all_contract_list_clear(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
                        (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)=read_contract_table(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
                        print(exp_xpath)
                        str3=input()
                    #mlock2.release()
                if mode.value==3:#step forward mode
                    if True:#step_flag.value==2:
                        if not q.empty():
                            path_queue=q.get(block=False)
                        if not q2.empty():
                            path_queue2=q2.get(block=False)
                        if not q3.empty():
                            path_queue3=q3.get(block=False)
                        new_number=0
                        for i in range(0,len(xpath_process_number),1):
                            if xpath_process_number[i]!=path_queue2:
                                new_number=new_number+1
                            elif xpath_process_number[i]==path_queue2:
                                xpath_table[i]=path_queue
                        if new_number==len(xpath_process_number):
                            xpath_process_number.append(path_queue2)
                            xpath_table.append(path_queue)
                            xpath_flag_number.append(path_queue3)
                        #expects check
                        check_flag=0
                        con_number=0
                        i=0
                        for check_PC in exp_PC:
                            if check_PC==program_counter.value:
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            print("expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1))
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in exp_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                            str2=input("1:end monitor, enter:continue")
                            if str2=='1':
                                break
                        #ensures control
                        con_number=0
                        check_flag=0
                        i=0
                        for check_PC in ens_PC:
                            if check_PC==program_counter.value:
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            print("ensures check")
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in ens_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                                #print(monitor_stack)
                            if monitor_stack[-1]==0:
                                print("[error] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                                mode.value=1
                                mchange_flag.value=0
                                back_ens_com=ens_com[con_number]
                                back_ens_opr=ens_opr[con_number]
                                back_xpath_process_path=xpath_process_path
                                back_my_flag_number=my_flag_number
                                ens_back_pc=program_counter.value
                                ens_error_check=0
                                with open("process_record.txt",'w') as f:
                                    f.write("")
                                f.close()
                                step_flag.value=0
                                monitor_process_count.value=0
                        #    sys.exit()
                            str2=input("1:backward 2:break")
                            if str2=='2':
                                break
                            elif str2=='1':
                                mode.value=1
                                mchange_flag.value=0
                                with open("process_record.txt",'w') as f:
                                    f.write("")
                                f.close()
                                step_flag.value=0
                                monitor_process_count.value=0
                        str5=input("enter: next step")
                        step_count=step_count+1
                elif mode.value==4:
                    if True:#step_flag.value==2:
                        if not q.empty():
                            path_queue=q.get(block=False)
                        if not q2.empty():
                            path_queue2=q2.get(block=False)
                        if not q3.empty():
                            path_queue3=q3.get(block=False)
                        new_number=0
                        for i in range(0,len(xpath_process_number),1):
                            if xpath_process_number[i]!=path_queue2:
                                new_number=new_number+1
                            elif xpath_process_number[i]==path_queue2:
                                xpath_table[i]=path_queue
                        if new_number==len(xpath_process_number):
                            xpath_process_number.append(path_queue2)
                            xpath_table.append(path_queue)
                            xpath_flag_number.append(path_queue3)
                        #expects check
                        check_flag=0
                        con_number=0
                        i=0
                        for check_PC in exp_PC:
                            if check_PC==program_counter.value:
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in exp_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                            if monitor_stack[-1]==0:
                                exp_error_flag=1
                        if exp_error_flag==1:
                            if one_time_error_flag==0:
                                print("[error] expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1))
                                with open("exp_error_process.txt",'w') as f:
                                    f.write(path_queue2)
                                one_time_error_flag=1
                                error_exp_com=exp_com[con_number]
                                error_exp_opr=exp_opr[con_number]
                                error_xpath_process_path=xpath_process_path
                                error_my_flag_number=my_flag_number
                                mode4_flag=1
                                exp_err_pc=program_counter.value
                                endflag[my_flag_number]=1
                                with open("endflag.txt",'w') as f:
                                    for i in range(0,100,1):
                                        f.write(str(endflag[i])+",")
                            if one_time_error_flag==1 and exp_err_pc!=program_counter.value:
                                record_pc=program_counter.value+1
                                one_time_error_flag=2
                                endflag[path_queue3]=1
                                with open("endflag.txt",'w') as f:
                                    for i in range(0,100,1):
                                        f.write(str(endflag[i])+",")
                            i=0
                            for l in error_exp_com:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,error_exp_com[i],error_exp_opr[i],error_xpath_process_path,terminate_flag[error_my_flag_number])
                                i=i+1
                            if monitor_stack[-1]==1:
                            #release error process
                                with open("exp_error_process.txt",'w') as f:
                                    f.write('-1')
                                exp_error_flag=0
                        #ensures control
                        con_number=0
                        check_flag=0
                        i=0
                        for check_PC in ens_PC:
                            if check_PC==program_counter.value:
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            print("ensures check")
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in ens_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                            if monitor_stack[-1]==0:
                                print("[error] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                                mode.value=1
                                mchange_flag.value=0
                                back_ens_com=ens_com[con_number]
                                back_ens_opr=ens_opr[con_number]
                                back_xpath_process_path=xpath_process_path
                                back_my_flag_number=my_flag_number
                                ens_back_pc=program_counter.value
                                ens_error_check=0
                                with open("process_record.txt",'w') as f:
                                    f.write("")
                                f.close()
                                step_flag.value=0
                                monitor_process_count.value=0
                        #    sys.exit()
                            str2=input("1:backward 2:break")
                            if str2=='2':
                                for i in range(0,process_count.value,1):
                                    if terminate_flag[i]==0:
                                        terminate_flag[i]=1
                                mlock.release()
                                break
                            elif str2=='1':
                                mode.value=1
                                mchange_flag.value=0
                                with open("process_record.txt",'w') as f:
                                    f.write("")
                                f.close()
                                step_flag.value=0
                                monitor_process_count.value=0
                        step_count=step_count+1
                mlock.release()
        elif exec_mode=='2':
            rough_mode_change=0
            mode.value=4
            while (program_counter.value+1!=count_pc and mode.value==4) or rough_mode_change==1:
                mlock.acquire()
                if mode.value==4:
                    check_flag=0
                    if not q.empty():
                        path_queue=q.get(block=False)
                    if not q2.empty():
                        path_queue2=q2.get(block=False)
                    if not q3.empty():
                        path_queue3=q3.get(block=False)
                        path_update_flag=1
                    search_process_number=path_queue2
                    new_number=0
                    for i in range(0,len(xpath_process_number),1):
                        if xpath_process_number[i]!=path_queue2:
                            new_number=new_number+1
                        elif xpath_process_number[i]==path_queue2:
                            xpath_table[i]=path_queue
                            xpath_flag_number[i]=path_queue3
                    if new_number==len(xpath_process_number):
                        xpath_process_number.append(path_queue2)
                        xpath_table.append(path_queue)
                        xpath_flag_number.append(path_queue3)
                    con_number=0
                    i=0
                    if check_skip==1:
                        for check_PC in exp_PC:
                            if check_PC==rec_check_pc:
                                check_flag=1
                                con_number=i
                                search_process_number=rec_process_number
                                check_skip=2
                        i=i+1
                    con_number=0
                    i=0
                    for check_PC in exp_PC:
                        if check_PC==program_counter.value:
                            if com[program_counter.value-1]==8 and opr[program_counter.value-1]==0 and check_skip==0:
                                check_skip=1
                                rec_check_pc=program_counter.value
                                rec_process_number=path_queue2
                                input("check through")
                                with open("exp_error_process.txt",'w') as f:
                                    f.write(path_queue2)
                            else:
                                check_flag=1
                                con_number=i
                        i=i+1
                    if check_flag==1:
                        (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,search_process_number,xpath_flag_number)
                        monitor_top=0
                        i=0
                        for l in exp_com[con_number]:
                            (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                            i=i+1
                        if monitor_stack[-1]==0:
                            exp_error_flag=1
                    if exp_error_flag==1:
                        if one_time_error_flag==0:
                            print("[error] expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1))
                            input("enter:next step")
                            if temp_path=='0':
                                with open("exp_error_process.txt",'w') as f:
                                    f.write(search_process_number)
                            elif temp_path!='0':
                                with open("exp_error_process.txt",'w') as f:
                                    f.write(temp_path)
                            one_time_error_flag=1
                            error_exp_com=exp_com[con_number]
                            error_exp_opr=exp_opr[con_number]
                            error_xpath_process_path=xpath_process_path
                            error_my_flag_number=my_flag_number
                            mode4_flag=1
                            exp_err_pc=program_counter.value
                            endflag[my_flag_number]=1
                            with open("endflag.txt",'w') as f:
                                for i in range(0,100,1):
                                    f.write(str(endflag[i])+",")
                        if one_time_error_flag==1 and exp_err_pc!=program_counter.value:
                            record_pc=program_counter.value+1
                            one_time_error_flag=2
                            endflag[path_queue3]=1
                            with open("endflag.txt",'w') as f:
                                for i in range(0,100,1):
                                    f.write(str(endflag[i])+",")
                        i=0
                        for l in error_exp_com:
                            (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,error_exp_com[i],error_exp_opr[i],error_xpath_process_path,terminate_flag[error_my_flag_number])
                            i=i+1
                        if monitor_stack[-1]==1:
                        #release error process
                            with open("exp_error_process.txt",'w') as f:
                                f.write('-1')
                            exp_error_flag=0
                    if temp_path!=path_queue2:
                        temp_path=path_queue2
                    if check_skip==2:
                        i=0
                        check_terminate_flag=0
                        for check_xpath_pc in xpath_process_number:
                            if check_xpath_pc!=rec_process_number:
                                if terminate_flag[xpath_flag_number[i]]==1:
                                    check_terminate_flag=check_terminate_flag+1
                            i=i+1
                        if check_terminate_flag==len(xpath_process_number)-2:
                            input("dead lock. enter:backward mode")
                            mode.value=1
                            rough_mode_change2=0
                            record_contract_top=2
                            ens_error_flag=0
                            break
                #ensures control
                    check_flag=0
                    i=0
                    for check_PC in ens_PC:
                        if check_PC==program_counter.value:
                            check_flag=1
                            con_number=i
                        i=i+1
                    if check_flag==1:
                        (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                        monitor_top=0
                        i=0
                        for l in ens_com[con_number]:
                            (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                            i=i+1
                        if monitor_stack[-1]==0:
                            print("[error] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                            #mode.value=1
                            with open("record_contract_table.txt",'a') as f:
                                f.write(str(ens_PC[con_number])+" F\n")
                    #    sys.exit()
                            str2=input("enter: next step")
                            if str2=='1':
                                break
                        elif monitor_stack[-1]==1:
                            with open("record_contract_table.txt",'a') as f:
                                f.write(str(ens_PC[con_number])+" T\n")
                    if program_counter.value+1==count_pc and rough_mode_change==0:
                        mode.value=5
                        rough_mode_change=1
                    elif rough_mode_change==1:
                        str7=input("enter: backward mode")
                        mode.value=1
                        rough_mode_change2=0
                        record_contract_top=2
                        ens_error_flag=0
                elif mode.value==1:
                    with open("record_contract_table.txt",'r') as f:
                        record_contract=f.read().split('\n')
                    if record_contract_top<len(record_contract):
                        t1=re.search(r'\d+',record_contract[-record_contract_top])
                        t2=re.search(r'T|F',record_contract[-record_contract_top])
                        if t2.group()=='F' and ens_error_flag==0:
                            if int(t1.group())==count_pc-program_counter.value+1:
                                input("next_step")
                                ens_error_flag=1
                        elif t2.group()=='T' and ens_error_flag==0:
                            record_contract_top=record_contract_top+1
                        elif ens_error_flag==1:
                            input("next_step")
                            for i in range(0,len(exp_PC),1):
                                if ens_PC[i]==int(t1.group()):
                                    ret_exp_pc=exp_PC[i]
                                    break
                            if ret_exp_pc==count_pc-program_counter.value:
                                record_contract_top=record_contract_top+1
                                ens_error_flag=0
                    if program_counter.value+1==count_pc and rough_mode_change2==0:
                        rough_mode_change2=1
                    elif rough_mode_change2==1:
                        input("enter: end")
                        break
                mlock.release()
            print("while end")
        process.join()
    elif args[2]=='c':#convert forward bytecode to backward bytecode
        forward(com,opr,count_pc)
    
    elapsed_time = time.time()-start_time
    print("elapsed_time:{0}".format(elapsed_time) + "[sec]")