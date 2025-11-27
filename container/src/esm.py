from io import BytesIO
from transformers import AutoModel, AutoTokenizer, EsmModel, EsmTokenizer
from transformers.modeling_outputs import BaseModelOutputWithPoolingAndCrossAttentions
from Bio import SeqIO
import numpy as np
import torch
from utils.checkpointing import JobData, InputFile
from itertools import batched


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
model_id = "facebook/esm2_t6_8M_UR50D"
tokenizer: EsmTokenizer = AutoTokenizer.from_pretrained(model_id)
model: EsmModel = AutoModel.from_pretrained(model_id).to(device)
PROTEIN_CHUNK_SIZE = model.config.max_position_embeddings - tokenizer.num_special_tokens_to_add()  # accounting for special tokens


def process_protein(file_path: str) -> bytes:
    first_fasta, *other_fasta = list(SeqIO.parse(file_path, "fasta"))
    if other_fasta:
        raise ValueError("Input FASTA file contains multiple sequences; only single sequence files are supported.")

    sequence = str(first_fasta.seq)
    chunks = [sequence[i:i+PROTEIN_CHUNK_SIZE] for i in range(0, len(sequence), PROTEIN_CHUNK_SIZE)]
    inputs = tokenizer(chunks, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        outputs: BaseModelOutputWithPoolingAndCrossAttentions = model(**inputs)
    embedding = outputs.last_hidden_state.numpy(force=True)  # Currently, the embedding is not averaged over the residues, giving a per-residue embedding
    stream = BytesIO()
    np.save(stream, embedding)
    stream.seek(0)
    return stream.read()


def main_individual():
    print("Job started.")
    job_data = JobData("*.fasta", "*.npy")
    job_data.process_files(process_protein)
    print("Job completed.")


def process_protein_batch(file_paths: list[str]) -> list[bytes]:
    fastas = []
    for file_path in file_paths:
        first_fasta, *other_fasta = list(SeqIO.parse(file_path, "fasta"))
        if other_fasta:
            raise ValueError("Input FASTA file contains multiple sequences; only single sequence files are supported.")
        fastas.append(first_fasta)

    sequences = [str(fasta.seq) for fasta in fastas]
    chunks: list[str] = []
    seq_sizes: list[int] = []
    for sequence in sequences:
        chunked = [sequence[i:i+PROTEIN_CHUNK_SIZE] for i in range(0, len(sequence), PROTEIN_CHUNK_SIZE)]
        chunks.extend(chunked)
        seq_sizes.append(len(chunked))

    inputs = tokenizer(chunks, return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        outputs: BaseModelOutputWithPoolingAndCrossAttentions = model(**inputs)
    embedding = outputs.last_hidden_state.numpy(force=True)  # Currently, the embedding is not averaged over the residues, giving a per-residue embedding

    embeds: list[bytes] = []
    curr = 0; prev = 0
    for size in seq_sizes:
        prev = curr
        curr += size
        data = embedding[prev:curr]

        stream = BytesIO()
        np.save(stream, data)
        stream.seek(0)
        embeds.append(stream.read())
    return embeds


BATCH_SIZE = 100  # Careful! The larger the batch, the lower the fault tolerance
def main_batched():
    print("Job started.")
    with JobData("*.fasta", "*.npy") as job_data:
        for input_files in batched(job_data.input_files(), BATCH_SIZE):
            outs = process_protein_batch([input_file.path for input_file in input_files])
            for input_file, out in zip(input_files, outs):
                job_data.write(input_file, out)
    print("Job completed.")


if __name__ == "__main__":
    main_individual()
