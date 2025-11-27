from utils.checkpointing import JobData, InputFile
from typing import BinaryIO


def main():
    print("Job started.")
    with JobData.get_data("input_*.txt", "output_*.txt") as job_data:
        for input_file in job_data.input_files():
            # Example processing: convert to uppercase
            input_bytes = input_file.data.read()
            input_file.data.close()
            output_bytes = bytes(input_bytes.decode(encoding='utf-8').upper(), 'utf-8')
            job_data.write(input_file, output_bytes)
    print("Job completed.")


def main_alt():
    print("Job started.")
    def process_function(data: BinaryIO) -> bytes:
        # Example processing: convert to uppercase
        input_bytes = data.read()
        data.close()
        return bytes(input_bytes.decode(encoding='utf-8').upper(), 'utf-8')

    job_data = JobData.get_data("input_*.txt", "output_*.txt")
    job_data.process_files(process_function)
    print("Job completed.")


if __name__ == "__main__":
    main()
