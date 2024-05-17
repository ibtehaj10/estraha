from api import apikey
from flask import Flask, request, jsonify
import pandas as pd
from csv import writer

import os
import time
import openai
import json
import jsonpickle
from langchain.document_loaders import PyPDFLoader
# from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
apikeys = apikey

app = Flask(__name__)


embeddings = OpenAIEmbeddings(openai_api_key=apikeys)
db = Chroma(persist_directory="mydb", embedding_function=embeddings)
# db.get()
# embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# db = Chroma.from_documents(docs, embedding_function)
############################## 
def retrieve_combined_documents(query, max_combined_docs=4):
    retriever = db.as_retriever(search_type="mmr")

    rev_doc = retriever.get_relevant_documents(query)
    lim_rev_doc = rev_doc[:max_combined_docs]

    docs = db.similarity_search(query)
    lim_docs = docs[:max_combined_docs]

    combined_docs = str(lim_rev_doc) + str(lim_docs)
    # combined_docs=db.similarity_search(query)

    return combined_docs


############## GPT PROMPT ####################
def gpt(inp,prompt,status):
    
    systems = {"role":"system","content":"""
              you are a propty recommendation assitant your job is to assist user from the given properties.
IMPORTANT TO ASNWER IN ARABIC AND DO NOT GENERATE ANY PROPERTY ON YOUR OWN FOLLOW THE INSTRUCTIONS
"""}
    rcd = retrieve_combined_documents(prompt)
    systems2 = {"role":"system","content":str(rcd)}
    systems3 = {"role":"system","content":"IMPORTANT : be concise as possible and do not says anything like you dont have the context or thing do not mention in document. If you cant find anything about question just redirect user to support@metutors.com email."}
    systems4 = {"role":"system","content":"The user is {}. answer him accordingly".format(status)}
    new_inp = inp
    new_inp.insert(0,systems)
    new_inp.insert(1,systems2)
    new_inp.insert(2,systems3)
    new_inp.insert(3,systems4)
    print("inp : \n ",new_inp)
    openai.api_key = apikeys
    print('&&&&&&&&&&&&^^^^^^^^^^^^%$######################$%^&*((((((((((((((()))))))))))))))')
    completion = openai.ChatCompletion.create(
    model="gpt-4-1106-preview", 
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





############### APPEND NEW CHAT TO USER ID JSON FILE #################
def write_chat(new_data, id):
    with open(id,'r+') as file:
          # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["chat"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent = 4)



################################ CHECK IF USER IS ALREADY EXIST IF NOT CREATE ONE ELSE RETURN GPT REPLY ##################
@app.route('/api', methods=['POST'])
def check_user():
    
    ids = request.json['user_id']
    prompt = request.json['prompt']
    status = request.json['status']
    print("asd")
    path = str(os.getcwd())+'//chats//'+ids+'.json'
    # path = str(os.getcwd())+'\\'+"5467484.json"
    isexist = os.path.exists(path)
    if isexist:
        # try:
        print(path," found!")
        write_chat({"role":"user","content":prompt},path)
        # print()
        chats = get_chats(path)
        print(chats)
        send = gpt(chats,prompt,status)
        reply = send.choices[0].message
        print("reply    ",reply.content)
        write_chat({"role":"assistant","content":reply.content},path)
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

####################   NEW ENPOINT GET CHAT ##############################
@app.route('/get_chats', methods=['POST'])
def get_chatss():
    ids = request.json['user_id']
    return jsonpickle.encode(get_chats(ids))





if __name__ == '__main__':
    app.run(debug=True)
    
