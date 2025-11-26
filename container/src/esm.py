from io import BytesIO
from transformers import AutoModel, AutoTokenizer, EsmModel, EsmTokenizer
from transformers.modeling_outputs import BaseModelOutputWithPoolingAndCrossAttentions
from Bio import SeqIO
import numpy as np
import torch
from utils.checkpointing import JobData, InputFile


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
model_id = "facebook/esm2_t6_8M_UR50D"
tokenizer: EsmTokenizer = AutoTokenizer.from_pretrained(model_id)
model: EsmModel = AutoModel.from_pretrained(model_id).to(device)
PROTEIN_CHUNK_SIZE = model.config.max_position_embeddings - tokenizer.num_special_tokens_to_add()  # accounting for special tokens


def process_function(file_path: str) -> bytes:
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


def main():
    print("Job started.")
    job_data = JobData("*.fasta", "*.npy")
    job_data.process_files(process_function)
    print("Job completed.")


if __name__ == "__main__":
    main()
