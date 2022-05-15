# -*- coding: utf-8 -*-
"""
Created on Mon Aug 10 18:56:14 2020

@author: Dikeshkumar.Faldu
"""


import re

def find_substitute(word_list,line_df,complete_matches,page_no,line_no):
    
    final_matches = []
    
    line_list = list(line_df['output'])
    x_list = list(line_df['x'])
    w_list = list(line_df['w'])
    
    for ind,each_word in enumerate(line_list):
        
        if each_word.lower().strip() == word_list[0]:
            start_ind = ind
            end_ind = ind
            final_i = 0
            for i in range(1,len(word_list)):
                
                if ind+i != len(line_list) and word_list[i] == line_list[ind+i].lower().strip():
                    end_ind = ind+i
                    final_i = i
                else:
                    break
            matched_str = line_list[start_ind:end_ind+1]
            x_matched = min(x_list[start_ind:end_ind+1])
            w_matched = max(w_list[start_ind:end_ind+1])
            mid_matched = (x_matched+w_matched)/2
            if len(matched_str) == len(word_list):
                remaining_word = []
                complete_matches.append([matched_str,x_matched,w_matched,mid_matched,remaining_word,page_no,line_no])
            else:
                remaining_word = word_list[final_i+1:]
                final_matches.append([matched_str,x_matched,w_matched,mid_matched,remaining_word])
            
    return final_matches,complete_matches


def check(x,w,mid,next_x,next_w,next_mid):
    
    if next_mid >= x and next_mid <=w:
        return True
    
    if mid >= next_x and mid <=next_w:
        return True
    
    if next_x >= x and next_x <= w:
        return True
    
    if next_w >= x and next_w <= w:
        return True
    
    return False
    

def find_sequence(matched_list,complete_matched,line_df,page_no,line_no):
    
    line_list = list(line_df['output'])
    x_list = list(line_df['x'])
    w_list = list(line_df['w'])
    final_matches = []
    #complete_matched = []
    for matched in matched_list:
        match_str = matched[0]
        x = matched[1]
        w = matched[2]
        mid = matched[3]
        remaining_words = matched[4]
        
        if len(remaining_words)==0:
            matched.append(page_no)
            matched.append(line_no)
            complete_matched.append(matched)
        elif len(remaining_words)>0:
            for ind,each_word in enumerate(line_list):
                
                if each_word.lower().strip() == remaining_words[0]:
                    start_ind = ind
                    end_ind = ind
                    final_i = 0
                    #print(ind,each_word)
                    for i in range(1,len(remaining_words)):
                        if ind+i != len(line_list) and remaining_words[i] == line_list[ind+i].lower().strip() :
                            end_ind = ind+i
                            final_i = i
                        else:
                            break
                        
                    
                    x_matched = min(x_list[start_ind:end_ind+1])
                    w_matched = max(w_list[start_ind:end_ind+1])
                    mid_matched = (x_matched+w_matched)/2
                    if check(x,w,mid,x_matched,w_matched,mid_matched):
                        new_x = min(x,x_matched)
                        new_w = max(w,w_matched)
                        new_mid = (new_x+new_w)/2
                        matched_str = match_str+line_list[start_ind:end_ind+1]
                        if final_i == len(remaining_words)-1:
                            remaining_word = []
                            complete_matched.append([matched_str,new_x,new_w,new_mid,remaining_word,page_no,line_no])
                        else:
                            remaining_word = remaining_words[final_i+1:]
                            final_matches.append([matched_str,new_x,new_w,new_mid,remaining_word])
    
    return final_matches,complete_matched


def find_values(matched_list,line_df):
    
    final_value = []
    
    x = matched_list[1]
    w = matched_list[2]
    mid = matched_list[3]
    
    for index,row in line_df.iterrows():
        
        x_line = row['x']
        w_line = row['w']
        mid_line = row['middle_x']
        
        if check(x,w,mid,x_line,w_line,mid_line):
            
            final_value.append(row['output'].strip())
        
    
    return " ".join(final_value)
                
    

def find_word(df,list_of_word):
    final_values = []
    location = []

    for word in list_of_word:
        word_list = word.split("|")
        if len(word_list)==1:
            check_str = ""
            word = word_list[0]
        elif len(word_list)==2:
            check_str = word_list[1]
            word = word_list[0]

        if check_str == "":
            flag = True
        else:
            flag = False

        word_list = word.lower().split()
    
        complete_matched = []
        
        for page_no in set(df['page_number']):
            
            page_df = df[df['page_number']==page_no]
            for line_no in set(page_df['line_number']):
                
                line_df = page_df[page_df['line_number']==line_no]
                
                line_str = " ".join(list(line_df['output']))


                if not flag and re.search(check_str,line_str,flags=re.I):
                    flag = True

                if flag:
                    matched_list,complete_matched = find_substitute(word_list,line_df,complete_matched,page_no,line_no)
        
                    if len(matched_list)>0:
                        #print(matched_list,line_no)
                        for n_line in range(line_no+1,line_no+3) :
                            if n_line in set(page_df['line_number']) and len(matched_list) > 0 :
                                line_df = page_df[page_df['line_number']==n_line]
                                matched_list,complete_matched= find_sequence(matched_list,complete_matched,line_df,page_no,n_line)
                        
                    #print(complete_matched)
        
        for matched_list in complete_matched:
            
            page_no = matched_list[-2]
            line_no = matched_list[-1]+1
            
            for line_no in range(matched_list[-1]+1,matched_list[-1]+3):
                line_df = df[(df['page_number']==page_no)&(df['line_number']==line_no)]
                
                values = find_values(matched_list,line_df)
                
                if values.strip()!="":
                    
                    final_values.append(values)
                    location.append(str(page_no)+"_"+str(line_no))
                    break
    
    if len(final_values)>0:
        return final_values[0],location[0]
    
    else:
        return "",""
    
