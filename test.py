import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine
from models import PushUpLog, UserTotal

# Load environment variables
load_dotenv()

# Get the database URL from the environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)


def clear_all_tables():
    # Drop all tables
    SQLModel.metadata.drop_all(engine)

    # Recreate all tables
    SQLModel.metadata.create_all(engine)

    print("All tables have been cleared and recreated.")


if __name__ == "__main__":
    clear_all_tables()
