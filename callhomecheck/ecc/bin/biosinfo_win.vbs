Set StdOut = WScript.StdOut
Set wbemSvc = GetObject("winmgmts://" & "." & "/root/cimv2")
Set csObjSet = wbemSvc.ExecQuery("Select * from Win32_ComputerSystemProduct")
ProductId = "Unknown"
For Each csObj In csObjSet
  ProductId = csObj.Name
  StdOut.WriteLine "SystemManufacturer=" & csObj.Vendor
  StdOut.WriteLine "SystemProduct=" & csObj.Name
  StdOut.WriteLine "SystemSerialNumber=" & csObj.IdentifyingNumber
  StdOut.WriteLine "SystemVersion=" & csObj.Version

  SystemUUID = Replace(csObj.UUID, "-", "")
  If (Len(SystemUUID) = 32) Then
    TempUUID1 = Mid(SystemUUID,7,2) & Mid(SystemUUID,5,2) & Mid(SystemUUID,3,2) & Mid(SystemUUID,1,2)
    TempUUID2 = Mid(SystemUUID,11,2) & Mid(SystemUUID,9,2) & Mid(SystemUUID,15,2) & Mid(SystemUUID,13,2)
    SystemUUID = TempUUID1 & TempUUID2 & Mid(SystemUUID, 17, 16)
  End If
  StdOut.WriteLine "SystemUUID=" & SystemUUID
Next
Set osObjSet = wbemSvc.ExecQuery("Select * from Win32_OperatingSystem")
For Each osObj In osObjSet
  StdOut.WriteLine "SystemCaption=" & osObj.Caption
  StdOut.WriteLine "SystemVersion=" & osObj.Version
Next

const HKEY_LOCAL_MACHINE = &H80000002
Set osReg = GetObject("winmgmts:\\" & "." & "\root\default:StdRegProv")
strKeyPath = "SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName"
strValueName = "TWGMachineID"
osReg.GetBinaryValue HKEY_LOCAL_MACHINE,strKeyPath,strValueName,strValue
If (IsNull(strValue) = false) Then
  StdOut.Write "SystemGUID="
  For i = lBound(strValue) to uBound(strValue)
    StdOut.Write ToHexStr(i)
  Next
  StdOut.WriteLine
End If

nodeCount = 0
Set nodeObjSet = wbemSvc.ExecQuery("Select * from Win32_SystemEnclosure")
For Each nodeObj In nodeObjSet
  nodeCount = nodeCount + 1
Next
If nodeCount > 1 Then
  StdOut.WriteLine "VMID=0"
  StdOut.WriteLine "MultiNode=true"
Else
  StdOut.WriteLine "MultiNode=false"
End If

Function ToHexStr(intVal)
  hexStr = Hex(strValue(intVal))
  If Len(hexStr) > 1 Then
    ToHexStr = hexStr
  Else
    ToHexStr = "0" & hexStr
  End If
End Function