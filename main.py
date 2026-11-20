"""
VoiceMate Laptop Agent - Main Entry Point.
Run as desktop application or console CLI agent.
"""
import sys
import argparse
import signal
import time

try:
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

def run_gui():
    print("🚀 VoiceMate Desktop GUI চালু হচ্ছে...", flush=True)
    import tkinter as tk
    from src.ui.main_window import MainWindow

    root = tk.Tk()
    app = MainWindow(root)
    root.protocol("WM_DELETE_WINDOW", app._exit_app)
    root.mainloop()

def run_cli():
    print("=" * 60, flush=True)
    print("🎙️ VoiceMate - Laptop Agent (Console CLI Mode)", flush=True)
    print("ভয়েস মেট সক্রিয় আছে। আপনি ভয়েস বা টাইপ করে কমান্ড দিতে পারেন।", flush=True)
    print("বন্ধ করতে 'exit' বা 'কাটো' লিখুন অথবা Ctrl+C চাপুন।", flush=True)
    print("=" * 60, flush=True)

    from src.agent_service import AgentService

    def state_callback(state):
        msg = state.get("message", "")
        if msg:
            print(f"[Agent]: {msg}")

    agent = AgentService(on_state_change=state_callback)
    agent.start()

    def signal_handler(sig, frame):
        print("\nঅ্যাসিস্ট্যান্ট বন্ধ করা হচ্ছে...")
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while agent.is_running:
            try:
                cmd = input("কমান্ড লিখুন (বা কথা বলুন) > ").strip()
                if cmd.lower() in ["exit", "বন্ধ", "কাটো", "quit"]:
                    break
                if cmd:
                    agent.process_results(cmd)
            except EOFError:
                break
    finally:
        agent.stop()
        print("ভয়েস মেট বন্ধ করা হয়েছে।")

def main():
    parser = argparse.ArgumentParser(description="VoiceMate Laptop Voice Agent")
    parser.add_argument("--cli", action="store_true", help="Run in Terminal / CLI mode")
    args = parser.parse_args()

    if args.cli:
        run_cli()
    else:
        try:
            run_gui()
        except Exception as e:
            err_str = str(e).lower()
            if "application has been destroyed" not in err_str:
                print(f"GUI closed: {e}", flush=True)

if __name__ == "__main__":
    main()
