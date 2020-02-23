import asyncio

async def hello():
    print("Hello")
    await asyncio.sleep(1)
    print("World!")

async def main():
    await asyncio.gather(hello(), hello(), hello())

if __name__ == "__main__":
    asyncio.run(main())
