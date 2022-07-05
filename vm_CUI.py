# 03/20/2022 S.Yuen
#
import re
import sys
import os
import time
import difflib
from multiprocessing import Process, Value, Array, Lock, Queue, Manager, Semaphore
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
    f.close()
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
    if args[2]=='df' or args[2]=='f':
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


#convert each instruction in the forward direction to backward instruction
def forward(com,opr,count_pc):
    f2=open("inv_code.txt",mode='w')
    for i in range(0,count_pc,1):
        if com[count_pc-i-1]==7:#label to rjmp
            f2.write("21     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==3:#store to restore
            f2.write("22 "+str(opr[count_pc-i-1]).rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==4:#jpc to nop (changed [yuen] to label)
            f2.write("7     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
        elif com[count_pc-i-1]==5:
            f2.write("7     0 ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")#jmp to nop (chnged [yuen] to label)
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
        elif com[count_pc-i-1]==12:#p_return to nop [yuen]
            pname="p"+str(opr[count_pc-i-1])
            f2.write("7  "+pname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
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
        elif com[count_pc-i-1]==18:#f_return to label [yuen]
            fname="f"+str(opr[count_pc-i-1])
            f2.write("7 "+fname.rjust(5)+" ("+str(ori_num[count_pc-i-1]).rjust(4)+")\n")
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
def coderead_list_clear():
    com.clear()
    opr.clear()
    ori_num.clear()
    back_com.clear()
    back_opr.clear()
    back_ori_num.clear()
    count_pc=0

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

#execution of each instruction
def executedcommand(stack,rstack,lstack,com,opr,back_com,back_opr,\
    pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,\
        process_number,process_path,count_pc,process_count,terminate_flag,flag_number,\
        mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,from_jump_flag,\
        monitor_process_count,now_process_count,process_back_ori_num,step_flag,jmp_flag,monitor_turn,p_turn,gjtop):
    #print("exec command called")
    #push push immediate value onto own operation stack
    if com[pc]==1 and mode.value!=1:
        if (mode.value==0 or mode.value==4):
            top=push(opr[pc],stack,top)
        # no operation for mode 3
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #load load value from the variable stack and push its value onto own operation stack
    elif com[pc]==2 and mode.value!=1:
        if (mode.value==0 or mode.value==4):
            value.acquire()
            c=value[search_table(opr[pc],process_path)]
            value.release()
            top=push(c,stack,top)
        # no operation for mode 
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #store variable value to the variable stack and the value stack
    elif com[pc]==3 and mode.value!=1:
        if (mode.value==0 or mode.value==4):
            value.acquire()
            (c,top) = pop1(stack,top)
            with open("value_stack.txt",'a') as f:
                f.write(str(value[search_table(opr[pc],process_path)])+' '+str(process_number)+'.'+process_path+' '+str(c)+'\n')
            f.close()
            value[search_table(opr[pc],process_path)]=c
            value.release()
        else: # mode.value == 3 rtop increased by 3 by execution
#            print("rtop=",rtop.value)
            with open("value_stack.txt",'r') as f:
                rstk = f.read().split()
            f.close()
            value[search_table(opr[pc],process_path)]=int(rstk[rtop.value+2])
#            print("pc="+str(pc)+" rtop="+str(rtop.value)+" rstk=",rstk)
        rtop.value = rtop.value + 3
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #jpc pop the value at the top of own stack and jumps to the address of the operand if the value is 1
    elif com[pc]==4 and mode.value!=1: #no jump in mode 1 (rev mode)
        if (mode.value==0 or  mode.value==4):
            (c,top)=pop1(stack,top)
            pre=pc
            if c==1:
                with open("jump_stack.txt",'a') as f:
                    f.write('1 '+process_number+' '+str(pc+1)+'\n')
                    f.flush()
                f.close()
                pc=opr[pc]-2
            else:
                with open("jump_stack.txt",'a') as f:
                    f.write('0 '+process_number+' '+str(pc+1)+'\n')
                    f.flush()
                f.close()
        else: # mode 3
            pre = pc
            if jmp_flag==1:
                pc = opr[pc]-2
            gjtop.value = gjtop.value + 3
            # proceed to next result of jump
            # didnt branch
#            print("mode 3 jpc: pid="+process_number+"jmp_flag="+str(jmp_flag))
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #jmp unconditionally jump to the address of the operand value
    elif com[pc]==5 and mode.value!=1:
        pre = pc
        if mode.value==0 or mode.value==4: # record jump happened
            with open("jump_stack.txt",'a') as f:
                f.write('1 '+process_number+' '+str(pc+1)+'\n')
                f.flush()
            f.close()
        else: # mode 3
            gjtop.value = gjtop.value + 3
        pc = opr[pc]-2 # operand is the address from 1.
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #op perform an operation of the type of the operand
    elif com[pc]==6 and mode.value!=1:
        if (mode.value==0 or mode.value==4):
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
        # noting for mode 3
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #label load the label stack with the value of the PC before the jump and the process number and block path
    elif com[pc]==7 and mode.value!=1:
        if mode.value==0 or mode.value==4:
            with open("label_stack.txt",'a') as f:
                if from_jump_flag == 1: # label from jump
                    f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+' 1\n')
                else: # label from flow
                    f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+' 0\n')
                f.flush()
            f.close()
        # else: # in mode 3, track the last entry of label_stack
        ltop.value=ltop.value+3
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    elif back_com[pc] == 7 and (mode.value==1): # jmp or jpc in the forward mode
        #!!! decreas jtop???? in the process
        # reversed a jump in mode 1 for mode 3
        # in mode 3, first jpc/jmp follow as jstack[jtop]
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #rjmp pop a value from the label stack and jump to its PC
    # ltop decreased by 2 [yuen]
    elif back_com[pc]==21 and mode.value==1:
        s2=re.search(r'([a-z]\d+\.)+',lstack[ltop.value-3+1])
        process_path=s2.group()+"E"
        if process_path[0]=='p':
            s3=re.search(r'(p\d+\.)(c\d+\.)',process_path)
            process_path=process_path[len(s3.group()):len(process_path)]
        a=count_pc-int(lstack[ltop.value-3])
        ltop.value=ltop.value-3
        pre=pc
        return (a,pre,stack,top,rtop,tablecount,process_path)
    #restore pop a value from the value stack and stores it on the variable stack
    elif back_com[pc]==22 and mode.value==1:
        s2=re.search(r'([a-z]\d+\.)+',rstack[rtop.value-3+1])
        process_path=s2.group()+"E"
        value[search_table(back_opr[pc],process_path)]=int(rstack[rtop.value-3])
        rtop.value=rtop.value-3 # [yuen]
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #nop no operation
    elif (com[pc]==19 and (mode.value==0 or mode.value==3 or mode.value==4))\
            or (back_com[pc]==28  and mode.value==1):
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #par indicates the start and end of a parallel block
    elif (com[pc]==8  and (mode.value==0 or mode.value==3 or mode.value==4))\
        or (back_com[pc]==23 and mode.value==1):
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #alloc allocate a new variable address and set its initial value to 0
    elif com[pc]==9 and mode.value!=1:
    #   if args[2]=='f' or args[2]=='df':
        if mode.value == 0 or mode.value == 4 or mode.value == 3:
            with open("variable_table.txt",'r') as f:
                t1=f.read().split('\n')
            var_flag=0
            s1=str(opr[pc])+'.'+process_path+'      0'
            for i in range(0,len(t1),1):
                if t1[i]==s1:
                    var_flag=1
            if var_flag==0: # variable not allocated
                value[tablecount.value] = 0
                variable_region.append(0)
                with open("variable_table.txt",'a') as f:
                    f.write(str(opr[pc])+'.'+process_path+'      0\n')
                tablecount.value=tablecount.value+1
        '''    
        elif args[2]=='b' or args[2]=='db': # code not used?
            variable_path=search_table(opr[pc],process_path)
            variable_region.append(0)
            with open("variable_table.txt",'r') as f:
                variable_table=f.read().split('\n')
            s=re.search(r'\s(-)?(\d+)',variable_table[variable_path])
            variable_value=int(s.group().strip(' '))
            value[search_table(opr[pc],process_path)]=variable_value
            tablecount.value=tablecount.value+1
        '''
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #free release a variable address and stores the previous value on the value stack
    elif com[pc]==10 and mode.value!=1:
        if mode.value == 0 or mode.value == 4:
            table_address=search_table(opr[pc],process_path)
            value.acquire()
            with open("value_stack.txt",'a') as f:
                f.write(str(value[search_table(opr[pc],process_path)])+' '+str(process_number)+'.'+process_path+' b'+'\n')
            f.close()
            value.release()
            value[table_address]=0
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #proc start the procedure, execute the label and block instructions
    elif com[pc]==11 and (mode.value==0 or mode.value==3 or mode.value==4):
        process_path='p'+str(opr[pc])+'.'+process_path
        if mode.value == 0 or mode.value == 4:
            with open("label_stack.txt",'a') as f:
                f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+' 1\n')
                f.flush()
            f.close()
        ltop.value=ltop.value+3
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #ret end the procedure and function
    elif (com[pc]==12 or com[pc]==18) and mode.value!=1:
        pre=pc
        p_lstack=[]
        with open("label_stack.txt",'r') as f:
            p_lstack=f.read().split()
        f.close()
        if process_path[0]!='p':
            process_path='p'+str(opr[pc])+'.'+process_path
        for i in range(0,len(p_lstack),3):
            t1=re.search(r'([a-z]\d+\.)+E',p_lstack[i+1])
            if t1.group()==process_path:
                c=int(p_lstack[i])
                break
        for i in range(0,len(process_path),1):
            if process_path[i] == '.':
                process_path=process_path[i+1:len(process_path)]
                break
        if mode.value==0 or mode.value ==4:
            with open("jump_stack.txt",'a') as f:
                f.write('1 '+str(process_number)+' '+str(pc+1)+'\n')
                f.flush()
            f.close()
        else: # mode 3
            gjtop.value = gjtop.value + 3
        # ltop.value = ltop.value + 2
        return (c,pre,stack,top,rtop,tablecount,process_path) # procedure path is lost !!
    #block add path
    elif com[pc]==13 and (mode.value==0 or mode.value==3 or mode.value==4):
        if com[pc+3]==14 and (com[pc+1]==5 or com[pc+1]==8): # pc+3 end  pc+1 jump/par  call block
            process_path='c'+str(opr[pc])+'.'+process_path # call path
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
    #end delete path
    elif com[pc]==14 and (mode.value==0 or mode.value==3 or mode.value==4):
        for i in range(0,len(process_path),1):
            if process_path[i] == '.':
                process_path=process_path[i+1:len(process_path)]
                break
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #fork generate parallel processes
    elif com[pc]==15 and (mode.value==0 or mode.value==3 or mode.value==4):
        lock.release()#lock.release()
        process={}
        mlock2.acquire() # exclude from the other forking processes until finishing makeing process names
        start_process_count = process_count.value
        already_terminate = {}
        now_process_count.value=now_process_count.value-1
        with open('a'+(str)(opr[pc])+'.txt',mode='r') as f:
            tables=f.read()
        f.close()
        #refer to the parallel block table, load the start and end address respectively, and give them to each process to generate a process
        for i in range(0,len(tables),10):
            t1=tables[i:i+4]
            s1=re.search(r'\d+',t1)
            t2=tables[i+5:i+9]
            s2=re.search(r'\d+',t2)
            my_flag_number=process_count.value+1
#           print("my_flag_number"+str(my_flag_number))
            terminate_flag[my_flag_number]=0
            monitor_turn.value = 1
            p_turn.value = 0
            process[process_count.value]=Process(target=execution,args=(com,opr,back_com,back_opr,(int)(s1.group())-1,(int)(s2.group()),\
                count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,gjtop,0,variable_region,lock,\
                    process_number + '.' + str(process_count.value-start_process_count+1),process_path,process_count,\
                        terminate_flag,my_flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,\
                            monitor_process_count,now_process_count,process_back_ori_num,step_flag,monitor_turn,p_turn,0))
            process_count.value=process_count.value+1
        end_process_count = process_count.value
        mlock2.release() # all subprocesses are ready
        p_turn.value = 0
        for i in range(start_process_count,end_process_count,1): # changed from process_count to end_process_count
            process[i].start()
        terminate_count=0
        #Monitors whether the process it generated is terminated or not, if it is terminated, terminate the process completely
        for i in range(0,100,1):
            already_terminate[i]=0
        while True:  # wait for all processes to terminate
            for i in range(start_process_count,end_process_count,1):
                if terminate_flag[i+1]==1 and already_terminate[i]==0:
                    process[i].terminate()
                    process[i].join()
                    already_terminate[i]=1
                    terminate_count=terminate_count+1
                    if not process[i].is_alive():
                        process[i].join()
            if terminate_count==end_process_count-start_process_count: # all processes are terminated
              pre=pc
              if p_turn.value == 1:
                lock.acquire()#lock.acquire()
                now_process_count.value=now_process_count.value+1
                process_count.value=process_count.value-terminate_count
                # Very trick situation happens when the direction is changed while waiting for terminations
                # subprocesses terminate either forwards or backwards.  The forking process acts as if it executed r_merge instruction.
                if mode.value == 1:
                    return (pre,int(s2.group())+1,stack,top,rtop,tablecount,process_path) # direction is changed while waiting for terminations
                else:
                    return (int(s2.group())+1,pre,stack,top,rtop,tablecount,process_path) # move to merge [yuen] pc must be next of last s2
        pre=pc
        lock.acquire()#lock.acquire()
        return (a,pre,stack,top,rtop,tablecount,process_path)
    #merge end the parallel block
    elif com[pc]==16 and (mode.value==0 or mode.value==3 or mode.value==4):
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #func start the function
    elif com[pc]==17 and mode.value!=1:
        process_path='f'+str(opr[pc])+'.'+process_path
        if mode.value == 0 or mode.value == 4:
            with open("label_stack.txt",'a') as f:
                f.write(str(pre+1)+' '+str(process_number)+'.'+process_path+' 1\n')
                f.flush()
            f.close()
        # else: # mode 3
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)

    #r_alloc the alloc instruction in the reverse direction, pop a value form the value stack and stores it at the address of the allocated variable stack
    elif back_com[pc]==24 and mode.value==1:
        s2=re.search(r'([a-z]\d+\.)+',rstack[rtop.value-3+1])
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
        value[search_table(back_opr[pc],process_path)]=int(rstack[rtop.value-3])
        rtop.value=rtop.value-3 # [yuen]
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #r_free free instuctions in the reverse direction
    elif back_com[pc]==25 and mode.value==1:
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
    #r_fork fork instructions in the reverse direction
    elif back_com[pc]==26 and mode.value==1:
        lock.release()
        process={}
        mlock2.acquire()
        start_process_count = process_count.value
        now_process_count.value=now_process_count.value-1
        f=open('a'+(str)(back_opr[pc])+'.txt',mode='r')
        already_terminate = {}
        tables=f.read()
        tables_process_number = int(len(tables)/10)
        for i in range(0,len(tables),10):
            t1=tables[i:i+4]
            s1=re.search(r'\d+',t1) # end address is count_pc-s1+1
            t2=tables[i+5:i+9]
            s2=re.search(r'\d+',t2) # start address is count_pc-s2+1
            my_flag_number=process_count.value+1
            terminate_flag[my_flag_number]=0
            revnew_process_number = process_number + '.' + str(process_count.value-start_process_count+1) # [yuen]
            # mchange_flag ?? doublely reverse???  #  
            process[process_count.value]=Process(target=execution,args=(com,opr,back_com,back_opr,count_pc-(int)(s2.group()),\
                count_pc-(int)(s1.group())+1,count_pc,stack,address,value,tablecount,rstack,lstack,rtop,ltop,gjtop,0,variable_region,\
                    lock,revnew_process_number,process_path,\
                        process_count,terminate_flag,my_flag_number,mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,\
                            monitor_process_count,now_process_count,process_back_ori_num,step_flag,monitor_turn,p_turn,1))
            process_count.value=process_count.value+1
        #    print("r_fork "+str(count_pc-(int)(s2.group()))+":"+str(count_pc-(int)(s1.group())+1))
        end_process_count = process_count.value
        mlock2.release()
        for i in range(start_process_count,end_process_count,1):
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
            if terminate_count==end_process_count-start_process_count: # all subporcesses are terminated
              pre=pc
              if p_turn.value == 1:
                lock.acquire()
                process_count.value=process_count.value-terminate_count
                now_process_count.value=now_process_count.value+1       # resume this process               
                if (mode.value==3 or mode.value==4) and com[ret_pc]!=16: # mode is changed while waiting
                #    t1=tables[0:4]
                #    s1=re.search(r'\d+',t1)
                    pre=int(s3.group())-1    # beginning address forward of the block
                    ret_pc=int(s2.group())+1 # end address forward of he block               
                else: # mode 1 Still in the backward mode
                    pre=pc
                    ret_pc=count_pc-int(s3.group())+2
                # Very trick situation happens when the direction is changed while waiting for terminations
                # subprocesses terminate either forwards or backwards.  The forking process acts as if it executed r_merge instruction
                return (ret_pc,pre,stack,top,rtop,tablecount,process_path)
        for i in range(start_process_count,process_count.value,1):
            process[i].join()
        a=count_pc-int(s3.group())
        pre=pc
        lock.acquire()
        return (a,pre,stack,top,rtop,tablecount,process_path)
    #r_merge merge instruction in the reverse direction
    elif back_com[pc]==27 and mode.value==1:
        pre=pc
        return (pc+1,pre,stack,top,rtop,tablecount,process_path)
#    return(pc,pre,stack,top,rtop,tablecount,process_path)
################# executed command ###########################################

#This function executes bytecodes.  wrapping Process invocation
def execution(command,opr,back_com,back_opr,start,end,count_pc,\
    stack,address,value,tablecount,rstack,lstack,rtop,ltop,gjtop,endflag,variable_region,\
        lock,process_number,process_path,process_count,terminate_flag,flag_number,\
            mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,\
            now_process_count,process_back_ori_num,step_flag,monitor_turn,p_turn,rstart_flag):
    pc=start
    pre=pc
    top=len(stack) # local stack
    num_variables = tablecount.value
    recovered_statement_flag=0 # inversion flag
    now_process_count.value=now_process_count.value+1 # process is started and alive
    my_terminate_flag=0
    end_skip_flag=0 # debug use
    jtop = 0 # jump counter
    jstack = []
    jmp_flag = 0
    path_record='E'
    # rough_mode_change=0
    next_process = '-1'  # for mode 3
    start_exec=0
    pre_mode = 0
    my_rstart_flag=rstart_flag # rstart_flag = 1 then the process invoded in mode 1
    my_initflag=1
    my_nonfork_flag = 0
    from_jump_flag = 0 # whether label is from jump or not
    jump_com = 0 # 1 if command is one of 4,5,12/reset by label
    #forward
    if args[2]=='df' or args[2]=='f':
        while pc!=end or (pc==end and end_skip_flag==1) or command[pre]==15 or my_terminate_flag==1:
            lock.acquire()
            if mode.value != pre_mode:
                my_initflag = 1 # mode changed this turn
#[0320]                print("Mode Change!! process_number=",process_number," mode=",mode.value," pre_mode=",pre_mode)
            pre_mode = mode.value
            #
            program_counter.value=pc
            if (command[pc]!=15 and (mode.value==0 or mode.value==3 or mode.value==4))\
                or (back_com[pc]!=26 and mode.value==1) or mode.value==2:
                my_nonfork_flag = 1
                mlock.acquire() # if not fork nor r_fork
            q.put(process_path)
            q2.put(process_number)
            q3.put(flag_number)
            ############ Mode 0/4 execution ###############################
            if mode.value == 0 or mode.value ==4:
                #### Mode 4 needs reversal initially ####
                if my_initflag == 1: #local initilization
                    my_initflag = 0 # reset initflag
                    # no initialization for mode 0
                    if mode.value == 4: # mode 4 initialization
                        pc = count_pc-pre-1
                        end = count_pc-start-1
                        with open("jump_stack.txt",'r') as f:
                            jstack0=f.read().split()
                        f.close()
                        for i in range(0,jtop,1):
                            if (process_number==jstack0[i*3+1]):
                                jstack.append(int(jstack0[i*3]))
                #### Forward execition
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
                    f.write("~~~~~~~~Process "+" "+process_number+" forward execute~~~~~~(mode="+str(mode.value)+")~~\n")
                    f.write("path : "+process_path+"\n")
                    f.write("pc = "+str(pc+1)+"["+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"\n")
                print("~~~~~~~~Process "+" "+process_number+" forward execute~~~~~~(mode="+str(mode.value)+")~~")
                print("path : "+process_path)
                print("pc = "+str(pc+1)+" [line:"+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"")
                # jmp_flag = 0
                if command[pc]==4 or command[pc]==5 or command[pc]==12:
                    jump_com=1
                if command[pc]==7:
                    if jump_com==1:
                        from_jump_flag = 1
                        jump_com=0
                    else:
                        from_jump_flag = 0
                #execute each instruction
                if p_turn.value == 1:
                  (pc,pre,stack,top,rtop,tablecount,process_path)=\
                    executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,\
                        pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,\
                            process_number,process_path,count_pc,process_count,terminate_flag,flag_number,\
                                mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,from_jump_flag,\
                                    monitor_process_count,now_process_count,process_back_ori_num,step_flag,0,monitor_turn,p_turn,gjtop)
                  monitor_turn.value = 1 # changed program counter
                  p_turn.value = 0 # executed an instruction
                if command[pre]==15: # fork has been executed: forked processes are terminated
                    with open("output.txt",'a') as f:
                        f.write("---fork end--- (process "+process_number+")\n")
                    print("---fork end--- (process "+process_number+")")
                    monitor_turn.value = 1
                with open("output.txt",'a') as f:
                    f.write("executing stack:       "+str(stack[0:])+"\n")
                    f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n")
                    f.write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n")
                print("executing stack:       "+str(stack[0:])+"")
                print("[variable]")
                with open("variable_table.txt",'r') as f: # internal representation
                    table1=f.read().split()
                with open("table.txt",'r') as f: # name table  name/offset
                    table2=f.read().split()
                variable_name=[]
                for i in range(0,len(table2),3):
                    variable_name.append(table2[i])
                for i in range(0,tablecount.value,1):
                    t1=re.search(r'\d+',table1[2*i])
                    t2=re.search(r'([a-z]\d+\.)+',table1[2*i])
                    print(t2.group()+'['+variable_name[int(t1.group())]+'] = '+str(value[i]))
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
                recovered_statement_flag = 0 # for mode 4
                path_record=process_path
            ###### backward mode (mode 1) #####
            elif mode.value ==1:
                if my_rstart_flag==0: # The process invoked in forward Local initialization
                    # started by r_fork with my_rstart_flag = 1, otherwise this is 0
                    # print("Process locally reversed")
                    my_rstart_flag=1
                    pc = count_pc-pre-1
                    end = count_pc-start-1
                if my_initflag ==1: # all processes deal with jump_stack locally
                    my_initflag =0
                    # initialize jump stack for this process
                    with open("jump_stack.txt",'r') as f:
                        jstack0=f.read().split()
                    f.close()
                    jstack=[]
                    for i in range(0,len(jstack0),3):
                        if (process_number==jstack0[i+1]): #extract jump history
                            jstack.append(int(jstack0[i]))
                    jtop = len(jstack) # 
                if mchange_flag.value==0: # global initialization
                    # initialize label stack for mode 1
                    with open("label_stack.txt",'r') as f:
                        lstack=f.read().split()
                    f.close()
                    ltop.value=len(lstack) # [yuen]
                    # initialize value stack for mode 1
                    with open("value_stack.txt",'r') as f:
                        rstack=f.read().split()
                    f.close()
                    rtop.value=len(rstack) # [yuen]
                    f.close()
                    mchange_flag.value=1        
                #backward exec
                if back_com[pc]==7:
                    command1='   label'
                elif back_com[pc]==21:
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
                s=re.search(r'\d(\.\d+)*',lstack[ltop.value-3+1]) # next process for lstack
                s2=re.search(r'\d(\.\d+)*',rstack[rtop.value-3+1]) # next process for rstack
                #check if the process number matches the process number on each value stack and label stack top in rjmp,restore.
                # check process number for restore and r_alloc with rstack and for rjmp with lstack
                if ((process_number==s2.group() and (back_com[pc]==22 or back_com[pc]==24))\
                     or (process_number==s.group() and back_com[pc]==21)\
                          or (back_com[pc]!=21 and back_com[pc]!=22 and back_com[pc]!=24))\
                               and my_terminate_flag==0:
                    with open("reverse_output.txt",'a') as f:
                        f.write("~~~~~~~~Process"+process_number+" backward execute~~~~~~(mode="+str(mode.value)+")~~\n")
                        f.write("path : "+process_path+"\n")
                        f.write("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(back_com[pc])+"    operand = "+str(back_opr[pc])+"\n")
                    print("~~~~~~~~Process "+process_number+" backward execute~~~~~~(mode="+str(mode.value)+")~~")
                    print("path : "+process_path)
                    print("pc = "+str(pc+1)+"("+str(count_pc-pc)+")   command = "+command1+":"+(str)(back_com[pc])+"    operand = "+str(back_opr[pc]))
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
#                   if my_endflag[0]!='':
#                        if my_endflag[flag_number]=='1' and back_com[pc]==23 and back_opr[pc]==1:
#                            my_terminate_flag=1
                    if back_com[pc]==21: #rjmp/label was from jump
                        if int(lstack[ltop.value-3+2])==1:
                            if process_number=='0':
                                print("Mode1: Process 0, jtop -1 at ltop=",ltop.value)
                            jtop = jtop - 1 # one jump reversed
                    if back_com[pc]==26: # r_fork
                        with open('a'+(str)(back_opr[pc])+'.txt',mode='r') as f:
                            tables=f.read()
                        t3=tables[0:0+4]
                        s3=re.search(r'\d+',t3)
                        if end==count_pc-int(s3.group())+1:
                            print("end_skip_flag set")
                            end_skip_flag=1
#[0320]                    print("pn:"+process_number+":jtop=",jtop," pc=",pc+1)
                    #execute each instructions
                    if p_turn.value == 1:
                      (pc,pre,stack,top,rtop,tablecount,process_path)=\
                        executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,\
                            pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,\
                                lock,process_number,process_path,count_pc,process_count,\
                                    terminate_flag,flag_number,mlock,mlock2,program_counter,\
                                    q,q2,q3,mode,mchange_flag,from_jump_flag,monitor_process_count,\
                                        now_process_count,process_back_ori_num,step_flag,jmp_flag,monitor_turn,p_turn,gjtop)
                      monitor_turn.value = 1 # pc changed
                      p_turn.value = 0
                    if back_com[pre]==26:
                        with open("reverse_output.txt",'a') as f:
                            f.write("---fork end--- (process "+process_number+")\n")
                        print("---fork end--- (process "+process_number+")")
                    with open("reverse_output.txt",'a') as f:
                        f.write("shared variable stack: "+str(value[0:tablecount.value])+"\n\n")
                    print("shared variable stack: "+str(value[0:tablecount.value])+"\n")
                    if back_com[pre]==27:
                        end_skip_flag=0
            elif mode.value==2 and recovered_statement_flag==0: # invert the abstract machine
                i=0
                while True:
                    if process_back_ori_num[pre+i]==process_back_ori_num[pre]: # slide pc till the next command
                        i=i+1
                    else:
                        break
                pc=count_pc-pre+i-2 # 
                if my_terminate_flag==1:
                    pc=pc-1
                recovered_statement_flag=1
                monitor_process_count.value=monitor_process_count.value+1 # confirm the process has been reversed
                pre_mode = 2 
                my_terminate_flag=0
                my_initflag = 0
                my_rstart_flag=0 # Now back to forward mode set once for forward execution
                mchange_flag.value=0 # globally reverse lstack and rstack
                monitor_turn.value = 1
                p_turn.value = 0
        #        print("process_number="+process_number+" jstack="+str(jstack)+" jtop="+str(jtop))
        ### mode =3 Execution ####
            elif mode.value==3: #
                if my_initflag==1: # initialization for jstack
                    my_initflag=0 # reset initflag
                    with open("jump_stack.txt",'r') as f:
                        jstack0=f.read().split()
                    f.close()
                    jstack=[]
                    for i in range(0,len(jstack0),3):
                        if (process_number==jstack0[i+1]):
                            jstack.append(int(jstack0[i]))
                    print("mode 3 (just before reset) jtop=",jtop," ltop=",ltop.value)
                    # jtop is at the top of jpc/jmp/return jump
                print("!!process:"+process_number+" jtop=",jtop," jstack=",jstack," pc=",pc," command=",command[pc]," operand=",opr[pc])
                #    if t1!=process_number: #  t1 is suspended
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
                if ltop.value < len(lstack): # no more branch
                    s=re.search(r'\d(\.\d+)*',lstack[ltop.value+1]) # next process for lstack
                else:
                    s=re.search(r'-1','-1') # impossible
                if rtop.value < len(rstack): # no more store
                    s2=re.search(r'\d(\.\d+)*',rstack[rtop.value+1]) # next process for rstack
                else:
                    s2=re.search(r'-1','-1') # impossible
                #print("process number="+process_number+" next process="+str(s2.group())+" pc="+str(pc)+":"+command1+" rtop="+str(rtop.value)+" rstack",rstack)
                #print("ltop=",ltop.value," lstack=",lstack)
                # match next process for store and jumps (jpc,jmp,return)
                print("rtop=",rtop.value," next process on rstack=",s2.group(),"ltop=",ltop.value," next process on lstack=",s.group())
            #    if (process_number==s2.group() and command[pc]==3)\
            #        or (process_number==s.group() and (command[pc]==4 or command[pc]==5 or command[pc]==12))\
            #            or (command[pc]!=3 and command[pc]!=4 and command[pc]!=5 and command[pc]!=12)\
            #                and my_terminate_flag==0:
                if (process_number==s2.group() and command[pc]==3)\
                    or (process_number==s.group() and (command[pc]==7))\
                        or (command[pc]!=3 and command[pc]!=7)\
                            and my_terminate_flag==0:

                    with open("output.txt",'a') as f:
                        f.write("~~~~~~~~Process"+process_number+" forward execute~~~~~~(mode="+str(mode.value)+")~~\n")
                        f.write("path : "+process_path+"\n")
                        f.write("pc = "+str(pc+1)+"   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"\n")
                    print("~~~~~~~~Process"+process_number+" forward execute~~~~~~(mode="+str(mode.value)+")~~")
                    print("path : "+process_path)
                    print("pc = "+str(pc+1)+" [line:"+str(process_back_ori_num[count_pc-pc-1])+"]   command = "+command1+":"+(str)(command[pc])+"    operand = "+str(opr[pc])+"")
                    step_flag.value=step_flag.value+1
                    jmp_flag = 0
                    if command[pc]==4 or command[pc]==5 or command[pc]==12:  # if jump, set stack top from jstack
                        print("jtop=",jtop," jstack=",jstack)
                        jmp_flag = jstack[jtop]
                        print("Mode3 jmp_flag=",jstack[jtop])
                        jtop = jtop + 1 # jtop points next available position (not pointing the top element!!)
                    #execute each instructions
                    if p_turn.value == 1:
                      (pc,pre,stack,top,rtop,tablecount,process_path)=executedcommand(stack,rstack,lstack,command,opr,back_com,back_opr,\
                        pc,pre,top,rtop,ltop,address,value,tablecount,variable_region,lock,\
                            process_number,process_path,count_pc,process_count,terminate_flag,flag_number,\
                                mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,from_jump_flag,\
                                    monitor_process_count,now_process_count,process_back_ori_num,step_flag,jmp_flag,monitor_turn,p_turn,gjtop)
                      monitor_turn.value = 1 # changed pc, next monitor_turn
                      p_turn.value = 0
                    if command[pre]==15: # all forked processes are terminated
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
                #    if command[pre]==8 and opr[pre]==1 and pc!=end: # par 1
                #        end=count_pc-start
                    path_record=process_path
                    recovered_statement_flag=0 # for next mode 2
                # --- end of mode 3 ---
            if my_nonfork_flag == 1:
            #if (command[pre]!=15 and (mode.value==0 or mode.value==3 or mode.value==4)) \
            #    or (back_com[pre]!=26 and mode.value==1) or mode.value==2: #and mode.value!=3 and mode.value!=4:
                my_nonfork_flag = 0
                mlock.release()
#0320           print("mlock.released in execution, mode=",mode.value)
            lock.release()
        ### end of one cycle ####
#            print("lock released pc=",pc," process_number=",process_number,\
#                " command[pre]=",command[pre]," back_com[pre]=",back_com[pre])
        #set terminate_flag to 1 when the process terminate.
        now_process_count.value=now_process_count.value-1
        terminate_flag[flag_number]=1 # mark the process is done
#        print("terminate execute "+str(flag_number))
    #return stack 
########################### execution end ###############################################       

###############################################################################################################################################
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
    gjtop = Value('i',0)
    program_counter = Value('i',0)
    endflag= manager.Array('i',range(100)) #{}
    for i in range(0,100,1):
        endflag[i]=0
    endflag0=Value('i',0)
    notlabelflag=0
    lock=Semaphore(1) #Lock()
    variable_region = []
    process_number='0'
    process_path='E'
    process_count = Value('i',0)
    process_table = []  # table for i-th process and name (not used yet)
    q = manager.Queue()
    q2 = manager.Queue()
    q3 = manager.Queue()
    terminate_flag = Array('i',100)
    mchange_flag = Value('i',0)
    for i in range(0,100,1):
        terminate_flag[i]=0
    exp_name = [] # expect decl number n out of dn
    exp_PC = [] # PC of the expects
    ens_name = [] # ensures decl number n out of dn
    ens_PC = [] # PC of the ensures
    exp_com = [[]*1 for i in range(10)] # expects command list
    ens_com = [[]*1 for i in range(10)] # ensures command list
    exp_opr = [[]*1 for i in range(10)] # expects operand list
    ens_opr = [[]*1 for i in range(10)] # ensures operand list
    exp_xpath = [[]] # location path for expects
    ens_xpath = [[]] # location path for ensures
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
    monitor_turn = Value('i',1)
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
    p_turn= Value('i',0)
    str4 = ""
    mode4_init = 0

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
        with open("reverse_output.txt",'w') as f:
            f.write("")
        f.close()
        with open("exp_error_process.txt",'w') as f:
            f.write("")
        f.close()
        with open("endflag.txt",'w') as f:
            f.write("")
        f.close()
        with open("jump_stack.txt",'w') as f:
            f.write("")
        f.close()
    k=0
    #read a bytecode
    coderead()
    for i in range(0,len(back_ori_num),1):
        process_back_ori_num[i]=back_ori_num[i]
    (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)\
        =read_contract_table(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
    #forward execution
    if args[2]=='df' or args[2]=='f':
        #################### Root Process Invocation ##################################
        process = Process(target=execution,args=(com,opr,back_com,back_opr,0,count_pc,count_pc,\
            stack,address,value,tablecount,rstack,lstack,rtop,ltop,gjtop,endflag0,variable_region,\
                lock,process_number,process_path,process_count,terminate_flag,0,\
                    mlock,mlock2,program_counter,q,q2,q3,mode,mchange_flag,monitor_process_count,
                    now_process_count,process_back_ori_num,step_flag,monitor_turn,p_turn,0))
        process_count.value=1
        process.start()
        ####################### Monitor ###################################
        while program_counter.value+1!=count_pc:
            if monitor_turn.value == 1:
                mlock.acquire()
                # Mode 0 forward
                if mode.value==0: # forward
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
                            print("[EXPECTS violated] expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1)+" execution suspends Process="+process_number)
                            str2=input("1:end monitor, enter:continue")
                            if str2=='1':
                                break
                            with open("exp_error_process.txt",'a') as f:
                                f.write(path_queue2+"\n")
                            f.close()
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
                            print("[ENSURES violated] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                            mode.value=1
                            back_ens_com=ens_com[con_number]
                            back_ens_opr=ens_opr[con_number]
                            back_xpath_process_path=xpath_process_path
                            back_my_flag_number=my_flag_number
                            ens_back_pc=program_counter.value
                            ens_error_check=0
                            print("Enter: change to backward mode\n1:quit")
                            str2=input(">")
                            if str2=='1':
                                break
                            monitor_process_count.value = 0
                            mchange_flag.value = 0
                            '''
                            if mchange_flag.value==0: # global initialization
                            # initialize label stack for mode 1
                                with open("label_stack.txt",'r') as f:
                                    lstack=f.read().split()
                                f.close()
                                ltop.value=len(lstack) # [yuen]
                            # initialize value stack for mode 1
                                with open("value_stack.txt",'r') as f:
                                    rstack=f.read().split()
                                f.close()
                                rtop.value=len(rstack) # [yuen]
                                f.close()
                                mchange_flag.value=1
                            '''
                # Mode 1 monitor ####
                elif mode.value==1: # backward
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
#[0320]                    print("mode 1 check exp_pc=",exp_PC,"pc(real)=",program_counter.value,"("+str(count_pc-program_counter.value)+")")
                    for check_PC in exp_PC:
#                        if ((count_pc-check_PC)==program_counter.value and mode4_flag==0):
                        if (count_pc-check_PC)==program_counter.value:
                            check_flag=1
                            con_number=i
                            print("expect check mode 1 pc(real)=",program_counter.value)
                        i=i+1
                    #if mode4_flag==1 and (count_pc-exp_err_pc)==program_counter.value:
                    #    mode4_flag=2
                    #if mode4_flag==2 and (count_pc-record_pc+1)==program_counter.value:
                    #    check_flag=1
                    #    mode4_flag=0
                    if check_flag==1:
                        print("[Reached EXPECTS] expects d"+str(ens_name[con_number])+" line:"+str(back_ori_num[error_pc]))
                        print("0:Backward more\n1:Step Forward - previous trace\n2:Auto Forward - previous trace\n3:Step forward\n4:Auto forward\n5:Load New contract")
                        str4=input(">")
                        if str4!='0':
                          mode.value=2
                elif mode.value==2:#change backward mode to forward step mode 
                    print("mode 2: monitor now_process_count=",now_process_count.value," monitor_process_count",monitor_process_count.value)
                    if now_process_count.value==monitor_process_count.value: # now_process_count = how many processes alive
                        print("ltop=",ltop.value)
                        # monitor_process_count = how many process has been inverted
                        # print("all process got back")
                    #    print("[Reached Expect] expects d"+str(ens_name[con_number])+" line:"+str(back_ori_num[error_pc]))
                    #    print("1:Step - previous trace\n2:Auto - previous trace\n3:Auto forward\n4:Load New contract")
                    #    str4=input()
                    #    str4=input("1:step mode 2:restrictive auto mode 3:non-restrictive auto mode 4:compile a program with new contract")
                        if str4=='5':
                            str5=input("Input file name with new contracts : ")
                            os.system('java Parser '+str5)
                            print("1:Step - previous trace\n2:Auto - previous trace\n3:Step Forward\n4:Auto Forward")
                            str4=input(">")
                        if str4=='1': # step mode 3
                            mode.value=3
                        elif str4=='2': # auto mode 3
                            mode.value=3
                        elif str4=='3': # step mode 4
                            mode4_init = 0
                            mode.value=4
                        elif str4=='4': # auto mode 4
                            mode4_init = 0
                            mode.value=4
                        for i in range(0,100,1):
                            endflag[i]=0
                        step_count=0
                        one_time_error_flag=0
#                        print(exp_xpath)
                    #    coderead_list_clear()
                    #    coderead()
                        for i in range(0,len(back_ori_num),1):
                            process_back_ori_num[i]=back_ori_num[i]
                        (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)=all_contract_list_clear(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
                        (exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)=read_contract_table(exp_name,exp_PC,ens_name,ens_PC,exp_com,exp_opr,ens_com,ens_opr,exp_xpath,ens_xpath)
                    #    print(exp_xpath)
                    #    str3=input()
                # Mode 3: monitor
                elif mode.value==3:#step forward mode
                    if True:#step_flag.value==2:
                        print("mode 3 monitor")
                        if not q.empty():
                            path_queue=q.get(block=False)
                        if not q2.empty():
                            path_queue2=q2.get(block=False)
                        if not q3.empty():
                            path_queue3=q3.get(block=False)
                        print("Mode 3:process_number=",path_queue2)
                        print("Mode 3:ltop=",ltop.value)
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
                            if check_PC==program_counter.value+1: #[yuen]
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            print("[Reached EXPECTS] expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1)+"pc(real)="+str(program_counter.value))
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in exp_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                            print("Enter:continue\n1:end monitor")
                            str2=input(">")
                            if str2=='1':
                                break
                        #ensures control
                        con_number=0
                        check_flag=0
                        i=0
                        # print("ens_PC",ens_PC," pc=",program_counter.value+1)
                        for check_PC in ens_PC:
                            if check_PC==program_counter.value: # [yuen]
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
#                            print("ensures check")
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in ens_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                                #print(monitor_stack)
                            if monitor_stack[-1]==0:
                                print("[ENSURES violated] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                                mode.value=1
                                mchange_flag.value=0
                                back_ens_com=ens_com[con_number]
                                back_ens_opr=ens_opr[con_number]
                                back_xpath_process_path=xpath_process_path
                                back_my_flag_number=my_flag_number
                                ens_back_pc=program_counter.value
                                ens_error_check=0
                                step_flag.value=0
                                monitor_process_count.value=0
                            #    print("rtop=",rtop.value," ltop=",ltop.value)
                                print("Enter:backward\n1:break")
                                str2=input(">")
                                if str2=='1':
                                    break
                                else: # backward again
                                    mode.value=1
                                    mchange_flag.value=0
                                    # recreate value_stack and label_stack upto rtop and ltop
                                    with open("value_stack.txt","r") as f:
                                        values = f.read().split()
                                    f.close()
                                    with open("value_stack.txt","w") as f:
                                        f.write("")
                                    f.close()
                                    with open("value_stack.txt","a") as f:
                                        for i in range(0,rtop.value,3):
                                            f.write(values[i]+" "+values[i+1]+" "+values[i+2]+'\n')
                                    f.close()
                                    with open("label_stack.txt","r") as f:
                                        labels = f.read().split()
                                    f.close()
                                    with open("label_stack.txt","w") as f:
                                        f.write("")
                                    f.close()
                                    with open("label_stack.txt","a") as f:
                                        for i in range(0,ltop.value,3):
                                            f.write(labels[i]+" "+labels[i+1]+" "+labels[i+2]+'\n')
                                    f.close()
                                    with open("jump_stack.txt","r") as f:
                                        jumps = f.read().split()
                                    f.close()
                                    with open("jump_stack.txt","w") as f:
                                        f.write("")
                                    f.close()
                                    with open("jump_stack.txt","a") as f:
                                        for i in range(0,gjtop.value,3):
                                            f.write(jumps[i]+" "+jumps[i+1]+" "+jumps[i+2]+'\n')
                                    f.close()
                                    step_flag.value=0 # reverse each processes
                                #    print("now_process_count=",now_process_count.value)
                                    monitor_process_count.value=0 # check if all processes are reversed
                                input("Mode 3 -> Mode 1")
                            #
                        if str4=='1': # step mode in mode 3
                            str5=input("Enter: next step")
                        step_count=step_count+1
                elif mode.value==4:
                    if mode4_init == 0: # initialize mode 4
                        mode4_init = 1
                    # recreate value_stack and label_stack upto rtop and ltop
                        with open("value_stack.txt","r") as f:
                            values = f.read().split()
                        f.close()
                        with open("value_stack.txt","w") as f:
                            f.write("")
                        f.close()
                        with open("value_stack.txt","a") as f:
                            for i in range(0,rtop.value,3):
                                f.write(values[i]+" "+values[i+1]+" "+values[i+2]+'\n')
                            f.close()
                        with open("label_stack.txt","r") as f:
                            labels = f.read().split()
                        f.close()
                        with open("label_stack.txt","w") as f:
                            f.write("")
                        f.close()
                        with open("label_stack.txt","a") as f:
                            for i in range(0,ltop.value,3):
                                f.write(labels[i]+" "+labels[i+1]+" "+labels[i+2]+'\n')
                        f.close()
                        with open("jump_stack.txt","r") as f:
                            jumps = f.read().split()
                        f.close()
                        with open("jump_stack.txt","w") as f:
                            f.write("")
                        f.close()
                        with open("jump_stack.txt","a") as f:
                            for i in range(0,gjtop.value,3):
                                f.write(jumps[i]+" "+jumps[i+1]+" "+jumps[i+2]+'\n')
                        f.close()
                    if True:# body of mode 4 monitor
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
                            if check_PC==program_counter.value: # [yuen]
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in exp_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,exp_com[con_number][i],exp_opr[con_number][i],xpath_rocess_path,terminate_flag[my_flag_number])
                                i=i+1
                            if monitor_stack[-1]==0:
                                exp_error_flag=1
                        if exp_error_flag==1:
                            if one_time_error_flag==0:
                                print("[EXPECTS violated] expects d"+str(exp_name[con_number])+" line:"+str(ori_num[exp_PC[con_number]]-1))
                                with open("exp_error_process.txt",'a') as f:
                                    f.write('{1}:{2}\n'.format(con_number,path_queue2))
                                #    f.write(path_queue2)
                                one_time_error_flag=1
                                error_exp_com=exp_com[con_number]
                                error_exp_opr=exp_opr[con_number]
                                error_xpath_process_path=xpath_process_path
                                error_my_flag_number=my_flag_number
                                mode4_flag=1
                                exp_err_pc=program_counter.value
                                endflag[my_flag_number]=1
                            #    with open("endflag.txt",'w') as f:
                            #        for i in range(0,100,1):
                            #            f.write(str(endflag[i])+",")
                            #if one_time_error_flag==1 and exp_err_pc!=program_counter.value:
                                record_pc=program_counter.value+1
                                one_time_error_flag=2
                            #    endflag[path_queue3]=1
                            #    with open("endflag.txt",'w') as f:
                            #        for i in range(0,100,1):
                            #            f.write(str(endflag[i])+",")
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
                            if check_PC==program_counter.value: # [yuen]
                                check_flag=1
                                con_number=i
                            i=i+1
                        if check_flag==1:
#                            print("ensures check")
                            (xpath_process_path,my_flag_number)=search_xpath(exp_xpath[con_number],xpath_table,xpath_process_number,path_queue2,xpath_flag_number)
                            monitor_top=0
                            i=0
                            for l in ens_com[con_number]:
                                (monitor_stack,monitor_top)=monitor_exec_command(monitor_stack,monitor_top,ens_com[con_number][i],ens_opr[con_number][i],xpath_process_path,terminate_flag[my_flag_number])
                                i=i+1
                            if monitor_stack[-1]==0:
                                print("[ENSURES violated] ensures d"+str(ens_name[con_number])+" line:"+str(ori_num[ens_PC[con_number]]-1))
                                mode.value=1
                                mchange_flag.value=0
                                back_ens_com=ens_com[con_number]
                                back_ens_opr=ens_opr[con_number]
                                back_xpath_process_path=xpath_process_path
                                back_my_flag_number=my_flag_number
                                ens_back_pc=program_counter.value
                                ens_error_check=0
                                step_flag.value=0
                                monitor_process_count.value=0
                        #    sys.exit()
                                print("1:Backward\n2:Break")
                                str2=input(">")
                                if str2=='2':
                                    for i in range(0,process_count.value,1):
                                        if terminate_flag[i]==0:
                                            terminate_flag[i]=1
                                    mlock.release()
                                    break
                                elif str2=='1':
                                    mode.value=1
                                    mchange_flag.value=0
                                    step_flag.value=0
                                    monitor_process_count.value=0
                            if str4=='4':
                                str6=input("Enter: next step")
                            step_count=step_count+1
                # mode selection end    
                monitor_turn.value = 0 # monitor has been executed
                p_turn.value = 1
                mlock.release()
        monitor_turn.value = 1
        process.kill()
    elif args[2]=='c':#convert forward bytecode to backward bytecode
        forward(com,opr,count_pc)
    
    elapsed_time = time.time()-start_time
    print("elapsed_time:{0}".format(elapsed_time) + "[sec]")
###############End of Monitor########################################################################

