"""
Speed Test GUI Application v1.01
================================================================================
CHANGELOG - Version 1.01
================================================================================
1. Added purple "Log" button to save test results to CSV file
2. Implemented CSV logging to 'internet_speed_log.csv' with full data export
3. CSV includes columns: timestamp, server, sponsor, location, country, cc, lat, 
   lon, isp, ip, download_mbps, upload_mbps, ping_ms, jitter_ms, comments
4. Newest test results are prepended to CSV (top row always latest)
5. Added comment input field with label "Comments, Keep it Short"
6. Comment input box spans full horizontal width of window
7. Log button disabled until test completes; enabled after results available
8. Window title updated to "Speed Test Application v1.01"
9. Window size increased to 900x620 to accommodate new UI elements
10. Comments from input field are automatically saved with each log entry

================================================================================
"""

import tkinter as tk
from tkinter import scrolledtext
import speedtest
import threading
from datetime import datetime
import socket
import csv
import os


class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Application v1.01")
        self.root.geometry("900x620")

        # Output text area
        self.output_frame = tk.Frame(root)
        self.output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.output_text = scrolledtext.ScrolledText(
            self.output_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            height=28,
            width=100
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.insert(tk.END, "Click 'Start Test' to begin speed testing...\n")

        # Comment entry (above buttons)
        self.comment_frame = tk.Frame(root)
        self.comment_frame.pack(fill=tk.X, padx=10, pady=(0, 6))
        tk.Label(self.comment_frame, text="Comments, Keep it Short", font=("Arial", 10)).pack(anchor='w')
        self.comment_entry = tk.Entry(self.comment_frame)
        self.comment_entry.pack(fill=tk.X, expand=True, padx=0, pady=(4, 0))

        # Button frame
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=6)

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

        # Log button (different color)
        self.log_button = tk.Button(
            self.button_frame,
            text="Log",
            command=self.save_log,
            width=15,
            height=2,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.log_button.pack(side=tk.LEFT, padx=5)
        self.log_button.config(state=tk.DISABLED)  # disabled until results exist

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
        self.latest_results = None

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
        self.log_button.config(state=tk.DISABLED)

        self.output_text.delete(1.0, tk.END)
        self.log_output("=" * 80)
        self.log_output(f"Speed Test Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_output("=" * 80)
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
            self.log_output(f"Server: {best_server.get('sponsor', 'N/A')}")
            self.log_output(f"Location: {best_server.get('name', 'N/A')}, {best_server.get('country', 'N/A')}")
            self.log_output(f"Country Code: {best_server.get('cc', 'N/A')}")
            self.log_output(f"Latitude: {best_server.get('lat', 'N/A')}")
            self.log_output(f"Longitude: {best_server.get('lon', 'N/A')}")

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
                    sock.connect((best_server.get('host', '').split(':')[0], 80))
                    sock.close()
                    elapsed = (time.time() - start) * 1000
                    pings.append(elapsed)
                except Exception:
                    pings.append(ping)

            if pings and len(pings) > 1:
                jitter = max(pings) - min(pings)
                self.log_output(f"Jitter: {jitter:.2f} ms")
            else:
                jitter = 0.0
                self.log_output("Jitter: Calculated from latency variation")

            # Save latest results to memory for logging
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.latest_results = {
                'timestamp': timestamp,
                'server': best_server.get('name', 'N/A'),
                'sponsor': best_server.get('sponsor', 'N/A'),
                'location': f"{best_server.get('name','N/A')}, {best_server.get('country','N/A')}",
                'country': best_server.get('country', 'N/A'),
                'cc': best_server.get('cc', 'N/A'),
                'lat': best_server.get('lat', 'N/A'),
                'lon': best_server.get('lon', 'N/A'),
                'isp': isp,
                'ip': ip_address,
                'download_mbps': round(download_speed, 2),
                'upload_mbps': round(upload_speed, 2),
                'ping_ms': round(ping, 2),
                'jitter_ms': round(jitter, 2),
                'comments': ''
            }

            # Summary
            self.log_output("\n" + "=" * 60)
            self.log_output("TEST SUMMARY")
            self.log_output("=" * 60)
            self.log_output(f"Download: {download_speed:.2f} Mbps")
            self.log_output(f"Upload: {upload_speed:.2f} Mbps")
            self.log_output(f"Ping: {ping:.2f} ms")
            self.log_output(f"Jitter: {jitter:.2f} ms")
            self.log_output("=" * 60)
            self.log_output(f"Test Completed - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_output("=" * 60)

            # Enable Log button now that results exist
            self.log_button.config(state=tk.NORMAL)

        except Exception as e:
            self.log_output(f"\nERROR: {str(e)}")
            self.log_output("Please check your internet connection and try again.")

        finally:
            self.test_running = False
            self.start_button.config(state=tk.NORMAL)
            self.retest_button.config(state=tk.NORMAL)

    def save_log(self):
        """Save the latest results to internet_speed_log.csv, newest row at top"""
        if not self.latest_results:
            self.log_output("No test results available to log.")
            return

        # Attach comment from entry
        comment = self.comment_entry.get().strip()
        self.latest_results['comments'] = comment

        filename = os.path.join(os.path.dirname(__file__), 'internet_speed_log.csv')
        header = ['timestamp', 'server', 'sponsor', 'location', 'country', 'cc', 'lat', 'lon', 'isp', 'ip', 'download_mbps', 'upload_mbps', 'ping_ms', 'jitter_ms', 'comments']
        new_row = [
            self.latest_results['timestamp'],
            self.latest_results['server'],
            self.latest_results['sponsor'],
            self.latest_results['location'],
            self.latest_results['country'],
            self.latest_results['cc'],
            self.latest_results['lat'],
            self.latest_results['lon'],
            self.latest_results['isp'],
            self.latest_results['ip'],
            self.latest_results['download_mbps'],
            self.latest_results['upload_mbps'],
            self.latest_results['ping_ms'],
            self.latest_results['jitter_ms'],
            self.latest_results['comments']
        ]

        # Read existing rows
        existing = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    existing = list(reader)
            except Exception:
                existing = []

        # Write header and new row, then existing rows (so newest at top)
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(new_row)
                # if existing has header, skip it
                if existing and existing[0] == header:
                    for row in existing[1:]:
                        writer.writerow(row)
                else:
                    for row in existing:
                        writer.writerow(row)

            self.log_output(f"Logged results to {filename}")
        except Exception as e:
            self.log_output(f"Failed to write log: {e}")


def main():
    root = tk.Tk()
    app = SpeedTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
