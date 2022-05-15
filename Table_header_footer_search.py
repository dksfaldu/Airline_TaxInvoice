# -*- coding: utf-8 -*-
"""
Created on Sat Mar  5 10:37:46 2022

@author: dikes
"""
import re
import pandas as pd

def get_subvalue(v,listofvalues):
    
    for v1 in listofvalues:
        
        if v1.lower() in v.lower():
            return v1
        
    return ""


def common_elements(list1, list2):
    result = []
    for element in list1:
                   
        if element in list2:
            list2.remove(element)
            result.append(element)
            

    
    return len(result)


def redefine_header(page_data, header_list, header_start, header_end):
    header_data = page_data[(page_data['line_number'] >= header_start) & (page_data['line_number'] <= header_end)]
    for i in range(header_start + 1, header_end):

        temp_df2 = header_data[header_data['line_number'] >= i]
        string_list = [k.strip().lower() for k in list(temp_df2['output'])]

        count1 = common_elements(header_list.copy(), string_list.copy())

        if count1 == len(header_list):
            header_start = i

        if count1 < len(header_list):
            break

    return header_start



def is_sub_with_gap(sub, lst):
    ln, j = len(sub), 0
    
    for ele in lst:
        
        if j < len(sub):
            curr_ele = sub[j]
    
           
            if curr_ele in ele:
            
                j += 1
        
        if j == ln:
        
            return True
    
    return False

def update_strlist(string_list):
    
    new_list = []
    
    for string1 in string_list:
        l1 = string1.split()
        if len(l1)>1:
            new_list.extend(l1)
        else:
            new_list.append(string1)
    
    return new_list
    

def find_starting_point(page_data,continue_table,config_dict):

    footer_found = False
    header_found = False
    flag = 0
    
    for formats in config_dict:
        
        format_values = config_dict[formats]
        header_list_init = format_values["HeaderList"]
        footer_list = format_values["FooterList"]
        
        if len(header_list_init)>0:
            header = " ".join(header_list_init).strip()
            if len(footer_list) == 0:
                footer = "endofpage"
            else:
                footer = "|".join(footer_list).strip().lower()
            # Column_name = header_footer[2]
            start_line = -1
            end_line = -1
            header_end = -1
            header_start = -1
            if continue_table:
                start_line = 0
                header_start = 0
                header_end = 0
                
            header_list = header.lower().split()
    
            for line_number in set(page_data['line_number']):
    
                temp_df2 = page_data[page_data['line_number'] == line_number]
                temp_df2 = temp_df2.sort_values(['x'], ascending=[True])
                string_list = [k.strip().lower() for k in list(temp_df2['output'])]
                # string_list = update_list(string_list)
                
                string_list = update_strlist(string_list)
                
                count1 = common_elements(header_list.copy(), string_list.copy())
                
                # print(count1)
                
                if start_line == -1 and (is_sub_with_gap(header_list, string_list) or  count1 == len(header_list)):
                    header_end = line_number
                    header_start = line_number
                    header_found = True
    
                elif start_line == -1 and count1 > 0:
                    
                    header_start = line_number
                    
                    for new_line in range(line_number + 1, line_number + 5):
                        # print(new_line)
                        temp_df2 = page_data[page_data['line_number'] == new_line]
                        temp_df2 = temp_df2.sort_values(['x'], ascending=[True])
                        string_list2 = [k.strip().lower() for k in list(temp_df2['output'])]
                        
                        if not is_sub_with_gap(header_list, string_list2):
                            
                            string_list.extend(string_list2)
        
                            # print(string_list)
                            count2 = common_elements(header_list.copy(), string_list.copy())
                            # print(count2)
                            # print(line_number,count2,len(header_list))
                            if count2 == len(header_list):
                                header_end = new_line
                                flag = 1
                                header_start = redefine_header(page_data, header_list, header_start, header_end)
                                header_found = True
                                break
        
                            elif count1 == count2:
                                header_start = -1
                                break
                            else:
                                count1 = count2
                            
                            
                        else:
                            header_start = -1
                            break
    
                if header_start != -1 and header_end != -1 and start_line == -1:
                    start_line = header_end
    
                elif start_line != -1 and footer == "endofpage":
    
                    end_line = max(list(set(page_data['line_number'])))+1
    
                elif start_line != -1 and re.search(footer, " ".join(string_list).lower(), flags=re.I):
                    
                    # print(footer,string_list)
                    end_line = line_number
                    footer_found = True
                    
                if start_line != -1 and end_line != -1:
                    break
            
            if end_line == -1:
                
                end_line = max(page_data["line_number"])+1
            
            if start_line != -1 and end_line != -1:
                print(header_start,header_end,end_line)
                table_data = page_data[(page_data['line_number'] > start_line) & (page_data['line_number'] < end_line)]
                header_data = page_data[
                    (page_data['line_number'] >= header_start) & (page_data['line_number'] <= header_end)]
                
                # header_list_init = update_header_list(header_data,header_list_init,header_list)
                format_values["FirstHeader"] = header_list_init
                
                return True, formats,format_values,header_list_init, table_data, header_data, flag,footer_found,header_found,end_line

    return False,"",{}, [], pd.DataFrame(), pd.DataFrame(), flag,footer_found,header_found,end_line


def find_table_next_pages(page_data,continue_table,formats,format_values):

    footer_found = False
    header_found = False
    flag = 0
    
    
    footer_list = format_values["FooterList"]
    
    
    if len(footer_list) == 0:
        footer = "endofpage"
    else:
        footer = "|".join(footer_list).strip().lower()
    # Column_name = header_footer[2]
    start_line = -1
    end_line = -1
    header_end = -1
    header_start = -1
    header_list_init = format_values["HeaderList"]
    if continue_table:
        start_line = 0
        header_start = 0
        header_end = 0
        header_list_init = format_values["FirstHeader"]
        
    
    header = " ".join(header_list_init).strip()
    header_list = header.lower().split()

    for line_number in set(page_data['line_number']):

        temp_df2 = page_data[page_data['line_number'] == line_number]
        temp_df2 = temp_df2.sort_values(['x'], ascending=[True])
        string_list = [k.strip().lower() for k in list(temp_df2['output'])]
        # string_list = update_list(string_list)
        
        count1 = common_elements(header_list.copy(), string_list.copy())
        
        if start_line == -1 and (is_sub_with_gap(header_list, string_list) or count1 == len(header_list)):
            header_end = line_number
            header_start = line_number
            header_found = True

        elif start_line == -1 and count1 > 0:
            
            header_start = line_number
            
            for new_line in range(line_number + 1, line_number + 5):
                temp_df2 = page_data[page_data['line_number'] == new_line]
                temp_df2 = temp_df2.sort_values(['x'], ascending=[True])
                string_list2 = [k.strip().lower() for k in list(temp_df2['output'])]
                
                if not is_sub_with_gap(header_list, string_list2):
                    
                    string_list.extend(string_list2)

                    # print(string_list)
                    count2 = common_elements(header_list.copy(), string_list.copy())

                    # print(line_number,count2,len(header_list))
                    if count2 == len(header_list):
                        header_end = new_line
                        flag = 1
                        header_start = redefine_header(page_data, header_list, header_start, header_end)
                        header_found = True
                        break

                    if count1 == count2:
                        header_start = -1
                        break
                else:
                    header_start = -1
                    break

        if header_start != -1 and header_end != -1 and start_line == -1:
            start_line = header_end

        elif start_line != -1 and line_number>start_line and footer == "endofpage":

            end_line = max(list(set(page_data['line_number'])))+1

        elif start_line != -1 and line_number>start_line and re.search(footer, " ".join(string_list).lower(), flags=re.I):

            end_line = line_number
            footer_found = True
            
        if start_line != -1 and end_line != -1:
            break
    
    if end_line == -1:
        
        end_line = max(page_data["line_number"])+1
    
    if start_line != -1 and end_line != -1:
        print(header_start,header_end,end_line)
        table_data = page_data[(page_data['line_number'] > start_line) & (page_data['line_number'] < end_line)]
        header_data = page_data[
            (page_data['line_number'] >= header_start) & (page_data['line_number'] <= header_end)]
        
        # header_list_init = update_header_list(header_data,header_list_init,header_list)
        
        return True, formats,format_values,header_list_init, table_data, header_data, flag,footer_found,header_found,end_line

    return False,formats,format_values, [], pd.DataFrame(), pd.DataFrame(), flag,footer_found,header_found,-1
