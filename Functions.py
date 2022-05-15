# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 17:18:38 2021

@author: Dikeshkumar.Faldu
"""

import re
import pandas as pd


def get_line_values(sentence_level_data,start_line,end_line,limit):
    # print(start_line)
    for i,string in enumerate(sentence_level_data):
        
        if re.search(start_line,string,flags=re.I):
            
            for j in range(i+1,i+limit+1):
                # print(j)
                new_string = sentence_level_data[j]
                if re.search(end_line,new_string,flags=re.I):
                    
                    final_address = " ".join(sentence_level_data[i+1:j])
                    
                    return preprocess(final_address)
            
    return ""



def extract_block_vals(df, v):
    result = {}
    temp_res = []
    keyword = v.lower()
    #print(keyword)
    page_match = None
    keywords_len = len(keyword.split())
    threshold1 = 10
    threshold2 = 650
    for pg in df['page_number'].unique():
        #print(pg)
        page = df[df['page_number'] == pg]
        for line in page['line_number'].unique():
            #print(line)
            line_text = " ".join((page[page['line_number']==line])['output']).lower()
            if keyword in line_text.lower():
                #print('yes')
                line_start = line
                page_match = pg
                start_line_df = df[(df['page_number'] == page_match) & (df['line_number'] == line_start)]
                for i in range(len(start_line_df)):
                    temp = " ".join(start_line_df.iloc[i:i+keywords_len,:]['output']).lower().strip()
                    if temp == keyword:
                        #print('match')
                        threshold1 = start_line_df.iloc[i,:]['x']-1
                        break
                start_line_df = start_line_df[start_line_df['x']>= threshold1]
                page = page[(page['x']>= threshold1) & (page['line_number'] >= line_start)]
                lines = page['line_number'].unique()
                for c,line2 in enumerate(lines):
                    if c>=2:
                        y1 = min(page[page['line_number'] == ((lines[c-1]))]['y'])
                        y2 = min(page[page['line_number'] == line2]['y'])
                        diff = y2 - y1
                        if abs(diff)>18:
                            line_end = lines[c-1]
                            break

    for i in range(len(start_line_df)-1):
        word_end = start_line_df.iloc[i,:]['w']
        next_word_start = start_line_df.iloc[i+1,:]['x']
        diff = abs(next_word_start-word_end)
        #print(diff)
        if diff >25:
            #threshold2 = ((next_word_start + word_end)/2)
            threshold2 = ((next_word_start + word_end)/2)+((next_word_start - word_end)/6)
            break
    result_val_df = df[(df['page_number'] == page_match) & (df['line_number'] >= line_start) & (df['line_number'] <= line_end) & (df['x'] <= threshold2) & (df['x']>=threshold1)]
    result_lines = result_val_df['line_number'].unique()
    res_list = []
    min_x = min(result_val_df['x'])
    for c,i in enumerate(result_lines):
        temp = result_val_df[result_val_df['line_number'] == i]
        temp = temp.sort_values(by = ['x'], ascending = True)
        #min_x = np.mean(temp['x'].iloc[0:4])
        #all_x = temp['x']#
        for w in range(len(temp)):
            if w==0:
                currernt_x_start = temp['x'].iloc[w]
                if abs(min_x - currernt_x_start)<60:
                    res_list.append(temp.iloc[w,:])
                else:
                    break
            else:
                prev_x_end = temp['w'].iloc[w-1]
                current_x_start = temp['x'].iloc[w]
                diff3 = current_x_start - prev_x_end
                if w<3:
                    word_diff_thresh = 30
                else:
                    word_diff_thresh = 15
                if abs(diff3)<word_diff_thresh:
                    res_list.append(temp.iloc[w,:])
                else:
                    break
    
    res_list_df = pd.DataFrame(res_list)                 
    temp_ans = " ".join(res_list_df['output']).strip()
    if (keyword.lower()!= 'hewlett-packard') and (keyword.lower()!= 'frau astrid'):
        temp_ans = re.sub('^'+keyword+' ?:?', '', temp_ans, flags=re.IGNORECASE)
    # temp_ans = re.sub('^'+keyword+' ?:?', '', temp_ans, flags=re.IGNORECASE)
    temp_ans = temp_ans.strip()
    temp_ans = temp_ans.strip('\n')
    temp_res.append(temp_ans.strip())
    
    location = str(min(result_val_df["page_number"]))+"_"+str(min(result_val_df["line_number"]))
    temp_res.append(" ".join(result_val_df['output']))

    #   Exception: Germany - Inv # 3339938, keyworld = 'hewlett-packard', Spain - Inv # 20 40.pdf: No keywords and far apart spread lines.         
    #   Check again: New Zealand - Inv # 97FI439137, keyword = 'ship to:' (ship to is not working.), , US - Inv # 245085.pdf: ship to: containing word: Cost center                
    return temp_ans ,location


def preprocess(string):
    
    string = re.sub("\(.*?\)","()",string).strip()
    string = re.sub("^:|\(|\)|`|\$","",string).strip()
    
    return string


def find_isp(field_info_json,sentence_level_data):
    
    isp_dict = field_info_json['Agent']
    
    full_text = " ".join(sentence_level_data)
    
    for key,value in isp_dict.items():
        
        if re.search(value.lower(),full_text.lower()):
            
            return key
    
    return ""

def LineBetween(sentence_level_data,field_dict,output_dict):
        
    for key,value in field_dict.items():
        
        if key not in output_dict.keys() or output_dict[key]=="":
            start = -1
            end = -1
            for start_end in value:
                
                start = -1
                end = -1
                
                for ind,line in enumerate(sentence_level_data):
        #                print(ind,line)
                    
                    if start == -1 and re.search(start_end[0].lower(),line.lower()):
                        start = ind
                    
                    if start != -1 and end==-1 and re.search(start_end[1].lower(),line.lower()):
                        end = ind
                    
                    if start!=-1 and end!=-1:
                        break
                    
                if start!=-1 and end!=-1:
                    break
            #print(start,end)
            if start!=-1 and end!=-1:
            
                Notice_Type = sentence_level_data[start+1:end]
                #print(Notice_Type)
                if len(Notice_Type)==1:
                    output_dict[key] = preprocess(Notice_Type[0])
        
    return output_dict

def verify(v):
    
    for v1 in v.split()[:2]:
        if re.search(r"^[\d,\.]+$",v1):
            return True
        
        return False


def find_page(page_level_data,val):
    """
    input:
        page_level_data : page wise line data of the PDF
        val : index of line data of PDF
    output:
        
    """
    total = val+1
    for i in range(len(page_level_data)):
        
        page_len = len(page_level_data[i])
        
        if total <= page_len:
            final=(str(i+1)+"_"+str(total-1))
            return final
        else:
            total = total-page_len
    return ""

def simple_field(sentence_level_data,page_level_data,simple_dict,output_dict,ISPName):
    
    for key,value in simple_dict.items():
        found = False
        sam_ind = -1
        for ind,line in enumerate(sentence_level_data):
            
            if len(value)==3 and (key not in output_dict.keys() or output_dict[key]==""):
                start = value[0]
                end = value[1]
                check_str = value[2]
                
                if check_str == "":
                    found = True
                elif re.search(check_str.lower(),line.lower()):
                    sam_ind = ind
                    found = True
                    
                
                if found and ind!=sam_ind:
                    if start != "":
                        if re.search(start,line,flags=re.I) :
                            v1 = re.split(start,line,flags=re.I)[-1]
                            
                            if v1!= "" and end !="":
                                v1 = re.split(end,v1,flags=re.I)[0]
                            
                            output_dict[key] = preprocess(v1)
                            #output_dict[key+"_wordlocation"]=find_page(page_level_data,ind)
                            
                            # if key == "GST": 
                            #     if not verify(output_dict[key]):
                            #         output_dict[key] = ""
                    
                    elif end != "":
                    
                        if re.search(end,line,flags=re.I) :
                            v1 = re.split(end,line,flags=re.I)[0].strip()
                        
                            if v1 != "":
                                output_dict[key] = preprocess(v1)
                                #output_dict[key+"_wordlocation"]=find_page(page_level_data,ind)
                                # if key == "GST": 
                                #     if not verify(output_dict[key]):
                                #         output_dict[key] = ""
                
    return output_dict


def find_amount(line):
    
    amount_regex = r"^\d+\.?\d*$"
    line_list = line.split()
    
    line_list.reverse()
    
    word = line_list[0]
    #for i,word in enumerate(line_list):
    word = re.sub("^\-|,","",word)
    if re.search(amount_regex,word):
        
        return round(float(word),2)
    
    else:
        return 0


def find_values(values,page_level_data):
    
    list_of_values = []
    
    list_of_data = []
    
    for i in range(3):
        if i < len(page_level_data):
            list_of_data.extend(page_level_data[i])


    for value in values:
        if len(value) == 2:
            string = value[0]
            pos = value[1]
            
            for ind,line in enumerate(list_of_data):
                index = ind+pos
                if re.search(string.lower(),line.lower()) and index < len(list_of_data) and index>-1:
                    v1 = find_amount(list_of_data[index])
                    if v1 != 0:
                        
                        list_of_values.append(v1)
                    
                    break
                    
    return list_of_values