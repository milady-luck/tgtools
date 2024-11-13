from telethon import TelegramClient
from collections import defaultdict
from datetime import datetime, timedelta
from typing import NamedTuple

import asyncio
import os
import sys
import json

class TgUser(NamedTuple):
    uid: int
    uname: str

# NOTE: should I include datetime here too? Probably, for sorting
class TgMessage(NamedTuple):
    msg_id: int

    sender: TgUser
    message: str

    # TODO: make these class constructors work
    async def from_telethon_msg(client, telethon_msg) -> TgMessage:
        # get user from client
        uid = telethon_msg.from_id.user_id

        user = await client.get_entity(uid)
        return TgMessage(
            telethon_msg.id,
            TgUser(uid, user.username),
            telethon_msg.message
        )

    async def from_id(client, msg_id) -> TgMessage:
        msg = await client.get_entity(msg_id)
        return TgMessage.from_telethon_msg(client, msg)

# NOTE: assuming this is static for now
RICK_NAME = "RickBurpBot"
RICK_ID = 6126376117

class TgRickbotMessage(NamedTuple):
    call_msg: TgMessage # NOTE: None implies no caller (i.e. Rickbot ad)
    resp_msg: TgMessage

# NOTE: gets rickbot messages + rick caller 
async def get_recent_rickbot_messages(
    client: TelegramClient, 
    group_id: int, 
    start_time: datetime
) -> list[TgRickbotMessage]:
    client = TelegramClient('coin-mentions', API_ID, API_HASH)

    async with client:
        group = await client.get_entity(group_id)

        messages = await client.get_messages(
            group, 
            reverse=True, # necessary for offset_date to be min_date
            offset_date=start_time,
            max_id=0, 
            min_id=0
        )
        id_to_msg = {msg.id: msg for msg in messages}
        rick_msgs = [msg for msg in messages if msg.from_id.user_id == rick.id]

        # for all rickbot messages, get the parent message too and create a TgRickbotMessage
        ret = []
        for msg in rick_msgs:
            # rick message
            call_msg = None
            resp_msg = TgMessage(msg.id, TgUser(RICK_ID, RICK_NAME), msg.message)

            if msg.reply_to_msg_id:
                # if call message in id_to_msg, great. if not, go get it and add to map
                reply_to_id = msg.reply_to_msg_id
                if msg.reply_to_msg_id in id_to_msg:
                    call_msg = await TgMessage.from_telethon_msg(client, id_to_msg[msg.reply_to_msg_id])
                    
                else:
                    call_msg = await TgMessage.from_id(client, reply_to_id)

            ret.append(TgRickbotMessage(call_msg, resp_msg))

        return ret

if __name__ == "__main__":
    import json

    async def print_recent_rickbot_messages(client, group_id, start_time):
        rickbot_msgs = await get_recent_rickbot_messages(client, group_id, start_time)
        for msg in rickbot_msgs:
            print(json.dumps(msg._asdict(), indent=4))
            
    
    API_ID = int(os.getenv("TG_API_ID"))
    API_HASH = os.getenv("TG_API_HASH")
    TARGET_GROUP_ID = -1001639107971 

    client = TelegramClient('testing-rick-scraper', API_ID, API_HASH)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        print_recent_rickbot_messages(
            client, 
            TARGET_GROUP_ID, 
            datetime.now() - timedelta(minutes=10)
        )
    )