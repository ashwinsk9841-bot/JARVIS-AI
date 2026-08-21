import threading, time, os, sys, socket, webbrowser

def resource_path(rel_path):
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, rel_path)

def run_streamlit():
    from streamlit.web import cli as stcli
    sys.argv = [
        "streamlit", "run", resource_path("app.py"),
        "--server.headless=true",
        "--global.developmentMode=false",
        "--server.address=127.0.0.1",
    ]
    stcli.main()  # blocks here on main thread — keeps the server alive

def wait_for_server(port=8501, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False

def open_browser_when_ready():
    if wait_for_server():
        webbrowser.open("http://127.0.0.1:8501")
    else:
        print("Streamlit failed to start in time.")

if __name__ == "__main__":
    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    run_streamlit()