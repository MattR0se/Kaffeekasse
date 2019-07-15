# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 11:51:49 2019

@author: Christian Post
"""
# TODO: row index as an attribute of Data?
# make iterrows return a row object to access column names for each row


import csv
import os
import datetime


def euro(number):
    return f'{number:.2f} €'.replace('.',',')


def date_s(date):
    # accepts datetime, returns formatted string
    return str(date.strftime("%d.%m.%Y"))


def convert_to_date(date):
    if type(date) == datetime.date:
        return date
    else:
        return date.date()



class Data():
    def __init__(self, data=None, columns=[]):
        self.data = {}
        self.columns = columns # column names
        self.shape = (0, 0)
        if data:
            if columns:
                for i in range(len(data[0])):
                    self.data[self.columns[i]] = []
            else:
                for i in range(len(data[0])):
                    self.columns.append(str(i))
                    self.data[str(i)] = []

            for i, row in enumerate(data):
                for j, col in enumerate(row):
                    self.data[self.columns[j]].append(col)
            self.shape = (len(data), len(data[0]))
            print(self.data)
            for col in self.columns:
                setattr(self, col, self.data[col])
                

    def write_csv(self, filename, decimal=',', sep=';', head=True):
        # writes self.data to a give csv file
        with open(filename, 'w+', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=sep)
            if head:
                writer.writerow(self.columns)
            for i, row in self.iterrows():
                str_row = [str(r).replace('.', decimal) for r in row]
                writer.writerow(str_row)


    def read_csv(self, filename, head=True, column_names=[],
                 decimal=',', parse_dates=[], date_parser=None):
        # make an array to store the csv data with shape (rows, columns)
        if not os.path.isfile(filename):
            print(f'Error: "{filename}" does not exist.')
            return
        file_data = []
        try:
            with open(filename, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                for row in reader:
                    file_data.append(row)
        except csv.Error:
            print(f'Error: Could not read "{filename}"')
            return
        if len(file_data) == 0:
            print(f'Error: "{filename}" does not contain any data.')
            return
        
        self.shape = (len(file_data), len(file_data[0]))
        if column_names and len(column_names) != self.shape[1]:
            print('Error: Mismatching length of column names ' +
                  f'(Got {len(column_names)} instead of {self.shape[1]}).')
            return
        
        if head and not column_names:
            # set or store column names
            self.columns = file_data[0]
            file_data = file_data[1:]
            for col in self.columns:
                self.data[col] = []
        elif head and column_names:
            # TODO: check if len of column names is compatible
            self.columns = list(column_names)
            file_data = file_data[1:]
            for col in self.columns:
                self.data[col] = []
        elif not head and column_names:
            self.columns = list(column_names)
            for col in self.columns:
                self.data[col] = []
        else:
            for i in range(len(file_data[0])):
                self.columns.append(str(i))
                self.data[str(i)] = []
                
        
        for i, row in enumerate(file_data):
            for j, col in enumerate(row):
                # check if data is boolean
                if col == 'True':
                    self.data[self.columns[j]].append(True)
                    continue
                elif col == 'False':
                    self.data[self.columns[j]].append(False)
                    continue
                
                # check if data is date
                if parse_dates and self.columns[j] in parse_dates:
                    self.data[self.columns[j]].append(date_parser(col))
                    continue
                
                # convert numbers to float or int
                value = col.replace(decimal, '.')
                try:
                    value = float(value)
                    if value.is_integer():
                        self.data[self.columns[j]].append(int(value))
                    else:
                        self.data[self.columns[j]].append(value)
                except ValueError:
                    # data is not a number
                    self.data[self.columns[j]].append(col)
        # set attributes of data object based on column names
        for col in self.columns:
            setattr(self, col, self.data[col])
            
    
    class Row():
        def __init__(self, data, columns):
            self.data = data
            self.columns = columns
            for i, col in enumerate(self.columns):
                setattr(self, col, data[i])
        
        def __getitem__(self, key):
            return self.data[self.columns.index(key)]
        
        def __iter__(self):
            return iter(self.data)
    
    
    def iterrows(self):
        # similar to iterrows
        # but yields a row object as well as the index
        # TODO: maybe replace iterrows with this
        v = list(self.data.values())
        if len(v) == 0:
            return
        i = 0
        while i < len(v[0]):
            data = []
            for col in v:
                data.append(col[i])
            row = self.Row(data, self.columns)
            yield i, row
            i += 1
            
    
    def sort(self, by=None, reverse=False):
        '''
        sorts the rows
        "by" has to be a column name
        '''
        #temp_data = list(self.iterrows())
        temp_data = [list(row) for i, row in self.iterrows()]
        #print(temp_data)
        if not by or by not in self.columns:
            i = 0
        else:
            i = self.columns.index(by)
        temp_data = sorted(temp_data, key=lambda x: x[i], reverse=reverse)
        
        # convert back to self.data structure
        for i, row in enumerate(temp_data):
            for j, col in enumerate(row):
                self.data[self.columns[j]][i] = col
        
        #return temp_data
            
    
    def to_html(self, filename, format_values={}, rename_columns={},
                css=[], column_align={}, caption=None, 
                format_columns={}):
        '''
        construct a html table out of this objects's data
        filename is a valid *.html or *.htm filename
        format_values is a dictionary with column names as keys
          and functions as values that take a single value as an argument
          and return the formatted (or otherwise processed) value
        rename_columns is a dictionary with pairs of
          current col name: new col name
        css is a list of css elements that are inserted into the
          <style> tag
        column_align is a dict with column name: align (left, right, center)
        caption specifies the table's caption
        format_columns is a dictionary with format options for the respective
          columns
        '''
        if len(self.data) == 0:
            # return if this has no data
            print('HTML building aborted: No data')
            return
        if filename[-4:] != 'html' and filename[-3:] != 'htm':
            print(f'Error: "{filename}" is not a valid html file')
            return
        strTable = '<html><head><style>'
        # css table style
        # add classes for alignment
        strTable += ('.right {text-align: right;} ' +
                     '.left {text-align: left;} ' +
                     '.center {text-align: center;}')
        
        for style in css:
            # add css elements to style tag
            strTable += style
        
        strTable += '</style></head><body><table>'
        if caption:
            strTable += f'<caption>{caption}</caption>'
        strTable += '<tr>'
        for col in self.columns:
            # add column names to table header
            if col in rename_columns.keys():
                col = rename_columns[col]
            strTable += f'<th>{col}</th>'
        strTable += '</tr>'
        
        for i, row in self.iterrows():
            # add rows to table
            strRW = '<tr>'
            for col in self.columns:
                strTD = '<td '
                value = row[col]
                if col in format_values.keys():
                    value = format_values[col](value)
                if col in format_columns.keys():
                    strTD += format_columns[col]
                if col in column_align.keys():
                    strTD += f' class=\"{column_align[col]}\">{value}'
                else:
                    strTD += f'>{value}'
                strTD += '</td>'
                strRW += strTD 
            strRW += '</tr>'
            strTable += strRW
        strTable += '</table></body></html>'
        
        with open(filename, 'w') as html_file:
            html_file.write(strTable)

        

if __name__ == '__main__':
    file_path = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(file_path, 'exported_csv', 'staff.csv')
    
    data = Data()
    data.read_csv(filename,
                  head=True,
                  column_names = ['A', 'B', 'C', 'D', 'E'],
                  parse_dates=['date'],
                  date_parser=lambda x: datetime.datetime.strptime(x, '%d.%m.%Y').date())
    
    table_css = [
            'table {border-collapse: collapse;}',
            'table, th, td {border: 1px solid black;}',
            'th, td {text-align: left; padding: 2px 6px 2px 6px;}'
            ]
    
    data.to_html('temp/test.html', 
                 format_values={'payment': euro,
                                 'date': date_s},
                 format_columns={'payment': 'width=400px;'},
                 rename_columns={'number': 'Number', 
                                 'name': 'Name', 
                                 'date': 'Date',
                                 'payment': 'Payment'},
                 css=table_css,
                 column_align={'payment': 'right'})
    
    #data.write_csv('test.csv')
