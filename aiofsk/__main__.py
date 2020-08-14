import asyncio
from aiofsk.transport import AFSKTransport


async def text_console(modem):
    def _text_console():
        while True:
            text = input(">> ")
            if 'quit' in text:
                return
            modem.write(text.encode())
    try:
        return await asyncio.get_event_loop().run_in_executor(None, _text_console)
    finally:
        modem.stop()


async def main():
    # modem = AFSKTransport(baud=300, loopback=False, modulator='nrzi')
    modem = AFSKTransport(baud=300, loopback=False, modulator='standard')

    terminal_task = asyncio.create_task(text_console(modem))
    try:
        await modem.connect_and_run_forever()
    finally:
        if not terminal_task.done():
            terminal_task.cancel()


if __name__ == '__main__':
    asyncio.run(main())
