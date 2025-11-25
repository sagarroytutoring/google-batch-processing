from utils.checkpointing import JobData, InputFile


def main():
    print("Job started.")
    with JobData("input_*.txt", "output_*.txt") as job_data:
        for input_file in job_data.input_files():
            with open(input_file.path, 'r') as f:
                data = f.read()
            # Example processing: convert to uppercase
            processed_data = data.upper()
            job_data.write(input_file, bytes(processed_data, 'utf-8'))
    print("Job completed.")

def main_alt():
    print("Job started.")
    def process_function(file_path: str) -> bytes:
        with open(file_path, 'r') as f:
            data = f.read()
        # Example processing: convert to uppercase
        return bytes(data.upper(), 'utf-8')

    job_data = JobData("input_*.txt", "output_*.txt")
    job_data.process_files(process_function)
    print("Job completed.")



if __name__ == "__main__":
    main()
