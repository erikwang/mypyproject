package com.ibm.system.spectrum.computing.support;
import com.ibm.ecc.problemreportingservice.FileUploadCallbackIfc;
import com.ibm.ecc.problemreportingservice.ProblemReportData;
import com.ibm.ecc.problemreportingservice.ProblemReportFormIfc;


public class PlatformSymphony implements ProblemReportFormIfc, FileUploadCallbackIfc {

	@Override
	public String getSerialization() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public String toXML() {
		// TODO Auto-generated method stub
		return null;
	}

	@Override
	public void uploadFailure(ProblemReportData arg0) {
		// TODO Auto-generated method stub
		System.out.println("Upload callback - Failed to upload a file");
	}

	@Override
	public void uploadSuccess(ProblemReportData arg0) {
		// TODO Auto-generated method stub
		System.out.println("Upload callback- File "+arg0.getThisURI()+" has been uploaded");
	}
}