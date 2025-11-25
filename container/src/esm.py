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


def process_function(file_path: str) -> bytes:
    fasta_sequences = list(SeqIO.parse(file_path, "fasta"))
    for fasta in fasta_sequences:
        sequence = str(fasta.seq)
        inputs = tokenizer(sequence, return_tensors="pt", padding=True, truncation=True).to(device)
        with torch.no_grad():
            outputs: BaseModelOutputWithPoolingAndCrossAttentions = model(**inputs)
        embedding = outputs.last_hidden_state.squeeze().numpy(force=True)  # Currently, the embedding is not averaged over the residues, giving a per-residue embedding
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
