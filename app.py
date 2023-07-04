import streamlit as st
import openai
import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat

# OpenAI API key
openai.api_key = st.secrets["apikey"]

# Helper function to get the brightness of an image


def get_brightness(image):
    greyscale_image = image.convert('L')
    stat = ImageStat.Stat(greyscale_image)
    return stat.mean[0]


def get_quote():
    response = requests.get("https://api.quotable.io/random")
    data = response.json()
    return data['content'], data['author']


def quote_to_prompt(quote, author):
    gpt_prompt = [
        {
            "role": "system",
            "content": "You are an art gallery docent with the unique ability to imagine and eloquently describe images based on simple words or phrases. Your goal is to portray these images in an artistic, picture-like style, creating a vivid mental image. Your descriptions should be concise, utilising rich vocabulary, and limited to approximately two sentences. Please respond in English.",
        },
        {
            "role": "user",
            "content": f"{quote} - {author}",
        },
    ]
    gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=gpt_prompt)
    return gpt_response.choices[0].message["content"]


def translate_quote(quote):
    translation_prompt = [
        {
            "role": "system",
            "content": "You are a highly skilled translator capable of translating English to Korean. Please translate the following text.",
        },
        {
            "role": "user",
            "content": quote,
        },
    ]
    translation_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=translation_prompt)
    return translation_response.choices[0].message["content"]


def add_text_to_image(image, text, line_spacing=2.2, font_size=40, font_bold=False):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('NotoSansKR-Light.otf', font_size)

    max_width = image.width * 0.6
    max_height = image.height * 0.6
    lines = []

    words = text.split(' ')
    line = ''

    for word in words:
        if draw.textsize(line + ' ' + word, font)[0] <= max_width:
            line += ' ' + word
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    while draw.textsize('\n'.join(lines), font)[1] > max_height:
        lines.pop()

    text = '\n'.join(lines)

    width, height = draw.textsize(text, font)
    x = (image.width - width) / 2
    y = (image.height - height) / 2

    brightness = get_brightness(image)
    if brightness > 128:  # bright background
        font_color = "black"
    else:
        font_color = "white"

    draw.text((x, y), text, align='center', font=font, fill=font_color)

    return image


st.title("엠파스봇의 명언 랜덤 생성기")

image_size = st.selectbox(
    '이미지 사이즈 선택', ['256x256', '512x512', '1024x1024'], index=2)

with st.form("form"):
    submit = st.form_submit_button("명언 생성하기")

    if submit:
        quote, author = get_quote()
        image_prompt = quote_to_prompt(quote, author)
        translated_quote = translate_quote(quote)

        with st.spinner("그림 그리는중..."):
            image_response = openai.Image.create(
                prompt=image_prompt, size=image_size)
            image = Image.open(requests.get(
                image_response["data"][0]["url"], stream=True).raw)
            image_with_text = add_text_to_image(
                image, translated_quote)

        st.image(image_with_text)
