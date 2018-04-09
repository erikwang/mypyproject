package com.ibm.system.spectrum.computing.support.util;

public class Option
{
  String flag;
  String opt;
  
  public Option(String flag, String opt)
  {
    this.flag = flag;this.opt = opt;
  }
  
  public String getflag() { return flag; }
  
  public String getopt()
  {
    return opt;
  }
}