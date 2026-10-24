param(
    [Parameter(Mandatory = $true)][string]$RequestPath,
    [Parameter(Mandatory = $true)][string]$ResponsePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$script:TerminalRootHandle = [IntPtr]::Zero
$script:FailureCheckpoint = "initializing"
$script:TesterPaneFailureDiagnostic = $null
$script:StrategyExecutionProof = $null

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
public static class MetafxMt5VisibleNative {
  public const int WM_COMMAND = 0x0111;
  public const int WM_GETTEXT = 0x000D;
  public const int WM_GETTEXTLENGTH = 0x000E;
  public const int WM_SETTEXT = 0x000C;
  public const int WM_LBUTTONDOWN = 0x0201;
  public const int WM_LBUTTONUP = 0x0202;
  public const int WM_CONTEXTMENU = 0x007B;
  public const int WM_KEYDOWN = 0x0100;
  public const int WM_KEYUP = 0x0101;
  public const int BM_CLICK = 0x00F5;
  public const int BM_GETCHECK = 0x00F0;
  public const int CB_ADDSTRING = 0x0143;
  public const int CB_DELETESTRING = 0x0144;
  public const int CB_GETCOUNT = 0x0146;
  public const int CB_GETCURSEL = 0x0147;
  public const int CB_GETLBTEXT = 0x0148;
  public const int CB_GETLBTEXTLEN = 0x0149;
  public const int CB_SETCURSEL = 0x014E;
  public const int CB_SHOWDROPDOWN = 0x014F;
  public const int CB_GETDROPPEDSTATE = 0x0157;
  public const int CB_ERR = -1;
  public const int CB_ERRSPACE = -2;
  public const int CBS_DROPDOWN = 0x0002;
  public const int CBS_DROPDOWNLIST = 0x0003;
  public const int CBS_HASSTRINGS = 0x0200;
  public const int CBN_SELCHANGE = 1;
  public const int CBN_EDITCHANGE = 5;
  public const int TB_GETSTATE = 0x0412;
  public const int DTM_GETSYSTEMTIME = 0x1001;
  public const int DTM_SETSYSTEMTIME = 0x1002;
  public const int GDT_VALID = 0;
  public const int TVM_GETNEXTITEM = 0x110A;
  public const int TVM_SELECTITEM = 0x110B;
  public const int TVM_GETITEMW = 0x113E;
  public const int TVGN_ROOT = 0x0000;
  public const int TVGN_NEXT = 0x0001;
  public const int TVGN_PARENT = 0x0003;
  public const int TVGN_CHILD = 0x0004;
  public const int TVGN_CARET = 0x0009;
  public const int MN_GETHMENU = 0x01E1;
  public const int MN_SELECTITEM = 0x01E5;
  public const int VK_RETURN = 0x000D;
  public const int VK_ESCAPE = 0x001B;
  public const int VK_RIGHT = 0x0027;
  public const int VK_F4 = 0x0073;
  public const uint MF_GRAYED = 0x0001;
  public const uint MF_DISABLED = 0x0002;
  public const uint MF_BYPOSITION = 0x0400;
  public const uint MF_SEPARATOR = 0x0800;
  public const int GWL_STYLE = -16;
  public const int WS_DISABLED = 0x08000000;
  public const uint SMTO_ABORTIFHUNG = 0x0002;
  public const uint SMTO_BLOCK = 0x0001;
  public const uint SMTO_NOTIMEOUTIFNOTHUNG = 0x0008;
  public const uint SMTO_ERRORONEXIT = 0x0020;
  public const uint GA_ROOT = 2;
  public const uint GW_OWNER = 4;
  public const uint GUI_INMENUMODE = 0x00000004;
  public const uint GUI_POPUPMENUMODE = 0x00000010;
  const uint PROCESS_ACCESS = 0x0438;
  const uint MEM_COMMIT = 0x1000;
  const uint MEM_RESERVE = 0x2000;
  const uint MEM_RELEASE = 0x8000;
  const uint PAGE_READWRITE = 0x0004;
  const uint TVIF_TEXT = 0x0001;
  const int TREE_TEXT_CHARS = 512;
  const int MAX_ROOT_TREE_ITEMS = 256;
  const int MAX_POPUP_MENU_ITEMS = 128;
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool BringWindowToTop(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr SetActiveWindow(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr SetFocus(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
  [DllImport("user32.dll", SetLastError=true)] public static extern bool AttachThreadInput(uint sourceThreadId, uint targetThreadId, bool attach);
  [DllImport("user32.dll")] public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool GetClientRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool ClientToScreen(IntPtr hWnd, ref POINT point);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr GetParent(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr GetWindow(IntPtr hWnd, uint command);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr GetAncestor(IntPtr hWnd, uint flags);
  [DllImport("user32.dll", SetLastError=true)] public static extern int GetDlgCtrlID(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern int GetWindowLong(IntPtr hWnd, int index);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool IsWindow(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool IsWindowEnabled(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
  [DllImport("user32.dll")] public static extern IntPtr GetKeyboardLayout(uint threadId);
  [DllImport("user32.dll")] public static extern IntPtr GetMenu(IntPtr hWnd);
  [DllImport("user32.dll", SetLastError=true)] static extern bool GetGUIThreadInfo(uint threadId, ref GUITHREADINFO info);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int maximum);
  delegate bool EnumWindowProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll", SetLastError=true)] static extern bool EnumWindows(EnumWindowProc callback, IntPtr lParam);
  [DllImport("user32.dll", SetLastError=true)] static extern bool EnumChildWindows(IntPtr parent, EnumWindowProc callback, IntPtr lParam);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maximum);
  [DllImport("user32.dll", SetLastError=true)] public static extern bool PostMessage(IntPtr hWnd, int message, IntPtr wParam, IntPtr lParam);
  [DllImport("user32.dll", SetLastError=true)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, int message, IntPtr wParam, IntPtr lParam, uint flags, uint timeout, out IntPtr result);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, int message, IntPtr wParam, StringBuilder lParam, uint flags, uint timeout, out IntPtr result);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, int message, IntPtr wParam, [MarshalAs(UnmanagedType.LPWStr)] string lParam, uint flags, uint timeout, out IntPtr result);
  [DllImport("user32.dll", SetLastError=true)] static extern bool IsMenu(IntPtr menu);
  [DllImport("user32.dll", SetLastError=true)] static extern int GetMenuItemCount(IntPtr menu);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool GetMenuItemInfo(IntPtr menu, uint item, bool byPosition, ref MENUITEMINFO info);
  [DllImport("user32.dll", SetLastError=true)] static extern bool GetMenuItemRect(IntPtr window, IntPtr menu, uint item, out RECT rect);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint processId);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr VirtualAllocEx(IntPtr process, IntPtr address, UIntPtr size, uint allocationType, uint protection);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool VirtualFreeEx(IntPtr process, IntPtr address, UIntPtr size, uint freeType);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr written);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr read);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
  [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool IsWow64Process(IntPtr process, out bool wow64);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetFileInformationByHandle(IntPtr handle, out BY_HANDLE_FILE_INFORMATION information);
  [StructLayout(LayoutKind.Sequential)] struct SYSTEMTIME {
    public ushort Year; public ushort Month; public ushort DayOfWeek; public ushort Day;
    public ushort Hour; public ushort Minute; public ushort Second; public ushort Milliseconds;
  }
  [StructLayout(LayoutKind.Sequential)] struct BY_HANDLE_FILE_INFORMATION {
    public uint FileAttributes;
    public System.Runtime.InteropServices.ComTypes.FILETIME CreationTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastAccessTime;
    public System.Runtime.InteropServices.ComTypes.FILETIME LastWriteTime;
    public uint VolumeSerialNumber;
    public uint FileSizeHigh;
    public uint FileSizeLow;
    public uint NumberOfLinks;
    public uint FileIndexHigh;
    public uint FileIndexLow;
  }
  [StructLayout(LayoutKind.Sequential)] struct TVITEM {
    public uint mask; public IntPtr hItem; public uint state; public uint stateMask;
    public IntPtr pszText; public int cchTextMax; public int iImage; public int iSelectedImage;
    public int cChildren; public IntPtr lParam;
  }
  struct TREEITEMMATCH {
    public IntPtr item; public IntPtr parent;
  }
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
  public struct POINT { public int X; public int Y; }
  [StructLayout(LayoutKind.Sequential)] struct GUITHREADINFO {
    public uint cbSize; public uint flags;
    public IntPtr hwndActive; public IntPtr hwndFocus; public IntPtr hwndCapture;
    public IntPtr hwndMenuOwner; public IntPtr hwndMoveSize; public IntPtr hwndCaret;
    public RECT rcCaret;
  }
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct MENUITEMINFO {
    public uint cbSize; public uint fMask; public uint fType; public uint fState; public uint wID;
    public IntPtr hSubMenu; public IntPtr hbmpChecked; public IntPtr hbmpUnchecked;
    public UIntPtr dwItemData; public IntPtr dwTypeData; public uint cch; public IntPtr hbmpItem;
  }
  public sealed class MENUITEMSNAPSHOT {
    public int Position;
    public uint CommandId;
    public string Text;
    public uint State;
    public bool IsEnabled;
    public bool IsSeparator;
    public bool HasSubmenu;
    public IntPtr SubmenuHandle;
    public UIntPtr ItemData;
    public uint TextLength;
  }
  public sealed class POPUPMENUTOKEN {
    public IntPtr PopupWindow;
    public IntPtr MenuHandle;
    public IntPtr CommandOwner;
    public uint MenuThreadId;
    public MENUITEMSNAPSHOT[] Items;
  }
  public static uint GetFileLinkCount(IntPtr handle) {
    if (handle == IntPtr.Zero || handle == new IntPtr(-1))
      throw new InvalidOperationException("checkpoint_handle_invalid");
    BY_HANDLE_FILE_INFORMATION information;
    if (!GetFileInformationByHandle(handle, out information) || information.NumberOfLinks == 0)
      throw new InvalidOperationException("checkpoint_identity_unavailable");
    return information.NumberOfLinks;
  }
  static string ReadWindowTextExact(IntPtr window) {
    StringBuilder text = new StringBuilder(4096);
    int length = GetWindowText(window, text, text.Capacity);
    if (length < 0 || length >= text.Capacity - 1) throw new InvalidOperationException("window_text_unavailable");
    return text.ToString();
  }
  static string ReadWindowClassExact(IntPtr window) {
    StringBuilder text = new StringBuilder(256);
    int length = GetClassName(window, text, text.Capacity);
    if (length <= 0 || length >= text.Capacity - 1) throw new InvalidOperationException("window_class_unavailable");
    return text.ToString();
  }
  public static string GetWindowTextExact(IntPtr window) {
    if (window == IntPtr.Zero || !IsWindow(window)) throw new InvalidOperationException("window_unavailable");
    return ReadWindowTextExact(window);
  }
  public static IntPtr FindTerminalMainWindowExact(uint expectedProcessId) {
    if (expectedProcessId == 0) throw new InvalidOperationException("mt5_terminal_process_changed");
    List<IntPtr> matches = new List<IntPtr>();
    bool enumerated = EnumWindows(delegate(IntPtr window, IntPtr ignored) {
      uint processId; GetWindowThreadProcessId(window, out processId);
      if (processId != expectedProcessId || !IsWindow(window) ||
          !IsWindowVisible(window) || !IsWindowEnabled(window) ||
          GetWindow(window, GW_OWNER) != IntPtr.Zero || GetAncestor(window, GA_ROOT) != window) return true;
      if (String.Equals(ReadWindowClassExact(window), "MetaQuotes::MetaTrader::5.00", StringComparison.Ordinal))
        matches.Add(window);
      return true;
    }, IntPtr.Zero);
    if (!enumerated) throw new InvalidOperationException("mt5_terminal_root_enumeration_failed");
    if (matches.Count > 1) throw new InvalidOperationException("mt5_terminal_root_ambiguous");
    return matches.Count == 1 ? matches[0] : IntPtr.Zero;
  }
  public static void PostButtonClickIfTextExact(IntPtr button, uint expectedProcessId, IntPtr expectedRoot, int expectedControlId, string expectedText) {
    if (expectedControlId <= 0 || String.IsNullOrEmpty(expectedText)) throw new InvalidOperationException("button_identity_invalid");
    AssertRemoteOwner(button, expectedProcessId, expectedRoot);
    uint buttonProcessId; uint buttonThreadId = GetWindowThreadProcessId(button, out buttonProcessId);
    uint rootProcessId; uint rootThreadId = GetWindowThreadProcessId(expectedRoot, out rootProcessId);
    if (GetForegroundWindow() != expectedRoot || buttonThreadId == 0 || rootThreadId == 0 ||
        buttonThreadId != rootThreadId || buttonProcessId != expectedProcessId || rootProcessId != expectedProcessId)
      throw new InvalidOperationException("button_foreground_binding_changed");
    if (!String.Equals(ReadWindowClassExact(button), "Button", StringComparison.Ordinal) ||
        GetDlgCtrlID(button) != expectedControlId ||
        (GetWindowLong(button, GWL_STYLE) & WS_DISABLED) != 0 ||
        !String.Equals(ReadWindowTextExact(button), expectedText, StringComparison.Ordinal))
      throw new InvalidOperationException("button_identity_changed");
    // BM_CLICK is intentionally queued exactly once.  A synchronous send can
    // remain inside MT5's button handler for the entire fast tester run, then
    // return only after Start is already idle and its Stop transition is lost.
    if (!PostMessage(button, BM_CLICK, IntPtr.Zero, IntPtr.Zero))
      throw new InvalidOperationException("button_click_post_failed");
  }
  public static IntPtr FindOwnedDialogExact(uint expectedProcessId, IntPtr expectedOwner, string[] expectedTitles) {
    if (expectedProcessId == 0 || expectedOwner == IntPtr.Zero || expectedTitles == null || expectedTitles.Length == 0 ||
        !IsWindow(expectedOwner)) throw new InvalidOperationException("file_dialog_binding_invalid");
    List<IntPtr> matches = new List<IntPtr>();
    bool enumerated = EnumWindows(delegate(IntPtr window, IntPtr ignored) {
      uint processId; GetWindowThreadProcessId(window, out processId);
      if (processId != expectedProcessId || GetWindow(window, GW_OWNER) != expectedOwner ||
          !IsWindowVisible(window) || !IsWindowEnabled(window) || ReadWindowClassExact(window) != "#32770") return true;
      string title = ReadWindowTextExact(window);
      int titleMatches = 0;
      foreach (string expected in expectedTitles)
        if (String.Equals(title, expected, StringComparison.Ordinal)) titleMatches++;
      if (titleMatches == 1) matches.Add(window);
      return true;
    }, IntPtr.Zero);
    if (!enumerated || matches.Count > 1) throw new InvalidOperationException("file_dialog_ambiguous");
    return matches.Count == 1 ? matches[0] : IntPtr.Zero;
  }
  public static IntPtr FindDialogControlExact(IntPtr dialog, uint expectedProcessId, int expectedId, string expectedClass) {
    if (dialog == IntPtr.Zero || expectedProcessId == 0 || String.IsNullOrWhiteSpace(expectedClass) ||
        !IsWindow(dialog) || !IsWindowVisible(dialog) || !IsWindowEnabled(dialog) ||
        ReadWindowClassExact(dialog) != "#32770") throw new InvalidOperationException("file_dialog_binding_invalid");
    uint dialogProcessId; GetWindowThreadProcessId(dialog, out dialogProcessId);
    if (dialogProcessId != expectedProcessId || GetAncestor(dialog, GA_ROOT) != dialog)
      throw new InvalidOperationException("file_dialog_binding_invalid");
    List<IntPtr> matches = new List<IntPtr>();
    bool enumerated = EnumChildWindows(dialog, delegate(IntPtr window, IntPtr ignored) {
      uint processId; GetWindowThreadProcessId(window, out processId);
      if (processId == expectedProcessId && GetAncestor(window, GA_ROOT) == dialog &&
          IsWindowVisible(window) && IsWindowEnabled(window) && GetDlgCtrlID(window) == expectedId &&
          String.Equals(ReadWindowClassExact(window), expectedClass, StringComparison.Ordinal)) matches.Add(window);
      return true;
    }, IntPtr.Zero);
    if (!enumerated || matches.Count != 1) throw new InvalidOperationException("file_dialog_control_not_unique");
    return matches[0];
  }
  public static IntPtr FindChildControlExact(IntPtr parent, uint expectedProcessId, IntPtr expectedRoot, int expectedId, string expectedClass) {
    if (parent == IntPtr.Zero || expectedProcessId == 0 || expectedRoot == IntPtr.Zero ||
        String.IsNullOrWhiteSpace(expectedClass) || !IsWindow(parent) || !IsWindow(expectedRoot) ||
        !IsWindowVisible(parent) || !IsWindowEnabled(parent) || GetAncestor(parent, GA_ROOT) != expectedRoot)
      throw new InvalidOperationException("mt5_child_control_binding_invalid");
    uint parentProcessId; GetWindowThreadProcessId(parent, out parentProcessId);
    uint rootProcessId; GetWindowThreadProcessId(expectedRoot, out rootProcessId);
    if (parentProcessId != expectedProcessId || rootProcessId != expectedProcessId)
      throw new InvalidOperationException("mt5_child_control_binding_invalid");
    List<IntPtr> matches = new List<IntPtr>();
    bool enumerated = EnumChildWindows(parent, delegate(IntPtr window, IntPtr ignored) {
      uint processId; GetWindowThreadProcessId(window, out processId);
      if (processId == expectedProcessId && GetAncestor(window, GA_ROOT) == expectedRoot &&
          GetParent(window) == parent && IsWindowVisible(window) && IsWindowEnabled(window) &&
          GetDlgCtrlID(window) == expectedId &&
          String.Equals(ReadWindowClassExact(window), expectedClass, StringComparison.Ordinal)) matches.Add(window);
      return true;
    }, IntPtr.Zero);
    if (!enumerated || matches.Count != 1)
      throw new InvalidOperationException("mt5_child_control_not_unique");
    return matches[0];
  }
  static void AssertRemoteOwner(IntPtr window, uint expectedProcessId, IntPtr expectedRoot) {
    if (window == IntPtr.Zero || expectedProcessId == 0 || expectedRoot == IntPtr.Zero ||
        !IsWindow(window) || !IsWindow(expectedRoot) || !IsWindowVisible(window) || !IsWindowEnabled(window))
      throw new InvalidOperationException("mt5_date_control_owner_invalid");
    uint owner; GetWindowThreadProcessId(window, out owner);
    uint rootOwner; GetWindowThreadProcessId(expectedRoot, out rootOwner);
    if (owner != expectedProcessId || rootOwner != expectedProcessId || GetAncestor(window, GA_ROOT) != expectedRoot)
      throw new InvalidOperationException("mt5_date_control_owner_invalid");
  }
  static byte[] StructureBytes(SYSTEMTIME value) {
    int size = Marshal.SizeOf(typeof(SYSTEMTIME));
    IntPtr local = Marshal.AllocHGlobal(size);
    try {
      Marshal.StructureToPtr(value, local, false);
      byte[] bytes = new byte[size]; Marshal.Copy(local, bytes, 0, size); return bytes;
    } finally { Marshal.FreeHGlobal(local); }
  }
  static SYSTEMTIME BytesStructure(byte[] bytes) {
    IntPtr local = Marshal.AllocHGlobal(bytes.Length);
    try { Marshal.Copy(bytes, 0, local, bytes.Length); return (SYSTEMTIME)Marshal.PtrToStructure(local, typeof(SYSTEMTIME)); }
    finally { Marshal.FreeHGlobal(local); }
  }
  static byte[] TreeItemBytes(TVITEM value) {
    int size = Marshal.SizeOf(typeof(TVITEM));
    IntPtr local = Marshal.AllocHGlobal(size);
    try {
      Marshal.StructureToPtr(value, local, false);
      byte[] bytes = new byte[size]; Marshal.Copy(local, bytes, 0, size); return bytes;
    } finally { Marshal.FreeHGlobal(local); }
  }
  static IntPtr SendRemoteDateMessage(IntPtr window, int message, IntPtr wParam, IntPtr remote) {
    IntPtr result;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_NOTIMEOUTIFNOTHUNG;
    if (SendMessageTimeout(window, message, wParam, remote, flags, 1500, out result) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_date_message_timeout");
    return result;
  }
  static void AssertRemoteTree(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteOwner(tree, expectedProcessId, expectedRoot);
    StringBuilder className = new StringBuilder(64);
    if (GetClassName(tree, className, className.Capacity) <= 0 ||
        !String.Equals(className.ToString(), "SysTreeView32", StringComparison.Ordinal))
      throw new InvalidOperationException("mt5_tree_control_invalid");
  }
  static IntPtr AssertPopupMenuOwner(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot) {
    if (menuWindow == IntPtr.Zero || expectedProcessId == 0 || expectedRoot == IntPtr.Zero ||
        !IsWindow(menuWindow) || !IsWindow(expectedRoot) || !IsWindowVisible(menuWindow) || !IsWindowEnabled(menuWindow))
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    uint owner; uint rootOwner;
    uint menuThread = GetWindowThreadProcessId(menuWindow, out owner);
    uint rootThread = GetWindowThreadProcessId(expectedRoot, out rootOwner);
    if (menuThread == 0 || rootThread == 0 || menuThread != rootThread ||
        owner != expectedProcessId || rootOwner != expectedProcessId)
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    if (GetAncestor(expectedRoot, GA_ROOT) != expectedRoot)
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    StringBuilder className = new StringBuilder(64);
    if (GetClassName(menuWindow, className, className.Capacity) <= 0 ||
        !String.Equals(className.ToString(), "#32768", StringComparison.Ordinal))
      throw new InvalidOperationException("mt5_popup_menu_class_invalid");
    // Standard #32768 popup hosts commonly have no GW_OWNER even though they
    // execute on the owning terminal UI thread.  Bind the host to that exact
    // thread/process/root and to the thread's active popup-menu mode instead of
    // rejecting the legitimate ownerless host or accepting a process peer.
    IntPtr ownerWindow = GetWindow(menuWindow, GW_OWNER);
    if (ownerWindow != IntPtr.Zero &&
        ownerWindow != expectedRoot && GetAncestor(ownerWindow, GA_ROOT) != expectedRoot)
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    if (GetForegroundWindow() != expectedRoot)
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    int infoSize = Marshal.SizeOf(typeof(GUITHREADINFO));
    if (infoSize != (IntPtr.Size == 8 ? 72 : 48))
      throw new InvalidOperationException("mt5_popup_menu_layout_invalid");
    GUITHREADINFO info = new GUITHREADINFO { cbSize = (uint)infoSize };
    if (!GetGUIThreadInfo(menuThread, ref info) || info.hwndActive != expectedRoot ||
        (info.flags & GUI_INMENUMODE) == 0 || (info.flags & GUI_POPUPMENUMODE) == 0)
      throw new InvalidOperationException("mt5_popup_menu_owner_invalid");
    IntPtr commandOwner = info.hwndMenuOwner;
    if (commandOwner == IntPtr.Zero || commandOwner == menuWindow || !IsWindow(commandOwner))
      throw new InvalidOperationException("mt5_popup_menu_command_owner_invalid");
    uint commandOwnerPid;
    uint commandOwnerThread = GetWindowThreadProcessId(commandOwner, out commandOwnerPid);
    if (commandOwnerThread != menuThread || commandOwnerPid != expectedProcessId ||
        (commandOwner != expectedRoot && GetAncestor(commandOwner, GA_ROOT) != expectedRoot))
      throw new InvalidOperationException("mt5_popup_menu_command_owner_invalid");
    return commandOwner;
  }
  static IntPtr GetPopupMenuHandleExact(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot) {
    AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot);
    IntPtr menu;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT;
    if (SendMessageTimeout(menuWindow, MN_GETHMENU, IntPtr.Zero, IntPtr.Zero, flags, 1500, out menu) == IntPtr.Zero || menu == IntPtr.Zero)
      throw new InvalidOperationException("mt5_popup_menu_handle_invalid");
    if (!IsMenu(menu)) throw new InvalidOperationException("mt5_popup_menu_handle_invalid");
    AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot);
    return menu;
  }
  static MENUITEMSNAPSHOT ReadPopupMenuItemExact(IntPtr menu, int position) {
    const uint MIIM_STATE = 0x00000001;
    const uint MIIM_ID = 0x00000002;
    const uint MIIM_SUBMENU = 0x00000004;
    const uint MIIM_DATA = 0x00000020;
    const uint MIIM_STRING = 0x00000040;
    const uint MIIM_FTYPE = 0x00000100;
    const uint MFT_SEPARATOR = 0x00000800;
    const uint MFS_DISABLED = 0x00000003;
    uint mask = MIIM_STATE | MIIM_ID | MIIM_SUBMENU | MIIM_DATA | MIIM_STRING | MIIM_FTYPE;
    MENUITEMINFO first = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask };
    if (!GetMenuItemInfo(menu, (uint)position, true, ref first) || first.cch > 511)
      throw new InvalidOperationException("mt5_popup_menu_item_invalid");
    bool separator = (first.fType & MFT_SEPARATOR) != 0;
    IntPtr textBuffer = IntPtr.Zero;
    try {
      const uint capacity = 512;
      int bufferBytes = checked((int)(capacity + 1) * 2);
      int sentinelOffset = checked((int)capacity * 2);
      textBuffer = Marshal.AllocHGlobal(bufferBytes);
      for (int offset = 0; offset < bufferBytes; offset++) Marshal.WriteByte(textBuffer, offset, 0);
      Marshal.WriteByte(textBuffer, sentinelOffset, 0xA5);
      Marshal.WriteByte(textBuffer, sentinelOffset + 1, 0x5A);
      MENUITEMINFO second = new MENUITEMINFO {
        cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask,
        dwTypeData=textBuffer, cch=capacity
      };
      if (!GetMenuItemInfo(menu, (uint)position, true, ref second) || second.cch > 511 ||
          second.cch != first.cch || Marshal.ReadByte(textBuffer, sentinelOffset) != 0xA5 ||
          Marshal.ReadByte(textBuffer, sentinelOffset + 1) != 0x5A ||
          first.fType != second.fType || first.fState != second.fState || first.wID != second.wID ||
          first.hSubMenu != second.hSubMenu || first.dwItemData != second.dwItemData)
        throw new InvalidOperationException("mt5_popup_menu_item_invalid");
      MENUITEMINFO third = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask };
      if (!GetMenuItemInfo(menu, (uint)position, true, ref third) || third.cch > 511 ||
          third.cch != second.cch || third.fType != second.fType || third.fState != second.fState ||
          third.wID != second.wID || third.hSubMenu != second.hSubMenu ||
          third.dwItemData != second.dwItemData)
        throw new InvalidOperationException("mt5_popup_menu_item_invalid");
      if (second.hSubMenu != IntPtr.Zero && !IsMenu(second.hSubMenu))
        throw new InvalidOperationException("mt5_popup_menu_item_invalid");
      string text = second.cch == 0 ? String.Empty : Marshal.PtrToStringUni(textBuffer, checked((int)second.cch));
      if (text == null || (!separator && String.IsNullOrWhiteSpace(text)))
        throw new InvalidOperationException("mt5_popup_menu_text_invalid");
      return new MENUITEMSNAPSHOT {
        Position=position, CommandId=second.wID, Text=text, State=second.fState,
        IsEnabled=(second.fState & MFS_DISABLED) == 0,
        IsSeparator=separator, HasSubmenu=second.hSubMenu != IntPtr.Zero,
        SubmenuHandle=second.hSubMenu, ItemData=second.dwItemData, TextLength=second.cch
      };
    } finally {
      if (textBuffer != IntPtr.Zero) Marshal.FreeHGlobal(textBuffer);
    }
  }
  static bool SamePopupMenuItem(MENUITEMSNAPSHOT left, MENUITEMSNAPSHOT right) {
    return left != null && right != null && left.Position == right.Position &&
      left.CommandId == right.CommandId && String.Equals(left.Text, right.Text, StringComparison.Ordinal) &&
      left.State == right.State && left.IsEnabled == right.IsEnabled &&
      left.IsSeparator == right.IsSeparator && left.HasSubmenu == right.HasSubmenu &&
      left.SubmenuHandle == right.SubmenuHandle && left.ItemData == right.ItemData &&
      left.TextLength == right.TextLength;
  }
  static bool SamePopupMenuItemIgnoringHighlight(MENUITEMSNAPSHOT left, MENUITEMSNAPSHOT right) {
    const uint MFS_HILITE = 0x00000080;
    return left != null && right != null && left.Position == right.Position &&
      left.CommandId == right.CommandId && String.Equals(left.Text, right.Text, StringComparison.Ordinal) &&
      (left.State & ~MFS_HILITE) == (right.State & ~MFS_HILITE) &&
      left.IsEnabled == right.IsEnabled && left.IsSeparator == right.IsSeparator &&
      left.HasSubmenu == right.HasSubmenu && left.SubmenuHandle == right.SubmenuHandle &&
      left.ItemData == right.ItemData && left.TextLength == right.TextLength;
  }
  public static MENUITEMSNAPSHOT[] ListPopupMenuItemsExact(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot) {
    IntPtr menu = GetPopupMenuHandleExact(menuWindow, expectedProcessId, expectedRoot);
    int count = GetMenuItemCount(menu);
    if (count <= 0 || count > MAX_POPUP_MENU_ITEMS)
      throw new InvalidOperationException("mt5_popup_menu_item_count_invalid");
    MENUITEMSNAPSHOT[] items = new MENUITEMSNAPSHOT[count];
    for (int position = 0; position < count; position++) {
      AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot);
      items[position] = ReadPopupMenuItemExact(menu, position);
    }
    AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot);
    if (GetPopupMenuHandleExact(menuWindow, expectedProcessId, expectedRoot) != menu || !IsMenu(menu))
      throw new InvalidOperationException("mt5_popup_menu_handle_changed");
    return items;
  }
  public static POPUPMENUTOKEN CapturePopupMenuTokenExact(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot) {
    IntPtr commandOwner = AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot);
    IntPtr menu = GetPopupMenuHandleExact(menuWindow, expectedProcessId, expectedRoot);
    MENUITEMSNAPSHOT[] items = ListPopupMenuItemsExact(menuWindow, expectedProcessId, expectedRoot);
    uint ownerPid;
    uint menuThread = GetWindowThreadProcessId(menuWindow, out ownerPid);
    if (menuThread == 0 || ownerPid != expectedProcessId ||
        commandOwner != AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot) ||
        menu != GetPopupMenuHandleExact(menuWindow, expectedProcessId, expectedRoot))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    return new POPUPMENUTOKEN {
      PopupWindow=menuWindow, MenuHandle=menu, CommandOwner=commandOwner,
      MenuThreadId=menuThread, Items=items
    };
  }
  static bool SamePopupMenuToken(POPUPMENUTOKEN left, POPUPMENUTOKEN right) {
    if (left == null || right == null || left.PopupWindow != right.PopupWindow ||
        left.MenuHandle != right.MenuHandle || left.CommandOwner != right.CommandOwner ||
        left.MenuThreadId != right.MenuThreadId || left.Items == null || right.Items == null ||
        left.Items.Length != right.Items.Length)
      return false;
    for (int index = 0; index < left.Items.Length; index++)
      if (!SamePopupMenuItem(left.Items[index], right.Items[index])) return false;
    return true;
  }
  static bool SamePopupMenuTokenIgnoringHighlight(POPUPMENUTOKEN left, POPUPMENUTOKEN right) {
    if (left == null || right == null || left.PopupWindow != right.PopupWindow ||
        left.MenuHandle != right.MenuHandle || left.CommandOwner != right.CommandOwner ||
        left.MenuThreadId != right.MenuThreadId || left.Items == null || right.Items == null ||
        left.Items.Length != right.Items.Length)
      return false;
    for (int index = 0; index < left.Items.Length; index++)
      if (!SamePopupMenuItemIgnoringHighlight(left.Items[index], right.Items[index])) return false;
    return true;
  }
  public static POPUPMENUTOKEN AssertPopupMenuTokenExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot) {
    if (expected == null || expected.PopupWindow == IntPtr.Zero || expected.MenuHandle == IntPtr.Zero ||
        expected.CommandOwner == IntPtr.Zero || expected.MenuThreadId == 0 || expected.Items == null)
      throw new InvalidOperationException("mt5_popup_menu_token_invalid");
    POPUPMENUTOKEN current = CapturePopupMenuTokenExact(expected.PopupWindow, expectedProcessId, expectedRoot);
    if (!SamePopupMenuToken(expected, current))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    return current;
  }
  public static POPUPMENUTOKEN RebindPopupMenuTokenIgnoringHighlightExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot) {
    if (expected == null || expected.PopupWindow == IntPtr.Zero || expected.MenuHandle == IntPtr.Zero ||
        expected.CommandOwner == IntPtr.Zero || expected.MenuThreadId == 0 || expected.Items == null)
      throw new InvalidOperationException("mt5_popup_menu_token_invalid");
    POPUPMENUTOKEN current = CapturePopupMenuTokenExact(expected.PopupWindow, expectedProcessId, expectedRoot);
    if (!SamePopupMenuTokenIgnoringHighlight(expected, current))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    return current;
  }
  static MENUITEMSNAPSHOT FindPopupMenuCommandExact(MENUITEMSNAPSHOT[] items, string expectedText, uint expectedCommandId) {
    if (String.IsNullOrWhiteSpace(expectedText) || expectedText.Length > 128 ||
        expectedCommandId == 0 || expectedCommandId > UInt16.MaxValue)
      throw new InvalidOperationException("mt5_popup_menu_command_invalid");
    MENUITEMSNAPSHOT textMatch = null; MENUITEMSNAPSHOT idMatch = null;
    int textMatches = 0; int idMatches = 0;
    for (int index = 0; index < items.Length; index++) {
      MENUITEMSNAPSHOT item = items[index];
      if (String.Equals(item.Text, expectedText, StringComparison.Ordinal)) { textMatch = item; textMatches++; }
      if (item.CommandId == expectedCommandId) { idMatch = item; idMatches++; }
    }
    if (textMatches != 1 || idMatches != 1 || textMatch == null || idMatch == null ||
        textMatch.Position != idMatch.Position || !SamePopupMenuItem(textMatch, idMatch) ||
        !textMatch.IsEnabled || textMatch.IsSeparator || textMatch.HasSubmenu)
      throw new InvalidOperationException("mt5_popup_menu_command_invalid");
    return textMatch;
  }
  static bool SamePopupMenuItemsIgnoringHighlight(MENUITEMSNAPSHOT[] left, MENUITEMSNAPSHOT[] right) {
    if (left == null || right == null || left.Length != right.Length) return false;
    for (int index = 0; index < left.Length; index++)
      if (!SamePopupMenuItemIgnoringHighlight(left[index], right[index])) return false;
    return true;
  }
  static bool SamePopupSubmenuItemAfterOpen(MENUITEMSNAPSHOT beforeOpen, MENUITEMSNAPSHOT afterOpen) {
    const uint MFS_HILITE = 0x00000080;
    if (beforeOpen == null || afterOpen == null || beforeOpen.Position != afterOpen.Position ||
        beforeOpen.CommandId != afterOpen.CommandId ||
        !String.Equals(beforeOpen.Text, afterOpen.Text, StringComparison.Ordinal) ||
        (beforeOpen.State & ~MFS_HILITE) != (afterOpen.State & ~MFS_HILITE) ||
        beforeOpen.IsEnabled != afterOpen.IsEnabled ||
        beforeOpen.IsSeparator != afterOpen.IsSeparator ||
        beforeOpen.HasSubmenu != afterOpen.HasSubmenu ||
        beforeOpen.SubmenuHandle != afterOpen.SubmenuHandle ||
        beforeOpen.TextLength != afterOpen.TextLength) return false;
    // Build 6230 lazily materializes each submenu item's private dwItemData
    // (the icon/resource value) when the submenu becomes visible.  Accept only
    // that one-way zero -> nonzero transition, or exact equality.  A nonzero
    // value changing to any other value remains a fail-closed identity change.
    return beforeOpen.ItemData == afterOpen.ItemData ||
      (beforeOpen.ItemData == UIntPtr.Zero && afterOpen.ItemData != UIntPtr.Zero);
  }
  static bool SamePopupSubmenuItemsAfterOpen(MENUITEMSNAPSHOT[] beforeOpen, MENUITEMSNAPSHOT[] afterOpen) {
    if (beforeOpen == null || afterOpen == null || beforeOpen.Length != afterOpen.Length) return false;
    for (int index = 0; index < beforeOpen.Length; index++)
      if (!SamePopupSubmenuItemAfterOpen(beforeOpen[index], afterOpen[index])) return false;
    return true;
  }
  static bool SamePopupMenuItems(MENUITEMSNAPSHOT[] left, MENUITEMSNAPSHOT[] right) {
    if (left == null || right == null || left.Length != right.Length) return false;
    for (int index = 0; index < left.Length; index++)
      if (!SamePopupMenuItem(left[index], right[index])) return false;
    return true;
  }
  static MENUITEMSNAPSHOT[] ListPopupMenuHandleItemsExact(IntPtr menu) {
    if (menu == IntPtr.Zero || !IsMenu(menu))
      throw new InvalidOperationException("mt5_popup_submenu_handle_invalid");
    int count = GetMenuItemCount(menu);
    if (count <= 0 || count > MAX_POPUP_MENU_ITEMS)
      throw new InvalidOperationException("mt5_popup_menu_item_count_invalid");
    MENUITEMSNAPSHOT[] items = new MENUITEMSNAPSHOT[count];
    for (int position = 0; position < count; position++)
      items[position] = ReadPopupMenuItemExact(menu, position);
    if (!IsMenu(menu) || GetMenuItemCount(menu) != count)
      throw new InvalidOperationException("mt5_popup_menu_changed");
    return items;
  }
  // Diagnostic only: unlabeled native MDI/icon items are data, never command matches.
  public sealed class TESTERMENUDIAGNOSTICITEM {
    public uint Type; public MENUITEMSNAPSHOT Item;
  }
  static TESTERMENUDIAGNOSTICITEM ReadTesterMenuDiagnosticItem(IntPtr menu, int position) {
    const uint MIIM_STATE = 0x00000001;
    const uint MIIM_ID = 0x00000002;
    const uint MIIM_SUBMENU = 0x00000004;
    const uint MIIM_DATA = 0x00000020;
    const uint MIIM_STRING = 0x00000040;
    const uint MIIM_FTYPE = 0x00000100;
    const uint MFT_SEPARATOR = 0x00000800;
    const uint MFS_DISABLED = 0x00000003;
    uint mask = MIIM_STATE | MIIM_ID | MIIM_SUBMENU | MIIM_DATA | MIIM_STRING | MIIM_FTYPE;
    MENUITEMINFO first = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask };
    if (!GetMenuItemInfo(menu, (uint)position, true, ref first) || first.cch > 511)
      throw new InvalidOperationException("mt5_tester_diagnostic_menu_item_invalid");
    bool separator = (first.fType & MFT_SEPARATOR) != 0;
    IntPtr textBuffer = IntPtr.Zero;
    try {
      const uint capacity = 512;
      int bufferBytes = checked((int)(capacity + 1) * 2);
      int sentinelOffset = checked((int)capacity * 2);
      textBuffer = Marshal.AllocHGlobal(bufferBytes);
      for (int offset = 0; offset < bufferBytes; offset++) Marshal.WriteByte(textBuffer, offset, 0);
      Marshal.WriteByte(textBuffer, sentinelOffset, 0xA5);
      Marshal.WriteByte(textBuffer, sentinelOffset + 1, 0x5A);
      MENUITEMINFO second = new MENUITEMINFO {
        cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask,
        dwTypeData=textBuffer, cch=capacity
      };
      if (!GetMenuItemInfo(menu, (uint)position, true, ref second) || second.cch > 511 ||
          second.cch != first.cch || Marshal.ReadByte(textBuffer, sentinelOffset) != 0xA5 ||
          Marshal.ReadByte(textBuffer, sentinelOffset + 1) != 0x5A ||
          first.fType != second.fType || first.fState != second.fState || first.wID != second.wID ||
          first.hSubMenu != second.hSubMenu || first.dwItemData != second.dwItemData)
        throw new InvalidOperationException("mt5_tester_diagnostic_menu_item_invalid");
      MENUITEMINFO third = new MENUITEMINFO { cbSize=(uint)Marshal.SizeOf(typeof(MENUITEMINFO)), fMask=mask };
      if (!GetMenuItemInfo(menu, (uint)position, true, ref third) || third.cch > 511 ||
          third.cch != second.cch || third.fType != second.fType || third.fState != second.fState ||
          third.wID != second.wID || third.hSubMenu != second.hSubMenu ||
          third.dwItemData != second.dwItemData)
        throw new InvalidOperationException("mt5_tester_diagnostic_menu_item_invalid");
      if (second.hSubMenu != IntPtr.Zero && !IsMenu(second.hSubMenu))
        throw new InvalidOperationException("mt5_tester_diagnostic_menu_item_invalid");
      string text = second.cch == 0 ? String.Empty : Marshal.PtrToStringUni(textBuffer, checked((int)second.cch));
      if (text == null)
        throw new InvalidOperationException("mt5_tester_diagnostic_menu_text_invalid");
      return new TESTERMENUDIAGNOSTICITEM { Type=second.fType, Item=new MENUITEMSNAPSHOT {
        Position=position, CommandId=second.wID, Text=text, State=second.fState,
        IsEnabled=(second.fState & MFS_DISABLED) == 0,
        IsSeparator=separator, HasSubmenu=second.hSubMenu != IntPtr.Zero,
        SubmenuHandle=second.hSubMenu, ItemData=second.dwItemData, TextLength=second.cch
      }};
    } finally {
      if (textBuffer != IntPtr.Zero) Marshal.FreeHGlobal(textBuffer);
    }
  }
  static TESTERMENUDIAGNOSTICITEM[] ListTesterMenuDiagnosticItems(IntPtr menu) {
    if (menu == IntPtr.Zero || !IsMenu(menu))
      throw new InvalidOperationException("mt5_tester_diagnostic_menu_invalid");
    int count = GetMenuItemCount(menu);
    if (count <= 0 || count > MAX_POPUP_MENU_ITEMS)
      throw new InvalidOperationException("mt5_tester_diagnostic_menu_count_invalid");
    TESTERMENUDIAGNOSTICITEM[] items = new TESTERMENUDIAGNOSTICITEM[count];
    for (int position=0; position<count; position++) items[position]=ReadTesterMenuDiagnosticItem(menu, position);
    if (!IsMenu(menu) || GetMenuItemCount(menu) != count)
      throw new InvalidOperationException("mt5_tester_diagnostic_menu_changed");
    return items;
  }
  public static void InvokeTesterRevealMenuExact(uint expectedProcessId, IntPtr signedRoot) {
    // Normal View > Strategy Tester command only. No tester Start is sent.
    if (GetForegroundWindow()!=signedRoot)
      throw new InvalidOperationException("mt5_tester_reveal_menu_foreground_changed");
    uint firstPid; uint firstThread=GetWindowThreadProcessId(signedRoot,out firstPid);
    TESTERVIEWMENUSNAPSHOT before=ReadTesterViewMenuExact(expectedProcessId,signedRoot);
    TESTERVIEWMENUSNAPSHOT current=ReadTesterViewMenuExact(expectedProcessId,signedRoot);
    int matchingIds=0;
    foreach (TESTERMENUDIAGNOSTICITEM row in current.ViewItems)
      if (row.Item.CommandId==32846) matchingIds++;
    if (current.TesterItem.CommandId!=32846 || matchingIds!=1 ||
        !current.ViewItem.IsEnabled || !current.TesterItem.IsEnabled ||
        before.MainMenu!=current.MainMenu || before.ViewMenu!=current.ViewMenu ||
        !SamePopupMenuItem(before.ViewItem,current.ViewItem) ||
        !SamePopupMenuItem(before.TesterItem,current.TesterItem))
      throw new InvalidOperationException("mt5_tester_reveal_menu_changed");
    uint lastPid; uint lastThread=GetWindowThreadProcessId(signedRoot,out lastPid);
    if (firstThread==0 || firstThread!=lastThread || firstPid!=expectedProcessId || lastPid!=expectedProcessId ||
        !IsWindow(signedRoot) || !IsWindowVisible(signedRoot) || !IsWindowEnabled(signedRoot) ||
        GetAncestor(signedRoot,GA_ROOT)!=signedRoot || GetWindow(signedRoot,GW_OWNER)!=IntPtr.Zero ||
        ReadWindowClassExact(signedRoot)!="MetaQuotes::MetaTrader::5.00" ||
        GetForegroundWindow()!=signedRoot || GetMenu(signedRoot)!=current.MainMenu)
      throw new InvalidOperationException("mt5_tester_reveal_menu_root_changed");
    if (!PostMessage(signedRoot,WM_COMMAND,(IntPtr)32846,IntPtr.Zero))
      throw new InvalidOperationException("mt5_tester_reveal_menu_dispatch_failed");
  }
  public sealed class TESTERWINDOWDIAGNOSTIC {
    public long handle, ownerHandle, rootHandle, topLevelHandle;
    public int controlId; public string nativeClass, titleCategory;
    public bool visible, enabled; public RECT nativeRect;
  }
  public sealed class TESTERWINDOWINVENTORY {
    public TESTERWINDOWDIAGNOSTIC[] topLevelWindows, testerControls;
    public bool truncated;
  }
  static TESTERWINDOWDIAGNOSTIC ReadTesterWindowDiagnostic(IntPtr window, uint expectedPid, IntPtr top) {
    uint pid; GetWindowThreadProcessId(window, out pid);
    if (pid != expectedPid || !IsWindow(window) || GetAncestor(window, GA_ROOT) != top)
      throw new InvalidOperationException("mt5_tester_window_diagnostic_changed");
    RECT rect; if (!GetWindowRect(window, out rect))
      throw new InvalidOperationException("mt5_tester_window_diagnostic_unreadable");
    string nativeClass=ReadWindowClassExact(window);
    if (nativeClass.Length>96) nativeClass=nativeClass.Substring(0,96);
    nativeClass=System.Text.RegularExpressions.Regex.Replace(nativeClass,"[^A-Za-z0-9_.#:-]","?");
    string category="unavailable";
    try {
      string title=ReadWindowTextExact(window);
      category=title.IndexOf("Strategy Tester",StringComparison.OrdinalIgnoreCase)>=0?"strategy_tester":
        title.IndexOf("MetaTrader",StringComparison.OrdinalIgnoreCase)>=0?"metatrader":title.Length==0?"empty":"other";
    } catch { }
    TESTERWINDOWDIAGNOSTIC result=new TESTERWINDOWDIAGNOSTIC {
      handle=window.ToInt64(),ownerHandle=GetWindow(window,GW_OWNER).ToInt64(),
      rootHandle=GetAncestor(window,GA_ROOT).ToInt64(),topLevelHandle=top.ToInt64(),
      controlId=GetDlgCtrlID(window),nativeClass=nativeClass,titleCategory=category,
      visible=IsWindowVisible(window),enabled=IsWindowEnabled(window),nativeRect=rect
    };
    GetWindowThreadProcessId(window,out pid);
    if (pid!=expectedPid || !IsWindow(window) || GetAncestor(window,GA_ROOT)!=top)
      throw new InvalidOperationException("mt5_tester_window_diagnostic_changed");
    return result;
  }
  public static TESTERWINDOWINVENTORY ReadTesterWindowsDiagnostic(uint expectedPid, IntPtr signedRoot) {
    uint pid; GetWindowThreadProcessId(signedRoot,out pid);
    if (expectedPid==0 || pid!=expectedPid || !IsWindow(signedRoot) ||
        GetAncestor(signedRoot,GA_ROOT)!=signedRoot || GetWindow(signedRoot,GW_OWNER)!=IntPtr.Zero ||
        ReadWindowClassExact(signedRoot)!="MetaQuotes::MetaTrader::5.00")
      throw new InvalidOperationException("mt5_tester_window_diagnostic_root_unverified");
    List<TESTERWINDOWDIAGNOSTIC> tops=new List<TESTERWINDOWDIAGNOSTIC>();
    List<TESTERWINDOWDIAGNOSTIC> controls=new List<TESTERWINDOWDIAGNOSTIC>();
    bool truncated=false; int visited=0,children=0;
    var timer=System.Diagnostics.Stopwatch.StartNew();
    bool enumerated=EnumWindows(delegate(IntPtr window,IntPtr ignored) {
      if (++visited>2048 || timer.ElapsedMilliseconds>2500) {truncated=true;return false;}
      uint owner; GetWindowThreadProcessId(window,out owner);
      if (owner!=expectedPid) return true;
      int controlsBefore=controls.Count;
      EnumChildWindows(window,delegate(IntPtr child,IntPtr unused) {
        if (++children>4096 || controls.Count>=32 || timer.ElapsedMilliseconds>2500) {truncated=true;return false;}
        uint childPid;GetWindowThreadProcessId(child,out childPid);
        if (childPid!=expectedPid) return true;
        int id=GetDlgCtrlID(child);
        if (id==32846 || id==16790 || id==10002 || id==10490)
          controls.Add(ReadTesterWindowDiagnostic(child,expectedPid,window));
        return true;
      },IntPtr.Zero);
      if (IsWindowVisible(window) || window==signedRoot || controls.Count>controlsBefore) {
        if (tops.Count>=16) {truncated=true;return false;}
        tops.Add(ReadTesterWindowDiagnostic(window,expectedPid,window));
      }
      return !truncated;
    },IntPtr.Zero);
    GetWindowThreadProcessId(signedRoot,out pid);
    if ((!enumerated&&!truncated) || pid!=expectedPid || !IsWindow(signedRoot) ||
        GetAncestor(signedRoot,GA_ROOT)!=signedRoot || GetWindow(signedRoot,GW_OWNER)!=IntPtr.Zero ||
        ReadWindowClassExact(signedRoot)!="MetaQuotes::MetaTrader::5.00")
      throw new InvalidOperationException("mt5_tester_window_diagnostic_changed");
    return new TESTERWINDOWINVENTORY {topLevelWindows=tops.ToArray(),testerControls=controls.ToArray(),truncated=truncated};
  }
  public sealed class TESTERVIEWMENUSNAPSHOT {
    public IntPtr MainMenu; public IntPtr ViewMenu;
    public MENUITEMSNAPSHOT ViewItem; public MENUITEMSNAPSHOT TesterItem;
    public TESTERMENUDIAGNOSTICITEM[] TopItems; public TESTERMENUDIAGNOSTICITEM[] ViewItems;
  }
  static string TesterMenuLabel(string text) {
    return (text ?? String.Empty).Split('\t')[0].Replace("&", "").Trim();
  }
  public static TESTERVIEWMENUSNAPSHOT ReadTesterViewMenuExact(uint expectedProcessId, IntPtr expectedRoot) {
    uint owner; GetWindowThreadProcessId(expectedRoot, out owner);
    if (expectedProcessId == 0 || owner != expectedProcessId || !IsWindow(expectedRoot) ||
        !IsWindowVisible(expectedRoot) || !IsWindowEnabled(expectedRoot) ||
        GetAncestor(expectedRoot, GA_ROOT) != expectedRoot || GetWindow(expectedRoot, GW_OWNER) != IntPtr.Zero ||
        ReadWindowClassExact(expectedRoot) != "MetaQuotes::MetaTrader::5.00")
      throw new InvalidOperationException("mt5_tester_menu_root_unverified");
    IntPtr mainMenu = GetMenu(expectedRoot);
    if (mainMenu == IntPtr.Zero || !IsMenu(mainMenu)) throw new InvalidOperationException("mt5_tester_native_menu_unavailable");
    MENUITEMSNAPSHOT view = null, tester = null;
    TESTERMENUDIAGNOSTICITEM[] topItems = ListTesterMenuDiagnosticItems(mainMenu);
    foreach (TESTERMENUDIAGNOSTICITEM observed in topItems) {
      MENUITEMSNAPSHOT item=observed.Item;
      if (TesterMenuLabel(item.Text) != "View" || item.IsSeparator || !item.HasSubmenu) continue;
      if (view != null) throw new InvalidOperationException("mt5_tester_view_menu_ambiguous");
      view = item;
    }
    if (view == null || view.Text.Length > 128) throw new InvalidOperationException("mt5_tester_view_menu_unavailable");
    TESTERMENUDIAGNOSTICITEM[] viewItems = ListTesterMenuDiagnosticItems(view.SubmenuHandle);
    foreach (TESTERMENUDIAGNOSTICITEM observed in viewItems) {
      MENUITEMSNAPSHOT item=observed.Item;
      if (TesterMenuLabel(item.Text) != "Strategy Tester" || item.IsSeparator || item.HasSubmenu) continue;
      if (tester != null) throw new InvalidOperationException("mt5_tester_menu_command_ambiguous");
      tester = item;
    }
    if (tester == null || tester.CommandId == 0 || tester.CommandId == UInt32.MaxValue || tester.Text.Length > 128)
      throw new InvalidOperationException("mt5_tester_menu_command_unavailable");
    TESTERMENUDIAGNOSTICITEM viewAfter=ReadTesterMenuDiagnosticItem(mainMenu, view.Position);
    TESTERMENUDIAGNOSTICITEM testerAfter=ReadTesterMenuDiagnosticItem(view.SubmenuHandle, tester.Position);
    GetWindowThreadProcessId(expectedRoot, out owner);
    if (owner != expectedProcessId || !IsWindow(expectedRoot) || GetMenu(expectedRoot) != mainMenu ||
        topItems[view.Position].Type != viewAfter.Type || viewItems[tester.Position].Type != testerAfter.Type ||
        !SamePopupMenuItem(view, viewAfter.Item) || !SamePopupMenuItem(tester, testerAfter.Item))
      throw new InvalidOperationException("mt5_tester_menu_changed");
    return new TESTERVIEWMENUSNAPSHOT { MainMenu=mainMenu, ViewMenu=view.SubmenuHandle, ViewItem=view, TesterItem=tester, TopItems=topItems, ViewItems=viewItems };
  }
  static MENUITEMSNAPSHOT FindPopupSubmenuExact(MENUITEMSNAPSHOT[] items, string expectedText) {
    if (items == null || String.IsNullOrWhiteSpace(expectedText) || expectedText.Length > 128)
      throw new InvalidOperationException("mt5_popup_submenu_invalid");
    MENUITEMSNAPSHOT match = null;
    int textMatches = 0;
    for (int index = 0; index < items.Length; index++) {
      MENUITEMSNAPSHOT item = items[index];
      if (item.HasSubmenu && String.Equals(item.Text, expectedText, StringComparison.Ordinal)) {
        match = item;
        textMatches++;
      }
    }
    if (textMatches != 1 || match == null || !match.IsEnabled || match.IsSeparator ||
        !match.HasSubmenu || match.SubmenuHandle == IntPtr.Zero || !IsMenu(match.SubmenuHandle))
      throw new InvalidOperationException("mt5_popup_submenu_invalid");
    int handleMatches = 0;
    for (int index = 0; index < items.Length; index++)
      if (items[index].HasSubmenu && items[index].SubmenuHandle == match.SubmenuHandle) handleMatches++;
    if (handleMatches != 1)
      throw new InvalidOperationException("mt5_popup_submenu_invalid");
    return match;
  }
  static MENUITEMSNAPSHOT FindPopupSubmenuCommandExact(MENUITEMSNAPSHOT[] items, string expectedParentText, string expectedText, uint expectedCommandId) {
    MENUITEMSNAPSHOT parent = FindPopupSubmenuExact(items, expectedParentText);
    MENUITEMSNAPSHOT[] first = ListPopupMenuHandleItemsExact(parent.SubmenuHandle);
    MENUITEMSNAPSHOT[] second = ListPopupMenuHandleItemsExact(parent.SubmenuHandle);
    if (!SamePopupMenuItems(first, second))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    return FindPopupMenuCommandExact(second, expectedText, expectedCommandId);
  }
  public static MENUITEMSNAPSHOT AssertPopupSubmenuCommandFromTokenExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot, string expectedParentText, string expectedText, uint expectedCommandId) {
    POPUPMENUTOKEN current = AssertPopupMenuTokenExact(expected, expectedProcessId, expectedRoot);
    MENUITEMSNAPSHOT command = FindPopupSubmenuCommandExact(current.Items, expectedParentText, expectedText, expectedCommandId);
    AssertPopupMenuTokenExact(current, expectedProcessId, expectedRoot);
    return command;
  }
  static IntPtr FindPopupWindowForMenuHandleExact(IntPtr expectedMenu, POPUPMENUTOKEN parent, uint expectedProcessId) {
    if (expectedMenu == IntPtr.Zero || !IsMenu(expectedMenu) || parent == null ||
        parent.PopupWindow == IntPtr.Zero || parent.MenuThreadId == 0 || expectedProcessId == 0)
      throw new InvalidOperationException("mt5_popup_submenu_handle_invalid");
    List<IntPtr> matches = new List<IntPtr>();
    bool enumerated = EnumWindows(delegate(IntPtr window, IntPtr ignored) {
      if (window == parent.PopupWindow || !IsWindowVisible(window) || !IsWindowEnabled(window)) return true;
      uint processId;
      uint threadId = GetWindowThreadProcessId(window, out processId);
      if (processId != expectedProcessId || threadId != parent.MenuThreadId) return true;
      StringBuilder className = new StringBuilder(64);
      if (GetClassName(window, className, className.Capacity) <= 0 ||
          !String.Equals(className.ToString(), "#32768", StringComparison.Ordinal)) return true;
      IntPtr observedMenu;
      uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT;
      if (SendMessageTimeout(window, MN_GETHMENU, IntPtr.Zero, IntPtr.Zero, flags, 250, out observedMenu) != IntPtr.Zero &&
          observedMenu == expectedMenu) matches.Add(window);
      return true;
    }, IntPtr.Zero);
    if (!enumerated || matches.Count > 1)
      throw new InvalidOperationException("mt5_popup_submenu_host_ambiguous");
    return matches.Count == 1 ? matches[0] : IntPtr.Zero;
  }
  public static MENUITEMSNAPSHOT InvokePopupSubmenuCommandExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot, string expectedParentText, string expectedText, uint expectedCommandId) {
    const uint MFS_HILITE = 0x00000080;
    POPUPMENUTOKEN current = AssertPopupMenuTokenExact(expected, expectedProcessId, expectedRoot);
    MENUITEMSNAPSHOT parent = FindPopupSubmenuExact(current.Items, expectedParentText);
    MENUITEMSNAPSHOT[] submenuFirst = ListPopupMenuHandleItemsExact(parent.SubmenuHandle);
    MENUITEMSNAPSHOT[] submenuSecond = ListPopupMenuHandleItemsExact(parent.SubmenuHandle);
    if (!SamePopupMenuItems(submenuFirst, submenuSecond))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    FindPopupMenuCommandExact(submenuSecond, expectedText, expectedCommandId);
    AssertPopupMenuTokenExact(current, expectedProcessId, expectedRoot);
    RECT itemRect; RECT menuRect;
    if (!GetMenuItemRect(current.CommandOwner, current.MenuHandle, (uint)parent.Position, out itemRect) ||
        !GetWindowRect(current.PopupWindow, out menuRect) || itemRect.Right <= itemRect.Left ||
        itemRect.Bottom <= itemRect.Top || itemRect.Left < menuRect.Left || itemRect.Top < menuRect.Top ||
        itemRect.Right > menuRect.Right || itemRect.Bottom > menuRect.Bottom ||
        itemRect.Right - itemRect.Left > 2048 || itemRect.Bottom - itemRect.Top > 256)
      throw new InvalidOperationException("mt5_popup_menu_item_rect_invalid");
    IntPtr messageResult;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT;
    if (SendMessageTimeout(current.PopupWindow, MN_SELECTITEM, (IntPtr)parent.Position, IntPtr.Zero,
        flags, 1500, out messageResult) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_popup_menu_selection_failed");
    MENUITEMSNAPSHOT[] highlightedFirst = ListPopupMenuItemsExact(current.PopupWindow, expectedProcessId, expectedRoot);
    MENUITEMSNAPSHOT[] highlightedSecond = ListPopupMenuItemsExact(current.PopupWindow, expectedProcessId, expectedRoot);
    if (highlightedFirst.Length != expected.Items.Length || highlightedSecond.Length != expected.Items.Length)
      throw new InvalidOperationException("mt5_popup_menu_changed");
    int highlightedCount = 0;
    for (int index = 0; index < expected.Items.Length; index++) {
      if (!SamePopupMenuItemIgnoringHighlight(expected.Items[index], highlightedFirst[index]) ||
          !SamePopupMenuItem(highlightedFirst[index], highlightedSecond[index]))
        throw new InvalidOperationException("mt5_popup_menu_changed");
      if ((highlightedFirst[index].State & MFS_HILITE) != 0) {
        highlightedCount++;
        if (index != parent.Position) throw new InvalidOperationException("mt5_popup_menu_selection_failed");
      }
    }
    if (highlightedCount != 1 || current.CommandOwner != AssertPopupMenuOwner(current.PopupWindow, expectedProcessId, expectedRoot) ||
        current.MenuHandle != GetPopupMenuHandleExact(current.PopupWindow, expectedProcessId, expectedRoot) ||
        !IsMenu(parent.SubmenuHandle))
      throw new InvalidOperationException("mt5_popup_menu_selection_failed");
    IntPtr submenuWindow = IntPtr.Zero;
    bool leafDispatchAttempted = false;
    try {
      if (SendMessageTimeout(current.PopupWindow, WM_KEYDOWN, (IntPtr)VK_RIGHT, (IntPtr)1,
          flags, 1500, out messageResult) == IntPtr.Zero)
        throw new InvalidOperationException("mt5_popup_submenu_open_failed");
      if (SendMessageTimeout(current.PopupWindow, WM_KEYUP, (IntPtr)VK_RIGHT,
          new IntPtr(unchecked((int)0xC0000001)), flags, 1500, out messageResult) == IntPtr.Zero)
        throw new InvalidOperationException("mt5_popup_submenu_open_failed");
      DateTime deadline = DateTime.UtcNow.AddSeconds(2);
      do {
        submenuWindow = FindPopupWindowForMenuHandleExact(parent.SubmenuHandle, current, expectedProcessId);
        if (submenuWindow != IntPtr.Zero) break;
        System.Threading.Thread.Sleep(10);
      } while (DateTime.UtcNow < deadline);
      if (submenuWindow == IntPtr.Zero)
        throw new InvalidOperationException("mt5_popup_submenu_open_failed");
      POPUPMENUTOKEN parentAfterOpen = CapturePopupMenuTokenExact(current.PopupWindow, expectedProcessId, expectedRoot);
      if (!SamePopupMenuTokenIgnoringHighlight(expected, parentAfterOpen))
        throw new InvalidOperationException("mt5_popup_menu_changed");
      POPUPMENUTOKEN submenuToken = CapturePopupMenuTokenExact(submenuWindow, expectedProcessId, expectedRoot);
      if (submenuToken.MenuHandle != parent.SubmenuHandle || submenuToken.CommandOwner != current.CommandOwner ||
          submenuToken.MenuThreadId != current.MenuThreadId ||
          !SamePopupSubmenuItemsAfterOpen(submenuSecond, submenuToken.Items))
        throw new InvalidOperationException("mt5_popup_submenu_changed");
      FindPopupMenuCommandExact(submenuToken.Items, expectedText, expectedCommandId);
      leafDispatchAttempted = true;
      MENUITEMSNAPSHOT invoked = InvokePopupMenuCommandExact(submenuToken, expectedProcessId, expectedRoot, expectedText, expectedCommandId);
      DateTime parentDeadline = DateTime.UtcNow.AddSeconds(2);
      while (IsWindow(current.PopupWindow) && IsWindowVisible(current.PopupWindow) && DateTime.UtcNow < parentDeadline)
        System.Threading.Thread.Sleep(10);
      if (IsWindow(current.PopupWindow) && IsWindowVisible(current.PopupWindow))
        throw new InvalidOperationException("mt5_popup_menu_command_dispatch_ambiguous");
      return invoked;
    } catch {
      if (submenuWindow == IntPtr.Zero) {
        try { submenuWindow = FindPopupWindowForMenuHandleExact(parent.SubmenuHandle, current, expectedProcessId); }
        catch { submenuWindow = IntPtr.Zero; }
      }
      // Once the leaf dispatch may have been queued, never send Escape into
      // that menu loop: doing so could race or alter the exactly-once command.
      if (!leafDispatchAttempted && submenuWindow != IntPtr.Zero && IsWindow(submenuWindow) && IsWindowVisible(submenuWindow)) {
        try {
          if (SendMessageTimeout(submenuWindow, WM_KEYDOWN, (IntPtr)VK_ESCAPE, (IntPtr)1,
              flags, 500, out messageResult) != IntPtr.Zero)
            SendMessageTimeout(submenuWindow, WM_KEYUP, (IntPtr)VK_ESCAPE,
              new IntPtr(unchecked((int)0xC0000001)), flags, 500, out messageResult);
          DateTime cleanupDeadline = DateTime.UtcNow.AddSeconds(1);
          while (IsWindow(submenuWindow) && IsWindowVisible(submenuWindow) && DateTime.UtcNow < cleanupDeadline)
            System.Threading.Thread.Sleep(10);
        } catch { }
      }
      throw;
    }
  }
  public static MENUITEMSNAPSHOT AssertPopupMenuCommandFromTokenExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    POPUPMENUTOKEN current = AssertPopupMenuTokenExact(expected, expectedProcessId, expectedRoot);
    return FindPopupMenuCommandExact(current.Items, expectedText, expectedCommandId);
  }
  static void AssertReboundPopupMenuTokenIdentityExact(POPUPMENUTOKEN current, uint expectedProcessId, IntPtr expectedRoot) {
    if (current == null || current.PopupWindow == IntPtr.Zero || current.MenuHandle == IntPtr.Zero ||
        current.CommandOwner == IntPtr.Zero || current.MenuThreadId == 0 || current.Items == null)
      throw new InvalidOperationException("mt5_popup_menu_token_invalid");
    uint ownerPid;
    uint menuThread = GetWindowThreadProcessId(current.PopupWindow, out ownerPid);
    if (menuThread == 0 || ownerPid != expectedProcessId || menuThread != current.MenuThreadId ||
        current.CommandOwner != AssertPopupMenuOwner(current.PopupWindow, expectedProcessId, expectedRoot) ||
        current.MenuHandle != GetPopupMenuHandleExact(current.PopupWindow, expectedProcessId, expectedRoot) ||
        !IsMenu(current.MenuHandle))
      throw new InvalidOperationException("mt5_popup_menu_changed");
  }
  public static MENUITEMSNAPSHOT AssertPopupMenuCommandFromReboundTokenExact(POPUPMENUTOKEN current, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    AssertReboundPopupMenuTokenIdentityExact(current, expectedProcessId, expectedRoot);
    return FindPopupMenuCommandExact(current.Items, expectedText, expectedCommandId);
  }
  public static MENUITEMSNAPSHOT AssertPopupMenuCommandExact(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    POPUPMENUTOKEN first = CapturePopupMenuTokenExact(menuWindow, expectedProcessId, expectedRoot);
    POPUPMENUTOKEN second = AssertPopupMenuTokenExact(first, expectedProcessId, expectedRoot);
    return FindPopupMenuCommandExact(second.Items, expectedText, expectedCommandId);
  }
  static MENUITEMSNAPSHOT InvokePopupMenuCommandCurrentTokenExact(POPUPMENUTOKEN current, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    const uint MFS_HILITE = 0x00000080;
    MENUITEMSNAPSHOT exact = FindPopupMenuCommandExact(current.Items, expectedText, expectedCommandId);
    IntPtr menuWindow = current.PopupWindow;
    IntPtr menu = current.MenuHandle;
    IntPtr commandOwner = current.CommandOwner;
    RECT itemRect; RECT menuRect;
    if (!GetMenuItemRect(commandOwner, menu, (uint)exact.Position, out itemRect) ||
        !GetWindowRect(menuWindow, out menuRect) || itemRect.Right <= itemRect.Left ||
        itemRect.Bottom <= itemRect.Top || itemRect.Left < menuRect.Left || itemRect.Top < menuRect.Top ||
        itemRect.Right > menuRect.Right || itemRect.Bottom > menuRect.Bottom ||
        itemRect.Right - itemRect.Left > 2048 || itemRect.Bottom - itemRect.Top > 256)
      throw new InvalidOperationException("mt5_popup_menu_item_rect_invalid");
    IntPtr messageResult;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT;
    if (SendMessageTimeout(menuWindow, MN_SELECTITEM, (IntPtr)exact.Position, IntPtr.Zero,
        flags, 1500, out messageResult) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_popup_menu_selection_failed");
    MENUITEMSNAPSHOT[] highlightedFirst = ListPopupMenuItemsExact(menuWindow, expectedProcessId, expectedRoot);
    MENUITEMSNAPSHOT[] highlightedSecond = ListPopupMenuItemsExact(menuWindow, expectedProcessId, expectedRoot);
    if (highlightedFirst.Length != current.Items.Length || highlightedSecond.Length != current.Items.Length)
      throw new InvalidOperationException("mt5_popup_menu_changed");
    int highlightedCount = 0;
    for (int index = 0; index < current.Items.Length; index++) {
      if (!SamePopupMenuItemIgnoringHighlight(current.Items[index], highlightedFirst[index]) ||
          !SamePopupMenuItem(highlightedFirst[index], highlightedSecond[index]))
        throw new InvalidOperationException("mt5_popup_menu_changed");
      if ((highlightedFirst[index].State & MFS_HILITE) != 0) {
        highlightedCount++;
        if (index != exact.Position) throw new InvalidOperationException("mt5_popup_menu_selection_failed");
      }
    }
    if (highlightedCount != 1 ||
        commandOwner != AssertPopupMenuOwner(menuWindow, expectedProcessId, expectedRoot) ||
        menu != GetPopupMenuHandleExact(menuWindow, expectedProcessId, expectedRoot) ||
        !IsMenu(menu))
      throw new InvalidOperationException("mt5_popup_menu_selection_failed");
    MENUITEMSNAPSHOT immediatelyBefore = FindPopupMenuCommandExact(highlightedSecond, expectedText, expectedCommandId);
    if (immediatelyBefore.Position != exact.Position || (immediatelyBefore.State & MFS_HILITE) == 0)
      throw new InvalidOperationException("mt5_popup_menu_selection_failed");
    // Queue exactly one balanced Enter press after the complete popup identity
    // and highlight have been rebound.  A synchronous send is not valid
    // evidence here: modern MT5 can enter an owned modal file dialog before
    // returning, so SendMessageTimeout may expire after the exact command was
    // already consumed.  WM_KEYUP uses repeat=1 plus previous/transition bits.
    // If the popup is destroyed between the two posts, the keydown was already
    // consumed and no popup-local key state remains to release.
    if (!PostMessage(menuWindow, WM_KEYDOWN, (IntPtr)VK_RETURN, (IntPtr)1))
      throw new InvalidOperationException("mt5_popup_menu_command_dispatch_ambiguous");
    if (!PostMessage(menuWindow, WM_KEYUP, (IntPtr)VK_RETURN,
        new IntPtr(unchecked((int)0xC0000001))) && IsWindow(menuWindow) && IsWindowVisible(menuWindow))
      throw new InvalidOperationException("mt5_popup_menu_command_dispatch_ambiguous");
    DateTime deadline = DateTime.UtcNow.AddSeconds(2);
    while (IsWindow(menuWindow) && IsWindowVisible(menuWindow) && DateTime.UtcNow < deadline)
      System.Threading.Thread.Sleep(10);
    if (IsWindow(menuWindow) && IsWindowVisible(menuWindow))
      throw new InvalidOperationException("mt5_popup_menu_command_dispatch_ambiguous");
    return immediatelyBefore;
  }
  public static MENUITEMSNAPSHOT InvokePopupMenuCommandExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    POPUPMENUTOKEN current = AssertPopupMenuTokenExact(expected, expectedProcessId, expectedRoot);
    return InvokePopupMenuCommandCurrentTokenExact(current, expectedProcessId, expectedRoot, expectedText, expectedCommandId);
  }
  public static MENUITEMSNAPSHOT InvokePopupMenuCommandFromReboundTokenExact(POPUPMENUTOKEN current, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    AssertReboundPopupMenuTokenIdentityExact(current, expectedProcessId, expectedRoot);
    return InvokePopupMenuCommandCurrentTokenExact(current, expectedProcessId, expectedRoot, expectedText, expectedCommandId);
  }
  public static MENUITEMSNAPSHOT InvokePopupMenuCommandExact(IntPtr menuWindow, uint expectedProcessId, IntPtr expectedRoot, string expectedText, uint expectedCommandId) {
    POPUPMENUTOKEN token = CapturePopupMenuTokenExact(menuWindow, expectedProcessId, expectedRoot);
    return InvokePopupMenuCommandExact(token, expectedProcessId, expectedRoot, expectedText, expectedCommandId);
  }
  public static void OpenInputsContextMenuExact(IntPtr list, uint expectedProcessId, IntPtr expectedRoot) {
    // The keyboard-position context menu belongs to whichever native control
    // owns focus.  Re-prove the exact Inputs list/root/thread/control-id binding
    // at the final native boundary so a neighbouring list can never consume it.
    AssertListFocusExact(list, expectedProcessId, expectedRoot, 10494);
    // WM_CONTEXTMENU is a pointer-free system message.  The documented -1
    // coordinate requests the control's keyboard context-menu position; the
    // exact bound list is both target and wParam, so no global input is used.
    // Post instead of synchronously waiting: the receiver enters a modal menu
    // loop and a SendMessageTimeout can expire after the popup already exists.
    if (!PostMessage(list, WM_CONTEXTMENU, list, new IntPtr(-1)))
      throw new InvalidOperationException("mt5_inputs_context_menu_failed");
  }
  static void AssertExactListBinding(IntPtr list, uint expectedProcessId, IntPtr expectedRoot, int expectedControlId) {
    if (list == IntPtr.Zero || expectedProcessId == 0 || expectedRoot == IntPtr.Zero ||
        expectedControlId <= 0 || !IsWindow(list) || !IsWindow(expectedRoot) ||
        !IsWindowVisible(list) || !IsWindowEnabled(list))
      throw new InvalidOperationException("mt5_results_list_invalid");
    uint owner; uint rootOwner;
    uint listThread = GetWindowThreadProcessId(list, out owner);
    uint rootThread = GetWindowThreadProcessId(expectedRoot, out rootOwner);
    StringBuilder className = new StringBuilder(64);
    if (listThread == 0 || rootThread == 0 || owner != expectedProcessId || rootOwner != expectedProcessId ||
        listThread != rootThread || GetAncestor(list, GA_ROOT) != expectedRoot ||
        GetClassName(list, className, className.Capacity) <= 0 ||
        !String.Equals(className.ToString(), "SysListView32", StringComparison.Ordinal) ||
        GetDlgCtrlID(list) != expectedControlId || (GetWindowLong(list, GWL_STYLE) & WS_DISABLED) != 0)
      throw new InvalidOperationException("mt5_results_list_invalid");
  }
  public static void AssertListFocusExact(IntPtr list, uint expectedProcessId, IntPtr expectedRoot, int expectedControlId) {
    AssertExactListBinding(list, expectedProcessId, expectedRoot, expectedControlId);
    if (GetForegroundWindow() != expectedRoot)
      throw new InvalidOperationException("mt5_results_list_focus_foreground_invalid");
    uint owner;
    uint targetThread = GetWindowThreadProcessId(list, out owner);
    int infoSize = Marshal.SizeOf(typeof(GUITHREADINFO));
    if (targetThread == 0 || owner != expectedProcessId || infoSize != (IntPtr.Size == 8 ? 72 : 48))
      throw new InvalidOperationException("mt5_results_list_focus_owner_invalid");
    GUITHREADINFO info = new GUITHREADINFO { cbSize = (uint)infoSize };
    if (!GetGUIThreadInfo(targetThread, ref info) || info.hwndActive != expectedRoot || info.hwndFocus != list)
      throw new InvalidOperationException("mt5_results_list_focus_readback_failed");
    AssertExactListBinding(list, expectedProcessId, expectedRoot, expectedControlId);
  }
  public static void FocusListExact(IntPtr list, uint expectedProcessId, IntPtr expectedRoot, int expectedControlId) {
    AssertExactListBinding(list, expectedProcessId, expectedRoot, expectedControlId);
    if (GetForegroundWindow() != expectedRoot)
      throw new InvalidOperationException("mt5_results_list_focus_foreground_invalid");
    uint owner;
    uint targetThread = GetWindowThreadProcessId(list, out owner);
    if (targetThread == 0 || owner != expectedProcessId)
      throw new InvalidOperationException("mt5_results_list_focus_owner_invalid");
    uint currentThread = GetCurrentThreadId();
    bool attached = false;
    try {
      if (currentThread != targetThread) {
        attached = AttachThreadInput(currentThread, targetThread, true);
        if (!attached) throw new InvalidOperationException("mt5_results_list_focus_attach_failed");
      }
      AssertExactListBinding(list, expectedProcessId, expectedRoot, expectedControlId);
      if (GetForegroundWindow() != expectedRoot)
        throw new InvalidOperationException("mt5_results_list_focus_foreground_invalid");
      SetFocus(list);
      AssertListFocusExact(list, expectedProcessId, expectedRoot, expectedControlId);
    } finally {
      if (attached && !AttachThreadInput(currentThread, targetThread, false))
        throw new InvalidOperationException("mt5_results_list_focus_detach_failed");
    }
    AssertListFocusExact(list, expectedProcessId, expectedRoot, expectedControlId);
  }
  public static void OpenListContextMenuExact(IntPtr list, uint expectedProcessId, IntPtr expectedRoot, int expectedControlId) {
    AssertListFocusExact(list, expectedProcessId, expectedRoot, expectedControlId);
    // The keyboard-position form of WM_CONTEXTMENU is pointer-free.  It is
    // posted only to the exact, focused native results list, never through
    // global SendKeys or the cursor.
    if (!PostMessage(list, WM_CONTEXTMENU, list, new IntPtr(-1)))
      throw new InvalidOperationException("mt5_results_context_menu_failed");
  }
  public static void DismissPopupMenuExact(POPUPMENUTOKEN expected, uint expectedProcessId, IntPtr expectedRoot) {
    if (expected == null || expected.PopupWindow == IntPtr.Zero) return;
    if (!IsWindow(expected.PopupWindow) || !IsWindowVisible(expected.PopupWindow)) return;
    // A failed command attempt may have selected (highlighted) the exact menu
    // item before dispatch stopped.  Highlight is transient presentation state,
    // not command identity.  Permit only that one-bit difference so cleanup can
    // close the still-bound menu without masking the original failure.
    POPUPMENUTOKEN current = CapturePopupMenuTokenExact(expected.PopupWindow, expectedProcessId, expectedRoot);
    if (!SamePopupMenuTokenIgnoringHighlight(expected, current))
      throw new InvalidOperationException("mt5_popup_menu_changed");
    IntPtr result;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT;
    if (SendMessageTimeout(current.PopupWindow, WM_KEYDOWN, (IntPtr)VK_ESCAPE, (IntPtr)1,
        flags, 1500, out result) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_popup_menu_dismiss_failed");
    if (SendMessageTimeout(current.PopupWindow, WM_KEYUP, (IntPtr)VK_ESCAPE,
        new IntPtr(unchecked((int)0xC0000001)), flags, 1500, out result) == IntPtr.Zero &&
        IsWindow(current.PopupWindow) && IsWindowVisible(current.PopupWindow))
      throw new InvalidOperationException("mt5_popup_menu_dismiss_failed");
    DateTime deadline = DateTime.UtcNow.AddSeconds(2);
    while (IsWindow(current.PopupWindow) && IsWindowVisible(current.PopupWindow) && DateTime.UtcNow < deadline)
      System.Threading.Thread.Sleep(10);
    if (IsWindow(current.PopupWindow) && IsWindowVisible(current.PopupWindow))
      throw new InvalidOperationException("mt5_popup_menu_dismiss_failed");
  }
  static IntPtr OpenTreeProcess(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    IntPtr process = OpenProcess(PROCESS_ACCESS, false, expectedProcessId);
    if (process == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_process_open_failed");
    bool currentWow64; bool targetWow64;
    if (!IsWow64Process(GetCurrentProcess(), out currentWow64) || !IsWow64Process(process, out targetWow64) || currentWow64 != targetWow64) {
      CloseHandle(process);
      throw new InvalidOperationException("mt5_tree_process_bitness_mismatch");
    }
    return process;
  }
  static IntPtr SendRemoteTreeMessage(IntPtr tree, int message, IntPtr wParam, IntPtr lParam) {
    IntPtr result;
    uint flags = SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_NOTIMEOUTIFNOTHUNG;
    if (SendMessageTimeout(tree, message, wParam, lParam, flags, 1500, out result) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_tree_message_timeout");
    return result;
  }
  static void WriteRemoteExact(IntPtr process, IntPtr remote, byte[] bytes, string code) {
    UIntPtr written;
    if (!WriteProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out written) || written.ToUInt64() != (ulong)bytes.Length)
      throw new InvalidOperationException(code);
  }
  static byte[] ReadRemoteExact(IntPtr process, IntPtr remote, int size, string code) {
    byte[] bytes = new byte[size]; UIntPtr read;
    if (!ReadProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out read) || read.ToUInt64() != (ulong)bytes.Length)
      throw new InvalidOperationException(code);
    return bytes;
  }
  static string ReadTreeItemText(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, IntPtr process, IntPtr itemRemote, IntPtr textRemote, IntPtr item) {
    if (item == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_item_invalid");
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    int textBytes = checked(TREE_TEXT_CHARS * 2);
    WriteRemoteExact(process, textRemote, new byte[textBytes], "mt5_tree_text_clear_failed");
    TVITEM value = new TVITEM { mask = TVIF_TEXT, hItem = item, pszText = textRemote, cchTextMax = TREE_TEXT_CHARS };
    WriteRemoteExact(process, itemRemote, TreeItemBytes(value), "mt5_tree_item_write_failed");
    if (SendRemoteTreeMessage(tree, TVM_GETITEMW, IntPtr.Zero, itemRemote) == IntPtr.Zero)
      throw new InvalidOperationException("mt5_tree_item_read_failed");
    byte[] raw = ReadRemoteExact(process, textRemote, textBytes, "mt5_tree_text_read_failed");
    int end = -1;
    for (int offset = 0; offset + 1 < raw.Length; offset += 2) {
      if (raw[offset] == 0 && raw[offset + 1] == 0) { end = offset; break; }
    }
    if (end <= 0) throw new InvalidOperationException("mt5_tree_text_invalid");
    string text = Encoding.Unicode.GetString(raw, 0, end);
    if (String.IsNullOrWhiteSpace(text) || text.Length >= TREE_TEXT_CHARS || text.IndexOf('\0') >= 0)
      throw new InvalidOperationException("mt5_tree_text_invalid");
    return text;
  }
  static IntPtr FindRootTreeItemExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, IntPtr process, IntPtr itemRemote, IntPtr textRemote, string expected) {
    if (String.IsNullOrWhiteSpace(expected) || expected.Length >= TREE_TEXT_CHARS)
      throw new InvalidOperationException("mt5_tree_expected_text_invalid");
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    // TVM_GETNEXTITEM consumes opaque HTREEITEM values by value; unlike
    // TVM_GETITEMW, these lParams are not caller-owned memory pointers.
    IntPtr current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_ROOT, IntPtr.Zero);
    IntPtr match = IntPtr.Zero; int matchCount = 0; int visited = 0;
    System.Collections.Generic.HashSet<long> seen = new System.Collections.Generic.HashSet<long>();
    while (current != IntPtr.Zero && visited < MAX_ROOT_TREE_ITEMS) {
      if (!seen.Add(current.ToInt64())) throw new InvalidOperationException("mt5_tree_traversal_cycle");
      string text = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, current);
      if (String.Equals(text, expected, StringComparison.Ordinal)) { match = current; matchCount++; }
      visited++;
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, current);
    }
    if (current != IntPtr.Zero) throw new InvalidOperationException("mt5_tree_traversal_limit");
    if (matchCount != 1 || match == IntPtr.Zero)
      throw new InvalidOperationException(matchCount == 0 ? "mt5_tree_item_missing" : "mt5_tree_item_ambiguous");
    return match;
  }
  static IntPtr GetSingleRootTreeItem(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    IntPtr root = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_ROOT, IntPtr.Zero);
    if (root == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_item_missing");
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    IntPtr next = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, root);
    if (next != IntPtr.Zero) throw new InvalidOperationException("mt5_tree_root_ambiguous");
    return root;
  }
  static IntPtr FindDirectChildTreeItemExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, IntPtr process, IntPtr itemRemote, IntPtr textRemote, IntPtr parent, string expected) {
    if (parent == IntPtr.Zero || String.IsNullOrWhiteSpace(expected) || expected.Length >= TREE_TEXT_CHARS)
      throw new InvalidOperationException("mt5_tree_expected_text_invalid");
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    IntPtr current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CHILD, parent);
    IntPtr match = IntPtr.Zero; int matchCount = 0; int visited = 0;
    System.Collections.Generic.HashSet<long> seen = new System.Collections.Generic.HashSet<long>();
    while (current != IntPtr.Zero && visited < MAX_ROOT_TREE_ITEMS) {
      if (!seen.Add(current.ToInt64())) throw new InvalidOperationException("mt5_tree_traversal_cycle");
      string text = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, current);
      if (String.Equals(text, expected, StringComparison.Ordinal)) { match = current; matchCount++; }
      visited++;
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, current);
    }
    if (current != IntPtr.Zero) throw new InvalidOperationException("mt5_tree_traversal_limit");
    if (matchCount != 1 || match == IntPtr.Zero)
      throw new InvalidOperationException(matchCount == 0 ? "mt5_tree_item_missing" : "mt5_tree_item_ambiguous");
    return match;
  }
  static TREEITEMMATCH FindRootOrSingleRootChildExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, IntPtr process, IntPtr itemRemote, IntPtr textRemote, string expected) {
    try {
      return new TREEITEMMATCH { item = FindRootTreeItemExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, expected), parent = IntPtr.Zero };
    } catch (InvalidOperationException error) {
      if (!String.Equals(error.Message, "mt5_tree_item_missing", StringComparison.Ordinal)) throw;
    }
    IntPtr parent = GetSingleRootTreeItem(tree, expectedProcessId, expectedRoot);
    IntPtr child = FindDirectChildTreeItemExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, parent, expected);
    return new TREEITEMMATCH { item = child, parent = parent };
  }
  public static string[] ListRootTreeItemTexts(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      IntPtr current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_ROOT, IntPtr.Zero);
      int visited = 0;
      System.Collections.Generic.HashSet<long> seen = new System.Collections.Generic.HashSet<long>();
      System.Collections.Generic.List<string> labels = new System.Collections.Generic.List<string>();
      while (current != IntPtr.Zero && visited < MAX_ROOT_TREE_ITEMS) {
        if (!seen.Add(current.ToInt64())) throw new InvalidOperationException("mt5_tree_traversal_cycle");
        labels.Add(ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, current));
        visited++;
        AssertRemoteTree(tree, expectedProcessId, expectedRoot);
        current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, current);
      }
      if (current != IntPtr.Zero) throw new InvalidOperationException("mt5_tree_traversal_limit");
      return labels.ToArray();
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static string[] ListSingleRootDirectChildItemTexts(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      IntPtr parent = GetSingleRootTreeItem(tree, expectedProcessId, expectedRoot);
      IntPtr current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CHILD, parent);
      int visited = 0;
      System.Collections.Generic.HashSet<long> seen = new System.Collections.Generic.HashSet<long>();
      System.Collections.Generic.List<string> labels = new System.Collections.Generic.List<string>();
      while (current != IntPtr.Zero && visited < MAX_ROOT_TREE_ITEMS) {
        if (!seen.Add(current.ToInt64())) throw new InvalidOperationException("mt5_tree_traversal_cycle");
        labels.Add(ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, current));
        visited++;
        AssertRemoteTree(tree, expectedProcessId, expectedRoot);
        current = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_NEXT, current);
      }
      if (current != IntPtr.Zero) throw new InvalidOperationException("mt5_tree_traversal_limit");
      return labels.ToArray();
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static string SelectRootOrSingleRootChildExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, string expected) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      TREEITEMMATCH match = FindRootOrSingleRootChildExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, expected);
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      if (SendRemoteTreeMessage(tree, TVM_SELECTITEM, (IntPtr)TVGN_CARET, match.item) == IntPtr.Zero)
        throw new InvalidOperationException("mt5_tree_select_failed");
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      IntPtr caret = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CARET, IntPtr.Zero);
      if (caret != match.item) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      IntPtr actualParent = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_PARENT, caret);
      if (actualParent != match.parent) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      string selected = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, caret);
      if (!String.Equals(selected, expected, StringComparison.Ordinal)) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      return selected;
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static string ReadSelectedRootOrSingleRootChildExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, string expected) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      TREEITEMMATCH match = FindRootOrSingleRootChildExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, expected);
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      IntPtr caret = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CARET, IntPtr.Zero);
      if (caret != match.item) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      IntPtr actualParent = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_PARENT, caret);
      if (actualParent != match.parent) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      string selected = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, caret);
      if (!String.Equals(selected, expected, StringComparison.Ordinal)) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      return selected;
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static void AssertTreeFocusExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    if (GetForegroundWindow() != expectedRoot)
      throw new InvalidOperationException("mt5_tree_focus_foreground_invalid");
    uint owner; uint rootOwner;
    uint targetThread = GetWindowThreadProcessId(tree, out owner);
    uint rootThread = GetWindowThreadProcessId(expectedRoot, out rootOwner);
    if (targetThread == 0 || rootThread == 0 || owner != expectedProcessId ||
        rootOwner != expectedProcessId || targetThread != rootThread)
      throw new InvalidOperationException("mt5_tree_focus_owner_invalid");
    int infoSize = Marshal.SizeOf(typeof(GUITHREADINFO));
    if (infoSize != (IntPtr.Size == 8 ? 72 : 48))
      throw new InvalidOperationException("mt5_tree_focus_layout_invalid");
    GUITHREADINFO info = new GUITHREADINFO { cbSize = (uint)infoSize };
    if (!GetGUIThreadInfo(targetThread, ref info))
      throw new InvalidOperationException("mt5_tree_focus_readback_failed");
    if (info.hwndActive != expectedRoot || info.hwndFocus != tree)
      throw new InvalidOperationException("mt5_tree_focus_readback_failed");
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
  }
  public static void AssertSelectedTreeContextExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, string expected) {
    string selected = ReadSelectedRootOrSingleRootChildExact(tree, expectedProcessId, expectedRoot, expected);
    if (!String.Equals(selected, expected, StringComparison.Ordinal))
      throw new InvalidOperationException("mt5_tree_select_readback_failed");
    AssertTreeFocusExact(tree, expectedProcessId, expectedRoot);
  }
  public static void FocusTreeExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteTree(tree, expectedProcessId, expectedRoot);
    if (GetForegroundWindow() != expectedRoot)
      throw new InvalidOperationException("mt5_tree_focus_foreground_invalid");
    uint owner; uint rootOwner;
    uint targetThread = GetWindowThreadProcessId(tree, out owner);
    uint rootThread = GetWindowThreadProcessId(expectedRoot, out rootOwner);
    if (targetThread == 0 || rootThread == 0 || owner != expectedProcessId ||
        rootOwner != expectedProcessId || targetThread != rootThread)
      throw new InvalidOperationException("mt5_tree_focus_owner_invalid");
    uint currentThread = GetCurrentThreadId();
    bool attached = false;
    try {
      if (currentThread != targetThread) {
        attached = AttachThreadInput(currentThread, targetThread, true);
        if (!attached) throw new InvalidOperationException("mt5_tree_focus_attach_failed");
      }
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      if (GetForegroundWindow() != expectedRoot)
        throw new InvalidOperationException("mt5_tree_focus_foreground_invalid");
      SetFocus(tree);
      AssertTreeFocusExact(tree, expectedProcessId, expectedRoot);
    } finally {
      if (attached && !AttachThreadInput(currentThread, targetThread, false))
        throw new InvalidOperationException("mt5_tree_focus_detach_failed");
    }
    AssertTreeFocusExact(tree, expectedProcessId, expectedRoot);
  }
  public static string SelectRootTreeItemExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, string expected) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      IntPtr match = FindRootTreeItemExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, expected);
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      if (SendRemoteTreeMessage(tree, TVM_SELECTITEM, (IntPtr)TVGN_CARET, match) == IntPtr.Zero)
        throw new InvalidOperationException("mt5_tree_select_failed");
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      IntPtr caret = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CARET, IntPtr.Zero);
      if (caret != match) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      string selected = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, caret);
      if (!String.Equals(selected, expected, StringComparison.Ordinal)) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      return selected;
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static string ReadSelectedRootTreeItemExact(IntPtr tree, uint expectedProcessId, IntPtr expectedRoot, string expected) {
    IntPtr process = IntPtr.Zero; IntPtr itemRemote = IntPtr.Zero; IntPtr textRemote = IntPtr.Zero;
    try {
      process = OpenTreeProcess(tree, expectedProcessId, expectedRoot);
      int itemSize = Marshal.SizeOf(typeof(TVITEM)); int textBytes = checked(TREE_TEXT_CHARS * 2);
      itemRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)itemSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      textRemote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)textBytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (itemRemote == IntPtr.Zero || textRemote == IntPtr.Zero) throw new InvalidOperationException("mt5_tree_remote_alloc_failed");
      IntPtr match = FindRootTreeItemExact(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, expected);
      AssertRemoteTree(tree, expectedProcessId, expectedRoot);
      IntPtr caret = SendRemoteTreeMessage(tree, TVM_GETNEXTITEM, (IntPtr)TVGN_CARET, IntPtr.Zero);
      if (caret != match) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      string selected = ReadTreeItemText(tree, expectedProcessId, expectedRoot, process, itemRemote, textRemote, caret);
      if (!String.Equals(selected, expected, StringComparison.Ordinal)) throw new InvalidOperationException("mt5_tree_select_readback_failed");
      return selected;
    } finally {
      if (textRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, textRemote, UIntPtr.Zero, MEM_RELEASE);
      if (itemRemote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, itemRemote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static void SetRemoteDate(IntPtr window, uint expectedProcessId, IntPtr expectedRoot, int year, int month, int day) {
    AssertRemoteOwner(window, expectedProcessId, expectedRoot);
    DateTime exact;
    try { exact = new DateTime(year, month, day, 0, 0, 0, DateTimeKind.Unspecified); }
    catch { throw new InvalidOperationException("mt5_date_value_invalid"); }
    SYSTEMTIME value = new SYSTEMTIME { Year=(ushort)exact.Year, Month=(ushort)exact.Month, Day=(ushort)exact.Day, DayOfWeek=(ushort)exact.DayOfWeek };
    byte[] bytes = StructureBytes(value); IntPtr process = IntPtr.Zero; IntPtr remote = IntPtr.Zero;
    try {
      process = OpenProcess(PROCESS_ACCESS, false, expectedProcessId);
      if (process == IntPtr.Zero) throw new InvalidOperationException("mt5_date_process_open_failed");
      remote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)bytes.Length, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (remote == IntPtr.Zero) throw new InvalidOperationException("mt5_date_remote_alloc_failed");
      UIntPtr written;
      if (!WriteProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out written) || written.ToUInt64() != (ulong)bytes.Length)
        throw new InvalidOperationException("mt5_date_remote_write_failed");
      AssertRemoteOwner(window, expectedProcessId, expectedRoot);
      if (SendRemoteDateMessage(window, DTM_SETSYSTEMTIME, (IntPtr)GDT_VALID, remote) == IntPtr.Zero)
        throw new InvalidOperationException("mt5_date_set_failed");
      AssertRemoteOwner(window, expectedProcessId, expectedRoot);
    } finally {
      if (remote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, remote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
  public static string GetRemoteDate(IntPtr window, uint expectedProcessId, IntPtr expectedRoot) {
    AssertRemoteOwner(window, expectedProcessId, expectedRoot);
    int size = Marshal.SizeOf(typeof(SYSTEMTIME)); IntPtr process = IntPtr.Zero; IntPtr remote = IntPtr.Zero;
    try {
      process = OpenProcess(PROCESS_ACCESS, false, expectedProcessId);
      if (process == IntPtr.Zero) throw new InvalidOperationException("mt5_date_process_open_failed");
      remote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
      if (remote == IntPtr.Zero) throw new InvalidOperationException("mt5_date_remote_alloc_failed");
      AssertRemoteOwner(window, expectedProcessId, expectedRoot);
      IntPtr status = SendRemoteDateMessage(window, DTM_GETSYSTEMTIME, IntPtr.Zero, remote);
      if (status.ToInt64() != GDT_VALID) throw new InvalidOperationException("mt5_date_read_failed");
      AssertRemoteOwner(window, expectedProcessId, expectedRoot);
      byte[] bytes = new byte[size]; UIntPtr read;
      if (!ReadProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out read) || read.ToUInt64() != (ulong)bytes.Length)
        throw new InvalidOperationException("mt5_date_remote_read_failed");
      SYSTEMTIME value = BytesStructure(bytes);
      DateTime exact;
      try { exact = new DateTime(value.Year, value.Month, value.Day, 0, 0, 0, DateTimeKind.Unspecified); }
      catch { throw new InvalidOperationException("mt5_date_read_failed"); }
      return exact.ToString("yyyy.MM.dd", System.Globalization.CultureInfo.InvariantCulture);
    } finally {
      if (remote != IntPtr.Zero && process != IntPtr.Zero) VirtualFreeEx(process, remote, UIntPtr.Zero, MEM_RELEASE);
      if (process != IntPtr.Zero) CloseHandle(process);
    }
  }
}
public sealed class MetafxMt5StartEventMonitor : IDisposable {
  const uint EVENT_OBJECT_NAMECHANGE = 0x800C;
  const uint WINEVENT_OUTOFCONTEXT = 0x0000;
  delegate void WinEventDelegate(IntPtr hook, uint eventType, IntPtr hwnd, int objectId, int childId, uint eventThread, uint eventTime);
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetWinEventHook(uint eventMin, uint eventMax, IntPtr module, WinEventDelegate callback, uint processId, uint threadId, uint flags);
  [DllImport("user32.dll", SetLastError=true)] static extern bool UnhookWinEvent(IntPtr hook);
  [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int maximum);
  [DllImport("user32.dll", SetLastError=true)] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);
  readonly IntPtr target;
  readonly WinEventDelegate callback;
  IntPtr hook;
  bool armed;
  bool sawStop;
  bool completed;
  public MetafxMt5StartEventMonitor(IntPtr targetWindow) {
    if (targetWindow == IntPtr.Zero) throw new InvalidOperationException("start_monitor_target_invalid");
    target = targetWindow;
    uint processId; uint threadId = GetWindowThreadProcessId(target, out processId);
    if (processId == 0 || threadId == 0) throw new InvalidOperationException("start_monitor_owner_invalid");
    callback = OnNameChanged;
    hook = SetWinEventHook(EVENT_OBJECT_NAMECHANGE, EVENT_OBJECT_NAMECHANGE, IntPtr.Zero, callback, processId, threadId, WINEVENT_OUTOFCONTEXT);
    if (hook == IntPtr.Zero) throw new InvalidOperationException("start_monitor_hook_unavailable");
    ObserveCurrent();
  }
  void OnNameChanged(IntPtr ignoredHook, uint ignoredEvent, IntPtr hwnd, int ignoredObject, int ignoredChild, uint ignoredThread, uint ignoredTime) {
    if (hwnd == target) ObserveCurrent();
  }
  public void ObserveCurrent() {
    StringBuilder value = new StringBuilder(64);
    if (GetWindowText(target, value, value.Capacity) <= 0) return;
    string state = value.ToString();
    lock (this) {
      // The hook exists before the durable boundary is written so hook setup
      // failure is still pre-Start.  Ignore every event until the sole native
      // post is armed under this same lock; an old/foreign Stop -> Start cycle
      // can therefore never satisfy the new operation's monitor.
      if (!armed) return;
      if (String.Equals(state, "Stop", StringComparison.Ordinal)) sawStop = true;
      else if (sawStop && String.Equals(state, "Start", StringComparison.Ordinal)) completed = true;
    }
  }
  public void PostStartOnce(uint expectedProcessId, IntPtr expectedRoot, int expectedControlId, string expectedText) {
    lock (this) {
      if (armed) throw new InvalidOperationException("start_monitor_already_armed");
      sawStop = false;
      completed = false;
      armed = true;
      try {
        // Arm and queue the one permitted BM_CLICK as one monitor epoch.  The
        // callback takes this same lock, so it cannot complete before the post.
        MetafxMt5VisibleNative.PostButtonClickIfTextExact(
          target, expectedProcessId, expectedRoot, expectedControlId, expectedText);
      } catch {
        armed = false;
        throw;
      }
    }
  }
  public bool Armed { get { lock (this) return armed; } }
  public bool SawStop { get { lock (this) return sawStop; } }
  public bool Completed { get { lock (this) return completed; } }
  public void Dispose() {
    IntPtr current = hook; hook = IntPtr.Zero;
    if (current != IntPtr.Zero) UnhookWinEvent(current);
    GC.KeepAlive(callback);
  }
}
"@
Add-Type @"
using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Drawing;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;
public static class MetafxMetaEditorCompileNative {
  [ThreadStatic] static long captureTimestamp;
  [ThreadStatic] static IDictionary<string,string> clipboardRestoreMismatchMetadata;
  public static void ResetCaptureTimestamp() { captureTimestamp = 0; }
  public static long ConsumeCaptureTimestamp() { long value = captureTimestamp; captureTimestamp = 0; return value; }
  public static IDictionary<string,string> ConsumeClipboardRestoreMismatchMetadata() {
    IDictionary<string,string> value = clipboardRestoreMismatchMetadata;
    clipboardRestoreMismatchMetadata = null;
    return value;
  }
  [ThreadStatic] static IDictionary<string,long> diagnosticTimings;
  [ThreadStatic] static System.Diagnostics.Stopwatch diagnosticClock;
  [ThreadStatic] static long diagnosticCheckpoint;
  static void DiagnosticMark(string checkpoint) {
    if (diagnosticTimings == null || diagnosticClock == null) return;
    long elapsed = diagnosticClock.ElapsedMilliseconds;
    long previous;
    diagnosticTimings.TryGetValue(checkpoint, out previous);
    diagnosticTimings[checkpoint] = previous + Math.Max(0, elapsed - diagnosticCheckpoint);
    diagnosticCheckpoint = elapsed;
  }
  const int WM_COMMAND = 0x0111;
  const int ID_EDIT_COPY = 57634;
  const int LVM_FIRST = 0x1000;
  const int LVM_GETITEMCOUNT = LVM_FIRST + 4;
  const int LVM_ENSUREVISIBLE = LVM_FIRST + 19;
  const int LVM_SETITEMSTATE = LVM_FIRST + 43;
  const int LVM_GETITEMSTATE = LVM_FIRST + 44;
  const uint LVIS_FOCUSED = 0x0001;
  const uint LVIS_SELECTED = 0x0002;
  const uint SMTO_ABORTIFHUNG = 0x0002;
  const uint PROCESS_ACCESS = 0x0438;
  const uint MEM_COMMIT = 0x1000;
  const uint MEM_RESERVE = 0x2000;
  const uint MEM_RELEASE = 0x8000;
  const uint PAGE_READWRITE = 0x0004;
  const uint CF_UNICODETEXT = 13;
  [StructLayout(LayoutKind.Sequential)] struct LVITEM {
    public uint mask; public int iItem; public int iSubItem; public uint state; public uint stateMask;
    public IntPtr pszText; public int cchTextMax; public int iImage; public IntPtr lParam; public int iIndent;
    public int iGroupId; public uint cColumns; public IntPtr puColumns; public IntPtr piColFmt; public int iGroup;
  }
  sealed class ClipboardSnapshot {
    public readonly DataObject Data;
    public readonly string[] Formats;
    public readonly Dictionary<string,string> Fingerprints;
    public ClipboardSnapshot(DataObject data, string[] formats, Dictionary<string,string> fingerprints) {
      Data = data; Formats = formats; Fingerprints = fingerprints;
    }
    public bool IsEmpty { get { return Formats.Length == 0; } }
  }
  [DllImport("user32.dll", SetLastError=true)] static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
  [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
  [DllImport("user32.dll", SetLastError=true)] static extern bool AttachThreadInput(uint source, uint target, bool attach);
  [DllImport("user32.dll", SetLastError=true)] static extern bool SetForegroundWindow(IntPtr window);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SetFocus(IntPtr window);
  [DllImport("user32.dll")] static extern IntPtr GetFocus();
  [DllImport("user32.dll", SetLastError=true)] static extern bool IsWindow(IntPtr window);
  [DllImport("user32.dll")] static extern uint GetClipboardSequenceNumber();
  [DllImport("user32.dll", SetLastError=true)] static extern bool OpenClipboard(IntPtr owner);
  [DllImport("user32.dll", SetLastError=true)] static extern bool CloseClipboard();
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr GetClipboardData(uint format);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr GlobalLock(IntPtr memory);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool GlobalUnlock(IntPtr memory);
  [DllImport("kernel32.dll", SetLastError=true)] static extern UIntPtr GlobalSize(IntPtr memory);
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SendMessageTimeout(IntPtr window, int message, IntPtr wParam, IntPtr lParam, uint flags, uint timeout, out IntPtr result);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint processId);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr VirtualAllocEx(IntPtr process, IntPtr address, UIntPtr size, uint allocationType, uint protection);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool VirtualFreeEx(IntPtr process, IntPtr address, UIntPtr size, uint freeType);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr written);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
  static long Message(IntPtr window, int message, int wParam, IntPtr lParam) {
    IntPtr result;
    if (SendMessageTimeout(window, message, (IntPtr)wParam, lParam, SMTO_ABORTIFHUNG, 1500, out result) == IntPtr.Zero)
      throw new InvalidOperationException("metaeditor_message_timeout");
    return result.ToInt64();
  }
  static byte[] StructureBytes(object value, int size) {
    IntPtr local = Marshal.AllocHGlobal(size);
    try { Marshal.StructureToPtr(value, local, false); byte[] bytes = new byte[size]; Marshal.Copy(local, bytes, 0, size); return bytes; }
    finally { Marshal.FreeHGlobal(local); }
  }
  static void SetItemState(IntPtr list, IntPtr process, IntPtr remote, int index, uint state) {
    LVITEM item = new LVITEM { state = state, stateMask = LVIS_FOCUSED | LVIS_SELECTED };
    byte[] bytes = StructureBytes(item, Marshal.SizeOf(typeof(LVITEM)));
    UIntPtr written;
    if (!WriteProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out written) || written.ToUInt64() != (ulong)bytes.Length)
      throw new InvalidOperationException("metaeditor_list_state_write_failed");
    if (Message(list, LVM_SETITEMSTATE, index, remote) == 0)
      throw new InvalidOperationException("metaeditor_list_state_write_failed");
  }
  static void RestoreSelectionAndFocus(IntPtr list, IntPtr process, IntPtr remote, uint[] priorStates, IntPtr previousFocus) {
    try {
      if (priorStates != null) {
        SetItemState(list, process, remote, -1, 0);
        for (int index = 0; index < priorStates.Length; index++) if (priorStates[index] != 0) SetItemState(list, process, remote, index, priorStates[index]);
      }
      if (previousFocus != IntPtr.Zero) {
        if (!IsWindow(previousFocus)) throw new InvalidOperationException();
        SetFocus(previousFocus);
        if (GetFocus() != previousFocus) throw new InvalidOperationException();
      }
    } catch {
      // Cleanup errors must never be retried as a transient compiler read.
      // Do not nest the generic native error: diagnostic unwrapping must retain
      // this fatal restoration classification.
      throw new InvalidOperationException("metaeditor_selection_focus_restore_failed");
    }
  }
  static string ReadClipboardText(uint priorSequence) {
    for (int attempt = 0; attempt < 100; attempt++) {
      if (GetClipboardSequenceNumber() != priorSequence && OpenClipboard(IntPtr.Zero)) {
        try {
          IntPtr memory = GetClipboardData(CF_UNICODETEXT);
          if (memory == IntPtr.Zero) throw new InvalidOperationException("metaeditor_compile_copy_text_missing");
          ulong size = GlobalSize(memory).ToUInt64();
          if (size < 2 || size > 1048576) throw new InvalidOperationException("metaeditor_compile_copy_text_invalid");
          IntPtr pointer = GlobalLock(memory);
          if (pointer == IntPtr.Zero) throw new InvalidOperationException("metaeditor_compile_copy_text_unavailable");
          try {
            string text = Marshal.PtrToStringUni(pointer);
            if (String.IsNullOrWhiteSpace(text) || text.Length > 8192) throw new InvalidOperationException("metaeditor_compile_copy_text_invalid");
            return text;
          } finally { GlobalUnlock(memory); }
        } finally { CloseClipboard(); }
      }
      Thread.Sleep(20);
    }
    throw new InvalidOperationException("metaeditor_compile_copy_timeout");
  }
  static object CloneClipboardValue(object value) {
    if (value == null) throw new InvalidOperationException("metaeditor_clipboard_format_unavailable");
    if (value is string) return value;
    if (value is string[]) return ((string[])value).Clone();
    if (value is byte[]) return ((byte[])value).Clone();
    if (value is StringCollection) {
      StringCollection source = (StringCollection)value; StringCollection copy = new StringCollection();
      foreach (string item in source) copy.Add(item); return copy;
    }
    if (value is Image) return new Bitmap((Image)value);
    if (value is MemoryStream) return new MemoryStream(((MemoryStream)value).ToArray(), false);
    if (value is Stream) {
      Stream source = (Stream)value; long position = 0;
      if (source.CanSeek) { position = source.Position; source.Position = 0; }
      try { MemoryStream copy = new MemoryStream(); source.CopyTo(copy); copy.Position = 0; return copy; }
      finally { if (source.CanSeek) source.Position = position; }
    }
    // Unknown cloneable/serializable objects cannot be proven byte-identical
    // after Windows Forms re-materializes them.  Fail closed instead of
    // claiming that the user's clipboard was restored exactly.
    throw new InvalidOperationException("metaeditor_clipboard_format_unsupported");
  }
  static byte[] ClipboardValueBytes(object value) {
    if (value == null) throw new InvalidOperationException("metaeditor_clipboard_format_unavailable");
    if (value is string) return Encoding.UTF8.GetBytes("string\0" + (string)value);
    if (value is byte[]) {
      byte[] raw = (byte[])value; byte[] prefix = Encoding.ASCII.GetBytes("bytes\0");
      byte[] result = new byte[prefix.Length + raw.Length]; Buffer.BlockCopy(prefix, 0, result, 0, prefix.Length); Buffer.BlockCopy(raw, 0, result, prefix.Length, raw.Length); return result;
    }
    if (value is string[] || value is StringCollection) {
      string[] values;
      if (value is string[]) values = (string[])value;
      else { StringCollection collection = (StringCollection)value; values = new string[collection.Count]; collection.CopyTo(values, 0); }
      using (MemoryStream stream = new MemoryStream()) using (BinaryWriter writer = new BinaryWriter(stream, Encoding.UTF8, true)) {
        writer.Write("strings"); writer.Write(values.Length); foreach (string item in values) writer.Write(item ?? String.Empty); writer.Flush(); return stream.ToArray();
      }
    }
    if (value is Image) {
      using (Bitmap bitmap = new Bitmap((Image)value)) using (MemoryStream stream = new MemoryStream()) {
        bitmap.Save(stream, System.Drawing.Imaging.ImageFormat.Png); return stream.ToArray();
      }
    }
    if (value is Stream) {
      Stream source = (Stream)value; long position = 0;
      if (source.CanSeek) { position = source.Position; source.Position = 0; }
      // OLE may return the same format's binary payload in a stream instead
      // of a byte array. Keep the binary tag and every byte identical across
      // those wrappers; other value families retain their own representation.
      try { using (MemoryStream copy = new MemoryStream()) { source.CopyTo(copy); return ClipboardValueBytes(copy.ToArray()); } }
      finally { if (source.CanSeek) source.Position = position; }
    }
    throw new InvalidOperationException("metaeditor_clipboard_format_unsupported");
  }
  static string FingerprintClipboardValue(object value) {
    using (SHA256 algorithm = SHA256.Create()) {
      byte[] digest = algorithm.ComputeHash(ClipboardValueBytes(value));
      StringBuilder text = new StringBuilder(digest.Length * 2);
      foreach (byte item in digest) text.Append(item.ToString("x2"));
      return text.ToString();
    }
  }
  static InvalidOperationException ClipboardRestoreMismatch(string format, object expected, object actual) {
    InvalidOperationException error = new InvalidOperationException("metaeditor_clipboard_restore_mismatch");
    // Diagnostic metadata only: never put clipboard text, bytes, or image
    // contents in an exception. The canonical failure code stays unchanged.
    Dictionary<string,string> metadata = new Dictionary<string,string>(StringComparer.Ordinal);
    metadata["clipboardFormat"] = format ?? "";
    metadata["expectedType"] = expected == null ? "null" : expected.GetType().FullName;
    metadata["actualType"] = actual == null ? "null" : actual.GetType().FullName;
    foreach (string key in new string[] { "clipboardFormat", "expectedType", "actualType" }) {
      string value = metadata[key] ?? "";
      metadata[key] = value.Substring(0, Math.Min(256, value.Length));
      error.Data[key] = metadata[key];
    }
    clipboardRestoreMismatchMetadata = metadata;
    return error;
  }
  static ClipboardSnapshot SnapshotClipboard() {
    if (Thread.CurrentThread.GetApartmentState() != ApartmentState.STA)
      throw new InvalidOperationException("metaeditor_clipboard_apartment_invalid");
    System.Windows.Forms.IDataObject source = null;
    bool clipboardObserved = false;
    for (int attempt = 0; attempt < 100; attempt++) {
      try { source = Clipboard.GetDataObject(); clipboardObserved = true; break; }
      catch (ExternalException) { Thread.Sleep(20); }
    }
    // A successful null return proves an empty clipboard.  Exhausting every
    // busy-clipboard retry proves nothing and must stop before WM_COMMAND can
    // replace user data; it must never be represented as an empty snapshot.
    if (!clipboardObserved) throw new InvalidOperationException("metaeditor_clipboard_snapshot_unavailable");
    if (source == null) return new ClipboardSnapshot(new DataObject(), new string[0], new Dictionary<string,string>(StringComparer.Ordinal));
    string[] formats = source.GetFormats(false);
    Array.Sort(formats, StringComparer.Ordinal);
    DataObject copy = new DataObject();
    Dictionary<string,string> fingerprints = new Dictionary<string,string>(StringComparer.Ordinal);
    foreach (string format in formats) {
      object cloned = CloneClipboardValue(source.GetData(format, false));
      copy.SetData(format, false, cloned);
      fingerprints.Add(format, FingerprintClipboardValue(cloned));
    }
    return new ClipboardSnapshot(copy, formats, fingerprints);
  }
  static void RestoreClipboard(ClipboardSnapshot snapshot) {
    for (int attempt = 0; attempt < 100; attempt++) {
      try {
        if (snapshot.IsEmpty) Clipboard.Clear(); else Clipboard.SetDataObject(snapshot.Data, true);
        DiagnosticMark("clipboard_restore_publish");
        System.Windows.Forms.IDataObject restored = Clipboard.GetDataObject();
        DiagnosticMark("clipboard_restore_readback_object");
        string[] restoredFormats = restored == null ? new string[0] : restored.GetFormats(false);
        Array.Sort(restoredFormats, StringComparer.Ordinal);
        DiagnosticMark("clipboard_restore_formats");
        if (restoredFormats.Length != snapshot.Formats.Length) throw new InvalidOperationException("metaeditor_clipboard_restore_incomplete");
        for (int index = 0; index < snapshot.Formats.Length; index++) {
          string expected = snapshot.Formats[index];
          if (!String.Equals(expected, restoredFormats[index], StringComparison.Ordinal)) throw new InvalidOperationException("metaeditor_clipboard_restore_incomplete");
          object actualValue = restored.GetData(expected, false);
          string actualFingerprint = FingerprintClipboardValue(actualValue);
          DiagnosticMark("clipboard_restore_verify_formats");
          if (!String.Equals(actualFingerprint, snapshot.Fingerprints[expected], StringComparison.Ordinal))
            throw ClipboardRestoreMismatch(expected, snapshot.Data.GetData(expected, false), actualValue);
        }
        return;
      } catch (ExternalException) { Thread.Sleep(20); }
    }
    throw new InvalidOperationException("metaeditor_clipboard_restore_failed");
  }
  public static int GetItemCount(IntPtr list) {
    ResetCaptureTimestamp();
    if (list == IntPtr.Zero || !IsWindow(list)) throw new InvalidOperationException("metaeditor_compile_controls_invalid");
    int count = checked((int)Message(list, LVM_GETITEMCOUNT, 0, IntPtr.Zero));
    if (count < 0 || count > 100000) throw new InvalidOperationException("metaeditor_compile_rows_invalid");
    captureTimestamp = System.Diagnostics.Stopwatch.GetTimestamp();
    return count;
  }
  public static string CopyDiagnosticRow(IntPtr root, IntPtr list) {
    IntPtr foreground = GetForegroundWindow();
    try { return CopyLastVisibleRow(root, list); }
    finally {
      if (foreground != IntPtr.Zero && IsWindow(foreground) && GetForegroundWindow() != foreground) {
        if (!SetForegroundWindow(foreground) || GetForegroundWindow() != foreground)
          throw new InvalidOperationException("metaeditor_diagnostic_foreground_restore_failed");
      }
    }
  }
  public static string CopyDiagnosticRowTimed(IntPtr root, IntPtr list, IDictionary<string,long> timings) {
    if (timings == null || diagnosticTimings != null) throw new InvalidOperationException("metaeditor_diagnostic_timing_invalid");
    diagnosticTimings = timings;
    diagnosticClock = System.Diagnostics.Stopwatch.StartNew();
    diagnosticCheckpoint = 0;
    try { return CopyDiagnosticRow(root, list); }
    finally {
      DiagnosticMark("foreground_restore");
      diagnosticTimings = null; diagnosticClock = null; diagnosticCheckpoint = 0;
    }
  }
  public static string CopyLastVisibleRow(IntPtr root, IntPtr list) {
    ResetCaptureTimestamp();
    clipboardRestoreMismatchMetadata = null;
    if (root == IntPtr.Zero || list == IntPtr.Zero || !IsWindow(root) || !IsWindow(list))
      throw new InvalidOperationException("metaeditor_compile_controls_invalid");
    ClipboardSnapshot original = SnapshotClipboard();
    DiagnosticMark("clipboard_snapshot");
    uint listProcessId; uint listThread = GetWindowThreadProcessId(list, out listProcessId);
    uint rootProcessId; GetWindowThreadProcessId(root, out rootProcessId);
    if (listProcessId == 0 || listProcessId != rootProcessId || listThread == 0) throw new InvalidOperationException("metaeditor_compile_controls_mismatch");
    IntPtr process = OpenProcess(PROCESS_ACCESS, false, listProcessId);
    if (process == IntPtr.Zero) throw new InvalidOperationException("metaeditor_compile_process_unavailable");
    int structureSize = Marshal.SizeOf(typeof(LVITEM));
    IntPtr remote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)structureSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (remote == IntPtr.Zero) { CloseHandle(process); throw new InvalidOperationException("metaeditor_compile_memory_unavailable"); }
    uint currentThread = GetCurrentThreadId();
    bool attached = false;
    IntPtr previousFocus = IntPtr.Zero;
    uint[] priorStates = null;
    bool clipboardMutated = false;
    try {
      int count = checked((int)Message(list, LVM_GETITEMCOUNT, 0, IntPtr.Zero));
      if (count < 1 || count > 100000) throw new InvalidOperationException("metaeditor_compile_rows_invalid");
      priorStates = new uint[count];
      for (int index = 0; index < count; index++) priorStates[index] = unchecked((uint)Message(list, LVM_GETITEMSTATE, index, (IntPtr)(LVIS_FOCUSED | LVIS_SELECTED)));
      SetItemState(list, process, remote, -1, 0);
      SetItemState(list, process, remote, count - 1, LVIS_FOCUSED | LVIS_SELECTED);
      Message(list, LVM_ENSUREVISIBLE, count - 1, IntPtr.Zero);
      DiagnosticMark("list_state_setup");
      if (currentThread != listThread) {
        attached = AttachThreadInput(currentThread, listThread, true);
        if (!attached) throw new InvalidOperationException("metaeditor_compile_focus_attach_failed");
      }
      if (!SetForegroundWindow(root) || GetForegroundWindow() != root) throw new InvalidOperationException("metaeditor_compile_foreground_failed");
      previousFocus = GetFocus();
      SetFocus(list);
      if (GetFocus() != list) throw new InvalidOperationException("metaeditor_compile_focus_failed");
      DiagnosticMark("focus_binding");
      uint sequence = GetClipboardSequenceNumber();
      clipboardMutated = true;
      Message(root, WM_COMMAND, ID_EDIT_COPY, IntPtr.Zero);
      DiagnosticMark("copy_dispatch");
      string copied = ReadClipboardText(sequence);
      captureTimestamp = System.Diagnostics.Stopwatch.GetTimestamp();
      DiagnosticMark("read_copied_text");
      return copied;
    } finally {
      try {
        RestoreSelectionAndFocus(list, process, remote, priorStates, previousFocus);
        DiagnosticMark("selection_focus_restore");
      } finally {
        if (attached) AttachThreadInput(currentThread, listThread, false);
        VirtualFreeEx(process, remote, UIntPtr.Zero, MEM_RELEASE);
        CloseHandle(process);
        if (clipboardMutated) RestoreClipboard(original);
        DiagnosticMark("clipboard_restore");
      }
    }
  }
}
"@ -ReferencedAssemblies @("System.Windows.Forms.dll", "System.Drawing.dll")
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class MetafxMt5TabNative {
  const int TCM_GETITEMCOUNT = 0x1304;
  const int TCM_GETITEMW = 0x133C;
  const int TCM_GETITEMRECT = 0x130A;
  const int TCM_GETCURSEL = 0x130B;
  const int WM_LBUTTONDOWN = 0x0201;
  const int WM_LBUTTONUP = 0x0202;
  const uint SMTO_ABORTIFHUNG = 0x0002;
  const uint PROCESS_ACCESS = 0x0438;
  const uint MEM_COMMIT = 0x1000;
  const uint MEM_RESERVE = 0x2000;
  const uint MEM_RELEASE = 0x8000;
  const uint PAGE_READWRITE = 0x0004;
  [StructLayout(LayoutKind.Sequential)] struct TCITEM { public uint mask; public uint state; public uint stateMask; public IntPtr pszText; public int cchTextMax; public int iImage; public IntPtr lParam; }
  [StructLayout(LayoutKind.Sequential)] struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
  [DllImport("user32.dll", SetLastError=true)] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
  [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SendMessageTimeout(IntPtr hWnd, int message, IntPtr wParam, IntPtr lParam, uint flags, uint timeout, out IntPtr result);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr OpenProcess(uint access, bool inherit, uint processId);
  [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr VirtualAllocEx(IntPtr process, IntPtr address, UIntPtr size, uint allocationType, uint protection);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool VirtualFreeEx(IntPtr process, IntPtr address, UIntPtr size, uint freeType);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr written);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool ReadProcessMemory(IntPtr process, IntPtr address, byte[] buffer, UIntPtr size, out UIntPtr read);
  [DllImport("kernel32.dll", SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
  static long Message(IntPtr handle, int message, int wParam, IntPtr lParam) {
    IntPtr result;
    if (SendMessageTimeout(handle, message, (IntPtr)wParam, lParam, SMTO_ABORTIFHUNG, 1500, out result) == IntPtr.Zero) throw new InvalidOperationException("tab_message_timeout");
    return result.ToInt64();
  }
  static byte[] StructureBytes(object value, int size) {
    IntPtr local = Marshal.AllocHGlobal(size);
    try { Marshal.StructureToPtr(value, local, false); byte[] bytes = new byte[size]; Marshal.Copy(local, bytes, 0, size); return bytes; }
    finally { Marshal.FreeHGlobal(local); }
  }
  static T BytesStructure<T>(byte[] bytes) {
    IntPtr local = Marshal.AllocHGlobal(bytes.Length);
    try { Marshal.Copy(bytes, 0, local, bytes.Length); return (T)Marshal.PtrToStructure(local, typeof(T)); }
    finally { Marshal.FreeHGlobal(local); }
  }
  static string[] ReadNames(IntPtr tab, IntPtr process, IntPtr remote, int structureSize, int textBytes) {
    int count = checked((int)Message(tab, TCM_GETITEMCOUNT, 0, IntPtr.Zero));
    if (count < 1 || count > 128) throw new InvalidOperationException("tab_count_invalid");
    string[] names = new string[count];
    byte[] empty = new byte[textBytes];
    for (int index = 0; index < count; index++) {
      UIntPtr transferred;
      if (!WriteProcessMemory(process, IntPtr.Add(remote, structureSize), empty, (UIntPtr)empty.Length, out transferred) || transferred.ToUInt64() != (ulong)empty.Length) throw new InvalidOperationException("tab_text_clear_failed");
      TCITEM item = new TCITEM { mask = 1, pszText = IntPtr.Add(remote, structureSize), cchTextMax = textBytes / 2 };
      byte[] itemBytes = StructureBytes(item, structureSize);
      if (!WriteProcessMemory(process, remote, itemBytes, (UIntPtr)itemBytes.Length, out transferred) || transferred.ToUInt64() != (ulong)itemBytes.Length) throw new InvalidOperationException("tab_item_write_failed");
      if (Message(tab, TCM_GETITEMW, index, remote) != 1) throw new InvalidOperationException("tab_item_read_failed");
      byte[] text = new byte[textBytes];
      if (!ReadProcessMemory(process, IntPtr.Add(remote, structureSize), text, (UIntPtr)text.Length, out transferred) || transferred.ToUInt64() != (ulong)text.Length) throw new InvalidOperationException("tab_text_read_failed");
      names[index] = Encoding.Unicode.GetString(text).TrimEnd('\0').Trim();
      if (String.IsNullOrWhiteSpace(names[index]) || names[index].Length > 128) throw new InvalidOperationException("tab_name_invalid");
    }
    return names;
  }
  public static string[] GetNames(IntPtr tab) {
    uint processId; GetWindowThreadProcessId(tab, out processId); if (processId == 0) throw new InvalidOperationException("tab_owner_invalid");
    IntPtr process = OpenProcess(PROCESS_ACCESS, false, processId); if (process == IntPtr.Zero) throw new InvalidOperationException("tab_process_unavailable");
    int structureSize = Marshal.SizeOf(typeof(TCITEM)); int textBytes = 1024; IntPtr remote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)(structureSize + textBytes), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (remote == IntPtr.Zero) { CloseHandle(process); throw new InvalidOperationException("tab_memory_unavailable"); }
    try { return ReadNames(tab, process, remote, structureSize, textBytes); }
    finally { VirtualFreeEx(process, remote, UIntPtr.Zero, MEM_RELEASE); CloseHandle(process); }
  }
  public static int GetSelectedIndex(IntPtr tab) { return checked((int)Message(tab, TCM_GETCURSEL, 0, IntPtr.Zero)); }
  public static bool SelectExact(IntPtr tab, string expected) {
    string[] names = GetNames(tab); int match = -1;
    for (int index = 0; index < names.Length; index++) if (String.Equals(names[index], expected, StringComparison.OrdinalIgnoreCase)) { if (match >= 0) return false; match = index; }
    if (match < 0) return false;
    uint processId; GetWindowThreadProcessId(tab, out processId); IntPtr process = OpenProcess(PROCESS_ACCESS, false, processId); if (process == IntPtr.Zero) return false;
    int rectSize = Marshal.SizeOf(typeof(RECT)); IntPtr remote = VirtualAllocEx(process, IntPtr.Zero, (UIntPtr)rectSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE); if (remote == IntPtr.Zero) { CloseHandle(process); return false; }
    try {
      if (Message(tab, TCM_GETITEMRECT, match, remote) != 1) return false;
      byte[] bytes = new byte[rectSize]; UIntPtr read; if (!ReadProcessMemory(process, remote, bytes, (UIntPtr)bytes.Length, out read) || read.ToUInt64() != (ulong)bytes.Length) return false;
      RECT rect = BytesStructure<RECT>(bytes); int x = rect.Left + Math.Max(1, (rect.Right - rect.Left) / 2); int y = rect.Top + Math.Max(1, (rect.Bottom - rect.Top) / 2);
      if (x < 0 || y < 0 || x > 32767 || y > 32767) return false; int point = ((y & 0xffff) << 16) | (x & 0xffff);
      Message(tab, WM_LBUTTONDOWN, 1, (IntPtr)point); Message(tab, WM_LBUTTONUP, 0, (IntPtr)point);
      return GetSelectedIndex(tab) == match;
    } finally { VirtualFreeEx(process, remote, UIntPtr.Zero, MEM_RELEASE); CloseHandle(process); }
  }
}
"@

$ResultSchema = "ea-factory-visible-powershell-result-v1"
$RequestSchema = "ea-factory-visible-powershell-request-v1"
$TerminalProcess = $null
$TerminalRoot = $null
$OperationMutex = $null
$OperationMutexHeld = $false
$TerminalMutex = $null
$TerminalMutexHeld = $false

function Fail([string]$Code) {
    throw [System.InvalidOperationException]::new($Code)
}

function Resolve-PopupDispatchFailureCode(
    [System.Management.Automation.ErrorRecord]$ErrorRecord,
    [string]$Code,
    [string]$Stage
) {
    if ($null -eq $ErrorRecord -or [string]::IsNullOrWhiteSpace($Code) -or
        @("popup_bind", "preflight", "dispatch").Where({ [string]$_ -ceq $Stage }).Count -ne 1) {
        return "$($Code)_dispatch_unexpected"
    }
    [System.Exception]$exception = $ErrorRecord.Exception
    $unwrapCount = 0
    while ($null -ne $exception -and $null -ne $exception.InnerException -and $unwrapCount -lt 2 -and
        @(
            "System.Management.Automation.MethodInvocationException",
            "System.Reflection.TargetInvocationException"
        ).Where({ [string]$_ -ceq $exception.GetType().FullName }).Count -eq 1) {
        $exception = $exception.InnerException
        $unwrapCount++
    }
    $nativeReason = if ($null -eq $exception -or
        [string]$exception.GetType().FullName -cne "System.InvalidOperationException" -or
        $null -ne $exception.InnerException) { "" } else { [string]$exception.Message }
    # Only exact native reasons produced by the bound popup implementation are
    # exposed.  Unknown/wrapped text is deliberately collapsed to unexpected;
    # substring matching would let arbitrary exception text forge a reason.
    $suffix = switch -CaseSensitive ($nativeReason) {
        "mt5_popup_menu_changed" { "menu_changed"; break }
        "mt5_popup_menu_class_invalid" { "menu_class_invalid"; break }
        "mt5_popup_menu_command_dispatch_ambiguous" {
            if ($Stage -ceq "dispatch") { "ambiguous" } else { "unexpected" }
            break
        }
        "mt5_popup_menu_command_invalid" { "command_invalid"; break }
        "mt5_popup_menu_command_owner_invalid" { "command_owner_invalid"; break }
        "mt5_popup_menu_handle_changed" { "handle_changed"; break }
        "mt5_popup_menu_handle_invalid" { "handle_invalid"; break }
        "mt5_popup_menu_item_count_invalid" { "item_count_invalid"; break }
        "mt5_popup_menu_item_invalid" { "item_invalid"; break }
        "mt5_popup_menu_item_rect_invalid" { "item_rect_invalid"; break }
        "mt5_popup_menu_layout_invalid" { "layout_invalid"; break }
        "mt5_popup_menu_owner_invalid" { "owner_invalid"; break }
        "mt5_popup_menu_selection_failed" { "selection_failed"; break }
        "mt5_popup_menu_text_invalid" { "text_invalid"; break }
        "mt5_popup_menu_token_invalid" { "token_invalid"; break }
        "mt5_popup_submenu_changed" { "submenu_changed"; break }
        "mt5_popup_submenu_handle_invalid" { "submenu_handle_invalid"; break }
        "mt5_popup_submenu_host_ambiguous" { "submenu_host_ambiguous"; break }
        "mt5_popup_submenu_invalid" { "submenu_invalid"; break }
        "mt5_popup_submenu_open_failed" { "submenu_open_failed"; break }
        default { "unexpected"; break }
    }
    if ($Stage -ceq "dispatch" -and $suffix -ceq "ambiguous") {
        return "$($Code)_dispatch_ambiguous"
    }
    return "$($Code)_$($Stage)_$suffix"
}

function Enter-OperationMutex([string]$OperationId) {
    if ($OperationId -notmatch '^ea-visible-[a-f0-9]{24}$') { Fail "visible_operation_invalid" }
    $script:OperationMutex = [System.Threading.Mutex]::new($false, "Global\MetafxclubEaFactoryMt5-$OperationId")
    try {
        $script:OperationMutexHeld = $script:OperationMutex.WaitOne(0)
    } catch [System.Threading.AbandonedMutexException] {
        $script:OperationMutexHeld = $true
    }
    if (-not $script:OperationMutexHeld) { Fail "visible_operation_already_running" }
}

function Exit-OperationMutex() {
    if ($null -ne $script:OperationMutex) {
        if ($script:OperationMutexHeld) {
            try { $script:OperationMutex.ReleaseMutex() } catch {}
        }
        try { $script:OperationMutex.Dispose() } catch {}
        $script:OperationMutex = $null
        $script:OperationMutexHeld = $false
    }
}

function Enter-TerminalMutex([string]$TerminalPath, [string]$DataPath) {
    $identity = ([System.IO.Path]::GetFullPath($TerminalPath).ToLowerInvariant() + "`n" + [System.IO.Path]::GetFullPath($DataPath).ToLowerInvariant())
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($identity)
    $hash = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
    $script:TerminalMutex = [System.Threading.Mutex]::new($false, "Global\MetafxclubEaFactoryMt5Terminal-$hash")
    try {
        $script:TerminalMutexHeld = $script:TerminalMutex.WaitOne(0)
    } catch [System.Threading.AbandonedMutexException] {
        $script:TerminalMutexHeld = $true
    }
    if (-not $script:TerminalMutexHeld) { Fail "visible_terminal_busy" }
}

function Exit-TerminalMutex() {
    if ($null -ne $script:TerminalMutex) {
        if ($script:TerminalMutexHeld) {
            try { $script:TerminalMutex.ReleaseMutex() } catch {}
        }
        try { $script:TerminalMutex.Dispose() } catch {}
        $script:TerminalMutex = $null
        $script:TerminalMutexHeld = $false
    }
}

function Write-JsonExclusive([string]$Path, [object]$Value) {
    $parent = [System.IO.Path]::GetDirectoryName($Path)
    if (-not [System.IO.Directory]::Exists($parent)) { Fail "visible_ui_response_parent_missing" }
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 30 -Compress))
    try {
        $stream = [System.IO.File]::Open($Path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    } catch { Fail "visible_ui_response_exists" }
}

function Get-FullFile([object]$Value, [string]$Leaf, [string]$Code) {
    $raw = [string]$Value
    if (-not [System.IO.Path]::IsPathRooted($raw)) { Fail $Code }
    $full = [System.IO.Path]::GetFullPath($raw)
    if (-not [System.IO.File]::Exists($full)) { Fail $Code }
    if ([System.IO.Path]::GetFileName($full) -ine $Leaf) { Fail $Code }
    return $full
}

function Get-FullExistingFile([object]$Value, [string]$Extension, [string]$Code) {
    $raw = [string]$Value
    if (-not [System.IO.Path]::IsPathRooted($raw)) { Fail $Code }
    $full = [System.IO.Path]::GetFullPath($raw)
    if (-not [System.IO.File]::Exists($full)) { Fail $Code }
    if ([System.IO.Path]::GetExtension($full).ToLowerInvariant() -cne $Extension) { Fail $Code }
    return $full
}

function Get-Sha256([string]$Path) {
    return ([System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash([System.IO.File]::ReadAllBytes($Path))).Replace("-", "").ToLowerInvariant())
}

function Get-TerminalMainWindowExact([object]$Process) {
    try { return [MetafxMt5VisibleNative]::FindTerminalMainWindowExact([uint32]$Process.Id) } catch {
        $failure = $_.Exception
        while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
        if ($failure.Message -cin @("mt5_terminal_root_ambiguous", "mt5_terminal_root_enumeration_failed", "mt5_terminal_process_changed")) {
            Fail $failure.Message
        }
        Fail "mt5_terminal_root_unverified"
    }
}

function Get-ExactTerminal([string]$TerminalPath, [int]$ExpectedPid, [long]$ExpectedWindow) {
    $pathMatches = @()
    foreach ($process in @(Get-Process -Name "terminal64" -ErrorAction SilentlyContinue)) {
        try { $image = [System.IO.Path]::GetFullPath($process.Path) } catch { continue }
        if ($image -ieq $TerminalPath) { $pathMatches += $process }
    }
    if ($ExpectedPid -gt 0) {
        $pidMatches = @($pathMatches | Where-Object { $_.Id -eq $ExpectedPid })
        if ($pidMatches.Count -ne 1) { Fail "mt5_terminal_process_changed" }
        $selected = $pidMatches[0]
    } else {
        # An unsigned capability probe may self-bind only when exactly one
        # visible terminal exists at the Backend-resolved executable path.
        $visibleMatches = @($pathMatches | Where-Object { (Get-TerminalMainWindowExact $_) -ne [IntPtr]::Zero })
        if ($visibleMatches.Count -ne 1) { Fail "mt5_selected_terminal_not_ready" }
        $selected = $visibleMatches[0]
    }
    if ($ExpectedWindow -gt 0) {
        # Process.MainWindowHandle is a dynamic convenience value and can point
        # briefly at an MT5-owned report/popup window.  Mutating and recovery
        # calls already carry the signed root HWND, so validate that exact HWND
        # natively instead of rejecting a still-valid binding because the
        # dynamic value drifted.
        [IntPtr]$signedRoot = [IntPtr][long]$ExpectedWindow
        if (-not [MetafxMt5VisibleNative]::IsWindow($signedRoot) -or
            -not [MetafxMt5VisibleNative]::IsWindowVisible($signedRoot) -or
            -not [MetafxMt5VisibleNative]::IsWindowEnabled($signedRoot) -or
            (Get-NativeOwner $signedRoot) -ne $selected.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($signedRoot, [MetafxMt5VisibleNative]::GA_ROOT) -ne $signedRoot) {
            Fail "mt5_terminal_window_changed"
        }
    }
    return $selected
}

function Get-Root([object]$Process, [IntPtr]$ExpectedHandle = [IntPtr]::Zero) {
    [IntPtr]$handle = if ($ExpectedHandle -ne [IntPtr]::Zero) { $ExpectedHandle } else { [IntPtr]$Process.MainWindowHandle }
    if ($handle -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
        (Get-NativeOwner $handle) -ne [int]$Process.Id) {
        Fail "mt5_window_automation_unavailable"
    }
    try { return [System.Windows.Automation.AutomationElement]::FromHandle($handle) } catch { Fail "mt5_window_automation_unavailable" }
}

function Get-All([System.Windows.Automation.AutomationElement]$Root, [System.Windows.Automation.Condition]$Condition) {
    return @($Root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $Condition))
}

function Get-NativeClass([IntPtr]$Handle) {
    $buffer = [System.Text.StringBuilder]::new(256)
    if ([MetafxMt5VisibleNative]::GetClassName($Handle, $buffer, $buffer.Capacity) -le 0) { Fail "mt5_control_class_unavailable" }
    return $buffer.ToString()
}

function Get-NativeOwner([IntPtr]$Handle) {
    [uint32]$owner = 0
    [void][MetafxMt5VisibleNative]::GetWindowThreadProcessId($Handle, [ref]$owner)
    return [int]$owner
}

function Assert-NativeControl([System.Windows.Automation.AutomationElement]$Control, [string]$ExpectedClass, [string]$Code) {
    [IntPtr]$expectedRoot = $script:TerminalRootHandle
    if ($expectedRoot -eq [IntPtr]::Zero) { Fail $Code }
    [IntPtr]$handle = [IntPtr]$Control.Current.NativeWindowHandle
    if ($handle -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
        -not [MetafxMt5VisibleNative]::IsWindowVisible($handle) -or
        -not [MetafxMt5VisibleNative]::IsWindowEnabled($handle) -or
        (Get-NativeOwner $handle) -ne $TerminalProcess.Id -or
        (Get-NativeClass $handle) -cne $ExpectedClass -or
        [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $expectedRoot -or
        (([MetafxMt5VisibleNative]::GetWindowLong($handle, [MetafxMt5VisibleNative]::GWL_STYLE) -band [MetafxMt5VisibleNative]::WS_DISABLED) -ne 0)) {
        Fail $Code
    }
    return $handle
}

function Invoke-NativeMessage([IntPtr]$Handle, [int]$Message, [int]$WParam, [int]$LParam, [string]$Code) {
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $Handle, $Message, [IntPtr]$WParam, [IntPtr]$LParam,
        [MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$result
    )
    if ($call -eq [IntPtr]::Zero) { Fail $Code }
    return $result
}

function Send-BalancedKey([IntPtr]$Handle, [int]$VirtualKey, [string]$Code) {
    if ($Handle -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($Handle) -or (Get-NativeOwner $Handle) -le 0) { Fail $Code }
    [IntPtr]$keyDownLParam = [IntPtr]1
    [IntPtr]$keyUpLParam = [IntPtr]([int]-1073741823) # 0xC0000001: repeat=1, previous=1, transition=1
    if (-not [MetafxMt5VisibleNative]::PostMessage($Handle, [MetafxMt5VisibleNative]::WM_KEYDOWN, [IntPtr]$VirtualKey, $keyDownLParam)) { Fail $Code }
    if (-not [MetafxMt5VisibleNative]::PostMessage($Handle, [MetafxMt5VisibleNative]::WM_KEYUP, [IntPtr]$VirtualKey, $keyUpLParam)) { Fail $Code }
}

function Read-NativeText([IntPtr]$Handle, [string]$Code) {
    $length = (Invoke-NativeMessage $Handle ([MetafxMt5VisibleNative]::WM_GETTEXTLENGTH) 0 0 $Code).ToInt32()
    if ($length -lt 0 -or $length -gt 4096) { Fail $Code }
    $buffer = [System.Text.StringBuilder]::new([Math]::Max(2, $length + 2))
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $Handle, [MetafxMt5VisibleNative]::WM_GETTEXT, [IntPtr]$buffer.Capacity, $buffer,
        [MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$result
    )
    if ($call -eq [IntPtr]::Zero) { Fail $Code }
    return $buffer.ToString().Trim()
}

function Read-NativeComboItem([IntPtr]$Handle, [int]$Index, [string]$Code) {
    $length = (Invoke-NativeMessage $Handle ([MetafxMt5VisibleNative]::CB_GETLBTEXTLEN) $Index 0 $Code).ToInt32()
    if ($length -lt 0 -or $length -gt 4096) { Fail $Code }
    $buffer = [System.Text.StringBuilder]::new([Math]::Max(2, $length + 2))
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $Handle, [MetafxMt5VisibleNative]::CB_GETLBTEXT, [IntPtr]$Index, $buffer,
        [MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$result
    )
    if ($call -eq [IntPtr]::Zero -or $result.ToInt32() -ne $length) { Fail $Code }
    return $buffer.ToString().Trim()
}

function Read-NativeCombo([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "ComboBox" $Code
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 $Code).ToInt32()
    $index = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCURSEL) 0 0 $Code).ToInt32()
    if ($count -lt 0 -or $count -gt 4096 -or $index -lt -1 -or $index -ge $count) { Fail $Code }
    if ($index -ge 0) { return Read-NativeComboItem $handle $index $Code }
    $value = Read-NativeText $handle $Code
    if ([string]::IsNullOrWhiteSpace($value)) { Fail $Code }
    return $value
}

function Get-NativeComboExactMatchEntries([System.Windows.Automation.AutomationElement]$Control, [string[]]$ExpectedNames, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "ComboBox" $Code
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 $Code).ToInt32()
    if ($count -lt 0 -or $count -gt 4096 -or $ExpectedNames.Count -lt 1) { Fail $Code }
    $matches = New-Object System.Collections.Generic.List[object]
    for ($index = 0; $index -lt $count; $index++) {
        $candidate = (Read-NativeComboItem $handle $index $Code).Trim().Replace("/", "\")
        if (@($ExpectedNames | Where-Object {
            $candidate.Equals(([string]$_).Trim().Replace("/", "\"), [System.StringComparison]::OrdinalIgnoreCase)
        }).Count -gt 0) {
            [void]$matches.Add([pscustomobject]@{ index = [int]$index; text = [string]$candidate })
        }
    }
    return @($matches.ToArray())
}

function Get-NativeComboExactMatches([System.Windows.Automation.AutomationElement]$Control, [string[]]$ExpectedNames, [string]$Code) {
    return @(Get-NativeComboExactMatchEntries $Control $ExpectedNames $Code | ForEach-Object { [string]$_.text })
}

function Assert-ExactExpertCombo([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "ComboBox" $Code
    $style = [MetafxMt5VisibleNative]::GetWindowLong($handle, [MetafxMt5VisibleNative]::GWL_STYLE)
    if (([MetafxMt5VisibleNative]::GetDlgCtrlID($handle) -ne 10485) -or
        (($style -band 3) -ne [MetafxMt5VisibleNative]::CBS_DROPDOWNLIST) -or
        (($style -band [MetafxMt5VisibleNative]::CBS_HASSTRINGS) -eq 0)) {
        Fail $Code
    }
    return $handle
}

function Close-NativeComboDropDownExact([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "ComboBox" $Code
    $state = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32()
    if ($state -notin @(0, 1)) { Fail $Code }
    if ($state -eq 1) {
        # CBS providers in MT5 build 6230 can acknowledge CB_SHOWDROPDOWN but
        # keep their popup visible.  Try the system message first, then use one
        # balanced F4 targeted to this exact owner/root-bound ComboBox only if
        # native drop-state still reports open.
        [void](Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_SHOWDROPDOWN) 0 0 $Code)
        if ((Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32() -eq 1) {
            Send-BalancedKey $handle ([MetafxMt5VisibleNative]::VK_F4) $Code
        }
        $deadline = [DateTime]::UtcNow.AddSeconds(2)
        do {
            $state = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32()
            if ($state -eq 0) { break }
            if ($state -ne 1) { Fail $Code }
            Start-Sleep -Milliseconds 25
        } while ([DateTime]::UtcNow -lt $deadline)
    }
    if ((Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32() -ne 0) { Fail $Code }
    return $handle
}

function Invoke-NativeComboAddStringExact([System.Windows.Automation.AutomationElement]$Control, [string]$Value, [string]$Code) {
    [IntPtr]$handle = Assert-ExactExpertCombo $Control $Code
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt 512 -or $Value.IndexOf([char]0) -ge 0) { Fail $Code }
    [IntPtr]$result = [IntPtr]::Zero
    # CB_ADDSTRING is a system message below WM_USER, so Windows marshals the
    # bounded Unicode string across processes.  No caller-local pointer is sent.
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $handle, [MetafxMt5VisibleNative]::CB_ADDSTRING, [IntPtr]::Zero, $Value,
        ([MetafxMt5VisibleNative]::SMTO_BLOCK -bor [MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG -bor [MetafxMt5VisibleNative]::SMTO_ERRORONEXIT),
        1500, [ref]$result
    )
    $index = $result.ToInt32()
    if ($call -eq [IntPtr]::Zero -or $index -in @([MetafxMt5VisibleNative]::CB_ERR, [MetafxMt5VisibleNative]::CB_ERRSPACE) -or $index -lt 0 -or $index -gt 4095) { Fail $Code }
    return [int]$index
}

function Send-NativeComboSelectionChange([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    [IntPtr]$handle = Assert-ExactExpertCombo $Control $Code
    [IntPtr]$parent = [MetafxMt5VisibleNative]::GetParent($handle)
    $controlId = [MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
    if ($parent -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($parent) -or
        (Get-NativeOwner $parent) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($parent, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle -or
        $controlId -ne 10485) {
        Fail $Code
    }
    $notification = (([MetafxMt5VisibleNative]::CBN_SELCHANGE -shl 16) -bor ($controlId -band 0xffff))
    if (-not [MetafxMt5VisibleNative]::PostMessage($parent, [MetafxMt5VisibleNative]::WM_COMMAND, [IntPtr]$notification, $handle)) { Fail $Code }
    [System.Windows.Forms.Application]::DoEvents()
    Start-Sleep -Milliseconds 100
}

function Read-UiaComboSelectionExact([System.Windows.Automation.AutomationElement]$Control, [string[]]$ExpectedNames, [string]$Code) {
    [void](Assert-ExactExpertCombo $Control $Code)
    $observations = New-Object System.Collections.Generic.List[string]
    # MT5 build 6230 exposes AutomationId 10485 as ControlType.Pane with no
    # supported UIA patterns, but its exact Current.Name tracks the selected
    # expert.  Treat that provider value as mandatory and cross-check any
    # optional Selection/Value patterns when a different build exposes them.
    $providerName = ([string]$Control.Current.Name).Trim().Replace("/", "\")
    if ([string]::IsNullOrWhiteSpace($providerName)) { Fail $Code }
    [void]$observations.Add($providerName)
    $selectionPattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern, [ref]$selectionPattern)) {
        $selected = @($selectionPattern.Current.GetSelection())
        if ($selected.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$selected[0].Current.Name)) { Fail $Code }
        [void]$observations.Add(([string]$selected[0].Current.Name).Trim().Replace("/", "\"))
    }
    $valuePattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$valuePattern)) {
        $value = ([string]$valuePattern.Current.Value).Trim().Replace("/", "\")
        if ([string]::IsNullOrWhiteSpace($value)) { Fail $Code }
        [void]$observations.Add($value)
    }
    if ($observations.Count -lt 1) { Fail $Code }
    $canonical = [string]$observations[0]
    foreach ($observation in @($observations.ToArray())) {
        if (-not $observation.Equals($canonical, [System.StringComparison]::OrdinalIgnoreCase) -or
            @($ExpectedNames | Where-Object {
                $observation.Equals(([string]$_).Trim().Replace("/", "\"), [System.StringComparison]::OrdinalIgnoreCase)
            }).Count -ne 1) {
            Fail $Code
        }
    }
    return $canonical
}

function Restore-NativeComboAfterInjectionFailure(
    [object]$Request,
    [string]$InjectedValue,
    [string]$OriginalValue,
    [int]$OriginalCount,
    [bool]$SelectionChanged
) {
    $rollback = Get-BoundTesterControlSet $Request
    if ((Read-TesterStartState $rollback.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    [IntPtr]$handle = Assert-ExactExpertCombo $rollback.controls.expert "mt5_expert_catalog_injection_rollback_failed"
    $matches = @(Get-NativeComboExactMatchEntries $rollback.controls.expert @($InjectedValue) "mt5_expert_catalog_injection_rollback_failed")
    if ($matches.Count -gt 1) { Fail "mt5_expert_catalog_injection_rollback_failed" }
    if ($matches.Count -eq 1) {
        $removed = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_DELETESTRING) ([int]$matches[0].index) 0 "mt5_expert_catalog_injection_rollback_failed").ToInt32()
        if ($removed -ne $OriginalCount) { Fail "mt5_expert_catalog_injection_rollback_failed" }
    }
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 "mt5_expert_catalog_injection_rollback_failed").ToInt32()
    if ($count -ne $OriginalCount -or @(Get-NativeComboExactMatchEntries $rollback.controls.expert @($InjectedValue) "mt5_expert_catalog_injection_rollback_failed").Count -ne 0) { Fail "mt5_expert_catalog_injection_rollback_failed" }
    $originalMatches = @(Get-NativeComboExactMatchEntries $rollback.controls.expert @($OriginalValue) "mt5_expert_catalog_injection_rollback_failed")
    if ($originalMatches.Count -ne 1) { Fail "mt5_expert_catalog_injection_rollback_failed" }
    $restored = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_SETCURSEL) ([int]$originalMatches[0].index) 0 "mt5_expert_catalog_injection_rollback_failed").ToInt32()
    if ($restored -ne [int]$originalMatches[0].index) { Fail "mt5_expert_catalog_injection_rollback_failed" }
    if ($SelectionChanged) { Send-NativeComboSelectionChange $rollback.controls.expert "mt5_expert_catalog_injection_rollback_failed" }
    $verified = Get-BoundTesterControlSet $Request
    if ((Read-TesterStartState $verified.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $nativeValue = (Read-NativeCombo $verified.controls.expert "mt5_expert_catalog_injection_rollback_failed").Trim().Replace("/", "\")
    if (-not $nativeValue.Equals($OriginalValue, [System.StringComparison]::OrdinalIgnoreCase) -or
        @(Get-NativeComboExactMatchEntries $verified.controls.expert @($InjectedValue) "mt5_expert_catalog_injection_rollback_failed").Count -ne 0) {
        Fail "mt5_expert_catalog_injection_rollback_failed"
    }
}

function Inject-NativeComboExpertExact(
    [object]$Request,
    [string]$ExactEx5Value,
    [string[]]$ExpectedNames
) {
    # MT5 build 6230 exposes the Strategy Tester Expert combo as an MRU-only
    # list: opening the dropdown does not enumerate the Navigator catalogue.
    # After a durable, verified Refresh boundary, add exactly the signed .ex5
    # path through the system-marshalled CB_ADDSTRING message, select it, notify
    # only its bound parent, then rebind and require both native and UIA proof.
    if ([string]::IsNullOrWhiteSpace($ExactEx5Value) -or
        -not $ExactEx5Value.EndsWith(".ex5", [System.StringComparison]::OrdinalIgnoreCase) -or
        $ExactEx5Value.Length -gt 512) {
        Fail "mt5_expert_catalog_injection_precondition_failed"
    }
    [void](Assert-ExpertCatalogRefreshBoundary $Request)
    $bound = Get-BoundTesterControlSet $Request
    if ((Read-TesterStartState $bound.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    [IntPtr]$handle = Assert-ExactExpertCombo $bound.controls.expert "mt5_expert_catalog_injection_precondition_failed"
    if ((Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 "mt5_expert_catalog_injection_precondition_failed").ToInt32() -ne 0) { Fail "mt5_expert_catalog_injection_precondition_failed" }
    $countBefore = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 "mt5_expert_catalog_injection_precondition_failed").ToInt32()
    $selectedBefore = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCURSEL) 0 0 "mt5_expert_catalog_injection_precondition_failed").ToInt32()
    if ($countBefore -lt 1 -or $countBefore -gt 4095 -or $selectedBefore -lt 0 -or $selectedBefore -ge $countBefore -or
        @(Get-NativeComboExactMatchEntries $bound.controls.expert $ExpectedNames "mt5_expert_catalog_injection_precondition_failed").Count -ne 0) {
        Fail "mt5_expert_catalog_injection_precondition_failed"
    }
    $originalValue = (Read-NativeComboItem $handle $selectedBefore "mt5_expert_catalog_injection_precondition_failed").Trim().Replace("/", "\")
    if ([string]::IsNullOrWhiteSpace($originalValue)) { Fail "mt5_expert_catalog_injection_precondition_failed" }
    $addAttempted = $false
    $selectionChanged = $false
    try {
        $addAttempted = $true
        $addedIndex = Invoke-NativeComboAddStringExact $bound.controls.expert $ExactEx5Value "mt5_expert_catalog_injection_add_failed"
        $countAfterAdd = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 "mt5_expert_catalog_injection_add_readback_failed").ToInt32()
        $matchesAfterAdd = @(Get-NativeComboExactMatchEntries $bound.controls.expert $ExpectedNames "mt5_expert_catalog_injection_add_readback_failed")
        if ($countAfterAdd -ne ($countBefore + 1) -or $matchesAfterAdd.Count -ne 1 -or
            [int]$matchesAfterAdd[0].index -ne $addedIndex -or
            -not ([string]$matchesAfterAdd[0].text).Equals($ExactEx5Value, [System.StringComparison]::OrdinalIgnoreCase)) {
            Fail "mt5_expert_catalog_injection_add_readback_failed"
        }
        if ((Read-TesterStartState $bound.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        $selected = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_SETCURSEL) $addedIndex 0 "mt5_expert_catalog_injection_select_failed").ToInt32()
        if ($selected -ne $addedIndex) { Fail "mt5_expert_catalog_injection_select_failed" }
        $selectionChanged = $true
        $selectedNative = (Read-NativeCombo $bound.controls.expert "mt5_expert_catalog_injection_select_failed").Trim().Replace("/", "\")
        if (-not $selectedNative.Equals($ExactEx5Value, [System.StringComparison]::OrdinalIgnoreCase)) { Fail "mt5_expert_catalog_injection_select_failed" }
        Send-NativeComboSelectionChange $bound.controls.expert "mt5_expert_catalog_injection_notify_failed"
        $readback = Get-BoundTesterControlSet $Request
        if ((Read-TesterStartState $readback.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        [IntPtr]$readbackHandle = Assert-ExactExpertCombo $readback.controls.expert "mt5_expert_catalog_injection_readback_failed"
        $readbackCount = (Invoke-NativeMessage $readbackHandle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 "mt5_expert_catalog_injection_readback_failed").ToInt32()
        $readbackMatches = @(Get-NativeComboExactMatchEntries $readback.controls.expert $ExpectedNames "mt5_expert_catalog_injection_readback_failed")
        $nativeValue = (Read-NativeCombo $readback.controls.expert "mt5_expert_catalog_injection_readback_failed").Trim().Replace("/", "\")
        $uiaValue = (Read-UiaComboSelectionExact $readback.controls.expert $ExpectedNames "mt5_expert_catalog_injection_uia_readback_failed").Trim().Replace("/", "\")
        if ($readbackCount -ne ($countBefore + 1) -or $readbackMatches.Count -ne 1 -or
            -not $nativeValue.Equals($ExactEx5Value, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not $uiaValue.Equals($ExactEx5Value, [System.StringComparison]::OrdinalIgnoreCase)) {
            Fail "mt5_expert_catalog_injection_readback_failed"
        }
        return [ordered]@{ selected = [string]$nativeValue; root = $readback.root; controls = $readback.controls }
    } catch {
        $failure = $_
        # A timed-out SendMessageTimeout is ambiguous: the receiver may have
        # processed CB_ADDSTRING before the caller observed failure.  Inspect
        # and restore the exact pre-state after every attempted add, including
        # explicit rejection, instead of assuming no mutation occurred.
        if ($addAttempted) {
            try {
                Restore-NativeComboAfterInjectionFailure $Request $ExactEx5Value $originalValue $countBefore $selectionChanged
            } catch {
                Fail "mt5_expert_catalog_injection_rollback_failed"
            }
        }
        throw $failure
    }
}

function Select-NativeComboExact([System.Windows.Automation.AutomationElement]$Control, [string[]]$ExpectedNames, [string]$Code) {
    [IntPtr]$handle = Close-NativeComboDropDownExact $Control $Code
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 $Code).ToInt32()
    if ($count -lt 1 -or $count -gt 4096) { Fail $Code }
    $matches = New-Object System.Collections.Generic.List[int]
    for ($index = 0; $index -lt $count; $index++) {
        $candidate = Read-NativeComboItem $handle $index $Code
        if (@($ExpectedNames | Where-Object { $candidate.Equals([string]$_, [System.StringComparison]::OrdinalIgnoreCase) }).Count -gt 0) {
            [void]$matches.Add($index)
        }
    }
    if ($matches.Count -ne 1) { Fail $Code }
    $selected = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_SETCURSEL) $matches[0] 0 $Code).ToInt32()
    if ($selected -ne $matches[0]) { Fail $Code }
    $submitted = Read-NativeComboItem $handle $selected $Code
    if (@($ExpectedNames | Where-Object {
        $submitted.Equals([string]$_, [System.StringComparison]::OrdinalIgnoreCase)
    }).Count -ne 1) { Fail $Code }
    [IntPtr]$parent = [MetafxMt5VisibleNative]::GetParent($handle)
    $controlId = [MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
    if ($parent -eq [IntPtr]::Zero -or (Get-NativeOwner $parent) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($parent, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle -or
        $controlId -le 0) { Fail $Code }
    $notification = (([MetafxMt5VisibleNative]::CBN_SELCHANGE -shl 16) -bor ($controlId -band 0xffff))
    if (-not [MetafxMt5VisibleNative]::PostMessage($parent, [MetafxMt5VisibleNative]::WM_COMMAND, [IntPtr]$notification, $handle)) { Fail $Code }
    # CBN_SELCHANGE is asynchronous and MT5 may destroy this ComboBox or any
    # sibling Settings widget while handling it.  Never dereference Control or
    # handle again.  Production callers must rebind from the signed root and
    # prove the committed value on the replacement control.
    return $submitted
}

function Assert-SymbolComboCommittedExact(
    [System.Windows.Automation.AutomationElement]$Control,
    [string[]]$ExpectedNames,
    [string]$Code
) {
    [IntPtr]$handle = Close-NativeComboDropDownExact $Control $Code
    if ([MetafxMt5VisibleNative]::GetDlgCtrlID($handle) -ne 10486) { Fail $Code }
    $style = [MetafxMt5VisibleNative]::GetWindowLong($handle, [MetafxMt5VisibleNative]::GWL_STYLE)
    if (($style -band 3) -ne [MetafxMt5VisibleNative]::CBS_DROPDOWN) { Fail $Code }
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 $Code).ToInt32()
    if ($count -lt 0 -or $count -gt 4096) { Fail $Code }
    if ($count -gt 0) {
        return Assert-ComboCommittedExact $Control $ExpectedNames $Code
    }

    # MT5 build 6230 can expose the Symbol control as an editable ComboBox
    # whose catalogue is empty even though its native text is already the
    # exact, committed tester symbol.  In that state there is no list item to
    # select, so accept only an unchanged exact current value proved by both
    # native text and the bound UIA provider.  Never inject free text here.
    $nativeValue = (Read-NativeText $handle $Code).Trim()
    $providerValue = ([string]$Control.Current.Name).Trim()
    if ([string]::IsNullOrWhiteSpace($nativeValue) -or
        [string]::IsNullOrWhiteSpace($providerValue) -or
        -not $providerValue.Equals($nativeValue, [System.StringComparison]::OrdinalIgnoreCase) -or
        @($ExpectedNames | Where-Object {
            $nativeValue.Equals(([string]$_).Trim(), [System.StringComparison]::OrdinalIgnoreCase)
        }).Count -ne 1) {
        Fail $Code
    }
    if ((Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32() -ne 0) { Fail $Code }
    return $nativeValue
}

function Select-SymbolComboExact(
    [System.Windows.Automation.AutomationElement]$Control,
    [string[]]$ExpectedNames,
    [string]$Code
) {
    [IntPtr]$handle = Close-NativeComboDropDownExact $Control $Code
    if ([MetafxMt5VisibleNative]::GetDlgCtrlID($handle) -ne 10486) { Fail $Code }
    $count = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCOUNT) 0 0 $Code).ToInt32()
    if ($count -lt 0 -or $count -gt 4096) { Fail $Code }
    if ($count -eq 0) {
        return Assert-SymbolComboCommittedExact $Control $ExpectedNames $Code
    }
    $matches = New-Object System.Collections.Generic.List[int]
    for ($index = 0; $index -lt $count; $index++) {
        $candidate = Read-NativeComboItem $handle $index $Code
        if (@($ExpectedNames | Where-Object {
            $candidate.Equals([string]$_, [System.StringComparison]::OrdinalIgnoreCase)
        }).Count -gt 0) {
            [void]$matches.Add($index)
        }
    }
    if ($matches.Count -ne 1) { Fail $Code }
    $selected = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_SETCURSEL) $matches[0] 0 $Code).ToInt32()
    if ($selected -ne $matches[0]) { Fail $Code }
    $observed = Read-NativeCombo $Control $Code
    if (@($ExpectedNames | Where-Object {
        $observed.Equals([string]$_, [System.StringComparison]::OrdinalIgnoreCase)
    }).Count -ne 1) { Fail $Code }
    [void](Close-NativeComboDropDownExact $Control $Code)
    [IntPtr]$parent = [MetafxMt5VisibleNative]::GetParent($handle)
    $controlId = [MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
    if ($parent -eq [IntPtr]::Zero -or
        (Get-NativeOwner $parent) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($parent, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle -or
        $controlId -ne 10486) {
        Fail $Code
    }
    $notification = (([MetafxMt5VisibleNative]::CBN_SELCHANGE -shl 16) -bor ($controlId -band 0xffff))
    if (-not [MetafxMt5VisibleNative]::PostMessage(
        $parent,
        [MetafxMt5VisibleNative]::WM_COMMAND,
        [IntPtr]$notification,
        $handle
    )) { Fail $Code }
    # CBN_SELCHANGE may recreate the editable Symbol ComboBox.  The caller
    # must rebind the complete Settings control set before any further proof;
    # never query this pre-notification AutomationElement again.
    Start-Sleep -Milliseconds 150
    return $observed
}

function Set-NativeComboText([System.Windows.Automation.AutomationElement]$Control, [string]$Value, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "ComboBox" $Code
    if ([string]::IsNullOrWhiteSpace($Value) -or $Value.Length -gt 512) { Fail $Code }
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $handle, [MetafxMt5VisibleNative]::WM_SETTEXT, [IntPtr]::Zero, $Value,
        [MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$result
    )
    if ($call -eq [IntPtr]::Zero -or $result.ToInt32() -ne 1) { Fail $Code }
    [IntPtr]$parent = [MetafxMt5VisibleNative]::GetParent($handle)
    $controlId = [MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
    $notification = (([MetafxMt5VisibleNative]::CBN_EDITCHANGE -shl 16) -bor ($controlId -band 0xffff))
    if ($parent -eq [IntPtr]::Zero -or $controlId -le 0 -or
        -not [MetafxMt5VisibleNative]::PostMessage($parent, [MetafxMt5VisibleNative]::WM_COMMAND, [IntPtr]$notification, $handle)) { Fail $Code }
    Start-Sleep -Milliseconds 150
    $observed = Read-NativeText $handle $Code
    if (-not $observed.Equals($Value, [System.StringComparison]::OrdinalIgnoreCase)) { Fail $Code }
    return $observed
}

function Get-NativeTesterDateText([string]$Value, [string]$Code) {
    $parsed = [DateTime]::MinValue
    if (-not [DateTime]::TryParseExact(
        $Value,
        "yyyy-MM-dd",
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::None,
        [ref]$parsed
    )) { Fail $Code }
    return $parsed.ToString("yyyy.MM.dd", [System.Globalization.CultureInfo]::InvariantCulture)
}

function Read-NativeDate([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "SysDateTimePick32" $Code
    try {
        return [MetafxMt5VisibleNative]::GetRemoteDate(
            $handle,
            [uint32]$TerminalProcess.Id,
            [IntPtr]$script:TerminalRootHandle
        )
    } catch { Fail $Code }
}

function Set-NativeDate([System.Windows.Automation.AutomationElement]$Control, [string]$Value, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Control "SysDateTimePick32" $Code
    $parsed = [DateTime]::MinValue
    if (-not [DateTime]::TryParseExact(
        $Value,
        "yyyy.MM.dd",
        [System.Globalization.CultureInfo]::InvariantCulture,
        [System.Globalization.DateTimeStyles]::None,
        [ref]$parsed
    )) { Fail $Code }
    try {
        [MetafxMt5VisibleNative]::SetRemoteDate(
            $handle,
            [uint32]$TerminalProcess.Id,
            [IntPtr]$script:TerminalRootHandle,
            $parsed.Year,
            $parsed.Month,
            $parsed.Day
        )
    } catch { Fail $Code }
    Start-Sleep -Milliseconds 100
    if ((Read-NativeDate $Control $Code) -cne $Value) { Fail $Code }
}

function Get-ControlById([System.Windows.Automation.AutomationElement]$Root, [string]$AutomationId, [string]$Code) {
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $AutomationId)
    $matches = @(Get-All $Root $condition)
    if ($matches.Count -ne 1) { Fail $Code }
    if (-not $matches[0].Current.IsEnabled -or $matches[0].Current.IsOffscreen) { Fail $Code }
    return $matches[0]
}

function Get-ControlByIdPresent([System.Windows.Automation.AutomationElement]$Root, [string]$AutomationId, [string]$Code) {
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $AutomationId)
    $matches = @(Get-All $Root $condition)
    if ($matches.Count -ne 1 -or $matches[0].Current.IsOffscreen) { Fail $Code }
    return $matches[0]
}

function Find-ControlByIdPresent([System.Windows.Automation.AutomationElement]$Root, [string]$AutomationId) {
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $AutomationId)
    $matches = @(Get-All $Root $condition)
    if ($matches.Count -eq 1 -and -not $matches[0].Current.IsOffscreen) { return $matches[0] }
    return $null
}

function Get-TesterResultTabs([System.Windows.Automation.AutomationElement]$Root, [object]$Required, [string]$Code) {
    # MT5 reuses AutomationId 10002 for multiple native tab strips.  The
    # Strategy Tester strip is identified by the exact native parent of the
    # already-bound Start button rather than by an ambiguous global lookup.
    $start = Get-ControlByIdPresent $Root ([string]$Required.start) $Code
    [IntPtr]$startHandle = Assert-NativeControl $start "Button" $Code
    [IntPtr]$tabsHandle = [MetafxMt5VisibleNative]::GetParent($startHandle)
    if ($tabsHandle -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($tabsHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowVisible($tabsHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowEnabled($tabsHandle) -or
        (Get-NativeOwner $tabsHandle) -ne $TerminalProcess.Id -or
        (Get-NativeClass $tabsHandle) -cne "SysTabControl32" -or
        [MetafxMt5VisibleNative]::GetDlgCtrlID($tabsHandle) -ne [int]$Required.tabs -or
        [MetafxMt5VisibleNative]::GetAncestor($tabsHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle) {
        Fail $Code
    }
    try { $tabs = [System.Windows.Automation.AutomationElement]::FromHandle($tabsHandle) }
    catch { Fail $Code }
    if ($null -eq $tabs -or $tabs.Current.IsOffscreen) { Fail $Code }
    return $tabs
}

function Test-TesterControlViewport(
    [object]$Control,
    [System.Windows.Automation.AutomationElement]$Root
) {
    $code = "mt5_tester_pane_geometry_unverified"
    [IntPtr]$rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
    [IntPtr]$handle = [IntPtr]$Control.Current.NativeWindowHandle
    if ($rootHandle -eq [IntPtr]::Zero -or $rootHandle -ne $script:TerminalRootHandle -or
        $handle -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
        (Get-NativeOwner $handle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle) { Fail $code }
    if (-not [MetafxMt5VisibleNative]::IsWindowVisible($handle) -or $Control.Current.IsOffscreen) { return $false }
    $rect = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::GetWindowRect($handle, [ref]$rect)) { Fail $code }
    if ($rect.Right -le $rect.Left -or $rect.Bottom -le $rect.Top) { return $false }
    [IntPtr]$ancestor = $handle
    for ($depth = 0; $depth -lt 16; $depth++) {
        if ($ancestor -eq $rootHandle) { return $true }
        $ancestor = [MetafxMt5VisibleNative]::GetParent($ancestor)
        if ($ancestor -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($ancestor) -or
            (Get-NativeOwner $ancestor) -ne $TerminalProcess.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($ancestor, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle) { Fail $code }
        if (-not [MetafxMt5VisibleNative]::IsWindowVisible($ancestor)) { return $false }
        $client = Read-TesterDiagnosticClientRect $ancestor $code
        # Native WS_VISIBLE/UIA IsOffscreen alone remain true for collapsed
        # docked panels. Every ancestor's actual client clip must contain the
        # whole control. A read failure or partial clip is not toggle authority.
        if ($client.right -le $client.left -or $client.bottom -le $client.top -or
            $rect.Right -le $client.left -or $rect.Left -ge $client.right -or
            $rect.Bottom -le $client.top -or $rect.Top -ge $client.bottom) { return $false }
        if ($rect.Left -lt $client.left -or $rect.Right -gt $client.right -or
            $rect.Top -lt $client.top -or $rect.Bottom -gt $client.bottom) {
            Fail "mt5_tester_pane_partially_clipped"
        }
    }
    Fail $code
}

function Test-TesterPaneContentVisible(
    [object]$Required,
    [System.Windows.Automation.AutomationElement]$Root
) {
    # MT5 can keep the Strategy Tester pane HWND/UIA element visible while its
    # docked content is collapsed.  Treat the pane as ready only when either the
    # Settings workspace or the complete Single-mode launcher is visible.
    $pane = Find-ControlByIdPresent $Root ([string]$Required.testerPane)
    if ($null -eq $pane) { return $false }
    if (-not (Test-TesterControlViewport $pane $Root)) { return $false }
    $start = Find-ControlByIdPresent $pane ([string]$Required.start)
    if ($null -ne $start) { return (Test-TesterControlViewport $start $Root) }

    $launcher = Find-ControlByIdPresent $pane "10887"
    if ($null -eq $launcher) { return $false }
    $button = Find-ControlByIdPresent $launcher "3734"
    $label = Find-ControlByIdPresent $launcher "10888"
    if ($null -eq $button -or $null -eq $label) { return $false }
    return ((Test-TesterControlViewport $launcher $Root) -and
            (Test-TesterControlViewport $button $Root) -and (Test-TesterControlViewport $label $Root))
}

function Test-TesterPaneCollapsed([object]$Required, [object]$Root) {
    $code = "mt5_tester_pane_geometry_unverified"
    [IntPtr]$rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
    if ($rootHandle -ne $script:TerminalRootHandle -or [string]$Required.testerPane -cne "32846") { Fail $code }
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, "32846")
    $panes = @(Get-All $Root $condition)
    if ($panes.Count -eq 0) { return $false }
    if ($panes.Count -ne 1) { Fail $code }
    [IntPtr]$pane = [IntPtr]$panes[0].Current.NativeWindowHandle
    if ($pane -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($pane) -or
        (Get-NativeOwner $pane) -ne $TerminalProcess.Id -or (Get-NativeOwner $rootHandle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetDlgCtrlID($pane) -ne 32846 -or
        [MetafxMt5VisibleNative]::GetParent($pane) -ne $rootHandle -or
        [MetafxMt5VisibleNative]::GetAncestor($pane, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle -or
        -not ([string](Get-NativeClass $pane)).StartsWith("Afx:ControlBar:", [StringComparison]::Ordinal)) { Fail $code }
    if (-not [MetafxMt5VisibleNative]::IsWindowVisible($pane)) { return $false }
    $rect = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::GetWindowRect($pane, [ref]$rect)) { Fail $code }
    $client = Read-TesterDiagnosticClientRect $pane $code
    if ((Get-NativeOwner $pane) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetParent($pane) -ne $rootHandle -or
        [MetafxMt5VisibleNative]::GetAncestor($pane, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle -or
        [MetafxMt5VisibleNative]::GetDlgCtrlID($pane) -ne 32846) { Fail $code }
    return ([MetafxMt5VisibleNative]::IsWindowVisible($pane) -and $rect.Right -gt $rect.Left -and
        $rect.Bottom -ge $rect.Top -and ($rect.Bottom - $rect.Top) -le 1 -and
        $client.right -gt $client.left -and $client.bottom -eq $client.top)
}

function Read-TesterPaneFailureDiagnostic([object]$Request, [string]$Code) {
    [IntPtr]$signedRoot = [IntPtr][long]$Request.expectedTerminalWindowHandle
    if ($signedRoot -eq [IntPtr]::Zero -or $signedRoot -ne $script:TerminalRootHandle -or
        -not [MetafxMt5VisibleNative]::IsWindow($signedRoot) -or
        (Get-NativeOwner $signedRoot) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($signedRoot, [MetafxMt5VisibleNative]::GA_ROOT) -ne $signedRoot) {
        Fail "mt5_tester_pane_failure_observation_unavailable"
    }
    # Observe only the foreground present at this failure boundary. Never
    # enumerate windows or return unrelated captions/account information.
    [IntPtr]$foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
    $foregroundInfo = [ordered]@{
        handle = [long]$foreground.ToInt64(); exists = $false; processId = 0
        nativeClass = ""; rootHandle = 0; ownerHandle = 0; titleCategory = "unavailable"
    }
    if ($foreground -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::IsWindow($foreground)) {
        $foregroundInfo.exists = $true
        $foregroundInfo.processId = [int](Get-NativeOwner $foreground)
        $className = [string](Get-NativeClass $foreground)
        $foregroundInfo.nativeClass = ([regex]::Replace($className, "[^A-Za-z0-9_.#:-]", "?")).Substring(0, [Math]::Min(96, $className.Length))
        $foregroundInfo.rootHandle = [long][MetafxMt5VisibleNative]::GetAncestor($foreground, [MetafxMt5VisibleNative]::GA_ROOT).ToInt64()
        $foregroundInfo.ownerHandle = [long][MetafxMt5VisibleNative]::GetWindow($foreground, [MetafxMt5VisibleNative]::GW_OWNER).ToInt64()
        # Category only: even the signed terminal caption may contain an
        # account identifier. Do not forward any original caption characters.
        try {
            $caption = [MetafxMt5VisibleNative]::GetWindowTextExact($foreground)
            $foregroundInfo.titleCategory = if ($caption -match "(?i)strategy tester") { "strategy_tester" }
                elseif ($caption -match "(?i)metatrader") { "metatrader" } else { "other" }
        } catch { $foregroundInfo.titleCategory = "unavailable" }
    }
    $rootRect = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::GetWindowRect($signedRoot, [ref]$rootRect)) { Fail "mt5_tester_pane_failure_observation_unavailable" }
    return [ordered]@{
        schemaVersion = "mt5-tester-pane-failure-diagnostic-v1"
        diagnosticOnly = $true; startInvoked = $false; testerVerified = $false
        reasonCode = $Code; checkpoint = [string]$script:FailureCheckpoint
        signedRoot = [ordered]@{
            handle = [long]$signedRoot.ToInt64(); processId = [int]$TerminalProcess.Id
            nativeRect = [ordered]@{ left = $rootRect.Left; top = $rootRect.Top; right = $rootRect.Right; bottom = $rootRect.Bottom }
            clientRect = Read-TesterDiagnosticClientRect $signedRoot
        }
        foreground = $foregroundInfo
        foregroundStable = [bool]([MetafxMt5VisibleNative]::GetForegroundWindow() -eq $foreground)
    }
}

function Fail-TesterPaneReadiness([object]$Request, [string]$Code) {
    if ($Request.PSObject.Properties.Name -contains "diagnosticFailureObservation" -and
        $Request.diagnosticFailureObservation -ceq $true -and [string]$Request.action -ceq "probe") {
        try { $script:TesterPaneFailureDiagnostic = Read-TesterPaneFailureDiagnostic $Request $Code }
        catch { $script:TesterPaneFailureDiagnostic = $null }
    }
    Fail $Code
}

function Ensure-TesterPaneVisible([object]$Request, [System.Windows.Automation.AutomationElement]$Root = $null) {
    $script:TesterPaneFailureDiagnostic = $null
    $Required = $Request.requiredAutomationIds
    [IntPtr]$signedRoot = [IntPtr][long]$Request.expectedTerminalWindowHandle
    if ($signedRoot -eq [IntPtr]::Zero -or $signedRoot -ne [IntPtr]$script:TerminalRootHandle) {
        Fail "mt5_terminal_window_changed"
    }
    $activeRoot = Get-BoundTerminalRoot $Request $signedRoot
    if ($null -ne $Root -and [IntPtr]$Root.Current.NativeWindowHandle -ne $signedRoot) {
        Fail "mt5_terminal_window_changed"
    }
    if (Test-TesterPaneContentVisible $Required $activeRoot) { return }
    # Bind menu dispatch, focus and readback to the signed terminal root; never trust the
    # process convenience MainWindowHandle, which can drift to an owned popup.
    $script:FailureCheckpoint = "tester_pane_focus_before_reveal"
    $activeRoot = Get-BoundTerminalRoot $Request $signedRoot
    try { Set-Foreground $TerminalProcess $activeRoot } catch {
        if ($_.Exception.Message -ceq "visible_window_foreground_failed") { Fail-TesterPaneReadiness $Request "mt5_tester_pane_focus_before_reveal_failed" }
        throw
    }
    if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $signedRoot) {
        Fail-TesterPaneReadiness $Request "mt5_tester_pane_focus_before_reveal_failed"
    }
    # Restoring a minimized terminal can itself reveal an already-open Tester.
    # Wait for actual client geometry, then rebind and recheck before toggling.
    $script:FailureCheckpoint = "tester_pane_restore_readback"
    $restoreDeadline = [DateTime]::UtcNow.AddSeconds(2)
    do {
        $activeRoot = Get-BoundTerminalRoot $Request $signedRoot
        if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $signedRoot) { Fail-TesterPaneReadiness $Request "mt5_tester_pane_restore_focus_lost" }
        $rootClient = Read-TesterDiagnosticClientRect $signedRoot "mt5_tester_pane_geometry_unverified"
        if ($rootClient.right -gt $rootClient.left -and $rootClient.bottom -gt $rootClient.top) { break }
        if ([DateTime]::UtcNow -ge $restoreDeadline) { Fail-TesterPaneReadiness $Request "mt5_tester_pane_restore_timeout" }
        Start-Sleep -Milliseconds 50
    } while ($true)
    if (Test-TesterPaneContentVisible $Required $activeRoot) { return }
    # An open but collapsed dock cannot be fixed by toggling its View command.
    if (Test-TesterPaneCollapsed $Required $activeRoot) { Fail "mt5_tester_pane_collapsed" }
    $script:FailureCheckpoint = "tester_pane_reveal_menu"
    try { [MetafxMt5VisibleNative]::InvokeTesterRevealMenuExact([uint32]$TerminalProcess.Id, $signedRoot) } catch {
        $failure = $_.Exception
        while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
        if ($failure.Message -match "^mt5_[a-z0-9_]{3,90}$") { Fail $failure.Message }
        Fail "mt5_tester_reveal_menu_unverified"
    }
    $script:FailureCheckpoint = "tester_pane_reveal_readback"
    $deadline = [DateTime]::UtcNow.AddSeconds(8)
    while ([DateTime]::UtcNow -lt $deadline) {
        $activeRoot = Get-BoundTerminalRoot $Request $signedRoot
        if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $signedRoot) {
            Fail-TesterPaneReadiness $Request "mt5_tester_pane_reveal_focus_lost"
        }
        if (Test-TesterPaneContentVisible $Required $activeRoot) { return }
        Start-Sleep -Milliseconds 100
    }
    if (Test-TesterPaneCollapsed $Required $activeRoot) { Fail "mt5_tester_pane_collapsed" }
    Fail-TesterPaneReadiness $Request "mt5_tester_pane_reveal_timeout"
}

function Ensure-TesterSingleModeReady(
    [object]$Request,
    [System.Windows.Automation.AutomationElement]$Root
) {
    $required = $Request.requiredAutomationIds
    $code = "mt5_tester_single_mode_selection_not_verified"
    if ($null -ne (Find-ControlByIdPresent $Root ([string]$required.start))) { return }

    # MT5 build 6230 can open Strategy Tester on a mode launcher rather than
    # the Settings workspace.  Bind the transition to one exact, visible
    # launcher card and its exact Single-mode button/label.  This is only UI
    # navigation: it does not create a tester start boundary or press Start.
    $testerPane = Get-ControlByIdPresent $Root ([string]$required.testerPane) $code
    $launcher = Get-ControlByIdPresent $testerPane "10887" $code
    $singleButton = Get-ControlByIdPresent $launcher "3734" $code
    $singleLabel = Get-ControlByIdPresent $launcher "10888" $code
    [IntPtr]$testerPaneHandle = [IntPtr]$testerPane.Current.NativeWindowHandle
    [IntPtr]$launcherHandle = Assert-NativeControl $launcher "#32770" $code
    [IntPtr]$buttonHandle = Assert-NativeControl $singleButton "Button" $code
    [IntPtr]$labelHandle = Assert-NativeControl $singleLabel "Static" $code
    if (
        [string]$singleLabel.Current.Name -cne "Single" -or
        $testerPaneHandle -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($testerPaneHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowVisible($testerPaneHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowEnabled($testerPaneHandle) -or
        (Get-NativeOwner $testerPaneHandle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($testerPaneHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle -or
        [MetafxMt5VisibleNative]::GetParent($launcherHandle) -ne $testerPaneHandle -or
        [MetafxMt5VisibleNative]::GetParent($buttonHandle) -ne $launcherHandle -or
        [MetafxMt5VisibleNative]::GetParent($labelHandle) -ne $launcherHandle
    ) {
        Fail $code
    }

    Set-Foreground $TerminalProcess
    Invoke-Exact $singleButton $code
    $deadline = [DateTime]::UtcNow.AddSeconds(12)
    while ([DateTime]::UtcNow -lt $deadline) {
        $reboundRoot = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
        $start = Find-ControlByIdPresent $reboundRoot ([string]$required.start)
        if ($null -ne $start) {
            [void](Assert-NativeControl $start "Button" $code)
            [void](Get-TesterResultTabs $reboundRoot $required $code)
            return
        }
        Start-Sleep -Milliseconds 100
    }
    Fail $code
}

function Get-ExactNamedControl([System.Windows.Automation.AutomationElement]$Root, [string[]]$Names, [string]$Code) {
    $matches = @()
    foreach ($name in $Names) {
        $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty, $name)
        $matches += @(Get-All $Root $condition)
    }
    $matches = @($matches | Where-Object { $_.Current.IsEnabled -and -not $_.Current.IsOffscreen })
    if ($matches.Count -ne 1) { Fail $Code }
    return $matches[0]
}

function Get-Value([System.Windows.Automation.AutomationElement]$Control) {
    $className = [string]$Control.Current.ClassName
    # Prefer the locale-independent, owner/root-validated native path for date
    # controls even when MT5 happens to expose a UIA ValuePattern whose text
    # format varies with the Windows locale.
    if ($className -ceq "SysDateTimePick32") { return Read-NativeDate $Control "mt5_date_readback_mismatch" }
    # Editable MT5 combo providers can publish transient UIA text before the
    # native selection is committed.  Native CB_GETCURSEL/CB_GETLBTEXT is the
    # authoritative value for every tester ComboBox.
    if ($className -ceq "ComboBox") { return Read-NativeCombo $Control "mt5_control_value_unavailable" }
    $pattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {
        return [string]$pattern.Current.Value
    }
    return [string]$Control.Current.Name
}

function Set-ValueExact([System.Windows.Automation.AutomationElement]$Control, [string]$Value, [string]$Code) {
    $className = [string]$Control.Current.ClassName
    if ($className -ceq "SysDateTimePick32") {
        # DTM_* messages are not marshalled by Windows.  Set-NativeDate uses a
        # buffer allocated inside the bound MT5 process and reads it back before
        # returning; it never sends a caller-local pointer across processes.
        Set-NativeDate $Control $Value $Code
        return
    }
    if ($className -ceq "ComboBox") {
        # A combo commit can asynchronously recreate this control and arbitrary
        # siblings.  Callers must use Select-BoundTesterComboMapped, which owns
        # the signed-root rebind; this generic setter cannot prove that contract.
        Fail $Code
    }
    $pattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {
        if ($pattern.Current.IsReadOnly) { Fail $Code }
        $pattern.SetValue($Value)
        Start-Sleep -Milliseconds 100
        if ((Get-Value $Control).Trim() -cne $Value.Trim()) { Fail $Code }
        return
    }
    $expand = $null
    if (-not $Control.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$expand)) { Fail $Code }
    $expand.Expand(); Start-Sleep -Milliseconds 150
    $item = Get-ExactNamedControl $Control @($Value) $Code
    $selection = $null
    if (-not $item.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection)) { Fail $Code }
    $selection.Select(); Start-Sleep -Milliseconds 100
    if ((Get-Value $Control).Trim() -cne $Value.Trim()) { Fail $Code }
}

function Get-SelectedComboText([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    if ([string]$Control.Current.ClassName -ceq "ComboBox") { return Read-NativeCombo $Control $Code }
    $selectionPattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.SelectionPattern]::Pattern, [ref]$selectionPattern)) {
        $selected = @($selectionPattern.Current.GetSelection())
        if ($selected.Count -eq 1 -and -not [string]::IsNullOrWhiteSpace([string]$selected[0].Current.Name)) {
            return ([string]$selected[0].Current.Name).Trim()
        }
    }
    $valuePattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$valuePattern)) {
        $value = ([string]$valuePattern.Current.Value).Trim()
        if (-not [string]::IsNullOrWhiteSpace($value)) { return $value }
    }
    Fail $Code
}

function Assert-ComboCommittedExact([System.Windows.Automation.AutomationElement]$Control, [string[]]$ExpectedNames, [string]$Code) {
    [void](Close-NativeComboDropDownExact $Control $Code)
    $nativeValue = (Read-NativeCombo $Control $Code).Trim()
    if (@($ExpectedNames | Where-Object {
        $nativeValue.Equals(([string]$_).Trim(), [System.StringComparison]::OrdinalIgnoreCase)
    }).Count -ne 1) { Fail $Code }
    $valuePattern = $null
    if ($Control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$valuePattern)) {
        $uiaValue = ([string]$valuePattern.Current.Value).Trim()
        if (-not $uiaValue.Equals($nativeValue, [System.StringComparison]::OrdinalIgnoreCase)) { Fail $Code }
    }
    if ((Invoke-NativeMessage ([IntPtr]$Control.Current.NativeWindowHandle) ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 $Code).ToInt32() -ne 0) { Fail $Code }
    return $nativeValue
}

function Select-ComboMapped([System.Windows.Automation.AutomationElement]$Control, [string[]]$UiNames, [string]$Code) {
    if ($UiNames.Count -lt 1) { Fail $Code }
    if ([string]$Control.Current.ClassName -ceq "ComboBox") { return Select-NativeComboExact $Control $UiNames $Code }
    $expand = $null
    if (-not $Control.TryGetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern, [ref]$expand)) { Fail $Code }
    $expand.Expand(); Start-Sleep -Milliseconds 150
    $matches = @()
    foreach ($name in $UiNames) {
        $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty, $name)
        $matches += @(Get-All $Control $condition | Where-Object { $_.Current.IsEnabled -and -not $_.Current.IsOffscreen })
    }
    if ($matches.Count -ne 1) { Fail $Code }
    $selection = $null
    if (-not $matches[0].TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection)) { Fail $Code }
    $selection.Select(); Start-Sleep -Milliseconds 100
    try { $expand.Collapse() } catch {}
    $observed = Get-SelectedComboText $Control $Code
    if ($observed -notin $UiNames) { Fail $Code }
    return $observed
}

function Get-ModelUiNames([string]$Token) {
    switch ($Token) {
        "every_tick" { return @("Every tick") }
        "every_tick_real_ticks" { return @("Every tick based on real ticks") }
        "one_minute_ohlc" { return @("1 minute OHLC", "1 minute OHLC (faster to analyze)") }
        "open_prices" { return @("Open prices only") }
        "math_calculations" { return @("Math calculations") }
        default { Fail "mt5_model_mapping_unsupported" }
    }
}

function Get-OptimizationUiNames([string]$Token) {
    switch ($Token) {
        "disabled" { return @("Disabled") }
        "fast_genetic" { return @("Fast genetic based algorithm") }
        "complete" { return @("Slow complete algorithm") }
        "all_symbols_market_watch" { return @("All symbols selected in Market Watch") }
        default { Fail "mt5_optimization_mode_mapping_unsupported" }
    }
}

function Get-CriterionUiNames([string]$Token) {
    switch ($Token) {
        "balance_max" { return @("Balance max") }
        "profit_factor_max" { return @("Profit Factor max") }
        "drawdown_min" { return @("Drawdown min") }
        "recovery_factor_max" { return @("Recovery Factor max") }
        "sharpe_max" { return @("Sharpe Ratio max") }
        default { Fail "mt5_criterion_mapping_unsupported" }
    }
}

function Get-PeriodUiNames([string]$Token) {
    switch ($Token.ToUpperInvariant()) {
        "D1" { return @("D1", "Daily") }
        "W1" { return @("W1", "Weekly") }
        "MN1" { return @("MN1", "Monthly") }
        default { return @($Token.ToUpperInvariant()) }
    }
}

function Get-PositiveDecimal([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    $token = (Get-Value $Control).Trim().Replace(" ", "").Replace([string][char]0x00A0, "")
    if ($token -notmatch "^[0-9]+([.,][0-9]+)?$") { Fail $Code }
    $normalized = $token.Replace(",", ".")
    $value = 0.0
    if (-not [double]::TryParse($normalized, [System.Globalization.NumberStyles]::AllowDecimalPoint, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$value)) { Fail $Code }
    if ([double]::IsNaN($value) -or [double]::IsInfinity($value) -or $value -le 0.0 -or $value -gt 1000000000.0) { Fail $Code }
    return $value
}

function Get-Toggle([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    $pattern = $null
    if (-not $Control.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$pattern)) {
        if ([string]$Control.Current.ClassName -cne "Button") { Fail $Code }
        [IntPtr]$handle = Assert-NativeControl $Control "Button" $Code
        $state = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::BM_GETCHECK) 0 0 $Code).ToInt32()
        if ($state -notin @(0, 1)) { Fail $Code }
        return ($state -eq 1)
    }
    return ($pattern.Current.ToggleState -eq [System.Windows.Automation.ToggleState]::On)
}

function Set-ToggleExact([System.Windows.Automation.AutomationElement]$Control, [bool]$Enabled, [string]$Code) {
    $pattern = $null
    if (-not $Control.TryGetCurrentPattern([System.Windows.Automation.TogglePattern]::Pattern, [ref]$pattern)) {
        if ([string]$Control.Current.ClassName -cne "Button") { Fail $Code }
        [IntPtr]$handle = Assert-NativeControl $Control "Button" $Code
        $current = Get-Toggle $Control $Code
        if ($current -ne $Enabled) { [void](Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::BM_CLICK) 0 0 $Code); Start-Sleep -Milliseconds 100 }
        if ((Get-Toggle $Control $Code) -ne $Enabled) { Fail $Code }
        return
    }
    $current = $pattern.Current.ToggleState -eq [System.Windows.Automation.ToggleState]::On
    if ($current -ne $Enabled) { $pattern.Toggle(); Start-Sleep -Milliseconds 100 }
    if ((Get-Toggle $Control $Code) -ne $Enabled) { Fail $Code }
}

function Invoke-Exact([System.Windows.Automation.AutomationElement]$Control, [string]$Code) {
    $pattern = $null
    if (-not $Control.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) {
        if ([string]$Control.Current.ClassName -cne "Button") { Fail $Code }
        [IntPtr]$handle = Assert-NativeControl $Control "Button" $Code
        [void](Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::BM_CLICK) 0 0 $Code)
        return
    }
    $pattern.Invoke()
}

function Set-Foreground([System.Diagnostics.Process]$Process, [System.Windows.Automation.AutomationElement]$Window = $null) {
    [IntPtr]$handle = if ($null -ne $Window) { [IntPtr]$Window.Current.NativeWindowHandle } else { $Process.MainWindowHandle }
    if ($handle -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($handle) -or (Get-NativeOwner $handle) -ne $Process.Id) { Fail "visible_window_foreground_failed" }
    [void][MetafxMt5VisibleNative]::ShowWindowAsync($handle, 3)
    try { if ($null -ne $Window) { $Window.SetFocus() } } catch {}
    [void][MetafxMt5VisibleNative]::SetForegroundWindow($handle)
    if ([MetafxMt5VisibleNative]::GetForegroundWindow() -ne $handle) {
        [uint32]$ownerPid = 0
        [uint32]$targetThread = [MetafxMt5VisibleNative]::GetWindowThreadProcessId($handle, [ref]$ownerPid)
        if ($ownerPid -ne $Process.Id) { Fail "visible_window_foreground_failed" }
        [uint32]$currentThread = [MetafxMt5VisibleNative]::GetCurrentThreadId()
        [IntPtr]$foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
        [uint32]$foregroundPid = 0
        [uint32]$foregroundThread = 0
        if ($foreground -ne [IntPtr]::Zero) { $foregroundThread = [MetafxMt5VisibleNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundPid) }
        $attachedForeground = $false
        $attachedTarget = $false
        try {
            if ($foregroundThread -gt 0 -and $foregroundThread -ne $currentThread -and $foregroundThread -ne $targetThread) {
                $attachedForeground = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $true)
            }
            if ($targetThread -gt 0 -and $targetThread -ne $currentThread) {
                $attachedTarget = [MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $targetThread, $true)
            }
            [void][MetafxMt5VisibleNative]::BringWindowToTop($handle)
            [void][MetafxMt5VisibleNative]::SetForegroundWindow($handle)
            [void][MetafxMt5VisibleNative]::SetActiveWindow($handle)
            [void][MetafxMt5VisibleNative]::SetFocus($handle)
        } finally {
            if ($attachedTarget) { [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $targetThread, $false) }
            if ($attachedForeground) { [void][MetafxMt5VisibleNative]::AttachThreadInput($currentThread, $foregroundThread, $false) }
        }
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ([MetafxMt5VisibleNative]::GetForegroundWindow() -eq $handle) { Start-Sleep -Milliseconds 150; return }
        try { if ($null -ne $Window) { $Window.SetFocus() } else { (Get-Root $Process).SetFocus() } } catch {}
        [void][MetafxMt5VisibleNative]::SetForegroundWindow($handle)
        Start-Sleep -Milliseconds 100
    }
    Fail "visible_window_foreground_failed"
}

function Capture-Window(
    [System.Diagnostics.Process]$Process,
    [string]$Path,
    [System.Windows.Automation.AutomationElement]$Window,
    [IntPtr]$ExpectedHandle = [IntPtr]::Zero
) {
    if ($null -eq $Window) { Fail "visible_screenshot_window_binding_missing" }
    [IntPtr]$handle = [IntPtr]$Window.Current.NativeWindowHandle
    if ($ExpectedHandle -ne [IntPtr]::Zero -and $handle -ne $ExpectedHandle) { Fail "visible_screenshot_window_binding_mismatch" }
    Set-Foreground $Process $Window
    $rect = [MetafxMt5VisibleNative+RECT]::new()
    if ($handle -eq [IntPtr]::Zero -or
        -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
        -not [MetafxMt5VisibleNative]::IsWindowVisible($handle) -or
        -not [MetafxMt5VisibleNative]::IsWindowEnabled($handle) -or
        (Get-NativeOwner $handle) -ne $Process.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $handle -or
        -not [MetafxMt5VisibleNative]::GetWindowRect($handle, [ref]$rect)) { Fail "visible_screenshot_bounds_failed" }
    $width = $rect.Right - $rect.Left; $height = $rect.Bottom - $rect.Top
    if ($width -lt 320 -or $height -lt 240 -or $width -gt 32768 -or $height -gt 32768) { Fail "visible_screenshot_bounds_invalid" }
    $bitmap = [System.Drawing.Bitmap]::new($width, $height)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try { $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size) } finally { $graphics.Dispose() }
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally { $bitmap.Dispose() }
    if (-not [System.IO.File]::Exists($Path) -or ([System.IO.FileInfo]$Path).Length -lt 1024) { Fail "visible_screenshot_invalid" }
    $postRect = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::IsWindow($handle) -or
        (Get-NativeOwner $handle) -ne $Process.Id -or
        -not [MetafxMt5VisibleNative]::GetWindowRect($handle, [ref]$postRect) -or
        $postRect.Left -ne $rect.Left -or $postRect.Top -ne $rect.Top -or
        $postRect.Right -ne $rect.Right -or $postRect.Bottom -ne $rect.Bottom) {
        Fail "visible_screenshot_bounds_invalid"
    }
    $savedImage = $null
    try {
        $savedImage = [System.Drawing.Image]::FromFile($Path)
        $pngGuid = [string]([System.Drawing.Imaging.ImageFormat]::Png.Guid)
        if ($savedImage.Width -ne $width -or $savedImage.Height -ne $height -or
            [string]$savedImage.RawFormat.Guid -cne $pngGuid) {
            Fail "visible_screenshot_dimensions_mismatch"
        }
    } catch {
        if ([string]$_.Exception.Message -ceq "visible_screenshot_dimensions_mismatch") { throw }
        Fail "visible_screenshot_invalid"
    } finally {
        if ($null -ne $savedImage) { $savedImage.Dispose() }
    }
}

function Capture-BoundTerminalWindow([object]$Request, [string]$Path) {
    $captureRoot = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    Capture-Window $TerminalProcess $Path $captureRoot ([IntPtr]$script:TerminalRootHandle)
}

function Get-AlgoTradingState([System.Windows.Automation.AutomationElement]$Root) {
    # MT5 exposes its Standard toolbar as one native ToolbarWindow32 rather
    # than individual UIA buttons. Command 32851 is the product's exact
    # "Algo Trading" button (verified by TB_GETBUTTONTEXTW during adapter
    # qualification); TB_GETSTATE bit 0 is its pressed/check state.
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, "488")
    $candidates = @(Get-All $Root $condition | Where-Object {
        [string]$_.Current.ClassName -ceq "ToolbarWindow32" -and -not $_.Current.IsOffscreen
    })
    if ($candidates.Count -ne 1) { Fail "mt5_algo_trading_state_unverified" }
    [IntPtr]$toolbar = Assert-NativeControl $candidates[0] "ToolbarWindow32" "mt5_algo_trading_state_unverified"
    $state = (Invoke-NativeMessage $toolbar ([MetafxMt5VisibleNative]::TB_GETSTATE) 32851 0 "mt5_algo_trading_state_unverified").ToInt64()
    if ($state -lt 0 -or $state -eq 4294967295) { Fail "mt5_algo_trading_state_unverified" }
    return (($state -band 1) -eq 1)
}

function New-Probe([System.Diagnostics.Process]$Process, [System.Windows.Automation.AutomationElement]$Root) {
    # The initial probe and its response must name the same proven MT5 main
    # root. Process.MainWindowHandle/Title can drift to a docked or owned pane.
    return New-BoundProbe $Process $Root
}

function New-BoundProbe(
    [System.Diagnostics.Process]$Process,
    [System.Windows.Automation.AutomationElement]$Root
) {
    [IntPtr]$rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
    if ($Root.Current.ProcessId -ne $Process.Id -or
        $rootHandle -eq [IntPtr]::Zero -or
        $rootHandle -ne $script:TerminalRootHandle -or
        -not [MetafxMt5VisibleNative]::IsWindow($rootHandle) -or
        (Get-NativeOwner $rootHandle) -ne $Process.Id) {
        Fail "mt5_terminal_process_changed"
    }
    return [ordered]@{
        observedAt = [DateTime]::UtcNow.ToString("o")
        processId = $Process.Id
        executablePath = [System.IO.Path]::GetFullPath($Process.Path)
        windowHandle = $rootHandle.ToInt64()
        windowOwnerProcessId = $Process.Id
        windowTitle = [string]$Root.Current.Name
        windowClass = [string]$Root.Current.ClassName
    }
}

function New-Binding([System.Diagnostics.Process]$Front, [string]$Kind, [bool]$AutoState, [System.Windows.Automation.AutomationElement]$FrontWindow = $null) {
    $frontRoot = if ($null -ne $FrontWindow) { $FrontWindow } else { Get-Root $Front }
    [IntPtr]$frontHandle = [IntPtr]$frontRoot.Current.NativeWindowHandle
    return [ordered]@{
        observedAt = [DateTime]::UtcNow.ToString("o")
        terminalProcessId = $TerminalProcess.Id
        terminalExecutablePath = [System.IO.Path]::GetFullPath($TerminalProcess.Path)
        terminalWindowHandle = $script:TerminalRootHandle.ToInt64()
        terminalWindowOwnerProcessId = $TerminalProcess.Id
        terminalWindowTitle = [string]$TerminalRoot.Current.Name
        terminalWindowClass = $TerminalRoot.Current.ClassName
        frontOfficeKind = $Kind
        frontOfficeProcessId = $Front.Id
        frontOfficeExecutablePath = [System.IO.Path]::GetFullPath($Front.Path)
        frontOfficeWindowHandle = $frontHandle.ToInt64()
        frontOfficeWindowOwnerProcessId = $Front.Id
        frontOfficeWindowTitle = [string]$frontRoot.Current.Name
        frontOfficeWindowClass = $frontRoot.Current.ClassName
        autoTradingState = $AutoState
    }
}

function Assert-RequiredControls([object]$Request) {
    $Required = $Request.requiredAutomationIds
    $normalized = Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $true "mt5_tester_settings_tab_not_verified"
    $Root = $normalized.root
    $verified = [ordered]@{}
    foreach ($property in $Required.PSObject.Properties) {
        # Date, criterion and optimization-dependent controls may legitimately be
        # disabled before the selected policy is applied.  Capability proves one
        # exact visible AutomationId; the action later proves it becomes usable.
        $controlCode = "mt5_tester_control_$(([string]$property.Name).ToLowerInvariant())_not_verified"
        if ([string]$property.Name -ceq "tabs") {
            [void](Get-TesterResultTabs $Root $Required $controlCode)
        } else {
            [void](Get-ControlByIdPresent $Root ([string]$property.Value) $controlCode)
        }
        $verified[$property.Name] = [string]$property.Value
    }
    return $verified
}

function Write-StartBoundary([object]$Request) {
    $path = [System.IO.Path]::GetFullPath([string]$Request.startBoundaryPath)
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes([string]$Request.startBoundaryJson)
    $actual = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
    if ($actual -cne [string]$Request.startBoundarySha256) { Fail "tester_start_boundary_digest_invalid" }
    try {
        $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    } catch { Fail "tester_start_boundary_exists" }
}

function Assert-StartBoundary([object]$Request) {
    $path = [System.IO.Path]::GetFullPath([string]$Request.startBoundaryPath)
    $evidence = Get-StableCheckpointFile $path ".json" 1 32768 "tester_start_boundary_mismatch"
    if ([string]$evidence.sha256 -cne [string]$Request.startBoundarySha256) { Fail "tester_start_boundary_mismatch" }
    return [string]$evidence.sha256
}

function Get-ExpertCatalogRefreshBoundaryPath([object]$Request) {
    return [System.IO.Path]::GetFullPath([string]$Request.expertCatalogRefreshBoundaryPath)
}

function Assert-ExpertCatalogRefreshBoundary([object]$Request) {
    $path = Get-ExpertCatalogRefreshBoundaryPath $Request
    if (-not [System.IO.File]::Exists($path)) { Fail "mt5_expert_catalog_refresh_boundary_missing" }
    try { $bytes = [System.IO.File]::ReadAllBytes($path) }
    catch { Fail "mt5_expert_catalog_refresh_boundary_invalid" }
    $actual = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
    if ($actual -cne [string]$Request.expertCatalogRefreshBoundarySha256) { Fail "mt5_expert_catalog_refresh_boundary_invalid" }
    return $actual
}

function Write-ExpertCatalogRefreshBoundary([object]$Request) {
    $path = Get-ExpertCatalogRefreshBoundaryPath $Request
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes([string]$Request.expertCatalogRefreshBoundaryJson)
    $actual = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
    if ($actual -cne [string]$Request.expertCatalogRefreshBoundarySha256) { Fail "mt5_expert_catalog_refresh_boundary_invalid" }
    try {
        $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    } catch { Fail "mt5_expert_catalog_refresh_boundary_exists" }
    return $actual
}

function Get-DispatchConfirmationPath([object]$Request) {
    return ([System.IO.Path]::GetFullPath([string]$Request.startBoundaryPath) + ".dispatch-confirmed")
}

function Write-DispatchConfirmation([object]$Request) {
    $path = Get-DispatchConfirmationPath $Request
    $payload = [ordered]@{
        schemaVersion = "ea-factory-mt5-start-dispatch-v1"
        operationId = [string]$Request.operationId
        actionRequestDigest = [string]$Request.actionRequestDigest
        startBoundarySha256 = [string]$Request.startBoundarySha256
        confirmedAt = [DateTime]::UtcNow.ToString("o")
    }
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes(($payload | ConvertTo-Json -Depth 8 -Compress))
    try {
        $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    } catch { Fail "tester_start_dispatch_confirmation_failed" }
}

function Assert-DispatchConfirmation([object]$Request) {
    $path = Get-DispatchConfirmationPath $Request
    $evidence = Get-StableCheckpointFile $path ".dispatch-confirmed" 1 32768 "tester_start_dispatch_unconfirmed"
    try {
        $text = [System.Text.UTF8Encoding]::new($false, $true).GetString([byte[]]$evidence.bytes)
        $payload = $text | ConvertFrom-Json
    }
    catch { Fail "tester_start_dispatch_unconfirmed" }
    $expectedFields = @("schemaVersion", "operationId", "actionRequestDigest", "startBoundarySha256", "confirmedAt")
    if (@($payload.PSObject.Properties.Name).Count -ne $expectedFields.Count -or
        @($expectedFields | Where-Object { $_ -cnotin @($payload.PSObject.Properties.Name) }).Count -gt 0 -or
        [string]$payload.schemaVersion -cne "ea-factory-mt5-start-dispatch-v1" -or
        [string]$payload.operationId -cne [string]$Request.operationId -or
        [string]$payload.actionRequestDigest -cne [string]$Request.actionRequestDigest -or
        [string]$payload.startBoundarySha256 -cne [string]$Request.startBoundarySha256 -or
        [string]::IsNullOrWhiteSpace([string]$payload.confirmedAt)) { Fail "tester_start_dispatch_unconfirmed" }
    try { [void][DateTimeOffset]::ParseExact([string]$payload.confirmedAt, "o", [System.Globalization.CultureInfo]::InvariantCulture) }
    catch { Fail "tester_start_dispatch_unconfirmed" }
    return [string]$evidence.sha256
}

function Wait-ExactOwnedFileDialog([string[]]$ExpectedNames, [string]$Code) {
    # Bind the native shell dialog directly.  Windows 11 may delay or omit its
    # UIA provider for many seconds even though the exact owned #32770 dialog
    # and its native controls are already ready.
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    while ([DateTime]::UtcNow -lt $deadline) {
        try {
            [IntPtr]$dialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact(
                [uint32]$TerminalProcess.Id,
                [IntPtr]$script:TerminalRootHandle,
                [string[]]$ExpectedNames
            )
        } catch { Fail $Code }
        if ($dialog -ne [IntPtr]::Zero) { return $dialog }
        Start-Sleep -Milliseconds 100
    }
    Fail $Code
}

function Get-ExactOwnedDialogControl(
    [IntPtr]$Dialog,
    [int]$ControlId,
    [string]$ExpectedClass,
    [string[]]$ExpectedNames,
    [string]$Code
) {
    if ($Dialog -eq [IntPtr]::Zero -or
        [MetafxMt5VisibleNative]::GetWindow($Dialog, [MetafxMt5VisibleNative]::GW_OWNER) -ne $script:TerminalRootHandle) { Fail $Code }
    try {
        [IntPtr]$handle = [MetafxMt5VisibleNative]::FindDialogControlExact(
            $Dialog, [uint32]$TerminalProcess.Id, $ControlId, $ExpectedClass
        )
        $nativeName = [MetafxMt5VisibleNative]::GetWindowTextExact($handle).Replace("&", "")
    } catch { Fail $Code }
    if ($ExpectedNames.Count -gt 0 -and
        @($ExpectedNames | Where-Object { $nativeName -ceq [string]$_ }).Count -ne 1) { Fail $Code }
    return $handle
}

function Enter-ExactFileDialogPath(
    [IntPtr]$Dialog,
    [string]$Path,
    [string[]]$CommitNames,
    [string]$Code
) {
    if (-not [System.IO.Path]::IsPathRooted($Path) -or [string]::IsNullOrWhiteSpace($Path)) { Fail "$($Code)_path_invalid" }
    [IntPtr]$dialogHandle = $Dialog
    $isOpen = @($CommitNames | Where-Object { [string]$_ -ceq "Open" }).Count -eq 1
    $isSave = @($CommitNames | Where-Object { [string]$_ -ceq "Save" }).Count -eq 1
    if ($isOpen -eq $isSave) { Fail "$($Code)_commit_contract_invalid" }
    $fileNameControlId = if ($isOpen) { 1148 } else { 1001 }
    [IntPtr]$editHandle = Get-ExactOwnedDialogControl $Dialog $fileNameControlId "Edit" @() "$($Code)_filename_edit_not_verified"
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxMt5VisibleNative]::SendMessageTimeout(
        $editHandle, [MetafxMt5VisibleNative]::WM_SETTEXT, [IntPtr]::Zero, $Path,
        ([MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG -bor [MetafxMt5VisibleNative]::SMTO_BLOCK -bor [MetafxMt5VisibleNative]::SMTO_ERRORONEXIT),
        1500, [ref]$result
    )
    if ($call -eq [IntPtr]::Zero -or $result.ToInt32() -ne 1 -or (Read-NativeText $editHandle "$($Code)_filename_readback_failed") -cne $Path) { Fail "$($Code)_filename_write_failed" }
    [IntPtr]$commitHandle = Get-ExactOwnedDialogControl $Dialog 1 "Button" $CommitNames "$($Code)_commit_button_not_verified"
    [void](Invoke-NativeMessage $commitHandle ([MetafxMt5VisibleNative]::BM_CLICK) 0 0 "$($Code)_commit_click_failed")
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    while ([MetafxMt5VisibleNative]::IsWindow($dialogHandle) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 50 }
    if ([MetafxMt5VisibleNative]::IsWindow($dialogHandle)) { Fail "$($Code)_dialog_commit_timeout" }
}

function Close-ExactOwnedFileDialogAfterFailure([IntPtr]$Dialog, [string]$Code) {
    [IntPtr]$dialogHandle = $Dialog
    if ($dialogHandle -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($dialogHandle)) { return }
    [IntPtr]$cancelHandle = Get-ExactOwnedDialogControl $Dialog 2 "Button" @("Cancel") $Code
    [void](Invoke-NativeMessage $cancelHandle ([MetafxMt5VisibleNative]::BM_CLICK) 0 0 $Code)
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    while ([MetafxMt5VisibleNative]::IsWindow($dialogHandle) -and [DateTime]::UtcNow -lt $deadline) { Start-Sleep -Milliseconds 50 }
    if ([MetafxMt5VisibleNative]::IsWindow($dialogHandle)) { Fail $Code }
}

function Find-MetaEditorSourceBinding([string]$CompilerPath, [string]$SourcePath) {
    $leaf = [System.IO.Path]::GetFileName($SourcePath)
    $bindings = @()
    foreach ($process in @(Get-Process -Name "MetaEditor64" -ErrorAction SilentlyContinue)) {
        try { if ([System.IO.Path]::GetFullPath($process.Path) -ine $CompilerPath) { continue } } catch { continue }
        $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $process.Id)
        foreach ($window in @([System.Windows.Automation.AutomationElement]::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children, $condition))) {
            [IntPtr]$handle = [IntPtr]$window.Current.NativeWindowHandle
            if ([string]$window.Current.ClassName -ceq "MetaQuotes::MetaEditor::5.00" -and
                $handle -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::IsWindowVisible($handle) -and
                (Get-NativeOwner $handle) -eq $process.Id -and
                ([string]$window.Current.Name).IndexOf($leaf, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                $bindings += [pscustomobject]@{ Process = $process; Window = $window }
            }
        }
    }
    if ($bindings.Count -gt 1) { Fail "mt5_metaeditor_source_window_ambiguous" }
    if ($bindings.Count -eq 1) { return $bindings[0] }
    return $null
}

function Assert-MetaEditorSourceBindingUnchanged(
    [object]$OriginalBinding,
    [string]$CompilerPath,
    [string]$SourcePath
) {
    # Verification after F7 is deliberately read-only.  Never reopen or start
    # MetaEditor here: the trusted compiler row and fresh EX5 must still belong
    # to the exact source window that received the compile key.
    if ($null -eq $OriginalBinding -or
        $null -eq $OriginalBinding.Process -or
        $null -eq $OriginalBinding.Window) { Fail "mt5_metaeditor_source_window_changed" }
    $current = Find-MetaEditorSourceBinding $CompilerPath $SourcePath
    if ($null -eq $current -or $null -eq $current.Process -or $null -eq $current.Window) {
        Fail "mt5_metaeditor_source_window_changed"
    }
    [IntPtr]$originalHandle = [IntPtr]$OriginalBinding.Window.Current.NativeWindowHandle
    [IntPtr]$currentHandle = [IntPtr]$current.Window.Current.NativeWindowHandle
    if ($current.Process.Id -ne $OriginalBinding.Process.Id -or
        $originalHandle -eq [IntPtr]::Zero -or
        $currentHandle -eq [IntPtr]::Zero -or
        $currentHandle -ne $originalHandle) { Fail "mt5_metaeditor_source_window_changed" }
    return $current
}

function Get-Or-StartMetaEditor([string]$CompilerPath, [string]$SourcePath) {
    $binding = Find-MetaEditorSourceBinding $CompilerPath $SourcePath
    if ($null -eq $binding) { [void](Start-Process -FilePath $CompilerPath -ArgumentList @("`"$SourcePath`"") -PassThru) }
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    while ([DateTime]::UtcNow -lt $deadline) {
        $binding = Find-MetaEditorSourceBinding $CompilerPath $SourcePath
        if ($null -ne $binding) { Set-Foreground $binding.Process $binding.Window; return $binding }
        Start-Sleep -Milliseconds 100
    }
    Fail "mt5_metaeditor_source_window_not_ready"
}

function Get-TrustedCompileSuccessRow([string]$CopiedRow) {
    # This parser is deliberately pure so the exact native owner-data TSV
    # contract can be regression-tested without touching MetaEditor.  Compiler
    # diagnostic rows legitimately contain File/Line/Column values and are not
    # successes; they remain valid *freshness snapshots* before F7, but can
    # never be promoted to successful compile evidence.
    $rawCopied = ([string]$CopiedRow).TrimEnd([char[]]@("`r", "`n"))
    $fields = @($rawCopied.Split([char]"`t"))
    if ($fields.Count -ne 4 -or
        -not [string]::IsNullOrWhiteSpace([string]$fields[1]) -or
        -not [string]::IsNullOrWhiteSpace([string]$fields[2]) -or
        ([string]$fields[3]).Trim() -cne "0") { return $null }
    $description = ([string]$fields[0]).Trim()
    $match = [regex]::Match($description, "^\s*(0\s+errors?,\s*0\s+warnings?(?:,\s*[0-9]+\s+ms\s+elapsed,\s*cpu='[^'\r\n]{1,80}')?)\s*$", "IgnoreCase")
    if (-not $match.Success) { return $null }
    return [pscustomobject]@{
        Description = $description
        ResultLine = $match.Groups[1].Value.Trim()
    }
}

function Set-CompileDiagnosticCheckpoint([hashtable]$State, [string]$Checkpoint) {
    if ($null -eq $State) { return }
    if (-not $State.ContainsKey("clock")) {
        $State["clock"] = [System.Diagnostics.Stopwatch]::StartNew()
        $State["timings"] = [ordered]@{}
        $State["checkpointAtMs"] = [long]0
    }
    [long]$elapsed = $State["clock"].ElapsedMilliseconds
    if ($State.ContainsKey("checkpoint")) {
        $State["timings"][[string]$State["checkpoint"]] = [Math]::Max(0, $elapsed - [long]$State["checkpointAtMs"])
    }
    $State["checkpoint"] = $Checkpoint
    $State["checkpointAtMs"] = $elapsed
}

function Find-CompileResult([System.Windows.Automation.AutomationElement]$Root, [System.Diagnostics.Process]$Editor, [bool]$RequireSuccess, [hashtable]$DiagnosticState = $null) {
    # MetaEditor exposes the current compiler rows through one owner-data native
    # list.  Generic UIA Text nodes are cached/stale on several builds and are
    # deliberately never accepted as compile evidence.
    [MetafxMetaEditorCompileNative]::ResetCaptureTimestamp()
    Set-CompileDiagnosticCheckpoint $DiagnosticState "root_binding"
    [IntPtr]$rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
    if ($null -ne $DiagnosticState) {
        $DiagnosticState["nativeRootClass"] = Get-NativeClass $rootHandle
    }
    if ($rootHandle -eq [IntPtr]::Zero -or
        (Get-NativeOwner $rootHandle) -ne $Editor.Id -or
        (Get-NativeClass $rootHandle) -cne "MetaQuotes::MetaEditor::5.00") { Fail "mt5_metaeditor_compile_result_unverified" }
    # Bind the exact Toolbox tab strip before looking for the Errors list.
    # MetaEditor removes the inactive owner-data list from the visible UIA tree;
    # therefore searching for control 10065 before selecting Errors can never
    # succeed when another Toolbox tab was selected at startup.
    $tabsCondition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, "10047")
    $toolboxTabs = @()
    Set-CompileDiagnosticCheckpoint $DiagnosticState "uia_tabs_find_all"
    $tabCandidates = @(Get-All $Root $tabsCondition)
    Set-CompileDiagnosticCheckpoint $DiagnosticState "uia_tabs_properties_and_toolbox_binding"
    foreach ($candidate in @($tabCandidates | Where-Object {
        -not $_.Current.IsOffscreen -and $_.Current.IsEnabled -and [string]$_.Current.ClassName -ceq "SysTabControl32"
    })) {
        [IntPtr]$candidateHandle = [IntPtr]$candidate.Current.NativeWindowHandle
        [IntPtr]$candidateParent = if ($candidateHandle -ne [IntPtr]::Zero) {
            [MetafxMt5VisibleNative]::GetParent($candidateHandle)
        } else { [IntPtr]::Zero }
        if ($candidateParent -ne [IntPtr]::Zero -and
            [MetafxMt5VisibleNative]::GetDlgCtrlID($candidateParent) -eq 32907 -and
            (Get-NativeOwner $candidateHandle) -eq $Editor.Id -and
            (Get-NativeOwner $candidateParent) -eq $Editor.Id -and
            [MetafxMt5VisibleNative]::GetAncestor($candidateHandle, [MetafxMt5VisibleNative]::GA_ROOT) -eq $rootHandle -and
            [MetafxMt5VisibleNative]::GetAncestor($candidateParent, [MetafxMt5VisibleNative]::GA_ROOT) -eq $rootHandle -and
            (Read-NativeText $candidateParent "mt5_metaeditor_compile_result_unverified") -ceq "Toolbox") {
            $toolboxTabs += [pscustomobject]@{
                Tab = $candidate
                TabHandle = $candidateHandle
                ToolboxHandle = $candidateParent
            }
        }
    }
    if ($toolboxTabs.Count -ne 1) { Fail "mt5_metaeditor_compile_result_unverified" }
    [IntPtr]$tabsHandle = [IntPtr]$toolboxTabs[0].TabHandle
    [IntPtr]$toolboxHandle = [IntPtr]$toolboxTabs[0].ToolboxHandle
    try {
        Set-CompileDiagnosticCheckpoint $DiagnosticState "errors_tab_binding"
        $tabNames = @([MetafxMt5TabNative]::GetNames($tabsHandle))
        $errorIndexes = @()
        for ($index = 0; $index -lt $tabNames.Count; $index++) {
            if ([string]$tabNames[$index] -ceq "Errors") { $errorIndexes += $index }
        }
        if ($errorIndexes.Count -ne 1) { Fail "mt5_metaeditor_compile_result_unverified" }
        if ([MetafxMt5TabNative]::GetSelectedIndex($tabsHandle) -ne [int]$errorIndexes[0]) {
            if ($null -ne $DiagnosticState) { Fail "compile_diagnostic_errors_tab_not_selected" }
            if (-not [MetafxMt5TabNative]::SelectExact($tabsHandle, "Errors") -or
                [MetafxMt5TabNative]::GetSelectedIndex($tabsHandle) -ne [int]$errorIndexes[0]) { Fail "mt5_metaeditor_compile_result_unverified" }
        }
        # Selection changes the active child list.  Only after Errors is the
        # selected tab may control 10065 be accepted, and it must be the sole
        # visible/enabled SysListView32 directly owned by this exact Toolbox.
        $listCondition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, "10065")
        Set-CompileDiagnosticCheckpoint $DiagnosticState "uia_list_find_all"
        $listCandidates = @(Get-All $Root $listCondition)
        Set-CompileDiagnosticCheckpoint $DiagnosticState "uia_list_properties_and_binding"
        $lists = @($listCandidates | Where-Object {
            -not $_.Current.IsOffscreen -and $_.Current.IsEnabled -and
            [string]$_.Current.ClassName -ceq "SysListView32" -and
            [MetafxMt5VisibleNative]::GetParent([IntPtr]$_.Current.NativeWindowHandle) -eq $toolboxHandle
        })
        if ($lists.Count -ne 1) { Fail "mt5_metaeditor_compile_result_unverified" }
        [IntPtr]$listHandle = [IntPtr]$lists[0].Current.NativeWindowHandle
        if ($listHandle -eq [IntPtr]::Zero -or
            (Get-NativeOwner $listHandle) -ne $Editor.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($listHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle -or
            [MetafxMt5VisibleNative]::GetParent($listHandle) -ne $toolboxHandle) { Fail "mt5_metaeditor_compile_result_unverified" }
        Set-CompileDiagnosticCheckpoint $DiagnosticState "native_row_count"
        $rowCount = [MetafxMetaEditorCompileNative]::GetItemCount($listHandle)
        Set-CompileDiagnosticCheckpoint $DiagnosticState "native_row_copy"
        $copied = if ($rowCount -gt 0) {
            if ($null -ne $DiagnosticState) {
                $DiagnosticState["nativeCopyTimings"] = [System.Collections.Generic.Dictionary[string,long]]::new()
                [MetafxMetaEditorCompileNative]::CopyDiagnosticRowTimed($rootHandle, $listHandle, $DiagnosticState["nativeCopyTimings"])
            }
            else { [MetafxMetaEditorCompileNative]::CopyLastVisibleRow($rootHandle, $listHandle) }
        } else { "" }
        # Consume exactly once, only after CopyLastVisibleRow's complete cleanup
        # succeeded. For an empty list this is the native count observation.
        [long]$captureTicks = [MetafxMetaEditorCompileNative]::ConsumeCaptureTimestamp()
        if ($captureTicks -le 0) { Fail "mt5_metaeditor_compile_capture_unverified" }
    } catch {
        $underlyingCode = Get-CompileDiagnosticErrorCode $_
        if ($null -ne $DiagnosticState) {
            $DiagnosticState["underlyingErrorCode"] = $underlyingCode
        }
        # Never retry an observation after incomplete restoration of user state.
        if ($underlyingCode -match '(clipboard_restore|foreground_restore|focus_restore)' -or
            $underlyingCode -ceq "mt5_metaeditor_compile_capture_unverified") { Fail $underlyingCode }
        Fail "mt5_metaeditor_compile_result_unverified"
    }
    # Copy from MetaEditor's owner-data Errors list is native TSV, not only
    # the visible Description cell.  A successful summary row on current MT5
    # builds is copied as:
    #   <description>\t<empty File>\t<empty Line>\t0<Column>\r\n
    # Bind the complete native row for freshness.  Only a post-F7 call with
    # RequireSuccess=true requires and accepts the exact success-summary shape;
    # a pre-F7 diagnostic row is allowed solely as the before-snapshot.
    $rawCopied = ([string]$copied).TrimEnd([char[]]@("`r", "`n"))
    Set-CompileDiagnosticCheckpoint $DiagnosticState "native_row_shape"
    $trustedSuccess = Get-TrustedCompileSuccessRow $rawCopied
    if ($RequireSuccess -and $null -eq $trustedSuccess) { Fail "mt5_metaeditor_compile_result_unverified" }
    $snapshotBytes = [System.Text.UTF8Encoding]::new($false).GetBytes("$rowCount`n$rawCopied")
    $snapshotDigest = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($snapshotBytes)).Replace("-", "").ToLowerInvariant()
    Set-CompileDiagnosticCheckpoint $DiagnosticState "complete"
    return [ordered]@{
        rowCount = [int]$rowCount
        captureTimestampTicks = $captureTicks
        rawLastRow = $rawCopied
        snapshotSha256 = $snapshotDigest
        resultLine = if ($null -ne $trustedSuccess) { [string]$trustedSuccess.ResultLine } else { $null }
    }
}

function Get-CompileDiagnosticErrorCode([object]$ErrorRecord) {
    $exception = $ErrorRecord.Exception
    while ($null -ne $exception.InnerException) { $exception = $exception.InnerException }
    $code = [string]$exception.Message
    if ($code -cmatch '^[a-z0-9_]{3,100}$') { return $code }
    return "compile_diagnostic_observation_failed"
}

function Read-CompileDiagnostic([object]$Request) {
    # Diagnostic-only observation of an already-open, exact source window.
    # Never start/open MetaEditor, select tabs, press F7, touch artifacts or mint
    # compile evidence. Native copying restores clipboard/selection/focus, and
    # CopyDiagnosticRow also restores the original foreground window on failure.
    if ([string]$Request.stageId -cne "compile_validate") { Fail "visible_stage_unsupported" }
    $source = Get-FullExistingFile $Request.sourcePath ".mq5" "mt5_source_invalid"
    if ((Get-Sha256 $source) -cne [string]$Request.expectedSourceDigest) { Fail "mt5_source_digest_mismatch" }
    $binding = Find-MetaEditorSourceBinding ([string]$Request.compilerPath) $source
    if ($null -eq $binding) { Fail "mt5_metaeditor_source_window_not_ready" }
    $editor = $binding.Process
    $root = $binding.Window
    [IntPtr]$rootHandle = [IntPtr]$root.Current.NativeWindowHandle
    $observation = [ordered]@{
        tabs = @(); lists = @(); qualifiedTabCount = 0; selectedTab = $null
        nativeTabNames = @(); qualifiedListCount = 0; rowCount = $null
        rawLastRow = $null; rawRowTruncated = $false; rawRowFieldCount = $null
        rawRowSha256 = $null; nativeSuccessShape = $false; reasonCode = $null
        nativeRootClass = Get-NativeClass $rootHandle; productionReader = $null
    }
    try {
        $qualifiedTabs = @()
        $qualifiedLists = @()
        foreach ($id in @("10047", "10065")) {
            $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $id)
            $items = @(Get-All $root $condition)
            if ($items.Count -gt 16) { Fail "compile_diagnostic_control_count_exceeded" }
            foreach ($item in $items) {
                [IntPtr]$handle = [IntPtr]$item.Current.NativeWindowHandle
                [IntPtr]$parent = if ($handle -ne [IntPtr]::Zero) { [MetafxMt5VisibleNative]::GetParent($handle) } else { [IntPtr]::Zero }
                $owned = $handle -ne [IntPtr]::Zero -and (Get-NativeOwner $handle) -eq $editor.Id
                $rootBound = $handle -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -eq $rootHandle
                $parentId = if ($parent -ne [IntPtr]::Zero) { [MetafxMt5VisibleNative]::GetDlgCtrlID($parent) } else { 0 }
                $row = [ordered]@{
                    automationId = $id; className = ([string]$item.Current.ClassName).Substring(0, [Math]::Min(80, ([string]$item.Current.ClassName).Length))
                    offscreen = [bool]$item.Current.IsOffscreen; enabled = [bool]$item.Current.IsEnabled
                    ownedByEditor = [bool]$owned; rootBound = [bool]$rootBound; parentControlId = [int]$parentId
                    parentRootBound = [bool]($parent -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::GetAncestor($parent, [MetafxMt5VisibleNative]::GA_ROOT) -eq $rootHandle)
                }
                if ($id -ceq "10047") {
                    $observation.tabs += $row
                    if ($owned -and $rootBound -and -not $row.offscreen -and $row.enabled -and
                        $row.className -ceq "SysTabControl32" -and $parentId -eq 32907 -and
                        (Get-NativeOwner $parent) -eq $editor.Id -and
                        (Read-NativeText $parent "compile_diagnostic_toolbox_unverified") -ceq "Toolbox") {
                        $qualifiedTabs += [pscustomobject]@{ Handle = $handle; Parent = $parent }
                    }
                } else {
                    $observation.lists += $row
                    if ($owned -and $rootBound -and -not $row.offscreen -and $row.enabled -and $row.className -ceq "SysListView32") {
                        $qualifiedLists += [pscustomobject]@{ Handle = $handle; Parent = $parent }
                    }
                }
            }
        }
        $observation.qualifiedTabCount = $qualifiedTabs.Count
        if ($qualifiedTabs.Count -ne 1) { Fail "compile_diagnostic_toolbox_not_unique" }
        $tabNames = @([MetafxMt5TabNative]::GetNames($qualifiedTabs[0].Handle))
        if ($tabNames.Count -gt 32 -or @($tabNames | Where-Object { ([string]$_).Length -gt 80 }).Count -gt 0) { Fail "compile_diagnostic_tabs_unbounded" }
        $observation.nativeTabNames = $tabNames
        $selectedIndex = [MetafxMt5TabNative]::GetSelectedIndex($qualifiedTabs[0].Handle)
        if ($selectedIndex -lt 0 -or $selectedIndex -ge $tabNames.Count) { Fail "compile_diagnostic_selected_tab_invalid" }
        $observation.selectedTab = [string]$tabNames[$selectedIndex]
        if ($observation.selectedTab -cne "Errors") { Fail "compile_diagnostic_errors_tab_not_selected" }
        $boundLists = @($qualifiedLists | Where-Object { $_.Parent -eq $qualifiedTabs[0].Parent })
        $observation.qualifiedListCount = $boundLists.Count
        if ($boundLists.Count -ne 1) { Fail "compile_diagnostic_errors_list_not_unique" }
        $count = [MetafxMetaEditorCompileNative]::GetItemCount($boundLists[0].Handle)
        $observation.rowCount = $count
        $copied = if ($count -gt 0) { [MetafxMetaEditorCompileNative]::CopyDiagnosticRow($rootHandle, $boundLists[0].Handle) } else { "" }
        $raw = ([string]$copied).TrimEnd([char[]]@("`r", "`n"))
        $observation.rawLastRow = $raw.Substring(0, [Math]::Min(1024, $raw.Length))
        $observation.rawRowTruncated = $raw.Length -gt 1024
        $observation.rawRowFieldCount = @($raw.Split([char]"`t")).Count
        $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($raw)
        $observation.rawRowSha256 = [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
        $observation.nativeSuccessShape = $null -ne (Get-TrustedCompileSuccessRow $raw)
        $readerState = @{}
        $readerStarted = [DateTime]::UtcNow
        $readerStartedTicks = [System.Diagnostics.Stopwatch]::GetTimestamp()
        $readerResult = $null
        $readerError = $null
        try { $readerResult = Find-CompileResult $root $editor $true $readerState }
        catch {
            $readerError = Get-CompileDiagnosticErrorCode $_
            if ($readerError -match '(clipboard_restore|foreground_restore|focus_restore)') { Fail $readerError }
        }
        Set-CompileDiagnosticCheckpoint $readerState ([string]$readerState["checkpoint"])
        $observation.productionReader = [ordered]@{
            accepted = $null -ne $readerResult; reasonCode = $readerError
            elapsedMs = [int]([DateTime]::UtcNow - $readerStarted).TotalMilliseconds
            checkpoint = $readerState["checkpoint"]; underlyingErrorCode = $readerState["underlyingErrorCode"]
            rowCount = if ($null -ne $readerResult) { $readerResult.rowCount } else { $null }
            snapshotSha256 = if ($null -ne $readerResult) { $readerResult.snapshotSha256 } else { $null }
            timingsMs = $readerState["timings"]; nativeCopyTimingsMs = $readerState["nativeCopyTimings"]
            captureAfterStartMs = if ($null -ne $readerResult) {
                [Math]::Round(1000.0 * ([long]$readerResult.captureTimestampTicks - $readerStartedTicks) / [System.Diagnostics.Stopwatch]::Frequency, 3)
            } else { $null }
            restorationCompleted = $null -ne $readerResult
        }
    } catch {
        $observation.reasonCode = Get-CompileDiagnosticErrorCode $_
        if ([string]$observation.reasonCode -match '(clipboard_restore|foreground_restore|focus_restore)') { Fail ([string]$observation.reasonCode) }
    }
    [void](Assert-MetaEditorSourceBindingUnchanged $binding ([string]$Request.compilerPath) $source)
    if ((Get-Sha256 $source) -cne [string]$Request.expectedSourceDigest) { Fail "mt5_source_digest_mismatch" }
    return [ordered]@{
        schemaVersion = $ResultSchema; ok = $true; action = "diagnose_compile"; operationId = [string]$Request.operationId
        diagnosticOnly = $true; compileInvoked = $false; compileVerified = $false
        workingSourceSha256 = [string]$Request.expectedSourceDigest; sourceWindowBound = $true
        editorProcessId = [int]$editor.Id; editorWindowHandle = [long]$rootHandle.ToInt64()
        observation = $observation
    }
}

function Wait-CompileResult(
    [System.Windows.Automation.AutomationElement]$Root,
    [System.Diagnostics.Process]$Editor,
    [bool]$RequireSuccess,
    [string]$DifferentFromSha256,
    [int]$TimeoutSeconds,
    [string]$TimeoutCode
) {
    # Opening a source in an existing MetaEditor updates the MDI title before
    # the Toolbox provider has necessarily rebound its native Errors tab/list.
    # Likewise, a fresh EX5 can become visible a few milliseconds before the
    # owner-data compile rows have been repainted.  Treat those windows as a
    # bounded readiness race only: every accepted result still comes from the
    # exact native evidence parser, and post-F7 evidence must also differ from
    # the pre-F7 snapshot.  No stale success row is ever promoted.
    if ($TimeoutSeconds -lt 1 -or $TimeoutSeconds -gt 30 -or
        $TimeoutCode -cnotmatch '^[a-z0-9_]{3,100}$') { Fail "mt5_metaeditor_compile_wait_contract_invalid" }
    if (-not [string]::IsNullOrEmpty($DifferentFromSha256) -and
        $DifferentFromSha256 -cnotmatch '^[a-f0-9]{64}$') { Fail "mt5_metaeditor_compile_wait_contract_invalid" }
    [long]$startedTicks = [System.Diagnostics.Stopwatch]::GetTimestamp()
    [long]$deadlineTicks = $startedTicks + [long]($TimeoutSeconds * [System.Diagnostics.Stopwatch]::Frequency)
    do {
        try {
            [long]$attemptStartedTicks = [System.Diagnostics.Stopwatch]::GetTimestamp()
            $observed = Find-CompileResult $Root $Editor $RequireSuccess
            [long]$returnedTicks = [System.Diagnostics.Stopwatch]::GetTimestamp()
            # Capture time belongs to the trusted native row/count operation.
            # Clipboard publication may finish later, but complete restoration
            # still must succeed before Find-CompileResult returns anything.
            if ($observed -isnot [System.Collections.IDictionary] -or
                -not $observed.Contains("captureTimestampTicks") -or
                $observed.captureTimestampTicks -isnot [long] -or
                [long]$observed.captureTimestampTicks -lt $attemptStartedTicks -or
                [long]$observed.captureTimestampTicks -gt $returnedTicks) {
                Fail "mt5_metaeditor_compile_capture_unverified"
            }
            if ([string]::IsNullOrEmpty($DifferentFromSha256) -or
                [string]$observed.snapshotSha256 -cne $DifferentFromSha256) {
                if ([long]$observed.captureTimestampTicks -lt $deadlineTicks) { return $observed }
            }
        } catch [System.InvalidOperationException] {
            if ([string]$_.Exception.Message -cne "mt5_metaeditor_compile_result_unverified") { throw }
        }
        Start-Sleep -Milliseconds 100
    } while ([System.Diagnostics.Stopwatch]::GetTimestamp() -lt $deadlineTicks)
    Fail $TimeoutCode
}

function Get-CompileArtifactIdentity([string]$Source, [string]$Binary) {
    $identity = [ordered]@{}
    foreach ($entry in @(@("source", $Source), @("binary", $Binary))) {
        $path = [string]$entry[1]
        if (-not [System.IO.File]::Exists($path)) { Fail "mt5_compile_artifacts_changed_during_observation" }
        $before = [System.IO.FileInfo]::new($path)
        [long]$length = $before.Length
        [long]$modified = $before.LastWriteTimeUtc.Ticks
        $digest = Get-Sha256 $path
        $after = [System.IO.FileInfo]::new($path)
        if (-not $after.Exists -or $after.Length -ne $length -or $after.LastWriteTimeUtc.Ticks -ne $modified) {
            Fail "mt5_compile_artifacts_changed_during_observation"
        }
        $identity[[string]$entry[0]] = "$length|$modified|$digest"
    }
    return $identity
}

function Assert-CompileArtifactIdentity([object]$Before, [object]$After) {
    if ($Before.source -cne $After.source -or $Before.binary -cne $After.binary) {
        Fail "mt5_compile_artifacts_changed_during_observation"
    }
}

function Invoke-Compile([object]$Request, [bool]$RecoverOnly) {
    $source = Get-FullExistingFile $Request.sourcePath ".mq5" "mt5_source_invalid"
    if ((Get-Sha256 $source) -cne [string]$Request.expectedSourceDigest) { Fail "mt5_source_digest_mismatch" }
    $binary = [System.IO.Path]::GetFullPath([string]$Request.binaryPath)
    if ([System.IO.Path]::GetExtension($binary).ToLowerInvariant() -cne ".ex5") { Fail "mt5_binary_path_invalid" }
    $editorBinding = Get-Or-StartMetaEditor ([string]$Request.compilerPath) $source
    $editor = $editorBinding.Process
    $editorWindow = $editorBinding.Window
    Set-Foreground $editor $editorWindow
    $autoBefore = Get-AlgoTradingState $TerminalRoot
    $compileBefore = Wait-CompileResult $editorWindow $editor $false $null 10 "mt5_metaeditor_compile_result_not_ready"
    if ((Get-Sha256 $source) -cne [string]$Request.expectedSourceDigest) { Fail "mt5_source_digest_mismatch" }
    if ([System.IO.File]::Exists($binary)) {
        try { [System.IO.File]::Delete($binary) } catch { Fail "mt5_compile_stale_binary_remove_failed" }
        if ([System.IO.File]::Exists($binary)) { Fail "mt5_compile_stale_binary_remove_failed" }
    }
    $started = [DateTime]::UtcNow
    # Compilation is safe and idempotent.  A recovery without a durable receipt
    # recompiles visibly so it can prove a fresh current Errors row rather than
    # blessing an old 0/0 line and an old EX5.
    Send-BalancedKey ([IntPtr]$editorWindow.Current.NativeWindowHandle) 0x76 "mt5_metaeditor_compile_key_failed"
    $deadline = [DateTime]::UtcNow.AddSeconds([int]$Request.timeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ([System.IO.File]::Exists($binary) -and ([System.IO.FileInfo]$binary).Length -gt 0 -and ([System.IO.FileInfo]$binary).LastWriteTimeUtc -ge $started.AddSeconds(-1)) { break }
        Start-Sleep -Milliseconds 150
    }
    if (-not [System.IO.File]::Exists($binary) -or ([System.IO.FileInfo]$binary).Length -le 0 -or
        ([System.IO.FileInfo]$binary).LastWriteTimeUtc -lt $started.AddSeconds(-1)) { Fail "mt5_compile_binary_not_fresh" }
    $artifactBeforeRead = Get-CompileArtifactIdentity $source $binary
    $compileAfter = Wait-CompileResult $editorWindow $editor $true ([string]$compileBefore.snapshotSha256) 10 "mt5_metaeditor_compile_result_not_fresh"
    Assert-CompileArtifactIdentity $artifactBeforeRead (Get-CompileArtifactIdentity $source $binary)
    $editorBinding = Assert-MetaEditorSourceBindingUnchanged $editorBinding ([string]$Request.compilerPath) $source
    $editor = $editorBinding.Process
    $editorWindow = $editorBinding.Window
    $resultLine = [string]$compileAfter.resultLine
    Capture-Window $editor ([string]$Request.screenshotPath) $editorWindow
    $pre = New-Binding $editor "metaeditor" $autoBefore $editorWindow
    $autoAfter = Get-AlgoTradingState $TerminalRoot
    if ($autoBefore -ne $autoAfter) { Fail "mt5_algo_trading_state_changed" }
    $post = New-Binding $editor "metaeditor" $autoAfter $editorWindow
    Assert-CompileArtifactIdentity $artifactBeforeRead (Get-CompileArtifactIdentity $source $binary)
    return [ordered]@{
        schemaVersion = $ResultSchema; ok = $true; action = [string]$Request.action; operationId = [string]$Request.operationId
        compileInvoked = $true; recoveryRecompile = $RecoverOnly; exactSourceWindowVerified = $true; compileWorkingCopyVerified = $true
        freshBinaryObserved = $true; workingSourceSha256 = Get-Sha256 $source; workingBinarySha256 = Get-Sha256 $binary
        compileResultLine = $resultLine; compileResultBeforeSha256 = [string]$compileBefore.snapshotSha256
        compileResultAfterSha256 = [string]$compileAfter.snapshotSha256; compileResultRowCount = [int]$compileAfter.rowCount
        processBinding = $pre; postProcessBinding = $post
    }
}

function Select-TabExact([System.Windows.Automation.AutomationElement]$Tabs, [string[]]$Names, [string]$Code) {
    if ([string]$Tabs.Current.ClassName -ceq "SysTabControl32") {
        [IntPtr]$handle = Assert-NativeControl $Tabs "SysTabControl32" $Code
        try { $available = @([MetafxMt5TabNative]::GetNames($handle)) } catch { Fail $Code }
        $matches = @()
        for ($index = 0; $index -lt $available.Count; $index++) {
            foreach ($name in $Names) {
                if ($available[$index].Equals([string]$name, [System.StringComparison]::Ordinal)) {
                    $matches += [pscustomobject]@{ Index = $index; Name = [string]$available[$index] }
                }
            }
        }
        if ($matches.Count -ne 1) { Fail $Code }
        Set-Foreground $TerminalProcess
        try { $selected = [MetafxMt5TabNative]::SelectExact($handle, [string]$matches[0].Name) } catch { Fail $Code }
        if (-not $selected -or [MetafxMt5TabNative]::GetSelectedIndex($handle) -ne [int]$matches[0].Index) { Fail $Code }
        Start-Sleep -Milliseconds 200
        return $Tabs
    }
    $item = Get-ExactNamedControl $Tabs $Names $Code
    $pattern = $null
    if (-not $item.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$pattern)) { Fail $Code }
    $pattern.Select(); Start-Sleep -Milliseconds 200
    return $item
}

function Resolve-TesterReportTabNameExact(
    [System.Windows.Automation.AutomationElement]$Tabs,
    [bool]$Optimize,
    [string]$Code
) {
    [IntPtr]$handle = Assert-NativeControl $Tabs "SysTabControl32" $Code
    try { $available = @([MetafxMt5TabNative]::GetNames($handle)) } catch { Fail $Code }
    # Build 6230 renamed the single-test report tab from the legacy "Results"
    # caption to "Backtest".  Accept only those two exact, case-sensitive
    # captions and require exactly one of them to exist.  This deliberately
    # rejects partial/localized/look-alike captions and an ambiguous UI that
    # exposes both names at once.
    $allowlist = if ($Optimize) { @("Optimization Results") } else { @("Backtest", "Results") }
    $matches = @()
    foreach ($name in $available) {
        if ([string]$name -cnotin $allowlist) { continue }
        $matches += [string]$name
    }
    if ($matches.Count -ne 1) { Fail $Code }
    return [string]$matches[0]
}

function Get-ExactTesterResultsList(
    [object]$Request,
    [string]$ExpectedTabName,
    [string]$Code,
    [int]$ExpectedControlId = 0
) {
    if ($ExpectedTabName -cnotin @("Backtest", "Results", "Optimization Results")) { Fail $Code }
    $root = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    $tabs = Get-TesterResultTabs $root $Request.requiredAutomationIds $Code
    [void](Assert-TesterTabSelectedExact $tabs $ExpectedTabName $Code)
    $start = Get-ControlByIdPresent $root ([string]$Request.requiredAutomationIds.start) $Code
    if ((Read-TesterStartState $start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $testerPane = Get-ControlByIdPresent $root ([string]$Request.requiredAutomationIds.testerPane) $Code
    # Terminal build 6230 exposes the native report list as UIA Pane rather
    # than DataGrid/Table/List and marks it non-keyboard-focusable.  Bind by
    # native class and the exact Strategy Tester control id instead.
    $classCondition = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ClassNameProperty,
        "SysListView32"
    )
    $lists = @(Get-All $testerPane $classCondition | Where-Object {
        $_.Current.IsEnabled -and -not $_.Current.IsOffscreen
    })
    if ($lists.Count -ne 1) { Fail $Code }
    [IntPtr]$handle = Assert-NativeControl $lists[0] "SysListView32" $Code
    [int]$observedControlId = [MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
    [int]$requiredControlId = if ($ExpectedTabName -ceq "Optimization Results") {
        10511
    } elseif ($ExpectedControlId -gt 0) {
        $ExpectedControlId
    } else {
        $observedControlId
    }
    if ($observedControlId -le 0 -or $observedControlId -ne $requiredControlId -or
        ($ExpectedControlId -gt 0 -and $observedControlId -ne $ExpectedControlId)) { Fail $Code }
    return [ordered]@{
        root = $root
        tabs = $tabs
        testerPane = $testerPane
        list = $lists[0]
        listHandle = $handle
        controlId = $observedControlId
        tabName = $ExpectedTabName
    }
}

function Focus-UniqueResultsTable([object]$Request, [string]$ExpectedTabName) {
    $binding = Get-ExactTesterResultsList $Request $ExpectedTabName "mt5_report_results_table_not_verified"
    Set-Foreground $TerminalProcess $binding.root
    try {
        [MetafxMt5VisibleNative]::FocusListExact(
            [IntPtr]$binding.listHandle,
            [uint32]$TerminalProcess.Id,
            [IntPtr]$binding.root.Current.NativeWindowHandle,
            [int]$binding.controlId
        )
    } catch { Fail "mt5_report_results_table_focus_failed" }
    $immediate = Get-ExactTesterResultsList $Request $ExpectedTabName "mt5_report_results_table_not_verified" ([int]$binding.controlId)
    if ([IntPtr]$immediate.listHandle -ne [IntPtr]$binding.listHandle) { Fail "mt5_report_results_table_not_verified" }
    try {
        [MetafxMt5VisibleNative]::AssertListFocusExact(
            [IntPtr]$immediate.listHandle,
            [uint32]$TerminalProcess.Id,
            [IntPtr]$immediate.root.Current.NativeWindowHandle,
            [int]$immediate.controlId
        )
    } catch { Fail "mt5_report_results_table_focus_failed" }
    return $immediate
}

function Invoke-TesterResultsReportCommandExact(
    [object]$Request,
    [string]$ExpectedTabName,
    [IntPtr]$ExpectedListHandle,
    [string]$Code
) {
    # Build 6230 exposes single-test HTML export only as the exact nested path
    # Report > HTML (Internet Explorer), command 33420.  Optimization Results
    # instead uses its durable SpreadsheetML leaf.  Bind every path component,
    # caption and command id so neighbouring display/export commands can never
    # be dispatched by mistake.
    $expectedCommandText = if ($ExpectedTabName -ceq "Optimization Results") {
        "Export to XML (MS Office Excel)"
    } else {
        "HTML (Internet Explorer)"
    }
    [uint32]$expectedCommandId = if ($ExpectedTabName -ceq "Optimization Results") { 33543 } else { 33420 }
    $expectedParentText = if ($ExpectedTabName -ceq "Optimization Results") { $null } else { "Report" }
    $binding = Focus-UniqueResultsTable $Request $ExpectedTabName
    if ([IntPtr]$binding.listHandle -ne $ExpectedListHandle) { Fail "$($Code)_initial_list_changed" }
    [IntPtr]$rootHandle = [IntPtr]$binding.root.Current.NativeWindowHandle
    try {
        [IntPtr]$preexistingDialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact(
            [uint32]$TerminalProcess.Id,
            $rootHandle,
            [string[]]@("Save As", "Save")
        )
    } catch { Fail "$($Code)_dispatch_precondition_unverified" }
    if ($preexistingDialog -ne [IntPtr]::Zero) { Fail "$($Code)_dispatch_preexisting_dialog" }
    $popupToken = $null
    $primaryMenuError = $null
    $dispatchAttempted = $false
    try {
        $script:FailureCheckpoint = "report_context_menu_open"
        try {
            [MetafxMt5VisibleNative]::OpenListContextMenuExact(
                [IntPtr]$binding.listHandle,
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                [int]$binding.controlId
            )
        } catch { Fail "$($Code)_context_open_failed" }
        $script:FailureCheckpoint = "report_popup_bind"
        $popup = Get-ExactNativePopupMenuHost 3000 "$($Code)_popup_host_unverified"
        [IntPtr]$popupHandle = [IntPtr]$popup.Current.NativeWindowHandle
        try {
            $popupToken = [MetafxMt5VisibleNative]::CapturePopupMenuTokenExact(
                $popupHandle,
                [uint32]$TerminalProcess.Id,
                $rootHandle
            )
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "popup_bind") }
        $script:FailureCheckpoint = "report_command_select"
        # Wrap the whole conditional in an array expression.  Under
        # StrictMode, assigning an if-expression that emits one object unwraps
        # it to a scalar whose .Count property is unavailable.
        $commands = @(
          if ($ExpectedTabName -ceq "Optimization Results") {
            $popupToken.Items | Where-Object {
                [string]$_.Text -ceq $expectedCommandText -and [uint32]$_.CommandId -eq $expectedCommandId -and
                [bool]$_.IsEnabled -and -not [bool]$_.IsSeparator -and -not [bool]$_.HasSubmenu
            }
          } else {
            $popupToken.Items | Where-Object {
                [string]$_.Text -ceq $expectedParentText -and [bool]$_.IsEnabled -and
                -not [bool]$_.IsSeparator -and [bool]$_.HasSubmenu -and
                [IntPtr]$_.SubmenuHandle -ne [IntPtr]::Zero
            }
          }
        )
        if ($commands.Count -ne 1) { Fail "$($Code)_candidate_count_invalid" }
        if ($ExpectedTabName -ceq "Optimization Results") {
            $command = $commands[0]
            if ([string]$command.Text -cne $expectedCommandText -or
                [uint32]$command.CommandId -ne $expectedCommandId) { Fail "$($Code)_candidate_identity_changed" }
        } else {
            try {
                $command = [MetafxMt5VisibleNative]::AssertPopupSubmenuCommandFromTokenExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle,
                    $expectedParentText,
                    $expectedCommandText,
                    $expectedCommandId
                )
            } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "preflight") }
        }
        # Rebind the root, selected tab, Start-idle state, native list HWND/id,
        # focus, popup host and complete native menu token immediately before
        # dispatch.  This prevents a stale or neighbouring context menu from
        # being accepted as report export.
        $script:FailureCheckpoint = "report_pre_dispatch_rebind"
        try {
            $immediate = Get-ExactTesterResultsList $Request $ExpectedTabName $Code ([int]$binding.controlId)
        } catch {
            if ([string]$_.Exception.Message -ceq $Code) { Fail "$($Code)_results_rebind_unverified" }
            throw
        }
        if ([IntPtr]$immediate.listHandle -ne $ExpectedListHandle -or
            [IntPtr]$immediate.root.Current.NativeWindowHandle -ne $rootHandle) { Fail "$($Code)_results_binding_changed" }
        $script:FailureCheckpoint = "report_native_dispatch"
        try {
            [MetafxMt5VisibleNative]::AssertListFocusExact(
                [IntPtr]$immediate.listHandle,
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                [int]$immediate.controlId
            )
        } catch { Fail "$($Code)_results_focus_lost" }
        $immediatePopup = Get-ExactNativePopupMenuHost 0 "$($Code)_popup_rebind_unverified"
        if ([IntPtr]$immediatePopup.Current.NativeWindowHandle -ne $popupHandle) { Fail "$($Code)_popup_identity_changed" }
        try {
            [IntPtr]$immediateDialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact(
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                [string[]]@("Save As", "Save")
            )
        } catch { Fail "$($Code)_dispatch_precondition_unverified" }
        if ($immediateDialog -ne [IntPtr]::Zero) { Fail "$($Code)_dispatch_preexisting_dialog" }
        try {
            if ($ExpectedTabName -ceq "Optimization Results") {
                [void][MetafxMt5VisibleNative]::AssertPopupMenuCommandFromTokenExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle,
                    $expectedCommandText,
                    $expectedCommandId
                )
                $dispatchAttempted = $true
                [void][MetafxMt5VisibleNative]::InvokePopupMenuCommandExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle,
                    $expectedCommandText,
                    $expectedCommandId
                )
            } else {
                [void][MetafxMt5VisibleNative]::AssertPopupSubmenuCommandFromTokenExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle,
                    $expectedParentText,
                    $expectedCommandText,
                    $expectedCommandId
                )
                $dispatchAttempted = $true
                [void][MetafxMt5VisibleNative]::InvokePopupSubmenuCommandExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle,
                    $expectedParentText,
                    $expectedCommandText,
                    $expectedCommandId
                )
            }
            # Menu disappearance proves only that the exact targeted dispatch
            # was consumed.  Do not attempt to dismiss an already-destroyed or
            # recycled HWND in finally; require the exact owned Save dialog as
            # positive command evidence before returning to the caller.
            $popupToken = $null
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "dispatch") }
        $script:FailureCheckpoint = "report_dispatch_confirmation"
        [IntPtr]$confirmedDialog = Wait-ExactOwnedFileDialog @("Save As", "Save") "$($Code)_dispatch_unconfirmed"
        if ($confirmedDialog -eq [IntPtr]::Zero) { Fail "$($Code)_dispatch_unconfirmed" }
        return $confirmedDialog
    } catch {
        $primaryMenuError = $_
        # Bare rethrow preserves the original fail-closed reason.  Cleanup in
        # finally is best effort during this error path and must not mask it.
        throw
    } finally {
        if ($null -ne $popupToken -and -not $dispatchAttempted) {
            $script:FailureCheckpoint = "report_popup_cleanup"
            try {
                [MetafxMt5VisibleNative]::DismissPopupMenuExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle
                )
            } catch {
                if ($null -eq $primaryMenuError) { Fail "$($Code)_cleanup_failed" }
            }
        }
    }
}

function Save-VisibleReport(
    [object]$Request,
    [System.Diagnostics.Process]$Terminal,
    [System.Windows.Automation.AutomationElement]$Tabs,
    [string[]]$TabNames,
    [string]$ExportPath,
    [string]$ArtifactPath
) {
    $ExportPath = [System.IO.Path]::GetFullPath($ExportPath)
    $ArtifactPath = [System.IO.Path]::GetFullPath($ArtifactPath)
    $extension = [System.IO.Path]::GetExtension($ExportPath).ToLowerInvariant()
    $artifactExtension = [System.IO.Path]::GetExtension($ArtifactPath).ToLowerInvariant()
    $parent = [System.IO.Path]::GetDirectoryName($ExportPath)
    $artifactParent = [System.IO.Path]::GetDirectoryName($ArtifactPath)
    if ($TabNames.Count -ne 1 -or [string]$TabNames[0] -cnotin @("Backtest", "Results", "Optimization Results")) { Fail "mt5_report_tab_not_verified" }
    $expectedTabName = [string]$TabNames[0]
    $expectedExtensions = if ($expectedTabName -ceq "Optimization Results") { @(".xml") } else { @(".htm", ".html") }
    if ($extension -cnotin $expectedExtensions -or $artifactExtension -cne $extension -or
        $ExportPath -ceq $ArtifactPath -or
        -not [System.IO.Directory]::Exists($parent) -or
        -not [System.IO.Directory]::Exists($artifactParent)) { Fail "mt5_report_target_invalid" }
    if ([System.IO.File]::Exists($ExportPath) -or [System.IO.File]::Exists($ArtifactPath)) { Fail "mt5_report_target_preexisting" }
    $exportStarted = [DateTime]::UtcNow
    $script:FailureCheckpoint = "report_tab_select"
    [void](Select-TabExact $Tabs $TabNames "mt5_report_tab_not_verified")
    $script:FailureCheckpoint = "report_results_focus"
    $binding = Focus-UniqueResultsTable $Request $expectedTabName
    $script:FailureCheckpoint = "report_command_dispatch"
    [IntPtr]$dialog = Invoke-TesterResultsReportCommandExact $Request $expectedTabName ([IntPtr]$binding.listHandle) "mt5_report_export_command_not_verified"
    if ($dialog -eq [IntPtr]::Zero) { Fail "mt5_report_save_dialog_missing" }
    $script:FailureCheckpoint = "report_dialog_submit"
    Enter-ExactFileDialogPath $dialog $ExportPath @("Save") "mt5_report_save_failed"
    $script:FailureCheckpoint = "report_file_verify"
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    $maximumBytes = if ($expectedTabName -ceq "Optimization Results") { 536870912L } else { 33554432L }
    $lastDigest = $null
    $lastLength = -1L
    $lastWrite = [DateTime]::MinValue
    while ([DateTime]::UtcNow -lt $deadline) {
        $sizeInvalid = $false
        if ([System.IO.File]::Exists($ExportPath)) {
            try {
                $item = [System.IO.FileInfo]::new($ExportPath)
                if ($item.Length -gt $maximumBytes) {
                    $sizeInvalid = $true
                } elseif ($item.Length -gt 0 -and $item.CreationTimeUtc -ge $exportStarted.AddSeconds(-1) -and $item.LastWriteTimeUtc -ge $exportStarted.AddSeconds(-1) -and
                    (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0)) {
                    $checkpoint = Get-StableCheckpointFile $ExportPath $extension 1 $maximumBytes "mt5_report_not_created" $false $true
                    $digest = [string]$checkpoint.sha256
                    if ($lastDigest -ceq $digest -and $lastLength -eq $item.Length -and $lastWrite -eq $item.LastWriteTimeUtc) {
                        $artifactCreated = $false
                        try {
                            # Copy before Excel/browser can make the viewer file
                            # unavailable.  The immutable artifact is never the
                            # path handed to the external viewer.
                            [System.IO.File]::Copy($ExportPath, $ArtifactPath, $false)
                            $artifactCreated = $true
                            [System.IO.File]::SetLastWriteTimeUtc($ArtifactPath, [DateTime]::UtcNow)
                            $artifactCheckpoint = Get-StableCheckpointFile $ArtifactPath $extension 1 $maximumBytes "mt5_report_artifact_not_created" $false $false
                            if ([string]$artifactCheckpoint.sha256 -cne $digest) { Fail "mt5_report_artifact_digest_mismatch" }
                            $artifactItem = [System.IO.FileInfo]::new($ArtifactPath)
                            return [ordered]@{
                                createdFresh = $true
                                sha256 = $digest
                                byteSize = [long]$artifactItem.Length
                                createdAt = $artifactItem.CreationTimeUtc.ToString("o")
                                lastWriteAt = $artifactItem.LastWriteTimeUtc.ToString("o")
                                format = if ($expectedTabName -ceq "Optimization Results") { "spreadsheetml" } else { "html" }
                                tabName = $expectedTabName
                            }
                        } catch {
                            if ($artifactCreated -and [System.IO.File]::Exists($ArtifactPath)) {
                                try { [System.IO.File]::Delete($ArtifactPath) } catch {}
                            }
                        }
                    }
                    $lastDigest = $digest; $lastLength = [long]$item.Length; $lastWrite = $item.LastWriteTimeUtc
                }
            } catch {}
        }
        if ($sizeInvalid) { Fail "mt5_report_size_invalid" }
        Start-Sleep -Milliseconds 100
    }
    Fail "mt5_report_not_created"
}

function Get-StableCheckpointFile([object]$Value, [string]$Extension, [long]$MinimumBytes, [long]$MaximumBytes, [string]$Code, [bool]$CaptureBytes = $true, [bool]$AllowReportWriter = $false) {
    $raw = [string]$Value
    if (-not [System.IO.Path]::IsPathRooted($raw)) { Fail $Code }
    $full = [System.IO.Path]::GetFullPath($raw)
    if ([System.IO.Path]::GetExtension($full).ToLowerInvariant() -cne $Extension -or -not [System.IO.File]::Exists($full)) { Fail $Code }
    $stream = $null
    $hasher = $null
    $bytes = $null
    try {
        $directory = [System.IO.DirectoryInfo]::new([System.IO.Path]::GetDirectoryName($full))
        while ($null -ne $directory) {
            if (-not $directory.Exists -or (($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { Fail $Code }
            $directory = $directory.Parent
        }
        $before = [System.IO.FileInfo]::new($full)
        $before.Refresh()
        if ($before.Length -lt $MinimumBytes -or $before.Length -gt $MaximumBytes -or
            (($before.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { Fail $Code }
        $share = if ($AllowReportWriter) { [System.IO.FileShare]::ReadWrite } else { [System.IO.FileShare]::Read }
        $stream = [System.IO.File]::Open($full, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
        if ([MetafxMt5VisibleNative]::GetFileLinkCount($stream.SafeFileHandle.DangerousGetHandle()) -ne 1) { Fail $Code }
        if ($stream.Length -ne $before.Length -or ($CaptureBytes -and $stream.Length -gt [int]::MaxValue)) { Fail $Code }
        $hasher = [System.Security.Cryptography.SHA256]::Create()
        if ($CaptureBytes) {
            $bytes = [byte[]]::new([int]$stream.Length)
            $offset = 0
            while ($offset -lt $bytes.Length) {
                $read = $stream.Read($bytes, $offset, $bytes.Length - $offset)
                if ($read -le 0) { Fail $Code }
                $offset += $read
            }
            $digestBytes = $hasher.ComputeHash($bytes)
        } else {
            $digestBytes = $hasher.ComputeHash($stream)
        }
        if ($stream.ReadByte() -ne -1) { Fail $Code }
        $digest = [System.BitConverter]::ToString($digestBytes).Replace("-", "").ToLowerInvariant()
        $after = [System.IO.FileInfo]::new($full)
        $after.Refresh()
        if ($after.Length -ne $before.Length -or $after.CreationTimeUtc -ne $before.CreationTimeUtc -or
            $after.LastWriteTimeUtc -ne $before.LastWriteTimeUtc -or
            (($after.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) -or
            [MetafxMt5VisibleNative]::GetFileLinkCount($stream.SafeFileHandle.DangerousGetHandle()) -ne 1) { Fail $Code }
    } catch { Fail $Code }
    finally {
        if ($null -ne $hasher) { $hasher.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
    return [ordered]@{ path = $full; sha256 = $digest; byteSize = [long]$after.Length; item = $after; bytes = $bytes }
}

function Get-ExistingPngCheckpoint([object]$Value, [object]$ExpectedSha256, [string]$Code) {
    $evidence = Get-StableCheckpointFile $Value ".png" 1024 33554432 $Code
    $header = [byte[]]$evidence.bytes
    if ($header.Length -lt 8) { Fail $Code }
    $signature = [byte[]](137, 80, 78, 71, 13, 10, 26, 10)
    for ($index = 0; $index -lt 8; $index++) { if ($header[$index] -ne $signature[$index]) { Fail $Code } }
    if ($null -ne $ExpectedSha256 -and -not [string]::IsNullOrWhiteSpace([string]$ExpectedSha256) -and
        [string]$evidence.sha256 -cne [string]$ExpectedSha256) { Fail $Code }
    return $evidence
}

function Get-ExistingReportEvidence([object]$Request, [string[]]$TabNames, [string]$Path, [object]$ExpectedSha256) {
    if ($TabNames.Count -ne 1 -or [string]$TabNames[0] -cnotin @("Backtest", "Results", "Optimization Results")) { Fail "mt5_report_tab_not_verified" }
    $expectedTabName = [string]$TabNames[0]
    $extension = if ($expectedTabName -ceq "Optimization Results") { ".xml" } else { ".htm" }
    $maximumBytes = if ($expectedTabName -ceq "Optimization Results") { 536870912L } else { 33554432L }
    $evidence = Get-StableCheckpointFile $Path $extension 1 $maximumBytes "mt5_tester_recovery_checkpoint_invalid" $false $true
    if ($null -eq $ExpectedSha256 -or [string]$evidence.sha256 -cne [string]$ExpectedSha256) { Fail "mt5_tester_recovery_checkpoint_mismatch" }
    $dispatchItem = [System.IO.FileInfo]::new((Get-DispatchConfirmationPath $Request))
    if ($evidence.item.CreationTimeUtc -lt $dispatchItem.LastWriteTimeUtc.AddSeconds(-3) -or
        $evidence.item.LastWriteTimeUtc -lt $dispatchItem.LastWriteTimeUtc.AddSeconds(-3) -or
        $evidence.item.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(5)) { Fail "mt5_tester_recovery_checkpoint_invalid" }
    return [ordered]@{
        createdFresh = $true
        sha256 = [string]$evidence.sha256
        byteSize = [long]$evidence.byteSize
        createdAt = $evidence.item.CreationTimeUtc.ToString("o")
        lastWriteAt = $evidence.item.LastWriteTimeUtc.ToString("o")
        format = if ($expectedTabName -ceq "Optimization Results") { "spreadsheetml" } else { "html" }
        tabName = $expectedTabName
    }
}

function Get-OptimizationCacheLineage([object]$Request) {
    $code = "mt5_optimization_completion_lineage_invalid"
    try {
        $dataPath = [System.IO.Path]::GetFullPath([string]$Request.dataPath)
        $cacheRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($dataPath, "Tester", "cache"))
        if (-not [System.IO.Directory]::Exists($cacheRoot)) { Fail $code }
        foreach ($directory in @($dataPath, [System.IO.Path]::Combine($dataPath, "Tester"), $cacheRoot)) {
            $item = [System.IO.DirectoryInfo]::new($directory)
            if (-not $item.Exists -or (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { Fail $code }
        }
        $expertFileName = [string]$Request.expertFileName
        $expertStem = [System.IO.Path]::GetFileNameWithoutExtension($expertFileName)
        $symbol = ([string]$Request.testerSettings.symbol).Trim()
        $period = ([string]$Request.testerSettings.period).Trim()
        if ([string]::IsNullOrWhiteSpace($expertStem) -or [string]::IsNullOrWhiteSpace($symbol) -or [string]::IsNullOrWhiteSpace($period)) { Fail $code }
        if ([bool]$Request.testerSettings.useDate) {
            $from = [DateTime]::ParseExact([string]$Request.testerSettings.fromDate, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture).ToString("yyyyMMdd")
            $to = [DateTime]::ParseExact([string]$Request.testerSettings.toDate, "yyyy-MM-dd", [System.Globalization.CultureInfo]::InvariantCulture).ToString("yyyyMMdd")
            $datePattern = "{0}\.{1}" -f [regex]::Escape($from), [regex]::Escape($to)
            $datePolicy = "custom_period"
        } else {
            if ($null -ne $Request.testerSettings.fromDate -or $null -ne $Request.testerSettings.toDate) { Fail $code }
            $from = $null; $to = $null
            $datePattern = "(?<cacheFrom>[0-9]{8})\.(?<cacheTo>[0-9]{8})"
            $datePolicy = "entire_history"
        }
        $pattern = "^{0}\.{1}\.{2}\.{3}\.[0-9A-Fa-f]{{2}}\.[0-9A-Fa-f]{{32}}\.opt$" -f
            [regex]::Escape($expertStem), [regex]::Escape($symbol), [regex]::Escape($period), $datePattern
        $embeddedExpertPath = "Experts\" + (([string]$Request.expertUiPath).Trim().Replace("/", "\").TrimStart("\"))
        if (-not $embeddedExpertPath.EndsWith(".ex5", [System.StringComparison]::OrdinalIgnoreCase)) { $embeddedExpertPath += ".ex5" }
        $dispatchItem = [System.IO.FileInfo]::new((Get-DispatchConfirmationPath $Request))
        $matches = @()
        foreach ($candidatePath in [System.IO.Directory]::GetFiles($cacheRoot, "*.opt", [System.IO.SearchOption]::TopDirectoryOnly)) {
            $name = [System.IO.Path]::GetFileName($candidatePath)
            $match = [regex]::Match($name, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            if (-not $match.Success) { continue }
            $candidate = Get-StableCheckpointFile $candidatePath ".opt" 512 67108864 $code
            # MT5 reuses the same .opt inode for identical optimizer settings,
            # so CreationTimeUtc may belong to a prior run.  Bind this run to
            # the completed content write instead: it must be at/after the
            # durable dispatch and never before the inode was created.  The
            # exact filename, embedded expert path, symbol and content digest
            # below provide the remaining lineage identity.
            if ($candidate.item.LastWriteTimeUtc -lt $dispatchItem.LastWriteTimeUtc -or
                $candidate.item.CreationTimeUtc -gt [DateTime]::UtcNow.AddMinutes(5) -or
                $candidate.item.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(5) -or
                $candidate.item.LastWriteTimeUtc -lt $candidate.item.CreationTimeUtc) { continue }
            $bytes = [byte[]]$candidate.bytes
            $decoded = [System.Text.Encoding]::Unicode.GetString($bytes)
            $strings = @([regex]::Matches($decoded, "[ -~]{3,}") | ForEach-Object { [string]$_.Value })
            foreach ($required in @($expertStem, $embeddedExpertPath, $symbol)) {
                if (@($strings | Where-Object { $_.Equals($required, [System.StringComparison]::OrdinalIgnoreCase) }).Count -lt 1) { Fail $code }
            }
            $epochTicks = [DateTime]::new(1970, 1, 1, 0, 0, 0, [DateTimeKind]::Utc).Ticks
            $cacheFrom = if ($datePolicy -ceq "custom_period") { $from } else { [string]$match.Groups["cacheFrom"].Value }
            $cacheTo = if ($datePolicy -ceq "custom_period") { $to } else { [string]$match.Groups["cacheTo"].Value }
            $lineage = [ordered]@{
                schemaVersion = "ea-factory-mt5-optimization-cache-lineage-v1"
                relativePath = "Tester/cache/$name"
                sha256 = [string]$candidate.sha256
                byteSize = [long]$candidate.byteSize
                createdTimeUtcNs = [long](($candidate.item.CreationTimeUtc.Ticks - $epochTicks) * 100L)
                lastWriteTimeUtcNs = [long](($candidate.item.LastWriteTimeUtc.Ticks - $epochTicks) * 100L)
                expertFileName = $expertFileName
                expertUiPath = [string]$Request.expertUiPath
                deployedExpertSha256 = [string]$Request.expectedDeployedExpertSha256
                embeddedExpertPath = $embeddedExpertPath
                symbol = $symbol
                period = $period
                datePolicy = $datePolicy
                fromDate = if ([bool]$Request.testerSettings.useDate) { [string]$Request.testerSettings.fromDate } else { $null }
                toDate = if ([bool]$Request.testerSettings.useDate) { [string]$Request.testerSettings.toDate } else { $null }
                cacheFromDate = $cacheFrom
                cacheToDate = $cacheTo
            }
            $matches += ,$lineage
        }
        if ($matches.Count -ne 1) { Fail $code }
        return $matches[0]
    } catch { Fail $code }
}

function Get-OptimizationCacheLineageDigest([object]$Lineage) {
    $values = @(
        $Lineage.schemaVersion, $Lineage.relativePath, $Lineage.sha256,
        ([long]$Lineage.byteSize).ToString([System.Globalization.CultureInfo]::InvariantCulture),
        ([long]$Lineage.createdTimeUtcNs).ToString([System.Globalization.CultureInfo]::InvariantCulture),
        ([long]$Lineage.lastWriteTimeUtcNs).ToString([System.Globalization.CultureInfo]::InvariantCulture),
        $Lineage.expertFileName, $Lineage.expertUiPath, $Lineage.deployedExpertSha256,
        $Lineage.embeddedExpertPath, $Lineage.symbol, $Lineage.period, $Lineage.datePolicy,
        $Lineage.fromDate, $Lineage.toDate, $Lineage.cacheFromDate, $Lineage.cacheToDate
    ) | ForEach-Object { if ($null -eq $_) { "" } else { [string]$_ } }
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes([string]::Join("`n", [string[]]$values))
    return [System.BitConverter]::ToString([System.Security.Cryptography.SHA256]::Create().ComputeHash($bytes)).Replace("-", "").ToLowerInvariant()
}

function New-OptimizationCompletionCheckpointObject([object]$Request, [string]$SettingsSha256, [string]$ResultSha256, [string]$DispatchSha256) {
    $lineage = Get-OptimizationCacheLineage $Request
    return [ordered]@{
        schemaVersion = "ea-factory-mt5-optimization-completion-checkpoint-v1"
        operationId = [string]$Request.operationId
        stageId = "optimize"
        actionRequestDigest = [string]$Request.actionRequestDigest
        startBoundarySha256 = [string]$Request.startBoundarySha256
        dispatchConfirmationSha256 = $DispatchSha256
        testerSettingsSha256 = $SettingsSha256
        testerResultSha256 = $ResultSha256
        optimizationCacheLineage = $lineage
        optimizationCacheLineageDigest = Get-OptimizationCacheLineageDigest $lineage
    }
}

function Test-ExactOptimizationCompletionCheckpoint([object]$Actual, [object]$Expected) {
    $top = @("schemaVersion", "operationId", "stageId", "actionRequestDigest", "startBoundarySha256", "dispatchConfirmationSha256", "testerSettingsSha256", "testerResultSha256", "optimizationCacheLineage", "optimizationCacheLineageDigest")
    $lineage = @("schemaVersion", "relativePath", "sha256", "byteSize", "createdTimeUtcNs", "lastWriteTimeUtcNs", "expertFileName", "expertUiPath", "deployedExpertSha256", "embeddedExpertPath", "symbol", "period", "datePolicy", "fromDate", "toDate", "cacheFromDate", "cacheToDate")
    if (@($Actual.PSObject.Properties.Name).Count -ne $top.Count -or @($Actual.optimizationCacheLineage.PSObject.Properties.Name).Count -ne $lineage.Count) { return $false }
    if (@($top | Where-Object { $_ -cnotin @($Actual.PSObject.Properties.Name) }).Count -gt 0) { return $false }
    if (@($lineage | Where-Object { $_ -cnotin @($Actual.optimizationCacheLineage.PSObject.Properties.Name) }).Count -gt 0) { return $false }
    foreach ($field in $top | Where-Object { $_ -ne "optimizationCacheLineage" }) {
        if ([string]$Actual.$field -cne [string]$Expected.$field) { return $false }
    }
    foreach ($field in $lineage) {
        if ([string]$Actual.optimizationCacheLineage.$field -cne [string]$Expected.optimizationCacheLineage.$field) { return $false }
    }
    return $true
}

function Write-OptimizationCompletionCheckpoint([object]$Request, [string]$SettingsSha256, [string]$ResultSha256, [string]$DispatchSha256) {
    $path = [System.IO.Path]::GetFullPath([string]$Request.optimizationCompletionCheckpointPath)
    $payload = New-OptimizationCompletionCheckpointObject $Request $SettingsSha256 $ResultSha256 $DispatchSha256
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes(($payload | ConvertTo-Json -Depth 12 -Compress))
    try {
        $stream = [System.IO.File]::Open($path, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        try { $stream.Write($bytes, 0, $bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
    } catch { Fail "mt5_optimization_completion_checkpoint_exists" }
    $evidence = Get-StableCheckpointFile $path ".json" 1 262144 "mt5_optimization_completion_checkpoint_invalid"
    return [ordered]@{ checkpoint = $payload; sha256 = [string]$evidence.sha256 }
}

function Assert-OptimizationCompletionCheckpoint([object]$Request, [string]$SettingsSha256, [string]$ResultSha256, [string]$DispatchSha256) {
    $path = [System.IO.Path]::GetFullPath([string]$Request.optimizationCompletionCheckpointPath)
    if (-not [System.IO.File]::Exists($path)) { Fail "mt5_optimization_completion_checkpoint_missing" }
    $evidence = Get-StableCheckpointFile $path ".json" 1 262144 "mt5_optimization_completion_checkpoint_invalid"
    try {
        $text = [System.Text.UTF8Encoding]::new($false, $true).GetString([byte[]]$evidence.bytes)
        $actual = $text | ConvertFrom-Json
    } catch { Fail "mt5_optimization_completion_checkpoint_invalid" }
    $expected = New-OptimizationCompletionCheckpointObject $Request $SettingsSha256 $ResultSha256 $DispatchSha256
    if (-not (Test-ExactOptimizationCompletionCheckpoint $actual $expected)) { Fail "mt5_optimization_completion_checkpoint_mismatch" }
    $digest = [string]$evidence.sha256
    if ($null -ne $Request.optimizationCompletionCheckpointSha256 -and
        -not [string]::IsNullOrWhiteSpace([string]$Request.optimizationCompletionCheckpointSha256) -and
        $digest -cne [string]$Request.optimizationCompletionCheckpointSha256) { Fail "mt5_optimization_completion_checkpoint_mismatch" }
    return [ordered]@{ checkpoint = $expected; sha256 = $digest }
}

function Test-Mt5SetValueEquivalent([string]$Actual, [string]$Expected, [string]$Kind) {
    $left = $Actual.Trim(); $right = $Expected.Trim()
    if ($Kind -ceq "bool") {
        $aliases = @{ "true" = "1"; "false" = "0"; "1" = "1"; "0" = "0" }
        $leftKey = $left.ToLowerInvariant(); $rightKey = $right.ToLowerInvariant()
        return ($aliases.ContainsKey($leftKey) -and $aliases.ContainsKey($rightKey) -and $aliases[$leftKey] -ceq $aliases[$rightKey])
    }
    $leftNumber = 0D; $rightNumber = 0D
    $style = [System.Globalization.NumberStyles]::Float
    return ([decimal]::TryParse($left, $style, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$leftNumber) -and
        [decimal]::TryParse($right, $style, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$rightNumber) -and
        $leftNumber -eq $rightNumber)
}

function Get-Mt5SetRows([string]$Path, [string]$Code) {
    try { $lines = [System.IO.File]::ReadAllLines($Path) } catch { Fail $Code }
    $rows = @(); $seen = @{}
    foreach ($rawLine in $lines) {
        $line = ([string]$rawLine).Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith(";")) { continue }
        $match = [regex]::Match($line, "^([A-Za-z_][A-Za-z0-9_]*)=([^|`r`n]+)\|\|([^|`r`n]+)\|\|([^|`r`n]+)\|\|([^|`r`n]+)\|\|([YyNn10])$")
        if (-not $match.Success) { Fail $Code }
        $name = $match.Groups[1].Value
        $folded = $name.ToLowerInvariant()
        if ($seen.ContainsKey($folded)) { Fail $Code }
        $seen[$folded] = $true
        $rows += [pscustomobject]@{
            inputName = $name; current = $match.Groups[2].Value.Trim(); start = $match.Groups[3].Value.Trim()
            step = $match.Groups[4].Value.Trim(); stop = $match.Groups[5].Value.Trim()
            enabled = ([string]$match.Groups[6].Value).ToUpperInvariant() -in @("Y", "1")
        }
    }
    if ($rows.Count -lt 1) { Fail $Code }
    return @($rows)
}

function Test-Mt5NativeDisabledBoolRangeEquivalent([object]$Actual, [object]$Expected) {
    if ([string]$Expected.valueKind -cne "bool" -or [bool]$Expected.enabled) { return $false }
    # The signed source must still be a disabled default-only bool row. MT5's
    # native Save canonicalizes only the inactive range metadata to
    # false/0/true; it must preserve the current tester value separately.
    if (-not (Test-Mt5SetValueEquivalent ([string]$Actual.current) ([string]$Expected.current) "bool") -or
        -not (Test-Mt5SetValueEquivalent ([string]$Expected.start) ([string]$Expected.current) "bool") -or
        -not (Test-Mt5SetValueEquivalent ([string]$Expected.step) "1" "bool") -or
        -not (Test-Mt5SetValueEquivalent ([string]$Expected.stop) ([string]$Expected.current) "bool")) { return $false }
    return ((Test-Mt5SetValueEquivalent ([string]$Actual.start) "false" "bool") -and
        (Test-Mt5SetValueEquivalent ([string]$Actual.step) "0" "bool") -and
        (Test-Mt5SetValueEquivalent ([string]$Actual.stop) "true" "bool"))
}

function Assert-Mt5SetReference(
    [object]$Reference,
    [string]$Path,
    [string]$Code,
    [bool]$RequireReferenceFileSha = $true,
    [bool]$AllowNativeDisabledBoolRangeNormalization = $false
) {
    $setPath = Get-FullExistingFile $Path ".set" $Code
    $observedSha = Get-Sha256 $setPath
    if ([string]$Reference.schemaVersion -cne "ea-factory-mt5-set-ref-v1" -or
        ($RequireReferenceFileSha -and $observedSha -cne [string]$Reference.sha256)) { Fail $Code }
    $expected = @($Reference.expectedReadbackEntries)
    $rows = @(Get-Mt5SetRows $setPath $Code)
    if ($expected.Count -lt 1 -or $rows.Count -ne $expected.Count -or [int]$Reference.entryCount -ne $expected.Count) { Fail $Code }
    for ($index = 0; $index -lt $expected.Count; $index++) {
        $wanted = $expected[$index]; $actual = $rows[$index]
        if ([int]$wanted.ordinal -ne $index -or
            [string]$actual.inputName -cne [string]$wanted.inputName -or
            [bool]$actual.enabled -ne [bool]$wanted.enabled) { Fail $Code }
        if (-not (Test-Mt5SetValueEquivalent ([string]$actual.current) ([string]$wanted.current) ([string]$wanted.valueKind))) { Fail $Code }
        $rangeMatches = $true
        foreach ($field in @("start", "step", "stop")) {
            if (-not (Test-Mt5SetValueEquivalent ([string]$actual.$field) ([string]$wanted.$field) ([string]$wanted.valueKind))) {
                $rangeMatches = $false
                break
            }
        }
        if (-not $rangeMatches -and
            -not ($AllowNativeDisabledBoolRangeNormalization -and
                (Test-Mt5NativeDisabledBoolRangeEquivalent $actual $wanted))) { Fail $Code }
    }
    return $observedSha
}

function Assert-TesterTabSelectedExact(
    [System.Windows.Automation.AutomationElement]$Tabs,
    [string]$ExpectedName,
    [string]$Code
) {
    [IntPtr]$tabsHandle = Assert-NativeControl $Tabs "SysTabControl32" $Code
    if ([MetafxMt5VisibleNative]::GetDlgCtrlID($tabsHandle) -ne 10002) { Fail $Code }
    try {
        $names = @([MetafxMt5TabNative]::GetNames($tabsHandle))
        $selectedIndex = [MetafxMt5TabNative]::GetSelectedIndex($tabsHandle)
    } catch { Fail $Code }
    $matches = @()
    for ($index = 0; $index -lt $names.Count; $index++) {
        if ([string]$names[$index] -ceq $ExpectedName) { $matches += $index }
    }
    if ($matches.Count -ne 1 -or $selectedIndex -ne [int]$matches[0]) { Fail $Code }
    return $ExpectedName
}

function Select-TesterTabExact(
    [object]$Request,
    [System.Windows.Automation.AutomationElement]$Root,
    [object]$Required,
    [string]$ExpectedName,
    [string]$Code
) {
    $tabs = Get-TesterResultTabs $Root $Required $Code
    [IntPtr]$tabsHandle = Assert-NativeControl $tabs "SysTabControl32" $Code
    try {
        $names = @([MetafxMt5TabNative]::GetNames($tabsHandle))
        if (@($names | Where-Object { [string]$_ -ceq $ExpectedName }).Count -ne 1 -or
            -not [MetafxMt5TabNative]::SelectExact($tabsHandle, $ExpectedName)) { Fail $Code }
    } catch { Fail $Code }
    Start-Sleep -Milliseconds 150
    $reboundRoot = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    $reboundTabs = Get-TesterResultTabs $reboundRoot $Required $Code
    [void](Assert-TesterTabSelectedExact $reboundTabs $ExpectedName $Code)
    return [ordered]@{ root = $reboundRoot; tabs = $reboundTabs }
}

function Get-ExactTesterInputsList(
    [System.Windows.Automation.AutomationElement]$Root,
    [System.Windows.Automation.AutomationElement]$Tabs,
    [string]$Code
) {
    [IntPtr]$rootHandle = [IntPtr]::Zero
    [int]$rootProcessId = 0
    try {
        $rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
        $rootProcessId = [int]$Root.Current.ProcessId
    } catch { Fail $Code }
    if ($rootHandle -eq [IntPtr]::Zero -or
        $rootHandle -ne [IntPtr]$script:TerminalRootHandle -or
        $rootProcessId -ne $TerminalProcess.Id -or
        -not [MetafxMt5VisibleNative]::IsWindow($rootHandle) -or
        (Get-NativeOwner $rootHandle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($rootHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle) { Fail $Code }
    [void](Assert-TesterTabSelectedExact $Tabs "Inputs" $Code)
    $list = Get-ControlById $Root "10494" $Code
    [IntPtr]$handle = Assert-NativeControl $list "SysListView32" $Code
    if ([MetafxMt5VisibleNative]::GetDlgCtrlID($handle) -ne 10494 -or
        (Get-NativeOwner $handle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle) { Fail $Code }
    return $list
}

function Invoke-TesterInputsContextCommandExact(
    [object]$Request,
    [string]$ExpectedName,
    [uint32]$ExpectedCommandId,
    [string]$Code
) {
    if (($ExpectedName -cne "Load" -or $ExpectedCommandId -ne 33160) -and
        ($ExpectedName -cne "Save" -or $ExpectedCommandId -ne 33159)) { Fail $Code }
    $bindingCode = "$($Code)_inputs_binding_failed"
    $foregroundCode = "$($Code)_inputs_foreground_failed"
    $focusCode = "$($Code)_inputs_focus_failed"
    $focusReadbackCode = "$($Code)_inputs_focus_readback_failed"
    $contextCode = "$($Code)_inputs_context_menu_failed"
    $popupCode = "$($Code)_inputs_popup_failed"
    $controlRebindCode = "$($Code)_inputs_control_rebind_failed"
    [string[]]$expectedDialogNames = if ($ExpectedName -ceq "Load") { @("Open") } else { @("Save As", "Save") }
    $root = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    $tabs = Get-TesterResultTabs $root $Request.requiredAutomationIds $bindingCode
    [void](Assert-TesterTabSelectedExact $tabs "Inputs" $bindingCode)
    $start = Get-ControlByIdPresent $root ([string]$Request.requiredAutomationIds.start) $bindingCode
    if ((Read-TesterStartState $start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $list = Get-ExactTesterInputsList $root $tabs $bindingCode
    [IntPtr]$listHandle = [IntPtr]$list.Current.NativeWindowHandle
    [IntPtr]$rootHandle = [IntPtr]$root.Current.NativeWindowHandle
    try {
        [IntPtr]$preexistingDialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact(
            [uint32]$TerminalProcess.Id,
            $rootHandle,
            $expectedDialogNames
        )
    } catch { Fail "$($Code)_dispatch_precondition_unverified" }
    if ($preexistingDialog -ne [IntPtr]::Zero) { Fail "$($Code)_dispatch_preexisting_dialog" }
    $script:FailureCheckpoint = "inputs_list_focus"
    try { Set-Foreground $TerminalProcess $root } catch { Fail $foregroundCode }
    try {
        [MetafxMt5VisibleNative]::FocusListExact(
            $listHandle,
            [uint32]$TerminalProcess.Id,
            $rootHandle,
            10494
        )
    } catch { Fail $focusCode }
    try {
        [MetafxMt5VisibleNative]::AssertListFocusExact(
            $listHandle,
            [uint32]$TerminalProcess.Id,
            $rootHandle,
            10494
        )
    } catch { Fail $focusReadbackCode }
    $popupToken = $null
    $primaryMenuError = $null
    $dispatchAttempted = $false
    try {
        $script:FailureCheckpoint = "inputs_context_menu_open"
        try {
            [MetafxMt5VisibleNative]::OpenInputsContextMenuExact(
                $listHandle,
                [uint32]$TerminalProcess.Id,
                $rootHandle
            )
        } catch { Fail $contextCode }
        $script:FailureCheckpoint = "inputs_popup_bind"
        $popup = Get-ExactNativePopupMenuHost 3000 $popupCode
        [IntPtr]$popupHandle = [IntPtr]$popup.Current.NativeWindowHandle
        try {
            $popupToken = [MetafxMt5VisibleNative]::CapturePopupMenuTokenExact(
                $popupHandle,
                [uint32]$TerminalProcess.Id,
                $rootHandle
            )
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "popup_bind") }
        $script:FailureCheckpoint = "inputs_command_preflight"
        try {
            $popupToken = [MetafxMt5VisibleNative]::RebindPopupMenuTokenIgnoringHighlightExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $rootHandle
            )
            $command = [MetafxMt5VisibleNative]::AssertPopupMenuCommandFromReboundTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                $ExpectedName,
                $ExpectedCommandId
            )
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "preflight") }
        if ([string]$command.Text -cne $ExpectedName -or [uint32]$command.CommandId -ne $ExpectedCommandId -or
            -not [bool]$command.IsEnabled -or [bool]$command.IsSeparator -or [bool]$command.HasSubmenu) { Fail $Code }
        # Rebind every control and the complete popup token immediately before
        # dispatch.  In particular never confuse the neighbouring
        # Start Optimization command (38763) with Load/Save.
        $script:FailureCheckpoint = "inputs_control_rebind"
        $immediateRoot = Get-BoundTerminalRoot $Request $rootHandle
        $immediateTabs = Get-TesterResultTabs $immediateRoot $Request.requiredAutomationIds $controlRebindCode
        [void](Assert-TesterTabSelectedExact $immediateTabs "Inputs" $controlRebindCode)
        $immediateStart = Get-ControlByIdPresent $immediateRoot ([string]$Request.requiredAutomationIds.start) $controlRebindCode
        if ((Read-TesterStartState $immediateStart "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        $immediateList = Get-ExactTesterInputsList $immediateRoot $immediateTabs $controlRebindCode
        if ([IntPtr]$immediateList.Current.NativeWindowHandle -ne $listHandle) { Fail $controlRebindCode }
        $immediatePopup = Get-ExactNativePopupMenuHost 0 $popupCode
        if ([IntPtr]$immediatePopup.Current.NativeWindowHandle -ne $popupHandle) { Fail $popupCode }
        # Close the dialog TOCTOU window immediately before dispatch.  Since no
        # command has been queued yet, any exact owned dialog here is stale or
        # externally created and must not be accepted as dispatch evidence.
        try {
            [IntPtr]$immediateDialog = [MetafxMt5VisibleNative]::FindOwnedDialogExact(
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                $expectedDialogNames
            )
        } catch { Fail "$($Code)_dispatch_precondition_unverified" }
        if ($immediateDialog -ne [IntPtr]::Zero) { Fail "$($Code)_dispatch_preexisting_dialog" }
        $script:FailureCheckpoint = "inputs_command_preflight_immediate"
        try {
            $popupToken = [MetafxMt5VisibleNative]::RebindPopupMenuTokenIgnoringHighlightExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $rootHandle
            )
            $commandImmediatelyBefore = [MetafxMt5VisibleNative]::AssertPopupMenuCommandFromReboundTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                $ExpectedName,
                $ExpectedCommandId
            )
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "preflight") }
        if ([string]$commandImmediatelyBefore.Text -cne $ExpectedName -or
            [uint32]$commandImmediatelyBefore.CommandId -ne $ExpectedCommandId -or
            -not [bool]$commandImmediatelyBefore.IsEnabled -or [bool]$commandImmediatelyBefore.IsSeparator -or
            [bool]$commandImmediatelyBefore.HasSubmenu) { Fail $Code }
        $script:FailureCheckpoint = "inputs_native_dispatch"
        try {
            $dispatchAttempted = $true
            [void][MetafxMt5VisibleNative]::InvokePopupMenuCommandFromReboundTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $rootHandle,
                $ExpectedName,
                $ExpectedCommandId
            )
            # The exact popup was consumed.  Do not attempt to dismiss a dead or
            # recycled HWND; the new exact owned dialog below is the positive
            # command proof and no ambiguous dispatch is ever retried.
            $popupToken = $null
        } catch { Fail (Resolve-PopupDispatchFailureCode $_ $Code "dispatch") }
        $script:FailureCheckpoint = "inputs_dispatch_confirmation"
        [IntPtr]$confirmedDialog = Wait-ExactOwnedFileDialog $expectedDialogNames "$($Code)_dispatch_unconfirmed"
        if ($confirmedDialog -eq [IntPtr]::Zero) { Fail "$($Code)_dispatch_unconfirmed" }
        return $confirmedDialog
    } catch {
        $primaryMenuError = $_
        throw
    } finally {
        if ($null -ne $popupToken -and -not $dispatchAttempted) {
            try {
                [MetafxMt5VisibleNative]::DismissPopupMenuExact(
                    $popupToken,
                    [uint32]$TerminalProcess.Id,
                    $rootHandle
                )
            } catch {
                if ($null -eq $primaryMenuError) { Fail "$($Code)_cleanup_failed" }
            }
        }
    }
}

function Restore-TesterSettingsTabExact([object]$Request, [string]$Code) {
    return Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $false $Code
}

function Load-And-VerifyInputSet([object]$Request, [System.Windows.Automation.AutomationElement]$Root, [object]$Reference, [string]$ReadbackPath, [string]$ScreenshotPath, [string]$Code) {
    $setPath = Get-FullExistingFile $Reference.path ".set" $Code
    [void](Assert-Mt5SetReference $Reference $setPath $Code)
    $readback = [System.IO.Path]::GetFullPath($ReadbackPath)
    $readbackParent = [System.IO.Path]::GetDirectoryName($readback)
    if ([System.IO.Path]::GetExtension($readback).ToLowerInvariant() -cne ".set" -or
        -not [System.IO.Directory]::Exists($readbackParent)) { Fail "$($Code)_readback_path_invalid" }
    # A failed pre-Start attempt can leave a complete operation-scoped
    # readback.  Accept it only after full semantic verification, still reload
    # the signed source set into the current tester, and never overwrite it.
    $existingReadbackSha = $null
    if ([System.IO.File]::Exists($readback)) {
        $existingReadbackSha = Assert-Mt5SetReference $Reference $readback "$($Code)_preexisting_readback_mismatch" $false $true
    }
    if ([IntPtr]$Root.Current.NativeWindowHandle -ne [IntPtr]$script:TerminalRootHandle) { Fail "$($Code)_root_mismatch" }

    [IntPtr]$activeDialog = [IntPtr]::Zero
    $failure = $null
    $result = $null
    try {
        # Every admission starts from an exact, idle Settings tab.  MT5 build
        # 6230 hosts inputs directly on the Strategy Tester Inputs tab; there
        # is no MT4-style Expert properties dialog.
        $settings = Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $false "$($Code)_settings_not_verified"
        if ((Read-TesterStartState $settings.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        [void](Close-NativeComboDropDownExact $settings.controls.expert "$($Code)_combo_cleanup_failed")
        $selectedInputs = Select-TesterTabExact $Request $settings.root $Request.requiredAutomationIds "Inputs" "$($Code)_tab_not_verified"
        [void](Get-ExactTesterInputsList $selectedInputs.root $selectedInputs.tabs "$($Code)_list_not_verified")

        $activeDialog = Invoke-TesterInputsContextCommandExact $Request "Load" 33160 "$($Code)_load_command_not_verified"
        if ($activeDialog -eq [IntPtr]::Zero) { Fail "$($Code)_load_dialog_missing" }
        Enter-ExactFileDialogPath $activeDialog $setPath @("Open") "$($Code)_load_failed"
        $activeDialog = [IntPtr]::Zero
        Start-Sleep -Milliseconds 300

        # Rebind the exact Inputs tab/list after the shell dialog because MT5
        # can recreate providers while applying a preset.
        $loadRoot = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
        $loadTabs = Get-TesterResultTabs $loadRoot $Request.requiredAutomationIds "$($Code)_load_readback_failed"
        [void](Get-ExactTesterInputsList $loadRoot $loadTabs "$($Code)_load_readback_failed")
        $loadStart = Get-ControlByIdPresent $loadRoot ([string]$Request.requiredAutomationIds.start) "$($Code)_load_readback_failed"
        if ((Read-TesterStartState $loadStart "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }

        if ($null -eq $existingReadbackSha) {
            $activeDialog = Invoke-TesterInputsContextCommandExact $Request "Save" 33159 "$($Code)_save_command_not_verified"
            if ($activeDialog -eq [IntPtr]::Zero) { Fail "$($Code)_save_dialog_missing" }
            Enter-ExactFileDialogPath $activeDialog $readback @("Save") "$($Code)_save_failed"
            $activeDialog = [IntPtr]::Zero
            $deadline = [DateTime]::UtcNow.AddSeconds(15)
            while ([DateTime]::UtcNow -lt $deadline -and -not [System.IO.File]::Exists($readback)) { Start-Sleep -Milliseconds 100 }
            if (-not [System.IO.File]::Exists($readback) -or ([System.IO.FileInfo]$readback).Length -le 0) { Fail "$($Code)_readback_missing" }
            $readbackSha = Assert-Mt5SetReference $Reference $readback "$($Code)_readback_mismatch" $false $true
        } else {
            $readbackSha = [string]$existingReadbackSha
        }
        if (-not [string]::IsNullOrWhiteSpace($ScreenshotPath)) {
            $captureRoot = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
            $captureTabs = Get-TesterResultTabs $captureRoot $Request.requiredAutomationIds "$($Code)_screenshot_state_not_verified"
            [void](Get-ExactTesterInputsList $captureRoot $captureTabs "$($Code)_screenshot_state_not_verified")
            Capture-Window $TerminalProcess $ScreenshotPath $captureRoot ([IntPtr]$script:TerminalRootHandle)
        }
        $result = [ordered]@{
            sourceSetSha256 = [string]$Reference.sha256
            readbackSetSha256 = [string]$readbackSha
            readbackEntriesDigest = [string]$Reference.expectedReadbackEntriesDigest
        }
    } catch {
        $failure = $_
    }

    # Cleanup is mandatory on every branch: close only the exact owned shell
    # dialog (when still present), return to Settings, reacquire all controls,
    # close the expert combo, and prove Start is still idle.
    Close-ExactOwnedFileDialogAfterFailure $activeDialog "$($Code)_dialog_cleanup_failed"
    $restored = Restore-TesterSettingsTabExact $Request "$($Code)_settings_restore_failed"
    if ((Read-TesterStartState $restored.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    [void](Close-NativeComboDropDownExact $restored.controls.expert "$($Code)_combo_cleanup_failed")
    if ($null -ne $failure) { throw $failure }
    return $result
}

function Get-BoundTerminalRoot([object]$Request, [IntPtr]$ExpectedRootHandle = [IntPtr]::Zero) {
    [long]$signedRootValue = [long]$Request.expectedTerminalWindowHandle
    if ($signedRootValue -le 0) { Fail "mt5_terminal_process_changed" }
    [IntPtr]$signedRoot = [IntPtr][long]$signedRootValue
    if ($ExpectedRootHandle -eq [IntPtr]::Zero) { $ExpectedRootHandle = $signedRoot }
    if ($ExpectedRootHandle -ne $signedRoot -or
        $script:TerminalRootHandle -eq [IntPtr]::Zero -or
        $script:TerminalRootHandle -ne $signedRoot) {
        Fail "mt5_terminal_window_changed"
    }
    try { $TerminalProcess.Refresh() } catch { Fail "mt5_terminal_process_changed" }
    if ($TerminalProcess.HasExited -or
        $TerminalProcess.Id -ne [int]$Request.expectedTerminalProcessId) {
        Fail "mt5_terminal_process_changed"
    }
    if (-not [MetafxMt5VisibleNative]::IsWindow($ExpectedRootHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowVisible($ExpectedRootHandle) -or
        -not [MetafxMt5VisibleNative]::IsWindowEnabled($ExpectedRootHandle) -or
        (Get-NativeOwner $ExpectedRootHandle) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($ExpectedRootHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $ExpectedRootHandle) {
        Fail "mt5_terminal_window_changed"
    }
    $root = Get-Root $TerminalProcess $ExpectedRootHandle
    [IntPtr]$rootHandle = [IntPtr]$root.Current.NativeWindowHandle
    if ($root.Current.ProcessId -ne $TerminalProcess.Id -or
        $rootHandle -ne $ExpectedRootHandle -or
        (Get-NativeOwner $rootHandle) -ne $TerminalProcess.Id) {
        Fail "mt5_terminal_window_changed"
    }
    return $root
}

function Get-BoundTesterControlSet(
    [object]$Request,
    [IntPtr]$ExpectedRootHandle = [IntPtr]::Zero,
    [bool]$AllowTesterPaneReveal = $true
) {
    $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    $ids = $Request.requiredAutomationIds
    if ($AllowTesterPaneReveal) {
        Ensure-TesterPaneVisible $Request $root
        Ensure-TesterSingleModeReady $Request $root
        $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    } elseif ($null -eq (Find-ControlByIdPresent $root ([string]$ids.testerPane))) {
        Fail "mt5_tester_controls_not_verified"
    }
    $controls = [ordered]@{}
    foreach ($property in $ids.PSObject.Properties) {
        $controls[$property.Name] = if ([string]$property.Name -ceq "tabs") {
            Get-TesterResultTabs $root $ids "mt5_tester_controls_not_verified"
        } else {
            Get-ControlByIdPresent $root ([string]$property.Value) "mt5_tester_controls_not_verified"
        }
    }
    return [ordered]@{ root = $root; controls = $controls }
}

function Get-BoundOptimizationCriterion(
    [object]$Request,
    [string]$Code = "mt5_criterion_control_not_verified",
    [bool]$AllowOffscreenReadback = $false
) {
    $criterionId = [string]$Request.optimizationCriterionAutomationId
    if ($criterionId -cne "10507") {
        Fail $Code
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        $bound = Get-BoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
        $root = $bound.root
        [IntPtr]$optimizationHandle = Assert-NativeControl $bound.controls.optimization "ComboBox" $Code
        [IntPtr]$settingsParentHandle = [MetafxMt5VisibleNative]::GetParent($optimizationHandle)
        if ($settingsParentHandle -eq [IntPtr]::Zero -or
            -not [MetafxMt5VisibleNative]::IsWindow($settingsParentHandle) -or
            -not [MetafxMt5VisibleNative]::IsWindowVisible($settingsParentHandle) -or
            -not [MetafxMt5VisibleNative]::IsWindowEnabled($settingsParentHandle) -or
            (Get-NativeOwner $settingsParentHandle) -ne $TerminalProcess.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($settingsParentHandle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle) {
            Fail $Code
        }
        try {
            [IntPtr]$criterionHandle = [MetafxMt5VisibleNative]::FindChildControlExact(
                $settingsParentHandle,
                [uint32]$TerminalProcess.Id,
                [IntPtr]$script:TerminalRootHandle,
                10507,
                "ComboBox"
            )
            $criterion = [System.Windows.Automation.AutomationElement]::FromHandle($criterionHandle)
        } catch {
            $criterion = $null
        }
        if ($null -ne $criterion -and
            $criterion.Current.IsEnabled -and
            ($AllowOffscreenReadback -or -not $criterion.Current.IsOffscreen)) {
            [IntPtr]$criterionHandle = Assert-NativeControl $criterion "ComboBox" $Code
            if ([MetafxMt5VisibleNative]::GetDlgCtrlID($criterionHandle) -ne 10507 -or
                [MetafxMt5VisibleNative]::GetParent($criterionHandle) -ne $settingsParentHandle) {
                Fail $Code
            }
            $bound.controls["criterion"] = $criterion
            return $bound
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    Fail $Code
}

function Get-BoundVisualModeControl(
    [object]$Request,
    [string]$Code = "mt5_visual_mode_control_not_verified"
) {
    $visualId = [string]$Request.requiredAutomationIds.visualMode
    if ($visualId -cne "10490") { Fail $Code }
    $bound = Get-BoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
    $visual = $bound.controls.visualMode
    if ($null -eq $visual) { Fail $Code }
    [IntPtr]$visualHandle = Assert-NativeControl $visual "Button" $Code
    [IntPtr]$optimizationHandle = Assert-NativeControl $bound.controls.optimization "ComboBox" $Code
    $visualStyle = [MetafxMt5VisibleNative]::GetWindowLong($visualHandle, [MetafxMt5VisibleNative]::GWL_STYLE)
    if ([MetafxMt5VisibleNative]::GetDlgCtrlID($visualHandle) -ne 10490 -or
        ($visualStyle -band 15) -ne 3 -or
        [MetafxMt5VisibleNative]::GetParent($visualHandle) -ne [MetafxMt5VisibleNative]::GetParent($optimizationHandle)) {
        Fail $Code
    }
    return [ordered]@{ root = $bound.root; controls = $bound.controls; visual = $visual }
}

function Get-MinimalBoundTesterControlSet(
    [object]$Request,
    [IntPtr]$ExpectedRootHandle = [IntPtr]::Zero,
    [bool]$AllowTesterPaneReveal = $true
) {
    $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    $ids = $Request.requiredAutomationIds
    if ($AllowTesterPaneReveal) {
        Ensure-TesterPaneVisible $Request $root
        Ensure-TesterSingleModeReady $Request $root
        $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    } elseif ($null -eq (Find-ControlByIdPresent $root ([string]$ids.testerPane))) {
        Fail "mt5_tester_controls_not_verified"
    }
    $testerPane = Get-ControlByIdPresent $root ([string]$ids.testerPane) "mt5_tester_controls_not_verified"
    $start = Get-ControlByIdPresent $root ([string]$ids.start) "mt5_tester_controls_not_verified"
    $tabs = Get-TesterResultTabs $root $ids "mt5_tester_controls_not_verified"
    return [ordered]@{
        root = $root
        controls = [ordered]@{ testerPane = $testerPane; start = $start; tabs = $tabs }
    }
}

function Get-BoundStableTesterControlSet(
    [object]$Request,
    [IntPtr]$ExpectedRootHandle = [IntPtr]::Zero,
    [bool]$AllowTesterPaneReveal = $true
) {
    $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    $ids = $Request.requiredAutomationIds
    if ($AllowTesterPaneReveal) {
        Ensure-TesterPaneVisible $Request $root
        Ensure-TesterSingleModeReady $Request $root
        $root = Get-BoundTerminalRoot $Request $ExpectedRootHandle
    } elseif ($null -eq (Find-ControlByIdPresent $root ([string]$ids.testerPane))) {
        Fail "mt5_tester_controls_not_verified"
    }
    $controls = [ordered]@{}
    foreach ($property in $ids.PSObject.Properties) {
        # Visual mode is created only after optimization is Disabled.  Criterion
        # is created only after optimization is enabled.  Neither is a stable
        # prerequisite for normalizing the Settings workspace.
        if ([string]$property.Name -cin @("visualMode", "criterion")) { continue }
        $controls[$property.Name] = if ([string]$property.Name -ceq "tabs") {
            Get-TesterResultTabs $root $ids "mt5_tester_controls_not_verified"
        } else {
            Get-ControlByIdPresent $root ([string]$property.Value) "mt5_tester_controls_not_verified"
        }
    }
    return [ordered]@{ root = $root; controls = $controls }
}

function Select-BoundTesterComboMapped(
    [object]$Request,
    [string]$ControlName,
    [string[]]$UiNames,
    [string]$Code
) {
    if ($ControlName -cnotin @("timeframe", "modelling", "useDate", "optimization", "forward", "criterion") -or
        $UiNames.Count -lt 1) {
        Fail $Code
    }
    $dynamicCriterion = $ControlName -ceq "criterion"
    $before = if ($dynamicCriterion) {
        Get-BoundOptimizationCriterion $Request $Code
    } else {
        Get-BoundStableTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
    }
    if (-not $before.controls.Contains($ControlName)) { Fail $Code }
    if ((Read-TesterStartState $before.controls.start "mt5_tester_not_idle") -cne "Start") {
        Fail "mt5_tester_not_idle"
    }
    [void](Select-ComboMapped $before.controls[$ControlName] $UiNames $Code)

    # Every native CBN_SELCHANGE is asynchronous.  MT5 may replace the selected
    # ComboBox and arbitrary sibling controls before processing the notification.
    # Discard the entire pre-notification set and accept only a fresh signed-root
    # binding whose native/UIA value has converged to the requested mapping.
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        [System.Windows.Forms.Application]::DoEvents()
        try {
            $rebound = if ($dynamicCriterion) {
                Get-BoundOptimizationCriterion $Request $Code
            } else {
                Get-BoundStableTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
            }
            if (-not $rebound.controls.Contains($ControlName)) { Fail $Code }
            $value = Assert-ComboCommittedExact $rebound.controls[$ControlName] $UiNames $Code
            if ((Read-TesterStartState $rebound.controls.start "mt5_tester_not_idle") -cne "Start") {
                Fail "mt5_tester_not_idle"
            }
            return [ordered]@{ root = $rebound.root; controls = $rebound.controls; value = [string]$value }
        } catch {
            $reason = [string]$_.Exception.Message
            if ($reason -cnotin @($Code, "mt5_tester_controls_not_verified", "mt5_criterion_control_not_verified")) {
                throw
            }
        }
        Start-Sleep -Milliseconds 50
    } while ([DateTime]::UtcNow -lt $deadline)
    Fail $Code
}

function Read-TesterPaneResizeDiagnostic([object]$Control) {
    [IntPtr]$pane = [IntPtr]$Control.Current.NativeWindowHandle
    [IntPtr]$root = $script:TerminalRootHandle
    if ($pane -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($pane) -or
        -not [MetafxMt5VisibleNative]::IsWindow($root) -or
        (Get-NativeOwner $root) -ne $TerminalProcess.Id -or (Get-NativeOwner $pane) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetDlgCtrlID($pane) -ne 32846 -or
        [MetafxMt5VisibleNative]::GetAncestor($pane, [MetafxMt5VisibleNative]::GA_ROOT) -ne $root -or
        [MetafxMt5VisibleNative]::GetParent($pane) -ne $root) { Fail "mt5_tester_resize_diagnostic_binding_invalid" }
    $result = [ordered]@{ supportedPatterns = @(); transformAvailable = $false; canResize = $null; canMove = $null; canRotate = $null; hitTests = @() }
    try {
        $patterns = @($Control.GetSupportedPatterns())
        if ($patterns.Count -gt 32) { Fail "mt5_tester_resize_diagnostic_patterns_invalid" }
        $names = @($patterns | ForEach-Object { [string]$_.ProgrammaticName })
        if (@($names | Where-Object { $_.Length -gt 96 }).Count -gt 0) { Fail "mt5_tester_resize_diagnostic_patterns_invalid" }
        $result.supportedPatterns = $names
        $transform = $null
        if ($Control.TryGetCurrentPattern([System.Windows.Automation.TransformPattern]::Pattern, [ref]$transform)) {
            $result.transformAvailable = $true
            $result.canResize = [bool]$transform.Current.CanResize
            $result.canMove = [bool]$transform.Current.CanMove
            $result.canRotate = [bool]$transform.Current.CanRotate
        }
    } catch { $result["patternReasonCode"] = "mt5_tester_resize_diagnostic_patterns_unavailable" }
    $rect = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::GetWindowRect($pane, [ref]$rect)) { Fail "mt5_tester_resize_diagnostic_geometry_unavailable" }
    [int]$x = $rect.Left + [int](($rect.Right - $rect.Left) / 2)
    foreach ($target in @($pane, $root)) {
        foreach ($delta in @(-1, 0, 1)) {
            [int]$y = $rect.Top + $delta
            if ($x -lt -32768 -or $x -gt 32767 -or $y -lt -32768 -or $y -gt 32767) { continue }
            [int]$packed = ($y -shl 16) -bor ($x -band 0xffff)
            [IntPtr]$hit = [IntPtr]::Zero
            # WM_NCHITTEST observes the non-client edge only; no mouse/resize message is sent.
            $ok = [MetafxMt5VisibleNative]::SendMessageTimeout($target, 0x0084, [IntPtr]::Zero, [IntPtr]$packed,
                ([MetafxMt5VisibleNative]::SMTO_ABORTIFHUNG -bor [MetafxMt5VisibleNative]::SMTO_BLOCK -bor [MetafxMt5VisibleNative]::SMTO_ERRORONEXIT), 250, [ref]$hit)
            $result.hitTests += [ordered]@{ targetHandle = [long]$target.ToInt64(); x = $x; y = $y; available = $ok -ne [IntPtr]::Zero; hitCode = if ($ok -ne [IntPtr]::Zero) { [long]$hit.ToInt64() } else { $null } }
        }
    }
    if ((Get-NativeOwner $pane) -ne $TerminalProcess.Id -or (Get-NativeOwner $root) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetDlgCtrlID($pane) -ne 32846 -or
        [MetafxMt5VisibleNative]::GetAncestor($pane, [MetafxMt5VisibleNative]::GA_ROOT) -ne $root -or
        [MetafxMt5VisibleNative]::GetParent($pane) -ne $root) { Fail "mt5_tester_resize_diagnostic_binding_changed" }
    return $result
}

function Read-TesterDiagnosticControl([object]$Root, [string]$Id, [string]$Kind) {
    $condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::AutomationIdProperty, $Id)
    $matches = @(Get-All $Root $condition)
    if ($matches.Count -gt 8) { Fail "mt5_tester_diagnostic_controls_ambiguous" }
    $rows = @()
    foreach ($control in $matches) {
        [IntPtr]$handle = [IntPtr]$control.Current.NativeWindowHandle
        $exists = $handle -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::IsWindow($handle)
        $row = [ordered]@{
            handle = [long]$handle.ToInt64(); offscreen = [bool]$control.Current.IsOffscreen
            enabled = [bool]$control.Current.IsEnabled; exists = [bool]$exists
            nativeClass = $null; nativeId = $null; ownerMatches = $false; rootMatches = $false
            visible = $false; nativeEnabled = $false; selectedIndex = $null
            selectedValue = $null; dropdownOpen = $null; reasonCode = $null
        }
        if ($exists) {
            $row.nativeClass = Get-NativeClass $handle
            $row.nativeId = [int][MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
            $row.ownerMatches = (Get-NativeOwner $handle) -eq $TerminalProcess.Id
            $row.rootMatches = [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -eq $script:TerminalRootHandle
            $row.visible = [bool][MetafxMt5VisibleNative]::IsWindowVisible($handle)
            $row.nativeEnabled = [bool][MetafxMt5VisibleNative]::IsWindowEnabled($handle)
            if ($row.ownerMatches -and $row.rootMatches -and $Kind -cin @("testerPane", "start")) {
                try {
                    $rect = [MetafxMt5VisibleNative+RECT]::new()
                    if (-not [MetafxMt5VisibleNative]::GetWindowRect($handle, [ref]$rect)) { Fail "mt5_tester_diagnostic_geometry_unverified" }
                    $row["nativeRect"] = [ordered]@{ left = $rect.Left; top = $rect.Top; right = $rect.Right; bottom = $rect.Bottom }
                    $row["clientRect"] = Read-TesterDiagnosticClientRect $handle
                } catch { $row.reasonCode = "mt5_tester_diagnostic_geometry_unverified" }
                if ($Kind -ceq "testerPane" -and $row.nativeId -eq 32846) {
                    try { $row["resizeCapabilities"] = Read-TesterPaneResizeDiagnostic $control }
                    catch { $row["resizeReasonCode"] = "mt5_tester_resize_diagnostic_unavailable" }
                }
            }
            if ($row.ownerMatches -and $row.rootMatches -and $row.nativeId -eq [int]$Id -and
                $row.nativeClass -ceq "ComboBox" -and $row.visible -and $row.nativeEnabled -and
                $Kind -cin @("optimization", "expert", "modelling")) {
                try {
                    $row.selectedIndex = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETCURSEL) 0 0 "mt5_tester_diagnostic_combo_unreadable").ToInt32()
                    $dropped = (Invoke-NativeMessage $handle ([MetafxMt5VisibleNative]::CB_GETDROPPEDSTATE) 0 0 "mt5_tester_diagnostic_combo_unreadable").ToInt32()
                    if ($dropped -notin @(0, 1)) { Fail "mt5_tester_diagnostic_combo_unreadable" }
                    $row.dropdownOpen = $dropped -eq 1
                    # This diagnostic is local-only. Limit reads to the bound
                    # Tester combo's committed value, never arbitrary UI text.
                    $value = Read-NativeCombo $control "mt5_tester_diagnostic_combo_unreadable"
                    $limit = if ($Kind -ceq "expert") { 512 } else { 128 }
                    if ($value.Length -gt $limit) { Fail "mt5_tester_diagnostic_combo_unreadable" }
                    $row.selectedValue = [string]$value
                } catch { $row.reasonCode = "mt5_tester_diagnostic_combo_unreadable" }
            }
        }
        $rows += $row
    }
    return [ordered]@{ automationId = $Id; matchCount = $matches.Count; controls = @($rows) }
}

function Read-TesterDiagnosticCheckboxes([object]$Root, [string]$OptimizationId) {
    $optimization = Get-ControlByIdPresent $Root $OptimizationId "mt5_tester_diagnostic_parent_unverified"
    [IntPtr]$optimizationHandle = Assert-NativeControl $optimization "ComboBox" "mt5_tester_diagnostic_parent_unverified"
    [IntPtr]$parent = [MetafxMt5VisibleNative]::GetParent($optimizationHandle)
    if ($parent -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($parent) -or
        (Get-NativeOwner $parent) -ne $TerminalProcess.Id -or
        [MetafxMt5VisibleNative]::GetAncestor($parent, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle) {
        Fail "mt5_tester_diagnostic_parent_unverified"
    }
    $parentElement = [System.Windows.Automation.AutomationElement]::FromHandle($parent)
    $condition = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::CheckBox)
    $matches = @(Get-All $parentElement $condition)
    if ($matches.Count -gt 16) { Fail "mt5_tester_diagnostic_controls_ambiguous" }
    $rows = @()
    foreach ($control in $matches) {
        [IntPtr]$handle = [IntPtr]$control.Current.NativeWindowHandle
        $name = [string]$control.Current.Name
        $id = [string]$control.Current.AutomationId
        if ($name.Length -gt 128 -or $id.Length -gt 32 -or $handle -eq [IntPtr]::Zero -or
            -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
            (Get-NativeOwner $handle) -ne $TerminalProcess.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $script:TerminalRootHandle) {
            Fail "mt5_tester_diagnostic_checkbox_unverified"
        }
        $rows += [ordered]@{
            name = $name; automationId = $id; controlType = "CheckBox"
            nativeClass = Get-NativeClass $handle; nativeId = [int][MetafxMt5VisibleNative]::GetDlgCtrlID($handle)
            directSettingsChild = [MetafxMt5VisibleNative]::GetParent($handle) -eq $parent
            offscreen = [bool]$control.Current.IsOffscreen; enabled = [bool]$control.Current.IsEnabled
            visible = [bool][MetafxMt5VisibleNative]::IsWindowVisible($handle)
        }
    }
    return [ordered]@{ matchCount = $matches.Count; controls = @($rows) }
}

function Read-TesterDiagnosticClientRect([IntPtr]$Handle, [string]$Code = "mt5_tester_diagnostic_geometry_unverified") {
    $client = [MetafxMt5VisibleNative+RECT]::new()
    if (-not [MetafxMt5VisibleNative]::GetClientRect($Handle, [ref]$client)) { Fail $Code }
    $topLeft = [MetafxMt5VisibleNative+POINT]::new(); $topLeft.X = $client.Left; $topLeft.Y = $client.Top
    $bottomRight = [MetafxMt5VisibleNative+POINT]::new(); $bottomRight.X = $client.Right; $bottomRight.Y = $client.Bottom
    if (-not [MetafxMt5VisibleNative]::ClientToScreen($Handle, [ref]$topLeft) -or
        -not [MetafxMt5VisibleNative]::ClientToScreen($Handle, [ref]$bottomRight)) { Fail $Code }
    return [ordered]@{ left = $topLeft.X; top = $topLeft.Y; right = $bottomRight.X; bottom = $bottomRight.Y }
}

function Read-TesterDiagnosticGeometry([object]$Bound, [object]$Request, [bool]$RootOnly = $false) {
    [IntPtr]$rootHandle = [IntPtr]$Bound.root.Current.NativeWindowHandle
    if ($rootHandle -ne $script:TerminalRootHandle) { Fail "mt5_tester_diagnostic_geometry_unverified" }
    $result = [ordered]@{
        rootClient = Read-TesterDiagnosticClientRect $rootHandle
        controls = [ordered]@{}
        startAncestors = @()
    }
    $controls = [ordered]@{ root = $Bound.root }
    if (-not $RootOnly) {
        $controls["testerPane"] = $Bound.controls.testerPane
        $controls["start"] = $Bound.controls.start
        $controls["tabs"] = $Bound.controls.tabs
        $controls["optimization"] = Get-ControlByIdPresent $Bound.root ([string]$Request.requiredAutomationIds.optimization) "mt5_tester_diagnostic_geometry_unverified"
    }
    foreach ($name in $controls.Keys) {
        $control = $controls[$name]
        [IntPtr]$handle = [IntPtr]$control.Current.NativeWindowHandle
        $rect = [MetafxMt5VisibleNative+RECT]::new()
        if ($handle -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($handle) -or
            (Get-NativeOwner $handle) -ne $TerminalProcess.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($handle, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle -or
            -not [MetafxMt5VisibleNative]::GetWindowRect($handle, [ref]$rect)) { Fail "mt5_tester_diagnostic_geometry_unverified" }
        $uiaRect = $control.Current.BoundingRectangle
        $uiaAvailable = @($uiaRect.Left, $uiaRect.Top, $uiaRect.Right, $uiaRect.Bottom | Where-Object {
            [double]::IsNaN([double]$_) -or [double]::IsInfinity([double]$_)
        }).Count -eq 0
        $result.controls[$name] = [ordered]@{
            handle = [long]$handle.ToInt64()
            nativeRect = [ordered]@{ left = $rect.Left; top = $rect.Top; right = $rect.Right; bottom = $rect.Bottom }
            uiaRectAvailable = [bool]$uiaAvailable
            uiaRect = if ($uiaAvailable) { [ordered]@{ left = $uiaRect.Left; top = $uiaRect.Top; right = $uiaRect.Right; bottom = $uiaRect.Bottom } } else { $null }
            nativeVisible = [bool][MetafxMt5VisibleNative]::IsWindowVisible($handle)
            offscreen = [bool]$control.Current.IsOffscreen
        }
    }
    if ($RootOnly) { return $result }
    [IntPtr]$ancestor = [MetafxMt5VisibleNative]::GetParent([IntPtr]$Bound.controls.start.Current.NativeWindowHandle)
    for ($depth = 0; $depth -lt 16; $depth++) {
        if ($ancestor -eq [IntPtr]::Zero -or -not [MetafxMt5VisibleNative]::IsWindow($ancestor) -or
            (Get-NativeOwner $ancestor) -ne $TerminalProcess.Id -or
            [MetafxMt5VisibleNative]::GetAncestor($ancestor, [MetafxMt5VisibleNative]::GA_ROOT) -ne $rootHandle) {
            Fail "mt5_tester_diagnostic_geometry_unverified"
        }
        $result.startAncestors += [ordered]@{
            handle = [long]$ancestor.ToInt64(); nativeClass = Get-NativeClass $ancestor
            nativeId = [int][MetafxMt5VisibleNative]::GetDlgCtrlID($ancestor)
            clientRect = Read-TesterDiagnosticClientRect $ancestor
            nativeVisible = [bool][MetafxMt5VisibleNative]::IsWindowVisible($ancestor)
        }
        if ($ancestor -eq $rootHandle) { break }
        $ancestor = [MetafxMt5VisibleNative]::GetParent($ancestor)
    }
    if ($ancestor -ne $rootHandle) { Fail "mt5_tester_diagnostic_geometry_unverified" }
    return $result
}

function Read-TesterDiagnosticNavigation([object]$Root, [object]$Request) {
    [IntPtr]$rootHandle = [IntPtr]$Root.Current.NativeWindowHandle
    if ($rootHandle -ne $script:TerminalRootHandle -or (Get-NativeOwner $rootHandle) -ne $TerminalProcess.Id) {
        Fail "mt5_tester_diagnostic_navigation_root_unverified"
    }
    $menu = [ordered]@{ available = $false; reasonCode = $null }
    try {
        $snapshot = [MetafxMt5VisibleNative]::ReadTesterViewMenuExact([uint32]$TerminalProcess.Id, $rootHandle)
        $menu = [ordered]@{
            available = $true; rootHandle = [long]$rootHandle.ToInt64()
            mainMenuHandle = [long]$snapshot.MainMenu.ToInt64(); viewMenuHandle = [long]$snapshot.ViewMenu.ToInt64()
            viewLabel = [string]$snapshot.ViewItem.Text; viewPosition = [int]$snapshot.ViewItem.Position
            label = [string]$snapshot.TesterItem.Text; position = [int]$snapshot.TesterItem.Position
            commandId = [long]$snapshot.TesterItem.CommandId
            enabled = [bool]($snapshot.ViewItem.IsEnabled -and $snapshot.TesterItem.IsEnabled)
            checked = [bool](($snapshot.TesterItem.State -band 8) -ne 0)
            topItemCount = $snapshot.TopItems.Count; viewItemCount = $snapshot.ViewItems.Count
            topItems = @(for ($index=0; $index -lt [Math]::Min(24, $snapshot.TopItems.Length); $index++) {
                $entry = $snapshot.TopItems[$index]
                [ordered]@{ position = $entry.Item.Position; type = $entry.Type; label = $entry.Item.Text.Substring(0, [Math]::Min(128, $entry.Item.Text.Length)); labelTruncated = $entry.Item.Text.Length -gt 128; commandId = [long]$entry.Item.CommandId; enabled = $entry.Item.IsEnabled; checked = ($entry.Item.State -band 8) -ne 0; separator = $entry.Item.IsSeparator; hasSubmenu = $entry.Item.HasSubmenu }
            })
            viewItems = @(for ($index=0; $index -lt [Math]::Min(24, $snapshot.ViewItems.Length); $index++) {
                $entry = $snapshot.ViewItems[$index]
                [ordered]@{ position = $entry.Item.Position; type = $entry.Type; label = $entry.Item.Text.Substring(0, [Math]::Min(128, $entry.Item.Text.Length)); labelTruncated = $entry.Item.Text.Length -gt 128; commandId = [long]$entry.Item.CommandId; enabled = $entry.Item.IsEnabled; checked = ($entry.Item.State -band 8) -ne 0; separator = $entry.Item.IsSeparator; hasSubmenu = $entry.Item.HasSubmenu }
            })
        }
    } catch {
        $failure = $_.Exception
        while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
        $menu.reasonCode = if ($failure.Message -match "^mt5_[a-z0-9_]{3,90}$") { $failure.Message } else { "mt5_tester_menu_unreadable" }
    }
    [uint32]$rootPid = 0; [uint32]$foregroundPid = 0
    [uint32]$rootThread = [MetafxMt5VisibleNative]::GetWindowThreadProcessId($rootHandle, [ref]$rootPid)
    [IntPtr]$foreground = [MetafxMt5VisibleNative]::GetForegroundWindow()
    [uint32]$foregroundThread = if ($foreground -ne [IntPtr]::Zero) {
        [MetafxMt5VisibleNative]::GetWindowThreadProcessId($foreground, [ref]$foregroundPid)
    } else { 0 }
    if ($rootThread -eq 0 -or $rootPid -ne $TerminalProcess.Id) { Fail "mt5_tester_diagnostic_navigation_root_unverified" }
    $keyboard = [ordered]@{
        rootThreadId = $rootThread; rootLayout = [MetafxMt5VisibleNative]::GetKeyboardLayout($rootThread).ToInt64().ToString("X16")
        foregroundHandle = [long]$foreground.ToInt64(); foregroundProcessId = $foregroundPid; foregroundThreadId = $foregroundThread
        foregroundLayout = if ($foregroundThread -gt 0) { [MetafxMt5VisibleNative]::GetKeyboardLayout($foregroundThread).ToInt64().ToString("X16") } else { $null }
    }
    # Dynamic convenience HWND is diagnostic data only; it must never replace
    # the signed root or become a source of execution/admission authority.
    $TerminalProcess.Refresh()
    [IntPtr]$dynamic = $TerminalProcess.MainWindowHandle
    $dynamicInfo = [ordered]@{ handle = [long]$dynamic.ToInt64(); sameProcess = $false; available = $false }
    if ($dynamic -ne [IntPtr]::Zero -and [MetafxMt5VisibleNative]::IsWindow($dynamic) -and
        (Get-NativeOwner $dynamic) -eq $TerminalProcess.Id) {
        $dynamicInfo.sameProcess = $true
        $rect = [MetafxMt5VisibleNative+RECT]::new()
        if ([MetafxMt5VisibleNative]::GetWindowRect($dynamic, [ref]$rect)) {
            $dynamicInfo.available = $true
            $dynamicInfo["nativeClass"] = Get-NativeClass $dynamic
            $dynamicInfo["ownerHandle"] = [long][MetafxMt5VisibleNative]::GetWindow($dynamic, [MetafxMt5VisibleNative]::GW_OWNER).ToInt64()
            $dynamicInfo["rootHandle"] = [long][MetafxMt5VisibleNative]::GetAncestor($dynamic, [MetafxMt5VisibleNative]::GA_ROOT).ToInt64()
            $dynamicInfo["nativeRect"] = [ordered]@{ left = $rect.Left; top = $rect.Top; right = $rect.Right; bottom = $rect.Bottom }
        }
    }
    $windowInventory = [ordered]@{ available = $false }
    try {
        $inventory = [MetafxMt5VisibleNative]::ReadTesterWindowsDiagnostic([uint32]$TerminalProcess.Id, $rootHandle)
        $windowInventory = [ordered]@{ available = $true; truncated = $inventory.truncated
            topLevelWindows = @($inventory.topLevelWindows); testerControls = @($inventory.testerControls) }
    } catch {
        $failure = $_.Exception
        while ($null -ne $failure.InnerException) { $failure = $failure.InnerException }
        $windowInventory["reasonCode"] = if ($failure.Message -match "^mt5_[a-z0-9_]{3,90}$") { $failure.Message } else { "mt5_tester_window_diagnostic_unreadable" }
    }
    $null = Get-BoundTerminalRoot $Request $rootHandle
    return [ordered]@{ viewMenu = $menu; keyboard = $keyboard; processConvenienceWindow = $dynamicInfo; selectedProcessWindows = $windowInventory }
}

function Read-TesterDiagnostic([object]$Request) {
    if ([string]$Request.stageId -cne "backtest_recheck" -or
        [string]$Request.expectedSourceDigest -cnotmatch "^[a-f0-9]{64}$" -or
        [string]$Request.expectedBinaryDigest -cnotmatch "^[a-f0-9]{64}$") { Fail "mt5_tester_diagnostic_request_invalid" }
    $script:FailureCheckpoint = "tester_diagnostic_read"
    # False is essential: no reveal, mode normalization or tab selection.
    $root = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    $bound = $null
    try { $bound = Get-MinimalBoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false } catch {
        # Missing Tester controls are diagnostic data, never execution proof.
        # Root/process drift and all other failures remain fatal before capture.
        if ($_.Exception.Message -cne "mt5_tester_controls_not_verified") { throw }
    }
    if ($null -eq $bound) {
        $observation = [ordered]@{
            available = $false; unavailableReason = "mt5_tester_controls_not_verified"
            geometry = Read-TesterDiagnosticGeometry ([ordered]@{ root = $root }) $Request $true
            testerPane = Read-TesterDiagnosticControl $root ([string]$Request.requiredAutomationIds.testerPane) "testerPane"
            start = Read-TesterDiagnosticControl $root ([string]$Request.requiredAutomationIds.start) "start"
        }
    } else {
    [IntPtr]$startHandle = Assert-NativeControl $bound.controls.start "Button" "mt5_tester_diagnostic_start_unreadable"
    $startBefore = Read-TesterStartState $bound.controls.start "mt5_tester_diagnostic_start_unreadable" $startHandle
    [IntPtr]$tabsHandle = [IntPtr]$bound.controls.tabs.Current.NativeWindowHandle
    $names = @([MetafxMt5TabNative]::GetNames($tabsHandle))
    $selected = [int][MetafxMt5TabNative]::GetSelectedIndex($tabsHandle)
    if ($names.Count -gt 32 -or @($names | Where-Object { $_.Length -gt 128 }).Count -gt 0 -or
        $selected -lt -1 -or $selected -ge $names.Count) { Fail "mt5_tester_diagnostic_tabs_unreadable" }
    $observation = [ordered]@{
        available = $true
        testerPane = Read-TesterDiagnosticControl $bound.root ([string]$Request.requiredAutomationIds.testerPane) "testerPane"
        startState = [string]$startBefore; tabNames = @($names); selectedTabIndex = $selected
        selectedTab = if ($selected -ge 0) { [string]$names[$selected] } else { $null }
        optimization = Read-TesterDiagnosticControl $bound.root ([string]$Request.requiredAutomationIds.optimization) "optimization"
        visualMode = Read-TesterDiagnosticControl $bound.root ([string]$Request.requiredAutomationIds.visualMode) "visualMode"
        expert = Read-TesterDiagnosticControl $bound.root ([string]$Request.requiredAutomationIds.expert) "expert"
        modelling = Read-TesterDiagnosticControl $bound.root ([string]$Request.requiredAutomationIds.modelling) "modelling"
        settingsCheckboxes = Read-TesterDiagnosticCheckboxes $bound.root ([string]$Request.requiredAutomationIds.optimization)
        geometry = Read-TesterDiagnosticGeometry $bound $Request
    }
    }
    $observation["navigation"] = Read-TesterDiagnosticNavigation $root $Request
    $captureRequested = $Request.PSObject.Properties.Name -contains "diagnosticScreenshotPath"
    if ($captureRequested) {
        if ($Request.allowDiagnosticFocusChange -cne $true -or
            [System.IO.File]::Exists([string]$Request.diagnosticScreenshotPath) -or
            [System.IO.Path]::GetExtension([string]$Request.diagnosticScreenshotPath) -ine ".png") {
            Fail "mt5_tester_diagnostic_screenshot_request_invalid"
        }
        # Explicit diagnostic-only capture may focus this exact signed terminal.
        # No settings, tab selection, execution boundary or report is changed.
        Capture-BoundTerminalWindow $Request ([string]$Request.diagnosticScreenshotPath)
    }
    if ($null -eq $bound) {
        # A capture may focus/restore the exact terminal, so merely rebind its
        # identity. The unavailable observation never becomes a ready result.
        $null = Get-BoundTerminalRoot $Request ([IntPtr]$script:TerminalRootHandle)
    } else {
    $after = Get-MinimalBoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
    [IntPtr]$tabsAfter = [IntPtr]$after.controls.tabs.Current.NativeWindowHandle
    if ($tabsAfter -ne $tabsHandle -or
        (Read-TesterStartState $after.controls.start "mt5_tester_diagnostic_state_changed" $startHandle) -cne $startBefore -or
        [MetafxMt5TabNative]::GetSelectedIndex($tabsAfter) -ne $selected -or
        ((@([MetafxMt5TabNative]::GetNames($tabsAfter)) -join "`n") -cne ($names -join "`n"))) {
        Fail "mt5_tester_diagnostic_state_changed"
    }
    }
    $result = [ordered]@{
        schemaVersion = $ResultSchema; ok = $true; action = "diagnose_tester"; operationId = [string]$Request.operationId
        diagnosticOnly = $true; startInvoked = $false; testerVerified = $false
        sourceDigest = [string]$Request.expectedSourceDigest; compiledBinarySha256 = [string]$Request.expectedBinaryDigest
        terminalProcessId = [int]$TerminalProcess.Id; terminalWindowHandle = [long]$script:TerminalRootHandle.ToInt64()
        observation = $observation
    }
    if ($captureRequested) {
        $result["diagnosticScreenshotCaptured"] = $true
        $result["focusMayHaveChanged"] = $true
    }
    return $result
}

function Normalize-TesterSettingsTabExact(
    [object]$Request,
    [IntPtr]$ExpectedRootHandle = [IntPtr]::Zero,
    [bool]$AllowTesterPaneReveal = $true,
    [string]$Code = "mt5_tester_settings_tab_not_verified"
) {
    $minimal = Get-MinimalBoundTesterControlSet $Request $ExpectedRootHandle $AllowTesterPaneReveal
    if ((Read-TesterStartState $minimal.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $tabsHandle = [IntPtr]$minimal.controls.tabs.Current.NativeWindowHandle
    try {
        $names = @([MetafxMt5TabNative]::GetNames($tabsHandle))
        $selectedIndex = [MetafxMt5TabNative]::GetSelectedIndex($tabsHandle)
    } catch { Fail $Code }
    if ($selectedIndex -lt 0 -or $selectedIndex -ge $names.Count) { Fail $Code }
    if ([string]$names[$selectedIndex] -cne "Settings") {
        [void](Select-TesterTabExact $Request $minimal.root $Request.requiredAutomationIds "Settings" $Code)
    } else {
        [void](Assert-TesterTabSelectedExact $minimal.controls.tabs "Settings" $Code)
    }
    $bound = Get-BoundStableTesterControlSet $Request $ExpectedRootHandle $false
    if ((Read-TesterStartState $bound.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $hasVisualMode = $Request.requiredAutomationIds.PSObject.Properties.Name -ccontains "visualMode"
    if ($hasVisualMode) {
        # A previous optimization run can leave this combo on Fast/Complete.
        # In that state MT5 legitimately removes AutomationId 10490, so bind
        # only stable controls, normalize the backtest mode idempotently, then
        # reacquire and require the complete backtest control set.
        $disabledNames = @(Get-OptimizationUiNames "disabled")
        $optimizationBefore = Get-SelectedComboText $bound.controls.optimization $Code
        if (@($disabledNames | Where-Object {
            $optimizationBefore.Equals(([string]$_), [System.StringComparison]::OrdinalIgnoreCase)
        }).Count -ne 1) {
            $selection = Select-BoundTesterComboMapped $Request "optimization" $disabledNames $Code
            $bound = [ordered]@{ root = $selection.root; controls = $selection.controls }
        }
        $visualId = [string]$Request.requiredAutomationIds.visualMode
        $visual = $null
        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        do {
            $reboundRoot = Get-BoundTerminalRoot $Request $ExpectedRootHandle
            $visual = Find-ControlByIdPresent $reboundRoot $visualId
            if ($null -ne $visual) { break }
            Start-Sleep -Milliseconds 100
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($null -eq $visual) { Fail $Code }
        $bound = Get-BoundTesterControlSet $Request $ExpectedRootHandle $false
        [void](Assert-ComboCommittedExact $bound.controls.optimization $disabledNames $Code)
    }
    [void](Close-NativeComboDropDownExact $bound.controls.expert $Code)
    return $bound
}

function Get-ExpertCatalogDecision([string]$StartState, [int]$MatchCount, [bool]$RefreshAlreadyAttempted) {
    if ($StartState -cne "Start") { Fail "mt5_tester_not_idle" }
    if ($MatchCount -gt 1) { Fail "mt5_expert_catalog_ambiguous" }
    if ($MatchCount -eq 1) { return "select" }
    if ($MatchCount -ne 0) { Fail "mt5_expert_catalog_invalid" }
    if ($RefreshAlreadyAttempted) { Fail "mt5_expert_catalog_refresh_timeout" }
    return "refresh"
}

function Find-UiaRootTreeItemExact([System.Windows.Automation.AutomationElement]$Tree, [string]$Name, [string]$Code) {
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    try { $item = $walker.GetFirstChild($Tree) } catch { Fail $Code }
    $matches = @(); $visited = 0
    while ($null -ne $item -and $visited -lt 256) {
        try {
            if ($item.Current.ProcessId -eq $TerminalProcess.Id -and
                $item.Current.ControlType.Id -eq [System.Windows.Automation.ControlType]::TreeItem.Id -and
                [string]$item.Current.Name -ceq $Name -and
                $item.Current.IsEnabled -and -not $item.Current.IsOffscreen) {
                $matches += $item
            }
            $item = $walker.GetNextSibling($item)
        } catch { Fail $Code }
        $visited++
    }
    if ($null -ne $item) { Fail $Code }
    if ($matches.Count -gt 1) { Fail $Code }
    if ($matches.Count -eq 1) { return $matches[0] }
    return $null
}

function Get-ExactNativePopupMenuHost([int]$TimeoutMilliseconds, [string]$Code) {
    if ($TimeoutMilliseconds -lt 0 -or $TimeoutMilliseconds -gt 5000) { Fail $Code }
    # Only report-export callers receive finer failure categories. These do
    # not admit a different ControlType or deduplicate ambiguous UIA nodes.
    $reportDiagnostic = $Code -cmatch '^mt5_report_export_command_not_verified_popup_(host|rebind)_unverified$'
    $controlTypeMismatch = $false
    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $classCondition = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ClassNameProperty,
        "#32768"
    )
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMilliseconds)
    do {
        try {
            $candidates = @($desktop.FindAll([System.Windows.Automation.TreeScope]::Children, $classCondition))
            $matches = @($candidates | Where-Object {
                $_.Current.ProcessId -eq $TerminalProcess.Id -and
                $_.Current.ControlType.Id -eq [System.Windows.Automation.ControlType]::Pane.Id -and
                $_.Current.IsEnabled -and -not $_.Current.IsOffscreen -and
                [string]$_.Current.ClassName -ceq "#32768" -and
                [long]$_.Current.NativeWindowHandle -gt 0
            })
            if ($reportDiagnostic -and $matches.Count -eq 0 -and $candidates.Count -le 64) {
                $controlTypeMismatch = @($candidates | Where-Object {
                    $_.Current.ProcessId -eq $TerminalProcess.Id -and
                    $_.Current.ControlType.Id -ne [System.Windows.Automation.ControlType]::Pane.Id -and
                    $_.Current.IsEnabled -and -not $_.Current.IsOffscreen -and
                    [string]$_.Current.ClassName -ceq '#32768' -and
                    [long]$_.Current.NativeWindowHandle -gt 0
                }).Count -gt 0
            }
        } catch {
            if ($reportDiagnostic) { Fail "$($Code)_read_failed" }
            Fail $Code
        }
        if ($matches.Count -gt 1) {
            if ($reportDiagnostic) {
                try { $handles = @($matches | ForEach-Object { [long]$_.Current.NativeWindowHandle } | Select-Object -Unique) }
                catch { Fail "$($Code)_read_failed" }
                if ($handles.Count -eq 1) { Fail "$($Code)_duplicate_handle" }
                Fail "$($Code)_distinct_handles"
            }
            Fail $Code
        }
        if ($matches.Count -eq 1) { return $matches[0] }
        if ([DateTime]::UtcNow -ge $deadline) { break }
        Start-Sleep -Milliseconds 25
    } while ($true)
    if ($reportDiagnostic) {
        if ($controlTypeMismatch) { Fail "$($Code)_control_type_mismatch" }
        Fail "$($Code)_no_host"
    }
    Fail $Code
}

function Invoke-Mt5ExpertCatalogRefresh([object]$Request) {
    $bound = Get-BoundTesterControlSet $Request
    $root = $bound.root
    $controls = $bound.controls
    [IntPtr]$boundRootHandle = [IntPtr]$root.Current.NativeWindowHandle
    if ($boundRootHandle -eq [IntPtr]::Zero -or
        $boundRootHandle.ToInt64() -ne [long]$Request.expectedTerminalWindowHandle -or
        $boundRootHandle -ne $script:TerminalRootHandle) {
        Fail "mt5_terminal_window_changed"
    }
    if ((Read-TesterStartState $controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $navigator = Get-ControlByIdPresent $root "32845" "mt5_expert_catalog_navigator_not_verified"
    if ($navigator.Current.ProcessId -ne $TerminalProcess.Id -or [string]$navigator.Current.AutomationId -cne "32845") {
        Fail "mt5_expert_catalog_navigator_not_verified"
    }
    $tree = Get-ControlByIdPresent $navigator "10064" "mt5_expert_catalog_tree_not_verified"
    [IntPtr]$treeHandle = Assert-NativeControl $tree "SysTreeView32" "mt5_expert_catalog_tree_not_verified"
    $expertNode = Find-UiaRootTreeItemExact $tree "Expert Advisors" "mt5_expert_catalog_node_not_verified"
    Set-Foreground $TerminalProcess $root
    if ($null -ne $expertNode) {
        $selection = $null
        if (-not $expertNode.TryGetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern, [ref]$selection)) {
            Fail "mt5_expert_catalog_node_not_verified"
        }
        $selection.Select()
        Start-Sleep -Milliseconds 100
        if (-not $selection.Current.IsSelected) { Fail "mt5_expert_catalog_focus_failed" }
    } else {
        try {
            $selectedNode = [MetafxMt5VisibleNative]::SelectRootOrSingleRootChildExact(
                $treeHandle,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Expert Advisors"
            )
        } catch { Fail "mt5_expert_catalog_node_not_verified" }
        if ([string]$selectedNode -cne "Expert Advisors") { Fail "mt5_expert_catalog_node_not_verified" }
    }
    Start-Sleep -Milliseconds 100
    # Native enumeration is authoritative even when UIA exposed a TreeItem.
    # It proves uniqueness at the top level or directly beneath the sole
    # broker root, and that the actual TreeView caret—not merely a
    # provider-side selection object—names the exact catalogue node.
    try {
        $selectedReadback = [MetafxMt5VisibleNative]::ReadSelectedRootOrSingleRootChildExact(
            $treeHandle,
            [uint32]$TerminalProcess.Id,
            $boundRootHandle,
            "Expert Advisors"
        )
    } catch { Fail "mt5_expert_catalog_focus_failed" }
    if ([string]$selectedReadback -cne "Expert Advisors") { Fail "mt5_expert_catalog_focus_failed" }
    try {
        [MetafxMt5VisibleNative]::FocusTreeExact(
            $treeHandle,
            [uint32]$TerminalProcess.Id,
            $boundRootHandle
        )
        [MetafxMt5VisibleNative]::AssertTreeFocusExact(
            $treeHandle,
            [uint32]$TerminalProcess.Id,
            $boundRootHandle
        )
    } catch { Fail "mt5_expert_catalog_focus_failed" }
    try {
            [MetafxMt5VisibleNative]::AssertSelectedTreeContextExact(
                $treeHandle,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Expert Advisors"
            )
    } catch { Fail "mt5_expert_catalog_focus_failed" }
        [System.Windows.Forms.SendKeys]::SendWait("+{F10}")
        $popup = Get-ExactNativePopupMenuHost 3000 "mt5_expert_catalog_refresh_command_not_verified"
        [IntPtr]$popupHandle = [IntPtr][long]$popup.Current.NativeWindowHandle
        try {
            $popupToken = [MetafxMt5VisibleNative]::CapturePopupMenuTokenExact(
                $popupHandle,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle
            )
            $nativeCommand = [MetafxMt5VisibleNative]::AssertPopupMenuCommandFromTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Refresh",
                [uint32]33416
            )
        } catch { Fail "mt5_expert_catalog_refresh_command_not_verified" }
        if ([int]$nativeCommand.Position -lt 0 -or [long]$nativeCommand.CommandId -ne 33416 -or
            [string]$nativeCommand.Text -cne "Refresh" -or -not [bool]$nativeCommand.IsEnabled -or
            [bool]$nativeCommand.IsSeparator -or [bool]$nativeCommand.HasSubmenu) {
            Fail "mt5_expert_catalog_refresh_command_not_verified"
        }
        # Commit the at-most-once boundary before invoking Refresh.  A crash or
        # ambiguous failure after this point can only poll/select the refreshed
        # catalogue; it can never dispatch a second Refresh for this operation.
        $beforeBoundary = Get-BoundTesterControlSet $Request $boundRootHandle $false
        if ((Read-TesterStartState $beforeBoundary.controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        $boundarySha256 = Write-ExpertCatalogRefreshBoundary $Request
        # This is the final state read immediately before the sole Refresh
        # invocation.  A concurrent tester run turns Start into Stop and leaves
        # the durable boundary in place, forcing every retry to fail closed.
        try {
            $selectedImmediatelyBefore = [MetafxMt5VisibleNative]::ReadSelectedRootOrSingleRootChildExact(
                $treeHandle,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Expert Advisors"
            )
        } catch { Fail "mt5_expert_catalog_refresh_command_not_verified" }
        if ([string]$selectedImmediatelyBefore -cne "Expert Advisors") { Fail "mt5_expert_catalog_refresh_command_not_verified" }
        $popupImmediatelyBefore = Get-ExactNativePopupMenuHost 0 "mt5_expert_catalog_refresh_command_not_verified"
        [IntPtr]$popupImmediatelyBeforeHandle = [IntPtr][long]$popupImmediatelyBefore.Current.NativeWindowHandle
        if ($popupImmediatelyBeforeHandle -ne $popupHandle) { Fail "mt5_expert_catalog_refresh_command_not_verified" }
        try {
            [void][MetafxMt5VisibleNative]::AssertPopupMenuTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle
            )
            $nativeCommandImmediatelyBefore = [MetafxMt5VisibleNative]::AssertPopupMenuCommandFromTokenExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Refresh",
                [uint32]33416
            )
        } catch { Fail "mt5_expert_catalog_refresh_command_not_verified" }
        if ([int]$nativeCommandImmediatelyBefore.Position -ne [int]$nativeCommand.Position) {
            Fail "mt5_expert_catalog_refresh_command_not_verified"
        }
        $beforeInvoke = Get-BoundTesterControlSet $Request $boundRootHandle $false
        $idleImmediatelyBeforeRefresh = Read-TesterStartState $beforeInvoke.controls.start "mt5_tester_not_idle"
        if ($idleImmediatelyBeforeRefresh -cne "Start") { Fail "mt5_tester_not_idle" }
        try {
            [void][MetafxMt5VisibleNative]::InvokePopupMenuCommandExact(
                $popupToken,
                [uint32]$TerminalProcess.Id,
                $boundRootHandle,
                "Refresh",
                [uint32]33416
            )
        } catch { Fail "mt5_expert_catalog_refresh_dispatch_ambiguous" }
        $closeDeadline = [DateTime]::UtcNow.AddSeconds(2)
        while ([MetafxMt5VisibleNative]::IsWindow($popupHandle) -and
               [MetafxMt5VisibleNative]::IsWindowVisible($popupHandle) -and
               [DateTime]::UtcNow -lt $closeDeadline) {
            Start-Sleep -Milliseconds 25
        }
        if ([MetafxMt5VisibleNative]::IsWindow($popupHandle) -and
            [MetafxMt5VisibleNative]::IsWindowVisible($popupHandle)) {
            Fail "mt5_expert_catalog_refresh_dispatch_ambiguous"
        }
    # No global Escape cleanup is emitted.  If dispatch is not proven, the
    # exact popup is deliberately left visible rather than risking an
    # unrelated window consuming a global key after focus or HWND theft.
    return [ordered]@{
        boundarySha256 = [string]$boundarySha256
        idleImmediatelyBeforeRefresh = [string]$idleImmediatelyBeforeRefresh
    }
}

function Select-ExpertWithCatalogRefresh([object]$Request) {
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $expected = ([string]$Request.expertUiPath).Trim().Replace("/", "\")
    if ([string]::IsNullOrWhiteSpace($expected) -or $expected.Length -gt 512) { Fail "mt5_expert_readback_mismatch" }
    $exactEx5Value = if ($expected.EndsWith(".ex5", [System.StringComparison]::OrdinalIgnoreCase)) { $expected } else { "$expected.ex5" }
    $expectedNames = @($expected, $exactEx5Value | Select-Object -Unique)
    $initial = Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $true "mt5_tester_settings_tab_not_verified"
    $activeRoot = $initial.root
    $activeControls = $initial.controls
    $algoBefore = Get-AlgoTradingState $activeRoot
    $idleBefore = Read-TesterStartState $activeControls.start "mt5_tester_not_idle"
    if ($idleBefore -cne "Start") { Fail "mt5_tester_not_idle" }
    $boundaryPath = Get-ExpertCatalogRefreshBoundaryPath $Request
    $recoveredAfterBoundary = [System.IO.File]::Exists($boundaryPath)
    $refreshAttempted = $recoveredAfterBoundary
    $refreshBoundarySha256 = if ($recoveredAfterBoundary) { Assert-ExpertCatalogRefreshBoundary $Request } else { $null }
    $idleImmediatelyBeforeRefresh = $null
    $injectionAttempted = $false
    $selectedByInjection = $null
    $beforeMatches = @(Get-NativeComboExactMatches $activeControls.expert $expectedNames "mt5_expert_catalog_read_failed")
    if ($beforeMatches.Count -gt 1) { Fail "mt5_expert_catalog_ambiguous" }
    if ($beforeMatches.Count -eq 0 -and -not $refreshAttempted) {
        $refreshResult = Invoke-Mt5ExpertCatalogRefresh $Request
        $refreshBoundarySha256 = [string]$refreshResult.boundarySha256
        $idleImmediatelyBeforeRefresh = [string]$refreshResult.idleImmediatelyBeforeRefresh
        $refreshAttempted = $true
    }
    # Refresh can recreate the tester widgets.  Never reuse a pre-refresh
    # AutomationElement/native handle.  Build 6230 then exposes only its MRU
    # item even while dropped, so a verified Refresh boundary authorizes one
    # exact, rollback-capable insertion of the signed .ex5 path.
    $current = Get-BoundTesterControlSet $Request
    $activeRoot = $current.root
    $activeControls = $current.controls
    if ((Read-TesterStartState $activeControls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    $afterMatches = @(Get-NativeComboExactMatches $activeControls.expert $expectedNames "mt5_expert_catalog_read_failed")
    if ($afterMatches.Count -gt 1) { Fail "mt5_expert_catalog_ambiguous" }
    if ($afterMatches.Count -eq 0 -and $refreshAttempted) {
        if ($injectionAttempted) { Fail "mt5_expert_catalog_injection_duplicate_attempt" }
        $injectionAttempted = $true
        # Revalidate the durable refresh evidence immediately before the only
        # insertion attempt.  Recovery therefore never dispatches Refresh or
        # performs a second insertion once the exact entry exists.
        [void](Assert-ExpertCatalogRefreshBoundary $Request)
        $injected = Inject-NativeComboExpertExact $Request $exactEx5Value $expectedNames
        $selectedByInjection = [string]$injected.selected
        $activeRoot = $injected.root
        $activeControls = $injected.controls
        $afterMatches = @(Get-NativeComboExactMatches $activeControls.expert $expectedNames "mt5_expert_catalog_read_failed")
        if ($afterMatches.Count -ne 1) { Fail "mt5_expert_catalog_injection_readback_failed" }
    }
    $final = Get-BoundTesterControlSet $Request
    $activeRoot = $final.root
    $activeControls = $final.controls
    $afterMatches = @(Get-NativeComboExactMatches $activeControls.expert $expectedNames "mt5_expert_catalog_read_failed")
    $idleAfter = Read-TesterStartState $activeControls.start "mt5_tester_not_idle"
    $decision = Get-ExpertCatalogDecision $idleAfter $afterMatches.Count $refreshAttempted
    if ($decision -cne "select") { Fail "mt5_expert_readback_mismatch" }
    $selected = if ($null -ne $selectedByInjection) {
        $nativeSelected = (Read-NativeCombo $activeControls.expert "mt5_expert_readback_mismatch").Trim().Replace("/", "\")
        $uiaSelected = (Read-UiaComboSelectionExact $activeControls.expert $expectedNames "mt5_expert_readback_mismatch").Trim().Replace("/", "\")
        if (-not $nativeSelected.Equals($selectedByInjection, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not $uiaSelected.Equals($selectedByInjection, [System.StringComparison]::OrdinalIgnoreCase)) {
            Fail "mt5_expert_readback_mismatch"
        }
        $nativeSelected
    } else {
        $submitted = Select-NativeComboExact $activeControls.expert $expectedNames "mt5_expert_readback_mismatch"
        $reboundSelection = $null
        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        do {
            [System.Windows.Forms.Application]::DoEvents()
            try {
                $candidate = Get-BoundTesterControlSet $Request ([IntPtr]$script:TerminalRootHandle) $false
                $nativeSelected = (Assert-ComboCommittedExact $candidate.controls.expert $expectedNames "mt5_expert_readback_mismatch").Trim().Replace("/", "\")
                $uiaSelected = (Read-UiaComboSelectionExact $candidate.controls.expert $expectedNames "mt5_expert_readback_mismatch").Trim().Replace("/", "\")
                if (-not $nativeSelected.Equals(([string]$submitted).Trim().Replace("/", "\"), [System.StringComparison]::OrdinalIgnoreCase) -or
                    -not $uiaSelected.Equals($nativeSelected, [System.StringComparison]::OrdinalIgnoreCase)) {
                    Fail "mt5_expert_readback_mismatch"
                }
                $reboundSelection = $candidate
                break
            } catch {
                $reason = [string]$_.Exception.Message
                if ($reason -cnotin @("mt5_expert_readback_mismatch", "mt5_tester_controls_not_verified")) { throw }
            }
            Start-Sleep -Milliseconds 50
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($null -eq $reboundSelection) { Fail "mt5_expert_readback_mismatch" }
        $activeRoot = $reboundSelection.root
        $activeControls = $reboundSelection.controls
        $nativeSelected
    }
    $uiaSelectedFinal = (Read-UiaComboSelectionExact $activeControls.expert $expectedNames "mt5_expert_readback_mismatch").Trim().Replace("/", "\")
    if (-not $uiaSelectedFinal.Equals(([string]$selected).Trim().Replace("/", "\"), [System.StringComparison]::OrdinalIgnoreCase)) { Fail "mt5_expert_readback_mismatch" }
    $idleAfter = Read-TesterStartState $activeControls.start "mt5_tester_not_idle"
    if ($idleAfter -cne "Start") { Fail "mt5_tester_not_idle" }
    $algoAfter = Get-AlgoTradingState $activeRoot
    if ($algoAfter -ne $algoBefore) { Fail "mt5_algo_trading_state_changed" }
    $timer.Stop()
    return [ordered]@{
        selected = [string]$selected
        root = $activeRoot
        controls = $activeControls
        evidence = [ordered]@{
            schemaVersion = "ea-factory-mt5-expert-catalog-refresh-v2"
            attempted = $refreshAttempted
            recoveredAfterBoundary = $recoveredAfterBoundary
            commandCount = if ($refreshAttempted) { 1 } else { 0 }
            commandName = if ($refreshAttempted) { "Refresh" } else { $null }
            boundarySha256 = if ($refreshAttempted) { [string]$refreshBoundarySha256 } else { $null }
            navigatorPaneAutomationId = "32845"
            navigatorTreeAutomationId = "10064"
            expertNodeName = "Expert Advisors"
            refreshMenuAutomationId = $null
            refreshMenuName = "Refresh"
            refreshMenuProvider = "native_hmenu"
            refreshMenuWindowClass = "#32768"
            refreshMenuNativeCommandId = 33416
            refreshMenuDispatchMethod = "targeted_menu_keyboard"
            matchCountBefore = [int]$beforeMatches.Count
            matchCountAfter = [int]$afterMatches.Count
            selectedExpertReadback = [string]$selected
            idleStateBefore = [string]$idleBefore
            idleStateImmediatelyBeforeRefresh = if ($null -ne $idleImmediatelyBeforeRefresh) { [string]$idleImmediatelyBeforeRefresh } else { $null }
            idleStateAfter = [string]$idleAfter
            algoTradingStateBefore = [bool]$algoBefore
            algoTradingStateAfter = [bool]$algoAfter
            terminalProcessId = [int]$TerminalProcess.Id
            terminalWindowHandle = [long]$script:TerminalRootHandle.ToInt64()
            elapsedMs = [int][Math]::Min([int]::MaxValue, [Math]::Max(0, $timer.ElapsedMilliseconds))
            verified = $true
        }
    }
}

function Configure-Tester([object]$Request, [bool]$Optimize) {
    # Catalogue refresh may recreate tester widgets.  The selector returns the
    # terminal root and complete control set reacquired after the final poll;
    # never continue configuration with pre-refresh AutomationElements.
    $expertSelection = Select-ExpertWithCatalogRefresh $Request
    $activeRoot = $expertSelection.root
    $controls = $expertSelection.controls
    $requestedSymbolNames = @()
    if ([string]$Request.testerSettings.symbolPolicy -ceq "explicit") {
        $requestedSymbolNames = @(([string]$Request.testerSettings.symbol).Trim())
        if ($requestedSymbolNames.Count -ne 1 -or [string]::IsNullOrWhiteSpace($requestedSymbolNames[0])) { Fail "mt5_symbol_readback_mismatch" }
        # MT5's editable symbol ComboBox can expose transient UIA text without
        # committing the native list selection.  Select exactly one existing
        # item, notify its exact parent, close its popup, then reacquire every
        # Settings control before accepting native/UIA readback.
        [void](Select-SymbolComboExact $controls.symbol $requestedSymbolNames "mt5_symbol_readback_mismatch")
        $symbolBound = Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $false "mt5_symbol_readback_mismatch"
        $activeRoot = $symbolBound.root
        $controls = $symbolBound.controls
        [void](Assert-SymbolComboCommittedExact $controls.symbol $requestedSymbolNames "mt5_symbol_readback_mismatch")
    }
    $periodSelection = Select-BoundTesterComboMapped $Request "timeframe" @(Get-PeriodUiNames ([string]$Request.testerSettings.period)) "mt5_timeframe_readback_mismatch"
    $activeRoot = $periodSelection.root
    $controls = $periodSelection.controls
    $periodLabel = [string]$periodSelection.value
    $modelSelection = Select-BoundTesterComboMapped $Request "modelling" @(Get-ModelUiNames ([string]$Request.testerSettings.model)) "mt5_model_readback_mismatch"
    $activeRoot = $modelSelection.root
    $controls = $modelSelection.controls
    $modelLabel = [string]$modelSelection.value
    $dateSelection = if ([bool]$Request.testerSettings.useDate) {
        Select-BoundTesterComboMapped $Request "useDate" @("Custom period") "mt5_use_date_readback_mismatch"
    } else {
        Select-BoundTesterComboMapped $Request "useDate" @("Entire history") "mt5_use_date_readback_mismatch"
    }
    $activeRoot = $dateSelection.root
    $controls = $dateSelection.controls
    $datePolicyLabel = [string]$dateSelection.value
    if ([bool]$Request.testerSettings.useDate) {
        $nativeFromDate = Get-NativeTesterDateText ([string]$Request.testerSettings.fromDate) "mt5_from_date_readback_mismatch"
        $nativeToDate = Get-NativeTesterDateText ([string]$Request.testerSettings.toDate) "mt5_to_date_readback_mismatch"
        Set-ValueExact $controls.fromDate $nativeFromDate "mt5_from_date_readback_mismatch"
        Set-ValueExact $controls.toDate $nativeToDate "mt5_to_date_readback_mismatch"
    }
    $optimizationToken = if ($Optimize) { [string]$Request.optimizationIntent.mode } else { "disabled" }
    $optimizationSelection = Select-BoundTesterComboMapped $Request "optimization" @(Get-OptimizationUiNames $optimizationToken) "mt5_optimization_mode_readback_mismatch"
    $activeRoot = $optimizationSelection.root
    $controls = $optimizationSelection.controls
    $optimizationLabel = [string]$optimizationSelection.value
    $forwardSelection = Select-BoundTesterComboMapped $Request "forward" @("No", "Disabled") "mt5_forward_mode_readback_mismatch"
    $activeRoot = $forwardSelection.root
    $controls = $forwardSelection.controls
    $forwardLabel = [string]$forwardSelection.value
    $criterionLabel = $null
    if ($Optimize) {
        # The criterion ComboBox is created only after optimization is enabled.
        # Enabling it can also recreate sibling widgets, so first reacquire the
        # stable base set, then bind the optimization-only control.
        $criterionSelection = Select-BoundTesterComboMapped $Request "criterion" @(Get-CriterionUiNames ([string]$Request.optimizationIntent.criterion)) "mt5_criterion_readback_mismatch"
        $activeRoot = $criterionSelection.root
        $controls = $criterionSelection.controls
        $criterionLabel = [string]$criterionSelection.value
    }
    $inputEvidence = $null; $baselineEvidence = $null; $optimizationEvidence = $null
    if ($Optimize) {
        $baselineEvidence = Load-And-VerifyInputSet $Request $activeRoot $Request.optimizationIntent.baselinePresetRef ([string]$Request.baselineInputReadbackSetPath) $null "mt5_optimization_baseline"
        $optimizationEvidence = Load-And-VerifyInputSet $Request $activeRoot $Request.optimizationIntent.setRef ([string]$Request.inputReadbackSetPath) $null "mt5_optimization_inputs"
    } else {
        $inputEvidence = Load-And-VerifyInputSet $Request $activeRoot $Request.inputPresetRef ([string]$Request.inputPresetReadbackSetPath) ([string]$Request.inputPresetScreenshotPath) "mt5_tester_input_preset"
    }
    # Input Load/Save switches the tester to Inputs and shell dialogs can
    # recreate AutomationElements.  Restore Settings and return only freshly
    # rebound controls to the Start path.
    $finalBound = Restore-TesterSettingsTabExact $Request "mt5_tester_settings_restore_failed"
    $activeRoot = $finalBound.root
    $controls = $finalBound.controls
    if ($Optimize) {
        # Loading an Inputs set can recreate Settings widgets.  Rebind and
        # re-read the optimization-only criterion before returning to Start.
        $criterionBound = Get-BoundOptimizationCriterion $Request
        $activeRoot = $criterionBound.root
        $controls = $criterionBound.controls
        $criterionLabel = Get-SelectedComboText $controls["criterion"] "mt5_criterion_readback_mismatch"
        if ($criterionLabel -notin @(Get-CriterionUiNames ([string]$Request.optimizationIntent.criterion))) { Fail "mt5_criterion_readback_mismatch" }
    }
    else {
        # Loading a SET can recreate the Settings controls. Rebind the exact
        # native visual-mode checkbox and prove that the requested state was
        # preserved before returning the Start control.
        $visualBound = Get-BoundVisualModeControl $Request
        $activeRoot = $visualBound.root
        $controls = $visualBound.controls
        Set-ToggleExact $visualBound.visual $true "mt5_visual_mode_readback_mismatch"
        if (-not (Get-Toggle $visualBound.visual "mt5_visual_mode_readback_mismatch")) { Fail "mt5_visual_mode_readback_mismatch" }
    }
    $expectedExpert = ([string]$Request.expertUiPath).Trim().Replace("/", "\")
    $expectedExperts = @($expectedExpert, "$expectedExpert.ex5" | Select-Object -Unique)
    [void](Assert-ComboCommittedExact $controls.expert $expectedExperts "mt5_expert_readback_mismatch")
    $symbolReadback = if ($requestedSymbolNames.Count -eq 1) {
        Assert-SymbolComboCommittedExact $controls.symbol $requestedSymbolNames "mt5_symbol_readback_mismatch"
    } else {
        Get-Value $controls.symbol
    }
    if ((Read-TesterStartState $controls.start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
    return [ordered]@{
        controls = $controls
        expert = [string]$expertSelection.selected
        expertCatalogRefresh = $expertSelection.evidence
        symbol = [string]$symbolReadback
        timeframe = $periodLabel
        modelLabel = $modelLabel
        optimizationLabel = $optimizationLabel
        forwardLabel = $forwardLabel
        criterionLabel = $criterionLabel
        deposit = Get-PositiveDecimal $controls.deposit "mt5_deposit_readback_mismatch"
        useDate = ($datePolicyLabel -ceq "Custom period")
        fromDate = if ([bool]$Request.testerSettings.useDate) { ([string]$Request.testerSettings.fromDate).Trim() } else { $null }
        toDate = if ([bool]$Request.testerSettings.useDate) { ([string]$Request.testerSettings.toDate).Trim() } else { $null }
        inputEvidence = $inputEvidence; baselineEvidence = $baselineEvidence; optimizationEvidence = $optimizationEvidence
    }
}

function Read-TesterStartState([System.Windows.Automation.AutomationElement]$Start, [string]$Code, [IntPtr]$ExpectedHandle = [IntPtr]::Zero) {
    [IntPtr]$uiaHandle = [IntPtr]$Start.Current.NativeWindowHandle
    if ($ExpectedHandle -ne [IntPtr]::Zero -and $uiaHandle -ne $ExpectedHandle) { Fail $Code }
    [IntPtr]$handle = Assert-NativeControl $Start "Button" $Code
    if (($ExpectedHandle -ne [IntPtr]::Zero -and $handle -ne $ExpectedHandle) -or $handle -ne $uiaHandle) { Fail $Code }
    try { $native = [MetafxMt5VisibleNative]::GetWindowTextExact($handle) }
    catch { Fail $Code }
    $uia = [string]$Start.Current.Name
    [IntPtr]$uiaHandleAfterRead = [IntPtr]$Start.Current.NativeWindowHandle
    $nativeAllowed = [string]::Equals($native, "Start", [System.StringComparison]::Ordinal) -or
        [string]::Equals($native, "Stop", [System.StringComparison]::Ordinal)
    $uiaAllowed = [string]::Equals($uia, "Start", [System.StringComparison]::Ordinal) -or
        [string]::Equals($uia, "Stop", [System.StringComparison]::Ordinal)
    if (-not $nativeAllowed -or -not $uiaAllowed -or
        -not [string]::Equals($native, $uia, [System.StringComparison]::Ordinal) -or
        $uiaHandleAfterRead -ne $handle) { Fail $Code }
    return $native
}

function Wait-TesterStartStateStable(
    [System.Windows.Automation.AutomationElement]$Start,
    [string]$Code,
    [IntPtr]$ExpectedHandle,
    [string]$ExpectedState = "",
    [int]$TimeoutMilliseconds = 1500
) {
    $expectedAny = [string]::IsNullOrEmpty($ExpectedState)
    if ($TimeoutMilliseconds -lt 50 -or $TimeoutMilliseconds -gt 5000 -or
        (-not $expectedAny -and
        -not [string]::Equals($ExpectedState, "Start", [System.StringComparison]::Ordinal) -and
        -not [string]::Equals($ExpectedState, "Stop", [System.StringComparison]::Ordinal))) {
        Fail $Code
    }
    # MT5 updates the native button text and the UI Automation provider on
    # separate message turns.  Immediately after a very fast optimization the
    # native HWND can already be back at Start while UIA still reports Stop (or
    # vice versa) for a few hundred milliseconds.  Keep the original, already
    # authenticated HWND binding and wait only for both providers to converge;
    # this helper never rebinds the control and can never dispatch Start.
    $deadline = [DateTime]::UtcNow.AddMilliseconds($TimeoutMilliseconds)
    do {
        try {
            $state = Read-TesterStartState $Start $Code $ExpectedHandle
            if ($expectedAny -or
                [string]::Equals($state, $ExpectedState, [System.StringComparison]::Ordinal)) {
                return $state
            }
        } catch {
            if (-not [string]::Equals([string]$_.Exception.Message, $Code, [System.StringComparison]::Ordinal)) {
                throw
            }
        }
        [System.Windows.Forms.Application]::DoEvents()
        Start-Sleep -Milliseconds 25
    } while ([DateTime]::UtcNow -lt $deadline)
    Fail $Code
}

function New-TesterStartMonitor([System.Windows.Automation.AutomationElement]$Start, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Start "Button" $Code
    try { return [MetafxMt5StartEventMonitor]::new($handle) } catch { Fail $Code }
}

function Invoke-TesterStartOnce([System.Windows.Automation.AutomationElement]$Start, [object]$Monitor, [string]$Code) {
    [IntPtr]$handle = Assert-NativeControl $Start "Button" $Code
    if ($null -eq $Monitor -or [bool]$Monitor.Armed) { Fail $Code }
    # This is the final instruction before the sole BM_CLICK.  A competing
    # actor that turned Start into Stop after the durable boundary is therefore
    # detected instead of accidentally cancelling the active tester run.
    $beforeClick = Read-TesterStartState $Start $Code $handle
    if (-not [string]::Equals($beforeClick, "Start", [System.StringComparison]::Ordinal)) { Fail $Code }
    try {
        # Recheck owner/root/control-id/class/enabled/text inside one native
        # helper immediately before the sole queued BM_CLICK.  Do not perform
        # any fallible UI read after posting: a false negative there could
        # strand a consumed Start behind the already-durable boundary.
        $Monitor.PostStartOnce(
            [uint32]$TerminalProcess.Id,
            [IntPtr]$script:TerminalRootHandle,
            16790,
            "Start"
        )
    } catch { Fail $Code }
}

function Wait-TesterCompletion(
    [System.Windows.Automation.AutomationElement]$Start,
    [int]$TimeoutSeconds,
    [bool]$AlreadyStarted,
    [object]$Monitor,
    [object]$Request = $null,
    [bool]$Optimize = $false,
    [object]$Configured = $null
) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    [IntPtr]$expectedHandle = Assert-NativeControl $Start "Button" "mt5_tester_start_state_unverified"
    $initialName = Wait-TesterStartStateStable $Start "mt5_tester_start_state_unverified" $expectedHandle
    if ($AlreadyStarted -and -not [string]::Equals($initialName, "Stop", [System.StringComparison]::Ordinal)) {
        # The dispatch receipt proves the one-shot post was accepted, but a
        # fast run can already be idle before collection reconnects.  Return a
        # sentinel only; the caller must bind the exact configured identity and
        # pass Assert-TesterCleanCompletion before touching any result/report.
        return "idle_after_dispatch_clean_log_completion"
    }
    $sawStop = [string]::Equals($initialName, "Stop", [System.StringComparison]::Ordinal) -or
        ($null -ne $Monitor -and ([bool]$Monitor.SawStop -or [bool]$Monitor.Completed))
    $nextLogProbe = [DateTime]::UtcNow.AddMilliseconds(250)
    while ([DateTime]::UtcNow -lt $deadline) {
        # WinEvent messages are dispatched on the hook-owning thread.  Pumping
        # the queue captures even a very fast Start -> Stop -> Start transition
        # that could otherwise occur entirely between polling intervals.
        [System.Windows.Forms.Application]::DoEvents()
        if ($null -ne $Monitor -and [bool]$Monitor.Completed) {
            $eventState = Wait-TesterStartStateStable $Start "mt5_tester_start_state_unverified" $expectedHandle "Start"
            return "native_event_stop_then_start"
        }
        $name = Wait-TesterStartStateStable $Start "mt5_tester_start_state_unverified" $expectedHandle
        if ($null -ne $Monitor -and ([bool]$Monitor.SawStop -or [bool]$Monitor.Completed)) { $sawStop = $true }
        if ([string]::Equals($name, "Stop", [System.StringComparison]::Ordinal)) { $sawStop = $true }
        elseif ($sawStop -and [string]::Equals($name, "Start", [System.StringComparison]::Ordinal)) { return "polled_stop_then_start" }
        elseif (-not $AlreadyStarted -and
            $null -ne $Request -and $null -ne $Configured -and
            [string]::Equals($name, "Start", [System.StringComparison]::Ordinal) -and
            [DateTime]::UtcNow -ge $nextLogProbe) {
            # If Stop -> Start completed entirely between UI observations, the
            # existing exact post-boundary log pairing is the only acceptable
            # fallback.  Failed probes remain non-authoritative and never post
            # Start again.
            try {
                [void](Assert-TesterCleanCompletion $Request $Optimize $Configured)
                return "fresh_exact_log_completion_after_dispatch"
            } catch {
                if ([string]$_.Exception.Message -cne "mt5_tester_clean_completion_unverified") { throw }
            }
            $nextLogProbe = [DateTime]::UtcNow.AddMilliseconds(250)
        }
        Start-Sleep -Milliseconds 25
    }
    Fail "mt5_tester_completion_timeout"
}

function Get-SharedUnicodeLogText([string]$Path, [string]$Code) {
    $stream = $null
    $reader = $null
    try {
        $item = [System.IO.FileInfo]::new($Path)
        if (-not $item.Exists -or $item.Length -le 0 -or $item.Length -gt 67108864L -or
            (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { Fail $Code }
        $stream = [System.IO.File]::Open($item.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete))
        $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::Unicode, $true)
        return $reader.ReadToEnd()
    } catch { Fail $Code }
    finally {
        if ($null -ne $reader) { $reader.Dispose() }
        elseif ($null -ne $stream) { $stream.Dispose() }
    }
}

function Get-FreshTesterLogRecords([object]$Request, [DateTime]$BoundaryUtc, [string]$Code) {
    $dataPath = [System.IO.Path]::GetFullPath([string]$Request.dataPath)
    $terminalLogRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($dataPath, "Tester", "logs"))
    $terminalIdentity = [System.IO.Path]::GetFileName($dataPath.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar))
    $agentLogRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine(
        [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::ApplicationData),
        "MetaQuotes", "Tester", $terminalIdentity
    ))
    $candidatePaths = @()
    if ([System.IO.Directory]::Exists($terminalLogRoot)) {
        $candidatePaths += @([System.IO.Directory]::GetFiles($terminalLogRoot, "*.log", [System.IO.SearchOption]::TopDirectoryOnly))
    }
    if ([System.IO.Directory]::Exists($agentLogRoot)) {
        $candidatePaths += @([System.IO.Directory]::GetFiles($agentLogRoot, "*.log", [System.IO.SearchOption]::AllDirectories))
    }
    $records = @()
    foreach ($candidatePath in $candidatePaths) {
        $item = [System.IO.FileInfo]::new($candidatePath)
        if (-not $item.Exists -or $item.LastWriteTimeUtc -lt $BoundaryUtc) { continue }
        $dateToken = [System.IO.Path]::GetFileNameWithoutExtension($item.Name)
        if ($dateToken -cnotmatch '^[0-9]{8}$') { continue }
        $text = Get-SharedUnicodeLogText $item.FullName $Code
        $lineIndex = 0
        foreach ($line in ($text -split "`r?`n")) {
            $lineIndex++
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $fields = $line -split "`t", 5
            if ($fields.Count -ne 5 -or [string]$fields[2] -cnotmatch '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}$') { continue }
            try {
                $local = [DateTime]::ParseExact(
                    "$dateToken $([string]$fields[2])",
                    "yyyyMMdd HH:mm:ss.fff",
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [System.Globalization.DateTimeStyles]::AssumeLocal
                )
                $observedUtc = $local.ToUniversalTime()
            } catch { continue }
            if ($observedUtc -lt $BoundaryUtc) { continue }
            $records += [pscustomobject]@{
                ObservedUtc = $observedUtc
                Source = [string]$fields[3]
                Message = [string]$fields[4]
                RawLine = [string]$line
                Path = [string]$item.FullName
                LineIndex = [int]$lineIndex
            }
        }
    }
    return @($records | Sort-Object ObservedUtc, Path, LineIndex)
}

function Get-LogLineSha256([string]$Line) {
    $bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Line)
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try { return [System.BitConverter]::ToString($hasher.ComputeHash($bytes)).Replace("-", "").ToLowerInvariant() }
    finally { $hasher.Dispose() }
}

function Test-LogMessageHasBoundedToken([string]$Message, [string]$Token) {
    if ([string]::IsNullOrEmpty($Message) -or [string]::IsNullOrEmpty($Token) -or
        $Token.Length -gt $Message.Length) { return $false }
    $offset = 0
    while ($offset -le ($Message.Length - $Token.Length)) {
        $index = $Message.IndexOf($Token, $offset, [System.StringComparison]::OrdinalIgnoreCase)
        if ($index -lt 0) { return $false }
        $beforeOk = $index -eq 0 -or [char]::IsWhiteSpace($Message[$index - 1]) -or
            '="([{'.IndexOf($Message[$index - 1], [System.StringComparison]::Ordinal) -ge 0
        $afterIndex = $index + $Token.Length
        $afterOk = $afterIndex -eq $Message.Length -or [char]::IsWhiteSpace($Message[$afterIndex]) -or
            '";:)]}'.IndexOf($Message[$afterIndex], [System.StringComparison]::Ordinal) -ge 0
        if ($beforeOk -and $afterOk) { return $true }
        $offset = $index + 1
    }
    return $false
}

function Test-LogMessagePrefixExact([string]$Message, [string]$Prefix) {
    if (-not $Message.StartsWith($Prefix, [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    return $Message.Length -eq $Prefix.Length -or [char]::IsWhiteSpace($Message[$Prefix.Length])
}

function Test-TesterLogIdentityExact(
    [string]$Message,
    [string]$EmbeddedExpert,
    [string]$SymbolPeriod
) {
    return (Test-LogMessageHasBoundedToken $Message $EmbeddedExpert) -and
        (Test-LogMessageHasBoundedToken $Message $SymbolPeriod)
}

function Test-TesterRunStartMessage([string]$Message) {
    if ([string]::IsNullOrWhiteSpace($Message) -or
        $Message.IndexOf('Experts\', [System.StringComparison]::OrdinalIgnoreCase) -lt 0) { return $false }
    foreach ($prefix in @('optimization of ', 'visual testing of ', 'testing of ', 'test of ')) {
        if ($Message.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    # MT5 build 6230 coordinator logs omit the leading "optimization of":
    #   Experts\...\Strategy.ex5 on EURUSD,H1 from ...
    # Keep this structural only; exact expert/symbol binding is enforced by the
    # caller before a record can become the selected start.
    if ($Message.StartsWith('Experts\', [System.StringComparison]::OrdinalIgnoreCase)) {
        $onIndex = $Message.IndexOf(' on ', [System.StringComparison]::OrdinalIgnoreCase)
        $fromIndex = if ($onIndex -gt 8) {
            $Message.IndexOf(' from ', $onIndex + 4, [System.StringComparison]::OrdinalIgnoreCase)
        } else { -1 }
        if ($fromIndex -gt ($onIndex + 4)) { return $true }
    }
    # Build 6230 Agent logs invert the coordinator wording:
    #   EURUSD,H1: testing of Experts\... from ... started with inputs:
    # Keep the generic ambiguity check deliberately structural so a different
    # symbol/expert start between the selected exact pair is still rejected.
    $separator = ': testing of Experts\'
    $separatorIndex = $Message.IndexOf($separator, [System.StringComparison]::OrdinalIgnoreCase)
    if ($separatorIndex -le 1 -or
        -not $Message.EndsWith(' started with inputs:', [System.StringComparison]::OrdinalIgnoreCase)) { return $false }
    $identityPrefix = $Message.Substring(0, $separatorIndex)
    if ($identityPrefix.IndexOfAny([char[]]@(' ', "`t", "`r", "`n", ':')) -ge 0 -or
        $identityPrefix.IndexOf(',') -le 0) { return $false }
    $fromIndex = $Message.IndexOf(
        ' from ',
        $separatorIndex + $separator.Length,
        [System.StringComparison]::OrdinalIgnoreCase
    )
    return $fromIndex -gt ($separatorIndex + $separator.Length)
}

function Test-OrdinalStringInList([string]$Value, [object[]]$Candidates) {
    foreach ($candidate in $Candidates) {
        if ([string]::Equals($Value, [string]$candidate, [System.StringComparison]::Ordinal)) { return $true }
    }
    return $false
}

function Test-CoreLogSource([string]$Source) {
    return [System.Text.RegularExpressions.Regex]::IsMatch(
        $Source,
        '^Core(?: [0-9]+)?$',
        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
    )
}

function Test-SameLogPath([object]$Left, [object]$Right) {
    return [string]::Equals(
        [string]$Left.Path,
        [string]$Right.Path,
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Test-LogRecordAfter([object]$Record, [object]$BoundaryRecord) {
    if ($Record.ObservedUtc -gt $BoundaryRecord.ObservedUtc) { return $true }
    if ($Record.ObservedUtc -lt $BoundaryRecord.ObservedUtc -or -not (Test-SameLogPath $Record $BoundaryRecord)) { return $false }
    return [int]$Record.LineIndex -gt [int]$BoundaryRecord.LineIndex
}

function Test-LogRecordBefore([object]$Record, [object]$BoundaryRecord) {
    if ($Record.ObservedUtc -lt $BoundaryRecord.ObservedUtc) { return $true }
    if ($Record.ObservedUtc -gt $BoundaryRecord.ObservedUtc -or -not (Test-SameLogPath $Record $BoundaryRecord)) { return $false }
    return [int]$Record.LineIndex -lt [int]$BoundaryRecord.LineIndex
}

function Test-LogRecordInClosedRunWindow([object]$Record, [object]$StartRecord, [object]$CompletionRecord) {
    $afterStart = $Record -eq $StartRecord -or (Test-LogRecordAfter $Record $StartRecord)
    $beforeCompletion = $Record -eq $CompletionRecord -or (Test-LogRecordBefore $Record $CompletionRecord)
    return $afterStart -and $beforeCompletion
}

function Test-ExactJsonPropertySet([object]$Value, [string[]]$Expected) {
    if ($null -eq $Value) { return $false }
    [string[]]$actual = @($Value.PSObject.Properties.Name)
    [string[]]$expectedCopy = @($Expected)
    [System.Array]::Sort($actual, [System.StringComparer]::Ordinal)
    [System.Array]::Sort($expectedCopy, [System.StringComparer]::Ordinal)
    if ($actual.Count -ne $expectedCopy.Count) { return $false }
    for ($index = 0; $index -lt $actual.Count; $index++) {
        if (-not [string]::Equals($actual[$index], $expectedCopy[$index], [System.StringComparison]::Ordinal)) { return $false }
    }
    return $true
}

function Convert-ExactJsonInt64([object]$Value, [string]$Code) {
    if ($Value -is [bool] -or $null -eq $Value) { Fail $Code }
    $text = [System.Convert]::ToString($Value, [System.Globalization.CultureInfo]::InvariantCulture)
    [long]$parsed = 0
    if (-not [long]::TryParse(
        $text,
        [System.Globalization.NumberStyles]::Integer,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    )) { Fail $Code }
    return $parsed
}

function Convert-ExactJsonDouble([object]$Value, [string]$Code) {
    if ($Value -is [bool] -or $null -eq $Value) { Fail $Code }
    $text = [System.Convert]::ToString($Value, [System.Globalization.CultureInfo]::InvariantCulture)
    [double]$parsed = 0.0
    if (-not [double]::TryParse(
        $text,
        [System.Globalization.NumberStyles]::Float,
        [System.Globalization.CultureInfo]::InvariantCulture,
        [ref]$parsed
    ) -or [double]::IsNaN($parsed) -or [double]::IsInfinity($parsed)) { Fail $Code }
    return $parsed
}

function Test-StrategyExecutionProfile([object]$Profile) {
    if (-not (Test-ExactJsonPropertySet $Profile @(
        "schemaVersion", "profileId", "sourceDigest", "proofRequired",
        "fastPeriod", "slowPeriod", "previousShift", "currentShift",
        "requiredDirections", "profileDigest"
    ))) { return $false }
    $directions = @($Profile.requiredDirections)
    return [string]$Profile.schemaVersion -ceq "ea-factory-strategy-execution-profile-v1" -and
        [string]$Profile.profileId -ceq "custom-ema-10-60-closed-bar-smoke-mt5-v3" -and
        [string]$Profile.sourceDigest -cmatch '^[0-9a-f]{64}$' -and
        $Profile.proofRequired -is [bool] -and [bool]$Profile.proofRequired -and
        (Convert-ExactJsonInt64 $Profile.fastPeriod "strategy_execution_profile_invalid") -eq 10 -and
        (Convert-ExactJsonInt64 $Profile.slowPeriod "strategy_execution_profile_invalid") -eq 60 -and
        (Convert-ExactJsonInt64 $Profile.previousShift "strategy_execution_profile_invalid") -eq 2 -and
        (Convert-ExactJsonInt64 $Profile.currentShift "strategy_execution_profile_invalid") -eq 1 -and
        $directions.Count -eq 2 -and
        [string]$directions[0] -ceq "BUY" -and
        [string]$directions[1] -ceq "SELL" -and
        [string]$Profile.profileDigest -cmatch '^[0-9a-f]{64}$'
}

function Get-CertifiedEmaSmokeTelemetryJson([string]$Message, [string]$Code) {
    # Native MT5 Agent logs prefix Expert Print() output with the simulated
    # market timestamp.  Keep the grammar exact and anchored so an unrelated
    # line that merely contains EMA_SMOKE_V1 cannot become acceptance proof.
    $match = [System.Text.RegularExpressions.Regex]::Match(
        $Message,
        '^[0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} {3}EMA_SMOKE_V1 (?<payload>\{.*\})$',
        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
    )
    if (-not $match.Success) { Fail $Code }
    return [string]$match.Groups['payload'].Value
}

function Assert-CertifiedEmaSmokeExecutionProof(
    [object]$Request,
    [object]$Configured,
    [object[]]$Records,
    [object]$StartRecord,
    [object]$CompletionRecord,
    [object[]]$BoundCoreRecords
) {
    $code = "strategy_execution_proof_unverified"
    $profile = $Request.strategyExecutionProfile
    if (-not (Test-StrategyExecutionProfile $profile)) { Fail $code }
    $allowedPaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    [void]$allowedPaths.Add([System.IO.Path]::GetFullPath([string]$StartRecord.Path))
    [void]$allowedPaths.Add([System.IO.Path]::GetFullPath([string]$CompletionRecord.Path))
    foreach ($bound in @($BoundCoreRecords)) {
        [void]$allowedPaths.Add([System.IO.Path]::GetFullPath([string]$bound.Path))
    }
    $expertLeaf = [System.IO.Path]::GetFileNameWithoutExtension(([string]$Request.expertFileName).Trim())
    $symbol = ([string]$Configured.symbol).Trim()
    $period = ([string]$Request.testerSettings.period).Trim()
    if ([string]::IsNullOrWhiteSpace($expertLeaf) -or
        [string]::IsNullOrWhiteSpace($symbol) -or
        [string]::IsNullOrWhiteSpace($period)) { Fail $code }
    $expectedTelemetrySource = "$expertLeaf ($symbol,$period)"
    $telemetryPattern = '^[0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} {3}EMA_SMOKE_V1 \{.*\}$'
    $telemetry = @($Records | Where-Object {
        (Test-LogRecordInClosedRunWindow $_ $StartRecord $CompletionRecord) -and
        $allowedPaths.Contains([System.IO.Path]::GetFullPath([string]$_.Path)) -and
        [string]::Equals(
            [string]$_.Source,
            $expectedTelemetrySource,
            [System.StringComparison]::Ordinal
        ) -and
        [System.Text.RegularExpressions.Regex]::IsMatch(
            [string]$_.Message,
            $telemetryPattern,
            [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
        )
    })
    if ($telemetry.Count -lt 7 -or $telemetry.Count -gt 100000) { Fail $code }
    $telemetryPaths = @($telemetry | ForEach-Object {
        [System.IO.Path]::GetFullPath([string]$_.Path).ToLowerInvariant()
    } | Sort-Object -CaseSensitive -Unique)
    $telemetrySources = @($telemetry | ForEach-Object { [string]$_.Source } | Sort-Object -CaseSensitive -Unique)
    if ($telemetryPaths.Count -ne 1 -or $telemetrySources.Count -ne 1 -or
        [string]::IsNullOrWhiteSpace($telemetrySources[0])) { Fail $code }

    $sequenceRows = [System.Collections.ArrayList]::new()
    $lineHashes = [System.Collections.ArrayList]::new()
    $deals = [System.Collections.Generic.HashSet[long]]::new()
    $current = $null
    $final = $null
    foreach ($record in $telemetry) {
        $message = [string]$record.Message
        $jsonText = Get-CertifiedEmaSmokeTelemetryJson $message $code
        try { $event = $jsonText | ConvertFrom-Json -ErrorAction Stop }
        catch { Fail $code }
        if ($null -eq $event -or -not ($event.PSObject.Properties.Name -contains "event")) { Fail $code }
        $lineHash = Get-LogLineSha256 ([string]$record.RawLine)
        [void]$lineHashes.Add($lineHash)
        $eventName = [string]$event.event
        if ($null -ne $final) { Fail $code }
        if ($eventName -ceq "signal") {
            if ($null -ne $current -or -not (Test-ExactJsonPropertySet $event @(
                "event", "seq", "direction", "closed_bar_time", "fast_period",
                "slow_period", "previous_shift", "current_shift", "fast_2",
                "fast_1", "slow_2", "slow_1"
            ))) { Fail $code }
            $seq = Convert-ExactJsonInt64 $event.seq $code
            $closedBarTime = Convert-ExactJsonInt64 $event.closed_bar_time $code
            $direction = [string]$event.direction
            $fast2 = Convert-ExactJsonDouble $event.fast_2 $code
            $fast1 = Convert-ExactJsonDouble $event.fast_1 $code
            $slow2 = Convert-ExactJsonDouble $event.slow_2 $code
            $slow1 = Convert-ExactJsonDouble $event.slow_1 $code
            $expectedSeq = [long]$sequenceRows.Count + 1L
            $crosses = if ($direction -ceq "BUY") {
                $fast2 -le $slow2 -and $fast1 -gt $slow1
            } elseif ($direction -ceq "SELL") {
                $fast2 -ge $slow2 -and $fast1 -lt $slow1
            } else { $false }
            if ($seq -ne $expectedSeq -or $closedBarTime -le 0 -or
                (Convert-ExactJsonInt64 $event.fast_period $code) -ne 10 -or
                (Convert-ExactJsonInt64 $event.slow_period $code) -ne 60 -or
                (Convert-ExactJsonInt64 $event.previous_shift $code) -ne 2 -or
                (Convert-ExactJsonInt64 $event.current_shift $code) -ne 1 -or
                -not $crosses) { Fail $code }
            $current = [ordered]@{
                seq = $seq; direction = $direction; closedBarTime = $closedBarTime
                fast2 = $fast2; fast1 = $fast1; slow2 = $slow2; slow1 = $slow1
                deal = $null; signalLineSha256 = $lineHash
                pendingLineSha256 = $null; entryLineSha256 = $null
            }
            continue
        }
        if ($eventName -ceq "pending") {
            if ($null -eq $current -or $null -ne $current.pendingLineSha256 -or
                -not (Test-ExactJsonPropertySet $event @(
                    "event", "seq", "direction", "closed_bar_time"
                )) -or
                (Convert-ExactJsonInt64 $event.seq $code) -ne [long]$current.seq -or
                [string]$event.direction -cne [string]$current.direction -or
                (Convert-ExactJsonInt64 $event.closed_bar_time $code) -ne [long]$current.closedBarTime) { Fail $code }
            $current.pendingLineSha256 = $lineHash
            continue
        }
        if ($eventName -ceq "entry") {
            if ($null -eq $current -or $null -eq $current.pendingLineSha256 -or
                -not (Test-ExactJsonPropertySet $event @(
                    "event", "seq", "direction", "closed_bar_time", "deal"
                )) -or
                (Convert-ExactJsonInt64 $event.seq $code) -ne [long]$current.seq -or
                [string]$event.direction -cne [string]$current.direction -or
                (Convert-ExactJsonInt64 $event.closed_bar_time $code) -ne [long]$current.closedBarTime) { Fail $code }
            $deal = Convert-ExactJsonInt64 $event.deal $code
            if ($deal -le 0 -or -not $deals.Add($deal)) { Fail $code }
            $current.deal = $deal
            $current.entryLineSha256 = $lineHash
            [void]$sequenceRows.Add([pscustomobject]$current)
            $current = $null
            continue
        }
        if ($eventName -ceq "final") {
            if ($null -ne $current -or -not (Test-ExactJsonPropertySet $event @(
                "event", "reason", "signal", "entry", "rejected", "orphan",
                "pending", "data_unavailable", "buy_signals", "sell_signals",
                "buy_entries", "sell_entries", "outcome"
            ))) { Fail $code }
            $final = $event
            continue
        }
        # Rejected and orphan_entry are never valid acceptance evidence.
        Fail $code
    }
    if ($null -ne $current -or $null -eq $final -or $sequenceRows.Count -lt 2) { Fail $code }
    $signalCount = Convert-ExactJsonInt64 $final.signal $code
    $entryCount = Convert-ExactJsonInt64 $final.entry $code
    $rejectedCount = Convert-ExactJsonInt64 $final.rejected $code
    $orphanCount = Convert-ExactJsonInt64 $final.orphan $code
    $pendingCount = Convert-ExactJsonInt64 $final.pending $code
    $dataUnavailableCount = Convert-ExactJsonInt64 $final.data_unavailable $code
    $buySignalCount = Convert-ExactJsonInt64 $final.buy_signals $code
    $sellSignalCount = Convert-ExactJsonInt64 $final.sell_signals $code
    $buyEntryCount = Convert-ExactJsonInt64 $final.buy_entries $code
    $sellEntryCount = Convert-ExactJsonInt64 $final.sell_entries $code
    $observedBuy = @($sequenceRows | Where-Object { [string]$_.direction -ceq "BUY" }).Count
    $observedSell = @($sequenceRows | Where-Object { [string]$_.direction -ceq "SELL" }).Count
    if ($signalCount -ne $sequenceRows.Count -or $entryCount -ne $sequenceRows.Count -or
        $rejectedCount -ne 0 -or $orphanCount -ne 0 -or $pendingCount -ne 0 -or
        $dataUnavailableCount -lt 0 -or $buySignalCount -ne $observedBuy -or
        $sellSignalCount -ne $observedSell -or $buyEntryCount -ne $observedBuy -or
        $sellEntryCount -ne $observedSell -or $observedBuy -lt 1 -or $observedSell -lt 1 -or
        [string]::IsNullOrWhiteSpace([string]$final.outcome) -or
        $lineHashes.Count -ne (($sequenceRows.Count * 3) + 1)) { Fail $code }
    [string[]]$lineHashArray = @($lineHashes | ForEach-Object { [string]$_ })
    $telemetryDigest = Get-LogLineSha256 ([string]::Join("`n", $lineHashArray))
    return [ordered]@{
        schemaVersion = "ea-factory-strategy-execution-proof-v1"
        profileId = [string]$profile.profileId
        sourceDigest = [string]$profile.sourceDigest
        operationId = [string]$Request.operationId
        symbol = ([string]$Configured.symbol).Trim()
        period = ([string]$Request.testerSettings.period).Trim()
        eventCount = [int]$lineHashArray.Count
        signalCount = [int]$signalCount
        entryCount = [int]$entryCount
        rejectedCount = [int]$rejectedCount
        orphanCount = [int]$orphanCount
        pendingCount = [int]$pendingCount
        dataUnavailableCount = [int]$dataUnavailableCount
        buySignalCount = [int]$buySignalCount
        sellSignalCount = [int]$sellSignalCount
        buyEntryCount = [int]$buyEntryCount
        sellEntryCount = [int]$sellEntryCount
        sequences = @($sequenceRows)
        telemetryLineSha256s = $lineHashArray
        telemetryDigest = $telemetryDigest
        finalLineSha256 = [string]$lineHashArray[-1]
        verified = $true
    }
}

function Assert-TesterCleanCompletion([object]$Request, [bool]$Optimize, [object]$Configured) {
    $code = "mt5_tester_clean_completion_unverified"
    $boundaryPath = [System.IO.Path]::GetFullPath([string]$Request.startBoundaryPath)
    $boundary = [System.IO.FileInfo]::new($boundaryPath)
    if (-not $boundary.Exists -or $boundary.Length -le 0 -or
        (($boundary.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)) { Fail $code }
    $boundaryUtc = $boundary.CreationTimeUtc
    if ($boundaryUtc -gt [DateTime]::UtcNow.AddMinutes(5)) { Fail $code }
    $records = @(Get-FreshTesterLogRecords $Request $boundaryUtc $code)
    if ($records.Count -lt 1) { Fail $code }

    $expertPath = (([string]$Request.expertUiPath).Trim().Replace("/", "\").TrimStart("\"))
    if (-not $expertPath.EndsWith(".ex5", [System.StringComparison]::OrdinalIgnoreCase)) { $expertPath += ".ex5" }
    $embeddedExpert = "Experts\$expertPath"
    $symbol = ([string]$Configured.symbol).Trim()
    $period = ([string]$Request.testerSettings.period).Trim()
    $symbolPeriod = "$symbol,$period"
    if ([string]::IsNullOrWhiteSpace($expertPath) -or
        [string]::IsNullOrWhiteSpace($symbol) -or
        [string]::IsNullOrWhiteSpace($period)) { Fail $code }

    $optimizationStartPrefix = "optimization of $embeddedExpert on $symbolPeriod"
    $modernOptimizationStartPrefix = "$embeddedExpert on $symbolPeriod"
    $backtestStartPrefixes = @(
        "visual testing of $embeddedExpert on $symbolPeriod",
        "testing of $embeddedExpert on $symbolPeriod",
        "test of $embeddedExpert on $symbolPeriod"
    )
    $modernAgentStartPrefix = "${symbolPeriod}: testing of $embeddedExpert"
    $modernAgentFinishLine = "test $embeddedExpert on $symbolPeriod thread finished"
    $startCandidates = @()
    $modernOptimizationStarts = @()
    foreach ($record in $records) {
        if (Test-CoreLogSource ([string]$record.Source)) { continue }
        $message = [string]$record.Message
        $modernAgentStartExact = (-not $Optimize) -and
            (Test-LogMessagePrefixExact $message $modernAgentStartPrefix) -and
            $message.IndexOf(
                " from ",
                $modernAgentStartPrefix.Length,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -eq $modernAgentStartPrefix.Length -and
            $message.EndsWith(" started with inputs:", [System.StringComparison]::OrdinalIgnoreCase)
        $modernOptimizationStartExact = $Optimize -and
            (Test-LogMessagePrefixExact $message $modernOptimizationStartPrefix) -and
            $message.IndexOf(
                " from ",
                $modernOptimizationStartPrefix.Length,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -eq $modernOptimizationStartPrefix.Length
        # The exact build-6230 prefix binds symbol/period and expert directly;
        # older forms retain the bounded-token identity check.
        if (-not $modernAgentStartExact -and -not $modernOptimizationStartExact -and
            -not (Test-TesterLogIdentityExact $message $embeddedExpert $symbolPeriod)) { continue }
        if ($Optimize) {
            $legacyOptimizationStartExact = (Test-LogMessagePrefixExact $message $optimizationStartPrefix) -and
                $message.IndexOf(" from ", $optimizationStartPrefix.Length, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
            if (-not $legacyOptimizationStartExact -and -not $modernOptimizationStartExact) { continue }
        } else {
            $backtestStart = $false
            foreach ($prefix in $backtestStartPrefixes) {
                if (Test-LogMessagePrefixExact $message $prefix) { $backtestStart = $true; break }
            }
            if (-not $backtestStart -and $modernAgentStartExact) { $backtestStart = $true }
            if (-not $backtestStart) { continue }
        }
        $startCandidates += $record
        if ($modernOptimizationStartExact) { $modernOptimizationStarts += $record }
    }
    $startRecord = $null
    $completionRecord = $null
    $completionMarker = $null
    $completionPassCount = $null
    $sameThreadBacktestCompletion = $false
    $modernOptimizationCoordinator = $false
    $boundOptimizationAgentRecords = @()
    if ($Optimize) {
        # A global optimization-finished line is only meaningful in the exact
        # coordinator path/source that emitted its one post-boundary start.
        if ($startCandidates.Count -ne 1) { Fail $code }
        $startRecord = $startCandidates[0]
        $modernOptimizationCoordinator = $modernOptimizationStarts.Count -eq 1 -and
            $modernOptimizationStarts[0] -eq $startRecord
        $completionCandidates = @()
        foreach ($record in $records) {
            if (-not (Test-LogRecordAfter $record $startRecord) -or
                -not (Test-SameLogPath $record $startRecord) -or
                -not [string]::Equals([string]$record.Source, [string]$startRecord.Source, [System.StringComparison]::Ordinal)) { continue }
            $match = [System.Text.RegularExpressions.Regex]::Match(
                [string]$record.Message,
                '^optimization finished, total passes ([1-9][0-9]*)$',
                ([System.Text.RegularExpressions.RegexOptions]::CultureInvariant -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
            )
            $passCount = 0
            if ($match.Success -and [int]::TryParse([string]$match.Groups[1].Value, [ref]$passCount) -and $passCount -ge 2) {
                $completionCandidates += [pscustomobject]@{ Record = $record; Marker = "optimization_finished"; PassCount = [int]$passCount }
            }
        }
        if ($completionCandidates.Count -ne 1) { Fail $code }
        $completionRecord = $completionCandidates[0].Record
        $completionMarker = [string]$completionCandidates[0].Marker
        $completionPassCount = $completionCandidates[0].PassCount
        if ($modernOptimizationCoordinator) {
            # Build 6230 writes the coordinator finish before each local Agent
            # emits its exact thread-finished line.  Bind every completed pass
            # to an Agent log with the same expert/symbol/period and admit only
            # a short post-coordinator teardown window.  This proves the global
            # pass count without treating a normal worker teardown as failure.
            # Build 6230 omits the timeframe from each local worker's exact
            # thread-finished line.  Do not infer the missing period from that
            # symbol-only line: every accepted worker must independently bind
            # the configured symbol/period through the native History grammar
            # in the same expert-added -> thread-finished window.
            $agentFinishLine = "optimize $embeddedExpert on $symbol thread finished"
            $agentPeriodHistoryPattern = '^' +
                [System.Text.RegularExpressions.Regex]::Escape($symbolPeriod) +
                ': history cache allocated for [0-9]+ bars and contains [0-9]+ bars from [0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2} to [0-9]{4}\.[0-9]{2}\.[0-9]{2} [0-9]{2}:[0-9]{2}$'
            $agentDeadline = $completionRecord.ObservedUtc.AddSeconds(2)
            $agentFinishes = @($records | Where-Object {
                (Test-LogRecordAfter $_ $startRecord) -and
                $_.ObservedUtc -le $agentDeadline -and
                [string]::Equals([string]$_.Source, "Tester", [System.StringComparison]::Ordinal) -and
                [string]::Equals([string]$_.Message, $agentFinishLine, [System.StringComparison]::Ordinal)
            })
            if ($agentFinishes.Count -lt 1 -or $agentFinishes.Count -gt 64) { Fail $code }
            $passIds = @()
            foreach ($agentFinish in $agentFinishes) {
                $agentPath = [string]$agentFinish.Path
                $expertAddedPrefix = "expert file added: $embeddedExpert."
                $expertAdded = @($records | Where-Object {
                    (Test-SameLogPath $_ $agentFinish) -and
                    [string]::Equals([string]$_.Source, "Tester", [System.StringComparison]::Ordinal) -and
                    (Test-LogRecordAfter $_ $startRecord) -and
                    (Test-LogRecordBefore $_ $agentFinish) -and
                    (Test-LogMessagePrefixExact ([string]$_.Message) $expertAddedPrefix)
                })
                if ($expertAdded.Count -ne 1) { Fail $code }
                $agentStart = $expertAdded[0]
                $agentPeriodHistory = @($records | Where-Object {
                    (Test-SameLogPath $_ $agentFinish) -and
                    [string]::Equals([string]$_.Source, "History", [System.StringComparison]::Ordinal) -and
                    (Test-LogRecordInClosedRunWindow $_ $agentStart $agentFinish) -and
                    [System.Text.RegularExpressions.Regex]::IsMatch(
                        [string]$_.Message,
                        $agentPeriodHistoryPattern,
                        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
                    )
                })
                if ($agentPeriodHistory.Count -ne 1) { Fail $code }
                $agentPassStarts = @{}
                $agentPassResults = @{}
                foreach ($agentRecord in $records) {
                    if (-not (Test-SameLogPath $agentRecord $agentFinish) -or
                        -not (Test-LogRecordInClosedRunWindow $agentRecord $agentStart $agentFinish)) { continue }
                    $startMatch = [System.Text.RegularExpressions.Regex]::Match(
                        [string]$agentRecord.Message,
                        '^optimization pass ([0-9]+) started$',
                        ([System.Text.RegularExpressions.RegexOptions]::CultureInvariant -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                    )
                    $agentMessage = [string]$agentRecord.Message
                    $resultMatch = [System.Text.RegularExpressions.Regex]::Match(
                        $agentMessage,
                        '^([0-9]+)(?: OnTester result ([+-]?(?:(?:[0-9]+(?:\.[0-9]*)?)|(?:\.[0-9]+))(?:[eE][+-]?[0-9]+)?))? : passed in [0-9]+:[0-9]{2}:[0-9]{2}\.[0-9]{3}$',
                        [System.Text.RegularExpressions.RegexOptions]::CultureInvariant
                    )
                    $mentionsOnTesterResult = [System.Text.RegularExpressions.Regex]::IsMatch(
                        $agentMessage,
                        '^[0-9]+ OnTester result(?:\s|$)',
                        ([System.Text.RegularExpressions.RegexOptions]::CultureInvariant -bor [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                    )
                    $resultMatchValid = $resultMatch.Success
                    if ($resultMatchValid -and $resultMatch.Groups[2].Success) {
                        [double]$onTesterResult = 0.0
                        $resultMatchValid = [double]::TryParse(
                            [string]$resultMatch.Groups[2].Value,
                            [System.Globalization.NumberStyles]::Float,
                            [System.Globalization.CultureInfo]::InvariantCulture,
                            [ref]$onTesterResult
                        ) -and -not [double]::IsNaN($onTesterResult) -and
                            -not [double]::IsInfinity($onTesterResult)
                    }
                    if ($mentionsOnTesterResult -and -not $resultMatchValid) {
                        Fail $code
                    }
                    $passRecordSourceIsTester = [string]::Equals(
                        [string]$agentRecord.Source,
                        "Tester",
                        [System.StringComparison]::Ordinal
                    )
                    if (($startMatch.Success -or $resultMatchValid -or $mentionsOnTesterResult) -and
                        -not $passRecordSourceIsTester) {
                        Fail $code
                    }
                    if ($startMatch.Success) {
                        [int]$parsedPassId = 0
                        if (-not [int]::TryParse(
                            [string]$startMatch.Groups[1].Value,
                            [System.Globalization.NumberStyles]::None,
                            [System.Globalization.CultureInfo]::InvariantCulture,
                            [ref]$parsedPassId
                        )) { Fail $code }
                        $id = $parsedPassId.ToString([System.Globalization.CultureInfo]::InvariantCulture)
                        if ($agentPassStarts.ContainsKey($id)) { Fail $code }
                        $agentPassStarts[$id] = $agentRecord
                    }
                    if ($resultMatchValid) {
                        [int]$parsedPassId = 0
                        if (-not [int]::TryParse(
                            [string]$resultMatch.Groups[1].Value,
                            [System.Globalization.NumberStyles]::None,
                            [System.Globalization.CultureInfo]::InvariantCulture,
                            [ref]$parsedPassId
                        )) { Fail $code }
                        $id = $parsedPassId.ToString([System.Globalization.CultureInfo]::InvariantCulture)
                        if ($agentPassResults.ContainsKey($id)) { Fail $code }
                        $agentPassResults[$id] = $agentRecord
                    }
                }
                if ($agentPassStarts.Count -lt 1 -or $agentPassStarts.Count -ne $agentPassResults.Count) { Fail $code }
                foreach ($id in $agentPassStarts.Keys) {
                    if (-not $agentPassResults.ContainsKey($id) -or
                        -not (Test-LogRecordAfter $agentPassResults[$id] $agentPassStarts[$id])) { Fail $code }
                    $passIds += [int]$id
                }
                $boundOptimizationAgentRecords += @($records | Where-Object {
                    (Test-SameLogPath $_ $agentFinish) -and
                    (Test-LogRecordInClosedRunWindow $_ $agentStart $agentFinish)
                })
            }
            $uniquePassIds = @($passIds | Sort-Object -Unique)
            if ($passIds.Count -ne $completionPassCount -or
                $uniquePassIds.Count -ne $completionPassCount) { Fail $code }
            for ($passIndex = 0; $passIndex -lt $completionPassCount; $passIndex++) {
                if ($uniquePassIds[$passIndex] -ne $passIndex) { Fail $code }
            }
        }
    } else {
        # MT5 build 6230 writes a second exact start inside the local Agent log
        # and completes that run as `Tester ... thread finished` in the same
        # path/source.  Pair that execution thread directly instead of making
        # the harmless coordinator start render the run globally ambiguous.
        $modernAgentStarts = @($startCandidates | Where-Object {
            (Test-LogMessagePrefixExact ([string]$_.Message) $modernAgentStartPrefix) -and
            ([string]$_.Message).IndexOf(
                " from ",
                $modernAgentStartPrefix.Length,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -eq $modernAgentStartPrefix.Length -and
            ([string]$_.Message).EndsWith(" started with inputs:", [System.StringComparison]::OrdinalIgnoreCase)
        })
        $modernAgentFinishes = @($records | Where-Object {
            [string]::Equals(
                [string]$_.Message,
                $modernAgentFinishLine,
                [System.StringComparison]::Ordinal
            )
        })
        $sameThreadPairs = @()
        foreach ($candidateStart in $modernAgentStarts) {
            foreach ($candidateFinish in $modernAgentFinishes) {
                if ((Test-SameLogPath $candidateStart $candidateFinish) -and
                    [string]::Equals(
                        [string]$candidateStart.Source,
                        [string]$candidateFinish.Source,
                        [System.StringComparison]::Ordinal
                    ) -and
                    (Test-LogRecordAfter $candidateFinish $candidateStart)) {
                    $sameThreadPairs += [pscustomobject]@{ Start = $candidateStart; Completion = $candidateFinish }
                }
            }
        }
        if ($sameThreadPairs.Count -gt 1) { Fail $code }
        if ($sameThreadPairs.Count -eq 1) {
            $sameThreadBacktestCompletion = $true
            $startRecord = $sameThreadPairs[0].Start
            $completionRecord = $sameThreadPairs[0].Completion
            $completionMarker = "thread_finished"
        } else {
            # Preserve the older coordinator -> Core topology.  It remains
            # fail-closed: one exact start, one later identity-bearing Core
            # finish, and an earlier identity-bearing record on that Core.
            if ($startCandidates.Count -ne 1) { Fail $code }
            $startRecord = $startCandidates[0]
            $completionCandidates = @()
            foreach ($record in $records) {
                if (-not (Test-LogRecordAfter $record $startRecord)) { continue }
                $message = [string]$record.Message
                $boundThreadFinish = (
                    (Test-TesterLogIdentityExact $message $embeddedExpert $symbolPeriod) -and
                    $message.EndsWith(" thread finished", [System.StringComparison]::OrdinalIgnoreCase)
                )
                if (-not $Optimize -and $boundThreadFinish) {
                    $completionCandidates += [pscustomobject]@{ Record = $record; Marker = "thread_finished"; PassCount = $null }
                }
            }
            if ($completionCandidates.Count -ne 1) { Fail $code }
            $completionRecord = $completionCandidates[0].Record
            $completionMarker = [string]$completionCandidates[0].Marker
            if (-not (Test-CoreLogSource ([string]$completionRecord.Source))) { Fail $code }
            $completionThreadLineage = @($records | Where-Object {
                (Test-LogRecordAfter $_ $startRecord) -and
                (Test-LogRecordBefore $_ $completionRecord) -and
                (Test-SameLogPath $_ $completionRecord) -and
                [string]::Equals(
                    [string]$_.Source,
                    [string]$completionRecord.Source,
                    [System.StringComparison]::Ordinal
                ) -and
                (Test-TesterLogIdentityExact ([string]$_.Message) $embeddedExpert $symbolPeriod)
            })
            # The identity-bearing finish cannot establish its own Core
            # lineage.  An earlier exact record must bind the same agent-log
            # path/source to this expert, symbol and period first.
            if ($completionThreadLineage.Count -lt 1) { Fail $code }
        }
    }

    # A different tester run starting in the same coordinator log before the
    # selected completion makes a global optimization completion ambiguous.
    $interveningStarts = @($records | Where-Object {
        (Test-LogRecordAfter $_ $startRecord) -and
        (Test-LogRecordBefore $_ $completionRecord) -and
        -not (Test-CoreLogSource ([string]$_.Source)) -and
        (Test-TesterRunStartMessage ([string]$_.Message))
    })
    if ($interveningStarts.Count -gt 0) { Fail $code }

    $boundCoreRecords = if ($modernOptimizationCoordinator) {
        @($boundOptimizationAgentRecords)
    } elseif ($sameThreadBacktestCompletion) {
        @($records | Where-Object {
            (Test-LogRecordInClosedRunWindow $_ $startRecord $completionRecord) -and
            (Test-SameLogPath $_ $startRecord) -and
            [string]::Equals(
                [string]$_.Source,
                [string]$startRecord.Source,
                [System.StringComparison]::Ordinal
            ) -and
            (Test-TesterLogIdentityExact ([string]$_.Message) $embeddedExpert $symbolPeriod)
        })
    } else {
        @($records | Where-Object {
            (Test-LogRecordInClosedRunWindow $_ $startRecord $completionRecord) -and
            (Test-CoreLogSource ([string]$_.Source)) -and
            (Test-TesterLogIdentityExact ([string]$_.Message) $embeddedExpert $symbolPeriod)
        })
    }
    $coreSources = @($boundCoreRecords | ForEach-Object { [string]$_.Source } | Sort-Object -CaseSensitive -Unique)
    if ($coreSources.Count -lt 1 -or $coreSources.Count -gt 64) { Fail $code }

    foreach ($record in $records) {
        if (-not (Test-LogRecordInClosedRunWindow $record $startRecord $completionRecord)) { continue }
        $boundThread = ((Test-SameLogPath $record $startRecord) -and [string]::Equals(
                [string]$record.Source, [string]$startRecord.Source, [System.StringComparison]::Ordinal
            )) -or ((Test-SameLogPath $record $completionRecord) -and [string]::Equals(
                [string]$record.Source, [string]$completionRecord.Source, [System.StringComparison]::Ordinal
            ))
        # On the modern Agent topology, fatal messages can be emitted by a
        # sibling component source in the same physical execution log.  The
        # exact start/finish pair binds that whole file for the closed window.
        if (-not $boundThread -and $sameThreadBacktestCompletion -and
            (Test-SameLogPath $record $startRecord)) { $boundThread = $true }
        if (-not $boundThread) {
            foreach ($coreRecord in $boundCoreRecords) {
                if ((Test-SameLogPath $record $coreRecord) -and [string]::Equals(
                        [string]$record.Source, [string]$coreRecord.Source, [System.StringComparison]::Ordinal
                    )) { $boundThread = $true; break }
            }
        }
        if (-not $boundThread) { continue }
        $message = ([string]$record.Message).ToLowerInvariant()
        foreach ($fatal in @("critical error", "out of memory", "not enough memory", "cannot allocate", "abnormal termination", "access violation")) {
            if ($message.Contains($fatal)) { Fail $code }
        }
    }
    $disconnectObserved = $false
    foreach ($record in $records) {
        if (-not (Test-LogRecordInClosedRunWindow $record $startRecord $completionRecord) -or
            -not ([string]$record.Message).EndsWith("disconnected", [System.StringComparison]::OrdinalIgnoreCase)) { continue }
        $boundThread = ((Test-SameLogPath $record $startRecord) -and [string]::Equals(
                [string]$record.Source, [string]$startRecord.Source, [System.StringComparison]::Ordinal
            )) -or ((Test-SameLogPath $record $completionRecord) -and [string]::Equals(
                [string]$record.Source, [string]$completionRecord.Source, [System.StringComparison]::Ordinal
            ))
        if (-not $boundThread -and $sameThreadBacktestCompletion -and
            (Test-SameLogPath $record $startRecord)) { $boundThread = $true }
        if (-not $boundThread) {
            foreach ($coreRecord in $boundCoreRecords) {
                if ((Test-SameLogPath $record $coreRecord) -and [string]::Equals(
                        [string]$record.Source, [string]$coreRecord.Source, [System.StringComparison]::Ordinal
                    )) { $boundThread = $true; break }
            }
        }
        if ($boundThread) { $disconnectObserved = $true; break }
    }
    if ($disconnectObserved) { Fail $code }
    $hasStrategyProfile = $Request.PSObject.Properties.Name -contains "strategyExecutionProfile"
    if ($hasStrategyProfile -and $null -ne $Request.strategyExecutionProfile) {
        if ($Optimize) { Fail "strategy_execution_profile_invalid" }
        $script:StrategyExecutionProof = Assert-CertifiedEmaSmokeExecutionProof `
            $Request $Configured $records $startRecord $completionRecord $boundCoreRecords
    } else {
        $script:StrategyExecutionProof = $null
    }
    $startLineSha256 = Get-LogLineSha256 ([string]$startRecord.RawLine)
    $completionLineSha256 = Get-LogLineSha256 ([string]$completionRecord.RawLine)
    $startLogPathSha256 = Get-LogLineSha256 ([System.IO.Path]::GetFullPath([string]$startRecord.Path).ToLowerInvariant())
    $completionLogPathSha256 = Get-LogLineSha256 ([System.IO.Path]::GetFullPath([string]$completionRecord.Path).ToLowerInvariant())
    $startSource = [string]$startRecord.Source
    $completionSource = [string]$completionRecord.Source
    if ([string]::IsNullOrWhiteSpace($startSource) -or [string]::IsNullOrWhiteSpace($completionSource)) { Fail $code }
    $startSourceSha256 = Get-LogLineSha256 $startSource
    $completionSourceSha256 = Get-LogLineSha256 $completionSource
    [string[]]$coreSourceSha256s = @($coreSources | ForEach-Object { Get-LogLineSha256 ([string]$_) })
    [System.Array]::Sort($coreSourceSha256s, [System.StringComparer]::Ordinal)
    $coreSourcesSha256 = Get-LogLineSha256 ([string]::Join("`n", $coreSourceSha256s))
    [string[]]$coreThreadIdentitySha256s = @($boundCoreRecords | ForEach-Object {
        $corePathSha256 = Get-LogLineSha256 ([System.IO.Path]::GetFullPath([string]$_.Path).ToLowerInvariant())
        $coreSourceSha256 = Get-LogLineSha256 ([string]$_.Source)
        Get-LogLineSha256 "$corePathSha256`n$coreSourceSha256"
    } | Sort-Object -CaseSensitive -Unique)
    if ($coreThreadIdentitySha256s.Count -lt 1 -or $coreThreadIdentitySha256s.Count -gt 64) { Fail $code }
    if (-not $Optimize -and $coreThreadIdentitySha256s.Count -ne 1) { Fail $code }
    [System.Array]::Sort($coreThreadIdentitySha256s, [System.StringComparer]::Ordinal)
    $coreThreadIdentitiesSha256 = Get-LogLineSha256 ([string]::Join("`n", $coreThreadIdentitySha256s))
    $expertUiPathSha256 = Get-LogLineSha256 ([string]$Request.expertUiPath)
    $expertSymbolPeriodSha256 = Get-LogLineSha256 "$([string]$Request.expertFileName)`n$([string]$Request.expectedDeployedExpertSha256)`n$expertUiPathSha256`n$(([string]$Configured.symbol).Trim())`n$(([string]$Request.testerSettings.period).Trim())"
    $logIdentitySha256 = Get-LogLineSha256 "$startLogPathSha256`n$completionLogPathSha256`n$startSourceSha256`n$completionSourceSha256"
    $executionThreadIdentitySha256 = Get-LogLineSha256 "$logIdentitySha256`n$([int]$startRecord.LineIndex)`n$([int]$completionRecord.LineIndex)`n$coreThreadIdentitiesSha256"
    $passToken = if ($Optimize) { [string]$completionPassCount } else { "" }
    $runIdentitySha256 = Get-LogLineSha256 "$([string]$Request.operationId)`n$completionMarker`n$expertSymbolPeriodSha256`n$logIdentitySha256`n$coreSourcesSha256`n$coreThreadIdentitiesSha256`n$startLineSha256`n$completionLineSha256`n$([int]$startRecord.LineIndex)`n$([int]$completionRecord.LineIndex)`n$passToken"
    return [ordered]@{
        schemaVersion = "ea-factory-mt5-tester-completion-evidence-v2"
        source = "fresh_tester_log_completion"
        boundaryCreatedAt = $boundaryUtc.ToString("o")
        runStartedAt = $startRecord.ObservedUtc.ToString("o")
        runCompletedAt = $completionRecord.ObservedUtc.ToString("o")
        startLineSha256 = $startLineSha256
        completionLineSha256 = $completionLineSha256
        completionMarker = $completionMarker
        startLogPathSha256 = $startLogPathSha256
        completionLogPathSha256 = $completionLogPathSha256
        startSourceSha256 = $startSourceSha256
        completionSourceSha256 = $completionSourceSha256
        coreSourceCount = [int]$coreSources.Count
        coreSourceSha256s = [string[]]$coreSourceSha256s
        coreSourcesSha256 = $coreSourcesSha256
        coreThreadCount = [int]$coreThreadIdentitySha256s.Count
        coreThreadIdentitySha256s = [string[]]$coreThreadIdentitySha256s
        coreThreadIdentitiesSha256 = $coreThreadIdentitiesSha256
        startLineOrdinal = [int]$startRecord.LineIndex
        completionLineOrdinal = [int]$completionRecord.LineIndex
        expertUiPathSha256 = $expertUiPathSha256
        deployedExpertSha256 = [string]$Request.expectedDeployedExpertSha256
        expertSymbolPeriodSha256 = $expertSymbolPeriodSha256
        logIdentitySha256 = $logIdentitySha256
        executionThreadIdentitySha256 = $executionThreadIdentitySha256
        runIdentitySha256 = $runIdentitySha256
        completionPassCount = if ($Optimize) { [int]$completionPassCount } else { $null }
        coreDisconnectObserved = [bool]$disconnectObserved
        verified = $true
    }
}

function Read-And-VerifyConfiguredTester([object]$Request, [bool]$Optimize) {
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $bound = Normalize-TesterSettingsTabExact $Request ([IntPtr]$script:TerminalRootHandle) $true "mt5_tester_settings_tab_not_verified"
    $activeRoot = $bound.root
    $controls = $bound.controls
    $algoBefore = Get-AlgoTradingState $activeRoot
    $idleBefore = Read-TesterStartState $controls.start "mt5_tester_not_idle"
    if ($idleBefore -cne "Start") { Fail "mt5_tester_not_idle" }
    $expert = (Get-Value $controls.expert).Trim().Replace("/", "\")
    $expectedExpert = ([string]$Request.expertUiPath).Trim().Replace("/", "\")
    if ($expert -notin @($expectedExpert, "$expectedExpert.ex5")) { Fail "mt5_expert_readback_mismatch" }
    # Collection/recovery is deliberately read-only: it never opens the
    # Navigator menu or refreshes the catalogue.  Still require that the
    # configured expert resolves to one and only one native combo entry so a
    # stale edit value or duplicate catalogue entry cannot be accepted.
    $expertMatches = @(Get-NativeComboExactMatches $controls.expert @($expectedExpert, "$expectedExpert.ex5") "mt5_expert_catalog_read_failed")
    if ($expertMatches.Count -ne 1) { Fail "mt5_expert_readback_mismatch" }
    $refreshBoundaryExists = [System.IO.File]::Exists((Get-ExpertCatalogRefreshBoundaryPath $Request))
    $refreshBoundarySha256 = if ($refreshBoundaryExists) { Assert-ExpertCatalogRefreshBoundary $Request } else { $null }
    $finalBound = Get-BoundTesterControlSet $Request
    $activeRoot = $finalBound.root
    $controls = $finalBound.controls
    $expert = (Get-Value $controls.expert).Trim().Replace("/", "\")
    if ($expert -notin @($expectedExpert, "$expectedExpert.ex5")) { Fail "mt5_expert_readback_mismatch" }
    $expertMatches = @(Get-NativeComboExactMatches $controls.expert @($expectedExpert, "$expectedExpert.ex5") "mt5_expert_catalog_read_failed")
    if ($expertMatches.Count -ne 1) { Fail "mt5_expert_readback_mismatch" }
    $idleAfter = Read-TesterStartState $controls.start "mt5_tester_not_idle"
    if ($idleAfter -cne "Start") { Fail "mt5_tester_not_idle" }
    $algoAfter = Get-AlgoTradingState $activeRoot
    if ($algoAfter -ne $algoBefore) { Fail "mt5_algo_trading_state_changed" }
    $timer.Stop()
    $expertCatalogRefresh = [ordered]@{
        schemaVersion = "ea-factory-mt5-expert-catalog-refresh-v2"
        attempted = $refreshBoundaryExists
        recoveredAfterBoundary = $refreshBoundaryExists
        commandCount = if ($refreshBoundaryExists) { 1 } else { 0 }
        commandName = if ($refreshBoundaryExists) { "Refresh" } else { $null }
        boundarySha256 = if ($refreshBoundaryExists) { [string]$refreshBoundarySha256 } else { $null }
        navigatorPaneAutomationId = "32845"
        navigatorTreeAutomationId = "10064"
        expertNodeName = "Expert Advisors"
        refreshMenuAutomationId = $null
        refreshMenuName = "Refresh"
        refreshMenuProvider = "native_hmenu"
        refreshMenuWindowClass = "#32768"
        refreshMenuNativeCommandId = 33416
        refreshMenuDispatchMethod = "targeted_menu_keyboard"
        matchCountBefore = 1
        matchCountAfter = 1
        selectedExpertReadback = [string]$expert
        idleStateBefore = [string]$idleBefore
        idleStateImmediatelyBeforeRefresh = $null
        idleStateAfter = [string]$idleAfter
        algoTradingStateBefore = [bool]$algoBefore
        algoTradingStateAfter = [bool]$algoAfter
        terminalProcessId = [int]$TerminalProcess.Id
        terminalWindowHandle = [long]$script:TerminalRootHandle.ToInt64()
        elapsedMs = [int][Math]::Min([int]::MaxValue, [Math]::Max(0, $timer.ElapsedMilliseconds))
        verified = $true
    }
    $symbol = (Get-Value $controls.symbol).Trim()
    if ([string]$Request.testerSettings.symbolPolicy -ceq "explicit" -and $symbol -cne ([string]$Request.testerSettings.symbol).Trim()) { Fail "mt5_symbol_readback_mismatch" }
    $timeframe = (Get-SelectedComboText $controls.timeframe "mt5_timeframe_readback_mismatch").Trim()
    if ($timeframe -notin @(Get-PeriodUiNames ([string]$Request.testerSettings.period))) { Fail "mt5_timeframe_readback_mismatch" }
    $modelLabel = Get-SelectedComboText $controls.modelling "mt5_model_readback_mismatch"
    if ($modelLabel -notin @(Get-ModelUiNames ([string]$Request.testerSettings.model))) { Fail "mt5_model_readback_mismatch" }
    $datePolicyLabel = Get-SelectedComboText $controls.useDate "mt5_use_date_readback_mismatch"
    $useDate = ($datePolicyLabel -ceq "Custom period")
    if ($useDate -ne [bool]$Request.testerSettings.useDate) { Fail "mt5_use_date_readback_mismatch" }
    $fromDate = if ($useDate) { (Get-Value $controls.fromDate).Trim() } else { $null }
    $toDate = if ($useDate) { (Get-Value $controls.toDate).Trim() } else { $null }
    if ($useDate) {
        $expectedFromDate = Get-NativeTesterDateText ([string]$Request.testerSettings.fromDate) "mt5_date_readback_mismatch"
        $expectedToDate = Get-NativeTesterDateText ([string]$Request.testerSettings.toDate) "mt5_date_readback_mismatch"
        if ($fromDate -cne $expectedFromDate -or $toDate -cne $expectedToDate) { Fail "mt5_date_readback_mismatch" }
        # The signed bridge contract uses ISO dates. Return those exact values
        # only after locale-independent native UI readback has succeeded.
        $fromDate = ([string]$Request.testerSettings.fromDate).Trim()
        $toDate = ([string]$Request.testerSettings.toDate).Trim()
    }
    $optimizationToken = if ($Optimize) { [string]$Request.optimizationIntent.mode } else { "disabled" }
    $optimizationLabel = Get-SelectedComboText $controls.optimization "mt5_optimization_mode_readback_mismatch"
    if ($optimizationLabel -notin @(Get-OptimizationUiNames $optimizationToken)) { Fail "mt5_optimization_mode_readback_mismatch" }
    $forwardLabel = Get-SelectedComboText $controls.forward "mt5_forward_mode_readback_mismatch"
    if ($forwardLabel -notin @("No", "Disabled")) { Fail "mt5_forward_mode_readback_mismatch" }
    $criterionLabel = $null
    $inputEvidence = $null; $baselineEvidence = $null; $optimizationEvidence = $null
    if ($Optimize) {
        # Recovery is read-only and may begin with Settings scrolled to the
        # top.  The criterion remains an exact owner/root/parent-bound native
        # ComboBox even when UIA marks it offscreen; read its native selection
        # without scrolling, focusing, opening, or changing it.
        $criterionBound = Get-BoundOptimizationCriterion $Request "mt5_criterion_control_not_verified" $true
        $activeRoot = $criterionBound.root
        $controls = $criterionBound.controls
        $criterionLabel = Get-SelectedComboText $controls["criterion"] "mt5_criterion_readback_mismatch"
        if ($criterionLabel -notin @(Get-CriterionUiNames ([string]$Request.optimizationIntent.criterion))) { Fail "mt5_criterion_readback_mismatch" }
        $baselineReadback = Get-FullExistingFile $Request.baselineInputReadbackSetPath ".set" "mt5_optimization_baseline_readback_missing"
        $optimizationReadback = Get-FullExistingFile $Request.inputReadbackSetPath ".set" "mt5_optimization_readback_missing"
        $baselineEvidence = [ordered]@{
            sourceSetSha256 = [string]$Request.optimizationIntent.baselinePresetRef.sha256
            readbackSetSha256 = Assert-Mt5SetReference $Request.optimizationIntent.baselinePresetRef $baselineReadback "mt5_optimization_baseline_readback_mismatch" $false $true
            readbackEntriesDigest = [string]$Request.optimizationIntent.baselinePresetRef.expectedReadbackEntriesDigest
        }
        $optimizationEvidence = [ordered]@{
            sourceSetSha256 = [string]$Request.optimizationIntent.setRef.sha256
            readbackSetSha256 = Assert-Mt5SetReference $Request.optimizationIntent.setRef $optimizationReadback "mt5_optimization_readback_mismatch" $false $true
            readbackEntriesDigest = [string]$Request.optimizationIntent.setRef.expectedReadbackEntriesDigest
        }
    } else {
        $visualBound = Get-BoundVisualModeControl $Request
        $activeRoot = $visualBound.root
        $controls = $visualBound.controls
        if (-not (Get-Toggle $visualBound.visual "mt5_visual_mode_readback_mismatch")) { Fail "mt5_visual_mode_readback_mismatch" }
        $inputReadback = Get-FullExistingFile $Request.inputPresetReadbackSetPath ".set" "mt5_tester_input_readback_missing"
        $inputEvidence = [ordered]@{
            sourceSetSha256 = [string]$Request.inputPresetRef.sha256
            readbackSetSha256 = Assert-Mt5SetReference $Request.inputPresetRef $inputReadback "mt5_tester_input_readback_mismatch" $false $true
            readbackEntriesDigest = [string]$Request.inputPresetRef.expectedReadbackEntriesDigest
        }
    }
    return [ordered]@{
        controls = $controls; expert = $expert; symbol = $symbol; timeframe = $timeframe
        modelLabel = $modelLabel; optimizationLabel = $optimizationLabel; forwardLabel = $forwardLabel
        criterionLabel = $criterionLabel; deposit = Get-PositiveDecimal $controls.deposit "mt5_deposit_readback_mismatch"
        useDate = $useDate; fromDate = $fromDate; toDate = $toDate
        inputEvidence = $inputEvidence; baselineEvidence = $baselineEvidence; optimizationEvidence = $optimizationEvidence
        expertCatalogRefresh = $expertCatalogRefresh
    }
}

function Invoke-Tester([object]$Request, [bool]$Optimize, [string]$RecoveryMode) {
    $script:FailureCheckpoint = "tester_request_validation"
    if ($RecoveryMode -cnotin @("none", "in_flight", "completed", "collected")) { Fail "visible_ui_request_contract_invalid" }
    $recovering = $RecoveryMode -cne "none"
    $hasNeverStart = $Request.PSObject.Properties.Name -contains "neverStart"
    $hasServiceAction = $Request.PSObject.Properties.Name -contains "serviceAction"
    if ($hasNeverStart -ne $hasServiceAction) { Fail "visible_ui_request_contract_invalid" }
    $expectedServiceAction = if ($RecoveryMode -ceq "none") { "start_round" } elseif ($RecoveryMode -ceq "in_flight") { "collect_round" } else { "recover_round" }
    if ($hasNeverStart) {
        if ($null -eq $Request.neverStart -or $Request.neverStart.GetType() -ne [bool] -or
            [string]$Request.serviceAction -cne $expectedServiceAction -or
            ([bool]$Request.neverStart) -ne $recovering) { Fail "visible_ui_request_contract_invalid" }
    }
    if ($Optimize -and -not $hasNeverStart) { Fail "visible_ui_request_contract_invalid" }
    if ($recovering -and -not $hasNeverStart) { Fail "mt5_tester_start_forbidden" }
    if ($recovering -and -not [System.IO.File]::Exists([string]$Request.startBoundaryPath)) { Fail "tester_start_boundary_missing" }
    $hasCriterionId = $Request.PSObject.Properties.Name -contains "optimizationCriterionAutomationId"
    $criterionId = if ($hasCriterionId) { [string]$Request.optimizationCriterionAutomationId } else { $null }
    $hasVisualModeId = $null -ne $Request.requiredAutomationIds.PSObject.Properties["visualMode"]
    # Optimization intentionally omits Visual mode.  Under StrictMode an
    # unconditional read of that absent property terminates request validation
    # before the native Start boundary, so only read it after proving it exists.
    $visualModeId = if ($hasVisualModeId) { [string]$Request.requiredAutomationIds.visualMode } else { $null }
    if ($Optimize) {
        if (-not $hasCriterionId -or $criterionId -cne "10507" -or $hasVisualModeId) { Fail "visible_ui_request_contract_invalid" }
    } elseif (-not $hasCriterionId -or $null -ne $Request.optimizationCriterionAutomationId) {
        Fail "visible_ui_request_contract_invalid"
    } elseif (-not $hasVisualModeId -or $visualModeId -cne "10490") {
        Fail "visible_ui_request_contract_invalid"
    }
    if ($recovering) { [void](Assert-StartBoundary $Request) }
    # A boundary without its exact durable dispatch receipt is ambiguous: the
    # one permitted Start may or may not have been consumed.  Recovery must
    # fail closed before inspecting results/logs and must never reconstruct the
    # receipt or replay Start.
    $dispatchConfirmationSha256 = if ($recovering) { Assert-DispatchConfirmation $Request } else { $null }
    $expert = Get-FullExistingFile $Request.deployedExpertPath ".ex5" "mt5_deployed_expert_missing"
    if ((Get-Sha256 $expert) -cne [string]$Request.expectedDeployedExpertSha256) { Fail "mt5_deployed_expert_digest_mismatch" }

    $settingsCheckpoint = $null; $resultCheckpoint = $null; $reportProofCheckpoint = $null
    if ($recovering) {
        $settingsCheckpoint = Get-ExistingPngCheckpoint $Request.settingsScreenshotPath $Request.testerSettingsSha256 "mt5_tester_recovery_checkpoint_mismatch"
        $resultExists = [System.IO.File]::Exists([string]$Request.resultScreenshotPath)
        $reportExists = [System.IO.File]::Exists([string]$Request.testerReportPath)
        $reportProofExists = [System.IO.File]::Exists([string]$Request.reportScreenshotPath)
        if ($reportExists -ne $reportProofExists) { Fail "mt5_tester_recovery_checkpoint_invalid" }
        if ($RecoveryMode -ceq "in_flight") {
            if ($resultExists -or $reportExists -or $reportProofExists) { Fail "mt5_tester_recovery_checkpoint_invalid" }
            if ($Optimize -and [System.IO.File]::Exists([string]$Request.optimizationCompletionCheckpointPath)) { Fail "mt5_tester_recovery_checkpoint_invalid" }
        } elseif ($RecoveryMode -ceq "completed") {
            if (-not $resultExists -or $reportExists -or $reportProofExists) { Fail "mt5_tester_recovery_checkpoint_invalid" }
            $resultCheckpoint = Get-ExistingPngCheckpoint $Request.resultScreenshotPath $Request.testerResultSha256 "mt5_tester_recovery_checkpoint_mismatch"
        } else {
            if (-not $resultExists -or -not $reportExists -or -not $reportProofExists) { Fail "mt5_tester_recovery_checkpoint_invalid" }
            $resultCheckpoint = Get-ExistingPngCheckpoint $Request.resultScreenshotPath $Request.testerResultSha256 "mt5_tester_recovery_checkpoint_mismatch"
            $reportProofCheckpoint = Get-ExistingPngCheckpoint $Request.reportScreenshotPath $Request.testerReportScreenshotSha256 "mt5_tester_recovery_checkpoint_mismatch"
        }
    }

    $script:FailureCheckpoint = "tester_state_readback"
    Set-Foreground $TerminalProcess
    $autoBefore = Get-AlgoTradingState $TerminalRoot
    $verifiedIds = Assert-RequiredControls $Request
    $configured = $null
    $transitionEvidence = $null
    $completionEvidence = $null
    if ($RecoveryMode -ceq "none") {
        $configured = Configure-Tester $Request $Optimize
        Capture-BoundTerminalWindow $Request ([string]$Request.settingsScreenshotPath)
        $start = $configured.controls.start
        $monitor = New-TesterStartMonitor $start "mt5_tester_start_monitor_unavailable"
        if ((Read-TesterStartState $start "mt5_tester_not_idle") -cne "Start") { Fail "mt5_tester_not_idle" }
        try {
            Write-StartBoundary $Request
            [void](Assert-StartBoundary $Request)
            Invoke-TesterStartOnce $start $monitor "mt5_tester_start_failed"
            # A successful PostMessage is the durable one-shot dispatch
            # receipt.  Persist it before any monitor/readback work so a fast
            # run or process crash cannot leave a consumed Start recoverable
            # only by an unsafe second click.
            Write-DispatchConfirmation $Request
            $dispatchConfirmationSha256 = Assert-DispatchConfirmation $Request
            $transitionEvidence = Wait-TesterCompletion $start ([int]$Request.timeoutSeconds) $false $monitor $Request $Optimize $configured
        } finally { if ($null -ne $monitor) { $monitor.Dispose() } }
        Capture-BoundTerminalWindow $Request ([string]$Request.resultScreenshotPath)
    } elseif ($RecoveryMode -ceq "in_flight") {
        $running = Get-BoundTesterControlSet $Request
        $start = $running.controls.start
        $monitor = New-TesterStartMonitor $start "mt5_tester_start_monitor_unavailable"
        try { $transitionEvidence = Wait-TesterCompletion $start ([int]$Request.timeoutSeconds) $true $monitor }
        finally { if ($null -ne $monitor) { $monitor.Dispose() } }
        $configured = Read-And-VerifyConfiguredTester $Request $Optimize
        if ([string]$transitionEvidence -ceq "idle_after_dispatch_clean_log_completion") {
            $completionEvidence = Assert-TesterCleanCompletion $Request $Optimize $configured
        }
        Capture-BoundTerminalWindow $Request ([string]$Request.resultScreenshotPath)
    } else {
        $configured = Read-And-VerifyConfiguredTester $Request $Optimize
        $transitionEvidence = if ($RecoveryMode -ceq "completed") { "completed_result_checkpoint_after_dispatch" } else { "collected_report_checkpoint_after_dispatch" }
    }
    if ($Optimize) { $verifiedIds["criterion"] = $criterionId }
    if ([string]$transitionEvidence -cnotin @("native_event_stop_then_start", "polled_stop_then_start", "fresh_exact_log_completion_after_dispatch", "idle_after_dispatch_clean_log_completion", "completed_result_checkpoint_after_dispatch", "collected_report_checkpoint_after_dispatch")) { Fail "mt5_tester_transition_unverified" }
    # Start -> Stop -> Start is only a UI transition.  A Core crash/disconnect
    # produces the same transition, so bind success to a fresh, post-boundary
    # tester-log start record plus an exact clean-completion record before any
    # report tab/export can be trusted.
    if ($null -eq $completionEvidence) { $completionEvidence = Assert-TesterCleanCompletion $Request $Optimize $configured }

    $script:FailureCheckpoint = "tester_evidence_binding"
    $settingsEvidence = Get-ExistingPngCheckpoint $Request.settingsScreenshotPath $(if ($recovering) { $Request.testerSettingsSha256 } else { $null }) "mt5_tester_recovery_checkpoint_mismatch"
    $resultEvidence = Get-ExistingPngCheckpoint $Request.resultScreenshotPath $(if ($RecoveryMode -in @("completed", "collected")) { $Request.testerResultSha256 } else { $null }) "mt5_tester_recovery_checkpoint_mismatch"
    $completionCheckpoint = $null
    if ($Optimize) {
        $script:FailureCheckpoint = "optimization_completion_binding"
        $completionCheckpoint = if ($RecoveryMode -in @("completed", "collected")) {
            Assert-OptimizationCompletionCheckpoint $Request ([string]$settingsEvidence.sha256) ([string]$resultEvidence.sha256) ([string]$dispatchConfirmationSha256)
        } else {
            Write-OptimizationCompletionCheckpoint $Request ([string]$settingsEvidence.sha256) ([string]$resultEvidence.sha256) ([string]$dispatchConfirmationSha256)
        }
    }
    $tabs = $configured.controls.tabs
    $tabNames = @((Resolve-TesterReportTabNameExact $tabs $Optimize "mt5_report_tab_not_verified"))
    if ($RecoveryMode -ceq "collected") {
        $script:FailureCheckpoint = "report_checkpoint_binding"
        $reportEvidence = Get-ExistingReportEvidence $Request $tabNames ([string]$Request.testerReportPath) $Request.testerReportSha256
        [void](Get-ExistingPngCheckpoint $Request.reportScreenshotPath $Request.testerReportScreenshotSha256 "mt5_tester_recovery_checkpoint_mismatch")
    } else {
        if ([System.IO.File]::Exists([string]$Request.testerReportPath) -or [System.IO.File]::Exists([string]$Request.reportScreenshotPath)) { Fail "mt5_tester_recovery_checkpoint_invalid" }
        $script:FailureCheckpoint = "report_export"
        $reportEvidence = Save-VisibleReport $Request $TerminalProcess $tabs $tabNames ([string]$Request.testerReportExportPath) ([string]$Request.testerReportPath)
        $script:FailureCheckpoint = "report_screenshot"
        Capture-BoundTerminalWindow $Request ([string]$Request.reportScreenshotPath)
    }
    $script:FailureCheckpoint = "post_report_guard"
    $autoAfter = Get-AlgoTradingState $TerminalRoot
    if ($autoBefore -ne $autoAfter) { Fail "mt5_algo_trading_state_changed" }
    $pre = New-Binding $TerminalProcess "strategy_tester" $autoBefore $TerminalRoot
    $post = New-Binding $TerminalProcess "strategy_tester" $autoAfter $TerminalRoot
    $resolved = [ordered]@{
        schemaVersion = "ea-factory-resolved-tester-settings-v1"
        expertFileName = [string]$Request.expertFileName
        symbol = [string]$configured.symbol
        period = [string]$Request.testerSettings.period
        model = [string]$Request.testerSettings.model
        spread = "current"
        useDate = [bool]$Request.testerSettings.useDate
        fromDate = $configured.fromDate
        toDate = $configured.toDate
        deposit = [double]$configured.deposit
        visualMode = (-not $Optimize)
        optimizationEnabled = $Optimize
        shutdownTerminalAfterTest = $false
    }
    return [ordered]@{
        schemaVersion = $ResultSchema; ok = $true; action = [string]$Request.action; operationId = [string]$Request.operationId
        startInvoked = (-not $recovering); recoveredWithoutStart = $recovering
        executionObservedRunning = ($RecoveryMode -in @("none", "in_flight"))
        completedResultCheckpointReused = ($RecoveryMode -in @("completed", "collected"))
        completedReportCheckpointReused = ($RecoveryMode -ceq "collected")
        testerCompleted = $true
        testerCompletionObservation = if ($RecoveryMode -ceq "in_flight") { "recovery_stop_transition_observed" } elseif ($RecoveryMode -ceq "completed") { "recovery_completed_checkpoint_observed" } elseif ($RecoveryMode -ceq "collected") { "recovery_collected_checkpoint_observed" } else { "start_stop_transition_observed" }
        testerCompletionEvidence = $completionEvidence
        strategyExecutionProof = $script:StrategyExecutionProof
        freshResultEvidenceCaptured = $true; testerRunTransitionObserved = $true; testerRunTransitionEvidence = [string]$transitionEvidence
        exactExpertVerified = $true; selectedExpertReadback = [string]$configured.expert
        expertCatalogRefreshEvidence = $configured.expertCatalogRefresh
        deployedExpertSha256 = Get-Sha256 $expert; startBoundaryCommitted = $true
        startBoundarySha256 = [string]$Request.startBoundarySha256; actionRequestDigest = [string]$Request.actionRequestDigest
        dispatchConfirmationSha256 = [string]$dispatchConfirmationSha256
        optimizationCompletionCheckpointSha256 = if ($null -ne $completionCheckpoint) { [string]$completionCheckpoint.sha256 } else { $null }
        reportCreatedFresh = [bool]$reportEvidence.createdFresh; reportSha256 = [string]$reportEvidence.sha256
        reportByteSize = [long]$reportEvidence.byteSize; reportCreatedAt = [string]$reportEvidence.createdAt
        reportLastWriteAt = [string]$reportEvidence.lastWriteAt; reportFormat = [string]$reportEvidence.format
        reportTabName = [string]$reportEvidence.tabName
        autoTradingToggled = $false; chartAttached = $false; liveTradingExecuted = $false; terminalClosedByAdapter = $false
        automationControlsVerified = $verifiedIds; optimizationRangesApplied = $Optimize
        optimizationRangesReadbackVerified = $Optimize
        inputPresetSetSha256 = if ($null -ne $configured.inputEvidence) { [string]$configured.inputEvidence.sourceSetSha256 } else { $null }
        inputPresetReadbackSetSha256 = if ($null -ne $configured.inputEvidence) { [string]$configured.inputEvidence.readbackSetSha256 } else { $null }
        inputPresetReadbackEntriesDigest = if ($null -ne $configured.inputEvidence) { [string]$configured.inputEvidence.readbackEntriesDigest } else { $null }
        baselineReadbackSetSha256 = if ($null -ne $configured.baselineEvidence) { [string]$configured.baselineEvidence.readbackSetSha256 } else { $null }
        baselineReadbackEntriesDigest = if ($null -ne $configured.baselineEvidence) { [string]$configured.baselineEvidence.readbackEntriesDigest } else { $null }
        inputReadbackSetSha256 = if ($null -ne $configured.optimizationEvidence) { [string]$configured.optimizationEvidence.readbackSetSha256 } else { $null }
        optimizationReadbackEntriesDigest = if ($null -ne $configured.optimizationEvidence) { [string]$configured.optimizationEvidence.readbackEntriesDigest } else { $null }
        resolvedTesterSettings = $resolved; processBinding = $pre; postProcessBinding = $post
    }
}

$request = $null
try {
    $requestFull = [System.IO.Path]::GetFullPath($RequestPath)
    $responseFull = [System.IO.Path]::GetFullPath($ResponsePath)
    if (-not [System.IO.File]::Exists($requestFull) -or [System.IO.File]::Exists($responseFull)) { Fail "visible_ui_request_invalid" }
    $request = Get-Content -LiteralPath $requestFull -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([string]$request.schemaVersion -cne $RequestSchema -or [string]$request.platform -cne "mt5") { Fail "visible_ui_request_contract_invalid" }
    Enter-OperationMutex ([string]$request.operationId)
    $terminalPath = Get-FullFile $request.terminalPath "terminal64.exe" "mt5_terminal_path_invalid"
    $compilerPath = Get-FullFile $request.compilerPath "MetaEditor64.exe" "mt5_metaeditor_path_invalid"
    if ([System.IO.Path]::GetDirectoryName($terminalPath) -ine [System.IO.Path]::GetDirectoryName($compilerPath)) { Fail "mt5_install_binding_mismatch" }
    $dataPath = [System.IO.Path]::GetFullPath([string]$request.dataPath)
    if (-not [System.IO.Directory]::Exists([System.IO.Path]::Combine($dataPath, "MQL5"))) { Fail "mt5_data_binding_invalid" }
    Enter-TerminalMutex $terminalPath $dataPath
    $expectedPid = if ($request.PSObject.Properties.Name -contains "expectedTerminalProcessId") { [int]$request.expectedTerminalProcessId } else { 0 }
    $expectedWindow = if ($request.PSObject.Properties.Name -contains "expectedTerminalWindowHandle") { [long]$request.expectedTerminalWindowHandle } else { 0 }
    $TerminalProcess = Get-ExactTerminal $terminalPath $expectedPid $expectedWindow
    [IntPtr]$initialRootHandle = if ($expectedWindow -gt 0) { [IntPtr][long]$expectedWindow } else { Get-TerminalMainWindowExact $TerminalProcess }
    if ($initialRootHandle -eq [IntPtr]::Zero) { Fail "mt5_selected_terminal_not_ready" }
    $TerminalRoot = Get-Root $TerminalProcess $initialRootHandle
    $script:TerminalRootHandle = [IntPtr]$TerminalRoot.Current.NativeWindowHandle
    if ($script:TerminalRootHandle -eq [IntPtr]::Zero -or
        ($expectedWindow -gt 0 -and $script:TerminalRootHandle.ToInt64() -ne $expectedWindow)) {
        Fail "mt5_terminal_window_changed"
    }
    # Capability probes intentionally begin without a process/window signature.
    # Get-ExactTerminal has already proved there is exactly one visible terminal
    # at the Backend-resolved executable path, so bind the rest of this probe to
    # that exact PID/root.  All mutating actions must arrive with the signed
    # values returned by this probe and are never allowed to self-bind.
    if ([string]$request.action -ceq "probe") {
        if (-not ($request.PSObject.Properties.Name -contains "expectedTerminalProcessId")) {
            $request | Add-Member -NotePropertyName expectedTerminalProcessId -NotePropertyValue ([int]$TerminalProcess.Id)
        }
        if (-not ($request.PSObject.Properties.Name -contains "expectedTerminalWindowHandle")) {
            $request | Add-Member -NotePropertyName expectedTerminalWindowHandle -NotePropertyValue ([long]$script:TerminalRootHandle.ToInt64())
        }
    } elseif ($expectedPid -le 0 -or $expectedWindow -le 0) {
        Fail "mt5_terminal_binding_missing"
    }
    switch ([string]$request.action) {
        "probe" {
            $verified = [ordered]@{}
            $testerStartState = $null
            if ([string]$request.stageId -in @("backtest_recheck", "optimize")) {
                $verified = Assert-RequiredControls $request
                $boundProbe = Get-BoundTesterControlSet $request ([IntPtr]$script:TerminalRootHandle) $false
                $testerStartState = Read-TesterStartState $boundProbe.controls.start "mt5_tester_start_state_unverified"
            }
            $probeRoot = Get-BoundTerminalRoot $request ([IntPtr]$script:TerminalRootHandle)
            $result = [ordered]@{ schemaVersion = $ResultSchema; ok = $true; action = "probe"; operationId = [string]$request.operationId; terminalProbe = New-Probe $TerminalProcess $probeRoot; automationControlsVerified = $verified; testerStartState = $testerStartState }
        }
        "post_probe" {
            if ([string]$request.stageId -notin @("backtest_recheck", "optimize")) { Fail "visible_stage_unsupported" }
            # This proof is deliberately read-only.  It must not normalize or
            # select a Tester tab, close a combo, reveal a pane, or dispatch
            # Start.  It only rebinds the already-visible tester controls and
            # records the exact idle process/window state after report parsing.
            $minimal = Get-MinimalBoundTesterControlSet $request ([IntPtr]$script:TerminalRootHandle) $false
            [IntPtr]$startHandle = Assert-NativeControl $minimal.controls.start "Button" "mt5_tester_start_state_unverified"
            $testerStartState = Read-TesterStartState $minimal.controls.start "mt5_tester_start_state_unverified" $startHandle
            if ($testerStartState -cne "Start") { Fail "mt5_tester_post_process_probe_invalid" }
            $autoTradingState = Get-AlgoTradingState $minimal.root
            $processBinding = New-Binding $TerminalProcess "strategy_tester" $autoTradingState $minimal.root
            $terminalProbe = New-BoundProbe $TerminalProcess $minimal.root
            $testerStartStateAfter = Read-TesterStartState $minimal.controls.start "mt5_tester_start_state_unverified" $startHandle
            $autoTradingStateAfter = Get-AlgoTradingState $minimal.root
            if ($testerStartStateAfter -cne "Start" -or $autoTradingStateAfter -ne $autoTradingState) {
                Fail "mt5_tester_post_process_probe_invalid"
            }
            $result = [ordered]@{
                schemaVersion = $ResultSchema
                ok = $true
                action = "post_probe"
                operationId = [string]$request.operationId
                terminalProbe = $terminalProbe
                testerStartState = $testerStartStateAfter
                processBinding = $processBinding
            }
        }
        "diagnose_compile" { $result = Read-CompileDiagnostic $request }
        "diagnose_tester" { $result = Read-TesterDiagnostic $request }
        "compile" { $result = Invoke-Compile $request $false }
        "recover_compile" { $result = Invoke-Compile $request $true }
        "backtest" { $result = Invoke-Tester $request $false "none" }
        "collect_backtest" { $result = Invoke-Tester $request $false "in_flight" }
        "recover_completed_backtest" { $result = Invoke-Tester $request $false "completed" }
        "recover_collected_backtest" { $result = Invoke-Tester $request $false "collected" }
        "optimize" { $result = Invoke-Tester $request $true "none" }
        "collect_optimization" { $result = Invoke-Tester $request $true "in_flight" }
        "recover_completed_optimization" { $result = Invoke-Tester $request $true "completed" }
        "recover_collected_optimization" { $result = Invoke-Tester $request $true "collected" }
        default { Fail "visible_ui_action_unsupported" }
    }
    Write-JsonExclusive $responseFull $result
    Exit-TerminalMutex
    Exit-OperationMutex
    exit 0
} catch {
    $code = [string]$_.Exception.Message
    if ($code -notmatch "^[a-z0-9_]{3,100}$") {
        $checkpoint = [string]$script:FailureCheckpoint
        $failureLine = [int]$_.InvocationInfo.ScriptLineNumber
        $code = if ($checkpoint -ceq "tester_request_validation") {
            # This checkpoint ends before any Tester state read or native Start
            # boundary. Keep the code stable so the bridge can prove an
            # explicit retry is pre-Start even when source line numbers move.
            "visible_ui_tester_request_validation_failed"
        } elseif ($checkpoint -match "^[a-z0-9_]{3,70}$") {
            if ($failureLine -gt 0) {
                "visible_ui_$($checkpoint)_line_$($failureLine)_failed"
            } else {
                "visible_ui_$($checkpoint)_failed"
            }
        } else {
            "visible_ui_action_failed"
        }
    }
    try {
        $operationId = if ($null -ne $request) { [string]$request.operationId } else { "unknown" }
        $action = if ($null -ne $request) { [string]$request.action } else { "unknown" }
        $failureResult = [ordered]@{ schemaVersion = $ResultSchema; ok = $false; action = $action; operationId = $operationId; reasonCode = $code }
        if ($action -ceq "probe" -and $null -ne $script:TesterPaneFailureDiagnostic -and
            $script:TesterPaneFailureDiagnostic.reasonCode -ceq $code) {
            $failureResult["testerPaneFailure"] = $script:TesterPaneFailureDiagnostic
            $script:TesterPaneFailureDiagnostic = $null
        }
        if ($action -ceq "diagnose_compile" -and $code -ceq "metaeditor_clipboard_restore_mismatch") {
            $mismatchMetadata = [MetafxMetaEditorCompileNative]::ConsumeClipboardRestoreMismatchMetadata()
            if ($null -ne $mismatchMetadata) {
                $failureResult["clipboardMismatch"] = $mismatchMetadata
            }
        }
        Write-JsonExclusive ([System.IO.Path]::GetFullPath($ResponsePath)) $failureResult
    } catch {}
    Exit-TerminalMutex
    Exit-OperationMutex
    exit 1
}
