import os


current_file = os.path.abspath(__file__)
CURRENT_DIR = os.path.dirname(current_file)


DATA_DIR_NAME = "data"
DATA_DIR_PATH = os.path.join(CURRENT_DIR, DATA_DIR_NAME)

NODE_ID_FILE_NAME = "node_id"
NODE_ID_FILE_PATH = os.path.join(DATA_DIR_PATH, NODE_ID_FILE_NAME)
