package com.ibm.system.spectrum.computing.support;

import com.ibm.ecc.common.Config;
import com.ibm.ecc.common.ECCException;
import com.ibm.ecc.common.ECCExceptionIfc;
import com.ibm.ecc.common.ECCHeader;
import com.ibm.ecc.problemreportingservice.FileUploadCallbackIfc;
import com.ibm.ecc.problemreportingservice.ProblemReportContext;
import com.ibm.ecc.problemreportingservice.ProblemReportContextState;
import com.ibm.ecc.problemreportingservice.ProblemReportData;
import com.ibm.ecc.problemreportingservice.UnstructuredData;
import com.ibm.ecc.protocol.Address;
import com.ibm.ecc.protocol.Contact;
import com.ibm.ecc.protocol.DataType;
import com.ibm.ecc.protocol.Descriptor;
import com.ibm.ecc.protocol.Fault;
import com.ibm.ecc.protocol.FaultDetail;
import com.ibm.ecc.protocol.Identity;
import com.ibm.ecc.protocol.IdentityType;
import com.ibm.ecc.protocol.Telephone;
import com.ibm.ecc.protocol.problemreport.ProblemReportRichNotes;
import com.ibm.ecc.protocol.problemreport.ProblemType;
import com.ibm.ecc.protocol.problemreport.ServiceProviderReport;
import com.ibm.system.spectrum.computing.support.util.Option;
import com.ibm.system.spectrum.computing.support.util.PmrOperations;

import java.io.File;
import java.math.BigInteger;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;

import org.apache.commons.lang3.StringEscapeUtils;
import org.apache.log4j.Logger;



public class ProblemReport implements IEccService
{
  static String DESCRIPTOR = "ibm/problem.ecurep";
  static String[] files = new String[' '];
  final static Logger logger = Logger.getLogger(ProblemReport.class);
  final static PmrOperations PmrUtil = new PmrOperations();

  public ProblemReport() {}
  
  @Override  
  public void run(String[] args){
    /*
		 * S = ECC Service type. e.g. ProblemReport, patching, etc. Currently the default service is ProblemReport
		 * E = ECC HOME; libs for ecc client, e.g. c:\\ecchome\\eccRootDirectory 
		 * i = Component ID (IBM/*********); For test SYM = IBM/5725G8601; LSF = IBM/5725G8201
		 * v = Version (611, 71, 711, 911, 912, 913, etc.)
		 * I = Customer Number (Customer ICN); For test use DS12IEE; For IEPD, ICN must be an existed one and should match country code.
		 * u = UUID (UUID for the cluster instance, can use a pseduo one, e.g."1234567890")
		 * N = Customer Name; e.g. "John Smith"
		 * F = IDENTIFIER, GROUP_NAME or PRODUCT_CID. For test environment, use GROUP; SYM = "IBM/SPECTRUM_SYM" LSF = "IBM/SPECTRUM_LSF"
		 * p = Customer phone number; e.g. "9053161550"
		 * e = Customer email; e.g. "erikwang@ca.ibm.com"
		 * s = Severity; 1,2,3,4
		 * C = Country; For test only use "US" since it needs coordinate to customer record
		 * c = CITY; e.g. "New York"
		 * T = PMR Comment Line (title); e.g. "Symphony 7.1.1 {ACE} libraries"
		 * t = PMR Start line; e.g. "This is a test PMR, please ignore"
		 * U = A gzip file to be uploaded; e.g. "/scratch/supsym/erikwang/symclnt-lnx26-lib23-x64-6.1.1_build241698.tar.gz"
		 * r = PMR URI for append additional files to the PMR. The URI is generated when the PMR is created. Don't use if it is a new PMR creation
		 * d = debug flag; default = false
		 * V = Show hello message
		 * D = TESTMODE, won't call ecc API to create PMR
		 * P = Set Product ID (7 digits). This is required for backend process which migrate PMR to Salesforce case. This Parameter doesn't work with this commit. Need more info from ECC team
		 * f = Add a [CH] in PMR title to indentify it is a Call Home PMR
		 * 
		 * 
		 * Test example
		 * On Windows
		 * -E "C:\ecchome\\eccRootDirectory" 
		 * -i "IBM/5725G8601" 
		 * -v "711" 
		 * -I "0992394" 
		 * -u "1234567890" 
		 * -N "Erik Wang" 
		 * -F "IBM/SPECTRUM_COMPUTING" 
		 * -p "9053161550" 
		 * -s "3" 
		 * -C "CA" 
		 * -c "Markham" 
		 * -T "Call Home test PMR - From Windows server" 
		 * -t "This is a test PMR, submitted from a IDE environment on Winodws host" 
		 * -U "c:\\log.log" 
		 * -e "erikwang@ca.ibm.com"
		 * -r "https://esupport.ibm.com:443/eccedge/gateway/services/projects/ecc/iepd/services/ProblemReport?vSessionId=UNQ2016071520221819817" Note: Don't use it if it is a new PMR creation
		 * -d "true"
		 * -V ""
		 * -D "true"
		 * -S "ProblemReport" //Note: by default it is ProblemReport
		 * -P "5725Y38"
		 * 
		 * 
		 * Arguments string for Eclipse test
		 * -E "C:\\ecchome\\eccRootDirectory" -i "IBM/5725G8201" -v "913" -I "0992394" -u "test-cluster" -N "Erik Wang" -F "IBM/SPECTRUM_COMPUTING"  -p "9053161550" -s "3" -C "CA" -c "New York" -T "Call Home test PMR - From my new DEV environment on Windows" -t "This is a test PMR, submitted from a IDE environment on my new laptop Winodws host. Just to verify the environment is OK" -e "erikwang@ca.ibm.com" -d "false" -P "5725G82"
	  */
	  logger.info("ecc agent start...");
	try{
      
		Boolean DEBUGFLAG = Boolean.valueOf(false);
      
		String ECCHOME = null;
		String COMPONENT_ID = null;
		String PRODUCT_ID = null;
		String VERSION = null;
		String CUSTOMER_ICN = null;
		String UUID = null;
		String CUSTOMER_NAME = null;
      	String IDENTIFIER = null;
      	String CUSTOMER_PHONE = null;
      	String SERVERITY = null;
      	String COUNTRY = null;
      	String CITY = null;
      	String PMR_COMMENT_LINE = null;
      	String PMR_START_LINE = null;
      	String FILES_TO_UPLOAD = null;
      	String EMAIL = null;
      	String PMRURI = null;
      	boolean HELLOINFO = false;
      	boolean DEMOMODE = false;
      	boolean TITLEPREFIX = true;
      	List<Option> optsList = new ArrayList();
      
      for (int t = 0; t < args.length; t++) {
        switch (args[t].charAt(0)) {
        case '-': 
          if (args[t].length() < 2) {
            throw new IllegalArgumentException("Not a valid argument: " + args[t]);
          }
   
          if((args[t].equals("-V"))){
          		System.out.println("ECC agent - Implemented by Spectrum Computing Support @ IBM Canada, 2017");
          		System.exit(0);    		
          }else{
        	  if ((args.length - 1 == t)) {
                  throw new IllegalArgumentException("Expected arg after: " + args[t]);
                }

        	  optsList.add(new Option(args[t], args[(t + 1)]));
              //System.out.println("args = " + args[t] + ";  value = " + args[(t + 1)]);
              switch (args[t].charAt(1)) {
              case 'E': 
                ECCHOME = args[(t + 1)];
                break;
              case 'i': 
                COMPONENT_ID = args[(t + 1)];
                break;
              case 'v': 
                VERSION = args[(t + 1)];
                break;
              case 'I': 
                CUSTOMER_ICN = args[(t + 1)];
                break;
              case 'u': 
                UUID = args[(t + 1)];
                break;
              case 'F': 
                IDENTIFIER = args[(t + 1)];
                break;
              case 'p': 
                CUSTOMER_PHONE = args[(t + 1)];
                break;
              case 's': 
                SERVERITY = args[(t + 1)];
                break;
              case 'N': 
                CUSTOMER_NAME = args[(t + 1)];
                break;
              case 'C': 
                COUNTRY = args[(t + 1)];
                break;
              case 'c': 
                CITY = args[(t + 1)];
                break;
              case 'T': 
                PMR_COMMENT_LINE = StringEscapeUtils.unescapeJava(args[(t + 1)]);
                break;
              case 't': 
                PMR_START_LINE = args[(t + 1)];
                break;
              case 'U': 
                FILES_TO_UPLOAD = args[(t + 1)];
                files = FILES_TO_UPLOAD.split(";");
                break;
              case 'e': 
                EMAIL = args[(t + 1)];
                break;
              case 'r': 
                PMRURI = args[(t + 1)];
                break;
              case 'd': 
                DEBUGFLAG = new Boolean(args[t + 1]);
                break;
              case 'P':
            	PRODUCT_ID = args[(t + 1)];
            	break;
              case 'V': 
                  HELLOINFO = new Boolean(true);
                  break;
              case 'D': 
                  DEMOMODE = new Boolean(true);
                  break;   
              case 'Z': 
                System.exit(99);
                break;
              case 'f':
            	  TITLEPREFIX = new Boolean(args[t + 1]);
            	  break;
              case 'S':
            	  break;
              default:
            	  System.out.println("Not a recognized argument "+ args[t]);
            	  logger.info("Not a recognized argument "+ args[t]+", ecc agent exits as 98");
            	  System.exit(98);
              }
              t++; 
          }
        }     
      }
      
      File ECC_ROOT_DIRECTORY = new File(ECCHOME);
      if (DEBUGFLAG.booleanValue()) {
        showConf(args);
      }
      
      //Indicate ECC call home version
      ECCHeader.setCallhomeVersion(2);
      
      //Set ecc root directory
      Config.setRootDataDirectory(ECC_ROOT_DIRECTORY);

      Identity subject = new Identity();
      subject.setType(IdentityType.software);

      //Set production id need to test further, by 4th/Oct/17 it doesn't work
      //subject.setProduct(PRODUCT_ID);
      
      subject.setProduct(COMPONENT_ID);
      subject.setVersion(VERSION);
      
      String[] customerNumber = new String[1];
      customerNumber[0] = CUSTOMER_ICN;
      subject.setCustomerNumber(customerNumber);
      subject.setUuid(UUID);
      subject.setCountry(COUNTRY);
      

      Identity submitter = new Identity();
      submitter.setType(IdentityType.software);
      submitter.setProduct(COMPONENT_ID);

      //Set production id need to test further, by 4th/Oct/17 it doesn't work
      //submitter.setProduct(PRODUCT_ID);
      
      submitter.setUuid(UUID);
      submitter.setName(CUSTOMER_NAME);
      

      Identity envGroup = new Identity();
      envGroup.setType(IdentityType.group);
      envGroup.setProduct(IDENTIFIER);
      

      Contact[] contacts = new Contact[1];
      Contact contact = new Contact();
      contacts[0] = contact;
      contact.setName(CUSTOMER_NAME);
      Telephone[] telephones = new Telephone[1];
      Telephone telephone = new Telephone();
      telephone.setNumber(CUSTOMER_PHONE);
      telephones[0] = telephone;
      contact.setVoice(telephones);
      
      String[] emails = new String[1];
      emails[0] = EMAIL;
      contact.setEmail(emails);
  
      Identity envHardware = new Identity();
      envHardware.setType(IdentityType.hardware);
      
      //For some reasons, even for SW, IEPD require a Hardware Product and SerialNumber, therefore we put fake code here.
      //This may need further follow up with IEPD team. But so far don't see any problem in PMR creation.
      envHardware.setProduct("IBM/UNKW/DSW");
      envHardware.setSerialNumber("8008800");
      

      //Required by IEPD
      Identity[] envs = new Identity[2];
      envs[0] = envGroup;
      envs[1] = envHardware;
      ProblemType[] problemTypes = new ProblemType[1];
      problemTypes[0] = ProblemType.errorIndication;
      
      //Prepare a Problem Report Context object
      ProblemReportContext prc = null;
      

      if (PMRURI != null) {
        prc = new ProblemReportContext(PMRURI, null, null, null);
        System.out.println("uri = " + prc.getProblemReportURI());
      }else{
        prc = new ProblemReportContext();
        prc.setSubject(subject);
        

        Address address = new Address();
        address.setCountry(COUNTRY);

        prc.setSubjectLocation(address);

        prc.setSubjectEnvironment(envs);

        prc.setProblemType(problemTypes);
        prc.setSeverity(new BigInteger(SERVERITY));
        
        ProblemReportRichNotes[] prrns = new ProblemReportRichNotes[1];
        ProblemReportRichNotes prrn = new ProblemReportRichNotes();
        prrn.setCategory("Normal");
        prrn.setNotes(PMR_START_LINE);
        prrns[0] = prrn;
        
        prc.setProblemReportRichNotes(prrns);
        prc.setSubmitter(submitter);
        prc.setContact(contacts);
        
        //To handle -f
        if(TITLEPREFIX){
        	PMR_COMMENT_LINE = "[CH] " + PMR_COMMENT_LINE;
        }
        prc.setProblemDescription(PMR_COMMENT_LINE);
        prc.setTest(new Boolean(true));
      }
  
      if (PMRURI == null) {
        //Start to submit the problem and trigger a PMR
    	
    	//Say Hello is -V is an argument
    	if(HELLOINFO){
    		System.out.println("ECC agent - Implemented by Spectrum Computing Support @ IBM Canada, 2017");
    		logger.info("A TESTMODE request has been received. ecc agent won't create PMR");
    		System.exit(0);    		
    	}
    	
    	logger.info("ecc agent will create a PMR");
        logger.info("<ECCHOME> "+ECCHOME+
        				" <COMPONENT_ID>"+COMPONENT_ID+
        				" <VERSION>"+VERSION+
        				" <CUSTOMER_ICN>"+CUSTOMER_ICN+
        				" <UUID>"+UUID+
        				" <CUSTOMER_NAME>"+CUSTOMER_NAME+
        				" <IDENTIFIER>"+IDENTIFIER+
        				" <CUSTOMER_PHONE>"+CUSTOMER_PHONE+
        				" <SERVERITY>"+SERVERITY+
        				" <COUNTRY>"+COUNTRY+
        				" <CITY>"+CITY+
        				" <PMR_COMMENT_LINE>"+PMR_COMMENT_LINE+
        				" <PMR_START_LINE>"+PMR_START_LINE+
        				" <FILES_TO_UPLOAD>"+FILES_TO_UPLOAD+
        				" <EMAIL>"+EMAIL+
        				" <PMRURI>"+PMRURI+
        				" <HELLOINFO>"+HELLOINFO+
        				" <DEMOMODE>"+DEMOMODE
        );

        if(DEMOMODE){
        	logger.info("DEMO MODE is true, exit as 97");
    		System.exit(97);    
        }
        
        //Submit PMR
        ProblemReportContextState status = prc.getContextState();
        prc.submitReport();	
               
       	printProgress(prc);
        
        if (status == ProblemReportContextState.error) {
            printExceptionsAndExit(prc);
        }
      
        //For append file to the created PMR, print to stdout for Checks
        System.out.println("uri = " + prc.getProblemReportURI());
        
        //Get response from IEPD
        try {
        	ServiceProviderReport[] spr_array = prc.getServiceProviderReport();
        	if ((spr_array != null) && (spr_array.length != 0)) {
            System.out.println("PMR ID = " + PmrUtil.parsePMRNumer(spr_array[0].getId()));
            logger.info("PMR ID = " + PmrUtil.parsePMRNumer(spr_array[0].getId()));
          }
        }catch (Exception e) {
            e.printStackTrace();
            //Exit code 4 = exceptions from retrieve response from IEPD 
            System.exit(4);
        }
      }//End of create a new PMR, next to upload file
        
      if (DEBUGFLAG.booleanValue()) {
        	printProgress(prc);
      }


      //Start to upload files to PMR
      if ((files.length >= 1) && (FILES_TO_UPLOAD != null)) {
    	  logger.debug("FILES_TO_UPLOAD = "+FILES_TO_UPLOAD+". Total ["+files.length+"] files to be uploaded");
    	  for (int t = 0; t < files.length; t++) {
    		  //Call back object
    		  PlatformSymphony ps = new PlatformSymphony();

	          //Start to upload attachment to ecurep 
	          logger.info("Ready to call prc.attach for file "+files[t]);
	          
	          if (DEBUGFLAG.booleanValue()){
	              logger.debug("Ready to call prc.attach for file "+files[t]);  
	          }
          
	          try{
	        	  prc.attach(createTier3Data(ps, 60000000L, files[t], COMPONENT_ID, VERSION)); 
	          }catch(Exception e){
	        	  e.printStackTrace();
	              //Exit code 5 = Failed to attach uploaded files to ProblemReportContent
	        	  System.out.println("Failed to attach file: " + FILES_TO_UPLOAD);
	        	  logger.info("Failed to attach file " + files[t]);
	              System.exit(5);
	          }

	          printProgress(prc);
               
	       	  if (DEBUGFLAG.booleanValue()){
	       		 logger.info("Ready to call prc.refresh for file "+files[t]);
	       	  }
	       	  //Required by ecc API
	       	  prc.refresh();
	       	  if (DEBUGFLAG.booleanValue()){
	       		  logger.info("Finish calling prc.refresh for file "+files[t]);
	       	  }
	       	  printProgress(prc);
        }
      }
    }
    catch (ECCException ex) {
    	System.out.println("PMR creatation failed. Cause is "+ex.getCause()+" ECCMessge.getId ="+ex.getECCMessage().getId());
    }
 }
  
  public static ProblemReportData createTier3Data(FileUploadCallbackIfc obj) {
    return createTier3Data(obj, 1234L, null, null, null);
  }
  
  public static ProblemReportData createTier3Data(FileUploadCallbackIfc obj, long size, String file2upload, String product, String version) {
    //Currently there is no size limit for uploading  
	Identity author = new Identity();
    author.setProduct(product);
    author.setVersion(version);
    author.setPlatform("Linux/Unix");
    
    File test_file = new File(file2upload);
    UnstructuredData ud = new UnstructuredData(test_file);
    ProblemReportData prd = null;
    Descriptor descriptor = new Descriptor();
    
    descriptor.set_value(DESCRIPTOR);
    
    DataType dataType = new DataType();
    dataType.set_value("text file");
    
    try{
      prd = new ProblemReportData(ud, ud.toString(), descriptor, dataType, ud.toString(), obj);
    } catch (ECCException ex) {
      System.out.println(ex.toString());
      System.exit(2);
    }
    
    ProblemReportRichNotes[] prrn = new ProblemReportRichNotes[1];
    prrn[0] = new ProblemReportRichNotes();
    prrn[0].setDateTime(Calendar.getInstance());
    prrn[0].setAuthor(author);
    
    prd.setProblemReportRichNotes(prrn);
    return prd;
  }
  
  public static void printProgress(ProblemReportContext prc){
	  ProblemReportContextState status = prc.getContextState();
	  System.out.println("Reporting status is " + status);
	  logger.debug("Reporting Status is " + status);
    		
	  if (status == ProblemReportContextState.processing) {
		  ServiceProviderReport[] spr_array = prc.getServiceProviderReport();
		  spr_array = prc.getServiceProviderReport();
		  if ((spr_array != null) && (spr_array.length != 0)) {
			  System.out.println("srid = " + spr_array[0].getId());
		  }
	  }else if (status == ProblemReportContextState.error) {
		  printExceptionsAndExit(prc);
	  }
  }
  
  public static void printExceptions(ProblemReportContext prc){
	  ECCExceptionIfc[] exception_array = prc.getExceptions();
	  if (exception_array != null) {
		  for (int i = 0; i < exception_array.length; i++) {
			  System.out.println("Exception[" + i + "][" + exception_array[i] + "]");
			  Throwable t = getCause(exception_array[i]);
			  if (t != null) {
				  System.out.println("Cause[" + i + "][" + t + "]");
				  if ((t instanceof Fault)) printFault((Fault)t); else
					  t.printStackTrace();
			  }
		  }
	  }
  }
  
  public static void printExceptionsAndExit(ProblemReportContext prc){
	  ECCExceptionIfc[] exception_array = prc.getExceptions();
	  if (exception_array != null) {
		  for (int i = 0; i < exception_array.length; i++) {
			  System.out.println("Exception[[" + i + "]][" + exception_array[i] + "]");
			  Throwable t = getCause(exception_array[i]);
			  if (t != null) {
				  System.out.println("Cause[[" + i + "]][" + t + "]");
				  if ((t instanceof Fault)) printFaultAndExit((Fault)t); else
					  t.printStackTrace();
			  }
		  }
	  }
  }
  
  public static void printFault(Fault f) {
    if (f == null) return;
    System.out.println("Subcode = " + f.getSubcode());
    System.out.println("Description = " + f.getDescription());
    printFaultDetail(f.getDetail());
  }
  
  public static void printFaultAndExit(Fault f) {
	  if (f == null) return;
	  System.out.println("Subcode = " + f.getSubcode());
	  System.out.println("Description = " + f.getDescription());
	    
	  switch(f.getSubcode()){
	  	case ("7301"):
			//Duplicated PMR
			//This request was detected as a Duplicate and determined not to create a new service request.
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 100");
			System.exit(100);
		case ("1120"):
			//Insufficient authority for the credentials Entity ID [XXX].  It does not match any of the ids in the Acl list.  Subsequent transaction [attach] is not allowed.
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 101");
			System.exit(101);
		case ("4454"):
			//Existed file name in ecurep for this PMR.
			//The request Attachment already exists in Session Attachment for vSessionId:[xxx] and thisURI:[FILE_TO_UPLOAD].
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 102");
			System.exit(102);
		case ("0552"):
			//RETAIN Customer Record NOT FOUND for Customer: [xxxx] and RETAIN CountryCode: [XX].
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 103");
			System.exit(103);
		case ("1020"):
			//RThe field: [customer number] in object: [Subject] contains invalid value: [] 
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 104");
			System.exit(104);
		case ("1022"):
			//Invalid object : [Subject]. Reason:[Required version field is missing]
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 105");
			System.exit(105);
		case ("1010"):
			//The required field: [country] in object: [SubjectLocation] is MISSING
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], ECC agent will exit as 106");
			System.exit(106);
		default:
			logger.debug("ECC agent caught Subcode["+f.getSubcode()+"] with cause["+f.getDescription()+"], but it doesn't match any known issue. ECC agent will exit as 200");
			System.exit(200);
	}
  }
  
  
  public static void printFaultDetail(FaultDetail fd) {
    if (fd == null) return;
    printCal("DateTime = ", fd.getDateTime());
    printStringArray("FaultDetail", fd.getExtendedData());
    printFault(fd.getNestedFault());
    System.out.println("TransactionId = " + fd.getTransactionId());
  }
  
  public static void printCal(String label, Calendar cal){
    if (cal == null) { return; }
    	DateFormat format = new SimpleDateFormat("MM/dd/yyyy kk:mm:ss z");
    	String time_string = format.format(cal.getTime());
    	System.out.println(label + time_string);
  }
  
  public static void printStringArray(String label, String[] sa) {
    if (sa == null) return;
    for (int i = 0; i < sa.length; i++)
      System.out.println(label + "[" + i + "] = " + sa[i]);
  }
  
  public static Throwable getCause(ECCExceptionIfc exception) {
    Throwable t = null;
    try {
      t = exception.toThrowable();
    } catch (NoSuchMethodError ex) {
      System.out.println("toThrowable function not available");
      System.exit(3);
      return null;
    }
    return t.getCause();
  }
  
  public static void showConf(String[] args) {
    System.out.println("[DEBUG] List args:");
    	for (int t = 0; t < args.length; t++) {
    		System.out.println("[DEBUG] args[" + t + "] = " + args[t]);
    	}
  }
  
  public String[] getFilesToUpload(String longString, String regex){
    return longString.split(regex);
  }


@Override
public void initialize() {
	// TODO Auto-generated method stub
	
}

@Override
public String serviceDescription() {
	// TODO Auto-generated method stub
	return null;
}
}