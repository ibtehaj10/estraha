from pywa import WhatsApp
from flask import Flask
from pywa.types import Message, CallbackButton
# from pywa.filters import  CallbackFilter
import requests
from PIL import Image
# import mysql.connector
import re

def gpt(uid,text):
    headers={'Content-Type': 'application/json'}
    body = {
        "user_id":uid,
        "prompt":text

    }
    r = requests.post('http://127.0.0.1:5002/chat',headers=headers,json=body)
    print(r)
    ans = r.json()
    print(ans)
    if 'filename' not in ans:
        anss = ans['message']
        return anss
    else:
        return ans

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
    for i in li:

        local_image_path = i.replace(base_url,'').replace('/','')
        local_image_path = 'images/'+local_image_path
        # Replace 'output_image.jpg' with the desired output path for the .jpg file
        jpg_image_path = local_image_path.replace('.webp','.jpg')
        response = requests.get(i)
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




flask_app = Flask(__name__)
wa = WhatsApp(
    phone_id='113578631653943',
    token='EAAMTxi1SmKQBOzZBkGRm1mq2wLkBnsnSpLhi8QtwxZCMw9MXXdZCCn4dDBLdgZAWcZAZAaYwrLWOVCRDRU7d8cYzZAFGgYoIEUDYnoS6cDobL1IEWwx4JOGmYYYAgZAVaqCB9Y7dHv5a7DW2Yy9b5vO4xBnZBwqLYZAiU1SxKGXaya4Jnn6wDqvbEUzxus9c9GqTcxK9DVS8qXXEuwPhvTPXgZD',
    server=flask_app,
    verify_token='asds'
)
image_url = 'https://www.estraha.com/assets/uploads/property_image'
@wa.on_message()
def hello(client: WhatsApp, message: Message):
    # message.react('👋')
    print(message)
    uid = message.from_user.wa_id
    msg = message.text
    reply = gpt(uid,msg)
    if image_url in reply:
        urls = url_fetch(reply)
        urlss = image_converter(urls)
        for i in urlss:
            # message.reply_image(image='https://imageio.forbes.com/specials-images/imageserve/5d35eacaf1176b0008974b54/0x0.jpg')
            print(i)
            message.reply_image(
                 image=i
            )
    else:
        message.reply_text(
            text=reply
       
    )
    # print('pdf send')

# @wa.on_callback_button(CallbackFilter.data_startswith('id'))
# def click_me(client: WhatsApp, clb: CallbackButton):
#     clb.reply_text('You clicked me!')

# flask_app.run(host='172.16.0.15',ssl_context=('certificate.crt', 'private.key'),port='5000') 
#  # Run the flask app to start the webhook

if __name__ == '__main__':
    flask_app.run(host='0.0.0.0',port=5008)