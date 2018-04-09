<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSLFormat ">
<xsl:output method="html" indent="yes"/>
 
<xsl:variable name="tab">
<xsl:text>&#160;&#160;&#160;</xsl:text>
</xsl:variable>
<xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ.'"/>
<xsl:variable name="lowercase" select="'abcdefghijklmnopqrstuvwxyz.'"/>
 
<!-- Call template to extract the class name from the fully qualified class -->
<xsl:template name="substring-after-last">
  <xsl:param name="input"/>
  <xsl:param name="substr"/>
  <!-- Extract the string which comes after the first occurence -->
  <xsl:variable name="temp" select="substring-after($input,$substr)"/>
  <xsl:choose>
     <!-- If it still contains the search string the recursively process -->
     <xsl:when test="$substr and contains($temp,$substr)">
          <xsl:call-template name="substring-after-last">
               <xsl:with-param name="input" select="$temp"/>
               <xsl:with-param name="substr" select="$substr"/>
          </xsl:call-template>
     </xsl:when>
     <xsl:otherwise>
          <xsl:value-of select="$temp"/>
     </xsl:otherwise>
  </xsl:choose>
</xsl:template>
 
<!-- template to replace newline chars to <br />  -->
<xsl:template name="br-replace">
   <xsl:param name="word"/>
   <xsl:variable name="cr" select="'&#xa;'"/>
   <xsl:choose>
   <xsl:when test="contains($word,$cr)">
       <xsl:value-of select="substring-before($word,$cr)"/>
       <br/><xsl:value-of select="$tab" />
       <xsl:call-template name="br-replace">
         <xsl:with-param name="word" 
             select="substring-after($word,$cr)"/>
       </xsl:call-template>
   </xsl:when>
   <xsl:otherwise>
     <xsl:value-of select="$word"/>
   </xsl:otherwise>
  </xsl:choose>
 </xsl:template>
 
<!-- general template to apply  -->
<xsl:template match="/">
  <xsl:apply-templates />
</xsl:template>
 
<!-- process all tags in the file  -->
<xsl:template match="log">
<html>
<style type="text/css"> 
  table { font-size: 75%; text-align: left; }
  td    { white-space: nowrap; vertical-align: text-top; }
</style>
 <head>
  <title>ecc trace log</title> 
  </head>
  <xsl:for-each select="logfile">
    <xsl:value-of select="." />
    <br />
  </xsl:for-each>
  <body>
<br /><br />
<table border="0">
<tr>
<th>Date/Time</th>
<th>Thread</th>
<th>Object ID</th>
<th>Method</th>
<th>Level</th>
<th>Trace data/Exception data</th>
<th>Full date/timestamp</th>
<th>Full class name</th>
<th>JVM ID</th>
</tr>
<xsl:for-each select="record">
<xsl:sort select="date"/>
<tr>
  <!-- output the date/time  -->
  <td>
   <tt>
    <xsl:value-of select="concat('[',substring(date,6,2),'/',substring(date,9,2),' ',substring(date,12,12),']') " />
    <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the thread id  -->
  <td>
   <tt>
     <xsl:value-of select="format-number(thread,'000000')" />
     <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the object id  -->
  <td>
   <tt>
     <xsl:value-of select="format-number(objectid,'##########')" />
     <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the classname/method  -->
  <td>
   <tt>
     <b><em>
       <xsl:choose>
          <xsl:when test="contains(class,'.')">
           <xsl:call-template name="substring-after-last">
                <xsl:with-param name="input" select="class"/>
                <xsl:with-param name="substr" select="'.'"/>
          </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
           <xsl:value-of select="class" />
          </xsl:otherwise>
        </xsl:choose>
      <xsl:value-of select="concat(':',method)" />
     </em></b>
     <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the level  -->
  <xsl:choose>
   <xsl:when test="level='SEVERE'">
    <td><tt><b><font color="red"><xsl:value-of select="level" /></font></b></tt>
     <xsl:text>&#160;&#160;</xsl:text>
    </td>
   </xsl:when>
   <xsl:when test="level='WARNING'">
       <td><tt><b><font color="maroon"><xsl:value-of select="level" /></font></b></tt>
      <xsl:text>&#160;&#160;</xsl:text>
    </td>
  </xsl:when>
   <xsl:otherwise>
     <td><tt><b><font color="black"><xsl:value-of select="level" /></font></b></tt>
      <xsl:text>&#160;&#160;</xsl:text>
    </td>
  </xsl:otherwise>
  </xsl:choose>
 
  <!-- output the trace data (if any) -->
  <td>
   <xsl:if test="message">
    <tt>
      <i><xsl:text>Trace data&#58;</xsl:text></i>
      <xsl:text>&#160;</xsl:text>
       <xsl:call-template name="br-replace">
         <xsl:with-param name="word" select="message"/>
       </xsl:call-template>
      <xsl:text>&#160;&#160;</xsl:text>
    </tt>
   </xsl:if>
 
   <!-- output the environment data (if any) -->
   <xsl:if test="environment">
    <tt>
      <xsl:if test="message">
       <br />
     </xsl:if>
     <i><xsl:text>Environment&#58;</xsl:text></i>
      <xsl:text>&#160;</xsl:text>
      <xsl:value-of select="environment" />
      <xsl:text>&#160;&#160;</xsl:text>
    </tt>
   </xsl:if>
 
   <!-- output the exception data (if any) -->
   <xsl:if test="exception">
      <xsl:if test="message or environment" >
       <br />
     </xsl:if>
     <xsl:apply-templates select="exception" />
      <xsl:text>&#160;&#160;</xsl:text>
   </xsl:if>
 
  </td>
 
  <!-- output the full date/timestamp  -->
  <td>
   <tt>
    <xsl:value-of select="concat('[',substring(date,6,2),'/',substring(date,9,2),'/',substring(date,1,4),' ',substring(date,12,12),' ',substring(date, 24, 5),']') " />
    <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the full class name -->
  <td>
   <tt>
     <xsl:value-of select="class" />
     <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
 
  <!-- output the jvmid -->
  <td>
   <tt>
     <xsl:value-of select="jvmid" />
     <xsl:text>&#160;&#160;</xsl:text>
   </tt>
  </td>
</tr>
</xsl:for-each>
 
</table>
</body>
</html>
</xsl:template>
 
<!-- template to format the exception data -->
<xsl:template match="exception">
     <tt>
      <i><xsl:text>Exception data&#58;</xsl:text></i>
      <xsl:text>&#160;</xsl:text>
       <font color="brown"> 
       <xsl:value-of select="error" />
       </font>
     </tt>
     <xsl:apply-templates select="frame" />
     <xsl:apply-templates select="causedby" />
</xsl:template>
 
<!-- template to format each frame of the exception data -->
<xsl:template match="frame">
      <tt>
      <br />
       <xsl:value-of select="$tab" />
       <xsl:text>at&#160;</xsl:text> 
       <xsl:value-of select="class" />
       <xsl:text>&#46;</xsl:text> 
       <xsl:value-of select="method" />
       <xsl:text>&#40;</xsl:text> 
       <xsl:value-of select="file" />
       <xsl:text>&#58;</xsl:text> 
       <xsl:value-of select="line" />
       <xsl:text>&#41;</xsl:text> 
      </tt>
</xsl:template>
<!-- template to format the caused by exception data -->
<xsl:template match="causedby">
     <tt>
      <br /><xsl:text>&#160;&#160;</xsl:text>
      <i><xsl:text>Caused by&#58;</xsl:text></i>
      <xsl:text>&#160;</xsl:text>
       <font color="brown"> 
       <xsl:value-of select="error" />
       </font>
     </tt>
     <xsl:apply-templates select="frame" />
</xsl:template>
 
</xsl:stylesheet>
