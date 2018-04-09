package com.ibm.system.spectrum.computing.support.util;

public class PmrOperations {

	//Parse PMR format, add comma in the string
	  public String parsePMRNumer(String _PMR) throws Exception {
	    String formatPMR = "";
	    if (_PMR.length() != 11) {
	      throw new Exception();
	    }
	    String first5digit = _PMR.substring(0, 5);
	    String mid3digit = _PMR.substring(5, 8);
	    String last3digit = _PMR.substring(8, 11);
	    formatPMR = first5digit + "," + mid3digit + "," + last3digit;
	    
	    return formatPMR;
	  }
	
}
