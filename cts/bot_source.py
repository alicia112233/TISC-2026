"""Rebuild the selected CtS bot. Strategy: four dispersed compact bombers."""
from pathlib import Path
from build_bots import distributed

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    bot = distributed(step=4100, count=1, fast=True, sites=0x2000)
    size = bot.save(root / "bot")
    import hashlib
    print(f"Built bot.bin and bot.hex: {size} bytes")
    print("SHA256", hashlib.sha256(bot.binary()).hexdigest())
