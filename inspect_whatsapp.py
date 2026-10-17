import uiautomation as auto
import os
import psutil
import ctypes
import ctypes.wintypes


def get_whatsapp_pids():
    """Return a set of PIDs belonging to WhatsApp processes."""
    pids = set()
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if "whatsapp" in (proc.info["name"] or "").lower():
                pids.add(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def find_whatsapp_window():
    """Find the WhatsApp window via multiple strategies."""
    wa_pids = get_whatsapp_pids()
    if not wa_pids:
        return None

    root = auto.GetRootControl()
    matches = []

    # Strategy 1: scan top-level children
    for win in root.GetChildren():
        try:
            if win.ProcessId in wa_pids:
                matches.append(win)
        except Exception:
            continue

    # Strategy 2: deeper UIA search (WinUI3 windows may hide from depth-1)
    if not matches:
        wa_win = auto.WindowControl(searchDepth=5, Name="WhatsApp")
        if wa_win.Exists(3, 1):
            matches.append(wa_win)

    # Strategy 3: walk the entire UIA tree (slow but thorough)
    if not matches:
        for control, depth in auto.WalkControl(root, maxDepth=4):
            try:
                if control.ProcessId in wa_pids:
                    matches.append(control)
                    break
            except Exception:
                continue

    if not matches:
        return None

    matches.sort(
        key=lambda w: w.BoundingRectangle.width() * w.BoundingRectangle.height(),
        reverse=True,
    )
    return matches[0]


def print_whatsapp_tree():
    wa_window = find_whatsapp_window()

    if wa_window is None:
        print("WhatsApp window not found. Ensure WhatsApp is open and visible.")
        return

    print(f"Found Window: {wa_window.Name} ({wa_window.ClassName})")

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "whatsapp_tree.txt"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        for control, depth in auto.WalkControl(wa_window, maxDepth=10):
            indent = " " * (depth * 2)
            try:
                line = (
                    f"{indent}- {control.ControlTypeName}: "
                    f"Name='{control.Name}', "
                    f"AutomationId='{control.AutomationId}', "
                    f"ClassName='{control.ClassName}'\n"
                )
                f.write(line)
            except Exception:
                continue
    print(f"Tree dumped to {out_path}")


if __name__ == "__main__":
    print_whatsapp_tree()