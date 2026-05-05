import tkinter as tk
from tkinter import scrolledtext
import speedtest
import threading
from datetime import datetime
import socket


class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Application")
        self.root.geometry("800x600")
        
        # Output text area
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            height=25,
            width=80
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.insert(tk.END, "Click 'Start Test' to begin speed testing...\n")
        
        # Button frame
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Start Test button
        self.start_button = tk.Button(
            self.button_frame,
            text="Start Test",
            command=self.start_test,
            width=15,
            height=2,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Re-test button
        self.retest_button = tk.Button(
            self.button_frame,
            text="Re-test",
            command=self.start_test,
            width=15,
            height=2,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.retest_button.pack(side=tk.LEFT, padx=5)
        
        # Exit button
        self.exit_button = tk.Button(
            self.button_frame,
            text="Exit",
            command=self.root.quit,
            width=15,
            height=2,
            bg="#f44336",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.exit_button.pack(side=tk.LEFT, padx=5)
        
        self.test_running = False
    
    def log_output(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def start_test(self):
        """Start the speed test in a separate thread"""
        if self.test_running:
            self.log_output("Test already in progress...")
            return
        
        self.test_running = True
        self.start_button.config(state=tk.DISABLED)
        self.retest_button.config(state=tk.DISABLED)
        
        self.output_text.delete(1.0, tk.END)
        self.log_output("=" * 60)
        self.log_output(f"Speed Test Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_output("=" * 60)
        self.log_output("")
        
        # Run speed test in separate thread
        test_thread = threading.Thread(target=self.run_speedtest)
        test_thread.daemon = True
        test_thread.start()
    
    def run_speedtest(self):
        """Run the actual speed test"""
        try:
            self.log_output("Initializing Speedtest...")
            st = speedtest.Speedtest()
            
            self.log_output("Getting server list...")
            st.get_servers()
            
            self.log_output("Getting best server...")
            best_server = st.get_best_server()
            
            # Server information
            self.log_output("\n" + "=" * 60)
            self.log_output("SERVER INFORMATION")
            self.log_output("=" * 60)
            self.log_output(f"Server: {best_server['sponsor']}")
            self.log_output(f"Location: {best_server['name']}, {best_server['country']}")
            self.log_output(f"Country Code: {best_server['cc']}")
            self.log_output(f"Latitude: {best_server['lat']}")
            self.log_output(f"Longitude: {best_server['lon']}")
            
            # ISP Information
            self.log_output("\n" + "=" * 60)
            self.log_output("ISP INFORMATION")
            self.log_output("=" * 60)
            isp = st.results.client.get('isp', 'N/A')
            ip_address = st.results.client.get('ip', 'N/A')
            country = st.results.client.get('country', 'N/A')
            self.log_output(f"ISP: {isp}")
            self.log_output(f"IP Address: {ip_address}")
            self.log_output(f"Country: {country}")
            
            # Download speed test
            self.log_output("\n" + "=" * 60)
            self.log_output("DOWNLOAD SPEED TEST")
            self.log_output("=" * 60)
            self.log_output("Testing download speed...")
            st.download()
            download_speed = st.results.download / 1_000_000  # Convert to Mbps
            self.log_output(f"Download Speed: {download_speed:.2f} Mbps")
            
            # Upload speed test
            self.log_output("\n" + "=" * 60)
            self.log_output("UPLOAD SPEED TEST")
            self.log_output("=" * 60)
            self.log_output("Testing upload speed...")
            st.upload()
            upload_speed = st.results.upload / 1_000_000  # Convert to Mbps
            self.log_output(f"Upload Speed: {upload_speed:.2f} Mbps")
            
            # Ping and Jitter
            self.log_output("\n" + "=" * 60)
            self.log_output("PING & LATENCY")
            self.log_output("=" * 60)
            
            # Get ping from results (already calculated during download/upload)
            ping = st.results.ping
            self.log_output(f"Ping (Latency): {ping:.2f} ms")
            
            # Calculate jitter with multiple ping attempts
            self.log_output("Calculating jitter...")
            pings = []
            for i in range(4):
                try:
                    # Measure ping by connecting to the server
                    import time
                    start = time.time()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((best_server['host'].split(':')[0], 80))
                    sock.close()
                    elapsed = (time.time() - start) * 1000
                    pings.append(elapsed)
                except:
                    pings.append(ping)
            
            if pings and len(pings) > 1:
                jitter = max(pings) - min(pings)
                self.log_output(f"Jitter: {jitter:.2f} ms")
            else:
                self.log_output("Jitter: Calculated from latency variation")
            
            # Summary
            self.log_output("\n" + "=" * 60)
            self.log_output("TEST SUMMARY")
            self.log_output("=" * 60)
            self.log_output(f"Download: {download_speed:.2f} Mbps")
            self.log_output(f"Upload: {upload_speed:.2f} Mbps")
            self.log_output(f"Ping: {ping:.2f} ms")
            self.log_output("=" * 60)
            self.log_output(f"Test Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_output("=" * 60)
            
        except Exception as e:
            self.log_output(f"\nERROR: {str(e)}")
            self.log_output("Please check your internet connection and try again.")
        
        finally:
            self.test_running = False
            self.start_button.config(state=tk.NORMAL)
            self.retest_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = SpeedTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
