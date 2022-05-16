# -*- coding: utf-8 -*-
"""
Created on Tue Jun 15 20:08:55 2021

@author: Dikeshkumar.Faldu
"""


import pandas as pd
import re
from fuzzywuzzy import fuzz


from Table_header_footer_search import find_table_next_pages,find_starting_point
from postprocessing import postprocess_table,merge_using_distance,copy_product_line


def find_width_of_columns(header_data, column_name):
    width_of_columns = []
    header_data.reset_index(drop=True, inplace=True)
    
    header_data = header_data.apply(lambda x:filter_headers(x,column_name),axis=1)

    header_data = header_data[header_data['Flag']==1]
        
    header_data["Columns"] = 0
    for ind,header in enumerate(column_name):
        
        header = column_name[ind]
        h_list = header.lower().split()
        # print(h_list)
        temp_df = header_data[header_data["Columns"]==0]
        
        for i in range(1,len(h_list)+2):
                        
            row_df = temp_df.iloc[:i,]
            out_list = [s.lower().strip() for s in row_df["output"]]
            new_out_list = []
            for ff in out_list:
                new_out_list.extend(ff.split())
            index_list = list(row_df.index)
            # print(h_list,out_list)
            if fuzz.token_set_ratio(h_list, new_out_list) == 100 and len(new_out_list)>=len(h_list):
                # print("#############")
                width_of_columns.append([min(row_df['x']), max(row_df['w'])])
                if len(index_list)==1:
                    header_data.loc[index_list[0],"Columns"]=ind+1
                else:
                    header_data.loc[index_list[0]:index_list[-1],"Columns"]=ind+1
                break                    
 

    return width_of_columns


def filter_headers(row, header):
    original_header = [j.lower() for j in header]
    header_list = " ".join(header).strip().lower().split()
    output = row['output'].lower().strip()
    
    output = re.sub(r"\s+"," ",output)
    if output in header_list or output in original_header:
        row['Flag'] = 1
        return row
    else:
        for hh in original_header:
            if output in hh:
                row['Flag'] = 1
                return row
        row['Flag'] = 0

    return row

def update_header_data(header_data,h_list,header,width_of_columns,ind):
    flag = False
    temp_df = header_data[header_data["Columns"]==0]
    
    if len(temp_df)>0:
        index_zero = list(temp_df.index)[0]
        row_df = temp_df.iloc[0]
        out_put = re.sub("\s+"," ",row_df["output"].lower()).strip()
        if out_put == header.lower():
             header_data.loc[index_zero,"Columns"] = ind+1
             width_of_columns.append([row_df['x'], row_df['w']])
             flag = True
             return flag,header_data,width_of_columns
        
        row_df = temp_df.iloc[:len(h_list),]
        
        
        out_list = [s.lower().strip() for s in row_df["output"]]
        index_list = list(row_df.index)
        if fuzz.token_set_ratio(h_list, out_list) == 100:
            
            width_of_columns.append([min(row_df['x']), max(row_df['w'])])
            header_data.loc[index_list[0]:index_list[-1],"Columns"]=ind+1
            flag = True
        else:
            header_data.loc[index_list[0],"Columns"] = -1

        return flag,header_data,width_of_columns
    
    return True,header_data,width_of_columns

def find_width_of_column_multipline(header_data, column_name):
    
    header_data.reset_index(drop=True, inplace=True)
    
    header_data = header_data.apply(lambda x:filter_headers(x,column_name),axis=1)

    header_data = header_data[header_data['Flag']==1]
    
    header_data = header_data.sort_values(['x'], ascending=[True])

    header_data["Columns"] = 0
    width_of_columns = []
    for ind,header in enumerate(column_name):
        # print(header)
        flag = False
        h_list = header.lower().split()
        
        while not flag:
            
            flag,header_data,width_of_columns = update_header_data(header_data,h_list,header,width_of_columns,ind)

    return width_of_columns

def column_mapping(row, width_columns, column_name,txt_allign):
    mid_point = row['middle_x']
    end_point = row['w']
    start_point = row['x']
    mid_list = []
    
    # first_columns = column_name[0]
            
    priority_cols = []
    mid_range = []
    other_range = []
    for ind,width in enumerate(width_columns):
        mid_p = (width[0] + width[1]) / 2.00
        
        if ind < len(width_columns)-1:
            next_width = width_columns[ind+1]
            
            if txt_allign == "r":
            
                if start_point > width[1] and end_point < next_width[0]:
                    priority_cols.append(ind+1)
        

        if ind == 0 and (end_point <= width[0] or start_point <= width[0]):
            row['Column'] = 1
            return row
        
        if mid_point >= width[0] and mid_point <= width[1]:
            mid_range.append(ind+1)
            # row['Column'] = ind + 1
            # return row
        
        if start_point <= width[1] and start_point >= width[0]:
            other_range.append(ind+1)
            # row['Column'] = ind + 1
            # return row

        if end_point <= width[1] and end_point >= width[0]:
            other_range.append(ind+1)
            # row['Column'] = ind + 1
            # return row
        
        mid_list.append(abs(mid_p - mid_point))

    if len(priority_cols)>0:
        row["Column"] = priority_cols[0]
        return row

    if len(mid_range)>0:
        row["Column"] = mid_range[0]
        return row
    
    if len(other_range)>0:
        row["Column"] = other_range[0]
        return row
        

    
    row['Column'] = mid_list.index(min(mid_list)) + 1
    return row


def make_list(line_df, list_length,txt_allign,formats):
    line_list = []
    count = 0
    for i in range(1, list_length + 1):
        row = line_df[line_df['Column'] == i]
        if len(row) == 1:
            output = row['output'].iloc[0].strip()
            output = re.sub(r"document|footer|text","",output,flags=re.I)

            line_list.append(output)
            count = count+1
        else:
            update_flag = True
            if formats in ["F64","F63_1"] and i>3 and i < list_length:
                next_row = line_df[line_df['Column'] == i+1]
                if len(next_row) == 1:
                    next_data = next_row['output'].iloc[0].strip().split(" ",1)
                    if len(next_data)==2:
                        update_flag = False
                        line_list.append(next_data[0])
                        line_df.loc[line_df['Column'] == i+1, 'output'] = next_data[1]
            
            if update_flag:
                line_list.append("")
    
    line_list.append(count)
    return line_list

def increase_width_of_special_cols(width_columns,column_name,special_cols,format_values):
    
    if "PixelDifference" in format_values:
        diff_pixel = format_values["PixelDifference"]
    else:
        diff_pixel = 10
    
    if len(special_cols)==1:
        colname = special_cols[0]
        index_value = column_name.index(colname)
        
        if index_value == 0:
            
            w_curr = width_columns[index_value][1]
            x_next = width_columns[1][0]
            
            if abs(x_next-w_curr) > 10:
                width_columns[index_value][1] = x_next-diff_pixel
        
        elif index_value > 0:
            
            w_prev = width_columns[index_value-1][1]
            x_curr = width_columns[index_value][0]
            if abs(w_prev-x_curr) > diff_pixel:
                width_columns[index_value][0] = w_prev+diff_pixel
                
            w_curr = width_columns[index_value][1]

            x_next = width_columns[index_value+1][0]
            if abs(x_next-w_curr) > diff_pixel:
                width_columns[index_value][1] = x_next-diff_pixel
    
    else:
        for colname in special_cols:
            index_value = column_name.index(colname)
        
            if index_value == 0:
                
                w_curr = width_columns[index_value][1]
                x_next = width_columns[1][0]
                
                if abs(x_next-w_curr) > 10:
                    width_columns[index_value][1] = x_next-15
            
            elif index_value > 0:
                
                w_prev = width_columns[index_value-1][1]
                x_curr = width_columns[index_value][0]
                if abs(w_prev-x_curr) > 10:
                    width_columns[index_value][0] = w_prev+15
                    
                w_curr = width_columns[index_value][1]
    
                x_next = width_columns[index_value+1][0]
                if abs(x_next-w_curr) > 10:
                    width_columns[index_value][1] = x_next-15
        

    return width_columns


def make_table(width_columns, table_data, column_name,formats,format_values,txt_allign):
    final_value = []
    special_cols = format_values["SpecialCols"]

    # print("width_columns :: ",width_columns)
    width_columns = increase_width_of_special_cols(width_columns,column_name,special_cols,format_values)
    # print("width_columns :: ",width_columns)
    
    table_data_new = table_data.apply(lambda x: column_mapping(x, width_columns,column_name,txt_allign), axis=1)

    table_df = table_data_new.groupby(['line_number', 'Column'])['output'].apply(lambda x: ' '.join(x)).reset_index()

    line_number_list = list(set(table_df['line_number']))
    line_number_list.sort()

    for line_number in line_number_list:
        line_df = table_df[table_df['line_number'] == line_number]

        line_list = make_list(line_df, len(column_name),txt_allign,formats)

        final_value.append(line_list)

    final_table = pd.DataFrame(final_value)

    output_df = pd.DataFrame()
    
    new_cols_list = column_name.copy()
    new_cols_list.append("CountOfValues")
    for original_name, expected in zip(list(final_table.columns), new_cols_list):
        ind = 1
        new_cols = expected 
        while new_cols in output_df.columns:
            new_cols = expected+"_"+str(ind)
            ind = ind+1
        
        if expected != "Extra":
            output_df[new_cols] = final_table[original_name]

    return output_df


def Transpose_df(final_df, Total_Value):
    final_df = final_df.T

    new_df = final_df[[final_df.columns[Total_Value]]]

    new_df.columns = ["Total"]
    new_df['Description'] = new_df.index

    new_df.reset_index(inplace=True, drop=True)

    return new_df


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



def postprocess(final_df,flag):
    
    if flag=="t":
        final_list = []
        prev_row = []
        for i in range(len(final_df)):
            
            row = final_df.iloc[i]
            count = row["CountOfValues"]
            
            if count<3:
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
    
    if flag=="b":
        final_list = []
        prev_row = []
        for i in range(len(final_df)):
            
            row = final_df.iloc[i]
            count = row["CountOfValues"]
            
            if count<3:
                if len(prev_row)==0:
                    prev_row = row
                else:
                    prev_row = merge(prev_row,row)
                    
            else:
                if len(prev_row)!=0:
                    prev_row = merge(prev_row,row)
                    final_list.append(prev_row)
                    prev_row = []
                else:
                    final_list.append(row)
                    
        
        final_df_new = pd.DataFrame(final_list)
        return final_df_new
    
    if flag=="m":
        final_list = []
        prev_row = []
        row_count = 0
        found = False
        for i in range(len(final_df)):
            
            row = final_df.iloc[i]
            count = row["CountOfValues"]
            # print(count)
            if count<3:
                if row_count == 0 and len(prev_row) == 0:
                    row_count = 1
                    prev_row = row
                
                elif len(prev_row)>0 and row_count>0: 
                    if found:
                        row_count = row_count-1
                    else:
                        row_count = row_count+1
                    
                    prev_row = merge(prev_row,row)
                    
                    if row_count == 0:
                        final_list.append(prev_row)
                        found = False
                        prev_row = []      
                    
            else:
                if len(prev_row)!=0:
                    found = True
                    prev_row = merge(prev_row,row)
                
                else:
                    found=False
                    row_count = 0
                    final_list.append(row)
            
            # print(i,row_count,found)
                    
        
        final_df_new = pd.DataFrame(final_list)
        return final_df_new
        

def ignore_values(table_data,width_columns,format_values):
    
    min_x = width_columns[0][0]    
    last_width = width_columns[-1][-1]
    
    flag = format_values["IgnoreData"]
    
    thresold = -1
    if "IgnoreData_Threshold" in format_values:
        thresold = format_values["IgnoreData_Threshold"]
    
    if flag.lower() == "after":
        if thresold == -1:
            thresold = 5
        table_data_new = table_data[table_data['x']<last_width+thresold]
        return table_data_new
        
        
    if flag.lower() == "before":
        if thresold == -1:
            thresold = 1
        table_data_new = table_data[table_data['x']>min_x-thresold]
        return table_data_new
    
    return table_data



def find_table_recursive(page_number,all_tables,formats,format_values,ContinueTableWithoutHeader,page_data,continue_table,width_columns,config_dict):
    
    
    if formats == "":
        status,formats,format_values, column_name, table_data, header_data, flag, footerfound, headerfound,end_line = find_starting_point(page_data,continue_table,config_dict)
        print("Format :: ",formats)
        
    else:
        status,formats,format_values, column_name, table_data, header_data, flag, footerfound, headerfound,end_line = find_table_next_pages(page_data,continue_table,formats,format_values)
    
    print("Table Found :: ",status, len(table_data))
    if status and len(table_data)>0:
        ContinueTableWithoutHeader = format_values["ContinueTableWithoutHeader"]
        
        if "TextAllign" in format_values:
            txt_allign = format_values["TextAllign"]
        else:
            txt_allign = ""
       
        if headerfound:
            if flag == 0:
                width_columns = find_width_of_columns(header_data, column_name)

            if flag == 1:
                width_columns = find_width_of_column_multipline(header_data, column_name)


        if len(width_columns) == len(column_name):
            
            if "IgnoreData" in format_values:
                table_data = ignore_values(table_data,width_columns,format_values)

            
            # max_distance = find_max_space(width_columns)
            
            if "FinalHeader" in format_values:
                column_name = format_values["FinalHeader"]
        
            final_df = make_table(width_columns, table_data, column_name ,formats, format_values,txt_allign)
            
            final_df = final_df.replace("Page 1 / 4","")


            if "DistanceThresold" in format_values:
                final_df = merge_using_distance(final_df,table_data,format_values["DistanceThresold"])
        
            elif "MultiLine" in format_values:
                final_df = postprocess(final_df,format_values["MultiLine"].lower())
                
            # if "CopyData" in format_values:
            #     copy_column_name,column_name = format_values["CopyData"]
            #     final_df = copy_product_line(final_df,column_name,copy_column_name)
            
            if "DefaultValues" in format_values:
                for kk,vv in format_values["DefaultValues"].items():
                    final_df[kk] = vv
            
            final_df["page_no"] = page_number
            print("Table Size :: ",len(final_df))
            all_tables.append(final_df)

        else:
            print("Differetn Size :: ",len(width_columns),len(column_name))
            
    
    if ContinueTableWithoutHeader and headerfound and not footerfound:
        
        continue_table = True
    
    if footerfound:
        continue_table = False
        temp_data = page_data[page_data["line_number"]>end_line]
        if len(temp_data)>5:
            all_tables,formats,format_values,continue_table,width_columns = find_table_recursive(page_number,all_tables,formats,format_values,ContinueTableWithoutHeader,temp_data,continue_table,width_columns,config_dict)

        
    return all_tables,formats,format_values,continue_table,width_columns

def Extract_Table_pdf(df,config_dict):
    
    all_tables = []
    format_values = {}
    formats = ""
    
    ContinueTableWithoutHeader = False
    continue_table = False
    
    width_columns = []
    for page_number in set(df['page_number']):
        # print(continue_table)
        print("############################################")
        print("Page Number :: ",page_number)
        page_data = df[df['page_number'] == page_number]

        all_tables,formats,format_values,continue_table,width_columns = find_table_recursive(page_number,all_tables,formats,format_values,ContinueTableWithoutHeader,page_data,continue_table,width_columns,config_dict)


    if len(all_tables) > 0:
        
        combined_table = pd.concat(all_tables)
        
        combined_table = postprocess_table(combined_table,format_values)
        
        del combined_table["page_no"],combined_table["CountOfValues"]
 
        return combined_table #json.loads(combined_table.to_json(orient="records"))

    return pd.DataFrame()


# def check_row(row_data, required_keys):
#     for key in required_keys:

#         if key not in row_data or row_data[key].strip() == "":
#             return False

#     return True


# def combine_json(json1, json2):
#     for key, value in json1.items():

#         if key in json2:
#             json1[key] = (value + " " + json2[key]).strip()

#     return json1


# def postprocessing(list_of_json, agent, required_keys):
#     final_list = []

#     prev_data = list_of_json[0]

#     for row_data in list_of_json[1:]:

#         if check_row(row_data, required_keys):
            
#             if check_row(prev_data,required_keys):
#                 final_list.append(prev_data)
#             prev_data = row_data.copy()

#         else:
#             prev_data = combine_json(prev_data, row_data)
    
#     #if check_row(prev_data,required_keys):
#     final_list.append(prev_data)

#     return final_list

    
# if __name__ == '__main__':
    
    
#     pdf_file = r"D:/Work/UpWork/OrderStack/Data/7cddaf41-1c4e-4fbe-8432-dd0cecdc8a9e.pdf"


#     table_header = [
#         [['Item', 'Pack', 'Dec', 'Nov', 'Op.', 'Pur', 'SP', 'Sale', 'SS', 'Br Bsc qt', 'Cr Db', 'Bal.', 'BVal', 'SVal', 'Order'],
#           ['For Manufacturer'],
#           ['Item', 'Pack', 'Dec', 'Nov', 'Op.', 'Pur', 'SP', 'Sale', 'SS', 'Br Bsc qt', 'Cr Db', 'Bal.', 'BVal', 'SVal', 'Order']],
        
#         [["ITEM NAME","PACK/ GRAD E","OPENING STOCK-1","PURCHA SE-1","PURCHA SE Value-1","PUR.ret URN-1","SALE-1","SALE RETURN- 1","SALE VALUE-1","CLOSING STOCK-1","CLOSING VALUE-1"],
#           [],
#           ["Item","PACK/ GRAD E","OPENING STOCK-1","PURCHA SE-1","PURCHA SE Value-1","PUR.ret URN-1","SALE-1","SALE RETURN- 1","SALE VALUE-1","CLOSING STOCK-1","CLOSING VALUE-1"]],
        
#         [['Item', 'Oct 21', 'Nov 21', 'OpStk', 'P.Qty', 'P.Val', 'P.Sch', 'S.Qty', 'S.Sch', 'S.Val', 'DbQty', 'StkAd', 'ClStk', 'ClVal', 'Order'],
#           [],
#           ['Item', 'Oct 21', 'Nov 21', 'OpStk', 'P.Qty', 'P.Val', 'P.Sch', 'S.Qty', 'S.Sch', 'S.Val', 'DbQty', 'StkAd', 'ClStk', 'ClVal', 'Order']],
        
#         [['Sr', 'Item Name', 'Pkg.', 'Opening Stock', 'Op.Stock value', 'Purchase Qty', 'Purchase amount', 'Sale Qty.',  'Sale Amount', 'Stk Trf Rect.', 'Stk Trf Issue', 'Closing Stock', 'Rate For Valuation', 'Stock Value'],
#           ["Closing Stock"],
#           ['Sr', 'Item', 'Pkg.', 'Opening Stock', 'Op.Stock value', 'Purchase Qty', 'Purchase amount', 'Sale Qty.',  'Sale Amount', 'Stk Trf Rect.', 'Stk Trf Issue', 'Closing Stock', 'Rate For Valuation', 'Stock Value']],
        
#         [["CODE" ,"ITEM DESCRIPTION" ,"OPENING" ,"RECEIPT" ,"ISSUE" ,"CLOSING"],
#           [],
#           ["CODE" ,"Item" ,"OPENING" ,"RECEIPT" ,"ISSUE" ,"CLOSING"]]
#     ]


