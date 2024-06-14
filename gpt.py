
from api import apikey
from flask import Flask, request, jsonify,Response
import pandas as pd
from csv import writer
from langchain.embeddings import OpenAIEmbeddings
import pandas as pd
import requests
from langchain.vectorstores import Chroma
import os
import re
from openai import OpenAI
import json
import jsonpickle
# from PIL import Image
import tiktoken
enc = tiktoken.get_encoding("cl100k_base")
assert enc.decode(enc.encode("hello world")) == "hello world"

# To get the tokeniser corresponding to a specific model in the OpenAI API:
enc = tiktoken.encoding_for_model("gpt-4-turbo")
from flask_cors import CORS, cross_origin
apikeys = apikey

app = Flask(__name__)

cors = CORS(app)
client = OpenAI(api_key=apikeys)



embeddings = OpenAIEmbeddings(openai_api_key=apikeys)
db = Chroma(persist_directory="mydb", embedding_function=embeddings)


##############################  Venctor search
def retrieve_combined_documents(query, max_combined_docs=4):
    retriever = db.as_retriever(search_type="mmr")

    rev_doc = retriever.get_relevant_documents(query)
    lim_rev_doc = rev_doc[:max_combined_docs]

    docs = db.similarity_search(query)
    lim_docs = docs[:max_combined_docs]

    combined_docs = str(lim_rev_doc) + str(lim_docs)
    return combined_docs
    # combined_docs=db.similarity_search(query)
####################################### GET ALL THE LISTING
def get_listing():

    url = "https://www.estraha.com/api/property_listing"

    payload = {'eChatBot': 'Yes'}
    headers = {
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json = response.json()
    return json['data']

#################################################### COUNT TOKEN
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens





def findproperty_citywise(data):
    js =[]
    if 'city' in data:
        city = data['city']
        if city == "جدة":
            city = "جده"
            print("city : " ,city)
        js = get_listing()
        js = filtered_data = [record for record in js if record['City'].lower() == city]
    if 'region' in data:
        region = data['region']
        js = filtered_data = [record for record in js if record['Region'].lower() == region]
    if 'pool' in data:
      
        js = filtered_data = [record for record in js if int(record['Swimming Pools']) >= 1]
    url = 'https://www.estraha.com/property-detail/'
    # record = ''
    for i in js:
        i['URL'] = url + str(i['property ID'])
        i['Description'] = []
    if js == []:
        return "No Property found in this city"
    else:
        return str(js[:6])
    
    
    
    # df = pd.DataFrame(get_listing())
    # url = 'https://www.estraha.com/property-detail/'
    # property = df.loc[df['City']==city ]
    # #property = property[['vProperty','eSwimmingPool','vAddress','eRegion','eSwimmingPool','tSwimingPool','image','eMonthPrice','vWeekdayPrice','iPropertyId']]
    # # property['URL'] = url + property['property ID'].astype(str)
    
    # # if property.empty:
    # #     print('NONE')
    # #     return "No Property found in this city"
    # # else:
    # #     print(property)
    # #     if len(property) > 3: 
    # #         propertyy = property.sample(n=2)
    # #         property_sample = propertyy
    # #         property_json= property.to_json()
    # #         print("3 Samples")
    # #         return property_json
    # #     else:
    # #         # propertyy = property.sample(n=6)
    # #         property_sample = property.to_string()
    # #         return property_sample
            
############## GPT PROMPT ####################
def gpt(inp,prompt):
    systems = {"role": "system", "content": """ 
              you are a propty recommendation assitant your job is to assist user from the given properties.
              you'll get the data when you call a funtion name check_propty that will fetch the property but you have to pass filters according to user.
              filters are :
              {'Property Name': 'استراحة الورود',
 'Address': 'جدة ابحر الشماليه بجوار جامعة الاعمال والتكنلوجيا',
 'City': 'جده',
 'Region': 'الشمال',
 'pool': 'Yes',
 'Swimming Pool Description': '0',
 'Football Yard': 'Yes',
 'Singles': 'No',
 'Bedroom': '2',
 'Bathroom': '2',
 'Swimming Pools': '1',
 'Latitude': '21.864041326744427',
 'Longitude': '39.06272548373611',
 'Area': '600',
 'Description': [],
 'Weekday Price': '900',
 'Thursday Price': '1300',
 'Friday Price': '1500',
 'Saturday Price': '1000',
 'property ID': '5825',}
             all filters are optional except city. so you must ask city if not defined in query
            so whenever user ask about any property you need to ask the city and return the ONLY city name in arabic in json with ```
              
              for e.g:IMPORTANT  `{"city":"مكه"}`   '`' is important you'll get data when you use,  don't send any region or anything else with city name`
              you can apply filter with in the same json like `{"city":"مكه","region":"الشمال","pool":"1"}` etc 
             IMPORTANT :  Do not generate any property details from your data use our data only if you dont get any property just say you dont find the property in database.
             \
             when you have all the properties then recommend it to user with some details and  URLs in a proper message then answer the questions related to data and apply all filters like
             if user wants property from south give him south property. propety type, pool yes or no and  all others 
            IMPORTANT TO ASNWER IN ARABIC AND DO NOT GENERATE ANY PROPERTY ON YOUR OWN FOLLOW THE INSTRUCTIONS
               
               when you have data in history then answer the questions of every query user do.
               Do not generate property data on your own 
               IMPORTANT : you are integrated in a website so act like html format while return string in user like use html tags as needed use <b> instead of ** and <br> in place of \n 
               and provide links in <a href=""> tag. always break the line after every property and name must be bold.
               Each property must be in new line with S NO.IMPORTANT  Dont break line after S NO only before S NO or after property details 
              """}
    new_inp = inp
    rcd = retrieve_combined_documents(prompt)
    systems2 = {"role":"system","content":str(rcd)}
    new_inp.insert(0,systems)
    new_inp.insert(0,systems2)
    count = num_tokens_from_string(str(new_inp), "cl100k_base")
    print("Total Token Counts are : ",count)
    completion = client.chat.completions.create(
    model="gpt-4o", 
    messages=new_inp
    )
    return completion

############    GET CHATS BY USER ID ##################
def get_chats(id):
    path = id
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




############### APPEND NEW CHAT TO USER ID JSON FILE #################
def write_chat(new_data, id):
    with open(id,'r+', encoding='utf-8') as file:
          # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["chat"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.

        json.dump(file_data, file, ensure_ascii=False, indent=4)


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
    # text = text.replace("`","")
    text = text.replace("json","")
    pattern = r"`(.*?)`"
    matches = re.findall(pattern, text)
    if matches == []:
        pattern = r"(.*?)"
        matches = text
    return matches


################################ CHECK IF USER IS ALREADY EXIST IF NOT CREATE ONE ELSE RETURN GPT REPLY ##################
@app.route('/chat', methods=['POST'])
@cross_origin()
def check_user():
    image_url = 'https://www.estraha.com/assets/uploads/property_image'
    ids = request.json['user_id']
    prompt = request.json['prompt']
    print("asd")
    path = str(os.getcwd())+'\\chats\\'+str(ids)+'.json'
    # path = str(os.getcwd())+'\\'+"5467484.json"
    isexist = os.path.exists(path)
    if isexist:
        # try:
        print(path," found!")
        write_chat({"role":"user","content":prompt},path)
        # print()
        chats = get_chats(path)
        chats = chats[-6:]
        print(chats)
        print("GETCHATS \n\n ",chats)
        send = gpt(chats,prompt)
        
        reply = send.choices[0].message.content
        print("reply   ...............:  ",reply)
        if "`" in str(reply) or "{" in str(reply):

            print('\n\nBacklist Found\n\n: ',reply)

            # try:
            get = fetch_content_between_backticks(str(reply))
            
            print("We got Fetched from backlist : ",get)
            listing = ""
            jsons = str_to_json(str(get[0]))
            print("We got JSON : ",jsons)
            if jsons !=  'None':
                listing = findproperty_citywise(jsons)
            else:
                listing = 'None'
                print('Listing is NONE')
            # except:
            #     # listing = None
            #     print("JSON CANT BE FETCHED.....!!!")
            #     pass
            
            if listing !=  'None':
                print("we hare at 1")
                # print("We got listing : ",listing)
                write_chat({"role":"system","content":f"The properties in JSON"+str(listing)+" Now send this to User with some Detail and URLs make it proper message"},path)
                chats = get_chats(path)
                chats = chats[-6:]
                send = gpt(chats,prompt)
                reply = send.choices[0].message.content
                write_chat({"role":"assistant","content":reply},path)   
                # return Response(reply, mimetype='text/html')
                reply = reply.replace("<b>","<br><b>")
                return {"message":reply,"status":"OK"}
            else:
                print("we hare at 2")
                write_chat({"role":"user","content":prompt+"""make sure  to return it in '`{"city":"مكه"}`' formate """},path)
                chats = get_chats(path)
                chats = chats[-5:]
                print("Miss hoa h")
                send = gpt(chats,prompt)
                get = fetch_content_between_backticks(str(reply))
                print("We got Fetched from backlist : ",get)
                jsons = str_to_json(str(get[0]))
                print("We got JSON : ",jsons)
                listing = findproperty_citywise(jsons)
                # return Response(reply, mimetype='text/html')
                reply = reply.replace("<b>","<br><b>")
                return {"message":reply,"status":"OK"}


        else:
            print("reply    ",reply)
            write_chat({"role":"assistant","content":reply},path)
            return {"message":reply,"status":"OK"}
            # return {"message":reply,"status":"OK","images":[]}
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
@cross_origin()
def get_chatss():
    ids = request.json['user_id']
    path = str(os.getcwd())+'//chats//'+ids+'.json'
    return jsonpickle.encode(get_chats(path))

######################################################### clear chats
@app.route('/delete_chats', methods=['POST'])
@cross_origin()
def clear_chatss():
    ids = request.json['user_id']

    try:
        path =os.remove(str(os.getcwd())+'//chats//'+ids+'.json')
     
        return {"status":"OK","message":"success"}
 
    except :
        return { "status":"error","message":"Something went wrong,chat doesn't exist" }

################################ GET ALL USER'S IDs
@app.route('/get_users', methods=['POST'])
@cross_origin()
def extract_json_filenames():
    """
    Extracts the names of all JSON files in the specified directory,
    removes their '.json' extensions, and returns a list of the names.

    Parameters:
    - directory: Path to the directory containing the JSON files.

    Returns:
    - A list of strings representing the names of the JSON files, without the '.json' extension.
    """
    # List to store the names of JSON files without extension
    cwd = str(os.getcwd())+'//chats//'
    json_filenames_without_extension = []
    
    # Iterate through all files in the specified directory
    for filename in os.listdir(cwd):
        # Check if the file is a JSON file by looking at its extension
        if filename.endswith('.json'):
            # Remove the '.json' extension and add it to the list
            name_without_extension = os.path.splitext(filename)[0]
            json_filenames_without_extension.append(name_without_extension)
    
    return json_filenames_without_extension

if __name__ == '__main__':
    app.run(port=5002,host='0.0.0.0',threaded=True)
    
