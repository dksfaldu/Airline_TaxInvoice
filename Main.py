# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 17:07:46 2021

@author: Dikeshkumar.Faldu
"""

import json
import re
from datetime import datetime


from PDF_Reader_New import read_list,add_line_number
from Functions import LineBetween,find_isp,simple_field,find_values,extract_block_vals,get_line_values
from FindValues_upsidedown import find_word
from Table_Extractor_Rule import Extract_Table_pdf
from normalise import convert_to_format

import os


json_file = "Field_information_pdf.json"

output_date_format = "%d-%b-%Y"

cwd = os.path.dirname(__file__)
PDF_folder = os.path.join(cwd,"PDFs")



def extract_table_details(df, ISP_json):

    ## Reading the config of line items.
    if "table_config" in ISP_json:
        config_dict = ISP_json["table_config"]
        
        ## Extracting the line items through this function
        table_data = Extract_Table_pdf(df, config_dict)
        
        return table_data.to_dict("records")
    
    return []


def find_details(output_dict, sentence_level_data, page_level_data, df, ISP_json,ISPName):

    
    # 
    if "LineBetween" in ISP_json:
        output_dict = LineBetween(sentence_level_data, ISP_json["LineBetween"], output_dict)

    ## Simple fields which can be extracted using this function
    if "Simple" in ISP_json:
        output_dict = simple_field(sentence_level_data, page_level_data, ISP_json["Simple"], output_dict,ISPName)

    ## Extracting UpSide down fields which is not available for Airline Invoices. Ignore this function
    if "Updown" in ISP_json and len(df) > 0:

        for key, value in ISP_json["Updown"].items():
            if key not in output_dict or output_dict[key] == "":
                v1, v2 = find_word(df, value)
                if v1 != "":
                    output_dict[key] = v1
                    #output_dict[key + "_wordlocation"] = v2

    ## Divide the sector value to From and To.
    if "sector" in output_dict:
        sector = output_dict["sector"]
        state_list = sector.split("-")
        if len(state_list) == 2:
            output_dict["flight_from"] = state_list[0].strip()
            output_dict["flight_to"] = state_list[1].strip()
            del output_dict["sector"]
        else:
            state_list = sector.split(" ")
            if len(state_list) == 2:
                output_dict["flight_from"] = state_list[0].strip()
                output_dict["flight_to"] = state_list[1].strip()
                del output_dict["sector"]


    ## Address fields which is extracted from starting of the line
    if "Address" in ISP_json and len(df) > 0:

        for key, value_list in ISP_json["Address"].items():

            if (key not in output_dict or output_dict[key] == "") and len(value_list)==3:
                
                out_address = get_line_values(sentence_level_data,value_list[0],value_list[1],value_list[2])
                
                if out_address != "":
                    output_dict[key] = out_address
                
    
    new_out_dict = {}
    new_out_dict["supplier_details"] = {}
    new_out_dict["receiver_details"] = {}
    table_dict = {}
    for key,value in output_dict.items():
        
        if re.search(r"\(supplier\)",key,flags=re.I):
            key = re.sub(r"\(supplier\)","",key,flags=re.I).strip()
            new_out_dict["supplier_details"][key] = value
        elif re.search(r"\(Receiver\)",key,flags=re.I):
            key = re.sub(r"\(Receiver\)","",key,flags=re.I).strip()
            new_out_dict["receiver_details"][key] = value
        elif re.search(r"\(table\)",key,flags=re.I):
            key = re.sub(r"\(table\)","",key,flags=re.I).strip()
            table_dict[key] = value
        
        else:
            new_out_dict[key] = value
    
    
    detailed_cost_list = extract_table_details(df, ISP_json)
    
    if len(detailed_cost_list) > 0:
        detailed_cost_list,total_dict = convert_to_format(detailed_cost_list)
        new_out_dict["detailed_cost"] = detailed_cost_list
        new_out_dict["total_cost"] = total_dict
    
    elif len(table_dict)>0:
        detailed_cost_list,total_dict = convert_to_format([table_dict])
        new_out_dict["detailed_cost"] = detailed_cost_list
        new_out_dict["total_cost"] = total_dict

    
    return new_out_dict




def extract_bill(pdf_file_path):
    output_dict = {}
    with open(os.path.join(cwd, json_file)) as fp:
        field_info_json = json.load(fp)

    df,page_level_data,sentence_level_data = read_list(pdf_file_path)

    ## Find out the Supplier name 
    ISPName = find_isp(field_info_json, sentence_level_data)

    if ISPName in field_info_json:
        
        
        print(ISPName)
        ## Take the configuration of the supplier
        ISP_json = field_info_json[ISPName]

        ## If any different thresold used for that supplier then again read the document with new threshold
        if "LineThreshold" in ISP_json:
            df,page_level_data,sentence_level_data = read_list(pdf_file_path,ISP_json["LineThreshold"])
        
        output_dict["name (Supplier)"] = ISPName

        ## Extract all the deatils
        output_dict = find_details(output_dict, sentence_level_data, page_level_data, df, ISP_json,ISPName)
        ## Process it further
        output_dict["Status"] = "Success"
        output_dict["StatusMessage"] = "Success"

    else:

        print("Agent not found")
        output_dict["Status"] = "Failed"
        output_dict["StatusMessage"] = "ISP Details not found."

    return output_dict



if __name__ == '__main__':
    pdf_file_path = r"D:/Work/UpWork/John/Data/Vistara.pdf"
    
    output_json = extract_bill(pdf_file_path)
    
    outputjson_file = re.sub(r"pdf$","json",pdf_file_path,flags=re.I)
    with open(outputjson_file,"w") as fp:
        json.dump(output_json, fp)
    
    