param(
    [Parameter(Mandatory = $true)][string]$RequestPath,
    [Parameter(Mandatory = $true)][string]$ResponsePath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Accessibility

Add-Type @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class MetafxVisibleNative {
    public const int WM_COMMAND = 0x0111;
    public const int WM_KEYDOWN = 0x0100;
    public const int WM_KEYUP = 0x0101;
    public const int WM_LBUTTONDOWN = 0x0201;
    public const int WM_LBUTTONUP = 0x0202;
    public const int WM_GETTEXT = 0x000D;
    public const int WM_GETTEXTLENGTH = 0x000E;
    public const int WM_SETTEXT = 0x000C;
    public const int BM_CLICK = 0x00F5;
    public const int BM_GETCHECK = 0x00F0;
    public const int CB_GETCOUNT = 0x0146;
    public const int CB_GETCURSEL = 0x0147;
    public const int CB_GETLBTEXT = 0x0148;
    public const int CB_GETLBTEXTLEN = 0x0149;
    public const int CB_SETCURSEL = 0x014E;
    public const int CB_SHOWDROPDOWN = 0x014F;
    public const int MN_GETHMENU = 0x01E1;
    public const int TB_GETSTATE = 0x0412;
    public const int TCM_GETITEMCOUNT = 0x1304;
    public const int TCM_GETCURSEL = 0x130B;
    public const int TVM_GETNEXTITEM = 0x110A;
    public const int TVM_ENSUREVISIBLE = 0x1114;
    public const int TVGN_CARET = 0x0009;
    public const int GWL_STYLE = -16;
    public const int WS_DISABLED = 0x08000000;
    public const int LVS_TYPEMASK = 0x0003;
    public const int LVS_REPORT = 0x0001;
    public const int LVS_OWNERDATA = 0x1000;
    public const int LVM_GETITEMCOUNT = 0x1004;
    public const int LVM_GETHEADER = 0x101F;
    public const int CBS_OWNERDRAWFIXED = 0x0010;
    public const int CBS_OWNERDRAWVARIABLE = 0x0020;
    public const int CBS_HASSTRINGS = 0x0200;
    public const int CBN_SELCHANGE = 1;
    public const uint MF_GRAYED = 0x0001;
    public const uint MF_DISABLED = 0x0002;
    public const uint MF_BYPOSITION = 0x0400;
    public const uint MF_SEPARATOR = 0x0800;
    public const uint SMTO_ABORTIFHUNG = 0x0002;
    public const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    public const uint MOUSEEVENTF_LEFTUP = 0x0004;
    public const uint MOUSEEVENTF_RIGHTDOWN = 0x0008;
    public const uint MOUSEEVENTF_RIGHTUP = 0x0010;
    public const uint KEYEVENTF_KEYUP = 0x0002;
    public const uint KEYEVENTF_UNICODE = 0x0004;
    public const ushort VK_TAB = 0x09;
    public const ushort VK_CONTROL = 0x11;
    public const ushort VK_A = 0x41;
    public const int SW_RESTORE = 9;
    public const uint GA_ROOT = 2;

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [StructLayout(LayoutKind.Sequential)]
    public struct POINT { public int X; public int Y; }
    [StructLayout(LayoutKind.Sequential)]
    public struct MOUSEINPUT {
        public int dx;
        public int dy;
        public uint mouseData;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct INPUT {
        public uint type;
        public MOUSEINPUT mi;
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct KEYBDINPUT {
        public ushort wVk;
        public ushort wScan;
        public uint dwFlags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Explicit)]
    public struct INPUTUNION {
        [FieldOffset(0)] public MOUSEINPUT mi;
        [FieldOffset(0)] public KEYBDINPUT ki;
    }
    [StructLayout(LayoutKind.Sequential)]
    public struct UNIVERSALINPUT {
        public uint type;
        public INPUTUNION value;
    }

    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr SetActiveWindow(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr SetFocus(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool PostMessage(IntPtr hWnd, int message, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll")]
    public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool AttachThreadInput(uint sourceThreadId, uint targetThreadId, bool attach);
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr GetAncestor(IntPtr hWnd, uint gaFlags);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool GetCursorPos(out POINT point);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint SendInput(uint count, INPUT[] inputs, int size);
    [DllImport("user32.dll", EntryPoint="SendInput", SetLastError=true)]
    public static extern uint SendKeyboardInput(
        uint count, UNIVERSALINPUT[] inputs, int size);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int maximum);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maximum);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd, int message, IntPtr wParam, IntPtr lParam,
        uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd, int message, IntPtr wParam, StringBuilder lParam,
        uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern IntPtr SendMessageTimeout(
        IntPtr hWnd, int message, IntPtr wParam,
        [MarshalAs(UnmanagedType.LPWStr)] string lParam,
        uint flags, uint timeout, out IntPtr result);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern int GetWindowLong(IntPtr hWnd, int index);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr GetParent(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern int GetDlgCtrlID(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool IsWindow(IntPtr hWnd);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr GetMenu(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern int GetMenuItemCount(IntPtr menu);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr GetSubMenu(IntPtr menu, int position);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint GetMenuItemID(IntPtr menu, int position);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern uint GetMenuState(IntPtr menu, uint item, uint flags);
    [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern int GetMenuString(IntPtr menu, uint item, StringBuilder text, int maximum, uint flags);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool GetMenuItemRect(IntPtr window, IntPtr menu, uint item, out RECT rect);

    public static IntPtr[] GetVisibleTopLevelWindows(int processId, string className) {
        List<IntPtr> handles = new List<IntPtr>();
        EnumWindows(delegate(IntPtr handle, IntPtr ignored) {
            uint owner;
            GetWindowThreadProcessId(handle, out owner);
            if (owner != (uint)processId || !IsWindowVisible(handle)) return true;
            StringBuilder currentClass = new StringBuilder(256);
            GetClassName(handle, currentClass, currentClass.Capacity);
            if (String.Equals(currentClass.ToString(), className, StringComparison.Ordinal)) {
                handles.Add(handle);
            }
            return true;
        }, IntPtr.Zero);
        return handles.ToArray();
    }

    public static bool SendMouseClick(bool rightButton) {
        INPUT[] inputs = new INPUT[2];
        inputs[0].type = 0;
        inputs[0].mi.dwFlags = rightButton
            ? MOUSEEVENTF_RIGHTDOWN
            : MOUSEEVENTF_LEFTDOWN;
        inputs[1].type = 0;
        inputs[1].mi.dwFlags = rightButton
            ? MOUSEEVENTF_RIGHTUP
            : MOUSEEVENTF_LEFTUP;
        return SendInput(
            (uint)inputs.Length,
            inputs,
             Marshal.SizeOf(typeof(INPUT))) == (uint)inputs.Length;
    }

    private static UNIVERSALINPUT VirtualKey(ushort key, uint flags) {
        UNIVERSALINPUT input = new UNIVERSALINPUT();
        input.type = 1;
        input.value.ki.wVk = key;
        input.value.ki.dwFlags = flags;
        return input;
    }

    private static UNIVERSALINPUT UnicodeKey(char value, uint flags) {
        UNIVERSALINPUT input = new UNIVERSALINPUT();
        input.type = 1;
        input.value.ki.wScan = value;
        input.value.ki.dwFlags = KEYEVENTF_UNICODE | flags;
        return input;
    }

    public static bool ReplaceFocusedText(string value) {
        if (value == null || value.Length == 0 || value.Length > 2048) return false;
        List<UNIVERSALINPUT> inputs = new List<UNIVERSALINPUT>(4 + value.Length * 2);
        inputs.Add(VirtualKey(VK_CONTROL, 0));
        inputs.Add(VirtualKey(VK_A, 0));
        inputs.Add(VirtualKey(VK_A, KEYEVENTF_KEYUP));
        inputs.Add(VirtualKey(VK_CONTROL, KEYEVENTF_KEYUP));
        foreach (char character in value) {
            inputs.Add(UnicodeKey(character, 0));
            inputs.Add(UnicodeKey(character, KEYEVENTF_KEYUP));
        }
        UNIVERSALINPUT[] payload = inputs.ToArray();
        return SendKeyboardInput(
            (uint)payload.Length,
            payload,
            Marshal.SizeOf(typeof(UNIVERSALINPUT))) == (uint)payload.Length;
    }

    public static bool SendVirtualKeyPress(ushort key) {
        UNIVERSALINPUT[] inputs = new UNIVERSALINPUT[2];
        inputs[0] = VirtualKey(key, 0);
        inputs[1] = VirtualKey(key, KEYEVENTF_KEYUP);
        return SendKeyboardInput(
            (uint)inputs.Length,
            inputs,
            Marshal.SizeOf(typeof(UNIVERSALINPUT))) == (uint)inputs.Length;
    }

}
"@

Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Accessibility;

public static class MetafxVisibleMsaa {
    private const uint OBJID_CLIENT = 0xFFFFFFFC;
    private const int SELFLAG_TAKEFOCUS = 0x1;
    private const int SELFLAG_TAKESELECTION = 0x2;
    private const int STATE_SYSTEM_SELECTED = 0x2;
    private const int STATE_SYSTEM_INVISIBLE = 0x8000;
    private const int STATE_SYSTEM_OFFSCREEN = 0x10000;
    private const int NAVDIR_LEFT = 0x3;
    private const int MaximumNodes = 8192;
    private const int MaximumDepth = 48;

    private sealed class NodeRef {
        public IAccessible Owner;
        public object ChildId;
        public IAccessible Child;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct Rect {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    private sealed class LocatedNode {
        public NodeRef Node;
        public int Left;
        public int Top;
        public int Width;
        public int Height;
    }

    [DllImport("oleacc.dll")]
    private static extern int AccessibleObjectFromWindow(
        IntPtr hwnd,
        uint objectId,
        ref Guid interfaceId,
        [In, Out, MarshalAs(UnmanagedType.Interface)] ref object accessibleObject);

    [DllImport("oleacc.dll")]
    private static extern int AccessibleChildren(
        IAccessible container,
        int start,
        int count,
        [Out, MarshalAs(UnmanagedType.LPArray, SizeParamIndex=2)] object[] children,
        out int obtained);

    [DllImport("user32.dll", SetLastError=true)]
    private static extern bool GetWindowRect(IntPtr handle, out Rect rect);

    private static IAccessible FromHandle(IntPtr handle) {
        object value = null;
        Guid iid = new Guid("618736e0-3c3d-11cf-810c-00aa00389b71");
        int result = AccessibleObjectFromWindow(handle, OBJID_CLIENT, ref iid, ref value);
        if (result < 0 || value == null) return null;
        return value as IAccessible;
    }

    private static string ReadName(NodeRef node) {
        try {
            string value = node.Child != null
                ? node.Child.get_accName(0)
                : node.Owner.get_accName(node.ChildId);
            return (value ?? String.Empty).Trim();
        } catch { return String.Empty; }
    }

    private static int ReadRole(NodeRef node) {
        try {
            object value = node.Child != null
                ? node.Child.get_accRole(0)
                : node.Owner.get_accRole(node.ChildId);
            return Convert.ToInt32(value);
        } catch { return -1; }
    }

    private static void Walk(
        IAccessible container,
        string expected,
        List<NodeRef> matches,
        ref int visited,
        int depth) {
        if (container == null || depth > MaximumDepth || visited >= MaximumNodes) return;
        int count;
        try { count = container.accChildCount; }
        catch { return; }
        if (count < 1 || count > MaximumNodes) return;
        object[] children = new object[count];
        int obtained;
        int result;
        try { result = AccessibleChildren(container, 0, count, children, out obtained); }
        catch { return; }
        if (result < 0 || obtained < 0 || obtained > count) return;
        for (int index = 0; index < obtained && visited < MaximumNodes; index++) {
            visited++;
            IAccessible child = children[index] as IAccessible;
            NodeRef node = new NodeRef {
                Owner = container,
                ChildId = child == null ? children[index] : (object)0,
                Child = child
            };
            if (String.Equals(ReadName(node), expected, StringComparison.OrdinalIgnoreCase)) {
                matches.Add(node);
            }
            IAccessible nested = child;
            if (nested == null) {
                try { nested = container.get_accChild(node.ChildId) as IAccessible; }
                catch { nested = null; }
            }
            if (nested != null) Walk(nested, expected, matches, ref visited, depth + 1);
        }
    }

    private static List<NodeRef> FindExact(IntPtr handle, string expected) {
        List<NodeRef> matches = new List<NodeRef>();
        IAccessible root = FromHandle(handle);
        if (root == null || String.IsNullOrWhiteSpace(expected)) return matches;
        int visited = 0;
        Walk(root, expected.Trim(), matches, ref visited, 0);
        return matches;
    }

    private static NodeRef Navigate(NodeRef node, int direction) {
        if (node == null) return null;
        IAccessible basis = node.Child != null ? node.Child : node.Owner;
        object childId = node.Child != null ? (object)0 : node.ChildId;
        if (basis == null) return null;
        object value;
        try { value = basis.accNavigate(direction, childId); }
        catch { return null; }
        if (value == null) return null;
        IAccessible child = value as IAccessible;
        return child != null
            ? new NodeRef { Owner = child, ChildId = 0, Child = child }
            : new NodeRef { Owner = basis, ChildId = value, Child = null };
    }

    private static bool ValidPath(string[] path) {
        if (path == null || path.Length < 1 || path.Length > 8) return false;
        foreach (string part in path) {
            if (String.IsNullOrWhiteSpace(part) || part.Trim().Length > 256) return false;
        }
        return true;
    }

    private static bool MatchesExactPath(NodeRef node, string[] path) {
        if (!ValidPath(path) || node == null ||
            !String.Equals(ReadName(node), path[path.Length - 1].Trim(),
                StringComparison.OrdinalIgnoreCase)) return false;
        for (int index = path.Length - 2; index >= 0; index--) {
            node = Navigate(node, NAVDIR_LEFT);
            if (node == null ||
                !String.Equals(ReadName(node), path[index].Trim(),
                    StringComparison.OrdinalIgnoreCase)) return false;
        }
        return true;
    }

    private static List<NodeRef> FindExactPath(IntPtr handle, string[] path) {
        List<NodeRef> matches = new List<NodeRef>();
        if (!ValidPath(path)) return matches;
        foreach (NodeRef node in FindExact(handle, path[path.Length - 1].Trim())) {
            if (MatchesExactPath(node, path)) matches.Add(node);
        }
        return matches;
    }

    private static bool SelectNode(NodeRef node) {
        if (node == null) return false;
        try {
            if (node.Child != null) {
                node.Child.accSelect(SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, 0);
                return (Convert.ToInt32(node.Child.get_accState(0)) &
                    STATE_SYSTEM_SELECTED) != 0;
            }
            node.Owner.accSelect(
                SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                node.ChildId);
            return (Convert.ToInt32(node.Owner.get_accState(node.ChildId)) &
                STATE_SYSTEM_SELECTED) != 0;
        } catch { return false; }
    }

    private static bool IsNodeSelected(NodeRef node) {
        if (node == null) return false;
        try {
            object state = node.Child != null
                ? node.Child.get_accState(0)
                : node.Owner.get_accState(node.ChildId);
            return (Convert.ToInt32(state) & STATE_SYSTEM_SELECTED) != 0;
        } catch { return false; }
    }

    private static bool TryLocate(NodeRef node, out int left, out int top, out int width, out int height) {
        left = top = width = height = 0;
        try {
            object state = node.Child != null
                ? node.Child.get_accState(0)
                : node.Owner.get_accState(node.ChildId);
            int flags = Convert.ToInt32(state);
            if ((flags & (STATE_SYSTEM_INVISIBLE | STATE_SYSTEM_OFFSCREEN)) != 0) return false;
            if (node.Child != null) {
                node.Child.accLocation(out left, out top, out width, out height, 0);
            } else {
                node.Owner.accLocation(out left, out top, out width, out height, node.ChildId);
            }
            return width > 1 && height > 1;
        } catch { return false; }
    }

    private static void WalkFullyVisible(
        IAccessible container,
        Rect bounds,
        List<LocatedNode> matches,
        ref int visited,
        int depth) {
        if (container == null || depth > MaximumDepth || visited >= MaximumNodes) return;
        int count;
        try { count = container.accChildCount; }
        catch { return; }
        if (count < 1 || count > MaximumNodes) return;
        object[] children = new object[count];
        int obtained;
        int result;
        try { result = AccessibleChildren(container, 0, count, children, out obtained); }
        catch { return; }
        if (result < 0 || obtained < 0 || obtained > count) return;
        for (int index = 0; index < obtained && visited < MaximumNodes; index++) {
            visited++;
            IAccessible child = children[index] as IAccessible;
            NodeRef node = new NodeRef {
                Owner = container,
                ChildId = child == null ? children[index] : (object)0,
                Child = child
            };
            int left, top, width, height;
            if (!String.IsNullOrWhiteSpace(ReadName(node)) &&
                TryLocate(node, out left, out top, out width, out height) &&
                left >= bounds.Left && top >= bounds.Top &&
                left + width <= bounds.Right && top + height <= bounds.Bottom) {
                matches.Add(new LocatedNode {
                    Node = node,
                    Left = left,
                    Top = top,
                    Width = width,
                    Height = height
                });
            }
            IAccessible nested = child;
            if (nested == null) {
                try { nested = container.get_accChild(node.ChildId) as IAccessible; }
                catch { nested = null; }
            }
            if (nested != null) WalkFullyVisible(nested, bounds, matches, ref visited, depth + 1);
        }
    }

    public static int CountExactName(IntPtr handle, string expected) {
        return FindExact(handle, expected).Count;
    }

    public static int CountExactPath(IntPtr handle, string[] path) {
        return FindExactPath(handle, path).Count;
    }

    public static bool SelectUniqueExactPath(IntPtr handle, string[] path) {
        List<NodeRef> matches = FindExactPath(handle, path);
        return matches.Count == 1 && SelectNode(matches[0]);
    }

    public static bool IsUniqueExactPathSelected(IntPtr handle, string[] path) {
        List<NodeRef> matches = FindExactPath(handle, path);
        return matches.Count == 1 && IsNodeSelected(matches[0]);
    }

    public static bool SelectUniqueExactName(IntPtr handle, string expected) {
        List<NodeRef> matches = FindExact(handle, expected);
        if (matches.Count != 1) return false;
        NodeRef node = matches[0];
        try {
            if (node.Child != null) {
                node.Child.accSelect(SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, 0);
                object state = node.Child.get_accState(0);
                return (Convert.ToInt32(state) & STATE_SYSTEM_SELECTED) != 0;
            }
            node.Owner.accSelect(
                SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                node.ChildId);
            object childState = node.Owner.get_accState(node.ChildId);
            return (Convert.ToInt32(childState) & STATE_SYSTEM_SELECTED) != 0;
        } catch { return false; }
    }

    public static bool TrySelectUniqueExactNameCenter(
        IntPtr handle,
        string expected,
        int expectedRole,
        out int x,
        out int y) {
        x = y = 0;
        List<NodeRef> matches = FindExact(handle, expected);
        Rect bounds;
        if (matches.Count != 1 || !GetWindowRect(handle, out bounds) ||
            bounds.Right <= bounds.Left || bounds.Bottom <= bounds.Top) return false;
        NodeRef node = matches[0];
        if (ReadRole(node) != expectedRole) return false;
        int left, top, width, height;
        if (!TryLocate(node, out left, out top, out width, out height) ||
            left < bounds.Left || top < bounds.Top ||
            left + width > bounds.Right || top + height > bounds.Bottom) return false;
        try {
            if (node.Child != null) {
                node.Child.accSelect(SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, 0);
                object state = node.Child.get_accState(0);
                if ((Convert.ToInt32(state) & STATE_SYSTEM_SELECTED) == 0) return false;
            } else {
                node.Owner.accSelect(
                    SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                    node.ChildId);
                object state = node.Owner.get_accState(node.ChildId);
                if ((Convert.ToInt32(state) & STATE_SYSTEM_SELECTED) == 0) return false;
            }
            x = left + (width / 2);
            y = top + (height / 2);
            return true;
        } catch { return false; }
    }

    public static bool TrySelectFirstFullyVisibleCenter(IntPtr handle, out int x, out int y) {
        x = y = 0;
        IAccessible root = FromHandle(handle);
        Rect bounds;
        if (root == null || !GetWindowRect(handle, out bounds) ||
            bounds.Right <= bounds.Left || bounds.Bottom <= bounds.Top) return false;
        List<LocatedNode> candidates = new List<LocatedNode>();
        int visited = 0;
        WalkFullyVisible(root, bounds, candidates, ref visited, 0);
        if (candidates.Count < 1) return false;
        candidates.Sort(delegate(LocatedNode first, LocatedNode second) {
            int vertical = first.Top.CompareTo(second.Top);
            return vertical != 0 ? vertical : first.Left.CompareTo(second.Left);
        });
        foreach (LocatedNode candidate in candidates) {
            try {
                if (candidate.Node.Child != null) {
                    candidate.Node.Child.accSelect(
                        SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, 0);
                } else {
                    candidate.Node.Owner.accSelect(
                        SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                        candidate.Node.ChildId);
                }
                x = candidate.Left + (candidate.Width / 2);
                y = candidate.Top + (candidate.Height / 2);
                return true;
            } catch { }
        }
        return false;
    }

    public static bool TrySelectFirstFullyVisibleRoleCenter(
        IntPtr handle,
        int expectedRole,
        out int x,
        out int y) {
        x = y = 0;
        IAccessible root = FromHandle(handle);
        Rect bounds;
        if (root == null || !GetWindowRect(handle, out bounds) ||
            bounds.Right <= bounds.Left || bounds.Bottom <= bounds.Top) return false;
        List<LocatedNode> candidates = new List<LocatedNode>();
        int visited = 0;
        WalkFullyVisible(root, bounds, candidates, ref visited, 0);
        candidates.Sort(delegate(LocatedNode first, LocatedNode second) {
            int vertical = first.Top.CompareTo(second.Top);
            return vertical != 0 ? vertical : first.Left.CompareTo(second.Left);
        });
        foreach (LocatedNode candidate in candidates) {
            if (ReadRole(candidate.Node) != expectedRole) continue;
            try {
                if (candidate.Node.Child != null) {
                    candidate.Node.Child.accSelect(
                        SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION, 0);
                } else {
                    candidate.Node.Owner.accSelect(
                        SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                        candidate.Node.ChildId);
                }
                x = candidate.Left + (candidate.Width / 2);
                y = candidate.Top + (candidate.Height / 2);
                return true;
            } catch { }
        }
        return false;
    }

    public static bool SetExactValue(IntPtr handle, string expected) {
        IAccessible accessible = FromHandle(handle);
        if (accessible == null || expected == null) return false;
        try {
            accessible.set_accValue(0, expected);
            string observed = accessible.get_accValue(0) ?? String.Empty;
            return String.Equals(observed.Trim(), expected.Trim(), StringComparison.Ordinal);
        } catch { return false; }
    }
}
"@ -ReferencedAssemblies @("Accessibility.dll")

function Stop-Adapter([string]$Code) {
    throw "METAFX_VISIBLE:$Code"
}

function Write-JsonResult([hashtable]$Value, [int]$ExitCode) {
    $json = $Value | ConvertTo-Json -Depth 16 -Compress
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($ResponsePath, $json, $utf8)
    exit $ExitCode
}

function Get-Sha256Hex([byte[]]$Bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Get-FileSha256Hex([string]$Path) {
    $stream = $null
    $sha = $null
    try {
        $stream = New-Object System.IO.FileStream(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        $sha = [System.Security.Cryptography.SHA256]::Create()
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace("-", "").ToLowerInvariant()
    } catch {
        Stop-Adapter "file_sha256_unavailable"
    } finally {
        if ($null -ne $sha) { $sha.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

function Write-DurableStartBoundary(
    [string]$Path,
    [string]$Json,
    [string]$ExpectedSha256,
    [string]$OperationId,
    [string]$ActionRequestDigest
) {
    if ([System.IO.File]::Exists($Path)) { Stop-Adapter "tester_start_boundary_exists" }
    if ($ExpectedSha256 -notmatch '^[a-f0-9]{64}$' -or
        $ActionRequestDigest -notmatch '^[a-f0-9]{64}$' -or
        -not $Json -or $Json.Length -gt 8192) {
        Stop-Adapter "tester_start_boundary_contract_invalid"
    }
    try { $boundary = $Json | ConvertFrom-Json }
    catch { Stop-Adapter "tester_start_boundary_contract_invalid" }
    $propertyNames = @($boundary.PSObject.Properties.Name)
    $expectedNames = @("actionRequestDigest", "operationId", "schemaVersion", "stageId")
    if ($propertyNames.Count -ne $expectedNames.Count -or
        @($expectedNames | Where-Object { $_ -notin $propertyNames }).Count -ne 0 -or
        [string]$boundary.schemaVersion -ne "ea-factory-tester-start-boundary-v1" -or
        [string]$boundary.operationId -ne $OperationId -or
        [string]$boundary.stageId -ne "backtest_recheck" -or
        [string]$boundary.actionRequestDigest -ne $ActionRequestDigest) {
        Stop-Adapter "tester_start_boundary_contract_invalid"
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [byte[]]$bytes = $utf8.GetBytes($Json)
    if ((Get-Sha256Hex $bytes) -ne $ExpectedSha256) {
        Stop-Adapter "tester_start_boundary_digest_invalid"
    }
    $stream = $null
    try {
        $stream = New-Object System.IO.FileStream(
            $Path,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None,
            4096,
            [System.IO.FileOptions]::WriteThrough
        )
        $stream.Write($bytes, 0, $bytes.Length)
        $stream.Flush($true)
    } catch [System.IO.IOException] {
        Stop-Adapter "tester_start_boundary_exists"
    } catch {
        Stop-Adapter "tester_start_boundary_write_failed"
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }
    try { [byte[]]$observed = [System.IO.File]::ReadAllBytes($Path) }
    catch { Stop-Adapter "tester_start_boundary_readback_failed" }
    if ($observed.Length -ne $bytes.Length -or (Get-Sha256Hex $observed) -ne $ExpectedSha256) {
        Stop-Adapter "tester_start_boundary_readback_mismatch"
    }
    return $ExpectedSha256
}

function Assert-DurableStartBoundary(
    [string]$Path,
    [string]$Json,
    [string]$ExpectedSha256,
    [string]$OperationId,
    [string]$ActionRequestDigest
) {
    if (-not [System.IO.File]::Exists($Path) -or
        $ExpectedSha256 -notmatch '^[a-f0-9]{64}$' -or
        $ActionRequestDigest -notmatch '^[a-f0-9]{64}$' -or
        -not $Json -or $Json.Length -gt 8192) {
        Stop-Adapter "tester_start_boundary_recovery_invalid"
    }
    $item = Get-Item -LiteralPath $Path
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $item.Length -le 0 -or $item.Length -gt 8192) {
        Stop-Adapter "tester_start_boundary_recovery_invalid"
    }
    try { $boundary = $Json | ConvertFrom-Json }
    catch { Stop-Adapter "tester_start_boundary_recovery_invalid" }
    $propertyNames = @($boundary.PSObject.Properties.Name)
    $expectedNames = @("actionRequestDigest", "operationId", "schemaVersion", "stageId")
    if ($propertyNames.Count -ne $expectedNames.Count -or
        @($expectedNames | Where-Object { $_ -notin $propertyNames }).Count -ne 0 -or
        [string]$boundary.schemaVersion -ne "ea-factory-tester-start-boundary-v1" -or
        [string]$boundary.operationId -ne $OperationId -or
        [string]$boundary.stageId -ne "backtest_recheck" -or
        [string]$boundary.actionRequestDigest -ne $ActionRequestDigest) {
        Stop-Adapter "tester_start_boundary_recovery_invalid"
    }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [byte[]]$expectedBytes = $utf8.GetBytes($Json)
    try { [byte[]]$observedBytes = [System.IO.File]::ReadAllBytes($Path) }
    catch { Stop-Adapter "tester_start_boundary_recovery_invalid" }
    if ($observedBytes.Length -ne $expectedBytes.Length -or
        (Get-Sha256Hex $observedBytes) -ne $ExpectedSha256) {
        Stop-Adapter "tester_start_boundary_recovery_invalid"
    }
    return $item.LastWriteTimeUtc
}

function Get-FullPath([object]$Value) {
    if ($null -eq $Value) { Stop-Adapter "request_path_missing" }
    return [System.IO.Path]::GetFullPath([string]$Value)
}

function Test-SamePath([string]$Left, [string]$Right) {
    return [string]::Equals(
        [System.IO.Path]::GetFullPath($Left).TrimEnd('\'),
        [System.IO.Path]::GetFullPath($Right).TrimEnd('\'),
        [System.StringComparison]::OrdinalIgnoreCase
    )
}

function Get-WindowClass([IntPtr]$Handle) {
    $buffer = New-Object System.Text.StringBuilder 256
    [void][MetafxVisibleNative]::GetClassName($Handle, $buffer, $buffer.Capacity)
    return $buffer.ToString()
}

function Get-WindowTextSafe([IntPtr]$Handle) {
    $buffer = New-Object System.Text.StringBuilder 2048
    [void][MetafxVisibleNative]::GetWindowText($Handle, $buffer, $buffer.Capacity)
    return $buffer.ToString()
}

function Get-WindowOwner([IntPtr]$Handle) {
    [uint32]$processId = 0
    [void][MetafxVisibleNative]::GetWindowThreadProcessId($Handle, [ref]$processId)
    return [int]$processId
}

function Test-ForegroundWindowBinding(
    [System.Windows.Automation.AutomationElement]$Window,
    [int]$ProcessId
) {
    [IntPtr]$expectedRoot = [IntPtr]$Window.Current.NativeWindowHandle
    if ($expectedRoot -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($expectedRoot) -or
        (Get-WindowOwner $expectedRoot) -ne $ProcessId) {
        return $false
    }
    [IntPtr]$foreground = [MetafxVisibleNative]::GetForegroundWindow()
    if ($foreground -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($foreground) -or
        (Get-WindowOwner $foreground) -ne $ProcessId) {
        return $false
    }
    # MT4 can make the focused Report SysListView32 the foreground HWND even
    # though it remains a native child of the exact terminal.  Bind through
    # GA_ROOT so that child focus is accepted only when its immutable top-level
    # owner is still the selected terminal window.
    [IntPtr]$foregroundRoot = [MetafxVisibleNative]::GetAncestor(
        $foreground,
        [MetafxVisibleNative]::GA_ROOT
    )
    return (
        $foregroundRoot -eq $expectedRoot -and
        (Get-WindowOwner $foregroundRoot) -eq $ProcessId
    )
}

function Get-ExactProcesses([string]$ExecutablePath) {
    $leaf = [System.IO.Path]::GetFileName($ExecutablePath)
    $matches = @()
    foreach ($process in @(Get-Process -Name ([System.IO.Path]::GetFileNameWithoutExtension($leaf)) -ErrorAction SilentlyContinue)) {
        try {
            $image = $process.MainModule.FileName
            if ((Test-SamePath $image $ExecutablePath)) {
                $matches += $process
            }
        } catch { }
    }
    return @($matches)
}

function Get-TopWindow([int]$ProcessId, [string]$Kind) {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty,
        $ProcessId
    )
    $windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)
    $valid = @()
    foreach ($window in $windows) {
        $handle = [IntPtr]$window.Current.NativeWindowHandle
        if ($handle -eq [IntPtr]::Zero) { continue }
        $className = [string]$window.Current.ClassName
        $title = [string]$window.Current.Name
        if ($Kind -eq "terminal") {
            if ($className -eq "MetaQuotes::MetaTrader::4.00" -and $title.Trim()) { $valid += $window }
        } elseif ($Kind -eq "metaeditor") {
            if ($className -eq "MetaQuotes::MetaEditor::5.00" -and $title.Trim()) { $valid += $window }
        }
    }
    if ($valid.Count -ne 1) { Stop-Adapter ("{0}_window_ambiguous" -f $Kind) }
    $selected = $valid[0]
    if ((Get-WindowOwner ([IntPtr]$selected.Current.NativeWindowHandle)) -ne $ProcessId) {
        Stop-Adapter ("{0}_window_owner_mismatch" -f $Kind)
    }
    return $selected
}

function Get-ExistingVisibleProcess([string]$ExecutablePath, [string]$Kind) {
    $processes = @(Get-ExactProcesses $ExecutablePath)
    if ($processes.Count -eq 0) { Stop-Adapter ("{0}_window_not_ready" -f $Kind) }
    if ($processes.Count -gt 1) { Stop-Adapter ("{0}_process_ambiguous" -f $Kind) }
    $withWindow = @()
    foreach ($process in $processes) {
        try {
            $window = Get-TopWindow ([int]$process.Id) $Kind
            $withWindow += [pscustomobject]@{ Process = $process; Window = $window }
        } catch { }
    }
    if ($withWindow.Count -ne 1) { Stop-Adapter ("{0}_window_not_ready" -f $Kind) }
    return $withWindow[0]
}

function Restore-Foreground([System.Windows.Automation.AutomationElement]$Window) {
    $handle = [IntPtr]$Window.Current.NativeWindowHandle
    if ($handle -eq [IntPtr]::Zero) { Stop-Adapter "foreground_window_missing" }
    try {
        $pattern = $Window.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
        if ($pattern.Current.WindowVisualState -eq [System.Windows.Automation.WindowVisualState]::Minimized) {
            $pattern.SetWindowVisualState([System.Windows.Automation.WindowVisualState]::Normal)
        }
    } catch {
        [void][MetafxVisibleNative]::ShowWindowAsync($handle, [MetafxVisibleNative]::SW_RESTORE)
    }
    [void][MetafxVisibleNative]::ShowWindowAsync($handle, [MetafxVisibleNative]::SW_RESTORE)
    try { $Window.SetFocus() } catch { }
    [void][MetafxVisibleNative]::SetForegroundWindow($handle)
    if ([MetafxVisibleNative]::GetForegroundWindow() -ne $handle) {
        # Windows may reject SetForegroundWindow from a background Bridge even
        # though the user explicitly requested visible UI automation.  Join
        # only the involved GUI input queues long enough to activate the exact
        # already-verified window; no keys, mouse events, or arbitrary handles
        # are used.
        [uint32]$targetProcessId = 0
        [uint32]$targetThreadId = [MetafxVisibleNative]::GetWindowThreadProcessId(
            $handle,
            [ref]$targetProcessId
        )
        if ($targetThreadId -eq 0 -or
            $targetProcessId -ne [uint32]$Window.Current.ProcessId) {
            Stop-Adapter "foreground_window_owner_mismatch"
        }
        [uint32]$currentThreadId = [MetafxVisibleNative]::GetCurrentThreadId()
        $foregroundHandle = [MetafxVisibleNative]::GetForegroundWindow()
        [uint32]$foregroundProcessId = 0
        [uint32]$foregroundThreadId = 0
        if ($foregroundHandle -ne [IntPtr]::Zero) {
            $foregroundThreadId = [MetafxVisibleNative]::GetWindowThreadProcessId(
                $foregroundHandle,
                [ref]$foregroundProcessId
            )
        }
        $attachedForeground = $false
        $attachedTarget = $false
        try {
            if ($foregroundThreadId -gt 0 -and
                $foregroundThreadId -ne $currentThreadId -and
                $foregroundThreadId -ne $targetThreadId) {
                $attachedForeground = [MetafxVisibleNative]::AttachThreadInput(
                    $currentThreadId,
                    $foregroundThreadId,
                    $true
                )
            }
            if ($targetThreadId -gt 0 -and $targetThreadId -ne $currentThreadId) {
                $attachedTarget = [MetafxVisibleNative]::AttachThreadInput(
                    $currentThreadId,
                    $targetThreadId,
                    $true
                )
            }
            [void][MetafxVisibleNative]::BringWindowToTop($handle)
            [void][MetafxVisibleNative]::SetActiveWindow($handle)
            [void][MetafxVisibleNative]::SetFocus($handle)
            [void][MetafxVisibleNative]::SetForegroundWindow($handle)
        } finally {
            if ($attachedTarget) {
                [void][MetafxVisibleNative]::AttachThreadInput(
                    $currentThreadId,
                    $targetThreadId,
                    $false
                )
            }
            if ($attachedForeground) {
                [void][MetafxVisibleNative]::AttachThreadInput(
                    $currentThreadId,
                    $foregroundThreadId,
                    $false
                )
            }
        }
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        Start-Sleep -Milliseconds 100
        if ([MetafxVisibleNative]::GetForegroundWindow() -eq $handle) { return }
        try { $Window.SetFocus() } catch { }
        [void][MetafxVisibleNative]::SetForegroundWindow($handle)
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "foreground_binding_failed"
}

function Assert-NoModal([int]$ProcessId, [IntPtr]$AllowedWindow) {
    $root = [System.Windows.Automation.AutomationElement]::RootElement
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty,
        $ProcessId
    )
    foreach ($window in $root.FindAll([System.Windows.Automation.TreeScope]::Children, $condition)) {
        $handle = [IntPtr]$window.Current.NativeWindowHandle
        if ($handle -eq [IntPtr]::Zero -or $handle -eq $AllowedWindow) { continue }
        $isModal = $false
        try {
            $pattern = $window.GetCurrentPattern([System.Windows.Automation.WindowPattern]::Pattern)
            $isModal = [bool]$pattern.Current.IsModal
        } catch { }
        if ($isModal) { Stop-Adapter "modal_window_present" }
    }
}

function Find-DescendantsById(
    [System.Windows.Automation.AutomationElement]$Root,
    [string]$AutomationId
) {
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
        $AutomationId
    )
    return @($Root.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition))
}

function Get-UniqueControl(
    [System.Windows.Automation.AutomationElement]$Root,
    [string]$AutomationId,
    [int]$OwnerProcessId
) {
    $matches = @(Find-DescendantsById $Root $AutomationId)
    $owned = @()
    foreach ($match in $matches) {
        $handle = [IntPtr]$match.Current.NativeWindowHandle
        if ($handle -ne [IntPtr]::Zero -and (Get-WindowOwner $handle) -eq $OwnerProcessId) {
            $owned += $match
        }
    }
    if ($owned.Count -eq 0) {
        Stop-Adapter ("control_{0}_unavailable" -f $AutomationId.Replace(' ', '_'))
    }
    if ($owned.Count -gt 1) {
        Stop-Adapter ("control_{0}_ambiguous" -f $AutomationId.Replace(' ', '_'))
    }
    return $owned[0]
}

function Get-UniqueOwnedPopup([int]$ProcessId, [string]$ClassName) {
    $handles = @([MetafxVisibleNative]::GetVisibleTopLevelWindows($ProcessId, $ClassName))
    if ($handles.Count -ne 1) {
        Stop-Adapter ("popup_{0}_ambiguous" -f $ClassName.Replace('#', 'class'))
    }
    [IntPtr]$handle = [IntPtr]$handles[0]
    if ($handle -eq [IntPtr]::Zero -or (Get-WindowOwner $handle) -ne $ProcessId) {
        Stop-Adapter ("popup_{0}_owner_mismatch" -f $ClassName.Replace('#', 'class'))
    }
    $popup = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
    if ($null -eq $popup) {
        Stop-Adapter ("popup_{0}_uia_unavailable" -f $ClassName.Replace('#', 'class'))
    }
    return $popup
}

function Wait-UniqueOwnedPopupHandle(
    [int]$ProcessId,
    [string]$ClassName,
    [string]$FailureCode
) {
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        $handles = @([MetafxVisibleNative]::GetVisibleTopLevelWindows($ProcessId, $ClassName))
        if ($handles.Count -gt 1) {
            foreach ($handle in $handles) { Dismiss-OwnedPopup ([IntPtr]$handle) }
            Stop-Adapter ("{0}_ambiguous" -f $FailureCode)
        }
        if ($handles.Count -eq 1) {
            [IntPtr]$handle = [IntPtr]$handles[0]
            if ($handle -eq [IntPtr]::Zero -or
                (Get-WindowOwner $handle) -ne $ProcessId -or
                (Get-WindowClass $handle) -ne $ClassName -or
                -not [MetafxVisibleNative]::IsWindowVisible($handle)) {
                Dismiss-OwnedPopup $handle
                Stop-Adapter ("{0}_identity_invalid" -f $FailureCode)
            }
            return $handle
        }
        Start-Sleep -Milliseconds 50
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter $FailureCode
}

function Get-TesterPane([System.Windows.Automation.AutomationElement]$TerminalWindow, [int]$ProcessId) {
    [IntPtr]$terminalHandle = [IntPtr]$TerminalWindow.Current.NativeWindowHandle
    if ($terminalHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($terminalHandle) -or
        [int]$TerminalWindow.Current.ProcessId -ne $ProcessId -or
        (Get-WindowOwner $terminalHandle) -ne $ProcessId -or
        [string]$TerminalWindow.Current.ClassName -ne "MetaQuotes::MetaTrader::4.00") {
        Stop-Adapter "tester_terminal_identity_invalid"
    }
    $tester = Get-UniqueControl $TerminalWindow "83" $ProcessId
    [IntPtr]$testerHandle = [IntPtr]$tester.Current.NativeWindowHandle
    if ($testerHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($testerHandle) -or
        [int]$tester.Current.ProcessId -ne $ProcessId -or
        (Get-WindowOwner $testerHandle) -ne $ProcessId -or
        [MetafxVisibleNative]::GetDlgCtrlID($testerHandle) -ne 83) {
        Stop-Adapter "tester_pane_identity_invalid"
    }
    return $tester
}

function Get-VisibleTesterReportLists(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId
) {
    [IntPtr]$testerHandle = [IntPtr]$TesterPane.Current.NativeWindowHandle
    if ($testerHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $testerHandle) -ne $ProcessId) {
        Stop-Adapter "tester_report_pane_invalid"
    }
    $testerRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($testerHandle, [ref]$testerRect)) {
        Stop-Adapter "tester_report_pane_invalid"
    }
    $eligible = New-Object System.Collections.Generic.List[System.Windows.Automation.AutomationElement]
    foreach ($candidate in @(Find-DescendantsById $TesterPane "33213")) {
        [IntPtr]$candidateHandle = [IntPtr]$candidate.Current.NativeWindowHandle
        if ($candidateHandle -eq [IntPtr]::Zero -or
            -not [MetafxVisibleNative]::IsWindow($candidateHandle) -or
            [string]$candidate.Current.ClassName -ne "SysListView32" -or
            [int]$candidate.Current.ProcessId -ne $ProcessId -or
            (Get-WindowOwner $candidateHandle) -ne $ProcessId -or
            [MetafxVisibleNative]::GetParent($candidateHandle) -ne $testerHandle -or
            [MetafxVisibleNative]::GetDlgCtrlID($candidateHandle) -ne 33213 -or
            -not [MetafxVisibleNative]::IsWindowVisible($candidateHandle) -or
            (([MetafxVisibleNative]::GetWindowLong(
                $candidateHandle,
                [MetafxVisibleNative]::GWL_STYLE
            ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0) -or
            [bool]$candidate.Current.IsOffscreen) {
            continue
        }
        [int]$candidateStyle = [MetafxVisibleNative]::GetWindowLong(
            $candidateHandle,
            [MetafxVisibleNative]::GWL_STYLE
        )
        if (($candidateStyle -band [MetafxVisibleNative]::LVS_TYPEMASK) -ne
            [MetafxVisibleNative]::LVS_REPORT) {
            continue
        }
        $candidateRect = New-Object MetafxVisibleNative+RECT
        if (-not [MetafxVisibleNative]::GetWindowRect($candidateHandle, [ref]$candidateRect) -or
            $candidateRect.Right -le $candidateRect.Left -or
            $candidateRect.Bottom -le $candidateRect.Top -or
            $candidateRect.Left -lt $testerRect.Left -or
            $candidateRect.Top -lt $testerRect.Top -or
            $candidateRect.Right -gt $testerRect.Right -or
            $candidateRect.Bottom -gt $testerRect.Bottom) {
            continue
        }
        [void]$eligible.Add($candidate)
    }
    return @($eligible.ToArray())
}

function Get-VisibleTesterSettingsSurface(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId
) {
    [IntPtr]$testerHandle = [IntPtr]$TesterPane.Current.NativeWindowHandle
    if ($testerHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($testerHandle) -or
        (Get-WindowOwner $testerHandle) -ne $ProcessId) {
        Stop-Adapter "tester_settings_pane_invalid"
    }
    $testerRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($testerHandle, [ref]$testerRect)) {
        Stop-Adapter "tester_settings_pane_invalid"
    }

    # The owner-drawn Report tab hides every Settings control from UIA even
    # though MT4 retains their native HWNDs.  A zero-match Start lookup is
    # therefore not an ambiguous dialog and must not be used to infer whether
    # the completed tester is idle.  Treat Settings as active only when the
    # complete, exact native/UIA control surface is visible under one owned
    # Afx settings parent.  This keeps tab discovery fail-closed and prevents a
    # same-id control elsewhere in the terminal from being accepted.
    $startCandidates = @(Find-DescendantsById $TesterPane "1034" | Where-Object {
        [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
        [string]$_.Current.ClassName -eq "Button" -and
        [int]$_.Current.ProcessId -eq $ProcessId -and
        (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq $ProcessId -and
        [MetafxVisibleNative]::GetDlgCtrlID([IntPtr]$_.Current.NativeWindowHandle) -eq 1034 -and
        [MetafxVisibleNative]::IsWindowVisible([IntPtr]$_.Current.NativeWindowHandle) -and
        (([MetafxVisibleNative]::GetWindowLong(
            [IntPtr]$_.Current.NativeWindowHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
        -not [bool]$_.Current.IsOffscreen -and
        ([string]$_.Current.Name).Trim() -in @("Start", "Stop")
    })
    if ($startCandidates.Count -gt 1) { Stop-Adapter "tester_settings_start_ambiguous" }
    if ($startCandidates.Count -eq 0) { return $null }

    $start = $startCandidates[0]
    [IntPtr]$startHandle = [IntPtr]$start.Current.NativeWindowHandle
    [IntPtr]$settingsParent = [MetafxVisibleNative]::GetParent($startHandle)
    if ($settingsParent -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($settingsParent) -or
        (Get-WindowOwner $settingsParent) -ne $ProcessId -or
        (Get-WindowClass $settingsParent) -ne "AfxWnd140s" -or
        [MetafxVisibleNative]::GetParent($settingsParent) -ne $testerHandle -or
        -not [MetafxVisibleNative]::IsWindowVisible($settingsParent) -or
        (([MetafxVisibleNative]::GetWindowLong(
            $settingsParent,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0)) {
        Stop-Adapter "tester_settings_parent_invalid"
    }
    $settingsRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($settingsParent, [ref]$settingsRect) -or
        $settingsRect.Right -le $settingsRect.Left -or
        $settingsRect.Bottom -le $settingsRect.Top -or
        $settingsRect.Left -lt $testerRect.Left -or
        $settingsRect.Top -lt $testerRect.Top -or
        $settingsRect.Right -gt $testerRect.Right -or
        $settingsRect.Bottom -gt $testerRect.Bottom) {
        Stop-Adapter "tester_settings_parent_invalid"
    }

    $requiredControls = @(
        @{ Id = "1128"; ClassName = "ComboBox" },
        @{ Id = "1347"; ClassName = "ComboBox" },
        @{ Id = "1228"; ClassName = "ComboBox" },
        @{ Id = "4027"; ClassName = "ComboBox" },
        @{ Id = "1023"; ClassName = "Button" },
        @{ Id = "1029"; ClassName = "Button" },
        @{ Id = "1400"; ClassName = "Button" }
    )
    $requiredElements = @{}
    foreach ($required in $requiredControls) {
        $eligible = @(Find-DescendantsById $TesterPane ([string]$required.Id) | Where-Object {
            [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
            [string]$_.Current.ClassName -eq [string]$required.ClassName -and
            [int]$_.Current.ProcessId -eq $ProcessId -and
            (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq $ProcessId -and
            [MetafxVisibleNative]::GetParent([IntPtr]$_.Current.NativeWindowHandle) -eq $settingsParent -and
            [MetafxVisibleNative]::GetDlgCtrlID([IntPtr]$_.Current.NativeWindowHandle) -eq [int]$required.Id -and
            [MetafxVisibleNative]::IsWindowVisible([IntPtr]$_.Current.NativeWindowHandle) -and
            (([MetafxVisibleNative]::GetWindowLong(
                [IntPtr]$_.Current.NativeWindowHandle,
                [MetafxVisibleNative]::GWL_STYLE
            ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
            -not [bool]$_.Current.IsOffscreen
        })
        if ($eligible.Count -gt 1) { Stop-Adapter "tester_settings_surface_ambiguous" }
        if ($eligible.Count -eq 0) { return $null }
        $requiredElements[[string]$required.Id] = $eligible[0]
    }

    $expertCombo = $requiredElements["1128"]
    [IntPtr]$expertComboHandle = [IntPtr]$expertCombo.Current.NativeWindowHandle
    $expertEdits = @(Find-DescendantsById $expertCombo "6217" | Where-Object {
        [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
        [string]$_.Current.ClassName -eq "Edit" -and
        [int]$_.Current.ProcessId -eq $ProcessId -and
        (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq $ProcessId -and
        [MetafxVisibleNative]::GetParent([IntPtr]$_.Current.NativeWindowHandle) -eq $expertComboHandle -and
        [MetafxVisibleNative]::GetDlgCtrlID([IntPtr]$_.Current.NativeWindowHandle) -eq 6217 -and
        [MetafxVisibleNative]::IsWindowVisible([IntPtr]$_.Current.NativeWindowHandle) -and
        (([MetafxVisibleNative]::GetWindowLong(
            [IntPtr]$_.Current.NativeWindowHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
        -not [bool]$_.Current.IsOffscreen
    })
    if ($expertEdits.Count -gt 1) { Stop-Adapter "tester_settings_expert_edit_ambiguous" }
    if ($expertEdits.Count -eq 0) { return $null }

    $spreadEdits = @(Find-DescendantsById $TesterPane "1001" | Where-Object {
        [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
        [string]$_.Current.ClassName -eq "Edit" -and
        [int]$_.Current.ProcessId -eq $ProcessId -and
        (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq $ProcessId -and
        [MetafxVisibleNative]::GetDlgCtrlID([IntPtr]$_.Current.NativeWindowHandle) -eq 1001 -and
        [MetafxVisibleNative]::IsWindowVisible([IntPtr]$_.Current.NativeWindowHandle) -and
        (([MetafxVisibleNative]::GetWindowLong(
            [IntPtr]$_.Current.NativeWindowHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
        -not [bool]$_.Current.IsOffscreen
    })
    if ($spreadEdits.Count -gt 1) { Stop-Adapter "tester_settings_spread_edit_ambiguous" }
    if ($spreadEdits.Count -eq 0) { return $null }
    [IntPtr]$spreadEditHandle = [IntPtr]$spreadEdits[0].Current.NativeWindowHandle
    [IntPtr]$spreadComboHandle = [MetafxVisibleNative]::GetParent($spreadEditHandle)
    if ($spreadComboHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($spreadComboHandle) -or
        (Get-WindowOwner $spreadComboHandle) -ne $ProcessId -or
        (Get-WindowClass $spreadComboHandle) -ne "ComboBox" -or
        [MetafxVisibleNative]::GetDlgCtrlID($spreadComboHandle) -ne 1207 -or
        [MetafxVisibleNative]::GetParent($spreadComboHandle) -ne $settingsParent -or
        -not [MetafxVisibleNative]::IsWindowVisible($spreadComboHandle) -or
        (([MetafxVisibleNative]::GetWindowLong(
            $spreadComboHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0)) {
        Stop-Adapter "tester_settings_spread_parent_invalid"
    }
    return [pscustomobject]@{
        TesterPane = $TesterPane
        SettingsParentHandle = [int64]$settingsParent
        StartButton = $start
    }
}

function Get-UniqueVisibleTesterTabStrip(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId,
    [string]$FailurePrefix
) {
    # MT4 can recreate the Strategy Tester content and owner-drawn tab HWNDs
    # after a tab change or Save As.  Treat every caller-provided UIA element as
    # a short-lived binding and prove the exact current native hierarchy before
    # returning it.
    [IntPtr]$testerHandle = [IntPtr]$TesterPane.Current.NativeWindowHandle
    if ($testerHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($testerHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($testerHandle) -or
        [int]$TesterPane.Current.ProcessId -ne $ProcessId -or
        (Get-WindowOwner $testerHandle) -ne $ProcessId -or
        [MetafxVisibleNative]::GetDlgCtrlID($testerHandle) -ne 83 -or
        (([MetafxVisibleNative]::GetWindowLong(
            $testerHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0) -or
        [bool]$TesterPane.Current.IsOffscreen) {
        Stop-Adapter ("{0}_tab_strip_parent_invalid" -f $FailurePrefix)
    }

    # UIA can enumerate multiple wrappers for one MFC HWND.  Collapse only
    # exact native duplicates; more than one distinct eligible HWND remains an
    # ambiguity and must fail closed.
    $tabStripsByHandle = @{}
    foreach ($candidate in @(Find-DescendantsById $TesterPane "1137")) {
        [IntPtr]$candidateHandle = [IntPtr]$candidate.Current.NativeWindowHandle
        if ($candidateHandle -ne [IntPtr]::Zero -and
            [MetafxVisibleNative]::IsWindow($candidateHandle) -and
            [string]$candidate.Current.ClassName -eq "AfxWnd140s" -and
            (Get-WindowClass $candidateHandle) -eq "AfxWnd140s" -and
            [int]$candidate.Current.ProcessId -eq $ProcessId -and
            (Get-WindowOwner $candidateHandle) -eq $ProcessId -and
            [MetafxVisibleNative]::GetParent($candidateHandle) -eq $testerHandle -and
            [MetafxVisibleNative]::GetDlgCtrlID($candidateHandle) -eq 1137 -and
            [MetafxVisibleNative]::IsWindowVisible($candidateHandle) -and
            (([MetafxVisibleNative]::GetWindowLong(
                $candidateHandle,
                [MetafxVisibleNative]::GWL_STYLE
            ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
            -not [bool]$candidate.Current.IsOffscreen) {
            $tabStripsByHandle[$candidateHandle.ToInt64().ToString()] = $candidate
        }
    }
    $tabStrips = @($tabStripsByHandle.Values)
    if ($tabStrips.Count -gt 1) {
        Stop-Adapter ("{0}_tab_strip_ambiguous" -f $FailurePrefix)
    }
    if ($tabStrips.Count -eq 0) {
        Stop-Adapter ("{0}_tab_strip_unavailable" -f $FailurePrefix)
    }

    $tabStrip = $tabStrips[0]
    [IntPtr]$tabHandle = [IntPtr]$tabStrip.Current.NativeWindowHandle
    $testerRect = New-Object MetafxVisibleNative+RECT
    $tabRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($testerHandle, [ref]$testerRect) -or
        -not [MetafxVisibleNative]::GetWindowRect($tabHandle, [ref]$tabRect)) {
        Stop-Adapter ("{0}_tab_strip_invalid" -f $FailurePrefix)
    }
    [int]$tabWidth = $tabRect.Right - $tabRect.Left
    [int]$tabHeight = $tabRect.Bottom - $tabRect.Top
    if ($tabWidth -lt 160 -or $tabHeight -lt 10 -or $tabHeight -gt 80 -or
        $tabRect.Left -lt $testerRect.Left -or $tabRect.Top -lt $testerRect.Top -or
        $tabRect.Right -gt $testerRect.Right -or $tabRect.Bottom -gt $testerRect.Bottom) {
        Stop-Adapter ("{0}_tab_strip_invalid" -f $FailurePrefix)
    }
    return [pscustomobject]@{
        TesterPane = $TesterPane
        TesterHandle = $testerHandle
        TabStrip = $tabStrip
        TabHandle = $tabHandle
        TesterRect = $testerRect
        TabRect = $tabRect
        TabWidth = $tabWidth
        TabHeight = $tabHeight
    }
}

function Select-TesterSettingsTab(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId
) {
    [IntPtr]$terminalHandle = [IntPtr]$TerminalWindow.Current.NativeWindowHandle
    $tester = Get-TesterPane $TerminalWindow $ProcessId
    $surface = Get-VisibleTesterSettingsSurface $tester $ProcessId
    if ($null -ne $surface) { return $tester }

    # MT4 does not expose owner-drawn Strategy Tester tab captions through UIA
    # or MSAA on every build.  Scan only the exact owned tab strip and accept a
    # click only when the complete Settings surface above becomes visible.
    $tabBinding = Get-UniqueVisibleTesterTabStrip $tester $ProcessId "tester_settings"
    Restore-Foreground $TerminalWindow
    try { $tabBinding.TabStrip.SetFocus() } catch { }
    [void][MetafxVisibleNative]::SetFocus([IntPtr]$tabBinding.TabHandle)
    [int]$accessibleSettingsX = 0
    [int]$accessibleSettingsY = 0
    if ([MetafxVisibleMsaa]::TrySelectUniqueExactNameCenter(
        [IntPtr]$tabBinding.TabHandle,
        "Settings",
        0x25,
        [ref]$accessibleSettingsX,
        [ref]$accessibleSettingsY
    )) {
        $accessibleDeadline = [DateTime]::UtcNow.AddSeconds(1)
        do {
            Start-Sleep -Milliseconds 100
            $tester = Get-TesterPane $TerminalWindow $ProcessId
            $surface = Get-VisibleTesterSettingsSurface $tester $ProcessId
            if ($null -ne $surface) { return $tester }
        } while ([DateTime]::UtcNow -lt $accessibleDeadline)
    }
    # The first four pixels are the MFC tab-strip border, not the Settings tab
    # hit target.  Reacquire both HWNDs and calculate client-relative bounds on
    # every iteration because MT4 may recreate either HWND after the prior click.
    for ([int]$scanIndex = 0; $scanIndex -le 90; $scanIndex++) {
        Restore-Foreground $TerminalWindow
        $currentTester = Get-TesterPane $TerminalWindow $ProcessId
        $currentBinding = Get-UniqueVisibleTesterTabStrip `
            $currentTester `
            $ProcessId `
            "tester_settings"
        [int]$scanRightClient = [Math]::Min(
            $currentBinding.TabWidth - 4,
            [Math]::Min(720, [Math]::Max(160, [int]($currentBinding.TabWidth * 0.40)))
        )
        [int]$settingsTabOffset = [Math]::Min(
            $currentBinding.TabWidth - 5,
            [Math]::Max(16, [int]($currentBinding.TabHeight * 1.75))
        )
        [int]$clientX = $settingsTabOffset + ($scanIndex * 8)
        [int]$clientY = [int]($currentBinding.TabHeight / 2)
        if ($clientX -gt $scanRightClient) { break }
        if (-not (Test-ForegroundWindowBinding $TerminalWindow $ProcessId)) {
            Stop-Adapter "tester_settings_tab_scan_binding_changed"
        }
        try { $currentBinding.TabStrip.SetFocus() } catch { }
        Invoke-ExactNativeTesterTabClick `
            ([IntPtr]$currentBinding.TabHandle) `
            ([IntPtr]$currentBinding.TesterHandle) `
            $terminalHandle `
            $ProcessId `
            $clientX `
            $clientY `
            "tester_settings_tab_scan"
        # Accept only the newly bound Tester whose complete Settings contract
        # becomes visible; never carry this iteration's HWND into the next one.
        $surfaceDeadline = [DateTime]::UtcNow.AddSeconds(1)
        do {
            Start-Sleep -Milliseconds 100
            $tester = Get-TesterPane $TerminalWindow $ProcessId
            $surface = Get-VisibleTesterSettingsSurface $tester $ProcessId
            if ($null -ne $surface) { return $tester }
        } while ([DateTime]::UtcNow -lt $surfaceDeadline)
    }
    Stop-Adapter "tester_settings_tab_unavailable"
}

function Select-TesterReportTab(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId
) {
    [IntPtr]$terminalHandle = [IntPtr]$TerminalWindow.Current.NativeWindowHandle
    $tester = Get-TesterPane $TerminalWindow $ProcessId
    $visibleReports = @(Get-VisibleTesterReportLists $tester $ProcessId)
    if ($visibleReports.Count -gt 1) { Stop-Adapter "tester_report_list_ambiguous" }
    if ($visibleReports.Count -eq 1) { return $visibleReports[0] }

    # MT4 renders the Strategy Tester tabs in an owner-drawn AfxWnd control.
    # On affected builds neither UIA nor MSAA exposes the visible tab captions,
    # so an exact-name accessibility selection always returns zero candidates.
    # Bind the scan to the one owned tab strip inside the already-bound Tester,
    # click only inside that strip, and accept a target only when MT4 exposes its
    # unique native Report list (dialog id 33213).  Unlike Results, the Report
    # pane still has summary rows when a strategy produces zero trades, so the
    # Save-as-Report menu remains reachable and the verifier can report that
    # outcome explicitly.  This avoids language-, DPI-
    # and theme-dependent fixed screen coordinates while remaining fail-closed.
    $tabBinding = Get-UniqueVisibleTesterTabStrip $tester $ProcessId "tester_report"
    [int]$accessibleReportX = 0
    [int]$accessibleReportY = 0
    if ([MetafxVisibleMsaa]::TrySelectUniqueExactNameCenter(
        [IntPtr]$tabBinding.TabHandle,
        "Report",
        0x25,
        [ref]$accessibleReportX,
        [ref]$accessibleReportY
    )) {
        $accessibleDeadline = [DateTime]::UtcNow.AddSeconds(1)
        do {
            Start-Sleep -Milliseconds 100
            $tester = Get-TesterPane $TerminalWindow $ProcessId
            $reportLists = @(Get-VisibleTesterReportLists $tester $ProcessId)
            if ($reportLists.Count -eq 1) { return $reportLists[0] }
            if ($reportLists.Count -gt 1) { Stop-Adapter "tester_report_list_ambiguous" }
        } while ([DateTime]::UtcNow -lt $accessibleDeadline)
    }
    Restore-Foreground $TerminalWindow
    try { $tabBinding.TabStrip.SetFocus() } catch { }
    [void][MetafxVisibleNative]::SetFocus([IntPtr]$tabBinding.TabHandle)
    for ([int]$scanIndex = 0; $scanIndex -le 90; $scanIndex++) {
        Restore-Foreground $TerminalWindow
        $currentTester = Get-TesterPane $TerminalWindow $ProcessId
        $currentBinding = Get-UniqueVisibleTesterTabStrip `
            $currentTester `
            $ProcessId `
            "tester_report"
        [int]$scanRightClient = [Math]::Min(
            $currentBinding.TabWidth - 4,
            [Math]::Min(720, [Math]::Max(160, [int]($currentBinding.TabWidth * 0.40)))
        )
        [int]$clientX = 4 + ($scanIndex * 8)
        [int]$clientY = [int]($currentBinding.TabHeight / 2)
        if ($clientX -gt $scanRightClient) { break }
        if (-not (Test-ForegroundWindowBinding $TerminalWindow $ProcessId)) {
            Stop-Adapter "tester_report_tab_scan_binding_changed"
        }
        try { $currentBinding.TabStrip.SetFocus() } catch { }
        Invoke-ExactNativeTesterTabClick `
            ([IntPtr]$currentBinding.TabHandle) `
            ([IntPtr]$currentBinding.TesterHandle) `
            $terminalHandle `
            $ProcessId `
            $clientX `
            $clientY `
            "tester_report_tab_scan"
        $reportDeadline = [DateTime]::UtcNow.AddMilliseconds(750)
        do {
            Start-Sleep -Milliseconds 75
            $tester = Get-TesterPane $TerminalWindow $ProcessId
            $visibleReports = @(Get-VisibleTesterReportLists $tester $ProcessId)
            if ($visibleReports.Count -gt 1) { Stop-Adapter "tester_report_list_ambiguous" }
            if ($visibleReports.Count -eq 1) { return $visibleReports[0] }
        } while ([DateTime]::UtcNow -lt $reportDeadline)
    }
    Stop-Adapter "tester_report_tab_unavailable"
}

function Set-TesterVisualSpeedMaximum(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId
) {
    $controls = @(Find-DescendantsById $TesterPane "1401" | Where-Object {
        [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
        $_.Current.ClassName -eq "msctls_trackbar32" -and
        (([MetafxVisibleNative]::GetWindowLong(
            [IntPtr]$_.Current.NativeWindowHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -eq 0) -and
        -not [bool]$_.Current.IsOffscreen -and
        [MetafxVisibleNative]::IsWindowVisible([IntPtr]$_.Current.NativeWindowHandle)
    })
    if ($controls.Count -ne 1) { Stop-Adapter "tester_visual_speed_control_ambiguous" }
    [IntPtr]$handle = [IntPtr]$controls[0].Current.NativeWindowHandle
    if ((Get-WindowOwner $handle) -ne $ProcessId -or
        [MetafxVisibleNative]::GetDlgCtrlID($handle) -ne 1401) {
        Stop-Adapter "tester_visual_speed_control_invalid"
    }
    $patternObject = $null
    if (-not $controls[0].TryGetCurrentPattern(
        [System.Windows.Automation.RangeValuePattern]::Pattern,
        [ref]$patternObject
    )) {
        Stop-Adapter "tester_visual_speed_pattern_unavailable"
    }
    $range = [System.Windows.Automation.RangeValuePattern]$patternObject
    [double]$minimum = $range.Current.Minimum
    [double]$maximum = $range.Current.Maximum
    [double]$before = $range.Current.Value
    if ($range.Current.IsReadOnly -or
        [Math]::Truncate($minimum) -ne $minimum -or
        [Math]::Truncate($maximum) -ne $maximum -or
        [Math]::Truncate($before) -ne $before -or
        $minimum -lt 0 -or $maximum -le $minimum -or $maximum -gt 100 -or
        $before -lt $minimum -or $before -gt $maximum) {
        Stop-Adapter "tester_visual_speed_range_invalid"
    }
    # Setting an already-maximized native trackbar through TBM_SETPOS alone
    # moves only the thumb and does not reliably notify MT4.  RangeValuePattern
    # uses the control provider's real value-change path.  A one-step probe
    # guarantees that MT4 receives a change even when the thumb was already at
    # maximum because of a stale visual-only write.
    if ($before -eq $maximum -and ($maximum - $minimum) -ge 1) {
        $range.SetValue($maximum - 1)
        Start-Sleep -Milliseconds 100
    }
    $range.SetValue($maximum)
    Start-Sleep -Milliseconds 100
    [double]$after = $range.Current.Value
    if ($after -ne $maximum) { Stop-Adapter "tester_visual_speed_not_applied" }
    return [ordered]@{
        before = [int]$before
        after = [int]$after
        minimum = [int]$minimum
        maximum = [int]$maximum
    }
}

function Invoke-TargetMessage([IntPtr]$Handle, [int]$Message, [int]$WParam, [int]$LParam) {
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxVisibleNative]::SendMessageTimeout(
        $Handle,
        $Message,
        [IntPtr]$WParam,
        [IntPtr]$LParam,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG,
        1500,
        [ref]$result
    )
    if ($call -eq [IntPtr]::Zero) { Stop-Adapter "window_message_timeout" }
    return $result
}

function Read-Win32Text([IntPtr]$Handle) {
    [IntPtr]$lengthResult = [IntPtr]::Zero
    $lengthCall = [MetafxVisibleNative]::SendMessageTimeout(
        $Handle, [MetafxVisibleNative]::WM_GETTEXTLENGTH,
        [IntPtr]::Zero, [IntPtr]::Zero,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$lengthResult
    )
    if ($lengthCall -eq [IntPtr]::Zero) { Stop-Adapter "control_text_timeout" }
    $length = $lengthResult.ToInt32()
    if ($length -lt 0 -or $length -gt 4096) { Stop-Adapter "control_text_length_invalid" }
    $buffer = New-Object System.Text.StringBuilder ([Math]::Max(2, $length + 2))
    [IntPtr]$textResult = [IntPtr]::Zero
    $textCall = [MetafxVisibleNative]::SendMessageTimeout(
        $Handle, [MetafxVisibleNative]::WM_GETTEXT,
        [IntPtr]$buffer.Capacity, $buffer,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$textResult
    )
    if ($textCall -eq [IntPtr]::Zero) { Stop-Adapter "control_text_timeout" }
    return $buffer.ToString().Trim()
}

function Convert-ComboMessageInteger(
    [IntPtr]$Value,
    [bool]$AllowCbErr,
    [string]$FailureCode
) {
    [int64]$raw = $Value.ToInt64()
    # A 32-bit MT4 CB_ERR may be sign-extended (-1) or zero-extended
    # (0x00000000FFFFFFFF) by the caller/runtime boundary.  Normalize it only
    # for messages where CB_ERR is an expected state such as CB_GETCURSEL.
    if ($raw -eq -1 -or $raw -eq 4294967295) {
        if ($AllowCbErr) { return -1 }
        Stop-Adapter $FailureCode
    }
    if ($raw -lt 0 -or $raw -gt [int]::MaxValue) { Stop-Adapter $FailureCode }
    return [int]$raw
}

function Assert-DeployedExpertDigest(
    [string]$Path,
    [string]$ExpectedPath,
    [string]$ExpectedDigest
) {
    $resolved = Get-FullPath $Path
    $expected = Get-FullPath $ExpectedPath
    $digest = $ExpectedDigest.Trim().ToLowerInvariant()
    if (-not (Test-SamePath $resolved $expected) -or
        $digest -notmatch '^[0-9a-f]{64}$' -or
        -not [System.IO.File]::Exists($resolved) -or
        [System.IO.Path]::GetExtension($resolved) -ine ".ex4" -or
        (Get-Item -LiteralPath $resolved).Length -le 0 -or
        ((Get-Item -LiteralPath $resolved).Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        Stop-Adapter "deployed_expert_identity_invalid"
    }
    $observed = Get-FileSha256Hex $resolved
    if ($observed -ne $digest) { Stop-Adapter "deployed_expert_digest_mismatch" }
    return $observed
}

function Get-ComboRuntimeInfo([System.Windows.Automation.AutomationElement]$Combo, [int]$ProcessId) {
    [IntPtr]$handle = [IntPtr]$Combo.Current.NativeWindowHandle
    if ($handle -eq [IntPtr]::Zero -or (Get-WindowOwner $handle) -ne $ProcessId -or
        [string]$Combo.Current.ClassName -ne "ComboBox") {
        Stop-Adapter "expert_combo_identity_invalid"
    }
    $style = [MetafxVisibleNative]::GetWindowLong($handle, [MetafxVisibleNative]::GWL_STYLE)
    $ownerDraw = (($style -band [MetafxVisibleNative]::CBS_OWNERDRAWFIXED) -ne 0 -or
        ($style -band [MetafxVisibleNative]::CBS_OWNERDRAWVARIABLE) -ne 0)
    $hasStrings = (($style -band [MetafxVisibleNative]::CBS_HASSTRINGS) -ne 0)
    if (-not $ownerDraw -and -not $hasStrings) { Stop-Adapter "expert_combo_style_unsupported" }
    $count = Convert-ComboMessageInteger `
        (Invoke-TargetMessage $handle ([MetafxVisibleNative]::CB_GETCOUNT) 0 0) `
        $false `
        "expert_combo_count_invalid"
    $index = Convert-ComboMessageInteger `
        (Invoke-TargetMessage $handle ([MetafxVisibleNative]::CB_GETCURSEL) 0 0) `
        $true `
        "expert_combo_index_invalid"
    $customValueOnly = (
        [string]$Combo.Current.AutomationId -eq "1128" -and
        $count -eq 0 -and
        $index -eq -1 -and
        ([string]$Combo.Current.Name).Trim()
    )
    if ($customValueOnly) {
        return [ordered]@{
            handle = $handle
            count = 0
            index = -1
            ownerDraw = $ownerDraw
            hasStrings = $hasStrings
            listedValue = $null
            nativeListAvailable = $false
        }
    }
    if ($count -lt 1 -or $count -gt 4096 -or $index -lt 0 -or $index -ge $count) {
        Stop-Adapter "expert_combo_index_invalid"
    }
    $listedValue = $null
    if ($hasStrings) {
        $length = (Invoke-TargetMessage $handle ([MetafxVisibleNative]::CB_GETLBTEXTLEN) $index 0).ToInt32()
        if ($length -lt 1 -or $length -gt 4096) { Stop-Adapter "expert_combo_list_text_length_invalid" }
        $buffer = New-Object System.Text.StringBuilder ($length + 2)
        [IntPtr]$textResult = [IntPtr]::Zero
        $textCall = [MetafxVisibleNative]::SendMessageTimeout(
            $handle, [MetafxVisibleNative]::CB_GETLBTEXT,
            [IntPtr]$index, $buffer,
            [MetafxVisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$textResult
        )
        if ($textCall -eq [IntPtr]::Zero -or $textResult.ToInt32() -ne $length) {
            Stop-Adapter "expert_combo_list_text_timeout"
        }
        $listedValue = $buffer.ToString().Trim()
        if (-not $listedValue) { Stop-Adapter "expert_combo_list_text_empty" }
    }
    return [ordered]@{
        handle = $handle
        count = $count
        index = $index
        ownerDraw = $ownerDraw
        hasStrings = $hasStrings
        listedValue = $listedValue
        nativeListAvailable = $true
    }
}

function Get-AutoTradingState([System.Windows.Automation.AutomationElement]$TerminalWindow, [int]$ProcessId) {
    $toolbar = Get-UniqueControl $TerminalWindow "99" $ProcessId
    if ($toolbar.Current.ClassName -ne "ToolbarWindow32") { Stop-Adapter "autotrading_toolbar_invalid" }
    [IntPtr]$stateResult = [IntPtr]::Zero
    $stateCall = [MetafxVisibleNative]::SendMessageTimeout(
        [IntPtr]$toolbar.Current.NativeWindowHandle,
        [MetafxVisibleNative]::TB_GETSTATE,
        [IntPtr]33020, [IntPtr]::Zero,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$stateResult
    )
    if ($stateCall -eq [IntPtr]::Zero) { Stop-Adapter "autotrading_state_timeout" }
    $state = $stateResult.ToInt64()
    if ($state -lt 0 -or $state -eq 4294967295) { Stop-Adapter "autotrading_state_unreadable" }
    return (($state -band 1) -eq 1)
}

function New-RawBinding(
    [pscustomobject]$Terminal,
    [pscustomobject]$FrontOffice,
    [string]$FrontOfficeKind,
    [bool]$AutoTradingState
) {
    $terminalHandle = [IntPtr]$Terminal.Window.Current.NativeWindowHandle
    $frontHandle = [IntPtr]$FrontOffice.Window.Current.NativeWindowHandle
    return [ordered]@{
        observedAt = [DateTime]::UtcNow.ToString("o")
        terminalProcessId = [int]$Terminal.Process.Id
        terminalExecutablePath = [string]$Terminal.Process.MainModule.FileName
        terminalWindowHandle = [int64]$terminalHandle
        terminalWindowOwnerProcessId = Get-WindowOwner $terminalHandle
        terminalWindowTitle = [string]$Terminal.Window.Current.Name
        terminalWindowClass = [string]$Terminal.Window.Current.ClassName
        frontOfficeKind = $FrontOfficeKind
        frontOfficeProcessId = [int]$FrontOffice.Process.Id
        frontOfficeExecutablePath = [string]$FrontOffice.Process.MainModule.FileName
        frontOfficeWindowHandle = [int64]$frontHandle
        frontOfficeWindowOwnerProcessId = Get-WindowOwner $frontHandle
        frontOfficeWindowTitle = [string]$FrontOffice.Window.Current.Name
        frontOfficeWindowClass = [string]$FrontOffice.Window.Current.ClassName
        autoTradingState = $AutoTradingState
    }
}

function Save-WindowPng([System.Windows.Automation.AutomationElement]$Window, [string]$Path) {
    if ([System.IO.File]::Exists($Path)) { Stop-Adapter "screenshot_path_exists" }
    $handle = [IntPtr]$Window.Current.NativeWindowHandle
    $rect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($handle, [ref]$rect)) { Stop-Adapter "screenshot_bounds_failed" }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 320 -or $height -lt 240 -or $width -gt 10000 -or $height -gt 10000) {
        Stop-Adapter "screenshot_bounds_invalid"
    }
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $hdc = $graphics.GetHdc()
    try {
        $printed = [MetafxVisibleNative]::PrintWindow($handle, $hdc, 2)
    } finally {
        $graphics.ReleaseHdc($hdc)
        $graphics.Dispose()
    }
    try {
        if (-not $printed) { Stop-Adapter "screenshot_capture_failed" }
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $bitmap.Dispose()
    }
    if (-not [System.IO.File]::Exists($Path) -or (Get-Item -LiteralPath $Path).Length -lt 1024) {
        Stop-Adapter "screenshot_capture_invalid"
    }
}

function Assert-ExistingPngEvidence([string]$Path, [string]$FailureCode) {
    if (-not [System.IO.File]::Exists($Path)) { Stop-Adapter $FailureCode }
    $item = Get-Item -LiteralPath $Path
    if ($item.Length -lt 1024) { Stop-Adapter $FailureCode }
    $stream = $null
    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::Read
        )
        $header = New-Object byte[] 8
        if ($stream.Read($header, 0, $header.Length) -ne $header.Length -or
            [BitConverter]::ToString($header) -ne "89-50-4E-47-0D-0A-1A-0A") {
            Stop-Adapter $FailureCode
        }
    } catch {
        if ([string]$_.Exception.Message -like "METAFX_VISIBLE:*") { throw }
        Stop-Adapter $FailureCode
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

function Find-MenuCommand([IntPtr]$Menu, [string]$ExpectedText) {
    if ($Menu -eq [IntPtr]::Zero) { return $null }
    $count = [MetafxVisibleNative]::GetMenuItemCount($Menu)
    for ($position = 0; $position -lt $count; $position++) {
        $buffer = New-Object System.Text.StringBuilder 512
        [void][MetafxVisibleNative]::GetMenuString($Menu, [uint32]$position, $buffer, $buffer.Capacity, 0x400)
        $label = ($buffer.ToString() -replace '&', '' -replace '\t.*$', '').Trim()
        $sub = [MetafxVisibleNative]::GetSubMenu($Menu, $position)
        if ($sub -ne [IntPtr]::Zero) {
            $nested = Find-MenuCommand $sub $ExpectedText
            if ($null -ne $nested) { return $nested }
        }
        if ($label -eq $ExpectedText) {
            $id = [MetafxVisibleNative]::GetMenuItemID($Menu, $position)
            if ($id -ne 0xFFFFFFFF) { return [int]$id }
        }
    }
    return $null
}

function Find-MenuItemLocations([IntPtr]$Menu, [string]$ExpectedText) {
    $matches = @()
    if ($Menu -eq [IntPtr]::Zero) { return $matches }
    $count = [MetafxVisibleNative]::GetMenuItemCount($Menu)
    if ($count -lt 0 -or $count -gt 256) { return $matches }
    for ($position = 0; $position -lt $count; $position++) {
        $buffer = New-Object System.Text.StringBuilder 512
        [void][MetafxVisibleNative]::GetMenuString($Menu, [uint32]$position, $buffer, $buffer.Capacity, 0x400)
        $label = ($buffer.ToString() -replace '&', '' -replace '\t.*$', '').Trim()
        $sub = [MetafxVisibleNative]::GetSubMenu($Menu, $position)
        if ($sub -ne [IntPtr]::Zero) {
            $matches += @(Find-MenuItemLocations $sub $ExpectedText)
        }
        if ($label -eq $ExpectedText) {
            $id = [MetafxVisibleNative]::GetMenuItemID($Menu, $position)
            if ($id -ne 0xFFFFFFFF) {
                $matches += [pscustomobject]@{
                    menu = $Menu
                    position = [int]$position
                    command = [int]$id
                    label = $label
                }
            }
        }
    }
    return @($matches)
}

function Dismiss-OwnedPopup([IntPtr]$PopupHandle) {
    if ($PopupHandle -eq [IntPtr]::Zero -or -not [MetafxVisibleNative]::IsWindow($PopupHandle)) { return }
    [void][MetafxVisibleNative]::PostMessage(
        $PopupHandle,
        [MetafxVisibleNative]::WM_KEYDOWN,
        [IntPtr]0x1B,
        [IntPtr]::Zero
    )
    [void][MetafxVisibleNative]::PostMessage(
        $PopupHandle,
        [MetafxVisibleNative]::WM_KEYUP,
        [IntPtr]0x1B,
        [IntPtr]::Zero
    )
}

function Get-CursorSnapshot([string]$FailureCode) {
    $point = New-Object MetafxVisibleNative+POINT
    if (-not [MetafxVisibleNative]::GetCursorPos([ref]$point)) {
        Stop-Adapter ("{0}_cursor_read_failed" -f $FailureCode)
    }
    return $point
}

function Restore-CursorSnapshot([object]$Point, [string]$FailureCode) {
    if ($null -eq $Point) {
        Stop-Adapter ("{0}_cursor_restore_snapshot_missing" -f $FailureCode)
    }
    if (-not [MetafxVisibleNative]::SetCursorPos([int]$Point.X, [int]$Point.Y)) {
        Stop-Adapter ("{0}_cursor_restore_failed" -f $FailureCode)
    }
    $observed = New-Object MetafxVisibleNative+POINT
    if (-not [MetafxVisibleNative]::GetCursorPos([ref]$observed) -or
        $observed.X -ne [int]$Point.X -or $observed.Y -ne [int]$Point.Y) {
        Stop-Adapter ("{0}_cursor_restore_mismatch" -f $FailureCode)
    }
}

function Invoke-PhysicalMouseClickAtScreenPoint(
    [int]$ScreenX,
    [int]$ScreenY,
    [ValidateSet("left", "right")][string]$Button,
    [string]$FailureCode
) {
    if (-not [MetafxVisibleNative]::SetCursorPos($ScreenX, $ScreenY)) {
        Stop-Adapter ("{0}_cursor_move_failed" -f $FailureCode)
    }
    $observed = New-Object MetafxVisibleNative+POINT
    if (-not [MetafxVisibleNative]::GetCursorPos([ref]$observed) -or
        $observed.X -ne $ScreenX -or $observed.Y -ne $ScreenY) {
        Stop-Adapter ("{0}_cursor_position_mismatch" -f $FailureCode)
    }
    if (-not [MetafxVisibleNative]::SendMouseClick($Button -eq "right")) {
        Stop-Adapter ("{0}_send_input_failed" -f $FailureCode)
    }
}

function Invoke-ExactNativeTesterTabClick(
    [IntPtr]$TabHandle,
    [IntPtr]$ExpectedTesterHandle,
    [IntPtr]$ExpectedTerminalHandle,
    [int]$ProcessId,
    [int]$ClientX,
    [int]$ClientY,
    [string]$FailureCode
) {
    # MT4's owner-drawn Strategy Tester tab strip can report IsEnabled=false
    # through UIA and can ignore a real SendInput mouse click. A synchronous
    # native click is permitted only for the exact, already-bound child HWND;
    # the caller must still validate the complete destination surface after it.
    if ($TabHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($TabHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($TabHandle) -or
        (Get-WindowOwner $TabHandle) -ne $ProcessId -or
        (Get-WindowClass $TabHandle) -ne "AfxWnd140s" -or
        [MetafxVisibleNative]::GetDlgCtrlID($TabHandle) -ne 1137 -or
        (([MetafxVisibleNative]::GetWindowLong(
            $TabHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0)) {
        Stop-Adapter ("{0}_identity_invalid" -f $FailureCode)
    }
    [IntPtr]$testerHandle = [MetafxVisibleNative]::GetParent($TabHandle)
    if ($ExpectedTesterHandle -eq [IntPtr]::Zero -or
        $testerHandle -ne $ExpectedTesterHandle -or
        -not [MetafxVisibleNative]::IsWindow($testerHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($testerHandle) -or
        (Get-WindowOwner $testerHandle) -ne $ProcessId -or
        [MetafxVisibleNative]::GetDlgCtrlID($testerHandle) -ne 83 -or
        (([MetafxVisibleNative]::GetWindowLong(
            $testerHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0)) {
        Stop-Adapter ("{0}_parent_invalid" -f $FailureCode)
    }
    if ($ExpectedTerminalHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($ExpectedTerminalHandle) -or
        (Get-WindowOwner $ExpectedTerminalHandle) -ne $ProcessId -or
        (Get-WindowClass $ExpectedTerminalHandle) -ne "MetaQuotes::MetaTrader::4.00" -or
        [MetafxVisibleNative]::GetAncestor(
            $testerHandle,
            [MetafxVisibleNative]::GA_ROOT
        ) -ne $ExpectedTerminalHandle) {
        Stop-Adapter ("{0}_terminal_invalid" -f $FailureCode)
    }
    $tabRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($TabHandle, [ref]$tabRect)) {
        Stop-Adapter ("{0}_bounds_unavailable" -f $FailureCode)
    }
    [int]$width = $tabRect.Right - $tabRect.Left
    [int]$height = $tabRect.Bottom - $tabRect.Top
    if ($width -le 0 -or $height -le 0 -or
        $ClientX -gt 32767 -or $ClientY -gt 32767 -or
        $ClientX -lt 0 -or $ClientX -ge $width -or
        $ClientY -lt 0 -or $ClientY -ge $height) {
        Stop-Adapter ("{0}_point_out_of_bounds" -f $FailureCode)
    }
    [void][MetafxVisibleNative]::SetFocus($TabHandle)
    [int]$packedPoint = (($ClientY -band 0xffff) -shl 16) -bor ($ClientX -band 0xffff)
    [IntPtr]$nativeResult = [IntPtr]::Zero
    [IntPtr]$downCall = [MetafxVisibleNative]::SendMessageTimeout(
        $TabHandle,
        [MetafxVisibleNative]::WM_LBUTTONDOWN,
        [IntPtr]1,
        [IntPtr]$packedPoint,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG,
        2000,
        [ref]$nativeResult
    )
    if ($downCall -eq [IntPtr]::Zero) {
        Stop-Adapter ("{0}_button_down_timeout" -f $FailureCode)
    }
    $nativeResult = [IntPtr]::Zero
    [IntPtr]$upCall = [MetafxVisibleNative]::SendMessageTimeout(
        $TabHandle,
        [MetafxVisibleNative]::WM_LBUTTONUP,
        [IntPtr]::Zero,
        [IntPtr]$packedPoint,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG,
        2000,
        [ref]$nativeResult
    )
    if ($upCall -eq [IntPtr]::Zero) {
        Stop-Adapter ("{0}_button_up_timeout" -f $FailureCode)
    }
}

function Invoke-ExactPopupMenuItem(
    [IntPtr]$PopupHandle,
    [int]$ProcessId,
    [string]$ExpectedText,
    [string]$FailureCode
) {
    if ($PopupHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($PopupHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($PopupHandle) -or
        (Get-WindowOwner $PopupHandle) -ne $ProcessId -or
        (Get-WindowClass $PopupHandle) -ne "#32768") {
        Stop-Adapter ("{0}_popup_identity_invalid" -f $FailureCode)
    }
    $rootMenu = Invoke-TargetMessage $PopupHandle ([MetafxVisibleNative]::MN_GETHMENU) 0 0
    $matches = @(Find-MenuItemLocations $rootMenu $ExpectedText)
    if ($matches.Count -ne 1) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_item_ambiguous" -f $FailureCode)
    }
    $item = $matches[0]
    # The MT4 Navigator and Tester menus currently expose these actions as
    # top-level popup items.  Reject nested matches rather than clicking a
    # coordinate for a submenu that has not been visibly opened.
    if ([IntPtr]$item.menu -ne $rootMenu) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_nested_item_unsupported" -f $FailureCode)
    }
    [uint32]$itemState = [MetafxVisibleNative]::GetMenuState(
        [IntPtr]$item.menu,
        [uint32]$item.position,
        [MetafxVisibleNative]::MF_BYPOSITION
    )
    if ($itemState -eq [uint32]::MaxValue -or
        ($itemState -band (
            [MetafxVisibleNative]::MF_GRAYED -bor
            [MetafxVisibleNative]::MF_DISABLED -bor
            [MetafxVisibleNative]::MF_SEPARATOR
        )) -ne 0) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_item_disabled" -f $FailureCode)
    }
    $itemRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetMenuItemRect(
        [IntPtr]::Zero,
        [IntPtr]$item.menu,
        [uint32]$item.position,
        [ref]$itemRect
    )) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_item_bounds_unavailable" -f $FailureCode)
    }
    $popupRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($PopupHandle, [ref]$popupRect)) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_popup_bounds_unavailable" -f $FailureCode)
    }
    $screenX = [int](($itemRect.Left + $itemRect.Right) / 2)
    $screenY = [int](($itemRect.Top + $itemRect.Bottom) / 2)
    if ($itemRect.Right -le $itemRect.Left -or $itemRect.Bottom -le $itemRect.Top -or
        $screenX -lt $popupRect.Left -or $screenX -ge $popupRect.Right -or
        $screenY -lt $popupRect.Top -or $screenY -ge $popupRect.Bottom) {
        Dismiss-OwnedPopup $PopupHandle
        Stop-Adapter ("{0}_item_bounds_invalid" -f $FailureCode)
    }
    Invoke-PhysicalMouseClickAtScreenPoint `
        $screenX `
        $screenY `
        "left" `
        ("{0}_item" -f $FailureCode)
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        Start-Sleep -Milliseconds 50
        if (-not [MetafxVisibleNative]::IsWindow($PopupHandle) -or
            -not [MetafxVisibleNative]::IsWindowVisible($PopupHandle)) {
            return [int]$item.command
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    Dismiss-OwnedPopup $PopupHandle
    Stop-Adapter ("{0}_popup_not_dismissed" -f $FailureCode)
}

function Ensure-TesterVisible([pscustomobject]$Terminal) {
    $processId = [int]$Terminal.Process.Id
    $window = $Terminal.Window
    try {
        [void](Get-TesterPane $window $processId)
        return
    } catch { }
    Restore-Foreground $window
    $menu = [MetafxVisibleNative]::GetMenu([IntPtr]$window.Current.NativeWindowHandle)
    $command = Find-MenuCommand $menu "Strategy Tester"
    if ($null -eq $command) { Stop-Adapter "strategy_tester_menu_unavailable" }
    [void](Invoke-TargetMessage ([IntPtr]$window.Current.NativeWindowHandle) ([MetafxVisibleNative]::WM_COMMAND) $command 0)
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 200
        try {
            [void](Get-TesterPane $window $processId)
            return
        } catch { }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "strategy_tester_not_ready"
}

function Read-ExpertSelection(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId
) {
    $combo = Get-UniqueControl $TesterPane "1128" $ProcessId
    $runtime = Get-ComboRuntimeInfo $combo $ProcessId
    $comboHandle = [IntPtr]$runtime.handle
    $edits = @(Find-DescendantsById $combo "6217")
    if ($edits.Count -ne 1) { Stop-Adapter "expert_edit_ambiguous" }
    $edit = $edits[0]
    $editHandle = [IntPtr]$edit.Current.NativeWindowHandle
    if ($editHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $editHandle) -ne $ProcessId) {
        Stop-Adapter "expert_edit_owner_mismatch"
    }
    $comboName = ([string]$combo.Current.Name).Trim()
    $editName = ([string]$edit.Current.Name).Trim()
    $winText = Read-Win32Text $editHandle
    if (-not $comboName -or -not $editName -or -not $winText) { Stop-Adapter "expert_readback_empty" }
    if ($comboName -ne $editName -or $editName -ne $winText) { Stop-Adapter "expert_readback_mismatch" }
    # MT4's editable Expert combo advertises CBS_HASSTRINGS even when it is in
    # its custom value-only state (CB_GETCOUNT=0 / CB_GETCURSEL=-1).  In that
    # state there is deliberately no native list item to compare; the exact
    # value is instead bound by the combo, child edit, Win32 text, unique
    # Navigator registration, deployed binary digest, and the later visible
    # Expert Properties/input readback.  Compare CB_GETLBTEXT only when the
    # runtime proved that a native selected list item actually exists.
    if ($runtime.nativeListAvailable -and $runtime.hasStrings -and
        $runtime.listedValue -ne $comboName) {
        Stop-Adapter "expert_combo_list_readback_mismatch"
    }
    return [ordered]@{
        combo = $combo
        edit = $edit
        value = $comboName
        comboHandle = $comboHandle
        editHandle = $editHandle
        selectedIndex = $runtime.index
        itemCount = $runtime.count
        ownerDraw = $runtime.ownerDraw
        hasStrings = $runtime.hasStrings
    }
}

function Normalize-ExpertName([string]$Value) {
    return (($Value -replace '/', '\').TrimStart('\')).ToLowerInvariant()
}

function Test-ExactExpertValue([string]$Actual, [string]$ExpectedUiPath, [string]$FileName) {
    $normalized = Normalize-ExpertName $Actual
    $expectedWithExtension = (Normalize-ExpertName ($ExpectedUiPath + ".ex4"))
    $expectedAsGiven = Normalize-ExpertName $ExpectedUiPath
    # A basename-only result is ambiguous for the deliberately nested unique
    # deployment and is therefore never accepted.
    if ($normalized -eq (Normalize-ExpertName $FileName)) { return $false }
    return ($normalized -eq $expectedWithExtension -or $normalized -eq $expectedAsGiven)
}

function Send-BalancedKey([IntPtr]$Handle, [int]$VirtualKey) {
    [void](Invoke-TargetMessage $Handle ([MetafxVisibleNative]::WM_KEYDOWN) $VirtualKey 0)
    try { Start-Sleep -Milliseconds 35 }
    finally { [void](Invoke-TargetMessage $Handle ([MetafxVisibleNative]::WM_KEYUP) $VirtualKey 0) }
}

function Select-ExactExpert(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId,
    [string]$ExpectedUiPath,
    [string]$FileName,
    [int]$MaximumSteps
) {
    if ($MaximumSteps -lt 1 -or $MaximumSteps -gt 512) { Stop-Adapter "expert_selection_bound_invalid" }
    if ($FileName -notmatch '^[A-Za-z0-9_.-]{1,128}\.ex4$') {
        Stop-Adapter "expert_file_name_invalid"
    }
    $expertStem = [System.IO.Path]::GetFileNameWithoutExtension($FileName)
    $expectedPattern = (
        '^Metafxclub\\AgentHQ\\(ea-visible-[a-f0-9]{24})\\' +
        [regex]::Escape($expertStem) + '$'
    )
    $expectedMatch = [regex]::Match($ExpectedUiPath, $expectedPattern)
    if (-not $expectedMatch.Success) {
        Stop-Adapter "expert_ui_path_invalid"
    }
    $operationFolder = [string]$expectedMatch.Groups[1].Value
    $tester = Get-TesterPane $TerminalWindow $ProcessId
    $readback = Read-ExpertSelection $tester $ProcessId
    if (Test-ExactExpertValue $readback.value $ExpectedUiPath $FileName) { return $readback.value }

    # This MT4 build exposes the Expert picker as a custom value-only combo:
    # CB_GETCOUNT=0 and typed WM_SETTEXT values are restored to the previous
    # Expert after Enter. Open its visible tree, bind the full verified
    # Metafxclub/AgentHQ/operation/file hierarchy, and commit only that leaf.
    Restore-Foreground $TerminalWindow
    $showResult = Invoke-TargetMessage `
        $readback.comboHandle `
        ([MetafxVisibleNative]::CB_SHOWDROPDOWN) `
        1 `
        0
    if ($showResult.ToInt32() -eq 0) { Stop-Adapter "expert_picker_open_failed" }
    [IntPtr]$pickerHandle = [IntPtr]::Zero
    try {
        $pickerHandle = Wait-UniqueOwnedPopupHandle `
            $ProcessId `
            "SysTreeView32" `
            "expert_picker_tree_unavailable"
        $comboRect = New-Object MetafxVisibleNative+RECT
        $pickerRect = New-Object MetafxVisibleNative+RECT
        if (-not [MetafxVisibleNative]::GetWindowRect($readback.comboHandle, [ref]$comboRect) -or
            -not [MetafxVisibleNative]::GetWindowRect($pickerHandle, [ref]$pickerRect) -or
            $comboRect.Right -le $comboRect.Left -or
            $comboRect.Bottom -le $comboRect.Top -or
            [Math]::Abs($pickerRect.Left - $comboRect.Left) -gt 4 -or
            [Math]::Abs($pickerRect.Right - $comboRect.Right) -gt 4 -or
            $pickerRect.Top -lt ($comboRect.Bottom - 2) -or
            $pickerRect.Top -gt ($comboRect.Bottom + 4) -or
            $pickerRect.Bottom -le ($pickerRect.Top + 30)) {
            Stop-Adapter "expert_picker_bounds_invalid"
        }
        [string[]]$folderPath = @("Metafxclub", "AgentHQ", $operationFolder)
        [string[]]$expertPath = @("Metafxclub", "AgentHQ", $operationFolder, $FileName)
        $leafCount = [MetafxVisibleMsaa]::CountExactPath($pickerHandle, $expertPath)
        if ($leafCount -gt 1) { Stop-Adapter "expert_picker_leaf_ambiguous" }
        if ($leafCount -eq 0) {
            if ([MetafxVisibleMsaa]::CountExactPath($pickerHandle, $folderPath) -ne 1 -or
                -not [MetafxVisibleMsaa]::SelectUniqueExactPath($pickerHandle, $folderPath)) {
                Stop-Adapter "expert_picker_folder_unavailable"
            }
            [void][MetafxVisibleNative]::SetFocus($pickerHandle)
            Send-BalancedKey $pickerHandle 0x27
            for ($step = 0; $step -lt $MaximumSteps; $step++) {
                Start-Sleep -Milliseconds 50
                $leafCount = [MetafxVisibleMsaa]::CountExactPath($pickerHandle, $expertPath)
                if ($leafCount -gt 1) { Stop-Adapter "expert_picker_leaf_ambiguous" }
                if ($leafCount -eq 1) { break }
            }
        }
        if ($leafCount -ne 1) { Stop-Adapter "expert_picker_leaf_unavailable" }
        if (-not [MetafxVisibleMsaa]::SelectUniqueExactPath($pickerHandle, $expertPath) -or
            -not [MetafxVisibleMsaa]::IsUniqueExactPathSelected($pickerHandle, $expertPath)) {
            Stop-Adapter "expert_picker_leaf_selection_failed"
        }
        Send-BalancedKey $pickerHandle 0x0D
        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        do {
            Start-Sleep -Milliseconds 50
            if (-not [MetafxVisibleNative]::IsWindowVisible($pickerHandle)) { break }
        } while ([DateTime]::UtcNow -lt $deadline)
        if ([MetafxVisibleNative]::IsWindowVisible($pickerHandle)) {
            Stop-Adapter "expert_picker_commit_not_dismissed"
        }
    } finally {
        if ($pickerHandle -ne [IntPtr]::Zero -and
            [MetafxVisibleNative]::IsWindowVisible($pickerHandle)) {
            Dismiss-OwnedPopup $pickerHandle
        }
    }
    Start-Sleep -Milliseconds 250
    $final = Read-ExpertSelection (Get-TesterPane $TerminalWindow $ProcessId) $ProcessId
    if (Test-ExactExpertValue $final.value $ExpectedUiPath $FileName) {
        return $final.value
    }
    Stop-Adapter "expert_exact_value_not_applied"
}

function Read-ButtonCheck([System.Windows.Automation.AutomationElement]$Button) {
    [IntPtr]$stateResult = [IntPtr]::Zero
    $stateCall = [MetafxVisibleNative]::SendMessageTimeout(
        [IntPtr]$Button.Current.NativeWindowHandle,
        [MetafxVisibleNative]::BM_GETCHECK,
        [IntPtr]::Zero, [IntPtr]::Zero,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG, 1500, [ref]$stateResult
    )
    if ($stateCall -eq [IntPtr]::Zero) { Stop-Adapter "checkbox_state_timeout" }
    $state = $stateResult.ToInt32()
    if ($state -notin @(0, 1)) { Stop-Adapter "checkbox_state_unreadable" }
    return ($state -eq 1)
}

function Get-TesterCheckControl(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId,
    [string]$AutomationId
) {
    $expectedName = switch ($AutomationId) {
        "1023" { "Use date" }
        "1029" { "Optimization" }
        "1400" { "Visual mode" }
        default { Stop-Adapter "tester_checkbox_id_unsupported" }
    }
    $button = Get-UniqueControl $TesterPane $AutomationId $ProcessId
    $name = (([string]$button.Current.Name) -replace '&', '').Trim()
    if ([string]$button.Current.ClassName -ne "Button" -or
        -not $name.Equals($expectedName, [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Adapter ("checkbox_{0}_semantic_mismatch" -f $AutomationId)
    }
    return $button
}

function Set-ButtonCheck(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId,
    [string]$AutomationId,
    [bool]$Expected
) {
    $button = Get-TesterCheckControl $TesterPane $ProcessId $AutomationId
    $current = Read-ButtonCheck $button
    if ($current -ne $Expected) {
        [void](Invoke-TargetMessage ([IntPtr]$button.Current.NativeWindowHandle) ([MetafxVisibleNative]::BM_CLICK) 0 0)
        Start-Sleep -Milliseconds 150
        $button = Get-TesterCheckControl $TesterPane $ProcessId $AutomationId
        $current = Read-ButtonCheck $button
    }
    if ($current -ne $Expected) { Stop-Adapter ("checkbox_{0}_not_applied" -f $AutomationId) }
    return $current
}

function Read-NativeComboListValue([IntPtr]$Handle, [int]$Index) {
    $length = (Invoke-TargetMessage $Handle ([MetafxVisibleNative]::CB_GETLBTEXTLEN) $Index 0).ToInt32()
    if ($length -lt 1 -or $length -gt 4096) { Stop-Adapter "tester_combo_list_text_length_invalid" }
    $buffer = New-Object System.Text.StringBuilder ($length + 2)
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxVisibleNative]::SendMessageTimeout(
        $Handle,
        [MetafxVisibleNative]::CB_GETLBTEXT,
        [IntPtr]$Index,
        $buffer,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG,
        1500,
        [ref]$result
    )
    if ($call -eq [IntPtr]::Zero -or $result.ToInt32() -ne $length) {
        Stop-Adapter "tester_combo_list_text_unavailable"
    }
    return $buffer.ToString().Trim()
}

function Test-TesterComboValue(
    [string]$AutomationId,
    [string]$Actual,
    [string]$ExpectedPrefix
) {
    $value = ([string]$Actual).Trim()
    if ($AutomationId -eq "1228") {
        $accepted = switch ($ExpectedPrefix.ToUpperInvariant()) {
            "D1" { @("D1", "Daily") }
            "W1" { @("W1", "Weekly") }
            "MN1" { @("MN1", "Monthly") }
            default { @($ExpectedPrefix) }
        }
        return @($accepted | Where-Object {
            $value.Equals([string]$_, [System.StringComparison]::OrdinalIgnoreCase)
        }).Count -eq 1
    }
    return $value.StartsWith($ExpectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Read-SelectedNativeComboValue(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId,
    [string]$AutomationId
) {
    $combo = Get-UniqueControl $TesterPane $AutomationId $ProcessId
    [IntPtr]$handle = [IntPtr]$combo.Current.NativeWindowHandle
    if ([string]$combo.Current.ClassName -ne "ComboBox" -or
        $handle -eq [IntPtr]::Zero -or (Get-WindowOwner $handle) -ne $ProcessId) {
        Stop-Adapter ("combo_{0}_readback_identity_invalid" -f $AutomationId)
    }
    $count = (Invoke-TargetMessage $handle ([MetafxVisibleNative]::CB_GETCOUNT) 0 0).ToInt32()
    $index = (Invoke-TargetMessage $handle ([MetafxVisibleNative]::CB_GETCURSEL) 0 0).ToInt32()
    if ($count -lt 1 -or $count -gt 4096 -or $index -lt 0 -or $index -ge $count) {
        Stop-Adapter ("combo_{0}_readback_index_invalid" -f $AutomationId)
    }
    return Read-NativeComboListValue $handle $index
}

function Select-ComboListItem(
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId,
    [string]$AutomationId,
    [string]$ExpectedPrefix
) {
    $combo = Get-UniqueControl $TesterPane $AutomationId $ProcessId
    if ([string]$combo.Current.ClassName -ne "ComboBox") {
        Stop-Adapter ("combo_{0}_class_mismatch" -f $AutomationId)
    }
    [IntPtr]$comboHandle = [IntPtr]$combo.Current.NativeWindowHandle
    if ($comboHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $comboHandle) -ne $ProcessId) {
        Stop-Adapter ("combo_{0}_owner_mismatch" -f $AutomationId)
    }
    $style = [MetafxVisibleNative]::GetWindowLong($comboHandle, [MetafxVisibleNative]::GWL_STYLE)
    $ownerDraw = (($style -band [MetafxVisibleNative]::CBS_OWNERDRAWFIXED) -ne 0 -or
        ($style -band [MetafxVisibleNative]::CBS_OWNERDRAWVARIABLE) -ne 0)
    $hasStrings = (($style -band [MetafxVisibleNative]::CBS_HASSTRINGS) -ne 0)
    if ($ownerDraw -and -not $hasStrings) {
        Stop-Adapter ("combo_{0}_owner_draw_without_strings" -f $AutomationId)
    }
    $count = (Invoke-TargetMessage $comboHandle ([MetafxVisibleNative]::CB_GETCOUNT) 0 0).ToInt32()
    if ($count -lt 1 -or $count -gt 4096) {
        Stop-Adapter ("combo_{0}_count_invalid" -f $AutomationId)
    }
    $matches = New-Object System.Collections.Generic.List[int]
    for ($index = 0; $index -lt $count; $index++) {
        $candidate = Read-NativeComboListValue $comboHandle $index
        if (Test-TesterComboValue $AutomationId $candidate $ExpectedPrefix) {
            [void]$matches.Add($index)
        }
    }
    if ($matches.Count -ne 1) {
        Stop-Adapter ("combo_{0}_item_ambiguous" -f $AutomationId)
    }
    $selected = (Invoke-TargetMessage $comboHandle ([MetafxVisibleNative]::CB_SETCURSEL) $matches[0] 0).ToInt32()
    if ($selected -ne $matches[0]) { Stop-Adapter ("combo_{0}_selection_failed" -f $AutomationId) }
    [IntPtr]$parent = [MetafxVisibleNative]::GetParent($comboHandle)
    $controlId = [MetafxVisibleNative]::GetDlgCtrlID($comboHandle)
    if ($parent -eq [IntPtr]::Zero -or (Get-WindowOwner $parent) -ne $ProcessId -or
        [string]$controlId -ne $AutomationId) {
        Stop-Adapter ("combo_{0}_parent_invalid" -f $AutomationId)
    }
    $notification = (([MetafxVisibleNative]::CBN_SELCHANGE -shl 16) -bor ($controlId -band 0xFFFF))
    $notificationPosted = [MetafxVisibleNative]::PostMessage(
        $parent,
        [MetafxVisibleNative]::WM_COMMAND,
        [IntPtr]$notification,
        $comboHandle
    )
    if (-not $notificationPosted) {
        Stop-Adapter ("combo_{0}_notification_failed" -f $AutomationId)
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        Start-Sleep -Milliseconds 100
        $combo = Get-UniqueControl $TesterPane $AutomationId $ProcessId
        [IntPtr]$readbackHandle = [IntPtr]$combo.Current.NativeWindowHandle
        if ($readbackHandle -ne $comboHandle) {
            Stop-Adapter ("combo_{0}_handle_changed" -f $AutomationId)
        }
        $selectedReadback = (Invoke-TargetMessage $comboHandle ([MetafxVisibleNative]::CB_GETCURSEL) 0 0).ToInt32()
        if ($selectedReadback -lt 0 -or $selectedReadback -ge $count) { continue }
        $actual = Read-NativeComboListValue $comboHandle $selectedReadback
        $selectedItems = @()
        try {
            $selectionPattern = $combo.GetCurrentPattern(
                [System.Windows.Automation.SelectionPattern]::Pattern
            )
            $selectedItems = @($selectionPattern.Current.GetSelection())
        } catch { continue }
        if ($selectedItems.Count -ne 1 -or
            [int]$selectedItems[0].Current.ProcessId -ne $ProcessId) { continue }
        # Owner-draw MT4 combos expose Current.Name as the static labels
        # "Period:"/"Model:".  Bind UIA evidence to the selected child item.
        $uiaReadback = ([string]$selectedItems[0].Current.Name).Trim()
        if ($selectedReadback -eq $matches[0] -and
            (Test-TesterComboValue $AutomationId $actual $ExpectedPrefix) -and
            (Test-TesterComboValue $AutomationId $uiaReadback $ExpectedPrefix) -and
            $uiaReadback.Equals($actual, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $actual
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter ("combo_{0}_readback_mismatch" -f $AutomationId)
}

function Read-CurrentSymbol([System.Windows.Automation.AutomationElement]$TesterPane, [int]$ProcessId) {
    $combo = Get-UniqueControl $TesterPane "1347" $ProcessId
    [IntPtr]$comboHandle = [IntPtr]$combo.Current.NativeWindowHandle
    if ([string]$combo.Current.ClassName -ne "ComboBox" -or
        $comboHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $comboHandle) -ne $ProcessId) {
        Stop-Adapter "tester_symbol_control_invalid"
    }
    # This MT4 owner-draw combo exposes Current.Name as the static label
    # "Symbol:".  The selected item is available through SelectionPattern.
    try {
        $pattern = $combo.GetCurrentPattern(
            [System.Windows.Automation.SelectionPattern]::Pattern
        )
        $selected = @($pattern.Current.GetSelection())
    } catch {
        Stop-Adapter "tester_symbol_selection_unavailable"
    }
    if ($selected.Count -ne 1 -or
        [int]$selected[0].Current.ProcessId -ne $ProcessId) {
        Stop-Adapter "tester_symbol_selection_ambiguous"
    }
    $value = ([string]$selected[0].Current.Name).Trim()
    $symbol = ($value -split ',')[0].Trim()
    if ($symbol -notmatch '^[A-Za-z0-9._#-]{1,40}$') { Stop-Adapter "tester_symbol_readback_invalid" }
    return $symbol
}

function Read-Spread([System.Windows.Automation.AutomationElement]$TesterPane, [int]$ProcessId) {
    $edit = Get-UniqueControl $TesterPane "1001" $ProcessId
    if ([string]$edit.Current.ClassName -ne "Edit") { Stop-Adapter "tester_spread_control_invalid" }
    $value = Read-Win32Text ([IntPtr]$edit.Current.NativeWindowHandle)
    if (-not $value -or $value.Length -gt 40) { Stop-Adapter "tester_spread_readback_invalid" }
    return $value
}

function Get-TesterStartButton([System.Windows.Automation.AutomationElement]$TesterPane, [int]$ProcessId) {
    $button = Get-UniqueControl $TesterPane "1034" $ProcessId
    $name = ([string]$button.Current.Name).Trim()
    if ([string]$button.Current.ClassName -ne "Button" -or $name -notin @("Start", "Stop")) {
        Stop-Adapter "tester_start_control_semantic_mismatch"
    }
    return $button
}

function Refresh-ExpertInventory(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId,
    [string]$ExpectedUiPath,
    [string]$ExpertFileName
) {
    $start = $null
    try {
        $tester = Get-TesterPane $TerminalWindow $ProcessId
        $start = Get-TesterStartButton $tester $ProcessId
        if (([string]$start.Current.Name).Trim() -ne "Start") { Stop-Adapter "tester_not_idle" }
    } catch { Stop-Adapter "tester_not_idle" }
    if ($ExpertFileName -notmatch '^[A-Za-z0-9_.-]{1,128}\.ex4$') {
        Stop-Adapter "navigator_expert_file_name_invalid"
    }
    $expertStem = [System.IO.Path]::GetFileNameWithoutExtension($ExpertFileName)
    $expectedPattern = (
        '^Metafxclub\\AgentHQ\\(ea-visible-[a-f0-9]{24})\\' +
        [regex]::Escape($expertStem) + '$'
    )
    $expectedMatch = [regex]::Match($ExpectedUiPath, $expectedPattern)
    if (-not $expectedMatch.Success) {
        Stop-Adapter "navigator_expert_ui_path_invalid"
    }
    $operationFolder = [string]$expectedMatch.Groups[1].Value
    $tree = Get-UniqueControl $TerminalWindow "35439" $ProcessId
    [IntPtr]$treeHandle = [IntPtr]$tree.Current.NativeWindowHandle
    if ([string]$tree.Current.ClassName -ne "SysTreeView32" -or
        $treeHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $treeHandle) -ne $ProcessId) {
        Stop-Adapter "navigator_tree_unavailable"
    }
    if (-not [MetafxVisibleMsaa]::SelectUniqueExactName($treeHandle, "Expert Advisors")) {
        Stop-Adapter "navigator_expert_advisors_selection_failed"
    }
    # The same compiled basename may legitimately exist under older operation
    # folders. Bind refresh readiness to this operation's unique folder token,
    # then require the full path again in Select-ExactExpert before Start.
    $count = [MetafxVisibleMsaa]::CountExactName($treeHandle, $operationFolder)
    if ($count -gt 1) { Stop-Adapter "navigator_expert_registration_ambiguous" }
    if ($count -eq 0) {
        Restore-Foreground $TerminalWindow
        # MSAA can select an exact tree item without scrolling it into the
        # visible viewport.  Bind the native caret to that already-verified
        # selection and ask the TreeView itself to reveal it before deriving
        # mouse coordinates.  No name guessing or unrelated tree navigation
        # is involved.
        [IntPtr]$selectedTreeItem = Invoke-TargetMessage `
            $treeHandle `
            ([MetafxVisibleNative]::TVM_GETNEXTITEM) `
            ([MetafxVisibleNative]::TVGN_CARET) `
            0
        if ($selectedTreeItem -eq [IntPtr]::Zero) {
            Stop-Adapter "navigator_refresh_selection_unavailable"
        }
        [void](Invoke-TargetMessage `
            $treeHandle `
            ([MetafxVisibleNative]::TVM_ENSUREVISIBLE) `
            0 `
            $selectedTreeItem.ToInt32())
        Start-Sleep -Milliseconds 200
        [int]$anchorX = 0
        [int]$anchorY = 0
        if (-not [MetafxVisibleMsaa]::TrySelectUniqueExactNameCenter(
            $treeHandle,
            "Expert Advisors",
            0x24,
            [ref]$anchorX,
            [ref]$anchorY
        )) {
            Stop-Adapter "navigator_refresh_anchor_unavailable"
        }
        $treeRect = New-Object MetafxVisibleNative+RECT
        if (-not [MetafxVisibleNative]::GetWindowRect($treeHandle, [ref]$treeRect) -or
            $anchorX -lt $treeRect.Left -or $anchorX -ge $treeRect.Right -or
            $anchorY -lt $treeRect.Top -or $anchorY -ge $treeRect.Bottom) {
            Stop-Adapter "navigator_refresh_anchor_invalid"
        }
        try { $tree.SetFocus() } catch { }
        [void][MetafxVisibleNative]::SetFocus($treeHandle)
        $cursorSnapshot = Get-CursorSnapshot "navigator_refresh"
        try {
            Invoke-PhysicalMouseClickAtScreenPoint `
                $anchorX `
                $anchorY `
                "right" `
                "navigator_refresh_menu"
            [IntPtr]$popupHandle = Wait-UniqueOwnedPopupHandle `
                $ProcessId `
                "#32768" `
                "navigator_refresh_menu_unavailable"
            Start-Sleep -Milliseconds 150
            [void](Invoke-ExactPopupMenuItem `
                $popupHandle `
                $ProcessId `
                "Refresh" `
                "navigator_refresh")
        } finally {
            Restore-CursorSnapshot $cursorSnapshot "navigator_refresh"
        }
        $deadline = [DateTime]::UtcNow.AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 250
            $count = [MetafxVisibleMsaa]::CountExactName($treeHandle, $operationFolder)
            if ($count -gt 1) { Stop-Adapter "navigator_expert_registration_ambiguous" }
            if ($count -eq 1) { return }
        } while ([DateTime]::UtcNow -lt $deadline)
        Stop-Adapter "navigator_expert_not_registered"
    }
}

function Invoke-MetaEditorCompile(
    [System.Windows.Automation.AutomationElement]$EditorWindow,
    [string]$SourceName
) {
    $title = ([string]$EditorWindow.Current.Name).Trim()
    if ($title -ne ("MetaEditor - [{0}]" -f $SourceName)) { Stop-Adapter "metaeditor_source_window_mismatch" }
    $controls = @(Find-DescendantsById $EditorWindow "Item 32796")
    if ($controls.Count -eq 1) {
        try {
            $invoke = $controls[0].GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
            $invoke.Invoke()
            return
        } catch { Stop-Adapter "metaeditor_compile_invoke_failed" }
    }
    if ($controls.Count -gt 1) { Stop-Adapter "metaeditor_compile_control_ambiguous" }
    # Some MT4 builds expose only the native Compile menu command.  Resolve it
    # by its visible label from this exact MetaEditor menu and send the command
    # to this exact bound HWND; no global accelerator key is used.
    $handle = [IntPtr]$EditorWindow.Current.NativeWindowHandle
    $command = Find-MenuCommand ([MetafxVisibleNative]::GetMenu($handle)) "Compile"
    if ($null -eq $command) { Stop-Adapter "metaeditor_compile_control_unavailable" }
    [void](Invoke-TargetMessage $handle ([MetafxVisibleNative]::WM_COMMAND) $command 0)
}

function Get-MetaEditorCompileToolboxState(
    [System.Windows.Automation.AutomationElement]$EditorWindow,
    [int]$ProcessId
) {
    $lists = @($EditorWindow.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::AutomationIdProperty,
            "10065"
        ))
    ) | Where-Object {
        [int]$_.Current.ProcessId -eq $ProcessId -and
        [string]$_.Current.ClassName -eq "SysListView32" -and
        -not [bool]$_.Current.IsOffscreen -and
        [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
        (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq $ProcessId
    })
    if ($lists.Count -ne 1) { Stop-Adapter "metaeditor_compile_result_unreadable" }
    $list = $lists[0]
    [IntPtr]$handle = [IntPtr]$list.Current.NativeWindowHandle
    $style = [MetafxVisibleNative]::GetWindowLong($handle, [MetafxVisibleNative]::GWL_STYLE)
    if (($style -band [MetafxVisibleNative]::LVS_TYPEMASK) -ne [MetafxVisibleNative]::LVS_REPORT -or
        ($style -band [MetafxVisibleNative]::LVS_OWNERDATA) -eq 0) {
        Stop-Adapter "metaeditor_compile_result_unreadable"
    }

    [IntPtr]$headerHandle = Invoke-TargetMessage $handle ([MetafxVisibleNative]::LVM_GETHEADER) 0 0
    if ($headerHandle -eq [IntPtr]::Zero -or
        (Get-WindowOwner $headerHandle) -ne $ProcessId -or
        (Get-WindowClass $headerHandle) -ne "SysHeader32") {
        Stop-Adapter "metaeditor_compile_result_unreadable"
    }
    $headerItems = @($list.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::HeaderItem
        ))
    ) | Where-Object {
        [int]$_.Current.ProcessId -eq $ProcessId -and -not [bool]$_.Current.IsOffscreen
    })
    if ($headerItems.Count -ne 4) { Stop-Adapter "metaeditor_compile_result_unreadable" }
    $expectedHeaders = @("Description", "File", "Line", "Column")
    for ($index = 0; $index -lt $expectedHeaders.Count; $index++) {
        if (-not [string]::Equals(
            ([string]$headerItems[$index].Current.Name).Trim(),
            $expectedHeaders[$index],
            [System.StringComparison]::Ordinal
        )) { Stop-Adapter "metaeditor_compile_result_unreadable" }
    }

    $dataItems = @($list.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        (New-Object System.Windows.Automation.PropertyCondition(
            [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
            [System.Windows.Automation.ControlType]::DataItem
        ))
    ) | Where-Object {
        [int]$_.Current.ProcessId -eq $ProcessId -and -not [bool]$_.Current.IsOffscreen
    })
    $nativeRowCount = (Invoke-TargetMessage $handle ([MetafxVisibleNative]::LVM_GETITEMCOUNT) 0 0).ToInt32()
    if ($nativeRowCount -gt 2 -or $dataItems.Count -gt 2) {
        Stop-Adapter "metaeditor_compile_diagnostics_present"
    }
    if ($nativeRowCount -lt 2 -or $dataItems.Count -lt 2) {
        Stop-Adapter "metaeditor_compile_result_unreadable"
    }
    if ($nativeRowCount -ne $dataItems.Count) {
        Stop-Adapter "metaeditor_compile_result_unreadable"
    }
    return [pscustomobject]@{
        ListHandle = [int64]$handle
        HeaderHandle = [int64]$headerHandle
        NativeRowCount = $nativeRowCount
        DataItemCount = $dataItems.Count
        HeaderNames = @($headerItems | ForEach-Object { ([string]$_.Current.Name).Trim() })
    }
}

function Read-MetaEditorCompileResult(
    [System.Windows.Automation.AutomationElement]$EditorWindow,
    [int]$ProcessId,
    [string]$SourceName,
    [bool]$FreshBinaryObserved
) {
    [IntPtr]$editorHandle = [IntPtr]$EditorWindow.Current.NativeWindowHandle
    if ([int]$EditorWindow.Current.ProcessId -ne $ProcessId -or
        [string]$EditorWindow.Current.ClassName -ne "MetaQuotes::MetaEditor::5.00" -or
        $editorHandle -eq [IntPtr]::Zero -or
        (Get-WindowOwner $editorHandle) -ne $ProcessId) {
        Stop-Adapter "metaeditor_compile_window_identity_invalid"
    }
    if (([string]$EditorWindow.Current.Name).Trim() -ne ("MetaEditor - [{0}]" -f $SourceName)) {
        Stop-Adapter "metaeditor_compile_source_mismatch"
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    $previousToolboxFingerprint = $null
    do {
        $matches = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::OrdinalIgnoreCase
        )
        foreach ($element in @($EditorWindow.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition
        ))) {
            try {
                if ([int]$element.Current.ProcessId -ne $ProcessId) { continue }
                $name = ([string]$element.Current.Name).Trim()
                $match = [regex]::Match(
                    $name,
                    '(?:Result:\s*)?0\s+errors?,\s*0\s+warnings?',
                    [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
                )
                if ($match.Success) {
                    # Keep one canonical value for the Python verifier and the
                    # immutable compile receipt even when a MetaEditor build
                    # exposes the summary without the optional "Result:" prefix.
                    [void]$matches.Add("Result: 0 errors, 0 warnings")
                }
            } catch { }
        }
        if ($matches.Count -eq 1) { return @($matches)[0] }
        if ($matches.Count -gt 1) { Stop-Adapter "metaeditor_compile_result_ambiguous" }
        if ($FreshBinaryObserved) {
            $toolbox = $null
            try {
                $toolbox = Get-MetaEditorCompileToolboxState $EditorWindow $ProcessId
            } catch {
                $reason = [string]$_.Exception.Message
                if ($reason -match '^METAFX_VISIBLE:metaeditor_compile_diagnostics_present$') { throw }
                if ($reason -notmatch '^METAFX_VISIBLE:metaeditor_compile_result_unreadable$') { throw }
                $previousToolboxFingerprint = $null
            }
            if ($null -ne $toolbox) {
                $toolboxFingerprint = "{0}|{1}|{2}|{3}|{4}" -f `
                    $toolbox.ListHandle, `
                    $toolbox.HeaderHandle, `
                    $toolbox.NativeRowCount, `
                    $toolbox.DataItemCount, `
                    ($toolbox.HeaderNames -join "|")
                if ($previousToolboxFingerprint -eq $toolboxFingerprint) {
                    return "Result: 0 errors, 0 warnings"
                }
                $previousToolboxFingerprint = $toolboxFingerprint
            }
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "metaeditor_compile_result_unreadable"
}

function Get-UniqueOwnedDialog(
    [int]$ProcessId,
    [IntPtr]$ExcludedHandle,
    [string]$FailureCode
) {
    $handles = @([MetafxVisibleNative]::GetVisibleTopLevelWindows($ProcessId, "#32770") |
        Where-Object { [IntPtr]$_ -ne $ExcludedHandle })
    if ($handles.Count -ne 1) { Stop-Adapter $FailureCode }
    [IntPtr]$handle = [IntPtr]$handles[0]
    if ($handle -eq [IntPtr]::Zero -or (Get-WindowOwner $handle) -ne $ProcessId) {
        Stop-Adapter ("{0}_owner_mismatch" -f $FailureCode)
    }
    $dialog = [System.Windows.Automation.AutomationElement]::FromHandle($handle)
    if ($null -eq $dialog) { Stop-Adapter ("{0}_uia_unavailable" -f $FailureCode) }
    return $dialog
}

function Wait-UniqueOwnedDialog(
    [int]$ProcessId,
    [IntPtr]$ExcludedHandle,
    [string]$FailureCode
) {
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 100
        try {
            return Get-UniqueOwnedDialog $ProcessId $ExcludedHandle $FailureCode
        } catch {
            if ([string]$_.Exception.Message -notmatch '^METAFX_VISIBLE:') { throw }
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter $FailureCode
}

function Invoke-ExactButton(
    [System.Windows.Automation.AutomationElement]$Root,
    [int]$ProcessId,
    [string]$AutomationId,
    [string[]]$AllowedNames,
    [string]$FailureCode
) {
    $button = Get-UniqueControl $Root $AutomationId $ProcessId
    $name = ([string]$button.Current.Name).Trim()
    [IntPtr]$buttonHandle = [IntPtr]$button.Current.NativeWindowHandle
    if ([string]$button.Current.ClassName -ne "Button" -or
        $name -notin $AllowedNames -or
        $buttonHandle -eq [IntPtr]::Zero -or
        (Get-WindowOwner $buttonHandle) -ne $ProcessId -or
        -not [MetafxVisibleNative]::IsWindowVisible($buttonHandle) -or
        (([MetafxVisibleNative]::GetWindowLong(
            $buttonHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0) -or
        [bool]$button.Current.IsOffscreen) {
        Stop-Adapter ("{0}_semantic_mismatch" -f $FailureCode)
    }
    # Opening a modal dialog keeps the target thread inside DialogBox or the
    # common-file-dialog handler.  Queue the exact owned click and let each
    # caller prove its visible effect instead of timing out on a synchronous
    # SendMessage after the dialog has already opened.
    $posted = [MetafxVisibleNative]::PostMessage(
        $buttonHandle,
        [MetafxVisibleNative]::BM_CLICK,
        [IntPtr]::Zero,
        [IntPtr]::Zero
    )
    if (-not $posted) { Stop-Adapter ("{0}_post_failed" -f $FailureCode) }
}

function Select-ExpertInputsTab(
    [System.Windows.Automation.AutomationElement]$Dialog,
    [int]$ProcessId
) {
    $tab = Get-UniqueControl $Dialog "12320" $ProcessId
    [IntPtr]$tabHandle = [IntPtr]$tab.Current.NativeWindowHandle
    if ([string]$tab.Current.ClassName -ne "SysTabControl32" -or
        $tabHandle -eq [IntPtr]::Zero -or (Get-WindowOwner $tabHandle) -ne $ProcessId) {
        Stop-Adapter "expert_properties_tab_control_invalid"
    }
    $count = (Invoke-TargetMessage $tabHandle ([MetafxVisibleNative]::TCM_GETITEMCOUNT) 0 0).ToInt32()
    if ($count -lt 2 -or $count -gt 8) {
        Stop-Adapter "expert_properties_tabs_ambiguous"
    }
    $tabItems = @($tab.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition
    ) | Where-Object {
        $_.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and
        [int]$_.Current.ProcessId -eq $ProcessId -and
        -not [bool]$_.Current.IsOffscreen
    })
    $inputItems = @($tabItems | Where-Object {
        ([string]$_.Current.Name).Trim().Equals(
            "Inputs",
            [System.StringComparison]::OrdinalIgnoreCase
        )
    })
    if ($inputItems.Count -ne 1) {
        Stop-Adapter "expert_inputs_tab_ambiguous"
    }
    try {
        $inputSelection = $inputItems[0].GetCurrentPattern(
            [System.Windows.Automation.SelectionItemPattern]::Pattern
        )
        if (-not [bool]$inputSelection.Current.IsSelected) {
            $inputSelection.Select()
        }
    } catch {
        Stop-Adapter "expert_inputs_tab_selection_failed"
    }
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        Start-Sleep -Milliseconds 100
        $selected = (Invoke-TargetMessage $tabHandle ([MetafxVisibleNative]::TCM_GETCURSEL) 0 0).ToInt32()
        $selectedByName = $false
        try {
            $selectedByName = [bool]$inputSelection.Current.IsSelected
        } catch { }
        if ($selected -ge 0 -and $selected -lt $count -and $selectedByName) {
            $list = Get-UniqueControl $Dialog "1357" $ProcessId
            [IntPtr]$listHandle = [IntPtr]$list.Current.NativeWindowHandle
            if ([string]$list.Current.ClassName -ne "SysListView32" -or
                $listHandle -eq [IntPtr]::Zero -or
                (Get-WindowOwner $listHandle) -ne $ProcessId -or
                -not [MetafxVisibleNative]::IsWindowVisible($listHandle)) {
                Stop-Adapter "expert_inputs_list_invalid"
            }
            return
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "expert_inputs_tab_not_selected"
}

function Wait-VerifiedElementFromHandle(
    [IntPtr]$Handle,
    [int]$ProcessId,
    [string]$FailureCode
) {
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    do {
        if (-not [MetafxVisibleNative]::IsWindow($Handle)) { Stop-Adapter $FailureCode }
        if ((Get-WindowOwner $Handle) -ne $ProcessId) {
            Stop-Adapter ("{0}_owner_mismatch" -f $FailureCode)
        }
        try {
            $element = [System.Windows.Automation.AutomationElement]::FromHandle($Handle)
            if ($null -ne $element) { return $element }
        } catch {
            $hresult = [int]$_.Exception.GetBaseException().HResult
            if ($hresult -ne -2147417851) { throw }
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter $FailureCode
}

function Set-NativeEditTextExact(
    [System.Windows.Automation.AutomationElement]$Edit,
    [int]$ProcessId,
    [string]$Value,
    [string]$FailureCode
) {
    [IntPtr]$handle = [IntPtr]$Edit.Current.NativeWindowHandle
    if ([string]$Edit.Current.ClassName -ne "Edit" -or
        $handle -eq [IntPtr]::Zero -or (Get-WindowOwner $handle) -ne $ProcessId) {
        Stop-Adapter ("{0}_identity_invalid" -f $FailureCode)
    }
    [IntPtr]$result = [IntPtr]::Zero
    $call = [MetafxVisibleNative]::SendMessageTimeout(
        $handle,
        [MetafxVisibleNative]::WM_SETTEXT,
        [IntPtr]::Zero,
        $Value,
        [MetafxVisibleNative]::SMTO_ABORTIFHUNG,
        1500,
        [ref]$result
    )
    if ($call -eq [IntPtr]::Zero -or $result.ToInt32() -ne 1) {
        Stop-Adapter ("{0}_set_failed" -f $FailureCode)
    }
    $observed = Read-Win32Text $handle
    if (-not [string]::Equals($observed, $Value, [System.StringComparison]::OrdinalIgnoreCase)) {
        Stop-Adapter ("{0}_readback_mismatch" -f $FailureCode)
    }
}

function Test-NativeWindowDescendantOf(
    [IntPtr]$Handle,
    [IntPtr]$ExpectedAncestor
) {
    if ($Handle -eq [IntPtr]::Zero -or $ExpectedAncestor -eq [IntPtr]::Zero) {
        return $false
    }
    [IntPtr]$current = $Handle
    for ($depth = 0; $depth -lt 32; $depth++) {
        if ($current -eq $ExpectedAncestor) { return $true }
        $current = [MetafxVisibleNative]::GetParent($current)
        if ($current -eq [IntPtr]::Zero) { return $false }
    }
    return $false
}

function Test-FileNameLabel([string]$Value) {
    # Keep this distributed no-BOM script ASCII-only so Windows PowerShell 5.1
    # does not decode Thai UTF-8 bytes through the active ANSI code page.
    $thaiFileName = -join @(
        [char]0x0E0A, [char]0x0E37, [char]0x0E48, [char]0x0E2D,
        [char]0x0E44, [char]0x0E1F, [char]0x0E25, [char]0x0E4C,
        [char]0x003A
    )
    $thaiFile = -join @(
        [char]0x0E0A, [char]0x0E37, [char]0x0E48, [char]0x0E2D,
        [char]0x0E41, [char]0x0E1F, [char]0x0E49, [char]0x0E21,
        [char]0x003A
    )
    return $Value.Trim() -in @("File name:", $thaiFileName, $thaiFile)
}

function Get-FileDialogFileNameBinding(
    [System.Windows.Automation.AutomationElement]$Dialog,
    [int]$ProcessId,
    [string]$FailureCode
) {
    [IntPtr]$dialogHandle = [IntPtr]$Dialog.Current.NativeWindowHandle
    if ($dialogHandle -eq [IntPtr]::Zero -or
        [string]$Dialog.Current.ClassName -ne "#32770" -or
        [int]$Dialog.Current.ProcessId -ne $ProcessId -or
        (Get-WindowOwner $dialogHandle) -ne $ProcessId -or
        -not [MetafxVisibleNative]::IsWindowVisible($dialogHandle) -or
        [bool]$Dialog.Current.IsOffscreen) {
        Stop-Adapter ("{0}_dialog_identity_invalid" -f $FailureCode)
    }

    $eligibleByHandle = @{}
    $candidates = @(
        @(Find-DescendantsById $Dialog "1001") +
        @(Find-DescendantsById $Dialog "1152")
    )
    foreach ($candidate in $candidates) {
        [IntPtr]$candidateHandle = [IntPtr]$candidate.Current.NativeWindowHandle
        if ([string]$candidate.Current.ClassName -ne "Edit" -or
            [int]$candidate.Current.ProcessId -ne $ProcessId -or
            $candidateHandle -eq [IntPtr]::Zero -or
            (Get-WindowOwner $candidateHandle) -ne $ProcessId -or
            -not [MetafxVisibleNative]::IsWindowVisible($candidateHandle) -or
            -not [bool]$candidate.Current.IsEnabled -or
            [bool]$candidate.Current.IsOffscreen -or
            -not (Test-NativeWindowDescendantOf $candidateHandle $dialogHandle)) {
            continue
        }

        [int]$nativeId = [MetafxVisibleNative]::GetDlgCtrlID($candidateHandle)
        [IntPtr]$parentHandle = [MetafxVisibleNative]::GetParent($candidateHandle)
        $binding = $null

        # Windows 10/11 common dialogs expose the inner Edit (id 1001) through
        # a native ComboBox represented by UIA as the named FileNameControlHost.
        # The address/search control can also use id 1001, so require this whole
        # semantic binding rather than accepting an Edit merely by id.
        if ($nativeId -eq 1001 -and
            $parentHandle -ne [IntPtr]::Zero -and
            (Get-WindowClass $parentHandle) -in @("ComboBox", "ComboBoxEx32") -and
            (Test-NativeWindowDescendantOf $parentHandle $dialogHandle)) {
            $fileNameHost = [System.Windows.Automation.AutomationElement]::FromHandle(
                $parentHandle
            )
            if ($null -ne $fileNameHost -and
                [int]$fileNameHost.Current.ProcessId -eq $ProcessId -and
                [IntPtr]$fileNameHost.Current.NativeWindowHandle -eq $parentHandle -and
                [string]$fileNameHost.Current.AutomationId -in @("FileNameControlHost", "1148") -and
                [string]$fileNameHost.Current.ClassName -in @("AppControlHost", "ComboBox", "ComboBoxEx32") -and
                $fileNameHost.Current.ControlType -eq [System.Windows.Automation.ControlType]::ComboBox -and
                (Test-FileNameLabel ([string]$fileNameHost.Current.Name)) -and
                (Test-FileNameLabel ([string]$candidate.Current.Name)) -and
                [bool]$fileNameHost.Current.IsEnabled -and
                -not [bool]$fileNameHost.Current.IsOffscreen) {
                $binding = [pscustomobject]@{
                    Kind = "modern"
                    Dialog = $Dialog
                    DialogHandle = $dialogHandle
                    Edit = $candidate
                    EditHandle = $candidateHandle
                    FileNameHost = $fileNameHost
                    FileNameHostHandle = $parentHandle
                }
            }
        }

        # A classic common dialog uses a direct Edit id 1152 and a sibling
        # Static label id 1090.  Keep this shape separate and equally strict.
        if ($null -eq $binding -and
            $nativeId -eq 1152 -and
            $parentHandle -eq $dialogHandle) {
            $labels = @(
                Find-DescendantsById $Dialog "1090" | Where-Object {
                    [string]$_.Current.ClassName -eq "Static" -and
                    [int]$_.Current.ProcessId -eq $ProcessId -and
                    [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
                    [MetafxVisibleNative]::GetDlgCtrlID(
                        [IntPtr]$_.Current.NativeWindowHandle
                    ) -eq 1090 -and
                    [MetafxVisibleNative]::GetParent(
                        [IntPtr]$_.Current.NativeWindowHandle
                    ) -eq $dialogHandle -and
                    (Test-FileNameLabel ([string]$_.Current.Name)) -and
                    -not [bool]$_.Current.IsOffscreen
                }
            )
            if ($labels.Count -eq 1) {
                $binding = [pscustomobject]@{
                    Kind = "classic"
                    Dialog = $Dialog
                    DialogHandle = $dialogHandle
                    Edit = $candidate
                    EditHandle = $candidateHandle
                    FileNameHost = $null
                    FileNameHostHandle = [IntPtr]::Zero
                }
            } elseif ($labels.Count -gt 1) {
                Stop-Adapter ("{0}_label_ambiguous" -f $FailureCode)
            }
        }

        if ($null -ne $binding) {
            $key = $candidateHandle.ToInt64().ToString()
            $eligibleByHandle[$key] = $binding
        }
    }

    $eligible = @($eligibleByHandle.Values)
    if ($eligible.Count -gt 1) {
        Stop-Adapter ("{0}_control_ambiguous" -f $FailureCode)
    }
    if ($eligible.Count -eq 0) {
        Stop-Adapter ("{0}_control_unavailable" -f $FailureCode)
    }
    return $eligible[0]
}

function Read-AutomationValueExact(
    [System.Windows.Automation.AutomationElement]$Element,
    [string]$FailureCode
) {
    try {
        $pattern = $Element.GetCurrentPattern(
            [System.Windows.Automation.ValuePattern]::Pattern
        )
        return [string]$pattern.Current.Value
    } catch {
        Stop-Adapter ("{0}_value_unavailable" -f $FailureCode)
    }
}

function Set-FileDialogFileNameExact(
    [object]$Binding,
    [int]$ProcessId,
    [string]$Value,
    [string]$FailureCode
) {
    if (-not $Value -or $Value.Length -gt 2048 -or
        [System.IO.Path]::GetFullPath($Value) -ne $Value) {
        Stop-Adapter ("{0}_path_invalid" -f $FailureCode)
    }
    [IntPtr]$dialogHandle = [IntPtr]$Binding.DialogHandle
    [IntPtr]$editHandle = [IntPtr]$Binding.EditHandle
    if ($dialogHandle -eq [IntPtr]::Zero -or
        $editHandle -eq [IntPtr]::Zero -or
        -not [MetafxVisibleNative]::IsWindow($dialogHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($dialogHandle) -or
        (Get-WindowOwner $dialogHandle) -ne $ProcessId -or
        (Get-WindowClass $dialogHandle) -ne "#32770" -or
        -not [MetafxVisibleNative]::IsWindow($editHandle) -or
        -not [MetafxVisibleNative]::IsWindowVisible($editHandle) -or
        (Get-WindowOwner $editHandle) -ne $ProcessId -or
        (Get-WindowClass $editHandle) -ne "Edit" -or
        -not (Test-NativeWindowDescendantOf $editHandle $dialogHandle)) {
        Stop-Adapter ("{0}_binding_changed" -f $FailureCode)
    }

    Restore-Foreground $Binding.Dialog
    $editRect = New-Object MetafxVisibleNative+RECT
    $dialogRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($editHandle, [ref]$editRect) -or
        -not [MetafxVisibleNative]::GetWindowRect($dialogHandle, [ref]$dialogRect) -or
        $editRect.Right -le $editRect.Left -or
        $editRect.Bottom -le $editRect.Top -or
        $editRect.Left -lt $dialogRect.Left -or
        $editRect.Top -lt $dialogRect.Top -or
        $editRect.Right -gt $dialogRect.Right -or
        $editRect.Bottom -gt $dialogRect.Bottom) {
        Stop-Adapter ("{0}_bounds_invalid" -f $FailureCode)
    }

    $cursorSnapshot = Get-CursorSnapshot $FailureCode
    try {
        Invoke-PhysicalMouseClickAtScreenPoint `
            ([int](($editRect.Left + $editRect.Right) / 2)) `
            ([int](($editRect.Top + $editRect.Bottom) / 2)) `
            "left" `
            $FailureCode
        Start-Sleep -Milliseconds 100
        $focused = [System.Windows.Automation.AutomationElement]::FocusedElement
        if ($null -eq $focused -or
            [IntPtr]$focused.Current.NativeWindowHandle -ne $editHandle -or
            [int]$focused.Current.ProcessId -ne $ProcessId -or
            -not (Test-ForegroundWindowBinding $Binding.Dialog $ProcessId)) {
            Stop-Adapter ("{0}_focus_invalid" -f $FailureCode)
        }
        # ValuePattern/WM_SETTEXT can update only the visible child Edit while
        # the shell dialog keeps its internal file-name model at StrategyTester.
        # Replace the text through the real foreground keyboard path, then move
        # focus with Tab so the common dialog commits the edit before BM_CLICK.
        if (-not [MetafxVisibleNative]::ReplaceFocusedText($Value)) {
            Stop-Adapter ("{0}_keyboard_input_failed" -f $FailureCode)
        }
        Start-Sleep -Milliseconds 300
        if (-not (Test-ForegroundWindowBinding $Binding.Dialog $ProcessId) -or
            -not [MetafxVisibleNative]::IsWindow($dialogHandle) -or
            -not [MetafxVisibleNative]::IsWindowVisible($dialogHandle)) {
            Stop-Adapter ("{0}_keyboard_binding_changed" -f $FailureCode)
        }
        if (-not [MetafxVisibleNative]::SendVirtualKeyPress(
            [MetafxVisibleNative]::VK_TAB
        )) {
            Stop-Adapter ("{0}_commit_key_failed" -f $FailureCode)
        }
        Start-Sleep -Milliseconds 300
        if (-not (Test-ForegroundWindowBinding $Binding.Dialog $ProcessId) -or
            -not [MetafxVisibleNative]::IsWindowVisible($dialogHandle)) {
            Stop-Adapter ("{0}_commit_binding_changed" -f $FailureCode)
        }
    } finally {
        Restore-CursorSnapshot $cursorSnapshot $FailureCode
    }

    $editNativeValue = Read-Win32Text $editHandle
    $editAutomationValue = Read-AutomationValueExact $Binding.Edit $FailureCode
    if (-not [string]::Equals(
            $editNativeValue,
            $Value,
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or
        -not [string]::Equals(
            $editAutomationValue,
            $Value,
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        Stop-Adapter ("{0}_edit_readback_mismatch" -f $FailureCode)
    }
    if ([string]$Binding.Kind -eq "modern") {
        [IntPtr]$fileNameHostHandle = [IntPtr]$Binding.FileNameHostHandle
        if ($fileNameHostHandle -eq [IntPtr]::Zero -or
            [MetafxVisibleNative]::GetParent($editHandle) -ne $fileNameHostHandle -or
            (Get-WindowClass $fileNameHostHandle) -notin @("ComboBox", "ComboBoxEx32") -or
            -not (Test-NativeWindowDescendantOf $fileNameHostHandle $dialogHandle)) {
            Stop-Adapter ("{0}_host_binding_changed" -f $FailureCode)
        }
        $hostNativeValue = Read-Win32Text $fileNameHostHandle
        $hostAutomationValue = Read-AutomationValueExact `
            $Binding.FileNameHost `
            $FailureCode
        if (-not [string]::Equals(
                $hostNativeValue,
                $Value,
                [System.StringComparison]::OrdinalIgnoreCase
            ) -or
            -not [string]::Equals(
                $hostAutomationValue,
                $Value,
                [System.StringComparison]::OrdinalIgnoreCase
            )) {
            Stop-Adapter ("{0}_host_readback_mismatch" -f $FailureCode)
        }
    }
}

function Close-ExactOwnedFileDialogAfterFailure(
    [System.Windows.Automation.AutomationElement]$Dialog,
    [IntPtr]$ExpectedDialogHandle,
    [int]$ProcessId
) {
    try {
        if ($ExpectedDialogHandle -eq [IntPtr]::Zero -or
            -not [MetafxVisibleNative]::IsWindow($ExpectedDialogHandle) -or
            -not [MetafxVisibleNative]::IsWindowVisible($ExpectedDialogHandle)) {
            return $true
        }
        if ($null -eq $Dialog -or
            [IntPtr]$Dialog.Current.NativeWindowHandle -ne $ExpectedDialogHandle -or
            [int]$Dialog.Current.ProcessId -ne $ProcessId -or
            [string]$Dialog.Current.ClassName -ne "#32770" -or
            (Get-WindowOwner $ExpectedDialogHandle) -ne $ProcessId -or
            (Get-WindowClass $ExpectedDialogHandle) -ne "#32770") {
            return $false
        }
        $cancelButtons = @(
            Find-DescendantsById $Dialog "2" | Where-Object {
                [string]$_.Current.ClassName -eq "Button" -and
                [int]$_.Current.ProcessId -eq $ProcessId -and
                [IntPtr]$_.Current.NativeWindowHandle -ne [IntPtr]::Zero -and
                [MetafxVisibleNative]::GetDlgCtrlID(
                    [IntPtr]$_.Current.NativeWindowHandle
                ) -eq 2 -and
                (Get-WindowOwner ([IntPtr]$_.Current.NativeWindowHandle)) -eq
                    $ProcessId -and
                [MetafxVisibleNative]::IsWindowVisible(
                    [IntPtr]$_.Current.NativeWindowHandle
                ) -and
                [bool]$_.Current.IsEnabled -and
                -not [bool]$_.Current.IsOffscreen
            }
        )
        if ($cancelButtons.Count -ne 1) { return $false }
        $thaiCancel = -join @(
            [char]0x0E22, [char]0x0E01, [char]0x0E40,
            [char]0x0E25, [char]0x0E34, [char]0x0E01
        )
        $cancelName = ([string]$cancelButtons[0].Current.Name).Trim()
        if ($cancelName -notin @("Cancel", $thaiCancel)) { return $false }
        [IntPtr]$cancelHandle = [IntPtr]$cancelButtons[0].Current.NativeWindowHandle
        if (-not [MetafxVisibleNative]::PostMessage(
            $cancelHandle,
            [MetafxVisibleNative]::BM_CLICK,
            [IntPtr]::Zero,
            [IntPtr]::Zero
        )) { return $false }
        $deadline = [DateTime]::UtcNow.AddSeconds(3)
        do {
            Start-Sleep -Milliseconds 50
            if (-not [MetafxVisibleNative]::IsWindow($ExpectedDialogHandle) -or
                -not [MetafxVisibleNative]::IsWindowVisible($ExpectedDialogHandle)) {
                return $true
            }
            if ((Get-WindowOwner $ExpectedDialogHandle) -ne $ProcessId -or
                (Get-WindowClass $ExpectedDialogHandle) -ne "#32770") {
                return $false
            }
        } while ([DateTime]::UtcNow -lt $deadline)
    } catch { }
    return $false
}

function Invoke-FileDialogPath(
    [int]$ProcessId,
    [IntPtr]$PropertiesHandle,
    [string]$Path,
    [string[]]$AllowedActionNames,
    [bool]$RequireExistingInput
) {
    if ($RequireExistingInput -and -not [System.IO.File]::Exists($Path)) {
        Stop-Adapter "tester_input_preset_set_missing"
    }
    if (-not $RequireExistingInput -and [System.IO.File]::Exists($Path)) {
        Stop-Adapter "tester_input_readback_set_exists"
    }
    $dialog = Wait-UniqueOwnedDialog $ProcessId $PropertiesHandle "tester_input_file_dialog_missing"
    [IntPtr]$dialogHandle = [IntPtr]$dialog.Current.NativeWindowHandle
    try {
        $fileNameBinding = Get-FileDialogFileNameBinding `
            $dialog `
            $ProcessId `
            "tester_input_file_name"
        Set-FileDialogFileNameExact `
            $fileNameBinding `
            $ProcessId `
            $Path `
            "tester_input_file_name"
        Invoke-ExactButton $dialog $ProcessId "1" $AllowedActionNames "tester_input_file_action"
        $deadline = [DateTime]::UtcNow.AddSeconds(15)
        do {
            Start-Sleep -Milliseconds 100
            if (-not [MetafxVisibleNative]::IsWindow($dialogHandle)) {
                if ($RequireExistingInput -or
                    ([System.IO.File]::Exists($Path) -and (Get-Item -LiteralPath $Path).Length -gt 0)) {
                    return
                }
            } elseif ((Get-WindowOwner $dialogHandle) -ne $ProcessId) {
                Stop-Adapter "tester_input_file_dialog_owner_changed"
            }
        } while ([DateTime]::UtcNow -lt $deadline)
        Stop-Adapter "tester_input_file_action_incomplete"
    } catch {
        [void](Close-ExactOwnedFileDialogAfterFailure `
            $dialog `
            $dialogHandle `
            $ProcessId)
        # Bare rethrow preserves the original METAFX_VISIBLE reason code.
        # Throwing the ErrorRecord object itself can stringify it and collapse
        # the public result to visible_ui_action_failed.
        throw
    }
}

function Test-TesterInputReadbackSet([string]$Path, [object]$Preset) {
    if (-not [System.IO.File]::Exists($Path)) { return $false }
    $assumptions = @($Preset.assumptions)
    if ($assumptions.Count -lt 1 -or $assumptions.Count -gt 64) { return $false }
    $expectedByName = @{}
    foreach ($assumption in $assumptions) {
        $name = [string]$assumption.inputName
        $kind = [string]$assumption.inputType
        if ($name -notmatch '^[A-Za-z_][A-Za-z0-9_]*$' -or
            $kind -notin @("bool", "int", "double") -or
            -not [string]$assumption.reasonCode -or
            $expectedByName.ContainsKey($name)) { return $false }
        $expectedByName[$name] = $assumption
    }
    try {
        $item = Get-Item -LiteralPath $Path
        if ($item.Length -le 0 -or $item.Length -gt 1048576) { return $false }
        $reader = New-Object System.IO.StreamReader($Path, $true)
        try { $text = $reader.ReadToEnd() } finally { $reader.Dispose() }
    } catch { return $false }
    $observed = @{}
    $optimizationMetadataSeen = @{}
    foreach ($rawLine in @($text -split "`r?`n")) {
        $line = ([string]$rawLine).Trim()
        if (-not $line -or $line.StartsWith(";") -or $line.StartsWith("#") -or
            -not $line.Contains("=")) { continue }
        $parts = $line.Split(@("="), 2, [System.StringSplitOptions]::None)
        $name = ([string]$parts[0]).Trim().TrimStart([char]0xFEFF)
        if (-not $expectedByName.ContainsKey($name)) {
            if ($name -match '^(.+),(F|1|2|3)$' -and
                $expectedByName.ContainsKey([string]$Matches[1]) -and
                -not $optimizationMetadataSeen.ContainsKey($name)) {
                $optimizationMetadataSeen[$name] = $true
                continue
            }
            return $false
        }
        if ($observed.ContainsKey($name)) { return $false }
        $token = (([string]$parts[1]).Split(@("||"), 2, [System.StringSplitOptions]::None)[0]).Trim().ToLowerInvariant()
        $observed[$name] = $token
    }
    if ($observed.Count -ne $assumptions.Count) { return $false }
    foreach ($assumption in $assumptions) {
        $name = [string]$assumption.inputName
        if (-not $observed.ContainsKey($name)) { return $false }
        $token = [string]$observed[$name]
        switch ([string]$assumption.inputType) {
            "bool" {
                if ($token -in @("true", "1")) { $value = $true }
                elseif ($token -in @("false", "0")) { $value = $false }
                else { return $false }
                if ($value -ne [bool]$assumption.testerValue) { return $false }
            }
            "int" {
                [long]$value = 0
                if (-not [long]::TryParse(
                    $token,
                    [System.Globalization.NumberStyles]::Integer,
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [ref]$value
                )) { return $false }
                if ($value -ne [long]$assumption.testerValue) { return $false }
            }
            "double" {
                [double]$value = 0
                if (-not [double]::TryParse(
                    $token,
                    [System.Globalization.NumberStyles]::Float,
                    [System.Globalization.CultureInfo]::InvariantCulture,
                    [ref]$value
                ) -or [double]::IsNaN($value) -or [double]::IsInfinity($value)) {
                    return $false
                }
                [double]$expected = [double]$assumption.testerValue
                $tolerance = 0.000000000001 * [Math]::Max(1.0, [Math]::Abs($expected))
                if ([Math]::Abs($value - $expected) -gt $tolerance) { return $false }
            }
            default { return $false }
        }
    }
    return $true
}

function Apply-TesterInputPreset(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [System.Windows.Automation.AutomationElement]$TesterPane,
    [int]$ProcessId,
    [object]$Preset,
    [string]$PresetSetPath,
    [string]$ReadbackSetPath,
    [string]$ScreenshotPath
) {
    Invoke-ExactButton $TesterPane $ProcessId "1025" @("Expert properties") "expert_properties"
    $properties = Wait-UniqueOwnedDialog $ProcessId ([IntPtr]::Zero) "expert_properties_dialog_missing"
    [IntPtr]$propertiesHandle = [IntPtr]$properties.Current.NativeWindowHandle
    Restore-Foreground $properties
    Select-ExpertInputsTab $properties $ProcessId
    Invoke-ExactButton $properties $ProcessId "4011" @("Load") "expert_inputs_load"
    Invoke-FileDialogPath $ProcessId $propertiesHandle $PresetSetPath @("Open") $true
    $properties = Wait-VerifiedElementFromHandle $propertiesHandle $ProcessId "expert_properties_dialog_lost_after_load"
    Select-ExpertInputsTab $properties $ProcessId
    Invoke-ExactButton $properties $ProcessId "4012" @("Save") "expert_inputs_save"
    Invoke-FileDialogPath $ProcessId $propertiesHandle $ReadbackSetPath @("Save") $false
    if (-not (Test-TesterInputReadbackSet $ReadbackSetPath $Preset)) {
        Stop-Adapter "tester_input_readback_value_mismatch"
    }
    $properties = Wait-VerifiedElementFromHandle $propertiesHandle $ProcessId "expert_properties_dialog_lost_after_save"
    Select-ExpertInputsTab $properties $ProcessId
    Save-WindowPng $properties $ScreenshotPath
    # The values are scoped to Strategy Tester and never applied to a live
    # chart. MT4 may retain Tester Inputs after this run, so do not describe
    # this as an ephemeral "this run only" mutation.
    Invoke-ExactButton $properties $ProcessId "1" @("OK") "expert_properties_ok"
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        Start-Sleep -Milliseconds 100
        if (-not [MetafxVisibleNative]::IsWindow($propertiesHandle)) {
            return [ordered]@{
                testerInputPresetApplied = $true
                testerInputPresetReadbackVerified = $true
                inputPresetReadbackSaved = $true
            }
        } elseif ((Get-WindowOwner $propertiesHandle) -ne $ProcessId) {
            Stop-Adapter "expert_properties_dialog_owner_changed"
        }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "expert_properties_dialog_not_closed"
}

function Invoke-StartButton([System.Windows.Automation.AutomationElement]$TesterPane, [int]$ProcessId) {
    $button = Get-TesterStartButton $TesterPane $ProcessId
    if (([string]$button.Current.Name).Trim() -ne "Start") { Stop-Adapter "tester_start_not_ready" }
    [IntPtr]$buttonHandle = [IntPtr]$button.Current.NativeWindowHandle
    if ($buttonHandle -eq [IntPtr]::Zero -or
        (Get-WindowOwner $buttonHandle) -ne $ProcessId -or
        -not [MetafxVisibleNative]::IsWindowVisible($buttonHandle) -or
        (([MetafxVisibleNative]::GetWindowLong(
            $buttonHandle,
            [MetafxVisibleNative]::GWL_STYLE
        ) -band [MetafxVisibleNative]::WS_DISABLED) -ne 0) -or
        [bool]$button.Current.IsOffscreen) {
        Stop-Adapter "tester_start_control_invalid"
    }
    # The durable boundary is committed by the caller before this once-only
    # post.  Never synchronously wait inside BM_CLICK: MT4 may already be
    # running even if its handler takes longer than the message timeout.
    $posted = [MetafxVisibleNative]::PostMessage(
        $buttonHandle,
        [MetafxVisibleNative]::BM_CLICK,
        [IntPtr]::Zero,
        [IntPtr]::Zero
    )
    if (-not $posted) { Stop-Adapter "tester_start_post_failed" }
    $deadline = [DateTime]::UtcNow.AddSeconds(2)
    do {
        Start-Sleep -Milliseconds 10
        $observed = Get-TesterStartButton $TesterPane $ProcessId
        $name = ([string]$observed.Current.Name).Trim()
        if ($name -eq "Stop") { return $true }
        if ($name -ne "Start") { Stop-Adapter "tester_start_state_ambiguous" }
    } while ([DateTime]::UtcNow -lt $deadline)
    # A tiny test may already have completed; Wait-TesterComplete requires a
    # fresh tester-log advance plus fresh report evidence for that race.
    return $false
}

function Get-TesterLogSnapshot([string]$DataPath) {
    $snapshot = @{}
    $root = Join-Path $DataPath "tester\logs"
    if (-not [System.IO.Directory]::Exists($root)) { return $snapshot }
    foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Filter "*.log" -ErrorAction SilentlyContinue)) {
        $key = $file.FullName.ToLowerInvariant()
        $snapshot[$key] = ("{0}:{1}" -f $file.Length, $file.LastWriteTimeUtc.Ticks)
    }
    return $snapshot
}

function Test-TesterLogAdvanced(
    [string]$DataPath,
    [hashtable]$Before,
    [DateTime]$StartInvokedAt
) {
    $root = Join-Path $DataPath "tester\logs"
    if (-not [System.IO.Directory]::Exists($root)) { return $false }
    foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Filter "*.log" -ErrorAction SilentlyContinue)) {
        $key = $file.FullName.ToLowerInvariant()
        $signature = ("{0}:{1}" -f $file.Length, $file.LastWriteTimeUtc.Ticks)
        if ($file.LastWriteTimeUtc -ge $StartInvokedAt.AddSeconds(-1) -and
            (-not $Before.ContainsKey($key) -or [string]$Before[$key] -ne $signature)) {
            return $true
        }
    }
    return $false
}

function Wait-TesterComplete(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId,
    [int]$TimeoutSeconds,
    [string]$DataPath,
    [hashtable]$TesterLogBefore,
    [DateTime]$StartInvokedAt,
    [bool]$StopAlreadyObserved
) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    $sawStop = $StopAlreadyObserved
    $fastIdleStartedAt = $null
    $fastIdleObservations = 0
    do {
        Start-Sleep -Milliseconds 25
        $tester = Get-TesterPane $TerminalWindow $ProcessId
        $button = Get-TesterStartButton $tester $ProcessId
        $name = ([string]$button.Current.Name).Trim()
        if ($name -eq "Stop") {
            $sawStop = $true
            $fastIdleStartedAt = $null
            $fastIdleObservations = 0
            continue
        }
        if ($name -eq "Start" -and $sawStop) { return "stop_transition_observed" }
        if ($name -eq "Start") {
            # A very small test can finish its Start -> Stop -> Start cycle
            # before the first observation after the queued BM_CLICK.
            # Repeated stable-idle reads only identify that race; they are not
            # success evidence.  The caller must still create a fresh result
            # screenshot and Tester report, and Python must verify that report
            # plus the exact pre/post process binding before committing success.
            # A write advance in this selected terminal's tester log is also
            # mandatory so an idle button plus stale on-screen results cannot
            # masquerade as a completed run.
            if ($null -eq $fastIdleStartedAt) { $fastIdleStartedAt = [DateTime]::UtcNow }
            $fastIdleObservations++
            if ($fastIdleObservations -ge 12 -and
                ([DateTime]::UtcNow - $fastIdleStartedAt).TotalMilliseconds -ge 250 -and
                (Test-TesterLogAdvanced $DataPath $TesterLogBefore $StartInvokedAt)) {
                return "fast_idle_evidence_required"
            }
        }
        if ($name -notin @("Start", "Stop")) { Stop-Adapter "tester_start_state_ambiguous" }
    } while ([DateTime]::UtcNow -lt $deadline)
    Stop-Adapter "strategy_tester_timeout"
}

function Save-TesterReport(
    [System.Windows.Automation.AutomationElement]$TerminalWindow,
    [int]$ProcessId,
    [string]$ReportPath,
    [string]$ReportScreenshotPath,
    [bool]$AllowExistingReportScreenshot
) {
    if ([System.IO.File]::Exists($ReportPath)) { Stop-Adapter "tester_report_path_exists" }
    if ([System.IO.File]::Exists($ReportScreenshotPath)) {
        if (-not $AllowExistingReportScreenshot) {
            Stop-Adapter "tester_report_screenshot_path_exists"
        }
        Assert-ExistingPngEvidence $ReportScreenshotPath "tester_report_screenshot_invalid"
    }
    [void](Select-TesterReportTab $TerminalWindow $ProcessId)
    $deadline = [DateTime]::UtcNow.AddSeconds(5)
    $lists = @()
    do {
        Start-Sleep -Milliseconds 100
        $tester = Get-TesterPane $TerminalWindow $ProcessId
        $lists = @(Get-VisibleTesterReportLists $tester $ProcessId)
        if ($lists.Count -eq 1) { break }
        if ($lists.Count -gt 1) { Stop-Adapter "tester_report_list_ambiguous" }
    } while ([DateTime]::UtcNow -lt $deadline)
    if ($lists.Count -ne 1) { Stop-Adapter "tester_report_list_ambiguous" }
    [IntPtr]$testerHandle = [IntPtr]$tester.Current.NativeWindowHandle
    $listHandle = [IntPtr]$lists[0].Current.NativeWindowHandle
    if ($testerHandle -eq [IntPtr]::Zero -or
        (Get-WindowOwner $listHandle) -ne $ProcessId -or
        [MetafxVisibleNative]::GetParent($listHandle) -ne $testerHandle) {
        Stop-Adapter "tester_report_list_owner_mismatch"
    }
    Restore-Foreground $TerminalWindow
    if (-not [System.IO.File]::Exists($ReportScreenshotPath)) {
        # Keep the earlier post-completion screenshot immutable.  This second
        # image is captured only after the exact native Report list is visible,
        # before opening a context menu that could obscure the evidence.
        Save-WindowPng $TerminalWindow $ReportScreenshotPath
    }
    [int]$anchorX = 0
    [int]$anchorY = 0
    # ROLE_SYSTEM_LISTITEM (0x22) excludes the column header and blank list
    # background.  The context menu is therefore opened on a real, visible
    # tester Report row instead of whichever control happens to own the cursor.
    if (-not [MetafxVisibleMsaa]::TrySelectFirstFullyVisibleRoleCenter(
        $listHandle,
        0x22,
        [ref]$anchorX,
        [ref]$anchorY
    )) {
        Stop-Adapter "tester_report_row_unavailable"
    }
    $listRect = New-Object MetafxVisibleNative+RECT
    if (-not [MetafxVisibleNative]::GetWindowRect($listHandle, [ref]$listRect) -or
        $anchorX -lt $listRect.Left -or $anchorX -ge $listRect.Right -or
        $anchorY -lt $listRect.Top -or $anchorY -ge $listRect.Bottom) {
        Stop-Adapter "tester_report_row_anchor_invalid"
    }
    try { $lists[0].SetFocus() } catch { }
    [void][MetafxVisibleNative]::SetFocus($listHandle)
    $cursorSnapshot = Get-CursorSnapshot "tester_save_report"
    try {
        # Reacquire immediately before SendInput.  A same-process HWND can be
        # destroyed/reused after the first lookup, so owner/id alone are not an
        # exact binding.  Require the one currently visible Report list to be
        # the same native child and require the current anchor to remain inside
        # its current bounds.
        $currentTester = Get-TesterPane $TerminalWindow $ProcessId
        [IntPtr]$currentTesterHandle = [IntPtr]$currentTester.Current.NativeWindowHandle
        $currentLists = @(Get-VisibleTesterReportLists $currentTester $ProcessId)
        if ($currentLists.Count -ne 1) {
            Stop-Adapter "tester_save_report_binding_changed"
        }
        [IntPtr]$currentListHandle = [IntPtr]$currentLists[0].Current.NativeWindowHandle
        $currentListRect = New-Object MetafxVisibleNative+RECT
        [int]$currentListStyle = [MetafxVisibleNative]::GetWindowLong(
            $currentListHandle,
            [MetafxVisibleNative]::GWL_STYLE
        )
        if (-not (Test-ForegroundWindowBinding $TerminalWindow $ProcessId) -or
            $currentTesterHandle -ne $testerHandle -or
            $currentListHandle -ne $listHandle -or
            -not [MetafxVisibleNative]::IsWindow($listHandle) -or
            (Get-WindowOwner $listHandle) -ne $ProcessId -or
            (Get-WindowClass $listHandle) -ne "SysListView32" -or
            [MetafxVisibleNative]::GetParent($listHandle) -ne $currentTesterHandle -or
            [MetafxVisibleNative]::GetDlgCtrlID($listHandle) -ne 33213 -or
            -not [MetafxVisibleNative]::IsWindowVisible($listHandle) -or
            ($currentListStyle -band [MetafxVisibleNative]::WS_DISABLED) -ne 0 -or
            [bool]$currentLists[0].Current.IsOffscreen -or
            ($currentListStyle -band [MetafxVisibleNative]::LVS_TYPEMASK) -ne
                [MetafxVisibleNative]::LVS_REPORT -or
            -not [MetafxVisibleNative]::GetWindowRect($listHandle, [ref]$currentListRect) -or
            $currentListRect.Right -le $currentListRect.Left -or
            $currentListRect.Bottom -le $currentListRect.Top -or
            $anchorX -lt $currentListRect.Left -or $anchorX -ge $currentListRect.Right -or
            $anchorY -lt $currentListRect.Top -or $anchorY -ge $currentListRect.Bottom) {
            Stop-Adapter "tester_save_report_binding_changed"
        }
        Invoke-PhysicalMouseClickAtScreenPoint `
            $anchorX `
            $anchorY `
            "right" `
            "tester_save_report_menu"
        [IntPtr]$popupHandle = Wait-UniqueOwnedPopupHandle `
            $ProcessId `
            "#32768" `
            "tester_save_report_menu_unavailable"
        Start-Sleep -Milliseconds 150
        [void](Invoke-ExactPopupMenuItem `
            $popupHandle `
            $ProcessId `
            "Save as Report" `
            "tester_save_report")
    } finally {
        Restore-CursorSnapshot $cursorSnapshot "tester_save_report"
    }
    $dialog = Wait-UniqueOwnedDialog $ProcessId ([IntPtr]::Zero) "tester_save_dialog_missing"
    [IntPtr]$dialogHandle = [IntPtr]$dialog.Current.NativeWindowHandle
    try {
        $fileNameBinding = Get-FileDialogFileNameBinding `
            $dialog `
            $ProcessId `
            "tester_save_filename"
        Set-FileDialogFileNameExact `
            $fileNameBinding `
            $ProcessId `
            $ReportPath `
            "tester_save_filename"
        $thaiSave = -join @(
            [char]0x0E1A, [char]0x0E31, [char]0x0E19,
            [char]0x0E17, [char]0x0E36, [char]0x0E01
        )
        Invoke-ExactButton $dialog $ProcessId "1" @("Save", $thaiSave) "tester_save"
        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        do {
            Start-Sleep -Milliseconds 200
            if ((-not [MetafxVisibleNative]::IsWindow($dialogHandle) -or
                -not [MetafxVisibleNative]::IsWindowVisible($dialogHandle)) -and
                [System.IO.File]::Exists($ReportPath) -and
                (Get-Item -LiteralPath $ReportPath).Length -gt 256) { return }
        } while ([DateTime]::UtcNow -lt $deadline)
        Stop-Adapter "tester_report_path_not_committed"
    } catch {
        [void](Close-ExactOwnedFileDialogAfterFailure `
            $dialog `
            $dialogHandle `
            $ProcessId)
        # Preserve the exact safe reason code from the failed binding/commit.
        throw
    }
}

$request = $null
$checkpoint = "request"
try {
    if (-not [System.IO.File]::Exists($RequestPath)) { Stop-Adapter "request_file_missing" }
    if ([System.IO.File]::Exists($ResponsePath)) { Stop-Adapter "response_path_exists" }
    $request = Get-Content -Raw -Encoding UTF8 -LiteralPath $RequestPath | ConvertFrom-Json
    if ($request.schemaVersion -ne "ea-factory-visible-powershell-request-v1") { Stop-Adapter "request_schema_invalid" }
    if ($request.platform -ne "mt4") { Stop-Adapter "mt5_visible_adapter_not_verified" }
    if ([string]$request.operationId -notmatch '^ea-visible-[a-f0-9]{24}$') { Stop-Adapter "operation_id_invalid" }
    $terminalPath = Get-FullPath $request.terminalPath
    $compilerPath = Get-FullPath $request.compilerPath
    $dataPath = Get-FullPath $request.dataPath
    if (-not [System.IO.File]::Exists($terminalPath) -or -not [System.IO.File]::Exists($compilerPath)) {
        Stop-Adapter "selected_executable_missing"
    }
    if ([System.IO.Path]::GetFileName($terminalPath) -ine "terminal.exe" -or
        [System.IO.Path]::GetFileName($compilerPath) -ine "metaeditor.exe") {
        Stop-Adapter "selected_executable_name_invalid"
    }

    if ($request.action -eq "probe") {
        $terminal = Get-ExistingVisibleProcess $terminalPath "terminal"
        $handle = [IntPtr]$terminal.Window.Current.NativeWindowHandle
        $result = [ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = "probe"
            operationId = [string]$request.operationId
            terminalProbe = [ordered]@{
                observedAt = [DateTime]::UtcNow.ToString("o")
                processId = [int]$terminal.Process.Id
                executablePath = [string]$terminal.Process.MainModule.FileName
                windowHandle = [int64]$handle
                windowOwnerProcessId = Get-WindowOwner $handle
                windowTitle = [string]$terminal.Window.Current.Name
                windowClass = [string]$terminal.Window.Current.ClassName
            }
        }
        Write-JsonResult $result 0
    }

    # A selected terminal must already be visibly running.  Starting it from
    # the adapter could restore live charts/EAs before the adapter can prove
    # the selected data folder, so fail closed instead of launching it.
    $terminal = Get-ExistingVisibleProcess $terminalPath "terminal"
    if ([int]$request.expectedTerminalProcessId -ne [int]$terminal.Process.Id -or
        [int64]$request.expectedTerminalWindowHandle -ne [int64]$terminal.Window.Current.NativeWindowHandle) {
        Stop-Adapter "terminal_process_changed_after_capability_probe"
    }
    Restore-Foreground $terminal.Window
    Assert-NoModal ([int]$terminal.Process.Id) ([IntPtr]$terminal.Window.Current.NativeWindowHandle)
    $autoBefore = Get-AutoTradingState $terminal.Window ([int]$terminal.Process.Id)

    if ($request.action -eq "recover_compile") {
        $sourcePath = Get-FullPath $request.sourcePath
        $binaryPath = Get-FullPath $request.binaryPath
        if (-not [System.IO.File]::Exists($sourcePath) -or [System.IO.Path]::GetExtension($sourcePath) -ine ".mq4") {
            Stop-Adapter "source_file_invalid"
        }
        if (-not (Test-SamePath $binaryPath ([System.IO.Path]::ChangeExtension($sourcePath, ".ex4"))) -or
            -not [System.IO.File]::Exists($binaryPath) -or
            (Get-Item -LiteralPath $binaryPath).Length -le 0) {
            Stop-Adapter "metaeditor_recovery_binary_invalid"
        }
        $expectedBinaryDigest = ([string]$request.expectedBinaryDigest).Trim().ToLowerInvariant()
        if ($expectedBinaryDigest -notmatch '^[0-9a-f]{64}$' -or
            (Get-FileSha256Hex $binaryPath) -ne $expectedBinaryDigest) {
            Stop-Adapter "metaeditor_recovery_binary_digest_mismatch"
        }
        $editors = @(Get-ExactProcesses $compilerPath)
        if ($editors.Count -ne 1) { Stop-Adapter "metaeditor_recovery_process_ambiguous" }
        $editorWindow = Get-TopWindow ([int]$editors[0].Id) "metaeditor"
        if ($editorWindow.Current.Name -ne ("MetaEditor - [{0}]" -f [System.IO.Path]::GetFileName($sourcePath))) {
            Stop-Adapter "metaeditor_recovery_source_mismatch"
        }
        Assert-NoModal ([int]$editors[0].Id) ([IntPtr]$editorWindow.Current.NativeWindowHandle)
        $editor = [pscustomobject]@{ Process = $editors[0]; Window = $editorWindow }
        $compileResultLine = Read-MetaEditorCompileResult `
            $editor.Window `
            ([int]$editor.Process.Id) `
            ([System.IO.Path]::GetFileName($sourcePath)) `
            $true
        $processBinding = New-RawBinding $terminal $editor "metaeditor" $autoBefore
        Start-Sleep -Milliseconds 100
        $terminalPost = Get-ExistingVisibleProcess $terminalPath "terminal"
        $editorPost = Get-ExistingVisibleProcess $compilerPath "metaeditor"
        if ($editorPost.Window.Current.Name -ne $editor.Window.Current.Name) {
            Stop-Adapter "metaeditor_recovery_source_drift"
        }
        $autoAfter = Get-AutoTradingState $terminalPost.Window ([int]$terminalPost.Process.Id)
        if ($autoAfter -ne $autoBefore) { Stop-Adapter "autotrading_state_changed" }
        $postBinding = New-RawBinding $terminalPost $editorPost "metaeditor" $autoAfter
        Write-JsonResult ([ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = "recover_compile"
            operationId = [string]$request.operationId
            processBinding = $processBinding
            postProcessBinding = $postBinding
            recoveredWithoutAction = $true
            exactSourceWindowVerified = $true
            compileResultLine = $compileResultLine
        }) 0
    }

    if ($request.action -in @(
        "recover_inflight_backtest",
        "recover_completed_backtest",
        "recover_collected_backtest"
    )) {
        $collectedCheckpoint = $request.action -eq "recover_collected_backtest"
        $completedCheckpoint = $request.action -in @(
            "recover_completed_backtest",
            "recover_collected_backtest"
        )
        # All recovery modes are collection-only and never invoke Start.  The
        # inflight mode requires a live Stop state and waits for Stop -> Start.
        # The completed mode is narrower: it requires the exact durable Start
        # boundary, a fresh result screenshot already committed by this same
        # operation, an advanced tester log, and an idle Start control before it
        # may collect the missing report.  The collected mode additionally
        # requires the canonical .htm report and both screenshots to exist; it
        # verifies those durable artifacts without opening Save As again.
        $expectedExpertPath = Join-Path $dataPath (
            "MQL4\Experts\Metafxclub\AgentHQ\{0}\{1}" -f
            [string]$request.operationId,
            [string]$request.expertFileName
        )
        $deployedExpertSha256 = Assert-DeployedExpertDigest `
            ([string]$request.deployedExpertPath) `
            $expectedExpertPath `
            ([string]$request.expectedDeployedExpertSha256)
        $boundaryPath = Get-FullPath $request.startBoundaryPath
        $boundaryTime = Assert-DurableStartBoundary `
            $boundaryPath `
            ([string]$request.startBoundaryJson) `
            ([string]$request.startBoundarySha256) `
            ([string]$request.operationId) `
            ([string]$request.actionRequestDigest)
        $settingsPath = Get-FullPath $request.settingsScreenshotPath
        $resultPath = Get-FullPath $request.resultScreenshotPath
        $reportScreenshotPath = Get-FullPath $request.reportScreenshotPath
        $reportPath = Get-FullPath $request.testerReportPath
        $resultExists = [System.IO.File]::Exists($resultPath)
        $reportScreenshotExists = [System.IO.File]::Exists($reportScreenshotPath)
        $reportExists = [System.IO.File]::Exists($reportPath)
        $legacyReportPath = [System.IO.Path]::ChangeExtension($reportPath, ".html")
        if (-not [string]::Equals(
            [System.IO.Path]::GetExtension($reportPath),
            ".htm",
            [System.StringComparison]::OrdinalIgnoreCase
        ) -or [System.IO.File]::Exists($legacyReportPath)) {
            # Never accept the legacy .html alias as the durable Tester report.
            Stop-Adapter "tester_inflight_recovery_checkpoint_invalid"
        }
        if (-not [System.IO.File]::Exists($settingsPath) -or
            (Get-Item -LiteralPath $settingsPath).Length -lt 1024 -or
            ($completedCheckpoint -and (-not $resultExists -or
                (Get-Item -LiteralPath $resultPath).Length -lt 1024)) -or
            ((-not $completedCheckpoint) -and $resultExists) -or
            ($reportScreenshotExists -and (-not $resultExists -or
                (Get-Item -LiteralPath $reportScreenshotPath).Length -lt 1024)) -or
            ($collectedCheckpoint -and (-not $reportScreenshotExists -or
                -not $reportExists -or
                (Get-Item -LiteralPath $reportPath).Length -lt 1024)) -or
            ((-not $collectedCheckpoint) -and $reportExists)) {
            Stop-Adapter "tester_inflight_recovery_checkpoint_invalid"
        }
        if ($resultExists) {
            Assert-ExistingPngEvidence `
                $resultPath `
                "tester_inflight_recovery_checkpoint_invalid"
        }
        if ($reportScreenshotExists) {
            Assert-ExistingPngEvidence `
                $reportScreenshotPath `
                "tester_inflight_recovery_checkpoint_invalid"
        }
        $presetResult = [ordered]@{
            testerInputPresetApplied = $false
            testerInputPresetReadbackVerified = $false
            inputPresetReadbackSaved = $false
        }
        if ($null -ne $request.testerSettings.testerInputPreset) {
            $presetSetPath = Get-FullPath $request.inputPresetSetPath
            $readbackSetPath = Get-FullPath $request.inputReadbackSetPath
            $inputScreenshotPath = Get-FullPath $request.inputPresetScreenshotPath
            if (-not [System.IO.File]::Exists($presetSetPath) -or
                -not [System.IO.File]::Exists($readbackSetPath) -or
                -not [System.IO.File]::Exists($inputScreenshotPath) -or
                (Get-Item -LiteralPath $inputScreenshotPath).Length -lt 1024 -or
                -not (Test-TesterInputReadbackSet $readbackSetPath $request.testerSettings.testerInputPreset)) {
                Stop-Adapter "tester_inflight_recovery_preset_invalid"
            }
            $presetResult = [ordered]@{
                testerInputPresetApplied = $true
                testerInputPresetReadbackVerified = $true
                inputPresetReadbackSaved = $true
            }
        } elseif ($null -ne $request.inputPresetSetPath -or
            $null -ne $request.inputReadbackSetPath -or
            $null -ne $request.inputPresetScreenshotPath) {
            Stop-Adapter "tester_inflight_recovery_preset_unexpected"
        }
        $tester = Select-TesterSettingsTab $terminal.Window ([int]$terminal.Process.Id)
        $start = Get-TesterStartButton $tester ([int]$terminal.Process.Id)
        $startName = ([string]$start.Current.Name).Trim()
        if ($completedCheckpoint -and $startName -ne "Start") {
            Stop-Adapter "tester_completed_recovery_not_idle"
        }
        if ((-not $completedCheckpoint) -and $startName -ne "Stop") {
            Stop-Adapter "tester_recovery_execution_unproven"
        }
        $expert = Read-ExpertSelection $tester ([int]$terminal.Process.Id)
        if (-not (Test-ExactExpertValue $expert.value ([string]$request.expertUiPath) ([string]$request.expertFileName))) {
            Stop-Adapter "tester_recovery_expert_mismatch"
        }
        $symbol = Read-CurrentSymbol $tester ([int]$terminal.Process.Id)
        $period = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "1228"
        $model = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "4027"
        $spread = Read-Spread $tester ([int]$terminal.Process.Id)
        $expectedModelPrefix = switch ([string]$request.testerSettings.model) {
            "every_tick" { "Every tick" }
            "control_points" { "Control points" }
            "open_prices" { "Open prices" }
            default { "" }
        }
        if (-not $symbol -or -not ([string]$spread).Trim() -or
            -not (Test-TesterComboValue "1228" $period ([string]$request.testerSettings.period)) -or
            -not $expectedModelPrefix -or
            -not $model.StartsWith($expectedModelPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1023")) -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1029")) -or
            -not (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1400"))) {
            Stop-Adapter "tester_recovery_settings_mismatch"
        }
        $recoveryObservedAt = [DateTime]::UtcNow
        $testerLogBefore = Get-TesterLogSnapshot $dataPath
        $testerFrontOffice = [pscustomobject]@{ Process = $terminal.Process; Window = $tester }
        $processBinding = New-RawBinding $terminal $testerFrontOffice "strategy_tester" $autoBefore
        if ($completedCheckpoint) {
            if (-not (Test-TesterLogAdvanced $dataPath @{} $boundaryTime)) {
                Stop-Adapter "tester_completed_recovery_log_unverified"
            }
            $completionObservation = if ($collectedCheckpoint) {
                "collected_checkpoint_observed"
            } else {
                "completed_checkpoint_observed"
            }
        } else {
            $completionObservation = Wait-TesterComplete `
                $terminal.Window `
                ([int]$terminal.Process.Id) `
                ([Math]::Min(7200, [int]$request.timeoutSeconds)) `
                $dataPath `
                $testerLogBefore `
                $recoveryObservedAt `
                $true
            if ($completionObservation -ne "stop_transition_observed" -or
                -not (Test-TesterLogAdvanced $dataPath @{} $boundaryTime)) {
                Stop-Adapter "tester_inflight_recovery_completion_unverified"
            }
            # Commit the completed terminal window before optional Report-tab
            # collection.  If MT4's owner-drawn tabs cannot be reached, this
            # immutable checkpoint lets an explicit resume collect the report
            # later without ever pressing Start a second time.
            Save-WindowPng $terminal.Window $resultPath
        }
        if (-not $collectedCheckpoint) {
            Save-TesterReport `
                $terminal.Window `
                ([int]$terminal.Process.Id) `
                $reportPath `
                $reportScreenshotPath `
                $true
        }
        $resultItem = Get-Item -LiteralPath $resultPath
        $reportScreenshotItem = Get-Item -LiteralPath $reportScreenshotPath
        $reportItem = Get-Item -LiteralPath $reportPath
        if (($completedCheckpoint -and (
                $resultItem.LastWriteTimeUtc -lt $boundaryTime.AddSeconds(-1) -or
                $resultItem.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(1)
            )) -or
            ((-not $completedCheckpoint) -and
                $resultItem.LastWriteTimeUtc -lt $recoveryObservedAt.AddSeconds(-1)) -or
            $reportScreenshotItem.LastWriteTimeUtc -lt $boundaryTime.AddSeconds(-1) -or
            $reportScreenshotItem.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(1) -or
            ($collectedCheckpoint -and (
                $reportItem.LastWriteTimeUtc -lt $boundaryTime.AddSeconds(-1) -or
                $reportItem.LastWriteTimeUtc -gt [DateTime]::UtcNow.AddMinutes(1)
            )) -or
            ((-not $collectedCheckpoint) -and
                $reportItem.LastWriteTimeUtc -lt $recoveryObservedAt.AddSeconds(-1))) {
            Stop-Adapter "tester_inflight_recovery_evidence_not_fresh"
        }
        $terminalPost = Get-ExistingVisibleProcess $terminalPath "terminal"
        $autoAfter = Get-AutoTradingState $terminalPost.Window ([int]$terminalPost.Process.Id)
        if ($autoAfter -ne $autoBefore) { Stop-Adapter "autotrading_state_changed" }
        $testerPost = Select-TesterSettingsTab $terminalPost.Window ([int]$terminalPost.Process.Id)
        $expertPost = Read-ExpertSelection $testerPost ([int]$terminalPost.Process.Id)
        if (-not (Test-ExactExpertValue $expertPost.value ([string]$request.expertUiPath) ([string]$request.expertFileName))) {
            Stop-Adapter "tester_recovery_expert_drift"
        }
        $postFrontOffice = [pscustomobject]@{ Process = $terminalPost.Process; Window = $testerPost }
        $postBinding = New-RawBinding $terminalPost $postFrontOffice "strategy_tester" $autoAfter
        $resolved = [ordered]@{
            schemaVersion = "ea-factory-resolved-tester-settings-v1"
            expertFileName = [string]$request.expertFileName
            symbol = $symbol
            period = [string]$request.testerSettings.period
            model = [string]$request.testerSettings.model
            spread = $spread
            useDate = $false
            fromDate = $null
            toDate = $null
            deposit = $null
            visualMode = $true
            optimizationEnabled = $false
            shutdownTerminalAfterTest = $false
        }
        Write-JsonResult ([ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = [string]$request.action
            operationId = [string]$request.operationId
            processBinding = $processBinding
            postProcessBinding = $postBinding
            recoveredWithoutStart = $true
            startInvoked = $false
            executionObservedRunning = -not $completedCheckpoint
            completedResultCheckpointReused = $completedCheckpoint
            completedReportCheckpointReused = $collectedCheckpoint
            testerCompleted = $true
            testerCompletionObservation = if ($collectedCheckpoint) {
                "recovery_collected_checkpoint_observed"
            } elseif ($completedCheckpoint) {
                "recovery_completed_checkpoint_observed"
            } else {
                "recovery_stop_transition_observed"
            }
            fastCompletionTesterLogAdvanced = $false
            freshResultEvidenceCaptured = $true
            exactExpertVerified = $true
            selectedExpertReadback = [string]$expert.value
            deployedExpertSha256 = $deployedExpertSha256
            startBoundaryCommitted = $true
            startBoundarySha256 = [string]$request.startBoundarySha256
            actionRequestDigest = [string]$request.actionRequestDigest
            resolvedTesterSettings = $resolved
            testerInputPresetApplied = [bool]$presetResult.testerInputPresetApplied
            testerInputPresetReadbackVerified = [bool]$presetResult.testerInputPresetReadbackVerified
            inputPresetReadbackSaved = [bool]$presetResult.inputPresetReadbackSaved
        }) 0
    }

    if ($request.action -eq "recover_backtest") {
        $expectedExpertPath = Join-Path $dataPath (
            "MQL4\Experts\Metafxclub\AgentHQ\{0}\{1}" -f
            [string]$request.operationId,
            [string]$request.expertFileName
        )
        $deployedExpertSha256 = Assert-DeployedExpertDigest `
            ([string]$request.deployedExpertPath) `
            $expectedExpertPath `
            ([string]$request.expectedDeployedExpertSha256)
        $tester = Get-TesterPane $terminal.Window ([int]$terminal.Process.Id)
        $start = Get-TesterStartButton $tester ([int]$terminal.Process.Id)
        if (([string]$start.Current.Name).Trim() -ne "Start") { Stop-Adapter "tester_recovery_not_idle" }
        $expert = Read-ExpertSelection $tester ([int]$terminal.Process.Id)
        if (-not (Test-ExactExpertValue $expert.value ([string]$request.expertUiPath) ([string]$request.expertFileName))) {
            Stop-Adapter "tester_recovery_expert_mismatch"
        }
        $symbol = Read-CurrentSymbol $tester ([int]$terminal.Process.Id)
        $period = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "1228"
        $model = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "4027"
        $spread = Read-Spread $tester ([int]$terminal.Process.Id)
        $expected = $request.expectedResolvedTesterSettings
        $expectedModelPrefix = switch ([string]$expected.model) {
            "every_tick" { "Every tick" }
            "control_points" { "Control points" }
            "open_prices" { "Open prices" }
            default { "" }
        }
        $spreadMatches = ([string]$spread).Trim().Equals(
            ([string]$expected.spread).Trim(),
            [System.StringComparison]::OrdinalIgnoreCase
        )
        if ([string]$expected.spread -match '^\d+$' -and [string]$spread -match '^\d+$') {
            $spreadMatches = ([int]$expected.spread -eq [int]$spread)
        }
        if (-not $symbol.Equals([string]$expected.symbol, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not (Test-TesterComboValue "1228" $period ([string]$expected.period)) -or
            -not $expectedModelPrefix -or
            -not $model.StartsWith($expectedModelPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            -not $spreadMatches -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1023")) -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1029")) -or
            -not (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1400"))) {
            Stop-Adapter "tester_recovery_settings_mismatch"
        }
        $testerFrontOffice = [pscustomobject]@{ Process = $terminal.Process; Window = $tester }
        $processBinding = New-RawBinding $terminal $testerFrontOffice "strategy_tester" $autoBefore
        Start-Sleep -Milliseconds 100
        $terminalPost = Get-ExistingVisibleProcess $terminalPath "terminal"
        $testerPost = Get-TesterPane $terminalPost.Window ([int]$terminalPost.Process.Id)
        $autoAfter = Get-AutoTradingState $terminalPost.Window ([int]$terminalPost.Process.Id)
        if ($autoAfter -ne $autoBefore) { Stop-Adapter "autotrading_state_changed" }
        $postFrontOffice = [pscustomobject]@{ Process = $terminalPost.Process; Window = $testerPost }
        $postBinding = New-RawBinding $terminalPost $postFrontOffice "strategy_tester" $autoAfter
        Write-JsonResult ([ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = "recover_backtest"
            operationId = [string]$request.operationId
            processBinding = $processBinding
            postProcessBinding = $postBinding
            recoveredWithoutAction = $true
            exactExpertVerified = $true
            selectedExpertReadback = [string]$expert.value
            deployedExpertSha256 = $deployedExpertSha256
            settingsStillVerified = $true
        }) 0
    }

    if ($request.action -eq "compile") {
        $sourcePath = Get-FullPath $request.sourcePath
        $binaryPath = Get-FullPath $request.binaryPath
        $screenshotPath = Get-FullPath $request.screenshotPath
        if (-not [System.IO.File]::Exists($sourcePath) -or [System.IO.Path]::GetExtension($sourcePath) -ine ".mq4") {
            Stop-Adapter "source_file_invalid"
        }
        $editorProcesses = @(Get-ExactProcesses $compilerPath)
        if ($editorProcesses.Count -gt 1) { Stop-Adapter "metaeditor_process_ambiguous" }
        # Always pass the exact absolute source to MetaEditor.  If an instance
        # already exists Windows routes this open request to that instance; it
        # is never closed or restarted by the adapter.
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $compilerPath
        $startInfo.UseShellExecute = $true
        $startInfo.Arguments = '"' + $sourcePath.Replace('"', '\"') + '"'
        [void][System.Diagnostics.Process]::Start($startInfo)
        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        do {
            Start-Sleep -Milliseconds 200
            $matchingEditors = @()
            foreach ($process in @(Get-ExactProcesses $compilerPath)) {
                try {
                    $window = Get-TopWindow ([int]$process.Id) "metaeditor"
                    if ($window.Current.Name -eq ("MetaEditor - [{0}]" -f [System.IO.Path]::GetFileName($sourcePath))) {
                        $matchingEditors += [pscustomobject]@{ Process = $process; Window = $window }
                    }
                } catch { }
            }
            if ($matchingEditors.Count -eq 1) { $editor = $matchingEditors[0]; break }
            if ($matchingEditors.Count -gt 1) { Stop-Adapter "metaeditor_source_window_ambiguous" }
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($null -eq $editor) { Stop-Adapter "metaeditor_source_window_not_ready" }
        Restore-Foreground $editor.Window
        Assert-NoModal ([int]$editor.Process.Id) ([IntPtr]$editor.Window.Current.NativeWindowHandle)
        $beforeBinaryWrite = if ([System.IO.File]::Exists($binaryPath)) { (Get-Item -LiteralPath $binaryPath).LastWriteTimeUtc.Ticks } else { 0 }
        $processBinding = New-RawBinding $terminal $editor "metaeditor" $autoBefore
        Invoke-MetaEditorCompile $editor.Window ([System.IO.Path]::GetFileName($sourcePath))
        $deadline = [DateTime]::UtcNow.AddSeconds([Math]::Min(120, [int]$request.timeoutSeconds))
        $freshBinary = $false
        do {
            Start-Sleep -Milliseconds 150
            if ([System.IO.File]::Exists($binaryPath)) {
                $write = (Get-Item -LiteralPath $binaryPath).LastWriteTimeUtc.Ticks
                if ($write -gt $beforeBinaryWrite -and (Get-Item -LiteralPath $binaryPath).Length -gt 0) {
                    $freshBinary = $true
                    break
                }
            }
        } while ([DateTime]::UtcNow -lt $deadline)
        if (-not $freshBinary) { Stop-Adapter "visible_compile_binary_not_fresh" }
        $compileResultLine = Read-MetaEditorCompileResult `
            $editor.Window `
            ([int]$editor.Process.Id) `
            ([System.IO.Path]::GetFileName($sourcePath)) `
            $freshBinary
        Save-WindowPng $editor.Window $screenshotPath
        $terminalPost = Get-ExistingVisibleProcess $terminalPath "terminal"
        $editorPost = Get-ExistingVisibleProcess $compilerPath "metaeditor"
        $autoAfter = Get-AutoTradingState $terminalPost.Window ([int]$terminalPost.Process.Id)
        if ($autoAfter -ne $autoBefore) { Stop-Adapter "autotrading_state_changed" }
        $postBinding = New-RawBinding $terminalPost $editorPost "metaeditor" $autoAfter
        $result = [ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = "compile"
            operationId = [string]$request.operationId
            processBinding = $processBinding
            postProcessBinding = $postBinding
            compileInvoked = $true
            exactSourceWindowVerified = $true
            freshBinaryObserved = $true
            compileResultLine = $compileResultLine
        }
        Write-JsonResult $result 0
    }

    if ($request.action -eq "backtest") {
        $expectedExpertPath = Join-Path $dataPath (
            "MQL4\Experts\Metafxclub\AgentHQ\{0}\{1}" -f
            [string]$request.operationId,
            [string]$request.expertFileName
        )
        $deployedExpertSha256 = Assert-DeployedExpertDigest `
            ([string]$request.deployedExpertPath) `
            $expectedExpertPath `
            ([string]$request.expectedDeployedExpertSha256)
        $checkpoint = "ensure_tester_visible"
        Ensure-TesterVisible $terminal
        $checkpoint = "restore_foreground"
        Restore-Foreground $terminal.Window
        $checkpoint = "assert_no_modal"
        Assert-NoModal ([int]$terminal.Process.Id) ([IntPtr]$terminal.Window.Current.NativeWindowHandle)
        $checkpoint = "tester_pane"
        $tester = Get-TesterPane $terminal.Window ([int]$terminal.Process.Id)
        $checkpoint = "tester_idle"
        $startButton = Get-TesterStartButton $tester ([int]$terminal.Process.Id)
        if (([string]$startButton.Current.Name).Trim() -ne "Start") { Stop-Adapter "tester_not_idle" }
        $checkpoint = "refresh_expert_inventory"
        Refresh-ExpertInventory $terminal.Window ([int]$terminal.Process.Id) `
            ([string]$request.expertUiPath) ([string]$request.expertFileName)
        $checkpoint = "select_exact_expert"
        $selectedExpert = Select-ExactExpert $terminal.Window ([int]$terminal.Process.Id) `
            ([string]$request.expertUiPath) ([string]$request.expertFileName) `
            ([int]$request.maxExpertSelectionSteps)
        $checkpoint = "tester_settings"
        $tester = Get-TesterPane $terminal.Window ([int]$terminal.Process.Id)
        $symbol = Read-CurrentSymbol $tester ([int]$terminal.Process.Id)
        $period = Select-ComboListItem $tester $terminal.Window ([int]$terminal.Process.Id) "1228" ([string]$request.testerSettings.period)
        $modelPrefix = switch ([string]$request.testerSettings.model) {
            "every_tick" { "Every tick" }
            "control_points" { "Control points" }
            "open_prices" { "Open prices only" }
            default { Stop-Adapter "tester_model_policy_invalid" }
        }
        [void](Select-ComboListItem $tester $terminal.Window ([int]$terminal.Process.Id) "4027" $modelPrefix)
        $spread = Read-Spread $tester ([int]$terminal.Process.Id)
        [void](Set-ButtonCheck $tester ([int]$terminal.Process.Id) "1023" $false)
        [void](Set-ButtonCheck $tester ([int]$terminal.Process.Id) "1029" $false)
        [void](Set-ButtonCheck $tester ([int]$terminal.Process.Id) "1400" $true)

        $presetResult = [ordered]@{
            testerInputPresetApplied = $false
            testerInputPresetReadbackVerified = $false
            inputPresetReadbackSaved = $false
        }
        $hasInputPreset = (
            $request.testerSettings.PSObject.Properties.Name -contains "testerInputPreset"
        )
        if ($hasInputPreset) {
            $checkpoint = "validate_input_preset"
            $preset = $request.testerSettings.testerInputPreset
            if ($null -eq $preset) {
                Stop-Adapter "tester_input_preset_policy_invalid"
            }
            $simulationInputNames = @($preset.simulationInputNames)
            $assumptions = @($preset.assumptions)
            if ([string]$preset.schemaVersion -ne "ea-factory-tester-input-preset-v1" -or
                [string]$preset.mode -ne "full_certified_input_snapshot_with_explicit_simulation_assumptions" -or
                [string]$preset.scope -ne "mt4_strategy_tester_only" -or
                $preset.liveSourceDefaultsPreserved -ne $true -or
                $preset.visibleExpertPropertiesRequired -ne $true -or
                $preset.readbackRequired -ne $true -or
                $preset.liveTradingAllowed -ne $false -or
                $preset.fullCertifiedInputSnapshot -ne $true -or
                $assumptions.Count -lt 1 -or $assumptions.Count -gt 64) {
                Stop-Adapter "tester_input_preset_policy_invalid"
            }
            $expectedByName = @{}
            $derivedSimulationNames = New-Object System.Collections.Generic.List[string]
            foreach ($assumption in $assumptions) {
                $name = [string]$assumption.inputName
                $kind = [string]$assumption.inputType
                $reason = [string]$assumption.reasonCode
                if ($name -notmatch '^[A-Za-z_][A-Za-z0-9_]*$' -or
                    $kind -notin @("bool", "int", "double") -or
                    -not $reason -or $expectedByName.ContainsKey($name)) {
                    Stop-Adapter "tester_input_preset_assumption_invalid"
                }
                $expectedByName[$name] = $true
                $isSimulation = ($assumption.testerValue -ne $assumption.sourceDefault)
                if ($isSimulation) {
                    if ($kind -ne "bool" -or
                        $assumption.sourceDefault -ne $false -or
                        $assumption.testerValue -ne $true -or
                        $name -notmatch '(?i)(Fundamental|External|Eligibility|Screen|Criteria)' -or
                        $name -match '(?i)(EnableTrading|TradingEnabled|AllowTrading|LiveTrading|AutoTrading|Safety)' -or
                        $reason -notlike 'simulate_*_for_historical_test_only') {
                        Stop-Adapter "tester_input_preset_assumption_invalid"
                    }
                    [void]$derivedSimulationNames.Add($name)
                } elseif ($kind -eq "double") {
                    [double]$sourceValue = [double]$assumption.sourceDefault
                    [double]$testerValue = [double]$assumption.testerValue
                    $tolerance = 0.000000000001 * [Math]::Max(1.0, [Math]::Abs($sourceValue))
                    if ([double]::IsNaN($sourceValue) -or [double]::IsInfinity($sourceValue) -or
                        [double]::IsNaN($testerValue) -or [double]::IsInfinity($testerValue) -or
                        [Math]::Abs($sourceValue - $testerValue) -gt $tolerance) {
                        Stop-Adapter "tester_input_preset_assumption_invalid"
                    }
                } elseif ($assumption.sourceDefault -ne $assumption.testerValue) {
                    Stop-Adapter "tester_input_preset_assumption_invalid"
                }
            }
            if ($simulationInputNames.Count -ne $derivedSimulationNames.Count) {
                Stop-Adapter "tester_input_preset_policy_invalid"
            }
            for ($index = 0; $index -lt $simulationInputNames.Count; $index++) {
                if ([string]$simulationInputNames[$index] -ne
                    [string]$derivedSimulationNames[$index]) {
                    Stop-Adapter "tester_input_preset_policy_invalid"
                }
            }
            $presetSetPath = Get-FullPath $request.inputPresetSetPath
            $readbackSetPath = Get-FullPath $request.inputReadbackSetPath
            $inputScreenshotPath = Get-FullPath $request.inputPresetScreenshotPath
            $presetResult = Apply-TesterInputPreset `
                $terminal.Window `
                $tester `
                ([int]$terminal.Process.Id) `
                $preset `
                $presetSetPath `
                $readbackSetPath `
                $inputScreenshotPath
            $checkpoint = "input_preset_applied"
            $tester = Get-TesterPane $terminal.Window ([int]$terminal.Process.Id)
        }

        # Re-resolve and independently read every critical field immediately
        # before Start.  From/To controls are intentionally never written.
        $checkpoint = "prestart_readback"
        $tester = Get-TesterPane $terminal.Window ([int]$terminal.Process.Id)
        $expertReadback = Read-ExpertSelection $tester ([int]$terminal.Process.Id)
        if (-not (Test-ExactExpertValue $expertReadback.value ([string]$request.expertUiPath) ([string]$request.expertFileName))) {
            Stop-Adapter "expert_prestart_readback_mismatch"
        }
        $symbol = Read-CurrentSymbol $tester ([int]$terminal.Process.Id)
        $periodReadback = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "1228"
        $modelReadback = Read-SelectedNativeComboValue $tester ([int]$terminal.Process.Id) "4027"
        $spread = Read-Spread $tester ([int]$terminal.Process.Id)
        if (-not (Test-TesterComboValue "1228" $periodReadback ([string]$request.testerSettings.period)) -or
            -not $modelReadback.StartsWith($modelPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1023")) -or
            (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1029")) -or
            -not (Read-ButtonCheck (Get-TesterCheckControl $tester ([int]$terminal.Process.Id) "1400"))) {
            Stop-Adapter "tester_prestart_settings_mismatch"
        }
        $visualSpeed = Set-TesterVisualSpeedMaximum $tester ([int]$terminal.Process.Id)
        $settingsPath = Get-FullPath $request.settingsScreenshotPath
        $resultPath = Get-FullPath $request.resultScreenshotPath
        $reportScreenshotPath = Get-FullPath $request.reportScreenshotPath
        $reportPath = Get-FullPath $request.testerReportPath
        $checkpoint = "settings_screenshot"
        Save-WindowPng $terminal.Window $settingsPath
        $testerFrontOffice = [pscustomobject]@{ Process = $terminal.Process; Window = $tester }
        $processBinding = New-RawBinding $terminal $testerFrontOffice "strategy_tester" $autoBefore
        $testerLogBefore = Get-TesterLogSnapshot $dataPath
        $checkpoint = "deployed_expert_prestart_digest"
        $deployedExpertSha256 = Assert-DeployedExpertDigest `
            ([string]$request.deployedExpertPath) `
            $expectedExpertPath `
            ([string]$request.expectedDeployedExpertSha256)
        $startBoundaryPath = Get-FullPath $request.startBoundaryPath
        $checkpoint = "commit_start_boundary"
        $startBoundarySha256 = Write-DurableStartBoundary `
            $startBoundaryPath `
            ([string]$request.startBoundaryJson) `
            ([string]$request.startBoundarySha256) `
            ([string]$request.operationId) `
            ([string]$request.actionRequestDigest)
        $startInvokedAt = [DateTime]::UtcNow
        $checkpoint = "start_tester"
        $stopAlreadyObserved = Invoke-StartButton $tester ([int]$terminal.Process.Id)
        $checkpoint = "wait_tester"
        $completionObservation = Wait-TesterComplete `
            $terminal.Window `
            ([int]$terminal.Process.Id) `
            ([Math]::Min(900, [int]$request.timeoutSeconds)) `
            $dataPath `
            $testerLogBefore `
            $startInvokedAt `
            $stopAlreadyObserved
        # This is the durable post-completion checkpoint.  Keep it before the
        # owner-drawn Report-tab interaction so a collection-only retry can be
        # proven safe and can never start the Tester again.
        $checkpoint = "result_screenshot"
        Save-WindowPng $terminal.Window $resultPath
        $checkpoint = "save_tester_report"
        Save-TesterReport `
            $terminal.Window `
            ([int]$terminal.Process.Id) `
            $reportPath `
            $reportScreenshotPath `
            $false
        $resultItem = Get-Item -LiteralPath $resultPath
        $reportScreenshotItem = Get-Item -LiteralPath $reportScreenshotPath
        $reportItem = Get-Item -LiteralPath $reportPath
        if ($resultItem.LastWriteTimeUtc -lt $startInvokedAt.AddSeconds(-1) -or
            $reportScreenshotItem.LastWriteTimeUtc -lt $startInvokedAt.AddSeconds(-1) -or
            $reportItem.LastWriteTimeUtc -lt $startInvokedAt.AddSeconds(-1)) {
            Stop-Adapter "tester_result_evidence_not_fresh"
        }
        $checkpoint = "post_binding"
        $terminalPost = Get-ExistingVisibleProcess $terminalPath "terminal"
        $autoAfter = Get-AutoTradingState $terminalPost.Window ([int]$terminalPost.Process.Id)
        if ($autoAfter -ne $autoBefore) { Stop-Adapter "autotrading_state_changed" }
        $testerPost = Get-TesterPane $terminalPost.Window ([int]$terminalPost.Process.Id)
        $testerPostFrontOffice = [pscustomobject]@{ Process = $terminalPost.Process; Window = $testerPost }
        $postBinding = New-RawBinding $terminalPost $testerPostFrontOffice "strategy_tester" $autoAfter
        $resolved = [ordered]@{
            schemaVersion = "ea-factory-resolved-tester-settings-v1"
            expertFileName = [string]$request.expertFileName
            symbol = $symbol
            period = [string]$request.testerSettings.period
            model = [string]$request.testerSettings.model
            spread = $spread
            useDate = $false
            fromDate = $null
            toDate = $null
            # The main Tester pane does not expose Initial deposit.  Leave it
            # unresolved here; Python's read-only verifier derives the numeric
            # value from the exact saved Tester HTML before evidence commit.
            deposit = $null
            visualMode = $true
            optimizationEnabled = $false
            shutdownTerminalAfterTest = $false
        }
        $result = [ordered]@{
            schemaVersion = "ea-factory-visible-powershell-result-v1"
            ok = $true
            action = "backtest"
            operationId = [string]$request.operationId
            processBinding = $processBinding
            postProcessBinding = $postBinding
            startInvoked = $true
            testerCompleted = $true
            testerCompletionObservation = $completionObservation
            fastCompletionTesterLogAdvanced = ($completionObservation -eq "fast_idle_evidence_required")
            freshResultEvidenceCaptured = $true
            exactExpertVerified = $true
            selectedExpertReadback = $selectedExpert
            deployedExpertSha256 = $deployedExpertSha256
            startBoundaryCommitted = $true
            startBoundarySha256 = $startBoundarySha256
            actionRequestDigest = [string]$request.actionRequestDigest
            resolvedTesterSettings = $resolved
            testerInputPresetApplied = [bool]$presetResult.testerInputPresetApplied
            testerInputPresetReadbackVerified = [bool]$presetResult.testerInputPresetReadbackVerified
            inputPresetReadbackSaved = [bool]$presetResult.inputPresetReadbackSaved
            visualSpeedBefore = [int]$visualSpeed.before
            visualSpeedAfter = [int]$visualSpeed.after
            visualSpeedMaximum = [int]$visualSpeed.maximum
        }
        Write-JsonResult $result 0
    }

    Stop-Adapter "visible_action_unsupported"
} catch {
    $message = [string]$_.Exception.Message
    $code = "visible_ui_action_failed"
    if ($message -match 'METAFX_VISIBLE:([a-z0-9_]{3,80})') { $code = $Matches[1] }
    elseif ($null -ne $request -and [string]$request.action -eq "backtest" -and
        [string]$checkpoint -match '^[a-z0-9_]{3,50}$') {
        $code = "visible_backtest_{0}_failed" -f [string]$checkpoint
    }
    if ($code -eq "window_message_timeout" -and
        $null -ne $request -and [string]$request.action -eq "backtest" -and
        [string]$checkpoint -match '^[a-z0-9_]{3,50}$') {
        # Preserve the exact pre/post-Start checkpoint while keeping the
        # public code path-free and retry classification suffix-compatible.
        $code = "window_message_{0}_timeout" -f [string]$checkpoint
    }
    Write-JsonResult ([ordered]@{
        schemaVersion = "ea-factory-visible-powershell-result-v1"
        ok = $false
        action = if ($null -ne $request) { [string]$request.action } else { $null }
        operationId = if ($null -ne $request) { [string]$request.operationId } else { $null }
        reasonCode = $code
    }) 1
}
