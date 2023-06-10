from PIL import Image, ImageDraw, ImageFont, ImageOps
from random import choice, randint, random
from io import BytesIO
import base64
import math as m

# diacritic list
marks = list(map(chr, range(768, 879)))

# numbers to words
under_20 = [
    "",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
tens = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]


def num_to_word(num):
    """Converts a positive number under 100 to english words"""
    if num < 0 or num >= 100:
        raise Exception("Numbers to convert must be between 0 and 100, non inclusive")
    if num == 0:
        return "zero"
    if num < 20:
        return under_20[num]
    else:
        ten = tens[int(num / 10)]
        one = under_20[num % 10]
        return f"{ten} {one}".strip()


def zalgo(string, num):
    """Zalgo-ifies a <string> with <num> diacritics"""
    words = string.split()
    for i, word in enumerate(words):
        words[i] = "".join(
            c + "".join([choice(marks) for _ in range(num)]) for c in word
        )
    return " ".join(words)


class ImageDeformer:
    """Slightly deforms an image"""

    def __init__(self, randomness=0, mag=4, freq=50, grid=5):
        self.w, self.h = 0, 0
        self.rand = randomness
        self.mag = mag  # wave magnitude
        self.freq = freq  # wave frequency
        self.grid = grid  # grid size

    def transform(self, x, y):
        mag = self.mag + random() * self.rand
        freq = self.freq + random() * self.rand
        y = y + mag * m.sin(freq * x)
        return x, y

    def transform_rectangle(self, x0, y0, x1, y1):
        return (
            *self.transform(x0, y0),
            *self.transform(x0, y1),
            *self.transform(x1, y1),
            *self.transform(x1, y0),
        )

    def getmesh(self, img):
        """Implement getmesh() function for ImageOps.deform()"""
        self.w, self.h = img.size

        target_grid = []
        for x in range(0, self.w, self.grid):
            for y in range(0, self.h, self.grid):
                target_grid.append((x, y, x + self.grid, y + self.grid))

        source_grid = [self.transform_rectangle(*rect) for rect in target_grid]

        return [t for t in zip(target_grid, source_grid)]


def string_to_image(string, size=50, color=(0, 0, 0)):
    """Outputs an HTML image tag with the embedded image"""
    # over-estimate image size based on font size
    width = size * len(string)
    height = 2 * size

    # create image
    img = Image.new(
        "RGBA", (width, height), (0, 0, 0, 0)
    )  # define completely transparent image
    font = ImageFont.truetype("flask_app/static/fonts/GOODDC.TTF", size)  # load a font
    draw = ImageDraw.Draw(img)  # get drawing context
    draw.text(
        (0, 0), string, font=font, fill=color
    )  # write the text onto the image with that font
    bbox = draw.textbbox((0, 0), string, font=font)
    img = img.crop(bbox)  # crop image to that size
    img = ImageOps.deform(img, ImageDeformer())  # distort image
    return img


def image_to_html(image, size=None):
    """
    Convert a PIL image to an HTML img tag with a base64 encoded PNG image.
    Size is a tuple (width, height)
    """
    if not size:
        size = image.size
    width = size[0]
    height = size[1]
    output = BytesIO()
    image.save(output, format="PNG")  # save PNG image to bytes object
    data = base64.b64encode(output.getvalue()).decode()  # base64 encode for img tag
    # return f'<img src="data:image/png;base64,{data}" width="{width}" height="{height}">'  # return HTML
    return f"data:image/png;base64,{data}"  # return img source


def generate_math():
    """
    Generates a random math problem in english words.
    Returns an HTML img tag with the raw img embedded and the corresponding answer as a string.
    """
    op = choice(["plus", "minus"])
    if op == "plus":
        a = randint(0, 20)
        b = randint(0, 20)
        answer = a + b
    elif op == "minus":
        a = randint(0, 10)
        b = randint(0, a)
        answer = a - b
    else:  # just in case
        op, a, b = "plus", randint(0, 10), randint(0, 10)
        answer = a + b

    answer = int(answer)
    question = f"What is {num_to_word(a)} {op} {num_to_word(b)}?"
    text_question = question
    # question = zalgo(question, 1)  # Need to use a font that supports combining diacritic marks
    question = string_to_image(
        question, color=(0, 150, 255)
    )  # convert question to image
    question = image_to_html(question)  # convert to image tag
    return question, answer, text_question


if __name__ == "__main__":
    import os

    os.chdir("../../")
    img = string_to_image("What is two minus two?", color=(0, 100, 200))
    img.show()
