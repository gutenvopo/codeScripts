"""
Speed Test GUI Application v1.04
================================================================================
CHANGELOG - Version 1.04
================================================================================
V1.04 CHANGES:
1. Enhanced error handling for all HTTP error codes (not just 403)
2. Added extract_error_code() method to parse HTTP status codes from exceptions
3. Improved error reporting to include detailed server information:
   - Server sponsor/name
   - Location and country codes
   - Coordinates (latitude/longitude)
   - Full error details
4. Server details now displayed when ANY error occurs (not just 403)
5. Better user feedback during server retry operations
6. TODO: Verify correct CSV output/update flow; investigate why `internet_speed_log.csv` is not updating.

PREVIOUS (V1.03) CHANGES:
1. FIRST RELEASE BUILD - Production-ready version
2. Packaged as standalone executable with digital signature
3. Includes comprehensive speed testing with 403 error retry logic
4. Full CSV logging and comment support for test results

PREVIOUS (V1.02) FEATURES:
1. Added automatic retry mechanism for 403 Forbidden errors from servers
2. Displays which server caused the 403 error before retrying
3. Retries up to 3 times to find an alternate working server
4. Logs all 403 errors with server sponsor and location details

PREVIOUS (V1.01) FEATURES:
1. Added purple "Log" button to save test results to CSV file
2. Implemented CSV logging to 'internet_speed_log.csv' with full data export
3. CSV includes columns: timestamp, server, sponsor, location, country, cc, lat, 
   lon, isp, ip, download_mbps, upload_mbps, ping_ms, jitter_ms, comments
4. Newest test results are prepended to CSV (top row always latest)
5. Added comment input field with label "Comments, Keep it Short"
6. Comment input box spans full horizontal width of window
7. Log button disabled until test completes; enabled after results available
8. Window size increased to 900x620 to accommodate UI elements
9. Comments from input field are automatically saved with each log entry

WHAT THIS CODE DOES
1. Provides a desktop Tkinter GUI to run internet speed tests using the `speedtest` library.
2. Displays real-time progress and detailed output in a scrollable text panel.
3. Collects and shows key metrics: download speed, upload speed, ping, and jitter.
4. Captures server and network details (sponsor, location, country, coordinates, ISP, and IP).
5. Handles server-related HTTP errors with retry feedback and clearer diagnostics.
6. Allows users to add short comments and log test results to `internet_speed_log.csv`.
7. Writes CSV output with the newest result at the top so recent tests are easy to find.

================================================================================
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
from datetime import datetime
import socket
import csv
import os
import sys

# Fix for PyInstaller GUI mode - redirect stdout/stderr before importing speedtest
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

import speedtest


class SpeedTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Application v1.04")
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

        # Stop button (different color)
        self.stop_button = tk.Button(
            self.button_frame,
            text="Stop",
            command=self.stop_test,
            width=15,
            height=2,
            bg="#FF9800",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Log button (different color)
        self.log_button = tk.Button(
            self.button_frame,
            text="Save To Log",
            command=self.save_log,
            width=15,
            height=2,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 10, "bold"),
            disabledforeground="grey"
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
        self.stop_requested = False
        self.latest_results = None

    def extract_error_code(self, error_string):
        """Extract HTTP error code from error message"""
        import re
        # Look for patterns like '403', 'HTTP 403', 'Status: 403'
        match = re.search(r'(\d{3})', error_string)
        if match:
            return match.group(1)
        return 'UNKNOWN'

    def log_output(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update()

    def stop_test(self):
        """Stop the running test"""
        if not self.test_running:
            self.output_text.delete(1.0, tk.END)
            self.log_output("No tests are running")
            self.log_output("")
            self.log_output("Click 'Start Test' to begin speed testing...\n")
            return
        
        self.stop_requested = True
        self.log_output("\n[INFO] User stopped the tests")
        self.log_output("")
        self.log_output("Click 'Start Test' to begin speed testing...\n")

    def draw_diagonal_lines(self):
        """Draw diagonal lines on canvas for disabled state"""
        self.log_button_canvas.delete("all")
        width = 100
        height = 48
        spacing = width // 6
        for i in range(8):
            x_start = i * spacing - height
            self.log_button_canvas.create_line(
                x_start, 0,
                x_start + height, height,
                fill="grey",
                width=2
            )

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

            # Retry logic for 403 errors
            max_retries = 3
            retry_count = 0
            best_server = None
            
            while retry_count < max_retries:
                if self.stop_requested:
                    raise Exception("Test stopped by user")
                try:
                    self.log_output("Getting best server...")
                    best_server = st.get_best_server()
                    break  # Success, exit retry loop
                except Exception as e:
                    error_code = self.extract_error_code(str(e))
                    if error_code == '403' or '403' in str(e):
                        retry_count += 1
                        self.log_output(f"\n[ERROR] HTTP {error_code} Forbidden Error encountered")
                        self.log_output(f"Details: {str(e)}")
                        if retry_count < max_retries:
                            self.log_output(f"Retrying server selection... (Attempt {retry_count}/{max_retries})")
                        else:
                            self.log_output(f"Max retries ({max_retries}) reached. Aborting test.")
                            raise
                    else:
                        raise

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

            # Download speed test with 403 error handling
            self.log_output("\n" + "=" * 60)
            self.log_output("DOWNLOAD SPEED TEST")
            self.log_output("=" * 60)
            self.log_output("Testing download speed...")
            if self.stop_requested:
                raise Exception("Test stopped by user")
            try:
                st.download()
                download_speed = st.results.download / 1_000_000  # Convert to Mbps
                self.log_output(f"Download Speed: {download_speed:.2f} Mbps")
            except Exception as e:
                error_code = self.extract_error_code(str(e))
                if error_code == '403' or '403' in str(e):
                    self.log_output(f"\n[ERROR] HTTP {error_code} Forbidden during download")
                    self.log_output(f"Server Details:")
                    self.log_output(f"  - Sponsor: {best_server.get('sponsor', 'Unknown')}")
                    self.log_output(f"  - Location: {best_server.get('name', 'N/A')}, {best_server.get('country', 'N/A')}")
                    self.log_output(f"  - Country Code: {best_server.get('cc', 'N/A')}")
                    self.log_output(f"  - Coordinates: ({best_server.get('lat', 'N/A')}, {best_server.get('lon', 'N/A')})")
                    self.log_output(f"Error Details: {str(e)}")
                    self.log_output("Attempting to select alternate server...")
                    st.get_servers()
                    best_server = st.get_best_server()
                    self.log_output(f"Retrying with alternate server: {best_server.get('sponsor', 'Unknown')} ({best_server.get('name', 'N/A')})")
                    st.download()
                    download_speed = st.results.download / 1_000_000
                    self.log_output(f"Download Speed: {download_speed:.2f} Mbps")
                else:
                    error_code = self.extract_error_code(str(e))
                    self.log_output(f"\n[ERROR] HTTP {error_code} error during download")
                    self.log_output(f"Server: {best_server.get('sponsor', 'Unknown')} ({best_server.get('name', 'N/A')})")
                    self.log_output(f"Location: {best_server.get('country', 'N/A')}")
                    self.log_output(f"Error Details: {str(e)}")
                    raise

            # Upload speed test with 403 error handling
            self.log_output("\n" + "=" * 60)
            self.log_output("UPLOAD SPEED TEST")
            self.log_output("=" * 60)
            self.log_output("Testing upload speed...")
            if self.stop_requested:
                raise Exception("Test stopped by user")
            try:
                st.upload()
                upload_speed = st.results.upload / 1_000_000  # Convert to Mbps
                self.log_output(f"Upload Speed: {upload_speed:.2f} Mbps")
            except Exception as e:
                error_code = self.extract_error_code(str(e))
                if error_code == '403' or '403' in str(e):
                    self.log_output(f"\n[ERROR] HTTP {error_code} Forbidden during upload")
                    self.log_output(f"Server Details:")
                    self.log_output(f"  - Sponsor: {best_server.get('sponsor', 'Unknown')}")
                    self.log_output(f"  - Location: {best_server.get('name', 'N/A')}, {best_server.get('country', 'N/A')}")
                    self.log_output(f"  - Country Code: {best_server.get('cc', 'N/A')}")
                    self.log_output(f"  - Coordinates: ({best_server.get('lat', 'N/A')}, {best_server.get('lon', 'N/A')})")
                    self.log_output(f"Error Details: {str(e)}")
                    self.log_output("Attempting to select alternate server...")
                    st.get_servers()
                    best_server = st.get_best_server()
                    self.log_output(f"Retrying with alternate server: {best_server.get('sponsor', 'Unknown')} ({best_server.get('name', 'N/A')})")
                    st.upload()
                    upload_speed = st.results.upload / 1_000_000
                    self.log_output(f"Upload Speed: {upload_speed:.2f} Mbps")
                else:
                    error_code = self.extract_error_code(str(e))
                    self.log_output(f"\n[ERROR] HTTP {error_code} error during upload")
                    self.log_output(f"Server: {best_server.get('sponsor', 'Unknown')} ({best_server.get('name', 'N/A')})")
                    self.log_output(f"Location: {best_server.get('country', 'N/A')}")
                    self.log_output(f"Error Details: {str(e)}")
                    raise

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
            if "Test stopped by user" not in str(e):
                self.log_output("Please check your internet connection and try again.")

        finally:
            self.test_running = False
            self.stop_requested = False
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
