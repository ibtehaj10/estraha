from api import apikey
from flask import Flask, request, jsonify
import pandas as pd
from csv import writer
import pandas as pd
import requests
import os
import re
from openai import OpenAI
import json
import jsonpickle
from PIL import Image
apikeys = apikey

app = Flask(__name__)


client = OpenAI(api_key=apikeys)



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
    property = property[['vProperty','eSwimmingPool','vAddress','eRegion','eSwimmingPool','tSwimingPool','image','eMonthPrice','vWeekdayPrice','iPropertyId']]
    property['URL'] = url + property['iPropertyId'].astype(str)
    
    if property.empty:
        print('NONE')
        return "No Property found in this city"
    else:
        propertyy = property.sample(n=3)
        property_sample = propertyy.to_string()
        return property_sample






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
               Do not generate property data on your own 
    
              """}
    new_inp = inp
    new_inp.insert(0,systems)
    # print("inp : \n ",new_inp)
    # openai.api_key = apikeys
    completion = client.chat.completions.create(
    model="gpt-4-turbo-preview", 
    messages=new_inp
    )
    return completion

############    GET CHATS BY USER ID ##################
def get_chats(id):
    path = str(os.getcwd())+'//chats//'+id+'.json'
    isexist = os.path.exists(path)
    if isexist:
        data = pd.read_json(path)
        chats = data.chat
        return  list(chats)
    else:
        return "No Chat found on this User ID."



def url_fetch(text):    
    url_pattern = r'https?://[^\s)\]]+'

    # Finding all URLs in the string
    urls = re.findall(url_pattern, text)

    # Print the list of URLs
    # for url in urls:
    #     print(url)
    return urls

def image_converter(li):
    base_url = 'https://www.estraha.com/assets/uploads/property_image/'
# Replace 'input_image.webp' with the path to your .webp file
    urls = []
    print(li)
    for i in li:

        local_image_path = i.replace(base_url,'').replace('/','')
        local_image_path = 'images/'+local_image_path
        # Replace 'output_image.jpg' with the desired output path for the .jpg file
        jpg_image_path = local_image_path.replace('.webp','.jpg')
        response = requests.get(i)
        print(response.content)
        print(local_image_path)
        # if response.status_code == 200:
    # Open a local file in binary write mode
        with open(local_image_path, 'wb') as file:
            # Write the content of the response to the file
            file.write(response.content)
       # Open the .webp image
        image = Image.open(local_image_path)

        # Convert the image to RGB mode if it is not already, as JPEG does not support alpha channel
        if image.mode in ("RGBA", "P", "LA"):
            image = image.convert("RGB")

        # Save the image in .jpg format
        image.save(jpg_image_path, 'JPEG')

        urls.append(jpg_image_path)
    return urls


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
        return 'None'
    


########################################## Fetch a Json from ``
def fetch_content_between_backticks(text):
    """
    Fetches and returns all occurrences of text found between backticks in the given string.

    Parameters:
    - text: A string that may contain one or more segments enclosed in backticks.

    Returns:
    - A list of strings found between backticks. Returns an empty list if no such text is found.
    """
    text = text.replace("\n","")
    text = text.replace("``","")
    text = text.replace("json","")
    pattern = r"`(.*?)`"
    matches = re.findall(pattern, text)
    return matches


################################ CHECK IF USER IS ALREADY EXIST IF NOT CREATE ONE ELSE RETURN GPT REPLY ##################
@app.route('/chat', methods=['POST'])
def check_user():
    image_url = 'https://www.estraha.com/assets/uploads/property_image'
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
        chats = chats[-3:]
        print(chats)
        send = gpt(chats)
        reply = send.choices[0].message.content
        print("reply   ...............:  ",reply)
        if "`" in str(reply):

            print('\n\nBacklist Found\n\n: ',reply)

            try:
                get = fetch_content_between_backticks(str(reply))
                
                print("We got Fetched from backlist : ",get)
                listing = ""
                jsons = str_to_json(str(get[0]))
                print("We got JSON : ",jsons)
                if jsons !=  'None':
                    listing = findproperty_citywise(jsons['city'])
                else:
                    listing = 'None'
                    print('Listing is NONE')
            except:
                # listing = None
                pass
            
            if listing !=  'None':
                print("we hare at 1")
                # print("We got listing : ",listing)
                write_chat({"role":"system","content":f"The properties in JSON"+str(listing)+" Now send this to User with some Detail and URLs make it proper message"},ids)
                chats = get_chats(ids)
                chats = chats[-2:]
                send = gpt(chats)
                reply = send.choices[0].message.content
                write_chat({"role":"assistant","content":reply},ids)    
                return {"message":reply,"status":"OK"}
            else:
                print("we hare at 2")
                write_chat({"role":"user","content":prompt+"""make sure  to return it in '`{"city":"مكه"}`' formate """},ids)
                chats = get_chats(ids)
                chats = chats[-2:]
                print("Miss hoa h")
                send = gpt(chats)
                get = fetch_content_between_backticks(str(reply))
                print("We got Fetched from backlist : ",get)
                jsons = str_to_json(str(get[0]))
                print("We got JSON : ",jsons)
                listing = findproperty_citywise(jsons['city'])
                return {"message":reply,"status":"OK"}


        else:
            print("reply    ",reply)
            write_chat({"role":"assistant","content":reply},ids)
            return {"message":reply,"status":"OK","images":[]}
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
    path = str(os.getcwd())+'//chats//'+ids+'.json'
    return jsonpickle.encode(get_chats(path))

######################################################### clear chats
@app.route('/delete_chats', methods=['POST'])
def clear_chatss():
    ids = request.json['user_id']

    try:
        path =os.remove(str(os.getcwd())+'//chats//'+ids+'.json')
     
        return {"status":"OK","message":"success"}
 
    except :
        return { "status":"error","message":"Something went wrong,chat doesn't exist" }



if __name__ == '__main__':
    app.run(port=5002)
    
