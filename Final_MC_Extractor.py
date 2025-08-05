import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import csv
import threading
import re
import os

class SmartMCNumberExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MC Number Information Extractor - Smart")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)  # Set minimum window size
        
        # Variables
        self.start_mc = tk.StringVar(value="1706527")
        self.end_mc = tk.StringVar(value="1706530")
        self.csv_file = tk.StringVar(value="mc_records.csv")
        self.bulk_file = tk.StringVar(value="")
        self.running = False
        self.driver = None
        self.stop_requested = False
        self.mc_list = []
        self.use_bulk = tk.BooleanVar(value=False)
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for different modes
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Range Mode Tab
        range_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(range_frame, text="Range Mode")
        
        # Bulk Upload Tab
        bulk_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(bulk_frame, text="Bulk Upload")
        
        # Create widgets for range mode
        self.create_range_widgets(range_frame)
        
        # Create widgets for bulk upload
        self.create_bulk_widgets(bulk_frame)
        
        # Create common widgets
        self.create_common_widgets(main_container)
        
    def create_range_widgets(self, parent):
        # Input fields for range mode
        ttk.Label(parent, text="Start MC Number:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=self.start_mc, width=15).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(parent, text="End MC Number:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(parent, textvariable=self.end_mc, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
    def create_bulk_widgets(self, parent):
        # File selection
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(file_frame, text="MC Number File:").pack(side=tk.LEFT, padx=(0, 5))
        entry = ttk.Entry(file_frame, textvariable=self.bulk_file, width=40, state='readonly')
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Browse", command=self.browse_bulk_file).pack(side=tk.LEFT, padx=(5, 0))
        
        # Create sample file button
        ttk.Button(parent, text="Create Sample File", command=self.create_sample_file).pack(pady=5)
        
        # Instructions
        instructions = tk.Label(parent, text="Create a text file with one MC number per line", 
                               font=("Arial", 9), fg="gray")
        instructions.pack(pady=5)
        
        # Preview area
        preview_frame = ttk.LabelFrame(parent, text="File Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=8, state='disabled')
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_common_widgets(self, parent):
        # Create a frame for common elements
        common_frame = ttk.Frame(parent)
        common_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output CSV file
        csv_frame = ttk.Frame(common_frame)
        csv_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(csv_frame, text="Output CSV File:").pack(side=tk.LEFT, padx=(0, 5))
        entry = ttk.Entry(csv_frame, textvariable=self.csv_file, width=40)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(csv_frame, text="Browse", command=self.browse_csv_file).pack(side=tk.LEFT)
        
        # Progress bar
        self.progress = ttk.Progressbar(common_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(common_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Buttons
        button_frame = ttk.Frame(common_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Start Extraction", command=self.start_extraction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Stop", command=self.stop_extraction).pack(side=tk.LEFT, padx=5)
        
        # Results table
        self.create_results_table(common_frame)
    
    def create_results_table(self, parent):
        # Results table with additional columns
        tree_frame = ttk.LabelFrame(parent, text="Results")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Configure grid weights for expansion
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, 
                                 columns=("MC Number", "Company Name", "Address", "Email", "Phone", "Status"), 
                                 show="headings", 
                                 height=10)
        
        # Setup columns
        columns = [
            ("MC Number", 100),
            ("Company Name", 200),
            ("Address", 250),
            ("Email", 200),
            ("Phone", 150),
            ("Status", 100)
        ]
        
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=50)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout with proper expansion
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
    def browse_csv_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=self.csv_file.get()
        )
        if filename:
            self.csv_file.set(filename)
    
    def browse_bulk_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if filename:
            self.bulk_file.set(filename)
            self.preview_file(filename)
    
    def preview_file(self, filename):
        try:
            self.preview_text.config(state='normal')
            self.preview_text.delete(1.0, tk.END)
            
            with open(filename, 'r') as file:
                lines = file.readlines()
                for line in lines[:50]:  # Show first 50 lines
                    self.preview_text.insert(tk.END, line)
                
                if len(lines) > 50:
                    self.preview_text.insert(tk.END, f"\n... and {len(lines)-50} more lines ...")
            
            self.preview_text.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {str(e)}")
    
    def create_sample_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="mc_numbers_sample.txt"
        )
        if filename:
            try:
                with open(filename, 'w') as file:
                    file.write("1706527\n1706528\n1706529\n1706530\n1706531\n")
                messagebox.showinfo("Sample File Created", f"Sample file created at:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not create sample file: {str(e)}")
    
    def start_extraction(self):
        if self.running:
            return
            
        try:
            # Get current tab from notebook
            current_tab = self.notebook.select()
            tab_text = self.notebook.tab(current_tab, "text")
            
            if tab_text == "Range Mode":
                start = int(self.start_mc.get())
                end = int(self.end_mc.get())
                
                if start > end:
                    messagebox.showerror("Error", "Start MC number must be less than or equal to End MC number")
                    return
                    
                self.mc_list = list(range(start, end + 1))
            else:  # Bulk Upload mode
                bulk_file = self.bulk_file.get()
                if not bulk_file:
                    messagebox.showerror("Error", "Please select a bulk MC numbers file")
                    return
                    
                try:
                    with open(bulk_file, 'r') as file:
                        self.mc_list = []
                        for line in file:
                            # Clean and validate MC numbers
                            mc = line.strip()
                            if mc and mc.isdigit():
                                self.mc_list.append(int(mc))
                        
                        if not self.mc_list:
                            messagebox.showerror("Error", "No valid MC numbers found in the file")
                            return
                except Exception as e:
                    messagebox.showerror("Error", f"Could not read bulk file: {str(e)}")
                    return
            
            # Prepare CSV file
            with open(self.csv_file.get(), mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["MC Number", "Company Name", "Address", "Email", "Phone", "Status"])
                
            # Clear previous results
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            # Reset stop flag
            self.stop_requested = False
                
            # Start extraction in a separate thread
            self.running = True
            self.status_var.set("Starting extraction...")
            
            # Configure Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            threading.Thread(target=self.run_smart_extraction, daemon=True).start()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid MC numbers")
    
    def run_smart_extraction(self):
        try:
            total = len(self.mc_list)
            current = 0
            
            for mc in self.mc_list:
                if self.stop_requested:
                    self.status_var.set("Stopped by user")
                    break
                    
                self.status_var.set(f"Processing MC Number: {mc} ({current+1}/{total})")
                self.root.update()
                
                # Get all information including company name and address
                result = self.smart_process_mc_number(mc)
                company_name = result["company_name"]
                address = result["address"]
                email = result["email"]
                phone = result["phone"]
                
                # Enhanced status determination
                if ("Not a CARRIER" in email or 
                    "Not ACTIVE" in email or
                    "Not AUTHORIZED FOR Property" in email or
                    "Not General Freight" in email or  # NEW FILTER CONDITION
                    "X Check Failed" in email or  # NEW FILTER CONDITION
                    "No SMS Link Found" in email or
                    "Address without Valid Postal Code" in email or  # UPDATED FILTER CONDITION
                    "Canadian Address Not Allowed" in email):  # NEW FILTER CONDITION
                    status = "Failed"
                else:
                    # Check if we have company info
                    has_company_info = (
                        company_name != "Company Name Not Found" and 
                        company_name != "Not Available" and
                        address != "Address Not Found" and
                        address != "Not Available"
                    )
                    
                    # Check contact info
                    has_email = "@" in email and "Email Not Found" not in email
                    has_phone = re.search(r'\d', phone) and "Phone Not Found" not in phone
                    
                    if has_email and has_phone:
                        status = "Success"
                    elif has_email or has_phone:
                        status = "Partial Success"
                    elif has_company_info:
                        status = "Manual Check"
                    else:
                        status = "Manual Check"
                
                # Create display-friendly address for GUI (replace newlines with commas)
                display_address = address.replace("\n", ", ") if "\n" in address else address
                
                # Always show in GUI
                self.tree.insert("", tk.END, values=(mc, company_name, display_address, email, phone, status))
                self.tree.see(self.tree.get_children()[-1])
                
                # Save all records except "Failed" to CSV
                if status != "Failed":
                    with open(self.csv_file.get(), mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        # Replace newlines with spaces for CSV to keep address in one line
                        csv_address = address.replace('\n', ' ')
                        writer.writerow([mc, company_name, csv_address, email, phone, status])
                
                current += 1
                self.progress['value'] = (current / total) * 100
                self.root.update()
                
            if not self.stop_requested:
                self.status_var.set(f"Extraction completed! Processed {current} MC numbers")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
            
        finally:
            self.running = False
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def smart_process_mc_number(self, mc_number):
        try:
            # Initialize all values
            result = {
                "company_name": "Not Available",
                "address": "Not Available",
                "email": "Not Available",
                "phone": "Not Available"
            }
            
            # STEP 1: Initial search
            self.driver.get("https://safer.fmcsa.dot.gov/CompanySnapshot.aspx")
            
            mc_radio = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "2"))
            )
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "2"))
            ).click()
            
            text_input = WebDriverWait(self.driver, 10).until(
                lambda d: d.find_element(By.ID, "4") if d.find_element(By.ID, "4").is_displayed() else False
            )
            text_input.clear()
            text_input.send_keys(str(mc_number))
            
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='SUBMIT'][value='Search']"))
            )
            search_button.click()

            # STEP 2: Check for CARRIER status
            try:
                carrier_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/p/table/tbody/tr[2]/td/table/tbody/tr[2]/td/center[1]/table/tbody/tr[3]/td"))
                )
                carrier_text = carrier_element.text.strip()
                
                if "CARRIER" not in carrier_text:
                    result["email"] = "Not a CARRIER"
                    result["phone"] = "Not a CARRIER"
                    return result
            except TimeoutException:
                result["email"] = "No SMS Link Found"
                result["phone"] = "No SMS Link Found"
                return result

            # STEP 3: Check for ACTIVE status
            try:
                active_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/p/table/tbody/tr[2]/td/table/tbody/tr[2]/td/center[1]/table/tbody/tr[4]/td[1]"))
                )
                active_text = active_element.text.strip()
                
                if "ACTIVE" not in active_text:
                    result["email"] = "Not ACTIVE"
                    result["phone"] = "Not ACTIVE"
                    return result
            except TimeoutException:
                result["email"] = "Status Check Failed"
                result["phone"] = "Status Check Failed"
                return result

            # STEP 4: Check for AUTHORIZED FOR Property status
            try:
                auth_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/p/table/tbody/tr[2]/td/table/tbody/tr[2]/td/center[1]/table/tbody/tr[8]/td"))
                )
                auth_text = auth_element.text.strip()
                
                if "AUTHORIZED FOR Property" not in auth_text:
                    result["email"] = "Not AUTHORIZED FOR Property"
                    result["phone"] = "Not AUTHORIZED FOR Property"
                    return result
            except TimeoutException:
                result["email"] = "Authorization Check Failed"
                result["phone"] = "Authorization Check Failed"
                return result
                
            # ====== NEW FILTER: X CHECK ======
            # STEP 5: Check for X status
            try:
                x_element = WebDriverWait(self.driver, 5).until(
                    # Replace with your actual XPath for "X"
                    EC.presence_of_element_located((By.XPATH, "/html/body/p/table/tbody/tr[2]/td/table/tbody/tr[2]/td/center[1]/table/tbody/tr[24]/td/table/tbody/tr[2]/td[1]/table/tbody/tr[2]/td[1]"))
                )
                x_text = x_element.text.strip()
                
                if "X" not in x_text:
                    result["email"] = "Not General Freight"
                    result["phone"] = "Not General Freight"
                    return result
            except TimeoutException:
                result["email"] = "X Check Failed"
                result["phone"] = "X Check Failed"
                return result
            # ====== END NEW FILTER ======
            
            # ====== ENHANCED ADDRESS VALIDATION ======
            # STEP 5.5: Check for valid postal code pattern in address
            try:
                address_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "physicaladdressvalue"))
                )
                address_text = address_element.text.strip()
                
                # Normalize address - replace non-breaking spaces and trim
                address_text = address_text.replace(u'\xa0', ' ').strip()
                
                # Extract last part (postal code area)
                last_part = address_text.split(',')[-1].strip()
                
                # Check for valid patterns in the last part
                # US ZIP pattern (5 digits or 5-4 format)
                us_zip_pattern = r'\d{5}(-\d{4})?$'
                # Canadian postal code pattern (A1A 1A1 or A1A1A1) - case insensitive
                canada_pattern = r'[A-Za-z]\d[A-Za-z][\s-]?\d[A-Za-z]\d$'
                
                # NEW: Fail if Canadian pattern is detected
                if re.search(canada_pattern, last_part, re.IGNORECASE):
                    result["email"] = "Canadian Address Not Allowed"
                    result["phone"] = "Canadian Address Not Allowed"
                    return result
                
                # Original validation logic
                if (not re.search(us_zip_pattern, last_part) and
                    not re.search(r'\d', last_part)):
                    result["email"] = "Address without Valid Postal Code"
                    result["phone"] = "Address without Valid Postal Code"
                    return result
                    
            except TimeoutException:
                result["email"] = "Address Not Found"
                result["phone"] = "Address Not Found"
                return result
            # ====== END ENHANCED VALIDATION ======

            # STEP 6: Click SMS Results link
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'safer_xfr')]"))
                )
                
                sms_link = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'safer_xfr')]"))
                )
                sms_link.click()
                
                if len(self.driver.window_handles) > 1:
                    self.driver.switch_to.window(self.driver.window_handles[1])
                
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                result["email"] = "No SMS Link Found"
                result["phone"] = "No SMS Link Found"
                return result

            # STEP 7: Try additional link
            try:
                additional_link = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/article/div[2]/div[2]/section/a[1]"))
                )
                additional_link.click()
                
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                pass

            # STEP 8: Extract all data
            result["company_name"] = self.extract_company_name()
            result["address"] = self.extract_address()
            result["email"] = self.extract_email()
            result["phone"] = self.extract_phone()
            
            self.cleanup_tabs()
            
            return result
                
        except Exception as e:
            self.driver.save_screenshot(f"error_{mc_number}.png")
            error_msg = f"Error: {str(e)}"
            return {
                "company_name": error_msg,
                "address": error_msg,
                "email": error_msg,
                "phone": error_msg
            }
    
    def extract_company_name(self):
        try:
            company_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='regBox']/ul[1]/li[1]/span"))
            )
            return company_element.text.strip()
        except TimeoutException:
            return "Company Name Not Found"
        except Exception:
            return "Company Name Not Found"
    
    def extract_address(self):
        try:
            # Find the address container element
            address_container = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='regBox']/ul[1]/li[4]"))
            )
            
            # Extract all text content including line breaks
            address_text = address_container.text.strip()
            
            # Remove "Address:" prefix if it exists
            if address_text.startswith("Address:"):
                address_text = address_text[8:].strip()
                
            return address_text
        except TimeoutException:
            return "Address Not Found"
        except Exception:
            return "Address Not Found"
    
    def extract_email(self):
        try:
            email = self.find_email_fast()
            if email:
                return email
            
            email_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(., '@') and string-length(.) < 50]"))
            )
            return email_element.text.strip()
        except TimeoutException:
            return "Email Not Found"
        except Exception:
            return "Email Not Found"
    
    def extract_phone(self):
        try:
            phone_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='regBox']/ul[1]/li[5]/span"))
            )
            phone_text = phone_element.text.strip()
            phone_text = re.sub(r'[^\d()\- ]', '', phone_text)
            return phone_text if phone_text else "Phone Not Found"
        except TimeoutException:
            return "Phone Not Found"
        except Exception:
            return "Phone Not Found"
    
    def find_email_fast(self):
        try:
            for xpath in [
                "//a[contains(@href, 'mailto:')]",
                "//div[contains(@class, 'email')]",
                "//span[contains(@class, 'email')]",
                "//td[contains(., '@')]"
            ]:
                try:
                    element = self.driver.find_element(By.XPATH, xpath)
                    if "@" in element.text:
                        return element.text.strip()
                except NoSuchElementException:
                    continue
        except:
            pass
        return None
    
    def cleanup_tabs(self):
        try:
            while len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.close()
            if len(self.driver.window_handles) > 0:
                self.driver.switch_to.window(self.driver.window_handles[0])
        except:
            pass
    
    def stop_extraction(self):
        if self.running:
            self.stop_requested = True
            self.status_var.set("Stopping... Please wait")
    
    def on_closing(self):
        if self.running:
            if messagebox.askokcancel("Quit", "Extraction is still running. Are you sure you want to quit?"):
                self.stop_requested = True
                if self.driver:
                    self.driver.quit()
                self.root.destroy()
        else:
            if self.driver:
                self.driver.quit()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartMCNumberExtractorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()