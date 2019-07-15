import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog, scrolledtext
import random
import datetime
import os
import platform
import re
import pickle
import prettytable
import traceback

from load_csv import Data, convert_to_date

# TODO
# calender date select with dropdown menu
# Funktion "Kassen bearbeiten" und Einträge (consumables)
# User Inputs überprüfen auf Richtigkeit (regex) (?)
# Sortierungsmöglichkeiten für ausgedruckte Listen
# und Listen im Notebook
# Scrollbar im "edit_consumables"
# Funktion "Kassenstände ausdrucken" unter Inventur
# Kasse anlegen
# noch zu tun:
## Kassen entfernen bzw. archivieren



# internal settings
DEBUG = False
TOOLTIP_DELAY = 800 # milliseconds

INFO_TXT = ('Kaffeeliste - Ein Programm zum Verwalten der Kaffeekasse\n' +
            'Version 0.2\n' +
            '© Christian Post 2019')


def error(number, *args):
    error_dict = {
            0: 'FEHLER: Bitte einen Namen eingeben.',
            1: 'ACHTUNG: Es wurden Änderungen nicht gespeichert. Trotzdem beenden?',
            2: 'FEHLER: Datei nicht gefunden',
            3: 'FEHLER: Ungültiger Wert',
            4: 'FEHLER: Datei nicht im CSV-Format.',
            5: 'FEHLER: Datei konnte nicht gelesen werden.',
            6: 'ACHTUNG: Dies wird {} archivieren. Fortfahren?',
            7: 'ACHTUNG: Dies wird {} wiederherstellen. Fortfahren?',
            8: 'FEHLER: Name "{}" ist zu kurz.',
            9: 'FEHLER: "{}" enthält unzulässige Zeichen.',
            10: 'FEHLER: "{}" ist kein gültiges Datum.',
            11: 'FEHLER: Ungültiger Wert "{}".',
            12: 'FEHLER: Bitte einen {} angeben.',
            13: 'FEHLER: Name "{}" ist zu lang (max. {} Zeichen).',
            14: 'Soll der Eintrag\n{}\nwirklich gelöscht werden?',
            15: 'FEHLER: Kein Mitarbeiter mit ID {} gefunden (eventuell archiviert oder gelöscht).',
            16: 'ACHTUNG: Keine Mitarbeiter zum Bearbeiten vorhanden.',
            17: 'FEHLER: Ein oder mehrere Mitarbeiter konnten nicht gefunden werden.',
            18: 'ACHTUNG: Keine Einträge zum Bearbeiten gefunden.',
            19: 'FEHLER: Die Datei "{}" enthält nicht alle erforderlichen Spalten.'
            }
    try:
        return error_dict[number].format(*args)
    except KeyError:
        traceback.print_exc()
        return 'something went wrong'


def tooltip(name, *args):
    ttp_dict = {
            'backup_interval': 'Anzahl der Tage, nachdem die Daten im Ordner '
                                + '"backup" gesichert werden.',
            'coffee_factor': 'Der Wert eines Striches auf der Strichliste. ' 
                            + '1 Strich = kleine Tasse, 2 Striche = große Tasse.',
            'debug_mode': 'Im aktiven Debug-Mode werden keine Änderungen gespeichert, '
                          + 'selbst wenn die Funktion "Änderungen speichern" '
                          + 'ausgeführt wird.'
            }
    try:
        return ttp_dict[name].format(*args)
    except KeyError:
        traceback.print_exc()
        return 'something went wrong'


def euro(number):
    return f'{number:.2f} €'.replace('.',',')


def euro_to_float(string):
    return float(string[:-2].replace(',', '.'))


def date_s(date):
    # accepts datetime, returns formatted string
    return str(date.strftime("%d.%m.%Y"))


def date_f(date_string):
    # accepts string, returns datetime
    try:
        return datetime.datetime.strptime(date_string, '%d.%m.%Y').date()
    except:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()


def today(long=True):
    if long:
        return str(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
    else:
        return str(datetime.datetime.now().strftime("%d.%m.%Y"))
    

def is_allowed_letters(string, spaces=False, numbers=False):
    charset = '^a-zA-ZäÄöÖüÜß'
    if spaces:
        charset += '\s_\-'
    if numbers:
        charset += '0-9'
    #print(charset)
    charRe = re.compile(r'[' + charset + ']')
    string = charRe.search(string)
    return not bool(string)


def capitalize_first(string):
    try:
        return f'{string[0].upper()}{string[1:]}'
    except IndexError:
        return ''


def on_resize(event):
    print((event.width, event.height))

    

cash_name = {
        'coffee': 'Kaffeekasse',
        'special': 'Sonderkasse',
        'party': 'Feierkasse'
        }



class App(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master = master
        self.staff_members = []
        self.staff_archive = []
        self.generated_IDs = []
        self.consumables = []
        self.tally_entries = {} # {Date: list with [Name, tally amount]} #TODO import previous entries for statistics
        
        self.debug_mode = DEBUG # wenn True, wird nichts in der Datei gespeichert
        self.tag = 0 # index for text widget style tags
        
        self.cashes = {
                'coffee': 0,
                'special': 0,
                'party': 0
                }
        
        # data structure for payments to the other cashes
        self.payments = {
                'special': [],
                'party': []
                }
        
        self.config = {
                'coffee_factor': 0.1,
                'tally_list_empty': 6,
                'on_tally_list': [1 for s in self.staff_members],
                'backup_interval': 14
                }
        
        self.saved = True
        
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.save_data_filename = os.path.join(self.path, 'coffee_data.dat')
        self.log_filename = os.path.join(self.path, 'log.txt')
        
        # make folder for exported csv files
        self.csv_folder = os.path.join(self.path, 'exported_csv')
        if not os.path.isdir(self.csv_folder):
            os.mkdir(self.csv_folder)
            
        # make folder for temporary html files for printing
        self.temp_folder = os.path.join(self.path, 'temp')
        if not os.path.isdir(self.temp_folder):
            os.mkdir(os.path.join(self.path, 'temp'))
        
        # check for existing save data
        if os.path.isfile(self.save_data_filename):
            # load data from coffee_data.dat
            self.load_data()
            
            # check if backup folder exists
            self.backup_folder = os.path.join(self.path, 'backup')
            if not os.path.isdir(self.backup_folder):
                os.mkdir(os.path.join(self.path, 'backup'))
            
            # check for existing backup files
            files = os.listdir(self.backup_folder)
            # get a list with filenames matching the pattern
            backup_files = list(filter(lambda x: re.search('data_backup_[0-9]{8}\.dat', x), files))
            # extract the dates from all backup files
            timestamps = sorted([fname[12:20] for fname in backup_files], reverse=True)
            if timestamps:
                # get date from most recent file
                recent_date = datetime.datetime.strptime(timestamps[0], '%Y%m%d')
                timedelta = datetime.datetime.now() - recent_date
                if timedelta.days > self.config['backup_interval']:
                    #print(timedelta)
                    # create backup file
                    fname = f'data_backup_{datetime.datetime.today().strftime("%Y%m%d")}.dat'
                    self.save_data(os.path.join(self.backup_folder, fname))
            else:
                # if no backup files exist, create one
                fname = f'data_backup_{datetime.datetime.today().strftime("%Y%m%d")}.dat'
                self.save_data(os.path.join(self.backup_folder, fname))
        
        # check for existing log file    
        if not os.path.isfile(self.log_filename):
            with open(self.log_filename, 'w') as file:
                file.write('')
        
        self.init_window()
        
        #self.consumables_from_file('exported_csv/Ein_und_Auszahlungen.csv')
        #self.staff_from_file('exported_csv/staff.csv')
        #self.payments_from_file('exported_csv/geldeingang.csv')

        
        self.update_tabs()
        
        if self.debug_mode:
            self.println('<<ACHTUNG>>: DEBUG MODE AKTIV. ÄNDERUNGEN WERDEN NICHT GESPEICHERT!',
                         color='red')
        
    
    def init_window(self):
        self.master.title('Kaffeeliste')
        
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)

        # Menüstruktur

        self.file_menu = tk.Menu(self.menu, tearoff=False)
        self.file_menu.add_command(label='Änderungen speichern', 
                                   command=lambda: self.save_data(self.save_data_filename))
        self.file_menu.add_separator()
        
        self.file_submenu3 = tk.Menu(self.file_menu, tearoff=False)
        self.file_submenu3.add_command(label='Kasse', 
                                      command=self.add_cashes)
        self.file_menu.add_cascade(label='Neu', menu=self.file_submenu3)
        
        self.file_submenu = tk.Menu(self.file_menu, tearoff=False)
        self.file_submenu.add_command(label='Mitarbeiterliste', 
                                      command=self.export_staff_data)
        self.file_submenu.add_command(label='Geldein-/ausgang Personal', 
                                      command=self.export_payments)
        self.file_submenu.add_command(label='Geldein-/ausgang Material', 
                                      command=self.export_consumables)
        self.file_submenu.add_command(label='Kassenstände', 
                                      command=self.export_cash_balances)
        self.file_menu.add_cascade(label='Exportieren', menu=self.file_submenu)
        
        self.file_submenu_2 = tk.Menu(self.file_menu, tearoff=False)
        self.file_submenu_2.add_command(label='Mitarbeiterliste', 
                                        command=self.open_load_staff_data)
        self.file_submenu_2.add_command(label='Geldein-/ausgang Personal', 
                                        command=self.open_load_payments)
        self.file_submenu_2.add_command(label='Geldein-/ausgang Material', 
                                        command=self.open_load_consumables)
        self.file_submenu_2.add_command(label='Kassenstände', 
                                        command=None)
        self.file_menu.add_cascade(label='Importieren', menu=self.file_submenu_2)
        self.file_menu.add_separator()
        
        self.file_menu.add_command(label='Einstellungen', 
                                   command=self.set_preferences)
        self.file_menu.add_command(label='test function (debugging)', 
                                   command=self.test_function, state='disabled')
        self.file_menu.add_command(label='Beenden', 
                                   command=self.client_exit)
        self.menu.add_cascade(label='Datei', 
                              menu=self.file_menu)
        
        # Menü für Personal bearbeiten
        self.staff_menu = tk.Menu(self.menu, tearoff=False)
        self.staff_menu.add_command(label='Hinzufügen', 
                                    command=self.add_staff)
        self.staff_menu.add_command(label='Liste bearbeiten', 
                                    command=self.edit_staff)
        self.staff_menu.add_command(label='Archiv', 
                                    command=self.edit_archive)
        self.staff_menu.add_separator()
        self.staff_menu.add_command(label='Statistiken', 
                                    command=None)
        self.menu.add_cascade(label='Personal', 
                              menu=self.staff_menu)
        
        # Menü für Geldbewegungen
        self.payment_menu = tk.Menu(self.menu, tearoff=False)
        self.payment_submenu = tk.Menu(self.payment_menu, tearoff=False)
        self.payment_submenu.add_command(label='Mitarbeiter', 
                                         command=self.enter_payment)
        self.payment_submenu.add_command(label='Verbrauchsmaterial', 
                                         command=self.enter_material)
        for key, value in self.cashes.items():
            if key != 'coffee':
                self.payment_submenu.add_command(label=cash_name[key], 
                                           command=lambda x=key: self.enter_cash(x))
                
        self.payment_menu.add_cascade(label='Eintrag', menu=self.payment_submenu)
        
        self.payment_submenu_2 = tk.Menu(self.payment_menu, tearoff=False)
        self.payment_submenu_2.add_command(label='Mitarbeiter', 
                                         command=self.edit_payments)
        self.payment_submenu_2.add_command(label='Verbrauchsmaterial', 
                                         command=self.edit_material)
        self.payment_submenu_2.add_command(label='Kassen', 
                                           command=None) #TODO: edit cashes
                
        self.payment_menu.add_cascade(label='Bearbeiten', menu=self.payment_submenu_2)
        
        self.payment_menu.add_separator()
        
        self.payment_menu.add_command(label='Inventur', 
                                      command=self.cashes_inventory)
        self.menu.add_cascade(label='Geldein-/ausgang', menu=self.payment_menu)
        
        # Menü für Einträge Striche
        self.tally_menu = tk.Menu(self.menu, tearoff=False)
        self.tally_menu.add_command(label='Eintrag', 
                                    command=self.enter_tally)
        self.tally_menu.add_command(label='Aus Datei...', 
                                    command=self.open_load_tally)
        self.menu.add_cascade(label='Striche', menu=self.tally_menu)
        
        # Menü für Drucken von Listen und Aushängen
        self.print_menu = tk.Menu(self.menu, tearoff=False)
        self.print_menu.add_command(label='Strichliste', 
                                  command=self.print_tally_table)
        self.print_menu.add_command(label='Kontostand', 
                                  command=self.print_balance)
        self.print_menu.add_command(label='Geldein-/ausgänge',
                                  command=self.print_payments)
        self.print_menu.add_separator()
        self.print_submenu = tk.Menu(self.print_menu, tearoff=False)
        self.print_submenu.add_command(label='Strichliste',
                                       command=self.configure_tally_list)
        self.print_submenu.add_command(label='Kontostand', 
                                       command=None)
        self.print_menu.add_cascade(label='Konfigurieren', menu=self.print_submenu)
        
        self.menu.add_cascade(label='Drucken', menu=self.print_menu)
        
        # Hilfe
        self.help_menu = tk.Menu(self.menu, tearoff=False)
        self.help_menu.add_command(label='Dokumentation', 
                                    command=None)
        self.help_menu.add_command(label='Über', 
                                   command=lambda: messagebox.showinfo('Info', 
                                                                       INFO_TXT))
        self.menu.add_cascade(label='Hilfe', menu=self.help_menu)

        #place a Notebook (tabs)
        self.nb = ttk.Notebook(self.master)
        self.nb.pack(fill=tk.BOTH, expand=True)
        
        # Adds main tab to the notebook
        self.page_main = ttk.Frame(self.nb)
        self.nb.add(self.page_main, text='Konsole')
        #place text widget
        self.console_txt = scrolledtext.ScrolledText(self.page_main)
        # disable text editing by user
        self.console_txt.bind('<Key>', lambda e: 'break')
        self.console_txt.pack(fill=tk.BOTH, expand=True)
        
        # Mitarbeiter-Übersicht
        self.staff_info = ttk.Frame(self.nb)
        self.nb.add(self.staff_info, text='Personal')
        
        self.staff_txt = scrolledtext.ScrolledText(self.staff_info)
        # disable text editing by user
        self.staff_txt.bind('<Key>', lambda e: 'break')
        self.staff_txt.pack(fill=tk.BOTH, expand=True)
        
        # Übersicht über Kassenstände
        self.cashes_info = ttk.Frame(self.nb)
        self.nb.add(self.cashes_info, text='Übersicht über Zahlungen')
        
        self.cashes_txt = scrolledtext.ScrolledText(self.cashes_info)
        # disable text editing by user
        self.cashes_txt.bind('<Key>', lambda e: 'break')
        self.cashes_txt.pack(fill=tk.BOTH, expand=True)
        
    
    def set_preferences(self):
        self.popup_preferences = EditPreferencesWindow(self, self.master)
        self.master.wait_window(self.popup_preferences.top)
        self.update_tabs()
        
    
    def add_cashes(self):
        self.popup_add_cash = AddCashWindow(self, self.master)
        self.master.wait_window(self.popup_add_cash.top)
        self.update_tabs()
        
    
    def add_staff(self):
        self.popup_add_staff = PopupStaff(self, self.master)
        self.master.wait_window(self.popup_add_staff.top)
        self.update_tabs()
        
    
    def edit_staff(self):
        if len(self.staff_members) == 0:
            messagebox.showinfo('Achtung', error(16))
            self.println(error(16))
            return
        self.popup_edit_staff = EditStaffWindow(self, self.master, 'edit')
        self.master.wait_window(self.popup_edit_staff.top)
        self.update_tabs()
        
    
    def edit_archive(self):
        if len(self.staff_archive) == 0:
            messagebox.showinfo('Achtung', error(16))
            self.println(error(16))
            return
        self.popup_edit_archive = EditStaffWindow(self, self.master, 'archive')
        self.master.wait_window(self.popup_edit_archive.top)
        self.update_tabs()
        
    
    def enter_payment(self):
        if len(self.staff_members) == 0:
            messagebox.showinfo('Achtung', error(16))
            self.println(error(16))
            return
        self.popup_add_payment = EnterPaymentWindow(self, self.master)
        self.master.wait_window(self.popup_add_payment.top)
        self.update_tabs()
    
    
    def edit_payments(self):
        pass
# =============================================================================
#         self.popup_add_payment = EditPaymentWindow(self, self.master)
#         self.master.wait_window(self.popup_add_payment.top)
#         self.update_tabs()
# =============================================================================
        
    
    def enter_tally(self):
        if len(self.staff_members) == 0:
            messagebox.showinfo('Achtung', error(16))
            self.println(error(16))
            return
        self.popup_enter_tally = EnterTallyWindow(self, self.master)
        self.master.wait_window(self.popup_enter_tally.top)
        self.update_tabs()
        
    
    def enter_material(self):
        self.popup_enter_material = EnterMaterialWindow(self, self.master)
        self.master.wait_window(self.popup_enter_material.top)
        self.update_tabs()
        
        
    def enter_cash(self, name):
        self.popup_enter_cash = EnterCashWindow(self, self.master, name)
        self.master.wait_window(self.popup_enter_cash.top)
        self.update_tabs()
        
    
    def edit_cash(self, name):
        pass
# =============================================================================
#         self.popup_enter_cash = EditCashWindow(self, self.master, name)
#         self.master.wait_window(self.popup_enter_cash.top)
#         self.update_tabs()
# =============================================================================
    
    
    def edit_material(self):
        if len(self.consumables) == 0:
            messagebox.showinfo('Achtung', error(18))
            self.println(error(18))
            return
        self.popup_edit_material = MaterialListWindow(self, self.master)
        self.master.wait_window(self.popup_edit_material.top)
        self.update_tabs()
        
    
    def cashes_inventory(self):
        self.popup_inventory = CashesInventoryWindow(self, self.master)
        self.master.wait_window(self.popup_inventory.top)
        self.update_tabs()
                
    
    def open_load_staff_data(self):
        f = filedialog.askopenfilename(initialdir=self.csv_folder,
                                       title="Datei mit Mitarbeitern auswählen",
                                       filetypes=(("CSV-Dateien","*.csv"),("all files","*.*")))
        if f:
            self.staff_from_file(f)
            self.update_tabs()
            
    
    def open_load_tally(self):
        f = filedialog.askopenfilename(initialdir=self.csv_folder,
                                       title="Datei für Striche auswählen",
                                       filetypes=(("CSV-Dateien","*.csv"),("all files","*.*")))
        if f:
            self.tally_entry_from_file(f)
            self.update_tabs()
    
    
    def open_load_payments(self):
        f = filedialog.askopenfilename(initialdir=self.csv_folder,
                                       title="Datei mit Bezahlungen auswählen",
                                       filetypes=(("CSV-Dateien","*.csv"),("all files","*.*")))
        if f:
            self.payments_from_file(f)
            self.update_tabs()
    
    
    def open_load_consumables(self):
        f = filedialog.askopenfilename(initialdir=self.csv_folder,
                                       title="Datei mit Verbrauchsmaterial auswählen",
                                       filetypes=(("CSV-Dateien","*.csv"),("all files","*.*")))
        if f:
            self.consumables_from_file(f)
            self.update_tabs()
    
    
    def export_staff_data(self):
        export_data = []
        init_fname = f'Mitarbeiter_{datetime.datetime.today().strftime("%Y%m%d")}.csv'
        filename = filedialog.asksaveasfilename(initialdir=self.csv_folder,
                                                initialfile=init_fname,
                                                title="Datei auswählen",
                                                filetypes=(("CSV-Dateien","*.csv"),
                                                           ("all files","*.*")),
                                                defaultextension='.csv')
        if not filename:
            return
        
        for s in self.staff_members:
            s.calculate_balance(self.config['coffee_factor'])
            export_data.append([s.id, s.firstname, s.lastname, s.initial_balance, 
                                s.coffee_sum, s.balance, s.credit, s.debit, False])
        for s in self.staff_archive:
            s.calculate_balance(self.config['coffee_factor'])
            export_data.append([s.id, s.firstname, s.lastname, s.initial_balance, 
                                s.coffee_sum, s.balance, s.credit, s.debit, True])
        
        df = Data(export_data, columns=['id', 'firstname', 'lastname',
                                        'initial_balance', 'coffee_sum', 'balance',
                                        'credit', 'debit', 'archive'])
        df.write_csv(filename)
        self.println(f'Daten exportiert nach {filename}')
        
    
    def export_payments(self):
        export_data = []
        init_fname = f'Geldeingang_{datetime.datetime.today().strftime("%Y%m%d")}.csv'
        filename = filedialog.asksaveasfilename(initialdir=self.csv_folder,
                                                initialfile=init_fname,
                                                title="Datei auswählen",
                                                filetypes=(("CSV-Dateien","*.csv"),
                                                           ("all files","*.*")),
                                                defaultextension='.csv')
        if not filename:
            return
        
        for s in self.staff_members + self.staff_archive:
            for p in s.payments:
                export_data.append([s.id, s, convert_to_date(p[0]), p[1]]) # TODO: temporärer fix
        
        df = Data(export_data, columns=['id', 'name', 'date', 'payment'])
        df.write_csv(filename)
        self.println(f'Daten exportiert nach {filename}')
    
    
    def export_consumables(self):
        export_data = []
        init_fname = f'Verbrauchsmaterial_{datetime.datetime.today().strftime("%Y%m%d")}.csv'
        filename = filedialog.asksaveasfilename(initialdir=self.csv_folder,
                                                initialfile=init_fname,
                                                title="Datei auswählen",
                                                filetypes=(("CSV-Dateien","*.csv"),
                                                           ("all files","*.*")),
                                                defaultextension='.csv')
        if not filename:
            return
        
        for c in self.consumables:
            export_data.append([c.id, c.name, c.date, c.amount, c.cost, 
                                c.buyer, c.paid])
        
        df = Data(export_data, columns=['id', 'name', 'date', 'amount', 'cost',
                                        'buyer', 'paid'])
        df.write_csv(filename)
        self.println(f'Daten exportiert nach {filename}')
        
    
    def export_cash_balances(self):
        init_fname = f'Kassenstände_{datetime.datetime.today().strftime("%Y%m%d")}.csv'
        filename = filedialog.asksaveasfilename(initialdir=self.csv_folder,
                                                initialfile=init_fname,
                                                title="Datei auswählen",
                                                filetypes=(("CSV-Dateien","*.csv"),
                                                           ("all files","*.*")),
                                                defaultextension='.csv')
        if not filename:
            return

        with open(filename, 'w') as f:
            txt = f'{today(long=False)}\n'
            for index, value in self.cashes.items():
                txt += f'{index};{str(value).replace(".", ",")}\n'
            f.write(txt)
            
        self.println(f'Kassenstände exportiert nach {filename}')
        
    
    def print_balance(self):
        if len(self.staff_members) == 0:
            self.println('Kontostand wurde nicht erstellt. Keine Mitarbeiter vorhanden.')
            return
        d = []
        date_string = f'Bis {datetime.datetime.today().strftime("%d.%m.%Y")}'
        
        for s in self.staff_members:
            debit = s.balance * -1 if s.balance < 0 else 0
            credit = s.balance if s.balance >= 0 else 0
            d.append([s, debit, credit])
        
        df = Data(d, columns=['Name', 'bezahlen', 'Guthaben'])

        # specify CSS formatting
        table_css = [
            'table {border-collapse: collapse;}',
            'table, th, td {border: 1px solid black;}',
            'th, td {text-align: left; padding: 2px 2px 2px 2px;}',
            'td {height: 24px;}',
            'caption {text-align: left; padding: 10px; font-weight: bold;}'
            ]
        value_format = {'bezahlen': euro, 'Guthaben': euro}
        column_format = {'bezahlen': 'width=100px;',
                         'Guthaben': 'width=100px;'}
        align = {'bezahlen': 'right', 'Guthaben': 'right'}
        
        filename = os.path.join(self.temp_folder, 'Kontostand.html')
        
        df.to_html(filename, format_values=value_format, 
                   format_columns=column_format, css=table_css,
                   column_align=align, caption=date_string)
        
        self.println(f'Beiträgeliste zum Druck exportiert nach {filename}')
        
        # Öffnet Datei im Browser
        import webbrowser
        webbrowser.open(filename)
        
    
    def print_tally_table(self):
        d = []
        date_string = f'ab dem {today(long=False)}'
        
        for index, s in enumerate(self.staff_members):
            if self.config['on_tally_list'][index]:
                if s.lastname != '':
                    string = f'{s.firstname} {s.lastname[0]}.'
                else:
                    string = s.firstname
                d.append([string, ''])
        
        # leere Zeilen ans Ende
        for i in range(self.config['tally_list_empty']):
            d.append(['', ''])
        
        df = Data(d, columns=['Name', date_string])
        
        # specify CSS formatting
        table_css = [
            'table {border-collapse: collapse;}',
            'table, th, td {border: 2px solid black;}',
            'th, td {text-align: left; padding: 2px 4px 2px 2px;}', # top right bottom left
            'td {height: 24px;}'
            ]
        column_format = {date_string: 'width=800px;'}
        
        filename = os.path.join(self.temp_folder, 'Strichliste.html')
        self.println(f'Strichliste zum Druck exportiert nach {filename}')
        df.to_html(filename, format_columns=column_format, css=table_css)
                
        # Öffnet Datei im Browser
        import webbrowser
        webbrowser.open(filename)
        
    
    def print_payments(self):
        d = []
        date_string = f'Geldein-/ausgänge bis zum {today(long=False)}'
        
        # struktur: | Datum | Kasse | Zweck | Name | Betrag |
        
        # Sonder- und Feierkasse
        for index, value in self.payments.items():
            for p in self.payments[index]:
                d.append([p[0], cash_name[index], p[2], ' - ', p[1]])
        
        # Mitarbeiter
        for s in self.staff_members + self.staff_archive:
            for p in s.payments:
                purpose = 'Einzahlung' if p[1] > 0 else 'Auszahlung'
                d.append([p[0], cash_name['coffee'], purpose, 
                          s, p[1]])
        
        # Materialien
        for c in self.consumables:
            d.append([c.date, cash_name['coffee'], 'Verbrauchsmaterial', 
                      f'{c.name} x{c.amount}', c.cost * -1])
        
        df = Data(d, columns=['Datum', 'Kasse', 'Zweck', 
                              'Name/Gegenstand', 'Betrag'])
        
        if len(df.data) == 0:
            self.println('Übersicht wurde nicht erstellt. Keine Einträge vorhanden.')
            return
        
        df.sort(by='Datum', reverse=True)
        
        # specify CSS formatting
        table_css = [
            'table {border-collapse: collapse;}',
            'table, th, td {border: 2px solid black;}',
            'th, td {text-align: left; padding: 2px 10px 2px 10px;}',
            'td {height: 24px;}',
            'caption {text-align: left; padding: 10px; font-weight: bold;}'
            ]
        value_format = {'Betrag': euro, 'Datum': date_s}
        align = {'Betrag': 'right'}
        
        filename = os.path.join(self.temp_folder, 'Ein_und_Auszahlungen.html')
        df.to_html(filename, format_values=value_format, css=table_css,
                   column_align=align, caption=date_string)
        self.println(f'Geldein-/ausgänge zum Druck exportiert nach {filename}')
        
        # Öffnet Datei im Browser
        import webbrowser
        webbrowser.open(filename)
    
    
    def configure_tally_list(self):
        self.popup_configure_tally = ConfigureTallyListWindow(self, self.master)
        self.master.wait_window(self.popup_configure_tally.top)
        
        
    
    def println(self, text, window=None, color=None):
        if window == None:
            window = self.console_txt
        if window == self.console_txt:
            text = f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")} {str(text)}'
        else:
            text = str(text)
        # prints text to the console notebook tab
        window.insert(tk.END, text + '\n')
        if color:
            try:
                rows = len(window.get('1.0', tk.END).splitlines()) - 1
                tag = f'tag_{self.tag}'
                self.tag += 1
                window.tag_add(tag, f'{rows}.0', f'{rows}.{len(text)}')
                window.tag_config(tag, foreground=color)
            except tk.TclError:
                traceback.print_exc()
                #print(f'Error: "{color}" is not a valid color.')
        # automatically jump to the bottom of the text window
        window.see(tk.END)
    
    
    def save_data(self, file):
        if self.debug_mode:
            return
        #file = self.save_data_filename
        data = {'staff_members': self.staff_members,
                'staff_archive': self.staff_archive,
                'consumables': self.consumables,
                'generated_IDs': self.generated_IDs,
                'config': self.config,
                'cashes': self.cashes,
                'payments': self.payments
                }
        with open(file, 'wb') as f:
            pickle.dump(data, f)
        
        self.saved = True
        if hasattr(self, 'console_txt'):
            self.println('Änderungen erfolgreich gespeichert.')
            
    
    def load_data(self):
        file = self.save_data_filename
        with open(file, 'rb') as f:
            data = pickle.load(f)
            
        for key, value in data.items():
            setattr(self, key, value)
            
    
    def create_staff_table(self, members):
        # Tabellen erstellen für den Mitarbeiter Tab
        staff_table = prettytable.PrettyTable()
        staff_table.field_names = ['Name', 'Saldo', 'Striche', 
                                        'bezahlen', 'Guthaben']
        
        sum_balance, sum_tally, sum_debit, sum_credit = 0, 0, 0, 0
        for row, staff in enumerate(members):
            staff.calculate_balance(self.config['coffee_factor'])
            debit = staff.balance * -1 if staff.balance < 0 else 0
            credit = staff.balance if staff.balance >= 0 else 0
            staff_table.add_row([staff, euro(staff.balance), staff.coffee_sum, 
                                      euro(debit), euro(credit)])
            sum_balance += staff.balance
            sum_tally += staff.coffee_sum
            sum_debit += debit
            sum_credit += credit
        staff_table.add_row(['','','','',''])
        staff_table.add_row(['Summe', euro(sum_balance), sum_tally, 
                                  euro(sum_debit), euro(sum_credit)])
            
        staff_table.align = 'r'
        staff_table.align['Name'] = 'l'
        
        return staff_table
    
    
    def format_table(self, table, members, start_row):
        # Saldo formatieren (positiv grün, negativ rot)
        # im Mitarbeiter Tab
        if len(members) == 0:
            return
        start_col = table._widths[0] + 5
        end_col = start_col + table._widths[1]
        for row, staff in enumerate(members):
            start = f'{row + start_row}.{start_col}'
            end = f'{row + start_row}.{end_col}'
            self.staff_txt.tag_add(f'red_{row + start_row}', start, end)
            if staff.balance >= 0:
                self.staff_txt.tag_config(f'red_{row + start_row}', foreground='green')
            else:
                self.staff_txt.tag_config(f'red_{row + start_row}', foreground='red')
        # Saldo gesamt formatieren
        start = f'{row + start_row + 2}.{start_col}'
        end = f'{row + start_row + 2}.{end_col}'
        self.staff_txt.tag_add(f'red_end_{members}', start, end)
        color = 'green' if euro_to_float(table._rows[-1][1]) >= 0 else 'red'
        self.staff_txt.tag_config(f'red_end_{members}', foreground=color)
    
        
    
    def update_tabs(self):
        try:
            #  ------------- Mitarbeiter Tab ----------------------------------
            # clear all previous text
            self.staff_txt.delete('1.0', tk.END)
            # create table from staff data
            self.println('\nAktive Mitarbeiter', self.staff_txt)
            self.staff_table = self.create_staff_table(self.staff_members)
            self.println(self.staff_table, self.staff_txt)
            self.format_table(self.staff_table, self.staff_members, 6)
                
            self.println('\nArchivierte Mitarbeiter', self.staff_txt)
            self.archive_table = self.create_staff_table(self.staff_archive)
            self.println(self.archive_table, self.staff_txt)
            self.format_table(self.archive_table, self.staff_archive, 14 + len(self.staff_members))
            self.staff_txt.see('1.0') # jump to top again
    
            
            # ----- Kassenstände und Zahlungen Tab ----------------------------
            self.cashes_txt.delete('1.0', tk.END)
            
            cashes_table = prettytable.PrettyTable()
            cashes_table.field_names = ['Kasse', 'Stand']
            for key, value in self.cashes.items():
                cashes_table.add_row([cash_name[key], euro(value)])
            
            self.println('\nKassenstände', self.cashes_txt)
            self.println(cashes_table, self.cashes_txt)
            
            # Saldo Formatieren
            start_row = 6
            start_col = cashes_table._widths[0] + 5
            end_col = start_col + cashes_table._widths[1]
            for row, cash in enumerate(self.cashes.keys()):
                start = f'{row + start_row}.{start_col}'
                end = f'{row + start_row}.{end_col}'
                self.cashes_txt.tag_add(f'red_{row + start_row}', start, end)
                color = 'green' if self.cashes[cash] >= 0 else 'red'
                self.cashes_txt.tag_config(f'red_{row + start_row}', foreground=color)
            
            self.payments_table = prettytable.PrettyTable()
            self.payments_table.field_names = ['Datum', 'Name', 'Betrag']
            
            payments = []
            
            for staff in self.staff_members:
                for payment in staff.payments:
                    payments.append([payment[0], str(staff), euro(payment[1])])
            payments = sorted(payments, key=lambda x: x[0], reverse=True)
            
            for p in payments:
                p[0] = p[0].strftime('%d.%m.%Y')
                self.payments_table.add_row(p)
            
            self.payments_table.align['Name'] = 'l'
            self.payments_table.align['Betrag'] = 'r'
            
            self.println('\nZahlungen der Mitarbeiter', self.cashes_txt)
            self.println(self.payments_table, self.cashes_txt)
            
            
            self.material_table = prettytable.PrettyTable()
            self.material_table.field_names = ['Datum', 'Verwendungszweck', 'Menge', 
                                               'Betrag', 'gekauft von', 'ausgezahlt']
            
            sum_ = 0
            for row, c in enumerate(sorted(self.consumables, key=lambda x: x.date,
                                           reverse=True)):
                row = []
                for col, label in enumerate(['date', 'name', 'amount', 'cost', 
                                             'buyer', 'paid']):
                    text = getattr(c, label)
                    if label == 'date':
                        text = text.strftime('%d.%m.%Y')
                    elif label == 'paid':
                        text = 'Ja' if getattr(c, label) else 'Nein'
                    elif label == 'cost':
                        text = euro(text)
                    row.append(text)
                sum_ += c.cost
                self.material_table.add_row(row)
            
            self.material_table.add_row(['' for i in range(6)])
            self.material_table.add_row(['', 'Summe', '', euro(sum_), '', ''])
            
            self.material_table.align['Datum'] = 'l'
            self.material_table.align['Verwendungszweck'] = 'l'
            self.material_table.align['Menge'] = 'r'
            self.material_table.align['Betrag'] = 'r'
            self.material_table.align['gekauft von'] = 'l'
            
            #self.material_table.padding_width = 1 #is default
            
            self.println('\nZahlungen für Verbrauchsmaterial', self.cashes_txt)
            self.println(self.material_table, self.cashes_txt)
            
            
            for name in ['special', 'party']:
                self.println(f'\nZahlungen {cash_name[name]}', self.cashes_txt)
                payments_table_special = prettytable.PrettyTable()
                payments_table_special.field_names = ['Datum', 'Betrag', 'Zweck']
                for p in self.payments[name]:
                    payments_table_special.add_row([date_s(p[0]), euro(p[1]), p[2]])
                
                payments_table_special.align['Betrag'] = 'r'
                payments_table_special.align['Zweck'] = 'l'
                
                self.println(payments_table_special, self.cashes_txt)
            
            
            self.cashes_txt.see('1.0') # jump to top again

                # TODO: Formatierung übernehmen
# =============================================================================
#             self.cashes_txt.delete('1.0', tk.END)
# 
#             cashes_table = prettytable.PrettyTable()
#             cashes_table.field_names = ['Kasse', 'Stand']
#             cashes_table.add_row(['Kaffeekasse', euro(self.cashes['coffee'])])
#             cashes_table.add_row(['Sonderkasse', euro(self.cashes['special'])])
#             cashes_table.add_row(['Feierkasse', euro(self.cashes['party'])])
#             
#             self.println(cashes_table, self.cashes_txt)
#             
#             # Saldo Formatieren
#             start_row = 4
#             start_col = cashes_table._widths[0] + 5
#             end_col = start_col + cashes_table._widths[1]
#             for row, cash in enumerate(['coffee', 'special', 'party']):
#                 start = f'{row + start_row}.{start_col}'
#                 end = f'{row + start_row}.{end_col}'
#                 self.cashes_txt.tag_add(f'red_{row + start_row}', start, end)
#                 color = 'green' if self.cashes[cash] >= 0 else 'red'
#                 self.cashes_txt.tag_config(f'red_{row + start_row}', foreground=color)
#             
#             for name in ['special', 'party']:
#                 self.println(f'\nZahlungen {cash_name[name]}', self.cashes_txt)
#                 payments_table_special = prettytable.PrettyTable()
#                 payments_table_special.field_names = ['Datum', 'Betrag', 'Zweck']
#                 for p in self.payments[name]:
#                     payments_table_special.add_row([date_s(p[0]), euro(p[1]), p[2]])
#                     
#                 self.println(payments_table_special, self.cashes_txt)
#                 
#                 start_row = 13 if name == 'special' else (len(self.payments['special']) + 19)
#                 start_col = payments_table_special._widths[0] + 5
#                 end_col = start_col + payments_table_special._widths[1]
#                 for row, p in enumerate(self.payments[name]):
#                     start = f'{row + start_row}.{start_col}'
#                     end = f'{row + start_row}.{end_col}'
#                     self.cashes_txt.tag_add(f'red_{row + start_row}', start, end)
#                     color = 'green' if p[1] >= 0 else 'red'
#                     self.cashes_txt.tag_config(f'red_{row + start_row}', foreground=color)
# =============================================================================

        except tk.TclError:
            # in case txt frames don't exist anymore
            return

    
    def consumables_from_file(self, filename):
        # lädt consumables objekte aus csv datei
        if not os.path.isfile(filename):
            self.println(error(2))
            self.println(filename)
            return
        self.println(f'Datei eingelesen: {filename}')       
        
        data = Data()
        data.read_csv(filename, parse_dates=['date'], date_parser=date_f)
        
        # check if file contains all required columns
        required_columns = ['date', 'name', 'amount', 'cost', 'buyer', 'paid', 'id']
        if not set(required_columns).issubset(set(data.columns)):
            self.println(error(19, filename))
            messagebox.showinfo('Fehler', error(19, filename))
            return
        
        doublings = 0
        for i, row in data.iterrows():
            if self.get_consumable_by_id(row.id):
                # test if consumable is already in the data
                # if so, skip it
                doublings += 1
                continue
            new_cons = Consumable()
            for col in data.columns:
                setattr(new_cons, col, row[col])
            self.consumables.append(new_cons)
        
        if doublings > 0:
            self.println(f'ACHTUNG: Die Datei enthielt {doublings} Dopplung{"en" if doublings > 1 else ""}.')

        # set saved to False to remind the user to save on exit
        self.saved = False
    
    
    def staff_from_file(self, filename):
        '''
        Lädt Mitarbeiter als Staff objekte aus csv datei
        Datei enthält: id, firstname, lastname, coffee_sum, initial_balance
        -- Nur für initialisierung des Programms
        '''
        if not os.path.isfile(filename):
            self.println(error(2))
            self.println(filename)
            return
        self.println(f'Datei eingelesen: {filename}')
        
        data = Data()
        data.read_csv(filename)
        
        # check if file contains all required columns
        required_columns = ['id', 'firstname', 'lastname', 'initial_balance', 
                            'coffee_sum', 'balance', 'credit', 'debit', 'archive']
        if not set(required_columns).issubset(set(data.columns)):
            self.println(error(19, filename))
            messagebox.showinfo('Fehler', error(19, filename))
            return
        
        for i, row in data.iterrows():
            if row.id in self.generated_IDs:
                # if staff already exists
                staff = self.get_staff_by_id(row.id)
                for col in data.columns:
                    setattr(staff, col, row[col])
                    if col == 'archive':
                        if staff.archive != row[col]:
                            # if archive status does not match status in file,
                            # remove from respective archive
                            if staff in self.staff_members:
                                self.staff_archive.append(staff)
                                self.staff_members.remove(staff)
                            else:
                                self.staff_members.append(staff)
                                self.staff_archive.remove(staff)
                self.println(f'Daten von "{staff}" wurden überschrieben.')
            else:
                # if staff does not exist, creat a new object
                new_staff = Staff()
                for col in data.columns:
                    setattr(new_staff, col, row[col])
                self.generated_IDs.append(new_staff.id)
                if new_staff.archive:
                    self.staff_archive.append(new_staff)
                else:
                    self.staff_members.append(new_staff)
            
        # set saved to False to remind the user to save on exit
        self.saved = False
            
    
    def payments_from_file(self, filename):
        '''
        Lädt Bezahlungen der Mitarbeiter aus csv datei
        Datei enthält: id, (firstname), date, payment
        -- Nur für initialisierung des Programms
        '''
        if not os.path.isfile(filename):
            self.println(error(2))
            self.println(filename)
            return
        self.println(f'Datei eingelesen: {filename}')
        
        def parse_date(date_s):
            try:
                return datetime.datetime.strptime(date_s, '%Y-%m-%d').date()
            except:
                return datetime.datetime.strptime(date_s, '%d.%m.%Y').date()
        
        data = Data()
        data.read_csv(filename, parse_dates=['date'], 
                      date_parser=parse_date)
        
        # TODO: check if payment already exists
        
        required_columns = ['id', 'name', 'date', 'payment']
        if not set(required_columns).issubset(set(data.columns)):
            self.println(error(19, filename))
            messagebox.showinfo('Fehler', error(19, filename))
            return
        
        not_found = []
        for i, row in data.iterrows():
            found = False
            for staff in self.staff_members:
                if staff.id == row.id:
                    found = True
                    staff.payments.append((row.date, row.payment))
                    break
            if found:
                continue
            for staff in self.staff_archive:
                if staff.id == row.id:
                    found = True
                    staff.payments.append((row.date, row.payment))
                    break
            if not found:
                not_found.append((row.id, row.name))
        
        if not_found:
            error_msg = 'ACHTUNG: Für folgende Bezahlungen konnte kein Mitarbeiter gefunden werden:'
            for f in not_found:
                error_msg += f'\n{f}'
            self.println(error_msg)
            messagebox.showinfo('Achtung', error_msg)
        
        # set saved to False to remind the user to save on exit
        self.saved = False
                    
    
    def tally_entry_from_file(self, filename):
        '''
        Liest Striche aus Datei
        Die Datei muss mindestens die 'ID' und die Anzahl 'Striche' enthalten 
        '''
        if not os.path.isfile(filename):
            self.println(error(2))
            self.println(filename)
            return
        elif filename[-3:] != 'csv':
            self.println(error(4))
            return

        data = Data()
        data.read_csv(filename)
        
        self.println(f'Striche aus Datei {filename} eingelesen\n')
        
        required_columns = ['ID', 'Striche']
        if not set(required_columns).issubset(set(data.columns)):
            self.println(error(19, filename))
            messagebox.showinfo('Fehler', error(19, filename))
            return
        
        error_happened = False
        try:
            t = prettytable.PrettyTable()
            t.field_names = ['Name', 'Striche']
            self.tally_entries[today()] = []
            for i, row in data.iterrows():
                tally = row.Striche
                if tally > 0:
                    staff = self.get_staff_by_id(row.ID)
                    if not staff:
                        self.println(error(15, row.ID))
                        error_happened = True
                        continue
                    staff.coffee_sum += tally
                    self.tally_entries[today()].append([staff, tally])
                    t.add_row([staff, int(tally)])
            self.println('\n' + str(t))
        except:
            self.println(error(5))
            traceback.print_exc()
        
        if error_happened:
            messagebox.showinfo('Fehler', error(17))
        # set saved to False to remind the user to save on exit
        self.saved = False
                    
                    
    def generate_id(self):
        while True:
            id_ = random.randint(1000000000, 9999999999)
            if id_ not in self.generated_IDs:
                self.generated_IDs.append(id_)
                break
        return id_
        
    
    def get_staff_by_id(self, id_):
        for staff in self.staff_members:
            if staff.id == id_:
                return staff
    
    
    def get_consumable_by_id(self, id_):
        for con in self.consumables:
            if con.id == id_:
                return con
            
    
    def check_name(self, firstname, lastname):
        name = lastname + ', ' + firstname
        if name == ', ':
            messagebox.showinfo('Fehler', error(0))
            return False
        elif len(firstname) < 2:
            messagebox.showinfo('Fehler', error(8, firstname))
            return False
        elif len(name) > 50:
            messagebox.showinfo('Fehler', error(13, name, 50))
            return False
        elif not is_allowed_letters(firstname, spaces=True):
            messagebox.showinfo('Fehler', error(9, firstname))
            return False
        elif not is_allowed_letters(lastname, spaces=True):
            messagebox.showinfo('Fehler', error(9, lastname))
            return False
        else:
            return True
    
    
    def show_error(self, *args):
        err = f"FEHLER: {''.join(traceback.format_exception(*args))}"
        print(err)
        messagebox.showerror('Exception', err)
        self.println(err)
    
    
    def client_exit(self):
        try:
            # save console to log file
            with open(self.log_filename, 'a') as f:
                txt = self.console_txt.get(1.0, tk.END).rstrip()
                if txt:
                    f.write(txt + '\n')
                    if not self.saved:
                        f.write(today() + ' Änderungen wurden beim Beenden nicht gespeichert.')
            
            # delete contents from temp folder
            for file in [os.path.join(self.temp_folder, filename) 
                         for filename in os.listdir(self.temp_folder)]:
                try:
                    os.remove(file)
                except FileNotFoundError:
                    traceback.print_exc()
                    pass
            
            
            if not self.saved and not self.debug_mode:
                if messagebox.askokcancel('Achtung', error(1)):
                    #self.save_data(self.save_data_filename) # das gehört hier gar nicht hin
                    self.master.destroy()
            else:
                self.master.destroy()
        except Exception:
            traceback.print_exc()
            self.master.destroy()


    def test_function(self):
        # test function for debugging stuff
        # random text color
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        col = '#' + ''.join('%02x'%i for i in (r, g, b))
        self.println('This is just a test to see if the color feature works', 
                     color=col)
        
        for i in range(30):
            self.consumables.append(Consumable(name='Etwas für Testzwecke', 
                                   amount=random.randint(1, 12), cost=random.random() * 100, 
                                   buyer=random.choice(self.staff_members).firstname))
        self.update_tabs()


class PopupStaff():
    """
    Fenster zum Hinzufügen oder Bearbeiten von Personen
    """
    def __init__(self, app, master, parent=None, mode='add'):
        self.app = app
        self.master = master
        self.parent = parent
        
        # TODO: change to grid
        
        self.top = top = tk.Toplevel(master)
        top.resizable(width=False, height=False)
        top.geometry('220x160')
        top.attributes('-topmost', 'true')
        top.lift()
        self.l1 = tk.Label(top, text='Vorname')
        self.l1.pack()
        self.e1 = tk.Entry(top)
        self.e1.pack()
        self.l2 = tk.Label(top, text='Nachname')
        self.l2.pack()
        self.e2 = tk.Entry(top)
        self.e2.pack()
        self.mode = mode
        if self.mode == 'add':
            self.b = tk.Button(top, 
                               text='Person hinzufügen',
                               command=self.cleanup_add)
        elif self.mode == 'edit':
            self.id = None
            staff_selected = self.app.popup_edit_staff.selected
            
            for staff in self.app.staff_members:
                if staff_selected.id == staff.id:
                    self.id = staff.id
            self.e1.insert(0, staff_selected.firstname)
            self.e2.insert(0, staff_selected.lastname)
            self.b = tk.Button(top,
                               text='Änderungen speichern',
                               command=self.cleanup_edit)
        elif self.mode == 'archive':
            self.id = None
            staff_selected = self.app.popup_edit_archive.selected
            
            for staff in self.app.staff_archive:
                if staff_selected.id == staff.id:
                    self.id = staff.id
            self.e1.insert(0, staff_selected.firstname)
            self.e2.insert(0, staff_selected.lastname)
            self.b = tk.Button(top,
                               text='Änderungen speichern',
                               command=self.cleanup_edit)
        
        self.b.pack()
        self.top.protocol('WM_DELETE_WINDOW', self.delete)

    
    def cleanup_add(self):
        # get name from entry forms
        firstname = self.e1.get().strip()
        lastname = self.e2.get().strip()
        if not self.app.check_name(firstname, lastname):
            self.top.lift()
            return
        else:
            # generate random ID and check for doubles
            id_ = self.app.generate_id()
            new_staff = Staff(firstname=firstname,
                              lastname=lastname,
                              staff_id=id_)
            self.app.staff_members.append(new_staff)
            self.app.config['on_tally_list'].append(1)
            self.e1.delete(0, tk.END)
            self.e2.delete(0, tk.END)
            self.app.println(f'{new_staff.lastname}, {new_staff.firstname} hinzugefügt.')
            messagebox.showinfo('Platzhalter', 
                                f'{new_staff.lastname}, {new_staff.firstname} hinzugefügt.')
            #self.top.lift()
            
            # set saved to False to remind the user to save on exit
            self.app.saved = False
    
    
    def cleanup_edit(self):
        if self.mode == 'edit':
            group = self.app.staff_members
        elif self.mode == 'archive':
            group = self.app.staff_archive
            
        if self.id:
            # check input
            firstname = self.e1.get().strip()
            lastname = self.e2.get().strip()
            if not self.app.check_name(firstname, lastname):
                self.top.lift()
                return
            else:
                for staff in group:
                    if staff.id == self.id:
                        staff.firstname = firstname
                        staff.lastname = lastname
                        break
            
        self.delete()
        self.app.println(f'{staff.lastname}, {staff.firstname} erfolgreich bearbeitet.')
        # set saved to False to remind the user to save on exit
        self.app.saved = False
        
    
    def delete(self):
        if self.parent:
            self.parent.top.attributes('-disabled', 'false')
        self.top.destroy()
        
        

class EditStaffWindow():
    def __init__(self, app, master, mode):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        self.mode = mode
        top.geometry('220x160')
        top.attributes('-topmost', 'true')
        top.resizable(width=False, height=False)
        
        tk.Label(top, text='Wähle eine Person zum bearbeiten').pack()
        
        self.frame1 = tk.Frame(top)
        self.frame1.pack()
        self.staff = tk.StringVar(top)
        self.menu = self.make_menu()
        self.menu.pack()
        button1 = tk.Button(top,
                           text='Bearbeiten', 
                           command=lambda: self.get_staff(self.mode))
        button1.pack()
        if self.mode == 'edit':
            button2 = tk.Button(top,
                               text='Archivieren', 
                               command=self.archive_staff)
        elif self.mode == 'archive':
            button2 = tk.Button(top,
                           text='Wiederherstellen', 
                           command=self.recover_staff)
        button2.pack()
        
        self.top.protocol('WM_DELETE_WINDOW', self.delete)
        
    
    def make_menu(self):
        if self.mode == 'edit':
            choices = self.app.staff_members
            default = self.app.staff_members[0]
        elif self.mode == 'archive':
            choices = self.app.staff_archive
            default = self.app.staff_archive[0]
        self.selected = default
        return ttk.OptionMenu(self.frame1, self.staff, default, *choices, 
                                   command=self.pass_value)


    def pass_value(self, value):
        self.selected = value


    def get_staff(self, mode):
        self.popup = PopupStaff(self.app, self.master, self, mode=mode)
        self.top.attributes('-disabled', 'true')
    
    
    def archive_staff(self):
        choice = messagebox.askokcancel('ACHTUNG', error(6, self.selected))
        if choice:
            self.app.staff_members.remove(self.selected)
            self.app.staff_archive.append(self.selected)
            self.app.println(f'{self.selected} wurde archiviert.')
            self.app.update_tabs()
            self.menu.destroy()
            self.menu = self.make_menu()
            self.menu.pack()
            # set saved to False to remind the user to save on exit
            self.app.saved = False
        #self.top.destroy()
    
    def recover_staff(self):
        choice = messagebox.askokcancel('ACHTUNG', error(7, self.selected))
        if choice:
            self.app.staff_archive.remove(self.selected)
            self.app.staff_members.append(self.selected)
            self.app.println(f'{self.selected} wurde wiederhergestellt.')
            self.app.update_tabs()
            self.menu.destroy()
            self.menu = self.make_menu()
            self.menu.pack()
            # set saved to False to remind the user to save on exit
            self.app.saved = False
        #self.top.destroy()
    
    
    def delete(self):
        # on window closing, ensure to kill all children as well
        try:
            self.popup.top.destroy()
        except:
            pass
        self.top.destroy()



class EnterPaymentWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('220x160')
        top.resizable(width=False, height=False)
        self.staff = tk.StringVar(top)
        choices = self.app.staff_members
        default = self.app.staff_members[0]
        self.selected = default
        popupMenu = ttk.OptionMenu(top, self.staff, default, *choices,
                                   command=self.pass_value)
        tk.Label(top, text='Wer hat bezahlt?').pack()
        popupMenu.pack()
        button = tk.Button(top,
                           text='Auswählen', 
                           command=self.payment_entry)
        button.pack()
        
        self.top.protocol('WM_DELETE_WINDOW', self.delete)
    
    
    def pass_value(self, value):
        self.selected = value
        
    def delete(self):
        # on window closing, ensure to kill all children as well
        try:
            self.popup.top.destroy()
        except:
            pass
        self.top.destroy()
        self.app.saved = False

    def payment_entry(self):
        self.name = self.staff.get()
        self.popup = PopupPayment(self.app, self.master, self.staff)
        


class AddCashWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('300x200')
        top.resizable(width=False, height=False)
        top.title('Kasse hinzufügen')
        
        padx = 5
        pady = 5
        
        self.l1 = tk.Label(top, text='Name')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.e1 = tk.Entry(top)
        self.e1.grid(row=0, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.l2 = tk.Label(top, text='Anfangsbetrag')
        self.l2.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.e2 = tk.Entry(top)
        self.e2.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.l3 = tk.Label(top, text='€')
        self.l3.grid(row=1, column=2, padx=0, pady=pady, sticky=tk.W)
        
        self.b = tk.Button(top,
                           text='Kasse hinzufügen',
                           command=self.cleanup)
        self.b.grid(row=2, column=0, padx=padx, pady=pady, columnspan=2, sticky=tk.S)
        
    
    def cleanup(self):
        name = self.e1.get().strip()
        if len(name) == 0:
            messagebox.showinfo('Fehler', error(0))
            return
        try:
            initial_balance = float(self.e2.get().strip().replace(',', '.'))
        except:
            messagebox.showinfo('Fehler', error(3))
            return
        
        index = len(self.app.cashes)
        self.app.cashes[f'custom_cash_{index}'] = initial_balance
        self.app.payments[f'custom_cash_{index}'] = []
        cash_name[f'custom_cash_{index}'] = name
        self.app.println(f'Kasse "{name}" hinzugefügt. Initialbetrag: {euro(initial_balance)}')
        
        self.app.payment_submenu.add_command(label=name, 
                           command=lambda x=index: self.app.enter_cash(f'custom_cash_{x}'))
        # TODO: edit cash zu menü hinzufügen
        self.app.update_tabs()
        


class PopupPayment():
    def __init__(self, app, master, staff):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('220x160')
        top.resizable(width=False, height=False)
        
        # TODO: make this a grid
        self.l1 = tk.Label(top, text=self.app.popup_add_payment.staff.get())
        self.l1.pack()
        self.e1 = tk.Entry(top)
        self.e1.pack()
        self.l2 = tk.Label(top, text='Datum')
        self.l2.pack()
        self.e2 = tk.Entry(top)
        self.e2.pack()
        self.id = None
        for staff in self.app.staff_members:
            if self.app.popup_add_payment.selected.id == staff.id:
                self.id = staff.id
        self.e1.insert(0, 0)
        self.e2.insert(0, date_s(datetime.date.today()))
        self.b = tk.Button(top,
                           text='Eingabe speichern',
                           command=self.cleanup)
        self.b.pack()

    
    def cleanup(self):
        if self.id:
            try:
                value = float(self.e1.get().strip().replace(',', '.'))
            except:
                messagebox.showinfo('Fehler', error(3))
                self.top.destroy()
                value = 0
            if abs(value) > 0.0:
                staff = self.app.get_staff_by_id(self.id)
                date = date_f(self.e2.get().strip())
                staff.payments.append((date, value))
                self.app.println(f'Bezahlung eingetragen für {staff}: '
                                    f'{euro(value)} am '
                                    f'{date_s(date)}')
                self.app.cashes['coffee'] += value
            # set saved to False to remind the user to save on exit
            self.app.saved = False
                    
        self.top.destroy()
        


class PaymentOverview():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.title('Übersicht über Zahlungen')
        top.resizable(width=False, height=False)
        self.text = scrolledtext.ScrolledText(top)
        self.text.pack(fill=tk.BOTH, expand=True)
        
        t = prettytable.PrettyTable()
        t.field_names = ['Datum', 'Name', 'Betrag']
        
        payments = []
        
        for staff in self.app.staff_members:
            for payment in staff.payments:
                payments.append([payment[0], str(staff), euro(payment[1])])
        payments = sorted(payments, key=lambda x: x[0])
        
        for p in payments:
            p[0] = p[0].strftime('%d.%m.%Y')
            t.add_row(p)
        
        self.app.println('---Kaffeekasse---', self.text)
        self.app.println('Zahlungen der Mitarbeiter', self.text)
        self.app.println(t, self.text)
        
        self.app.println('\nEinkauf von Verbrauchsmaterial', self.text)
        
        
        self.text.see('1.0') # zum Schluss nach oben scrollen



class EnterTallyWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('500x800')
        top.title('Striche eintragen')
        top.resizable(width=False, height=False)
        padx = 5
        pady = 5
        self.l1 = tk.Label(top, text='Datum')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.e1 = tk.Entry(top)
        self.e1.grid(row=0, column=1)
        self.e1.insert(0, date_s(datetime.date.today()))
        self.b = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        
        self.b.grid(row=0, column=2, padx=10)
        
        self.entries = []
        
        for index, s in enumerate(self.app.staff_members):
            l = tk.Label(top, text=s)
            l.grid(row=index+1, column=0, sticky=tk.W)
            e = tk.Entry(top)
            e.grid(row=index+1, column=1)
            e.insert(0, 0)
            self.entries.append(e)
            
        
    def cleanup(self):
        date = self.e1.get()
        try:
            self.app.tally_entries[date] = []
            for index, s in enumerate(self.app.staff_members):
                amount = int(self.entries[index].get())
                s.coffee_sum += amount
                self.app.tally_entries[date].append([s, amount])
        except:
            messagebox.showinfo('FEHLER', error(3))
            self.app.println(error(3))
            return
        
        for e in self.entries:
            e.delete(0, tk.END)
            e.insert(0, 0)
        
        self.app.println(f'Striche eingetragen für den {date}.')
        self.app.update_tabs()
        
        # set saved to False to remind the user to save on exit
        self.app.saved = False
        
        
        
class EnterMaterialWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('300x250')
        top.title('Verbrauchsmaterial')
        top.resizable(width=False, height=False)
        padx = 5
        pady = 5
        
        self.checkvar = tk.BooleanVar()
        
        self.l1 = tk.Label(top, text='Datum')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e1 = tk.Entry(top)
        self.e1.grid(row=0, column=1, sticky=tk.W)
        self.e1.insert(0, date_s(datetime.datetime.today()))
        
        self.l2 = tk.Label(top, text='Verwendungszweck')
        self.l2.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e2 = tk.Entry(top)
        self.e2.grid(row=1, column=1, sticky=tk.W)
        
        self.l3 = tk.Label(top, text='Menge')
        self.l3.grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e3 = tk.Spinbox(top, from_=1, to=9999999999)
        self.e3.grid(row=2, column=1, sticky=tk.W)
        
        self.l4 = tk.Label(top, text='Betrag')
        self.l4.grid(row=3, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e4 = tk.Entry(top)
        self.e4.grid(row=3, column=1, sticky=tk.W)
        self.l4_1 = tk.Label(top, text='€')
        self.l4_1.grid(row=3, column=2, padx=padx, pady=pady, sticky=tk.W)
        
        self.l5 = tk.Label(top, text='gekauft von')
        self.l5.grid(row=4, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e5 = tk.Entry(top) #TODO: drop down menu mit Mitarbeitern?
        self.e5.grid(row=4, column=1, sticky=tk.W)
        
        self.l6 = tk.Label(top, text='ausgezahlt')
        self.l6.grid(row=5, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e6 = tk.Checkbutton(top, variable=self.checkvar)
        self.e6.grid(row=5, column=1, sticky=tk.W)

        self.b = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        self.b.grid(row=6, column=1, padx=padx, pady=pady, sticky=tk.W)
    
    
    def cleanup(self):
        # check inputs
        try:
            date = date_f(self.e1.get().strip())
        except ValueError:
            messagebox.showinfo('Fehler', error(10, self.e1.get().strip()))
            self.top.lift()
            return
        
        name = self.e2.get().strip() # Verwendungszweck
        if len(name) == 0:
            messagebox.showinfo('Fehler', error(8, self.e2.get().strip()))
            self.top.lift()
            return
        
        try:
            amount = int(self.e3.get()) # Menge
        except ValueError:
            messagebox.showinfo('Fehler', error(11, self.e3.get().strip()))
            self.top.lift()
            return
        
        try:
            cost = float(self.e4.get().replace(',', '.'))
        except ValueError:
            messagebox.showinfo('Fehler', error(11, self.e4.get().strip()))
            self.top.lift()
            return
        
        buyer = self.e5.get().strip()
        if not is_allowed_letters(buyer, spaces=True):
            messagebox.showinfo('Fehler', error(9, buyer))
            self.top.lift()
            return
        
        paid = self.checkvar.get()

        c = Consumable(name, amount, cost, buyer, date, paid, 
                       self.app.generate_id())
        self.app.consumables.append(c)
        self.app.println(f'Verbrauchsmaterial hinzugefügt: {c}')
        
        self.app.cashes['coffee'] -= cost
            
        for e in [self.e2, self.e3, self.e4, self.e5]:
            e.delete(0, 'end')
            if e == self.e3:
                e.insert(0, '1')
        
        self.app.update_tabs()
        self.app.saved = False



class MaterialListWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('482x420')
        top.title('Verbrauchsmaterial')
        top.resizable(width=False, height=False)
        top.bind('<Destroy>', self._destroy)
        #top.bind("<Configure>", on_resize)
        
        tk.Grid.rowconfigure(top, 0, weight=1)
        tk.Grid.columnconfigure(top, 0, weight=1)
        
        self.canvas = tk.Canvas(top)
        self.canvas.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        
        vsbar = tk.Scrollbar(top, orient=tk.VERTICAL, command=self.canvas.yview)
        vsbar.grid(row=0, column=1, sticky=tk.NS)
        self.canvas.configure(yscrollcommand=vsbar.set)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.buttons_frame = tk.Frame(self.canvas, bd=2)
        
        self.construct_canvas()
        
        
    def construct_canvas(self):
        padx = 1
        pady = 1
        if len(self.app.consumables) == 0:
            l = tk.Label(self.buttons_frame, text='Keine Einträge vorhanden.')
            self.elements.append(l)
            l.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        else:
            self.elements = []
            for index, con in enumerate(self.app.consumables):
                # limit length of name to 50 characters
                name = str(con)
                if len(name) > 50:
                    name = name[:47] + '...'
                l1 = tk.Label(self.buttons_frame, text=name)
                ToolTip(l1, name)
                self.elements.append(l1)
                l1.grid(row=index, column=0, padx=padx, pady=pady, sticky=tk.W)
                l2 = tk.Label(self.buttons_frame, text=euro(con.cost))
                self.elements.append(l2)
                l2.grid(row=index, column=1, padx=padx, pady=pady, sticky=tk.E)
                b1 = tk.Button(self.buttons_frame, text='Bearbeiten', 
                               command=lambda i=index: self.edit(i))
                self.elements.append(b1)
                b1.grid(row=index, column=2, padx=padx, pady=pady, sticky=tk.W)
                b2 = tk.Button(self.buttons_frame, text='Löschen', 
                               command=lambda i=index: self.delete(i))
                self.elements.append(b2)
                b2.grid(row=index, column=3, padx=padx, pady=pady, sticky=tk.W)
        
        self.canvas.create_window((0,0), window=self.buttons_frame, anchor=tk.NW)
        
        self.buttons_frame.update_idletasks()  # Needed to make bbox info available.
        bbox = self.canvas.bbox(tk.ALL)  # Get bounding box of canvas with Buttons.

        # Define the scrollable region as entire canvas with only the desired
        # number of rows and columns displayed.
        ROWS, COLS = 10, 6  # Size of grid.
        ROWS_DISP = 8  # Number of rows to display.
        COLS_DISP = 6  # Number of columns to display.
        w, h = bbox[2]-bbox[1], bbox[3]-bbox[1]
        dw, dh = int((w/COLS) * COLS_DISP), int((h/ROWS) * ROWS_DISP)
        self.canvas.configure(scrollregion=bbox, width=dw, height=dh)
    
    
    def delete(self, index):
        item = self.app.consumables[index]
        choice = messagebox.askokcancel("Achtung!", error(14, item), parent=self.top)
        if choice:
            del self.app.consumables[index]
            self.app.println(f'{item} {euro(item.cost)} wurde gelöscht.')
            self.app.cashes['coffee'] += item.cost
            for elem in self.elements:
                elem.destroy()
            self.construct_canvas()
            self.app.update_tabs()
            self.top.lift()
    
    
    def edit(self, index):
        id_ = self.app.consumables[index].id
        mw = EditMaterialWindow(self.app, self.master, id_)
        self.top.wait_window(mw.top)
        for elem in self.elements:
            elem.destroy()
        self.construct_canvas()
        
        
    def _on_mousewheel(self, event):
        sys_name = platform.system()
        if sys_name == 'Windows':
            self.canvas.yview_scroll(-1 * (event.delta//120), "units")
        elif sys_name == 'Darwin':
            self.canvas.yview_scroll(-1 * event.delta, "units")
    
    
    def _destroy(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        


class EditMaterialWindow():
    def __init__(self, app, master, id_):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('300x250')
        top.title('Verbrauchsmaterial')
        top.resizable(width=False, height=False)
        padx = 5
        pady = 5
        
        self.checkvar = tk.BooleanVar()
        
        self.id = id_
        con = self.app.get_consumable_by_id(id_)
        
        self.l1 = tk.Label(top, text='Datum')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e1 = tk.Entry(top)
        self.e1.grid(row=0, column=1, sticky=tk.W)
        self.e1.insert(0, date_s(con.date))
        
        self.l2 = tk.Label(top, text='Verwendungszweck')
        self.l2.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e2 = tk.Entry(top)
        self.e2.grid(row=1, column=1, sticky=tk.W)
        self.e2.insert(0, con.name)
        
        self.l3 = tk.Label(top, text='Menge')
        self.l3.grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e3 = tk.Spinbox(top, from_=1, to=9999999999)
        self.e3.grid(row=2, column=1, sticky=tk.W)
        self.e3.delete(0, 'end')
        self.e3.insert(0, con.amount)
        
        self.l4 = tk.Label(top, text='Betrag')
        self.l4.grid(row=3, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e4 = tk.Entry(top)
        self.e4.grid(row=3, column=1, sticky=tk.W)
        self.e4.insert(0, str(con.cost).replace('.', ','))
        self.l4_1 = tk.Label(top, text='€')
        self.l4_1.grid(row=3, column=2, padx=padx, pady=pady, sticky=tk.W)
        
        self.l5 = tk.Label(top, text='gekauft von')
        self.l5.grid(row=4, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e5 = tk.Entry(top) #TODO: drop down menu mit Mitarbeitern?
        self.e5.grid(row=4, column=1, sticky=tk.W)
        self.e5.insert(0, con.buyer)
        
        self.l6 = tk.Label(top, text='ausgezahlt')
        self.l6.grid(row=5, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.checkvar.set(bool(con.paid))
        self.e6 = tk.Checkbutton(top, variable=self.checkvar)
        self.e6.grid(row=5, column=1, sticky=tk.W)

        self.b = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        self.b.grid(row=6, column=1, padx=padx, pady=pady, sticky=tk.W)
    
    
    def cleanup(self):
        # check inputs
        try:
            date = date_f(self.e1.get().strip())
        except ValueError:
            messagebox.showinfo('Fehler', error(10, self.e1.get().strip()))
            self.top.lift()
            return
        
        name = self.e2.get().strip() # Verwendungszweck
        if not is_allowed_letters(name, spaces=True, numbers=True):
            messagebox.showinfo('Fehler', error(9, name))
            self.top.lift()
            return
        
        try:
            amount = int(self.e3.get()) # Menge
        except ValueError:
            messagebox.showinfo('Fehler', error(11, self.e3.get().strip()))
            self.top.lift()
            return
        
        try:
            cost = float(self.e4.get().replace(',', '.'))
        except ValueError:
            messagebox.showinfo('Fehler', error(11, self.e4.get().strip()))
            self.top.lift()
            return
        
        buyer = self.e5.get().strip()
        if not is_allowed_letters(buyer, spaces=True):
            messagebox.showinfo('Fehler', error(9, buyer))
            self.top.lift()
            return
        
        paid = self.checkvar.get()

        con = self.app.get_consumable_by_id(self.id)
        # set new values
        con.date = date
        con.name = name
        con.amount = amount
        con.buyer = buyer
        con.paid = paid
        
        # check if cost changed
        if cost != con.cost:
            self.app.cashes['coffee'] += con.cost
            self.app.cashes['coffee'] -= cost
            con.cost = cost
        
        
        self.app.update_tabs()
        self.app.saved = False
        
        

class EnterCashWindow():
    def __init__(self, app, master, name):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        self.name = name
        top.geometry('300x250')
        top.title(cash_name[name])
        top.resizable(width=False, height=False)
        
        padx = 5
        pady = 5
        
        self.l1 = tk.Label(top, text='Datum')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e1 = tk.Entry(top)
        self.e1.grid(row=0, column=1)
        self.e1.insert(0, date_s(datetime.datetime.today()))
        
        self.l2 = tk.Label(top, text='Betrag')
        self.l2.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e2 = tk.Entry(top)
        self.e2.grid(row=1, column=1)
        self.l2_1 = tk.Label(top, text='€')
        self.l2_1.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.E)
        
        self.l3 = tk.Label(top, text='Zweck')
        self.l3.grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.E)
        self.e3 = tk.Entry(top)
        self.e3.grid(row=2, column=1)
        
        self.b = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        self.b.grid(row=3, column=1, padx=padx, pady=pady, sticky=tk.W)
    
    
    def cleanup(self):
        try:
            date = date_f(self.e1.get().strip())
        except ValueError:
            messagebox.showinfo('Fehler', error(10, self.e1.get().strip()))
            self.top.lift()
            return
        
        try:
            value = float(self.e2.get().replace(',', '.')) # Betrag
        except ValueError:
            messagebox.showinfo('Fehler', error(11, self.e2.get().strip()))
            self.top.lift()
            return
        
        purpose = self.e3.get()
        if len(purpose) == 0:
            messagebox.showinfo('Fehler', error(12, 'Verwendungszweck'))
            self.top.lift()
            return
        
        if value == 0:
            return
        purpose = self.e3.get().strip()
        self.app.cashes[self.name] += value
        self.app.payments[self.name].append([date, value, purpose])
        if value > 0:
            self.app.println(f'{euro(value)} eingezahlt in {self.top.title()} '
                                + f'am {date_s(date)}. Zweck: {purpose}')
        else:
            self.app.println(f'{euro(value)} entnommen aus {self.top.title()} ' 
                                + f'am {date_s(date)}. Zweck: {purpose}')
        self.e2.delete(0, 'end')
        self.e3.delete(0, 'end')
        
        self.app.saved = False
        


class EditPreferencesWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('250x300')
        top.title('Einstellungen')
        top.resizable(width=False, height=False)
        
        padx = 5
        pady = 5
        
        self.l1 = tk.Label(top, text='Backup-Intervall')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.e1 = tk.Spinbox(top, from_=0, to=365, width=6)
        self.e1.grid(row=0, column=1)
        self.e1.delete(0, 'end')
        self.e1.insert(0, str(self.app.config['backup_interval']))
        self.l1_1 = tk.Label(top, text='Tag(e)')
        self.l1_1.grid(row=0, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.ttp1 = ToolTip(self.l1, tooltip('backup_interval'))
        
        self.l2 = tk.Label(top, text='Preis pro Strich')
        self.l2.grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.e2 = tk.Spinbox(top, from_=1, to=1000, width=6)
        self.e2.grid(row=1, column=1)
        self.e2.delete(0, 'end')
        self.e2.insert(0, str(int(self.app.config['coffee_factor'] * 100)))
        self.l2_1 = tk.Label(top, text='Cent')
        self.l2_1.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.ttp2 = ToolTip(self.l2, tooltip('coffee_factor'))
        
        self.l3 = tk.Label(top, text='Debug Mode')
        self.l3.grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.var3 = tk.BooleanVar()
        self.var3.set(self.app.debug_mode)
        self.e3 = tk.Checkbutton(top, variable=self.var3)
        self.e3.grid(row=2, column=1)
        self.ttp3 = ToolTip(self.l3, tooltip('debug_mode'))
        
        self.b1 = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        self.b1.grid(row=3, column=0, padx=padx, pady=pady, sticky=tk.W)
        
    
    def cleanup(self):
        # check values
        val_1 = self.e1.get()
        try:
            self.app.config['backup_interval'] = int(val_1)
        except ValueError:
            messagebox.showinfo('Fehler', error(11, val_1))
            self.top.lift()
            return
        
        val_2 = self.e2.get()
        try:
            self.app.config['coffee_factor'] = int(val_2) * 0.01
        except ValueError:
            messagebox.showinfo('Fehler', error(11, val_2))
            self.top.lift()
            return
        
        val_3 = self.var3.get()
        if not val_3 and self.app.debug_mode:
            self.app.println('<<ACHTUNG>>: DEBUG MODE DEAKTIVIERT!', color='green')
        self.app.debug_mode = val_3
        
        self.app.saved = False
        self.app.println('Einstellungen geändert.')
        self.top.destroy()
        
        
        
class ConfigureTallyListWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('400x800')
        top.title('Strichliste konfigurieren')
        top.resizable(width=False, height=False)
        for r in range(4):
            top.columnconfigure(r, minsize=10)
        top.rowconfigure(2, minsize=20)
        #top.bind('<Configure>', lambda x: print(x.width, x.height)) #Fenstergröße anzeigen
        self.l1 = tk.Label(top, text='Anzahl leerer Zeilen')
        self.l1.grid(row=0, column=0)
        self.var1 = tk.IntVar()
        choices = list(range(21))
        default = self.app.config['tally_list_empty']
        popupMenu = ttk.OptionMenu(top, self.var1, default, *choices,
                                   command=self.pass_value1)
        popupMenu.grid(row=0, column=1, sticky='w')
        
        save_button = tk.Button(top,
                               text='Eingaben speichern',
                               command=self.cleanup)
        save_button.grid(row=0, column=3)
    
        tk.Label(top, text='Mitarbeiter auf der Liste').grid(row=3, column=0)
    
        self.checkbox_vars = []
        for index, s in enumerate(self.app.staff_members):
            try:
                v = tk.IntVar(value=self.app.config['on_tally_list'][index])
            except IndexError:
                v = tk.IntVar(value=1) # fallback if something doesn't match
            self.checkbox_vars.append(v)
            c = tk.Checkbutton(top, text=s, variable=v,
                               command=self.save_tally_config)
            list_size = 25
            col = 0 if index < list_size else 1
            row = index % list_size + 4
            c.grid(row=row, column=col, sticky='w')
            
    
    
    def pass_value1(self, value):
        self.app.config['tally_list_empty'] = value
        
    
    def save_tally_config(self):
        get_vars = [v.get() for v in self.checkbox_vars]
        self.app.config['on_tally_list'] = get_vars
        # set saved to False to remind the user to save on exit
        self.app.saved = False
    
    
    def cleanup(self):
        self.app.println('Änderungen an der Strichliste gespeichert')
        pass
        
    

class CashesInventoryWindow():
    def __init__(self, app, master):
        self.app = app
        self.master = master
        self.top = top = tk.Toplevel(master)
        top.geometry('300x300')
        top.title('Inventur')
        top.resizable(width=False, height=False)
        
        padx = 4
        pady = 3
        
        self.l1 = tk.Label(top, text='Kasse')
        self.l1.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.l2 = tk.Label(top, text='Alt')
        self.l2.grid(row=0, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.l3 = tk.Label(top, text='Neu')
        self.l3.grid(row=0, column=2, padx=padx, pady=pady, sticky=tk.W)
        
        self.entries = {}
        for i, key in enumerate(app.cashes):
            l1 = tk.Label(top, text=cash_name[key])
            l1.grid(row=i + 1, column=0, padx=padx, pady=pady, sticky=tk.W)
            l2 = tk.Label(top, text=euro(app.cashes[key]))
            l2.grid(row=i + 1, column=1, padx=padx, pady=pady, sticky=tk.E)
            e = tk.Entry(top)
            e.grid(row=i + 1, column=2, padx=padx, pady=pady, sticky=tk.W)
            self.entries[key] = e
            l3 = tk.Label(top, text='€')
            l3.grid(row=i + 1, column=3, padx=padx, pady=pady, sticky=tk.E)
            
        self.b = tk.Button(top,
                           text='Eingaben speichern',
                           command=self.cleanup)
        self.b.grid(row=i + 2, column=0, columnspan=2, 
                    padx=padx, pady=pady, sticky=tk.W)
        
    
    def cleanup(self):
        for key, entry in self.entries.items():
            value = entry.get()
            if value:
                try:
                    value = float(value.replace(',', '.'))
                    self.app.println(f'Inventur {cash_name[key]}: Alt: ' +
                                     f'{euro(self.app.cashes[key])}, Neu: ' +
                                     f'{euro(value)}.')
                    self.app.cashes[key] = value
                except ValueError:
                    traceback.print_exc()



class Staff():
    '''
    Class to store staff member information
    '''
    def __init__(self, firstname='default', lastname='default', 
                 staff_id=None, archive=False):
        self.firstname = capitalize_first(firstname)
        self.lastname = capitalize_first(lastname)
        self.archive = archive
        self.id = staff_id
        
        self.initial_balance = 0
        self.balance = 0
        self.credit = 0
        self.debit = 0
        self.coffee_sum = 0
        self.payments = [] # [(Zeitstempel, Menge)]
        
        
    def __repr__(self):
        return f'{self.firstname} {self.lastname}'.strip()
    
    
    def calculate_balance(self, factor):
        self.balance = 0
        self.debit = round(self.coffee_sum * factor, 10)
        self.credit = sum([p[1] for p in self.payments])
        self.balance = self.credit - self.debit + self.initial_balance
        # runden wegen floating point fehlern
        self.balance = round(self.balance, 10)
        if self.balance == -0.0:
            self.balance = 0
        


class Consumable():
    '''
    Class for consumables (coffee, filter, etc.)
    '''
    def __init__(self, name='default', amount=1, cost=0, 
                 buyer=None, date=datetime.date.today(), paid=False,
                 id_=None):
        self.name = name
        self.amount = amount
        self.cost = cost
        self.buyer = buyer
        self.date = date
        self.paid = paid
        self.id = id_
        
    
    def __repr__(self):
        return f'{self.date.strftime("%d.%m.%Y")} | {self.name} x{self.amount}'
    


class ToolTip(object):
    '''
    create a tooltip for a given widget
    https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
    '''
    def __init__(self, widget, text='widget info'):
        self.waittime = TOOLTIP_DELAY
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()
            

class MyDialog:
    def __init__(self, parent, title='default', text='default'):
        top = self.top = tk.Toplevel(parent)
        tk.Label(top, text=text).pack()

        self.e = tk.Entry(top)
        self.e.pack(padx=5)

        b = tk.Button(top, text="OK", command=self.ok)
        b.pack(pady=5)

    def ok(self):
        print("value is", self.e.get())
        self.top.destroy()
        


root = tk.Tk()
root.geometry('900x600')
root.resizable(width=False, height=False)
app = App(root)
root.protocol("WM_DELETE_WINDOW", app.client_exit)
root.report_callback_exception = app.show_error
root.mainloop()

