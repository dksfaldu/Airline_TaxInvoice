# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 23:25:35 2022

@author: dikes
"""

import pandas as pd
import re


def copy_product_line(final_df,column_name,copy_column_name):
    
    for i in range(1,len(final_df)):
        
        prev_row = final_df.iloc[i-1]
        row = final_df.iloc[i]
        Product_name = row[copy_column_name]
        Prev_Product_name = prev_row[copy_column_name]
        Pack_name = row[column_name]
        
        if Product_name == "" and Pack_name != "":
            final_df.loc[i,copy_column_name] = Prev_Product_name
        
    return final_df
        

def merge(prev_row,row):
    
    for index,v1 in prev_row.iteritems():
        
        v2 = row[index]
        
        # print(index,v1,v2)
        if v2 != "":
            if re.search(r"^[\d+\.,]+$",str(v1)) and re.search(r"^[\d+\.,]+$", str(v2)):
                prev_row[index] = v1+v2
            else:
                prev_row[index] = (v1+" "+v2).strip()
    
    return prev_row


def merge_using_distance(final_df,table_data,distance_thresold):
    
    y_min_list = []
    y_max_list = []
    line_number_list = list(set(table_data['line_number']))
    line_number_list.sort()

    for line_number in line_number_list:
        line_df = table_data[table_data['line_number'] == line_number]
        y_min = min(line_df["y"])
        y_max = max(line_df["h"])
        y_min_list.append(y_min)
        y_max_list.append(y_max)
    
    
    final_df["y_min"] = y_min_list
    final_df["y_max"] = y_max_list
    
    final_df["spaceinbetween"] = final_df['y_min'] - final_df['y_max'].shift(1)
    space_inbetween = list(final_df["spaceinbetween"])    
    del final_df["spaceinbetween"],final_df["y_min"],final_df["y_max"]
    
    final_list = []
    prev_row = final_df.iloc[0]
    
    for i in range(1,len(final_df)):
        
        row = final_df.iloc[i]
        distance = space_inbetween[i]
        
        if distance<distance_thresold:
            if len(prev_row)!=0:
                prev_row = merge(prev_row,row)
        else:
            if len(prev_row)==0:
                prev_row = row
            else:
                final_list.append(prev_row)
                prev_row = row
    
    if len(prev_row)>0:
        final_list.append(prev_row)
    
    final_df_new = pd.DataFrame(final_list)
    
    
    return final_df_new


def split_data(row,column,values):
    
    if column in row.index:
        column_value = row[column]
        column_value_list = column_value.split()
        
        if len(column_value_list) == len(values):
            
            for column_name,v in zip(values,column_value_list):
                
                row[column_name] = v
        
        else:
            for column_name in values:
                row[column_name] = ""
    
    return row


def postprocess_table(combined_table,format_values):
    
    
    list_of_columns = list(combined_table.columns)
    
    if "SplitColumns" in format_values:
        
        for column,values in format_values["SplitColumns"].items():
            
            if column in list_of_columns:
                
                index_of_column = list_of_columns.index(column)
                for ind,v1 in enumerate(values):
                    list_of_columns.insert(index_of_column+ind, v1)
                
                list_of_columns.remove(column)
                
                table_data = combined_table.apply(lambda x: split_data(x,column,values),axis=1)
                
                table_data = table_data[list_of_columns]
                
                combined_table = table_data.copy()
            
    return combined_table






