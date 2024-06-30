import tkinter as tk
import pandas as pd
import os
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageTk

class Booking:
    def __init__(self, booking_id, name, campsite, start_date, end_date, checkin_time, checkout_time, people, status, extras, extras_paid, kayaks, kayaks_count):
        self.booking_id = booking_id
        self.name = name
        self.campsite = campsite
        self.start_date = start_date
        self.end_date = end_date
        self.checkin_time = checkin_time
        self.checkout_time = checkout_time
        self.people = people
        self.status = status
        self.extras = extras
        self.extras_paid = extras_paid
        self.kayaks = kayaks
        self.kayaks_count = kayaks_count

    def to_dict(self):
        return {
            "ID": self.booking_id,
            "Name": self.name,
            "Campsite": self.campsite,
            "Start Date": self.start_date,
            "End Date": self.end_date,
            "Check-in Time": self.checkin_time,
            "Check-out Time": self.checkout_time,
            "People": self.people,
            "Status": self.status,
            "Extras": self.extras,
            "Extras Paid": self.extras_paid,
            "Kayaks": self.kayaks,
            "Kayaks Count": self.kayaks_count
        }

class BookingManager:
    def __init__(self, master):
        self.master = master
        self.master.title("Warrago Farm, Condamine River Caravan & Camping - Booking Manager")
        self.master.attributes('-zoomed', True)
        self.master.resizable(True, True)
        self.master.grid_rowconfigure(1, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

        self.bookings = []
        self.next_booking_id = 1
        self.load_bookings()

        self.campsites = {
            '1a': 4, '1b': 4, '1c': 4, '1d': 4,
            '2a': 4, '2b': 4, '2c': 4, '2d': 4,
            '3': 4, '4': 4, '5': 4,
            '6a': 4, '6b': 4,
            'Sandy': 10,
            'Jerrys': 4,
            'Gidgea Flats': 30
        }

        self.create_widgets()

    def load_bookings(self):
        if os.path.exists('bookings.csv'):
            df = pd.read_csv('bookings.csv', parse_dates=['Start Date', 'End Date'])
            for _, row in df.iterrows():
                booking = Booking(
                    booking_id=row['ID'],
                    name=row['Name'],
                    campsite=row['Campsite'],
                    start_date=row['Start Date'],
                    end_date=row['End Date'],
                    checkin_time=row['Check-in Time'],
                    checkout_time=row['Check-out Time'],
                    people=row['People'],
                    status=row['Status'],
                    extras=row['Extras'],
                    extras_paid=row['Extras Paid'],
                    kayaks=row['Kayaks'],
                    kayaks_count=row['Kayaks Count']
                )
                self.bookings.append(booking)
                if booking.booking_id >= self.next_booking_id:
                    self.next_booking_id = booking.booking_id + 1

    def save_bookings(self):
        df = pd.DataFrame([b.to_dict() for b in self.bookings])
        df.to_csv('bookings.csv', index=False)

    def create_widgets(self):
        main_frame = tk.Frame(self.master, padx=10, pady=10)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Add logo and branding
        logo = Image.open("warrago_farm_logo.png")  # Make sure to place your logo image in the same directory
        logo = logo.resize((150, 150), Image.Resampling.LANCZOS)
        logo = ImageTk.PhotoImage(logo)
        logo_label = tk.Label(main_frame, image=logo)
        logo_label.image = logo  # keep a reference!
        logo_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        header_label = tk.Label(main_frame, text="Warrago Farm \n Condamine River Caravan & Camping", font=("Helvetica", 35))
        header_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.calendar_frame = tk.Frame(main_frame)
        self.calendar_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.calendar_frame.grid_rowconfigure(1, weight=1)
        self.calendar_frame.grid_columnconfigure(0, weight=1)

        self.month_year_nav_frame = tk.Frame(self.calendar_frame)
        self.month_year_nav_frame.grid(row=0, column=0, columnspan=7, pady=10)

        self.prev_button = tk.Button(self.month_year_nav_frame, text="<< Previous", command=self.prev_month)
        self.prev_button.pack(side=tk.LEFT)

        self.month_year_label = tk.Label(self.month_year_nav_frame, text="", font=("Helvetica", 16))
        self.month_year_label.pack(side=tk.LEFT, padx=20)

        self.next_button = tk.Button(self.month_year_nav_frame, text="Next >>", command=self.next_month)
        self.next_button.pack(side=tk.LEFT)

        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self.display_calendar(self.current_year, self.current_month)

        self.booking_frame = tk.Frame(main_frame)
        self.booking_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.booking_frame.grid_rowconfigure(0, weight=1)
        self.booking_frame.grid_columnconfigure(0, weight=1)

        self.booking_canvas = tk.Canvas(self.booking_frame)
        self.scrollbar = tk.Scrollbar(self.booking_frame, orient="vertical", command=self.booking_canvas.yview)
        self.scrollable_frame = tk.Frame(self.booking_canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: self.booking_canvas.configure(scrollregion=self.booking_canvas.bbox("all")))

        self.booking_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.booking_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.booking_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.create_booking_form()

    def create_booking_form(self):
        form_labels = ["Name", "Campsite", "Start Date", "End Date", "Check-in Time", "Check-out Time", "People", "Status"]
        self.form_vars = {}

        section_title = tk.Label(self.scrollable_frame, text="Booking Details", font=("Helvetica", 18))
        section_title.grid(row=0, column=0, columnspan=2, pady=10)

        for i, label in enumerate(form_labels):
            tk.Label(self.scrollable_frame, text=label).grid(row=i+1, column=0, sticky="e")
            if label in ["Campsite", "Status"]:
                self.form_vars[label] = tk.StringVar()
                entry = ttk.Combobox(self.scrollable_frame, textvariable=self.form_vars[label])
                if label == "Campsite":
                    entry['values'] = list(self.campsites.keys())
                else:
                    entry['values'] = ['Pending', 'Confirmed', 'Canceled']
            elif label in ["Start Date", "End Date"]:
                entry = DateEntry(self.scrollable_frame, date_pattern='dd/MM/yyyy')
                self.form_vars[label] = entry
            elif label == "People":
                self.form_vars[label] = tk.StringVar()
                entry = ttk.Combobox(self.scrollable_frame, textvariable=self.form_vars[label])
                entry['values'] = [str(i) for i in range(1, 31)]
            else:
                self.form_vars[label] = tk.StringVar()
                entry = tk.Entry(self.scrollable_frame, textvariable=self.form_vars[label])
            entry.grid(row=i+1, column=1, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_field)
            entry.bind("<KeyRelease>", self.validate_field)
            self.add_tooltip(entry, f"Enter {label.lower()}")

        self.form_vars["Check-in Time"].set("13:00")
        self.form_vars["Check-out Time"].set("11:00")

        self.create_extras_section()

        self.add_booking_button = tk.Button(self.scrollable_frame, text="Add Booking", command=self.add_booking)
        self.add_booking_button.grid(row=10, column=0, columnspan=2, pady=10)

        self.edit_booking_button = tk.Button(self.scrollable_frame, text="Edit Booking", command=self.edit_booking)
        self.edit_booking_button.grid(row=11, column=0, columnspan=2, pady=10)

        self.detail_button = tk.Button(self.scrollable_frame, text="Show Details", command=self.show_details)
        self.detail_button.grid(row=12, column=0, columnspan=2, pady=10)

        self.delete_booking_button = tk.Button(self.scrollable_frame, text="Delete Booking", command=self.delete_booking)
        self.delete_booking_button.grid(row=13, column=0, columnspan=2, pady=10)

        self.view_all_button = tk.Button(self.scrollable_frame, text="View All Bookings", command=self.view_all_bookings)
        self.view_all_button.grid(row=14, column=0, columnspan=2, pady=10)

        self.search_button = tk.Button(self.scrollable_frame, text="Search Bookings", command=self.search_bookings)
        self.search_button.grid(row=15, column=0, columnspan=2, pady=10)

        self.report_button = tk.Button(self.scrollable_frame, text="Generate Report", command=self.generate_report)
        self.report_button.grid(row=16, column=0, columnspan=2, pady=10)

        self.extras_cost_label = tk.Label(self.scrollable_frame, text="Extras Cost: $0")
        self.extras_cost_label.grid(row=17, column=0, columnspan=2, pady=10)

    def create_extras_section(self):
        extras_frame = tk.LabelFrame(self.scrollable_frame, text="Extras", padx=10, pady=10)
        extras_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")

        self.extras_vars = {
            'Portable Toilet': tk.BooleanVar(),
            'Fire Wood': tk.StringVar(),
            'Bag of Ice': tk.StringVar(),
            '1 Dozen Eggs': tk.StringVar(),
            'Honey': tk.StringVar(),
            'Breakfast Special': tk.StringVar(),
            'Meat Tray': tk.StringVar(),
            'Kayaks': tk.BooleanVar(),
            'Kayaks Count': tk.StringVar()
        }

        tk.Checkbutton(extras_frame, text="Portable Toilet ($70 for <10 people or Free for >10 people)", variable=self.extras_vars['Portable Toilet'], command=self.update_extras_cost).grid(row=0, column=0, sticky="w")
        self.create_extras_entry(extras_frame, "Fire Wood ($15 per 20 kg bag)", 'Fire Wood', 1)
        self.create_extras_entry(extras_frame, "Bag of Ice ($5 each)", 'Bag of Ice', 2)
        self.create_extras_entry(extras_frame, "1 Dozen Eggs ($8)", '1 Dozen Eggs', 3)
        self.create_extras_entry(extras_frame, "Honey ($13)", 'Honey', 4)
        self.create_extras_entry(extras_frame, "Breakfast Special ($20)", 'Breakfast Special', 5)
        self.create_extras_entry(extras_frame, "Meat Tray ($60)", 'Meat Tray', 6)

        tk.Checkbutton(extras_frame, text="Use of Kayaks", variable=self.extras_vars['Kayaks'], command=self.update_extras_cost).grid(row=7, column=0, sticky="w")
        self.create_extras_entry(extras_frame, "Number of Kayaks", 'Kayaks Count', 8)

        self.extras_paid_var = tk.BooleanVar()
        tk.Checkbutton(extras_frame, text="Extras Paid?", variable=self.extras_paid_var).grid(row=9, column=0, columnspan=2, sticky="w")

    def create_extras_entry(self, frame, label_text, var_key, row):
        tk.Label(frame, text=label_text).grid(row=row, column=0, sticky="e")
        entry = tk.Entry(frame, textvariable=self.extras_vars[var_key])
        entry.grid(row=row, column=1, pady=5, sticky="ew")
        entry.bind("<KeyRelease>", self.update_extras_cost)
        self.add_tooltip(entry, f"Enter quantity for {label_text.split(' ')[0].lower()}")

    def display_calendar(self, year, month):
        for widget in self.calendar_frame.winfo_children():
            if widget != self.month_year_nav_frame:
                widget.destroy()

        self.month_year_label.config(text=f"{datetime(year, month, 1).strftime('%B %Y')}")

        days_in_month = (datetime(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31
        first_day = datetime(year, month, 1).weekday()

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i, day in enumerate(days):
            tk.Label(self.calendar_frame, text=day).grid(row=1, column=i, sticky="ew")

        row = 2
        col = first_day
        for day in range(1, days_in_month + 1):
            day_str = f"{day:02d}/{month:02d}/{year}"
            day_btn = tk.Button(self.calendar_frame, text=str(day), width=12, height=5, command=lambda d=day_str: self.show_day_bookings(d))
            day_btn.grid(row=row, column=col, sticky="nsew")
            if self.is_date_booked(day_str):
                day_btn.config(background='red')
            else:
                day_btn.config(background='green')
            col += 1
            if col > 6:
                col = 0
                row += 1

        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.display_calendar(self.current_year, self.current_month)

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.display_calendar(self.current_year, self.current_month)

    def add_booking(self):
        booking_data = {label: var.get() for label, var in self.form_vars.items()}
        booking_data['Start Date'] = self.form_vars['Start Date'].get_date()
        booking_data['End Date'] = self.form_vars['End Date'].get_date()
        booking_data['People'] = int(self.form_vars['People'].get() or 0)
        booking_data['Kayaks'] = self.extras_vars['Kayaks'].get()
        booking_data['Kayaks Count'] = int(self.extras_vars['Kayaks Count'].get() or 0)

        extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.extras_vars.items() if isinstance(var, tk.StringVar)}
        extras_booleans = {key: var.get() for key, var in self.extras_vars.items() if isinstance(var, tk.BooleanVar)}
        extras_paid = self.extras_paid_var.get()

        if not (booking_data['Name'] and booking_data['Campsite'] and booking_data['Start Date'] and booking_data['End Date'] and booking_data['People']):
            messagebox.showerror("Input Error", "All fields are required.")
            return

        if booking_data['Start Date'] > booking_data['End Date']:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return

        try:
            booking_data['Check-in Time'] = datetime.strptime(booking_data['Check-in Time'], '%H:%M').time()
            booking_data['Check-out Time'] = datetime.strptime(booking_data['Check-out Time'], '%H:%M').time()
        except ValueError:
            messagebox.showerror("Time Error", "Time must be in HH:MM format.")
            return

        if self.is_site_booked(booking_data['Campsite'], booking_data['Start Date'], booking_data['End Date'], booking_data['Check-in Time'], booking_data['Check-out Time']):
            messagebox.showerror("Booking Error", "This campsite is already booked for the selected dates and times.")
            return

        extras_cost = self.calculate_extras_cost(extras_data, extras_booleans, booking_data['People'])
        extras_summary = ', '.join([f"{key} ({value})" for key, value in extras_data.items() if value] + [f"{key} (Yes)" for key, value in extras_booleans.items() if value])

        new_booking = Booking(
            booking_id=self.next_booking_id,
            name=booking_data['Name'],
            campsite=booking_data['Campsite'],
            start_date=booking_data['Start Date'],
            end_date=booking_data['End Date'],
            checkin_time=booking_data['Check-in Time'],
            checkout_time=booking_data['Check-out Time'],
            people=booking_data['People'],
            status=booking_data['Status'],
            extras=extras_summary,
            extras_paid=extras_paid,
            kayaks=booking_data['Kayaks'],
            kayaks_count=booking_data['Kayaks Count']
        )
        self.bookings.append(new_booking)
        self.next_booking_id += 1

        self.save_bookings()
        self.update_calendar()
        messagebox.showinfo("Success", f"Booking added successfully. Extras cost: ${extras_cost}")
        self.extras_cost_label.config(text=f"Extras Cost: ${extras_cost}")

    def calculate_extras_cost(self, extras, booleans, people):
        cost = 0
        if booleans['Portable Toilet'] and people < 10:
            cost += 70
        cost += extras['Fire Wood'] * 15
        cost += extras['Bag of Ice'] * 5
        cost += extras['1 Dozen Eggs'] * 8
        cost += extras['Honey'] * 13
        cost += extras['Breakfast Special'] * 20
        cost += extras['Meat Tray'] * 60
        return cost

    def is_site_booked(self, campsite, start_date, end_date, start_time, end_time):
        for booking in self.bookings:
            if booking.campsite == campsite and booking.status != 'Canceled':
                if start_date <= booking.end_date and end_date >= booking.start_date:
                    if start_date == booking.end_date and start_time < booking.checkout_time:
                        return True
                    if end_date == booking.start_date and end_time > booking.checkin_time:
                        return True
                    if start_date < booking.end_date and end_date > booking.start_date:
                        return True
        return False

    def edit_booking(self):
        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Booking")
        edit_window.geometry("400x700")

        self.create_edit_form(edit_window)

    def create_edit_form(self, window):
        tk.Label(window, text="Booking ID").grid(row=0, column=0, sticky="e")
        self.booking_id_var = tk.StringVar()
        self.booking_id_entry = tk.Entry(window, textvariable=self.booking_id_var)
        self.booking_id_entry.grid(row=0, column=1, pady=5, sticky="ew")

        form_labels = ["New Name", "New Campsite", "New Start Date", "New End Date", "New Start Time", "New End Time", "New People", "New Status"]
        self.edit_vars = {}

        for i, label in enumerate(form_labels):
            tk.Label(window, text=label).grid(row=i + 1, column=0, sticky="e")
            if label in ["New Campsite", "New Status"]:
                self.edit_vars[label] = tk.StringVar()
                entry = ttk.Combobox(window, textvariable=self.edit_vars[label])
                if label == "New Campsite":
                    entry['values'] = list(self.campsites.keys())
                else:
                    entry['values'] = ['Pending', 'Confirmed', 'Canceled']
            elif label in ["New Start Date", "New End Date"]:
                entry = DateEntry(window, date_pattern='dd/MM/yyyy')
                self.edit_vars[label] = entry
            elif label == "New People":
                self.edit_vars[label] = tk.StringVar()
                entry = ttk.Combobox(window, textvariable=self.edit_vars[label])
                entry['values'] = [str(i) for i in range(1, 31)]
            else:
                self.edit_vars[label] = tk.StringVar()
                entry = tk.Entry(window, textvariable=self.edit_vars[label])
            entry.grid(row=i + 1, column=1, pady=5, sticky="ew")
            entry.bind("<FocusOut>", self.validate_field)
            entry.bind("<KeyRelease>", self.validate_field)
            self.add_tooltip(entry, f"Enter new {label.split(' ')[1].lower()}")

        new_extras_frame = tk.LabelFrame(window, text="New Extras", padx=10, pady=10)
        new_extras_frame.grid(row=9, column=0, columnspan=2, pady=10, sticky="ew")

        self.new_extras_vars = {
            'Portable Toilet': tk.BooleanVar(),
            'Fire Wood': tk.StringVar(),
            'Bag of Ice': tk.StringVar(),
            '1 Dozen Eggs': tk.StringVar(),
            'Honey': tk.StringVar(),
            'Breakfast Special': tk.StringVar(),
            'Meat Tray': tk.StringVar(),
            'Kayaks': tk.BooleanVar(),
            'Kayaks Count': tk.StringVar()
        }

        tk.Checkbutton(new_extras_frame, text="Portable Toilet ($70 for <10 people)", variable=self.new_extras_vars['Portable Toilet']).grid(row=0, column=0, sticky="w")
        self.create_extras_entry(new_extras_frame, "Fire Wood ($15 per 20 kg bag)", 'Fire Wood', 1)
        self.create_extras_entry(new_extras_frame, "Bag of Ice ($5 each)", 'Bag of Ice', 2)
        self.create_extras_entry(new_extras_frame, "1 Dozen Eggs ($8)", '1 Dozen Eggs', 3)
        self.create_extras_entry(new_extras_frame, "Honey ($13)", 'Honey', 4)
        self.create_extras_entry(new_extras_frame, "Breakfast Special ($20)", 'Breakfast Special', 5)
        self.create_extras_entry(new_extras_frame, "Meat Tray ($60)", 'Meat Tray', 6)

        tk.Checkbutton(new_extras_frame, text="Use of Kayaks", variable=self.new_extras_vars['Kayaks']).grid(row=7, column=0, sticky="w")
        self.create_extras_entry(new_extras_frame, "Number of Kayaks", 'Kayaks Count', 8)

        self.new_extras_paid_var = tk.BooleanVar()
        tk.Checkbutton(new_extras_frame, text="Extras Paid", variable=self.new_extras_paid_var).grid(row=9, column=0, columnspan=2, sticky="w")

        self.update_booking_button = tk.Button(window, text="Update Booking", command=self.update_booking)
        self.update_booking_button.grid(row=11, column=0, columnspan=2, pady=10)

        window.columnconfigure(1, weight=1)

    def update_booking(self):
        booking_id = self.booking_id_var.get()
        updated_data = {label: var.get() for label, var in self.edit_vars.items()}
        updated_data['New Start Date'] = self.edit_vars['New Start Date'].get_date()
        updated_data['New End Date'] = self.edit_vars['New End Date'].get_date()
        updated_data['New People'] = int(self.edit_vars['New People'].get() or 0)
        updated_data['New Kayaks'] = self.new_extras_vars['Kayaks'].get()
        updated_data['New Kayaks Count'] = int(self.new_extras_vars['Kayaks Count'].get() or 0)

        new_extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.new_extras_vars.items() if isinstance(var, tk.StringVar)}
        new_extras_booleans = {key: var.get() for key, var in self.new_extras_vars.items() if isinstance(var, tk.BooleanVar)}
        new_extras_paid = self.new_extras_paid_var.get()

        if not (updated_data['New Name'] and updated_data['New Campsite'] and updated_data['New Start Date'] and updated_data['New End Date'] and updated_data['New People']):
            messagebox.showerror("Input Error", "All fields are required.")
            return

        if updated_data['New Start Date'] > updated_data['New End Date']:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return

        try:
            updated_data['New Start Time'] = datetime.strptime(updated_data['New Start Time'], '%H:%M').time()
            updated_data['New End Time'] = datetime.strptime(updated_data['New End Time'], '%H:%M').time()
        except ValueError:
            messagebox.showerror("Time Error", "Time must be in HH:MM format.")
            return

        try:
            booking_id = int(booking_id)
        except ValueError:
            messagebox.showerror("ID Error", "Booking ID must be a number.")
            return

        booking = next((b for b in self.bookings if b.booking_id == booking_id), None)
        if not booking:
            messagebox.showerror("ID Error", "Booking ID does not exist.")
            return

        if self.is_site_booked(updated_data['New Campsite'], updated_data['New Start Date'], updated_data['New End Date'], updated_data['New Start Time'], updated_data['New End Time']):
            messagebox.showerror("Booking Error", "This campsite is already booked for the selected dates and times.")
            return

        new_extras_cost = self.calculate_extras_cost(new_extras_data, new_extras_booleans, updated_data['New People'])
        new_extras_summary = ', '.join([f"{key} ({value})" for key, value in new_extras_data.items() if value] + [f"{key} (Yes)" for key, value in new_extras_booleans.items() if value])

        booking.name = updated_data['New Name']
        booking.campsite = updated_data['New Campsite']
        booking.start_date = updated_data['New Start Date']
        booking.end_date = updated_data['New End Date']
        booking.checkin_time = updated_data['New Start Time']
        booking.checkout_time = updated_data['New End Time']
        booking.people = updated_data['New People']
        booking.status = updated_data['New Status']
        booking.extras = new_extras_summary
        booking.extras_paid = new_extras_paid
        booking.kayaks = updated_data['New Kayaks']
        booking.kayaks_count = updated_data['New Kayaks Count']

        self.save_bookings()
        self.update_calendar()
        messagebox.showinfo("Success", f"Booking updated successfully. New extras cost: ${new_extras_cost}")
        self.extras_cost_label.config(text=f"Extras Cost: ${new_extras_cost}")

    def delete_booking(self):
        delete_window = tk.Toplevel(self.master)
        delete_window.title("Delete Booking")
        delete_window.geometry("300x100")

        tk.Label(delete_window, text="Booking ID").grid(row=0, column=0, sticky="e")
        self.del_booking_id_var = tk.StringVar()
        self.del_booking_id_entry = tk.Entry(delete_window, textvariable=self.del_booking_id_var)
        self.del_booking_id_entry.grid(row=0, column=1, pady=5, sticky="ew")

        self.delete_booking_button = tk.Button(delete_window, text="Delete Booking", command=self.confirm_delete_booking)
        self.delete_booking_button.grid(row=1, column=0, columnspan=2, pady=10)

        delete_window.columnconfigure(1, weight=1)

    def confirm_delete_booking(self):
        booking_id = self.del_booking_id_var.get()

        try:
            booking_id = int(booking_id)
        except ValueError:
            messagebox.showerror("ID Error", "Booking ID must be a number.")
            return

        booking = next((b for b in self.bookings if b.booking_id == booking_id), None)
        if not booking:
            messagebox.showerror("ID Error", "Booking ID does not exist.")
            return

        confirmation = messagebox.askyesno("Delete Confirmation", "Are you sure you want to delete this booking?")
        if confirmation:
            self.bookings.remove(booking)
            self.save_bookings()
            self.update_calendar()
            messagebox.showinfo("Success", "Booking deleted successfully.")

    def show_details(self):
        details_window = tk.Toplevel(self.master)
        details_window.title("Campsite Details")
        details_window.geometry("500x400")

        tk.Label(details_window, text="Campsite").grid(row=0, column=0, sticky="e")
        self.details_campsite_var = tk.StringVar()
        self.details_campsite_entry = ttk.Combobox(details_window, textvariable=self.details_campsite_var)
        self.details_campsite_entry['values'] = list(self.campsites.keys())
        self.details_campsite_entry.grid(row=0, column=1, pady=5, sticky="ew")

        self.show_details_button = tk.Button(details_window, text="Show Bookings", command=self.display_details)
        self.show_details_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.details_text = tk.Text(details_window, width=50, height=20)
        self.details_text.grid(row=2, column=0, columnspan=2)

        details_window.columnconfigure(1, weight=1)

    def display_details(self):
        campsite = self.details_campsite_var.get()
        if not campsite:
            messagebox.showerror("Input Error", "Campsite is required.")
            return

        details = pd.DataFrame([b.to_dict() for b in self.bookings if b.campsite == campsite])
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details.to_string(index=False))

    def show_day_bookings(self, date):
        day_window = tk.Toplevel(self.master)
        day_window.title(f"Bookings on {date}")
        day_window.geometry("500x400")

        day_text = tk.Text(day_window, width=50, height=20)
        day_text.pack(pady=10)

        day_date = datetime.strptime(date, '%d/%m/%Y')
        day_bookings = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date.date() <= day_date.date() <= b.end_date.date()])
        if day_bookings.empty:
            day_text.insert(tk.END, "No bookings for this day.")
        else:
            day_text.insert(tk.END, day_bookings.to_string(index=False))

    def view_all_bookings(self):
        all_window = tk.Toplevel(self.master)
        all_window.title("All Bookings")
        all_window.geometry("800x600")

        all_text = tk.Text(all_window, width=80, height=20)
        all_text.pack(pady=10)

        all_bookings = pd.DataFrame([b.to_dict() for b in self.bookings])
        if all_bookings.empty:
            all_text.insert(tk.END, "No bookings available.")
        else:
            all_text.insert(tk.END, all_bookings.to_string(index=False))

    def search_bookings(self):
        search_window = tk.Toplevel(self.master)
        search_window.title("Search Bookings")
        search_window.geometry("300x200")

        tk.Label(search_window, text="Search by Name").grid(row=0, column=0, sticky="e")
        self.search_name_var = tk.StringVar()
        self.search_name_entry = tk.Entry(search_window, textvariable=self.search_name_var)
        self.search_name_entry.grid(row=0, column=1, pady=5, sticky="ew")

        tk.Label(search_window, text="Search by Date").grid(row=1, column=0, sticky="e")
        self.search_date_entry = DateEntry(search_window, date_pattern='dd/MM/yyyy')
        self.search_date_entry.grid(row=1, column=1, pady=5, sticky="ew")

        self.search_button = tk.Button(search_window, text="Search", command=self.perform_search)
        self.search_button.grid(row=2, column=0, columnspan=2, pady=10)

        search_window.columnconfigure(1, weight=1)

    def perform_search(self):
        name = self.search_name_var.get()
        date = self.search_date_entry.get_date()

        results = pd.DataFrame()
        if name:
            results = pd.DataFrame([b.to_dict() for b in self.bookings if name.lower() in b.name.lower()])

        if date:
            date_results = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date.date() <= date <= b.end_date.date()])
            results = pd.concat([results, date_results]).drop_duplicates().reset_index(drop=True)

        if results.empty:
            messagebox.showinfo("Search Results", "No bookings found.")
        else:
            search_results_window = tk.Toplevel(self.master)
            search_results_window.title("Search Results")
            search_results_window.geometry("800x600")

            results_text = tk.Text(search_results_window, width=80, height=20)
            results_text.pack(pady=10)

            results_text.insert(tk.END, results.to_string(index=False))

    def generate_report(self):
        report_window = tk.Toplevel(self.master)
        report_window.title("Generate Report")
        report_window.geometry("300x200")

        tk.Label(report_window, text="Start Date").grid(row=0, column=0, sticky="e")
        self.report_start_date_entry = DateEntry(report_window, date_pattern='dd/MM/yyyy')
        self.report_start_date_entry.grid(row=0, column=1, pady=5, sticky="ew")

        tk.Label(report_window, text="End Date").grid(row=1, column=0, sticky="e")
        self.report_end_date_entry = DateEntry(report_window, date_pattern='dd/MM/yyyy')
        self.report_end_date_entry.grid(row=1, column=1, pady=5, sticky="ew")

        self.generate_button = tk.Button(report_window, text="Generate", command=self.perform_generate_report)
        self.generate_button.grid(row=2, column=0, columnspan=2, pady=10)

        report_window.columnconfigure(1, weight=1)

    def perform_generate_report(self):
        start_date = self.report_start_date_entry.get_date()
        end_date = self.report_end_date_entry.get_date()

        if start_date > end_date:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return

        report_results = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date.date() >= start_date and b.end_date.date() <= end_date])

        if report_results.empty:
            messagebox.showinfo("Report Results", "No bookings found for the selected period.")
        else:
            self.export_to_pdf(report_results)

    def export_to_pdf(self, data):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            c = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter
            x_offset = 50
            y_offset = height - 50
            line_height = 15

            c.setFont("Helvetica", 12)
            for i, col in enumerate(data.columns):
                c.drawString(x_offset + i*70, y_offset, col)

            y_offset -= line_height
            for _, row in data.iterrows():
                for i, value in enumerate(row):
                    c.drawString(x_offset + i*70, y_offset, str(value))
                y_offset -= line_height
                if y_offset < 50:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y_offset = height - 50

            c.save()
            messagebox.showinfo("Export Success", f"Data exported successfully to {file_path}")

    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            if isinstance(widget, tk.Button):
                date = widget.cget("text")
                day_str = f"{int(date):02d}/{self.current_month:02d}/{self.current_year}"
                if self.is_date_booked(day_str):
                    widget.config(background='red')
                else:
                    widget.config(background='green')

    def is_date_booked(self, date):
        date = datetime.strptime(date, '%d/%m/%Y').date()
        for booking in self.bookings:
            if booking.start_date.date() <= date <= booking.end_date.date():
                return True
        return False

    def validate_field(self, event):
        widget = event.widget
        if isinstance(widget, DateEntry):
            date_str = widget.get()
            try:
                datetime.strptime(date_str, '%d/%m/%Y')
                widget.configure(background='white')
            except ValueError:
                widget.configure(background='red')
        elif isinstance(widget, tk.Entry) or isinstance(widget, ttk.Combobox):
            value = widget.get()
            if widget in self.extras_vars.values() or widget == self.form_vars['People'] or widget == self.extras_vars['Kayaks Count']:
                if not value.isdigit() and value != '':
                    widget.config(background='red')
                else:
                    widget.config(background='white')
            else:
                if not value.strip():
                    widget.config(background='red')
                else:
                    widget.config(background='white')

    def add_tooltip(self, widget, text):
        tooltip = Tooltip(widget, text)
        widget.bind("<Enter>", tooltip.show)
        widget.bind("<Leave>", tooltip.hide)

    def update_extras_cost(self, event=None):
        extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.extras_vars.items() if isinstance(var, tk.StringVar)}
        extras_booleans = {key: var.get() for key, var in self.extras_vars.items() if isinstance(var, tk.BooleanVar)}
        people = int(self.form_vars['People'].get() or 0)
        extras_cost = self.calculate_extras_cost(extras_data, extras_booleans, people)
        self.extras_cost_label.config(text=f"Extras Cost: ${extras_cost}")

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show(self, event):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hide(self, event):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BookingManager(master=root)
    root.mainloop()
