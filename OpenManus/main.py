import argparse
import asyncio
import os
import warnings

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*TripleDES.*")
warnings.filterwarnings("ignore", message=".*underscore_attrs_are_private.*")

# Suppress PyTorch warnings through environment variables
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"

# Load .env file at the very beginning
from dotenv import load_dotenv
load_dotenv()

from app.agent.manus import Manus
from app.logger import logger


async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run Manus agent with a prompt")
    parser.add_argument(
        "--prompt", type=str, required=False, help="Input prompt for the agent"
    )
    args = parser.parse_args()

    # Create and initialize Manus agent
    agent = await Manus.create()
    try:
        # Use command line prompt if provided, otherwise ask for input
        prompt = args.prompt if args.prompt else input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")
    finally:
        # Ensure agent resources are cleaned up before exiting
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
