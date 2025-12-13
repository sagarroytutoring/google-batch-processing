import csv
from collections import defaultdict
from Bio import SeqIO

MOLECULAR_FUNCTION = "F"
BIOLOGICAL_PROCESS = "P"
CELLULAR_COMPONENT = "C"

def get_subtontology_proteins(
        subtontology: str = MOLECULAR_FUNCTION,
        tsv_file: str = "train_terms.tsv", 
        min_cutoff :int = 200,
        max_cutoff:int = 100,
        max_num_proteins:int = 10000
        ) -> list:
    
    with open(tsv_file, 'r', encoding='utf-8') as file:
        tsv_reader = csv.reader(file, delimiter='\t')
        GO_dict = defaultdict(set)

        for protein_name, go_func, sub in tsv_reader:
            if sub == subtontology:
                GO_dict[go_func].add(protein_name)

        common_proteins = set()
        for go_func in sorted(GO_dict,key=lambda k: len(GO_dict[k]), reverse= True):
            num_proteins = len(GO_dict[go_func])
            if min_cutoff < num_proteins or num_proteins < max_cutoff:
                continue
            elif max_num_proteins <= len(common_proteins) + num_proteins:
                break
            common_proteins.update(GO_dict[go_func])

    return common_proteins

def protein_list_to_fasta(
        protein_list: set,
        input_fasta_path: str = "train_sequences.fasta",
        output_fasta_path: str = "mf_subset.fasta"
    ):
    proteins_added = 0
    with open(output_fasta_path, "w", encoding="utf-8") as out_f:
        for record in SeqIO.parse(input_fasta_path, "fasta"):
            
            if record.id.split("|")[1] in protein_list:
                SeqIO.write(record, out_f, "fasta")
                proteins_added += 1

    return proteins_added

def linker_to_fasta(
        input_ref_file:str = "train_terms.tsv", 
        input_fasta_path: str = "train_sequences.fasta",
        subtontology: str = MOLECULAR_FUNCTION,
        output_fasta_path: str = "mf_subset.fasta"
        ):
    
    protein_list = get_subtontology_proteins(subtontology=subtontology, tsv_file=input_ref_file)
    num_proteins = protein_list_to_fasta(
        protein_list,
        input_fasta_path,
        output_fasta_path
    )
    print(f"Created fasta for {num_proteins} proteins")

linker_to_fasta()
