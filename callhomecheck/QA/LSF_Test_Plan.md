Testing setup			 
					
TestID 	Test Case 	          Expected Result 	Result 	Related Comment	

1	Start CallHome Agent                   				

2	Check Python Version as root.				

					
					
Testing functionality	
====================================================================
TestID:1

Test Case:Check master LIM down  	 

Expected Result:Agent Alert lim down

====================================================================

TestID:2

Test Case:Check mbatchd down

Test Method: kill -STOP/CONT <pid>

Expected Result:Agent report mbatchd down


====================================================================


TestID:3

Test Case:Check mbschd performance 

Expected Result:Agent Alert lim down

====================================================================


TestID:4

Test Case:Check SBATCHD performance  	 

Expected Result:Agent Alert lim down


====================================================================

TestID:5

Test Case:Check LSB_SHAREDIR  	 

Expected Result:WARN:5000, ALERT:1000

====================================================================

TestID:6

Test Case:Check /tmp   

Expected Result:WARN:5000, ALERT:1000

====================================================================

TestID:7

Test Case:Check BLACKHOLE 	

Expected Result:File Name: 'alert_*' 	

====================================================================

TestID:8

Test Case: Check CUSTOM

Expected Result:Determine by command exit code	

Sample Defination: clustercheck.conf

       ===============
[[[[CUSTOM]]]]
           [[[[[TEST_SCRIPT]]]]]
                  ENABLED=Y                                  
                  NAME="test script"                         
                  FAIL_LIMIT=1
                  RETRY_IMMEDIATELY=Y  
                  TIMEOUT=30
                  COMMAND=exit -1
                  SUCCESS_EXIT_CODES=0                    


====================================================================

TestID:9

Test Case:Check Command line PMR createtion

Expected Result:Command provided script could generate Alert.	

Sample Command: <CALL_HOME_TOP>CallHomePMR.sample


