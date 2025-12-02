# Load model directly
from transformers import AutoTokenizer, AutoModel
import torch
import os
import numpy as np
from io import BytesIO, TextIOWrapper
from typing import BinaryIO
from utils.checkpointing import JobData


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
MODEL_NAME = "dmis-lab/biobert-v1.1"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)


def go_unpacker(file_path: str) -> list[tuple[str, BinaryIO]]:
    outputs = []
    with open(file_path, 'r') as f:
        current_go = ''
        go_def = ''
        for line in f:
            line = line.strip()
            if line.startswith('id: GO:'):
                current_go = line[len('id: GO:'):]
            elif line.startswith('def: ') and current_go:
                go_def = line[len('def: '):].strip('"')
                outputs.append((current_go, BytesIO(bytes(go_def, 'utf-8'))))
                current_go = ''; go_def = ''
    return outputs


INPUT_PACKED = os.environ['INPUT_PACKED'].lower() == 'true'
if not INPUT_PACKED:
    raise ValueError("This script only supports packed input currently.")
job_data = JobData.get_data(go_unpacker, "*.npy")


def process_go(data: BinaryIO) -> bytes:
    data_string = TextIOWrapper(data)
    inputs = tokenizer(data_string.read(), return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    embedding = outputs.last_hidden_state.numpy(force=True)  # Currently, the embedding is not averaged over the tokens, giving a per-token embedding

    stream = BytesIO()
    np.save(stream, embedding)
    stream.seek(0)
    np_data = stream.read()
    stream.close()
    return np_data


def main():
    print("Job started.")
    job_data.process_files(process_go)
    print("Job completed.")


if __name__ == '__main__':
    main()
