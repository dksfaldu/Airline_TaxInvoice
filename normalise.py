# -*- coding: utf-8 -*-
"""
Created on Sun May 15 09:50:20 2022

@author: dikes
"""

import re

string_columns = ["sac_code","description","chargecode"]
amount_columns = ["amount","taxable_amount","nontaxable_amount", "discount", "net_amount", "igst_amount","sgst_amount","cgst_amount","igst_percentage","sgst_percentage","cgst_percentage", "total_amount"]
total_columns = ["amount","discount","net_amount","igst_amount","sgst_amount","cgst_amount","total_amount"]
Merging_columns = {
    "amount":["taxable_amount","nontaxable_amount"]
    }

def convert_amount(string):
    
    string = re.sub("[^\d\.]","",str(string))
    if string == "":
        return 0
    # if string == ".":
    #     return 0
    amount = float(string)
    
    return amount

def update_percentage(values):
    
    for amount,per in zip(["igst_amount","sgst_amount","cgst_amount"],["igst_percentage","sgst_percentage","cgst_percentage"]):
        if amount in values and values[amount] == 0:
            values[per] = 0
            
    return values
        

def convert_to_format(list_of_json):
    total_dict = {}
    final_json = []
    total_line = False
    for values in list_of_json:
        
        desc_keys = [key for key in values if re.search("^description",key)]
        
        if len(desc_keys)>1:
            value_list = [values[key] for key in desc_keys]
            
            [values.pop(key) for key in desc_keys]
            
            values["description"] = " ".join(value_list)
        
        for key in amount_columns:
            
            if key in values:
                
                values[key] = convert_amount(values[key])
            elif key in ["discount"]:
                values[key] = 0
        
        
        values = update_percentage(values)
        if "taxable_amount" in values and "nontaxable_amount" in values:
            v1 = values["taxable_amount"]
            v2 = values["nontaxable_amount"]
            values["amount"] = v1+v2
            # if (v1 ==0 and v2 > 0) or (v1 > 0 and v2 == 0 ):
            #     values["amount"] = v1+v2
            #     del values["taxable_amount"],values["nontaxable_amount"]
        
        
        if "net_amount" not in values:
            if "amount" in values:
                values["net_amount"] = values["amount"] - values["discount"]
                
        if "total_amount" not in values:
            total = 0
            for key in ["net_amount", "igst_amount","sgst_amount","cgst_amount"]:
                if key in values:
                    total = total+values[key]
                
            values["total_amount"] = total
        
        string_list  = [values[key] for key in string_columns if key in values]
        
        string_line = (" ".join(string_list)).strip()
        
        
        
        if not total_line and re.search("Total|Grand Total",string_line,flags=re.I):
            total_line = True
            for key in total_columns:
                if key in values:
                    total_dict[key] = values[key]
                    
        
        final_json.append(values)
            
    
    
    if not total_line:
        
        for values in list_of_json:
            
            for key in total_columns:
                if key in values:
                    if key in total_dict:
                        total_dict[key] += values[key]
                    else:
                        total_dict[key] = values[key]
            
    
    return final_json,total_dict
    
                
                
            
    
    
