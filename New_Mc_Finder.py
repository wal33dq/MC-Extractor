import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, Canvas
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import csv
import re
import time
import threading
import os
import random
from datetime import datetime
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HeadlessScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FMCSA Data Scraper")
        self.root.geometry("950x700")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f2f5")
        
        # Variables
        self.is_running = False
        self.driver = None
        self.csv_filename = "extracted_numbers.csv"
        self.status_updates = []
        self.data_points = []
        
        # Create GUI elements
        self.create_widgets()
        
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
    def create_widgets(self):
        # Custom title bar
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=50)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(
            title_frame, 
            text="FMCSA Register Data Extractor", 
            font=("Arial", 16, "bold"), 
            fg="white", 
            bg="#2c3e50"
        ).grid(row=0, column=0, padx=10, sticky="w")
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        main_frame.grid(row=1, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Left panel - Controls
        control_frame = tk.LabelFrame(
            main_frame, 
            text="Scraper Controls", 
            font=("Arial", 10, "bold"),
            bg="#f0f2f5",
            padx=15,
            pady=15
        )
        control_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # Status summary
        self.summary_frame = tk.Frame(control_frame, bg="#e3f2fd", bd=1, relief="solid")
        self.summary_frame.pack(fill="x", pady=5)
        
        tk.Label(
            self.summary_frame, 
            text="CURRENT STATUS:", 
            font=("Arial", 9, "bold"), 
            bg="#e3f2fd"
        ).pack(side="left", padx=5, pady=5)
        
        self.status_label = tk.Label(
            self.summary_frame, 
            text="Ready to start", 
            font=("Arial", 9), 
            fg="#2c3e50",
            bg="#e3f2fd"
        )
        self.status_label.pack(side="left", padx=5, pady=5)
        
        # Buttons
        button_frame = tk.Frame(control_frame, bg="#f0f2f5")
        button_frame.pack(fill="x", pady=10)
        
        self.start_button = tk.Button(
            button_frame, 
            text="Start Scraping", 
            command=self.start_scraping_thread,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat"
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = tk.Button(
            button_frame, 
            text="Stop Scraping", 
            command=self.stop_scraping,
            state=tk.DISABLED,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat"
        )
        self.stop_button.pack(side="left", padx=5)
        
        self.open_button = tk.Button(
            button_frame, 
            text="Open CSV", 
            command=self.open_csv,
            state=tk.DISABLED,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15,
            relief="flat"
        )
        self.open_button.pack(side="left", padx=5)
        
        # Progress
        progress_frame = tk.Frame(control_frame, bg="#f0f2f5")
        progress_frame.pack(fill="x", pady=10)
        
        tk.Label(
            progress_frame, 
            text="Progress:", 
            font=("Arial", 9, "bold"), 
            bg="#f0f2f5"
        ).pack(anchor="w")
        
        self.progress = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=400, 
            mode='determinate'
        )
        self.progress.pack(fill="x", pady=5)
        
        # Stats frame
        stats_frame = tk.Frame(control_frame, bg="#f0f2f5")
        stats_frame.pack(fill="x", pady=10)
        
        tk.Label(
            stats_frame, 
            text="Statistics:", 
            font=("Arial", 9, "bold"), 
            bg="#f0f2f5"
        ).pack(anchor="w")
        
        stats_subframe = tk.Frame(stats_frame, bg="#f0f2f5")
        stats_subframe.pack(fill="x", pady=5)
        
        tk.Label(
            stats_subframe, 
            text="Rows Processed:", 
            font=("Arial", 8), 
            bg="#f0f2f5"
        ).grid(row=0, column=0, sticky="w")
        
        self.rows_processed = tk.Label(
            stats_subframe, 
            text="0", 
            font=("Arial", 8, "bold"), 
            bg="#f0f2f5"
        )
        self.rows_processed.grid(row=0, column=1, sticky="w", padx=10)
        
        tk.Label(
            stats_subframe, 
            text="Numbers Found:", 
            font=("Arial", 8), 
            bg="#f0f2f5"
        ).grid(row=1, column=0, sticky="w")
        
        self.numbers_found = tk.Label(
            stats_subframe, 
            text="0", 
            font=("Arial", 8, "bold"), 
            bg="#f0f2f5"
        )
        self.numbers_found.grid(row=1, column=1, sticky="w", padx=10)
        
        tk.Label(
            stats_subframe, 
            text="Time Elapsed:", 
            font=("Arial", 8), 
            bg="#f0f2f5"
        ).grid(row=2, column=0, sticky="w")
        
        self.time_elapsed = tk.Label(
            stats_subframe, 
            text="0s", 
            font=("Arial", 8, "bold"), 
            bg="#f0f2f5"
        )
        self.time_elapsed.grid(row=2, column=1, sticky="w", padx=10)
        
        # Right panel - Logs and Visualization
        right_frame = tk.Frame(main_frame, bg="#f0f2f5")
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # Log Frame
        log_frame = tk.LabelFrame(
            right_frame, 
            text="Log Messages", 
            font=("Arial", 10, "bold"),
            bg="#f0f2f5",
            padx=15,
            pady=15
        )
        log_frame.pack(fill="both", expand=True)
        
        self.log_area = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=60, 
            height=15,
            font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True)
        self.log_area.configure(state='disabled')
        
        # Visualization Frame
        viz_frame = tk.LabelFrame(
            right_frame, 
            text="Data Visualization", 
            font=("Arial", 10, "bold"),
            bg="#f0f2f5",
            padx=15,
            pady=15
        )
        viz_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Create a placeholder for the visualization
        self.viz_canvas = Canvas(viz_frame, bg="white", height=150)
        self.viz_canvas.pack(fill="both", expand=True)
        
        # Draw initial placeholder
        self.draw_placeholder()
        
        # Status Bar
        status_bar = tk.Frame(self.root, bg="#2c3e50", height=25)
        status_bar.grid(row=2, column=0, sticky="ew", columnspan=2)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to start scraping")
        tk.Label(
            status_bar, 
            textvariable=self.status_var, 
            bg="#2c3e50",
            fg="white",
            font=("Arial", 9)
        ).pack(side="left", padx=10)
        
        # Set column weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        
    def draw_placeholder(self):
        self.viz_canvas.delete("all")
        self.viz_canvas.create_text(
            150, 75,
            text="Data visualization will appear here after scraping",
            fill="#7f8c8d",
            font=("Arial", 10, "italic")
        )
        
    def draw_data_viz(self, data):
        self.viz_canvas.delete("all")
        
        if not data:
            self.draw_placeholder()
            return
            
        # Create a figure for the bar chart
        fig = plt.Figure(figsize=(5, 2), dpi=80)
        ax = fig.add_subplot(111)
        
        # Count first digits for Benford's Law visualization
        first_digits = [int(str(num)[0]) for num in data if num]
        digit_counts = {i: first_digits.count(i) for i in range(1, 10)}
        
        # Create bar chart
        digits = list(digit_counts.keys())
        counts = [digit_counts.get(d, 0) for d in digits]
        
        ax.bar(digits, counts, color='#3498db')
        ax.set_title('First Digit Distribution', fontsize=10)
        ax.set_xlabel('Digit')
        ax.set_ylabel('Count')
        ax.set_xticks(digits)
        
        # Embed in Tkinter
        chart = FigureCanvasTkAgg(fig, master=self.viz_canvas)
        chart.draw()
        chart.get_tk_widget().pack(fill="both", expand=True)
        
    def log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)
        self.status_updates.append(message)
        self.root.update_idletasks()
        
    def update_status(self, message):
        self.status_var.set(message)
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
    def update_progress(self, value, max_value=None):
        if max_value:
            self.progress['maximum'] = max_value
        self.progress['value'] = value
        self.root.update_idletasks()
        
    def update_stats(self, processed, found, elapsed):
        self.rows_processed.config(text=str(processed))
        self.numbers_found.config(text=str(found))
        self.time_elapsed.config(text=f"{elapsed:.1f}s")
        self.root.update_idletasks()
        
    def start_scraping_thread(self):
        if self.is_running:
            return
            
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.open_button.config(state=tk.DISABLED)
        self.log_area.configure(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.configure(state='disabled')
        self.update_progress(0)
        self.status_updates = []
        self.data_points = []
        
        # Start scraping in a separate thread
        threading.Thread(target=self.run_scraper, daemon=True).start()
        
    def stop_scraping(self):
        self.is_running = False
        self.log_message("Process stop requested...")
        self.update_status("Stopping...")
        
    def run_scraper(self):
        start_time = time.time()
        processed_count = 0
        found_count = 0
        
        try:
            # Configure headless browser
            self.log_message("Starting headless browser...")
            self.update_status("Initializing browser...")
            
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            self.log_message("Navigating to FMCSA website...")
            self.update_status("Loading page...")
            self.driver.get("https://li-public.fmcsa.dot.gov/LIVIEW/pkg_html.prc_limain")
            self.log_message("Page loaded successfully")
            
            # Wait for and select dropdown
            self.log_message("Selecting 'FMCSA Register' option...")
            self.update_status("Selecting option...")
            dropdown = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "menu"))
            )
            Select(dropdown).select_by_value("FED_REG")
            self.log_message('Selected "FMCSA Register" option')
            
            # Click first submit button
            self.log_message("Clicking first submit button...")
            self.update_status("Processing step 1/3...")
            button1_xpath = "/html/body/font/table[1]/tbody/tr/td/div/div/table/tbody/tr/td/form/input[1]"
            submit_button = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, button1_xpath))
            )
            submit_button.click()
            self.log_message("Clicked the first submit button")
            
            # Wait for page load
            time.sleep(2)
            
            # Click HTML Detail button
            self.log_message('Clicking "HTML Detail" button...')
            self.update_status("Processing step 2/3...")
            html_detail_xpath = "/html/body/font/font/table/tbody/tr[2]/td[2]/form/input[3]"
            html_detail_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, html_detail_xpath))
            )
            html_detail_button.click()
            self.log_message('Clicked "HTML Detail" button')
            
            # Wait for table to load
            self.log_message("Waiting for data table to load...")
            self.update_status("Processing step 3/3...")
            table_xpath = "/html/body/font/table[8]"
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, table_xpath))
            )
            self.log_message("Target table loaded")
            
            # Get table rows
            rows = self.driver.find_elements(By.XPATH, f"{table_xpath}/tbody/tr[position()>1]")
            row_count = len(rows)
            self.log_message(f"Found {row_count} rows in the table")
            self.update_status(f"Processing {row_count} rows...")
            
            # Extract numbers
            numbers = []
            self.update_progress(0, row_count)
            self.log_message("Extracting numbers from table...")
            
            for i, row in enumerate(rows, 1):
                if not self.is_running:
                    self.log_message("Process stopped by user")
                    break
                    
                try:
                    th_element = row.find_element(By.XPATH, "./th")
                    raw_text = th_element.text.strip()
                    
                    # Extract number
                    number_match = re.search(r'\d{5,}', raw_text)
                    
                    if number_match:
                        extracted_number = number_match.group(0)
                        numbers.append(extracted_number)
                        self.data_points.append(extracted_number)
                        found_count += 1
                        self.log_message(f"Row {i}: Extracted number {extracted_number}")
                    else:
                        self.log_message(f"Row {i}: No number found in '{raw_text}'")
                        
                except Exception as e:
                    self.log_message(f"Error processing row {i}: {str(e)}")
                
                processed_count = i
                self.update_progress(i)
                self.update_stats(processed_count, found_count, time.time() - start_time)
                self.update_status(f"Processed {i}/{row_count} rows")
                
                # Throttle processing to avoid overwhelming the system
                time.sleep(0.05)
            
            # Save to CSV
            if numbers:
                self.log_message(f"Saving {len(numbers)} numbers to CSV...")
                self.update_status("Saving results...")
                
                with open(self.csv_filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['MC-Number'])
                    for number in numbers:
                        writer.writerow([number])
                
                self.log_message(f"Saved results to {self.csv_filename}")
                self.open_button.config(state=tk.NORMAL)
                self.update_status(f"Completed! {len(numbers)} numbers saved")
                self.draw_data_viz(numbers)
            else:
                self.log_message("No numbers extracted - CSV file not created")
                self.update_status("Completed! No numbers found")
                
        except WebDriverException as e:
            self.log_message(f"Browser error: {str(e)}")
            self.update_status("Error occurred - check logs")
            if "This site can't be reached" in str(e):
                self.log_message("Possible network error or site unavailable")
        except Exception as e:
            self.log_message(f"An error occurred: {str(e)}")
            self.update_status("Error occurred - check logs")
            # Take screenshot
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_name = f"error_screenshot_{timestamp}.png"
                self.driver.save_screenshot(screenshot_name)
                self.log_message(f"Screenshot saved as {screenshot_name}")
            except:
                self.log_message("Could not save screenshot")
        finally:
            # Clean up
            self.log_message("Cleaning up...")
            self.update_status("Closing browser...")
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
            self.log_message("Browser closed")
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_progress(0)
            self.update_status("Ready to start new scraping")
            self.update_stats(processed_count, found_count, time.time() - start_time)
            
    def open_csv(self):
        try:
            if os.path.exists(self.csv_filename):
                os.startfile(self.csv_filename)
            else:
                messagebox.showwarning("File Not Found", "The CSV file could not be found")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HeadlessScraperApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()