from api import apikey
from flask import Flask, request, jsonify
import pandas as pd
from csv import writer
import pandas as pd
import requests
import os
import re
import openai
import json
import jsonpickle

apikeys = apikey

app = Flask(__name__)



####################################### GET ALL THE LISTING
def get_listing():

    url = "https://www.estraha.com/api/property_listing"

    payload = {}
    headers = {
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json = response.json()
    return json['data']


######################################### Fetch Propertiies with respect to cites
def findproperty_citywise(city):
    df = pd.DataFrame(get_listing())
    url = 'https://www.estraha.com/property-detail/'
    property = df.loc[df['vCity']==city ]
    property = property.drop(['tContractData','iUserId','iCategoryId','vProperty','iCityId','iRegionId','eRegion','tDescription','vVideo','iViewOwner','iView','eFeaturedOwner'], axis=1)
    property['URL'] = url + property['iPropertyId'].astype(str)
    property = property.head()
    property = property.to_string()
    return property






############## GPT PROMPT ####################
def gpt(inp):
    systems = {"role": "system", "content": """ 
              you are a propty recommendation assitant your job is to assist user from the given properties.
              you'll get the data when you call a funtion name check_propty that can only one param city.
            so whenever user ask about any property you need to ask the city and return the city name in arabic in json with ```
              
              for e.g:IMPORTANT  `{"city":"مكه"}`   '`' is important you'll get data when you use `
             
             when you have all the properties then recommend it to user with some details and  URLs in a proper message then answer the questions related to data 
            IMPORTANT TO ASNWER IN ARABIC AND DO NOT GENERATE ANY PROPERTY ON YOUR OWN FOLLOW THE INSTRUCTIONS
               
               when you have data in history then answer the questions of every query user do.
               
    
              """}
    new_inp = inp
    new_inp.insert(0,systems)
    print("inp : \n ",new_inp)
    openai.api_key = apikeys
    completion = openai.ChatCompletion.create(
    model="gpt-4-turbo-preview", 
    messages=new_inp
    )
    return completion

############    GET CHATS BY USER ID ##################
def get_chats(id):
    path = str(os.getcwd())+'\\chats\\'+id+'.json'
    isexist = os.path.exists(path)
    if isexist:
        data = pd.read_json(path)
        chats = data.chat
        return  list(chats)
    else:
        return "No Chat found on this User ID."





############### APPEND NEW CHAT TO USER ID JSON FILE #################
def write_chat(new_data, id):
    with open("chats/"+id+".json",'r+') as file:
          # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["chat"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)


####################################### Funtion to convert str to JSON
def str_to_json(json_str):
    """
    Convert a JSON-formatted string to a Python dictionary.
    
    Parameters:
    - json_str: A string in JSON format.
    
    Returns:
    - A Python dictionary representing the JSON object.
    """
    try:
        return  json.loads(json_str)
    except json.JSONDecodeError:
        print("Error: The string could not be converted to JSON.")
        return None
    


########################################## Fetch a Json from ``
def fetch_content_between_backticks(text):
    """
    Fetches and returns all occurrences of text found between backticks in the given string.

    Parameters:
    - text: A string that may contain one or more segments enclosed in backticks.

    Returns:
    - A list of strings found between backticks. Returns an empty list if no such text is found.
    """
    pattern = r"`(.*?)`"
    matches = re.findall(pattern, text)
    return matches


################################ CHECK IF USER IS ALREADY EXIST IF NOT CREATE ONE ELSE RETURN GPT REPLY ##################
@app.route('/chat', methods=['POST'])
def check_user():
    
    ids = request.json['user_id']
    prompt = request.json['prompt']
    print("asd")
    path = str(os.getcwd())+'\\chats\\'+ids+'.json'
    # path = str(os.getcwd())+'\\'+"5467484.json"
    isexist = os.path.exists(path)
    if isexist:
        # try:
        print(path," found!")
        write_chat({"role":"user","content":prompt},ids)
        # print()
        chats = get_chats(ids)
        print(chats)
        send = gpt(chats)
        reply = send.choices[0].message.content
        print("reply   ...............:  ",reply)
        if "`" in str(reply):
            get = fetch_content_between_backticks(str(reply))
            print("We got Fetched from backlist : ",get)
            jsons = str_to_json(str(get[0]))
            print("We got JSON : ",jsons)
            listing = findproperty_citywise(jsons['city'])
            print("We got listing : ",listing)
            write_chat({"role":"assistant","content":f"The properties in JSON"+str(listing)+" Now send this to User with some Detail and URLs make it proper message"},ids)
            chats = get_chats(ids)
            send = gpt(chats)
            reply = send.choices[0].message.content
            write_chat({"role":"assistant","content":reply},ids)
            return {"message":reply,"status":"OK"}
        # return 'None'
        else:
            print("reply    ",reply)
            write_chat({"role":"assistant","content":reply},ids)
            return {"message":reply,"status":"OK"}
        # except:
        #     return {"message":"something went wrong!","status":"404"}

    else:
        print(path," Not found!")
        dictionary = {
        "user_id":ids,
        "chat":[]


        }
        
        # Serializing json
        json_object = json.dumps(dictionary, indent=4)
        
        # Writing to sample.json
        with open(path, "w") as outfile:
            outfile.write(json_object)
        reply = check_user()
        return reply

####################   NEW ENPOINT GET CHATS ##############################
@app.route('/get_chats', methods=['POST'])
def get_chatss():
    ids = request.json['user_id']
    return jsonpickle.encode(get_chats(ids))

######################################################### clear chats
@app.route('/delete_chats', methods=['POST'])
def clear_chatss():
    ids = request.json['user_id']

    try:
        path =os.remove(str(os.getcwd())+'\\chats\\'+ids+'.json')
     
        return {"status":"OK","message":"success"}
 
    except :
        return { "status":"error","message":"Something went wrong,chat doesn't exist" }



if __name__ == '__main__':
    app.run(port=5002)
    
