import tkinter as tk
import pandas as pd
import os
import logging
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from PIL import Image, ImageTk
from typing import List, Dict, Any, Tuple
from tabulate import tabulate

# Constants
DATE_PATTERN = 'dd/MM/yyyy'
FORM_LABELS = ["Name", "Phone", "Email", "Campsite", "Start Date", "End Date", "People", "Status"]
CAMPSITES = {
    '1a': 25, '1b': 25, '1c': 25, '1d': 25,
    '2a': 25, '2b': 25, '2c': 25, '2d': 25,
    '3': 15, '4': 15, '5': 15,
    '6a': 15, '6b': 15,
    'Sandys': 15,
    'Jerrys': 20,
    'Gidgea Flats': 15
}

# Set up logging
logging.basicConfig(filename='app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class Booking:
    def __init__(self, booking_id: int, name: str, phone: str, email: str, campsite: str, start_date: str, end_date: str,
                 people: int, status: str, extras: str, extras_paid: bool, kayaks: bool, kayaks_count: int, is_group_booking: bool):
        self.booking_id = booking_id
        self.name = name
        self.phone = phone
        self.email = email
        self.campsite = campsite
        self.start_date = pd.Timestamp(start_date)
        self.end_date = pd.Timestamp(end_date)
        self.people = people
        self.status = status
        self.extras = extras
        self.extras_paid = extras_paid
        self.kayaks = kayaks
        self.kayaks_count = kayaks_count
        self.is_group_booking = is_group_booking

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ID": self.booking_id,
            "Name": self.name,
            "Phone": self.phone,
            "Email": self.email,
            "Campsite": self.campsite,
            "Start Date": self.start_date,
            "End Date": self.end_date,
            "People": self.people,
            "Status": self.status,
            "Extras": self.extras,
            "Extras Paid": self.extras_paid,
            "Kayaks": self.kayaks,
            "Kayaks Count": self.kayaks_count,
            "Is Group Booking": self.is_group_booking
        }

class BookingManager:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("Warrago Farm, Condamine River Caravan & Camping - Booking Manager")
        self.master.geometry("800x600")
        self.master.resizable(True, True)

        self.bookings: List[Booking] = []
        self.next_booking_id: int = 1
        self.campsites: Dict[str, int] = CAMPSITES
        self.load_all_bookings()
        self.create_widgets()

    def load_all_bookings(self) -> None:
        try:
            if os.path.exists('bookings.csv'):
                self.bookings_df = pd.read_csv('bookings.csv', parse_dates=['Start Date', 'End Date'])
                self._ensure_columns_exist()
                self.next_booking_id = self.bookings_df['ID'].max() + 1
            else:
                self.bookings_df = self.create_empty_bookings_df()
        except pd.errors.EmptyDataError:
            self.bookings_df = self.create_empty_bookings_df()

    def _ensure_columns_exist(self) -> None:
        for col in ['Phone', 'Email', 'Is Group Booking']:
            if col not in self.bookings_df.columns:
                if col == 'Is Group Booking':
                    self.bookings_df[col] = False
                else:
                    self.bookings_df[col] = ''

    def create_empty_bookings_df(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            'ID', 'Name', 'Phone', 'Email', 'Campsite', 'Start Date', 'End Date',
            'People', 'Status', 'Extras', 'Extras Paid', 'Kayaks', 'Kayaks Count', 'Is Group Booking'
        ])

    def load_bookings(self, year: int, month: int) -> None:
        start_date = pd.Timestamp(datetime(year, month, 1))
        end_date = (start_date + pd.DateOffset(days=32)).replace(day=1) - pd.DateOffset(days=1)
        bookings = self.bookings_df[
            (self.bookings_df['Start Date'] <= end_date) &
            (self.bookings_df['End Date'] >= start_date)
        ]
        self.bookings = [
            Booking(
                booking_id=row['ID'],
                name=row['Name'],
                phone=row['Phone'],
                email=row['Email'],
                campsite=row['Campsite'],
                start_date=row['Start Date'],
                end_date=row['End Date'],
                people=row['People'],
                status=row['Status'],
                extras=row['Extras'],
                extras_paid=row['Extras Paid'],
                kayaks=row['Kayaks'],
                kayaks_count=row['Kayaks Count'],
                is_group_booking=row.get('Is Group Booking', False)
            )
            for _, row in bookings.iterrows()
        ]

    def save_bookings(self) -> None:
        try:
            if not self.bookings:
                logging.warning("No bookings available to save.")
                messagebox.showwarning("Warning", "No bookings available to save.")
                return

            df = pd.DataFrame([b.to_dict() for b in self.bookings])
            df.to_csv('bookings.csv', index=False)
            logging.info("Bookings saved to bookings.csv")

            table_str = tabulate(df, headers='keys', tablefmt='grid')
            with open('bookings_formatted.txt', 'w') as f:
                f.write(table_str)
            logging.info("Formatted bookings saved to bookings_formatted.txt")

            self.load_all_bookings()

        except (pd.errors.EmptyDataError, FileNotFoundError) as e:
            logging.error(f"Error while saving bookings: {e}")
            messagebox.showerror("Error", "An error occurred while saving the bookings. Please try again.")
        except Exception as e:
            logging.error(f"Unexpected error while saving bookings: {e}")
            messagebox.showerror("Error", "An unexpected error occurred while saving the bookings. Please try again.")

    def create_widgets(self) -> None:
        main_frame = tk.Frame(self.master, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        self.create_logo(main_frame)
        self.create_calendar_frame(main_frame)
        self.create_booking_frame(main_frame)
        self.create_booking_form()

    def create_logo(self, main_frame: tk.Frame) -> None:
        def resize_logo(event):
            new_width = min(event.width // 4, 200)
            new_height = int(new_width * logo_original.height / logo_original.width)
            logo_resized = logo_original.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logo_image = ImageTk.PhotoImage(logo_resized)
            logo_label.config(image=logo_image)
            logo_label.image = logo_image

        logo_original = Image.open("logo.png")
        logo_placeholder = logo_original.resize((200, 200), Image.Resampling.LANCZOS)
        logo_image = ImageTk.PhotoImage(logo_placeholder)

        logo_label = tk.Label(main_frame, image=logo_image)
        logo_label.image = logo_image
        logo_label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        header_label = tk.Label(main_frame, text="Warrago Farm \n Condamine River Caravan & Camping", font=("Helvetica", 24))
        header_label.grid(row=0, column=1, padx=10, pady=10, sticky="nw")

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.bind("<Configure>", resize_logo)
        self.master.minsize(400, 300)

    def create_calendar_frame(self, main_frame: tk.Frame) -> None:
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
        self.load_bookings(self.current_year, self.current_month)
        self.display_calendar(self.current_year, self.current_month)

    def create_booking_frame(self, main_frame: tk.Frame) -> None:
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

    def create_booking_form(self) -> None:
        self.form_vars = {}
        self.create_form_title()
        self.create_form_fields(FORM_LABELS)
        self.create_group_booking_section()
        self.create_extras_section()
        self.create_form_buttons()

    def create_form_title(self) -> None:
        section_title = tk.Label(self.scrollable_frame, text="Booking Details", font=("Helvetica", 18))
        section_title.grid(row=0, column=0, columnspan=2, pady=10)

    def create_form_fields(self, labels: List[str]) -> None:
        for i, label in enumerate(labels):
            self.create_form_field(i + 1, label)

    def create_form_field(self, row: int, label: str) -> None:
        tk.Label(self.scrollable_frame, text=label).grid(row=row, column=0, sticky="e")
        if label in ["Campsite", "Status"]:
            self.form_vars[label] = tk.StringVar()
            entry = ttk.Combobox(self.scrollable_frame, textvariable=self.form_vars[label])
            entry['values'] = list(self.campsites.keys()) if label == "Campsite" else ['Pending', 'Confirmed', 'Canceled']
        elif label in ["Start Date", "End Date"]:
            entry = DateEntry(self.scrollable_frame, date_pattern=DATE_PATTERN)
            self.form_vars[label] = entry
        elif label == "People":
            self.form_vars[label] = tk.StringVar()
            entry = ttk.Combobox(self.scrollable_frame, textvariable=self.form_vars[label])
            entry['values'] = [str(i) for i in range(1, 31)]
        else:
            self.form_vars[label] = tk.StringVar()
            entry = tk.Entry(self.scrollable_frame, textvariable=self.form_vars[label])
        entry.grid(row=row, column=1, pady=5, sticky="ew")
        entry.bind("<FocusOut>", self.validate_field)
        entry.bind("<KeyRelease>", self.validate_field)
        self.add_tooltip(entry, f"Enter {label.lower()}")

    def create_group_booking_section(self) -> None:
        tk.Label(self.scrollable_frame, text="Group Booking").grid(row=9, column=0, sticky="e")
        self.group_booking_var = tk.BooleanVar()
        self.group_booking_checkbutton = tk.Checkbutton(self.scrollable_frame, variable=self.group_booking_var)
        self.group_booking_checkbutton.grid(row=9, column=1, sticky="w")

    def create_extras_section(self) -> None:
        extras_frame = tk.LabelFrame(self.scrollable_frame, text="Extras", padx=10, pady=10)
        extras_frame.grid(row=10, column=0, columnspan=2, pady=10, sticky="ew")

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

        self.create_extras_option(extras_frame, "Portable Toilet ($70 for <10 people or Free for >10 people)", 'Portable Toilet', 0, True)
        self.create_extras_entry(extras_frame, "Fire Wood ($15 per 20 kg bag)", 'Fire Wood', 1)
        self.create_extras_entry(extras_frame, "Bag of Ice ($5 each)", 'Bag of Ice', 2)
        self.create_extras_entry(extras_frame, "1 Dozen Eggs ($8)", '1 Dozen Eggs', 3)
        self.create_extras_entry(extras_frame, "Honey ($13)", 'Honey', 4)
        self.create_extras_entry(extras_frame, "Breakfast Special ($20)", 'Breakfast Special', 5)
        self.create_extras_entry(extras_frame, "Meat Tray ($60)", 'Meat Tray', 6)
        self.create_extras_option(extras_frame, "Use of Kayaks", 'Kayaks', 7, True)
        self.create_extras_entry(extras_frame, "Number of Kayaks", 'Kayaks Count', 8)

        self.extras_paid_var = tk.BooleanVar()
        tk.Checkbutton(extras_frame, text="Extras Paid?", variable=self.extras_paid_var).grid(row=9, column=0, columnspan=2, sticky="w")

    def create_extras_option(self, frame: tk.Frame, label_text: str, var_key: str, row: int, has_callback: bool = False) -> None:
        tk.Checkbutton(frame, text=label_text, variable=self.extras_vars[var_key], command=self.update_extras_cost if has_callback else None).grid(row=row, column=0, sticky="w")

    def create_extras_entry(self, frame: tk.Frame, label_text: str, var_key: str, row: int) -> None:
        tk.Label(frame, text=label_text).grid(row=row, column=0, sticky="e")
        entry = tk.Entry(frame, textvariable=self.extras_vars[var_key])
        entry.grid(row=row, column=1, pady=5, sticky="ew")
        entry.bind("<KeyRelease>", self.update_extras_cost)
        self.add_tooltip(entry, f"Enter quantity for {label_text.split(' ')[0].lower()}")

    def create_form_buttons(self) -> None:
        button_frame = tk.Frame(self.scrollable_frame)
        button_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")

        self.add_booking_button = tk.Button(button_frame, text="Add Booking", command=self.add_booking)
        self.add_booking_button.grid(row=0, column=0, padx=5, pady=5)

        self.edit_booking_button = tk.Button(button_frame, text="Edit Booking", command=self.edit_booking)
        self.edit_booking_button.grid(row=0, column=1, padx=5, pady=5)

        self.detail_button = tk.Button(button_frame, text="Show Details", command=self.show_details)
        self.detail_button.grid(row=0, column=2, padx=5, pady=5)

        self.delete_booking_button = tk.Button(button_frame, text="Delete Booking", command=self.delete_booking)
        self.delete_booking_button.grid(row=1, column=0, padx=5, pady=5)

        self.view_all_button = tk.Button(button_frame, text="View All Bookings", command=self.view_all_bookings)
        self.view_all_button.grid(row=1, column=1, padx=5, pady=5)

        self.search_button = tk.Button(button_frame, text="Search Bookings", command=self.search_bookings)
        self.search_button.grid(row=1, column=2, padx=5, pady=5)

        self.report_button = tk.Button(button_frame, text="Generate Report", command=self.generate_report)
        self.report_button.grid(row=2, column=0, columnspan=3, pady=5)

        self.extras_cost_label = tk.Label(self.scrollable_frame, text="Extras Cost: $0")
        self.extras_cost_label.grid(row=12, column=0, columnspan=2, pady=10)

    def display_calendar(self, year: int, month: int) -> None:
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
            bookings = self.get_booking_text_for_date(day_str)
            if bookings:
                day_btn.config(text=f"{day}\n{bookings}", anchor='n')
                day_btn.config(background='red')
            else:
                day_btn.config(background='green')
            col += 1
            if col > 6:
                col = 0
                row += 1

        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)

    def prev_month(self) -> None:
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.load_bookings(self.current_year, self.current_month)
        self.display_calendar(self.current_year, self.current_month)

    def next_month(self) -> None:
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.load_bookings(self.current_year, self.current_month)
        self.display_calendar(self.current_year, self.current_month)

    def get_booking_text_for_date(self, date: str) -> str:
        date = pd.Timestamp(datetime.strptime(date, '%d/%m/%Y'))
        bookings_text = []
        for booking in self.bookings:
            if booking.start_date <= date <= booking.end_date:
                if booking.start_date == date and booking.end_date == date:
                    bookings_text.append(f"{booking.campsite} {booking.name} (in/out)")
                elif booking.start_date == date:
                    bookings_text.append(f"{booking.campsite} {booking.name} (in)")
                elif booking.end_date == date:
                    bookings_text.append(f"{booking.campsite} {booking.name} (out)")
                else:
                    bookings_text.append(f"{booking.campsite} {booking.name}")
        return '\n'.join(bookings_text)

    def add_booking(self) -> None:
        try:
            booking_data = self.get_form_data()
            extras_data, extras_booleans, extras_paid = self.get_extras_data()

            if not self.validate_booking_data(booking_data):
                return

            if not booking_data['Is Group Booking'] and self.is_site_booked(booking_data['Campsite'], booking_data['Start Date'], booking_data['End Date']):
                self.suggest_alternatives(booking_data)
                return

            extras_cost = self.calculate_extras_cost(extras_data, extras_booleans, booking_data['People'])
            extras_summary = ', '.join([f"{key} ({value})" for key, value in extras_data.items() if value] + [f"{key} (Yes)" for key, value in extras_booleans.items() if value])

            new_booking = Booking(
                booking_id=self.next_booking_id,
                name=booking_data['Name'],
                phone=booking_data['Phone'],
                email=booking_data['Email'],
                campsite=booking_data['Campsite'],
                start_date=booking_data['Start Date'],
                end_date=booking_data['End Date'],
                people=booking_data['People'],
                status=booking_data['Status'],
                extras=extras_summary,
                extras_paid=extras_paid,
                kayaks=booking_data['Kayaks'],
                kayaks_count=booking_data['Kayaks Count'],
                is_group_booking=booking_data['Is Group Booking']
            )
            self.bookings.append(new_booking)
            self.next_booking_id += 1

            self.save_bookings()
            self.update_calendar()
            messagebox.showinfo("Success", f"Booking added successfully. Extras cost: ${extras_cost}")
            self.extras_cost_label.config(text=f"Extras Cost: ${extras_cost}")
            self.clear_form_fields()
        except Exception as e:
            logging.error(f"Error in add_booking: {e}")
            messagebox.showerror("Error", "An error occurred while adding the booking. Please try again.")

    def get_form_data(self) -> Dict[str, Any]:
        booking_data = {label: var.get() for label, var in self.form_vars.items()}
        booking_data['Start Date'] = pd.Timestamp(self.form_vars['Start Date'].get_date())
        booking_data['End Date'] = pd.Timestamp(self.form_vars['End Date'].get_date())
        booking_data['People'] = int(self.form_vars['People'].get() or 0)
        booking_data['Kayaks'] = self.extras_vars['Kayaks'].get()
        booking_data['Kayaks Count'] = int(self.extras_vars['Kayaks Count'].get() or 0)
        booking_data['Is Group Booking'] = self.group_booking_var.get()
        return booking_data

    def get_extras_data(self) -> Tuple[Dict[str, int], Dict[str, bool], bool]:
        extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.extras_vars.items() if isinstance(var, tk.StringVar)}
        extras_booleans = {key: var.get() for key, var in self.extras_vars.items() if isinstance(var, tk.BooleanVar)}
        extras_paid = self.extras_paid_var.get()
        return extras_data, extras_booleans, extras_paid

    def validate_booking_data(self, booking_data: Dict[str, Any]) -> bool:
        if not (booking_data['Name'] and booking_data['Phone'] and booking_data['Email'] and booking_data['Campsite'] and booking_data['Start Date'] and booking_data['End Date'] and booking_data['People']):
            messagebox.showerror("Input Error", "All fields are required.")
            return False

        if booking_data['Start Date'] > booking_data['End Date']:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return False

        return True

    def calculate_extras_cost(self, extras: Dict[str, int], booleans: Dict[str, bool], people: int) -> int:
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

    def is_site_booked(self, campsite: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> bool:
        logging.debug(f"Checking availability for {campsite} from {start_date} to {end_date}")
        for booking in self.bookings:
            if booking.campsite == campsite and booking.status != 'Canceled' and not booking.is_group_booking:
                if start_date < booking.end_date and end_date > booking.start_date:
                    return True
        logging.debug(f"Campsite {campsite} is available for the selected dates.")
        return False

    def edit_booking(self) -> None:
        edit_window = tk.Toplevel(self.master)
        edit_window.title("Edit Booking")
        edit_window.geometry("400x700")

        self.create_edit_form(edit_window)

    def create_edit_form(self, window: tk.Toplevel) -> None:
        tk.Label(window, text="Booking ID").grid(row=0, column=0, sticky="e")
        self.booking_id_var = tk.StringVar()
        self.booking_id_entry = tk.Entry(window, textvariable=self.booking_id_var)
        self.booking_id_entry.grid(row=0, column=1, pady=5, sticky="ew")

        form_labels = ["New Name", "New Phone", "New Email", "New Campsite", "New Start Date", "New End Date", "New People", "New Status"]
        self.edit_vars = {}

        for i, label in enumerate(form_labels):
            self.create_edit_form_field(i + 1, label, window)

        self.create_edit_extras_section(window)

        self.update_booking_button = tk.Button(window, text="Update Booking", command=self.update_booking)
        self.update_booking_button.grid(row=10, column=0, columnspan=2, pady=10)

        window.columnconfigure(1, weight=1)

    def create_edit_form_field(self, row: int, label: str, window: tk.Toplevel) -> None:
        tk.Label(window, text=label).grid(row=row, column=0, sticky="e")
        if label in ["New Campsite", "New Status"]:
            self.edit_vars[label] = tk.StringVar()
            entry = ttk.Combobox(window, textvariable=self.edit_vars[label])
            entry['values'] = list(self.campsites.keys()) if label == "New Campsite" else ['Pending', 'Confirmed', 'Canceled']
        elif label in ["New Start Date", "New End Date"]:
            entry = DateEntry(window, date_pattern=DATE_PATTERN)
            self.edit_vars[label] = entry
        elif label == "New People":
            self.edit_vars[label] = tk.StringVar()
            entry = ttk.Combobox(window, textvariable=self.edit_vars[label])
            entry['values'] = [str(i) for i in range(1, 31)]
        else:
            self.edit_vars[label] = tk.StringVar()
            entry = tk.Entry(window, textvariable=self.edit_vars[label])
        entry.grid(row=row, column=1, pady=5, sticky="ew")
        entry.bind("<FocusOut>", self.validate_field)
        entry.bind("<KeyRelease>", self.validate_field)
        self.add_tooltip(entry, f"Enter new {label.split(' ')[1].lower()}")

    def create_edit_extras_section(self, window: tk.Toplevel) -> None:
        new_extras_frame = tk.LabelFrame(window, text="New Extras", padx=10, pady=10)
        new_extras_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")

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

        self.create_extras_option(new_extras_frame, "Portable Toilet ($70 for <10 people)", 'Portable Toilet', 0)
        self.create_extras_entry(new_extras_frame, "Fire Wood ($15 per 20 kg bag)", 'Fire Wood', 1)
        self.create_extras_entry(new_extras_frame, "Bag of Ice ($5 each)", 'Bag of Ice', 2)
        self.create_extras_entry(new_extras_frame, "1 Dozen Eggs ($8)", '1 Dozen Eggs', 3)
        self.create_extras_entry(new_extras_frame, "Honey ($13)", 'Honey', 4)
        self.create_extras_entry(new_extras_frame, "Breakfast Special ($20)", 'Breakfast Special', 5)
        self.create_extras_entry(new_extras_frame, "Meat Tray ($60)", 'Meat Tray', 6)
        self.create_extras_option(new_extras_frame, "Use of Kayaks", 'Kayaks', 7)
        self.create_extras_entry(new_extras_frame, "Number of Kayaks", 'Kayaks Count', 8)

        self.new_extras_paid_var = tk.BooleanVar()
        tk.Checkbutton(new_extras_frame, text="Extras Paid", variable=self.new_extras_paid_var).grid(row=9, column=0, columnspan=2, sticky="w")

    def update_booking(self) -> None:
        try:
            booking_id = self.booking_id_var.get()
            updated_data = {label: var.get() for label, var in self.edit_vars.items()}
            updated_data['New Start Date'] = pd.Timestamp(self.edit_vars['New Start Date'].get_date())
            updated_data['New End Date'] = pd.Timestamp(self.edit_vars['New End Date'].get_date())
            updated_data['New People'] = int(self.edit_vars['New People'].get() or 0)
            updated_data['New Kayaks'] = self.new_extras_vars['Kayaks'].get()
            updated_data['New Kayaks Count'] = int(self.new_extras_vars['Kayaks Count'].get() or 0)

            new_extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.new_extras_vars.items() if isinstance(var, tk.StringVar)}
            new_extras_booleans = {key: var.get() for key, var in self.new_extras_vars.items() if isinstance(var, tk.BooleanVar)}
            new_extras_paid = self.new_extras_paid_var.get()

            if not self.validate_updated_data(updated_data):
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

            if self.is_site_booked(updated_data['New Campsite'], updated_data['New Start Date'], updated_data['New End Date']):
                self.suggest_alternatives(updated_data, edit=True)
                return

            new_extras_cost = self.calculate_extras_cost(new_extras_data, new_extras_booleans, updated_data['New People'])
            new_extras_summary = ', '.join([f"{key} ({value})" for key, value in new_extras_data.items() if value] + [f"{key} (Yes)" for key, value in new_extras_booleans.items() if value])

            booking.name = updated_data['New Name']
            booking.phone = updated_data['New Phone']
            booking.email = updated_data['New Email']
            booking.campsite = updated_data['New Campsite']
            booking.start_date = updated_data['New Start Date']
            booking.end_date = updated_data['New End Date']
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
            self.clear_form_fields()
        except Exception as e:
            logging.error(f"Error in update_booking: {e}")
            messagebox.showerror("Error", "An error occurred while updating the booking. Please try again.")

    def validate_updated_data(self, updated_data: Dict[str, Any]) -> bool:
        if not (updated_data['New Name'] and updated_data['New Phone'] and updated_data['New Email'] and updated_data['New Campsite'] and updated_data['New Start Date'] and updated_data['New End Date'] and updated_data['New People']):
            messagebox.showerror("Input Error", "All fields are required.")
            return False

        if updated_data['New Start Date'] > updated_data['New End Date']:
            messagebox.showerror("Date Error", "End date must be after start date.")
            return False

        return True

    def delete_booking(self) -> None:
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

    def confirm_delete_booking(self) -> None:
        try:
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
                self.clear_form_fields()
        except Exception as e:
            logging.error(f"Error in confirm_delete_booking: {e}")
            messagebox.showerror("Error", "An error occurred while deleting the booking. Please try again.")

    def show_details(self) -> None:
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

    def display_details(self) -> None:
        campsite = self.details_campsite_var.get()
        if not campsite:
            messagebox.showerror("Input Error", "Campsite is required.")
            return

        details = pd.DataFrame([b.to_dict() for b in self.bookings if b.campsite == campsite])
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details.to_string(index=False))

    def show_day_bookings(self, date: str) -> None:
        day_window = tk.Toplevel(self.master)
        day_window.title(f"Bookings on {date}")
        day_window.geometry("500x400")

        day_text = tk.Text(day_window, width=50, height=20)
        day_text.pack(pady=10)

        day_date = pd.Timestamp(datetime.strptime(date, '%d/%m/%Y'))
        day_bookings = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date <= day_date and b.end_date >= day_date])
        if day_bookings.empty:
            day_text.insert(tk.END, "No bookings for this day.")
        else:
            day_text.insert(tk.END, day_bookings.to_string(index=False))

    def view_all_bookings(self) -> None:
        try:
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
        except Exception as e:
            logging.error(f"Error in view_all_bookings: {e}")
            messagebox.showerror("Error", "An error occurred while viewing all bookings. Please try again.")

    def search_bookings(self) -> None:
        try:
            search_window = tk.Toplevel(self.master)
            search_window.title("Search Bookings")
            search_window.geometry("300x200")

            tk.Label(search_window, text="Search by Name").grid(row=0, column=0, sticky="e")
            self.search_name_var = tk.StringVar()
            self.search_name_entry = tk.Entry(search_window, textvariable=self.search_name_var)
            self.search_name_entry.grid(row=0, column=1, pady=5, sticky="ew")

            tk.Label(search_window, text="Search by Date").grid(row=1, column=0, sticky="e")
            self.search_date_entry = DateEntry(search_window, date_pattern=DATE_PATTERN)
            self.search_date_entry.grid(row=1, column=1, pady=5, sticky="ew")

            self.search_button = tk.Button(search_window, text="Search", command=self.perform_search)
            self.search_button.grid(row=2, column=0, columnspan=2, pady=10)

            search_window.columnconfigure(1, weight=1)
        except Exception as e:
            logging.error(f"Error in search_bookings: {e}")
            messagebox.showerror("Error", "An error occurred while opening the search bookings window. Please try again.")

    def perform_search(self) -> None:
        try:
            name = self.search_name_var.get()
            date = self.search_date_entry.get_date()

            results = pd.DataFrame()
            if name:
                results = pd.DataFrame([b.to_dict() for b in self.bookings if name.lower() in b.name.lower()])

            if date:
                date_results = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date.date() <= date and b.end_date.date() >= date])
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
        except Exception as e:
            logging.error(f"Error in perform_search: {e}")
            messagebox.showerror("Error", "An error occurred while performing the search. Please try again.")

    def generate_report(self) -> None:
        try:
            report_window = tk.Toplevel(self.master)
            report_window.title("Generate Report")
            report_window.geometry("400x300")

            tk.Label(report_window, text="Start Date").grid(row=0, column=0, sticky="e")
            self.report_start_date_entry = DateEntry(report_window, date_pattern=DATE_PATTERN)
            self.report_start_date_entry.grid(row=0, column=1, pady=5, sticky="ew")

            tk.Label(report_window, text="End Date").grid(row=1, column=0, sticky="e")
            self.report_end_date_entry = DateEntry(report_window, date_pattern=DATE_PATTERN)
            self.report_end_date_entry.grid(row=1, column=1, pady=5, sticky="ew")

            self.generate_button = tk.Button(report_window, text="Generate", command=self.perform_generate_report)
            self.generate_button.grid(row=2, column=0, columnspan=2, pady=10)

            report_window.columnconfigure(1, weight=1)
        except Exception as e:
            logging.error(f"Error in generate_report: {e}")
            messagebox.showerror("Error", "An error occurred while opening the generate report window. Please try again.")

    def perform_generate_report(self) -> None:
        try:
            start_date = self.report_start_date_entry.get_date()
            end_date = self.report_end_date_entry.get_date()

            if start_date > end_date:
                messagebox.showerror("Date Error", "End date must be after start date.")
                return

            report_results = pd.DataFrame([b.to_dict() for b in self.bookings if b.start_date.date() >= start_date and b.end_date.date() <= end_date])

            if report_results.empty:
                messagebox.showinfo("Report Results", "No bookings found for the selected period.")
            else:
                self.display_report(report_results)
        except Exception as e:
            logging.error(f"Error in perform_generate_report: {e}")
            messagebox.showerror("Error", "An error occurred while generating the report. Please try again.")

    def display_report(self, data: pd.DataFrame) -> None:
        report_window = tk.Toplevel(self.master)
        report_window.title("Booking Report")
        report_window.geometry("900x700")

        report_text = tk.Text(report_window, width=700, height=500)
        report_text.pack(pady=10)

        for _, row in data.iterrows():
            booking_date = row['Start Date'].strftime('%d/%m/%y')
            campsite = row['Campsite']
            name = row['Name']
            phone = row['Phone']
            email = row['Email']
            people = row['People']
            nights = (row['End Date'] - row['Start Date']).days
            extras_str = row['Extras']
            extras_paid = 'y' if row['Extras Paid'] else 'n'

            line = f"{booking_date} - {campsite}, {name}, {phone}, {email}, {people} {'person' if people == 1 else 'people'}, {nights} {'night' if nights == 1 else 'nights'}, {extras_str}, Extras paid? {extras_paid}"

            report_text.insert(tk.END, line + "\n")

    def update_calendar(self) -> None:
        try:
            self.load_bookings(self.current_year, self.current_month)
            for widget in self.calendar_frame.winfo_children():
                if isinstance(widget, tk.Button):
                    date = widget.cget("text").split("\n")[0]
                    day_str = f"{int(date):02d}/{self.current_month:02d}/{self.current_year}"
                    bookings = self.get_booking_text_for_date(day_str)
                    if bookings:
                        widget.config(text=f"{date}\n{bookings}", anchor='n')
                        widget.config(background='red')
                    else:
                        widget.config(background='green')
        except Exception as e:
            logging.error(f"Error in update_calendar: {e}")
            messagebox.showerror("Error", "An error occurred while updating the calendar. Please try again.")

    def is_date_booked(self, date: str) -> bool:
        try:
            date = pd.Timestamp(datetime.strptime(date, '%d/%m/%Y'))
            for booking in self.bookings:
                if booking.start_date <= date <= booking.end_date:
                    return True
            return False
        except Exception as e:
            logging.error(f"Error in is_date_booked: {e}")
            messagebox.showerror("Error", "An error occurred while checking date availability. Please try again.")
            return False

    def validate_field(self, event: tk.Event) -> None:
        widget = event.widget
        if isinstance(widget, DateEntry):
            date_str = widget.get()
            try:
                datetime.strptime(date_str, DATE_PATTERN)
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

    def add_tooltip(self, widget: tk.Widget, text: str) -> None:
        tooltip = Tooltip(widget, text)
        widget.bind("<Enter>", tooltip.show)
        widget.bind("<Leave>", tooltip.hide)

    def update_extras_cost(self, event: tk.Event = None) -> None:
        try:
            extras_data = {key: (int(var.get()) if var.get().isdigit() else 0) for key, var in self.extras_vars.items() if isinstance(var, tk.StringVar)}
            extras_booleans = {key: var.get() for key, var in self.extras_vars.items() if isinstance(var, tk.BooleanVar)}
            people = int(self.form_vars['People'].get() or 0)
            extras_cost = self.calculate_extras_cost(extras_data, extras_booleans, people)
            self.extras_cost_label.config(text=f"Extras Cost: ${extras_cost}")
        except Exception as e:
            logging.error(f"Error in update_extras_cost: {e}")
            messagebox.showerror("Error", "An error occurred while updating extras cost. Please try again.")

    def clear_form_fields(self) -> None:
        for var in self.form_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, DateEntry):
                var.set_date(datetime.now())
        for var in self.extras_vars.values():
            if isinstance(var, tk.StringVar):
                var.set("")
            elif isinstance(var, tk.BooleanVar):
                var.set(False)
        self.extras_paid_var.set(False)
        self.group_booking_var.set(False)

class Tooltip:
    def __init__(self, widget: tk.Widget, text: str):
        self.widget = widget
        self.text = text
        self.tip_window = None

    def show(self, event: tk.Event) -> None:
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

    def hide(self, event: tk.Event) -> None:
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = BookingManager(master=root)
    root.mainloop()
