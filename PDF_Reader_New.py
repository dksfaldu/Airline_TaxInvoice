

import pandas as pd
import numpy as np
import re
import warnings
import fitz
import unicodedata

warnings.filterwarnings("ignore")


def computing_median_height(dataframe):
    """
        This method calculates median hight of char , we assume 15 id default height
    """
    avg_height = 15 # this is default value fixed by Quadtatyx team
    try:
        dataframe = dataframe.reset_index(drop=True)
        dataframe['height'] = dataframe['h'] - dataframe['y']
        avg_height = int(np.median(dataframe.height.tolist()))
    except Exception as ve:
        print(str(ve))
    return avg_height

def compute_median(row):
    """
        This method calculates median of h and y coordinates
    """
    try:
        return (int((row['h'] + row['y']) / 2))
    except Exception as ke:
        print(str(ke))

# def add_blank_line(row,median_char_height):
    
#     diff_of_midian = row['Mid_Point_diff']
    
#     if(diff_of_midian > median_char_height+2):
#         row['output'] = "\n"+str(row['output'])
        
#     return row



def compute_line_number(pageDF,threshold):
    """
        This method caluculates line number for particular page data frame given as an argument
    """
    # calculating median char height
    median_char_height = computing_median_height(pageDF)
    # Sorting by page number , y and x
    pageDF = pageDF.sort_values(['page_number', 'y', 'x'], ascending=[True, True, True])
#    page_box_df = page_box_df.sort_values(['page_number', 'y', 'x'], ascending=[True, True, True])
    # reseting index
    pageDF = pageDF.reset_index(drop=True)
#    page_box_df = page_box_df.reset_index(drop=True)
    # calculating median of char height for each word
    pageDF["median_word_y_coOrdinate"] = pageDF.apply(compute_median, axis=1)
    # calculating difference between mediam-height of each word with its next word's median height
    pageDF["diff_of_midian"] = pageDF['median_word_y_coOrdinate'] - pageDF['median_word_y_coOrdinate'].shift(1)
#    page_box_df["diff_of_midian"] = page_box_df['y']-page_box_df['y'].shift(1)
    # there is no prev word for the very first word hence we are adding big num for this
    pageDF["diff_of_midian"].iloc[0] = 100000000
#    page_box_df["diff_of_midian"].iloc[0] = 100000000
    ## Copy these value to other column for further use
    pageDF['Mid_Point_diff'] = pageDF["diff_of_midian"]
    # changing to int
    pageDF['diff_of_midian'] = pageDF['diff_of_midian'].astype(int)
    # putting very large number if difference is > half of threshold median height 
    # pageDF.loc[pageDF['diff_of_midian'] > int(median_char_height * 3 / 2)-1, 'diff_of_midian'] = 100000000

    pageDF.loc[pageDF['diff_of_midian'] > int(median_char_height*threshold ), 'diff_of_midian'] = 100000000

#    page_box_df.loc[page_box_df['diff_of_midian'] > int(median_char_height / 2), 'diff_of_midian'] = 100000000
    # incrementally adding integer to line_number
    pageDF['line_number'] = (pageDF.diff_of_midian == 100000000).cumsum()
#    page_box_df['line_number'] = (page_box_df.diff_of_midian == 100000000).cumsum()
    
    pageDF = pageDF.sort_values(['line_number','x'], ascending=[True, True])
#    page_box_df = page_box_df.sort_values(['line_number', 'x'], ascending=[True, True])
    # droping unused columns
    
    # pageDF = pageDF.apply(lambda x : add_blank_line(x,median_char_height),axis=1)
    
    del pageDF['median_word_y_coOrdinate'], pageDF['diff_of_midian'] , pageDF['Mid_Point_diff']
    
    ## Removing the page number at the end of every page
#    last_line = max(list(pageDF['line_number']))
#    pageDF = pageDF[pageDF['line_number']<last_line]

    return pageDF

def add_line_number(df,threshold):
    """
        This method will add line number to words
    """
    pages = list(set(df['page_number']))
    new_df = pd.DataFrame()

    for page_num in pages:
        pageDF = df[df['page_number'] == page_num]
        pageDF = compute_line_number(pageDF,threshold)
        new_df = new_df.append(pageDF)
        
    return new_df


def compute(page_df,page_no,threshold):
    
    page_df = page_df[["x","y","w","h","output"]]
    
    page_df = page_df[page_df["output"]!="|"]
         
    page_df = page_df.drop_duplicates(["x","y","w","h","output"])
    
    page_df["page_number"] = page_no+1

    page_df = compute_line_number(page_df,threshold)
    
    return page_df

def get_df_fitz(pdf_file,threshold):

    doc = fitz.open(pdf_file)
    df = pd.DataFrame()
    # new_df= pd.DataFrame()
    for page_no in range(doc.page_count): #doc.page_count

        # for page_no in range(10):
        # print("Page No : ",page_no)
        
        page1 = doc[page_no]
        
        words = page1.get_text("words")
        
        if len(words)>0:
            
            page_df = pd.DataFrame(words)
            
            # new_page_df = page_df.copy()
            
            page_df.columns = ["x","y","w","h","output","block","lines","count"]
            
            page_df["output"] = [unicodedata.normalize("NFKD", string).replace('\xad', '-') for string in page_df["output"]]
            # new_page_df.columns = ["y","w","h","x","output","block","lines","count"]
            
            # x_max = max(new_page_df["x"])
            # x_min = min(new_page_df["x"])
            
            # new_page_df.loc[:, 'x'] = x_max - new_page_df.loc[:, 'x'] + x_min
            # new_page_df.loc[:, 'w'] = x_max - new_page_df.loc[:, 'w'] + x_min

            page_df = compute(page_df,page_no,threshold)
            df = df.append(page_df)
            
            # new_page_df = compute(new_page_df,page_no)
            # new_df = new_df.append(new_page_df)
      
    
    return df


def change_coordinate(df):
    
    new_df = df.copy()
    new_df.columns = ["y","w","h","x","output", "page_number", "line_number", "middle_x","height"]
    
    x_max = max(new_df["x"])
    x_min = min(new_df["x"])
    
    new_df.loc[:, 'x'] = x_max - new_df.loc[:, 'x'] + x_min
    new_df.loc[:, 'w'] = x_max - new_df.loc[:, 'w'] + x_min
    
    new_df = new_df[["x","y","w","h","output","page_number"]]
    
    new_df = new_df.drop_duplicates(["x","y","w","h","output","page_number"])
    
    new_df = add_line_number(new_df)
    
    new_df['middle_x'] = (new_df['x']+new_df['w'])/2
    new_df["height"] = new_df["h"] - new_df["y"]
    
    return new_df


def read_list(pdf_file_path,threshold = 2/3):
    
    df = get_df_fitz(pdf_file_path,threshold)
    
    df['middle_x'] = (df['x']+df['w'])/2
    df["height"] = df["h"] - df["y"]
    
    
    page_level_data = []
    sentence_level_data = []
    
    for page_number in set(list(df['page_number'])):
        temp_page_level_data = []
        temp_page_level_index = []
        temp_df1 = df[df['page_number'] == page_number]
            
            
        for line_number in set(list(temp_df1['line_number'])):
            temp_df2 = temp_df1[temp_df1['line_number']==line_number]
            temp_df2 = temp_df2.sort_values(['x'], ascending=[True])
            string_list = [k.strip() for k in list(temp_df2['output'])]
            string = " ".join(string_list).strip()
            temp_page_level_data.append(string)
            temp_page_level_index.append(str(page_number)+"_"+str(line_number))
        
        page_level_data.append(temp_page_level_data)
        sentence_level_data.extend(temp_page_level_data)
        
    
    return df,page_level_data,sentence_level_data

    
def get_pdf_df(pdf_file_path):
    
       
    df = get_df_fitz(pdf_file_path)
    
    df['middle_x'] = (df['x']+df['w'])/2
    df["height"] = df["h"] - df["y"]
    
    # new_df['middle_x'] = (new_df['x']+new_df['w'])/2
    # new_df["height"] = new_df["h"] - new_df["y"]
            
    return df

# if __name__ == "__main__":
    
#     pdf_file_path  = r"D:/Work/UpWork/OrderStack/Data/Test-Batch 3 Part -1/8e1b1025-e82e-474a-9699-46d4ad29e4a0/0a381133-907b-4aa0-8950-6a6dc552eb67.pdf"

#     # pdf_file_path = r"C:/Users/dikes/Downloads/1040ez-RobbStark-example.pdf"
#     df = get_pdf_df(pdf_file_path)



