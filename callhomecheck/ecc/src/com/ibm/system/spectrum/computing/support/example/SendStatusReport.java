package com.ibm.system.spectrum.computing.support.example;
import java.io.File;
import java.util.Calendar;
import com.ibm.ecc.common.Config;
import com.ibm.ecc.common.ECCException;
import com.ibm.ecc.common.ExtendedAttribute;
import com.ibm.ecc.protocol.DataPortPreference;
import com.ibm.ecc.protocol.Identity;
import com.ibm.ecc.protocol.URITypePreference;
import com.ibm.ecc.statusservice.StatusReportContext;
import com.ibm.ecc.statusservice.StatusReportData;

public class SendStatusReport {
	
	final static String ROOTDIR = new String("c:\\ecchome\\eccRootDirectory");
	
	// use the ECC test descriptor
	final static String ECCDESCRIPTOR = new String("data/ibm.eccedge.indirect+direct.uritype");
	
	public static void main(String[] args)
	{
		try
		{
			// setup root directory and create the Context
			System.out.println("Start SendStatusReport....");
			
			File dir = new File(ROOTDIR);
			Config.setRootDataDirectory(dir);
			
			// Create the file to upload
			String filename = "TESTFILE-" + Calendar.getInstance().getTimeInMillis() + ".txt";
			File testFile = new File(ROOTDIR + "/" + filename);
			System.out.println("File name: "+filename);
			
			// Create the data and write to the file and set descriptor
			StatusReportData data = new StatusReportData(testFile, "Test Type");			
			String data1 = "IBM Platform Computing ECC agent test - erikwang@ca.ibm.com @ today123";
			data.storeData(data1.getBytes("UTF8"), "Test Format");
    		data.setDescriptor(ECCDESCRIPTOR);
    		
			
    		// Create extended attributes defining file and machine information
			/*
    		ExtendedAttribute ap1 = new ExtendedAttribute("Filename", filename);
			ExtendedAttribute ap2 = new ExtendedAttribute("Geography", "NA");		// NA,LA = testcase. EMA,AP = ecurep
			ExtendedAttribute ap3 = new ExtendedAttribute("Machine Type", "1234");
			ExtendedAttribute ap4 = new ExtendedAttribute("Model", "3222");
			ExtendedAttribute ap5 = new ExtendedAttribute("SerialNumber", "E9A9CCC");
			//data will be in HW:/ecurep/hw/1/1234/E9/A9/E9A9CCC/2016-xxxxxx/*
			*/
    		
    		
    		ExtendedAttribute ap1 = new ExtendedAttribute("Filename", filename);
            ExtendedAttribute ap2 = new ExtendedAttribute("Component", "5725G8602");
            ExtendedAttribute ap3 = new ExtendedAttribute("Version", "710");
            ExtendedAttribute ap4 = new ExtendedAttribute("countryCode", "CA");
            ExtendedAttribute ap5 = new ExtendedAttribute("Division", "05");
            ExtendedAttribute ap6 = new ExtendedAttribute("PID", "5725G86");

			data.setExtendedAttributes(new ExtendedAttribute[] { ap1,ap2,ap3,ap4,ap5,ap6 } );
			//data.setExtendedAttributes(new ExtendedAttribute[] {ap1,ap2,ap3,ap4,ap5} );
			
			// Now build the Status Report Context
			StatusReportContext src = new StatusReportContext();
		
			// set data into context and create the subject
			src.setStatusReportData(new StatusReportData[] { data } );
			Identity subject = new Identity();
			subject.setName("Erik's Test subject name");
			//subject.setSerialNumber("R9K0MHY");
			//subject.setSerialNumber("FF99FFF");
		    //subject.setProduct("LENOVO/4282/A34");
			//subject.setProduct("APPALE/IPHONE/7");
			src.setSubject(subject);
			
			// use the Edge server for file uploads
			DataPortPreference dpp = new DataPortPreference();
			dpp.setDataURIType(URITypePreference.indirect);
			src.setDataPortPreference(dpp);	
			
			try
			{				
				src.submit();
				System.out.println("Transaction id: "+src.getLastTransactionId());
				
				String state = src.getState().getValue();
				long processTime = src.getEstimatedTimeToProcess();
				System.out.println("Context state: "+state);
				System.out.println("Process time: "+processTime);
				System.out.println("Data state: "+src.getStatusReportData()[0].getState().getValue());
				if (src.getStatusReportData()[0].getDataPortUsedForUpload() != null)
					System.out.println("Upload URI: "+src.getStatusReportData()[0].getDataPortUsedForUpload().getDataURI());
				
				// loop until processing is complete
				while (0 != processTime)
				{
					Thread.sleep(5000);
					src.refresh();
					System.out.println("Refresh complete.");
					System.out.println(src.getLastTransactionId());
					state = src.getState().getValue();
					processTime = src.getEstimatedTimeToProcess();
					System.out.println(state);
					System.out.println(processTime);
					System.out.println(src.getStatusReportData()[0].getState().getValue());
				}

				src.close();
				System.out.println("Transaction id: "+src.getLastTransactionId());
				state = src.getState().getValue();
				processTime = src.getEstimatedTimeToProcess();
				System.out.println("Context state: "+state);
				System.out.println("Process time: "+processTime);
				System.out.println("Data state: "+src.getStatusReportData()[0].getState().getValue());				
			}
			catch (ECCException ecce)
			{
				System.out.println("Submit failed.");
				ecce.printStackTrace(System.out);
				System.out.println(src.getLastTransactionId());
			}

			System.out.println("End SendStatusReport....");
		}
		catch (Exception e)
		{
			e.printStackTrace(System.out);
		}
	}
	
}

