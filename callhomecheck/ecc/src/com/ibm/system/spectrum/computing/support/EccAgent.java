package com.ibm.system.spectrum.computing.support;

import java.util.ArrayList;
import java.util.List;

import com.ibm.system.spectrum.computing.support.util.Option;

public class EccAgent {
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		System.out.println("Welcome to Ecc Agent for IBM Spectrum Computing Support team");
		
		String EccService = null;
		EccService  = getEccService(args);
		 
		if (EccService == null){
			EccService = "ProblemReport";
		}
		switch(EccService){
		 	case "ProblemReport":
		 		ProblemReport myProblemReport = new ProblemReport();
		 		myProblemReport.run(args);
		 		break;
		 	default:
		 		System.out.println("Unknow Ecc service, please verify argument -S");
		 		System.exit(97);
		 	}
	}
	
//To get ECC service type:
	public static String getEccService(String args[]){
		String EccService = null;
		List<Option> optsList = new ArrayList(); 
		for (int t = 0; t < args.length; t++) {
		        switch (args[t].charAt(0)) {
		        case '-': 
		          if (args[t].length() < 2) {
		            throw new IllegalArgumentException("Not a valid argument: " + args[t]);
		          }
		          if((args[t].equals("-V"))){
		          		System.out.println("ECC agent - Implemented by Spectrum Computing Support @ IBM Canada, 2017");
		          		showHelp();
		          		System.exit(0);    		
		          }else{
		        	  if ((args.length - 1 == t)) {
		                  throw new IllegalArgumentException("Expected arg after: " + args[t]);
		                }

		        	  optsList.add(new Option(args[t], args[(t + 1)]));
		              //System.out.println("args = " + args[t] + ";  value = " + args[(t + 1)]);
		              switch (args[t].charAt(1)) {
		              	case 'S': 
		              		EccService = args[(t + 1)];
		            	if(!EccService.equals("ProblemReport")){
		            		EccService = "ProblemReport";
		            	}
		            	break;
		              }
		              t++; 
		          }
		        }
		 }// End of parse arguments
		return EccService;
	}
	
	public static void showHelp(){
		System.out.println("Supported arguments: [SEivIuNFpesCcTtUrdVD]");
		//Can add more information here
						
	}
}

