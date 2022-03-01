# Debugging details

1. First a pair of expects and ensures is inserted to see 'seats' >=0

```C
    begin b1
        var seats;
        var agent1;
        var agent2;
        proc p1 airline() is
            par a1
                begin b2
                    while (agent1==1) do
                        if (seats>0) then
                            seats=seats-1
                        else
                            agent1=0
                        fi
                    od
                end
            ||     
                begin b3
                    while (agent2==1) do
                        if (seats>0) then
                            seats=seats-1
                        else   
                            agent2=0
                        fi
                    od
                end
            rap
        end
        seats=3;
        agent1=1;
        agent2=1;
        [[expects d1 SELF true *]]
        call c1 airline()
        [[ensures d1 SELF (seats>-1) *]]
        remove agent2;
        remove agent1;
        remove seats;
    end
```

2. When ensure is violated, go back to expects d1 and update the contracts to check if the violation happens
either in b2 and b3

``` C
begin b1
    var seats;
    var agent1;
    var agent2;
    proc p1 airline() is
        par a1
            begin b2
            [[expects d2 SELF true *]]
                while (agent1==1) do
                    if (seats>0) then
                        seats=seats-1
                    else
                        agent1=0
                    fi
                od
            [[ensures d2 SELF (seats>-1) *]]
            end
        ||     
            begin b3
            [[expects d3 SELF true *]]
                while (agent2==1) do
                    if (seats>0) then
                        seats=seats-1
                    else   
                        agent2=0
                    fi
                od
            [[ensures d3 SELF (seats>-1) *]]
            end
        rap
    end
    seats=3;
    agent1=1;
    agent2=1;
    [[expects d1 SELF true *]]
    call c1 airline()
    [[ensures d1 SELF (seats>-1) *]]
    remove agent2;
    remove agent1;
    remove seats;
end
```

3. Let ensure d2 be violated.   Go back to expects d2.
Once reaches d2, agent1 = 0 and seats is still negative.
Go backwards again and stop at d2 where agent1=1.
Update the contract to see if the illegal update happens in b2.

```C
begin b1
    var seats;
    var agent1;
    var agent2;
    proc p1 airline() is
        par a1
            begin b2
            [[expects d2 SELF true *]]
                while (agent1==1) do
                    [[expects d4 SELF true *]]
                    if (seats>0) then
                        seats=seats-1
                        [[ensures d4 SELF seats >-1 *]]
                    else
                        agent1=0
                    fi
                od
            [[ensures d2 SELF (seats>-1) *]]
            end
        ||     
            begin b3
            [[expects d3 SELF true *]]
                while (agent2==1) do
                    if (seats>0) then
                        seats=seats-1
                    else   
                        agent2=0
                    fi
                od
            [[ensures d3 SELF (seats>-1) *]]
            end
        rap
    end
    seats=3;
    agent1=1;
    agent2=1;
    [[expects d1 SELF true *]]
    call c1 airline()
    [[ensures d1 SELF (seats>-1) *]]
    remove agent2;
    remove agent1;
    remove seats;
end
```

4. Add expects d4 and ensure d4.
Trace forward the previous backward execution.  If ensures d4 is violated,
go backwards till expects d4.   Or, it may reaches d2.  Then, go backwards
again to d2 twice.  Update to add [[expects d5 SELF true *]] and 
[[ensures d5 SELF seats > -1 *]] as follows.

```C
begin b1
    var seats;
    var agent1;
    var agent2;
    proc p1 airline() is
        par a1
            begin b2
            [[expects d2 SELF true *]]
                while (agent1==1) do
                    [[expects d4 SELF true *]]
                    if (seats>0) then
                        seats=seats-1
                        [[ensures d4 SELF seats >-1 *]]
                    else
                        agent1=0
                    fi
                od
            [[ensures d2 SELF (seats>-1) *]]
            end
        ||     
            begin b3
            [[expects d3 SELF true *]]
                while (agent2==1) do
                    [[expects d5 SELF true *]]
                    if (seats>0) then
                        seats=seats-1
                        [[ensure d5 SELF seats >-1 *]]
                    else   
                        agent2=0
                    fi
                od
            [[ensures d3 SELF (seats>-1) *]]
            end
        rap
    end
    seats=3;
    agent1=1;
    agent2=1;
    [[expects d1 SELF true *]]
    call c1 airline()
    [[ensures d1 SELF (seats>-1) *]]
    remove agent2;
    remove agent1;
    remove seats;
end
```



4'. Or, at step 3 above, b2 waits till b3 is terminated.  No ensures will be violated.

```C
begin b1
    var seats;
    var agent1;
    var agent2;
    proc p1 airline() is
        par a1
            begin b2
            [[expects d2 SELF true *]]
                while (agent1==1) do
                    [[expects d4 FOLLOW true TERMINATED]]
                    if (seats>0) then
                        seats=seats-1
                        [[ensures d4 SELF seats >-1 *]]
                    else
                        agent1=0
                    fi
                od
            [[ensures d2 SELF (seats>-1) *]]
            end
        ||     
            begin b3
            [[expects d3 SELF true *]]
                while (agent2==1) do
                    if (seats>0) then
                        seats=seats-1
                    else   
                        agent2=0
                    fi
                od
            [[ensures d3 SELF (seats>-1) *]]
            end
        rap
    end
    seats=3;
    agent1=1;
    agent2=1;
    [[expects d1 SELF true *]]
    call c1 airline()
    [[ensures d1 SELF (seats>-1) *]]
    remove agent2;
    remove agent1;
    remove seats;
end
```
