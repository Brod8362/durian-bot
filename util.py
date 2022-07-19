#!/bin/python3
from bdb import effective
from PIL import Image, ImageDraw, ImageFont
import asyncio
import requests
from io import BytesIO

AVATAR_CACHE = {}

class PhonyDiscordUser:
    def __init__(self, id, name, avatar):
        self.id = id
        self.name = name
        self.avatar_url = avatar

class PhonyDiscord:
    def __init__(self):
        self.users = {
            188453877438218240: PhonyDiscordUser(188453877438218240, "Brod8362", "https://cdn.discordapp.com/avatars/188453877438218240/fe8a27a65d316dedc1031137f1f46000.webp?size=128"),
            226521865537978368: PhonyDiscordUser(226521865537978368, "score", "https://cdn.discordapp.com/avatars/226521865537978368/3292512395ebe0dc95a21fa00fa8eb1a.webp?size=128"),
            191222014705532928: PhonyDiscordUser(191222014705532928, "lettuce", "https://cdn.discordapp.com/avatars/191222014705532928/12e5df7c4b6bc16ec7c86f684df13cb8.webp?size=128"),
            168612709036720129: PhonyDiscordUser(168612709036720129, "Nozomi", "https://cdn.discordapp.com/avatars/168612709036720129/ceec24d42754c11077e6f2851c56b708.webp?size=128")
        }

    async def fetch_user(self, uid):
        return self.users[uid]

def nice_time(seconds) -> str:
    units = {
        "d": 60*60*24,
        "h": 60*60,
        "m": 60,
        "s": 1
    }
    remaining = int(seconds)
    output = []
    for unit in units:
        ratio = remaining/units[unit]
        if ratio >= 1.0:
            remaining -= int(ratio)*units[unit]
            output.append(f"{int(ratio)}{unit}")
    return " ".join(output)


IMAGE_WIDTH = 384
ROW_HEIGHT = 32
AVATAR_DIM = ROW_HEIGHT
BAR_HEIGHT = 10
BAR_SIDE_MARGIN = 16
BAR_TOP_MARGIN = 16
BAR_MAX_LENGTH = IMAGE_WIDTH - BAR_SIDE_MARGIN*2 - AVATAR_DIM
BAR_LEFT_EDGE = AVATAR_DIM + BAR_SIDE_MARGIN
BAR_POSITION_COLORS = {
    0: (255, 215, 0), #gold
    1: (192, 192, 192), #silver
    2: (205, 127, 50), #bronze
}
BAR_DEFAULT_COLOR = (255,255,255) #white
BAR_USER_COLOR = (0, 255, 0) #green

async def generate_image(leaderboard: "list[tuple[int, int]]", generating_user: int, discord, lb_size = 10) -> Image:
    effective_leaderboard = leaderboard[:lb_size]
    #TODO: add generating user on the end if they're not in it 
    if sum(1 for x in effective_leaderboard if x[0] == generating_user) == 0:
        potential_user = filter(lambda x: x[0] == generating_user, leaderboard)
        try:
            effective_leaderboard.append(next(potential_user))
        except:
            effective_leaderboard.append((generating_user, 0))
    image_segments = []
    ## generate header
    text_font = ImageFont.truetype("font.ttf", 16)
    header: Image.Image = Image.new("RGBA", (IMAGE_WIDTH, 32))
    header_draw = ImageDraw.Draw(header)
    header_draw.text((0, 0), "Durian Leaderboard", font=text_font)
    image_segments.append(header)
    max_score = max(map(lambda x: x[1], leaderboard))
    ## generate user rows
    for (index, (user_id, score)) in enumerate(effective_leaderboard):
        print(index)
        row = Image.new("RGBA", (IMAGE_WIDTH, ROW_HEIGHT))
        user = await discord.fetch_user(user_id)
        
        if user_id not in AVATAR_CACHE:
            avatar_url = user.avatar_url
            resp = requests.get(avatar_url)
            if resp.status_code != 200:
                print("failed to get user avatar")
            temp_image = Image.open(BytesIO(resp.content))
            temp_image = temp_image.resize((ROW_HEIGHT, ROW_HEIGHT))
            AVATAR_CACHE[user_id] = temp_image

        avatar_i = AVATAR_CACHE[user_id]
        row.paste(avatar_i, None)
        row_draw = ImageDraw.Draw(row)
        bar_color = BAR_USER_COLOR
        if user_id != generating_user:
            bar_color = BAR_POSITION_COLORS.get(index, BAR_DEFAULT_COLOR)
        row_draw.text((ROW_HEIGHT, 0), f"{user.name} ({nice_time(score)})", fill=bar_color)
        bar_length = (score/max_score)*BAR_MAX_LENGTH
        row_draw.rounded_rectangle((BAR_LEFT_EDGE, BAR_TOP_MARGIN, BAR_LEFT_EDGE+bar_length, BAR_TOP_MARGIN+BAR_HEIGHT), fill=bar_color, radius = 4)
        image_segments.append(row)
        
    total_height = sum(map(lambda x: x.height, image_segments))
    final = Image.new("RGBA", (IMAGE_WIDTH,total_height))
    final_draw = ImageDraw.Draw(final)
    final_draw.rectangle((0, 0, IMAGE_WIDTH, total_height), fill=(0,0,0))
    y_pos = 0
    for s in image_segments:
        final.paste(s, (0, y_pos), s)
        y_pos += s.height
    return final

# just for tesing
if __name__ == "__main__":
    leaderboard = [
        (226521865537978368, 99999),
        (188453877438218240, 10000),
        (191222014705532928, 5000),
        # (168612709036720129, 2500),
    ]
    loop = asyncio.new_event_loop()
    image = loop.run_until_complete(generate_image(leaderboard, 168612709036720129, PhonyDiscord(), lb_size=5))
    image.show()