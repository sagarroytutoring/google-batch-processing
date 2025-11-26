import threading
import time
import os
from dataclasses import dataclass
from typing import Optional, Callable
from .intspan import IntSpan
from .star_format import StarFormat


@dataclass
class InputFile:
    idx: str
    path: str


class JobData:
    def __init__(
            self,
            input_format: str,
            output_format: str,
            interval: Optional[int]=None,
            complete_mode: Optional[str]=None,
            span: Optional[str]=None
        ) -> None:

        input_subdir = os.environ['INPUT_BUCKET_PATH']
        output_subdir = os.environ['OUTPUT_BUCKET_PATH']
        print(f"Initializing JobData for subdir: {input_subdir}")
        self._input_dir = os.path.join(os.environ['INPUT_MOUNT_PATH'], input_subdir)
        self._output_dir = os.path.join(os.environ['RESULT_MOUNT_PATH'], output_subdir)
        if not os.path.exists(self._input_dir):
            print("Input directory contents: " + str(os.listdir(os.environ['INPUT_MOUNT_PATH'])))
            raise ValueError("Subdirectory does not exist in input bucket")
        os.makedirs(self._output_dir, exist_ok=True)

        self._input_format = StarFormat(input_format)
        self._output_format = StarFormat(output_format)

        self._interval = interval or 15
        self._output_dict: dict[str, bytes] = {}
        self._output_lock = threading.Lock()
        self._running_flush = False

        self._complete_mode = complete_mode or os.environ['COMPLETE_MODE']
        spanstr = os.environ['SPAN'] if span is None else span  # Cannot use 'or' because '' is valid
        self._span = IntSpan(spanstr) if spanstr else None

        self._ins_list = self._list_ins()
        self.__job_ins_range = self._job_ins_range()
        self._first_attempt_init()
        print(f"Job initialized for subdir: {input_subdir}")
        print(f"Number of input files to process: {self.__job_ins_range[1] - self.__job_ins_range[0]}")

    def _list_ins(self) -> list[str]:
        # Create a set of indices to include, if a span is specified
        spanset = set(self._span) if self._span else None

        # Create a set of indices to exclude, if in REMAINING mode
        # Otherwise, all files matching the input format are included, redoing any previously completed
        outset = set()
        if self._complete_mode == 'REMAINING':
            filenames = [os.path.basename(path) for path in os.environ["OUTPUT_BUCKET_FILES"].split()[1:]]  # Skip folder path
            for filename in filenames:
                idx = self._output_format.match(filename)
                if idx is not None:
                    outset.add(idx)

        # List input indices based on the above sets
        ins = set()
        for filename in os.listdir(self._input_dir):
            idx = self._input_format.match(filename)
            if idx is not None and (spanset is None or int(idx) in spanset) and (idx not in outset):
                ins.add(idx)
        return sorted(ins)

    def _job_ins_range(self) -> tuple[int, int]:
        ins_count = len(self._ins_list)
        job_count = int(os.environ['BATCH_TASK_COUNT'])
        job_index = int(os.environ['BATCH_TASK_INDEX'])

        print(f"Total input files to process: {ins_count}")
        print(f"Total job tasks: {job_count}, current task index: {job_index}")

        min_ins, rem_ins = divmod(ins_count, job_count)
        start_idx = job_index * min_ins + min(job_index, rem_ins)
        end_idx = start_idx + min_ins + (job_index < rem_ins)
        return start_idx, end_idx
    
    def _first_attempt_init(self) -> None:
        if os.environ['BATCH_TASK_RETRY_ATTEMPT'] != '0':
            return

        print("First attempt for this task, clearing output files for this task's input files.")
        start_idx, end_idx = self.__job_ins_range
        for i in range(start_idx, end_idx):
            output_path = os.path.join(self._output_dir, self._output_format.format(self._ins_list[i]))
            if os.path.exists(output_path):
                print(f"Removing existing output file: {output_path}")
                os.remove(output_path)
        print("Cleared output files for this task's input files.")

    def input_files(self) -> list[InputFile]:
        start_idx, end_idx = self.__job_ins_range
        return [
            InputFile(
                idx=self._ins_list[i],
                path=os.path.join(self._input_dir, self._input_format.format(self._ins_list[i]))
            )
            for i in range(start_idx, end_idx)

            # This check is here because in task retries, some files may have been completed in previous attempts
            # If this is the first attempt, all output files would have been cleared already, so all files are included
            if not os.path.exists(os.path.join(self._output_dir, self._output_format.format(self._ins_list[i])))
        ]

    def write(self, input_file: InputFile, data: bytes) -> None:
        with self._output_lock:
            self._output_dict[input_file.idx] = data

    def _flush(self):
        print("Flushing output data.")
        with self._output_lock:
            for idx, data in self._output_dict.items():
                output_path = os.path.join(self._output_dir, self._output_format.format(idx))
                with open(output_path, 'wb') as f:
                    f.write(data)
            self._output_dict.clear()
        print("Flushed output data.")

    def __enter__(self):
        print(f"Entering JobData context at input dir {self._input_dir}")
        def _flush_periodically():
            while self._running_flush:
                time.sleep(self._interval)
                self._flush()
        self._running_flush = True
        threading.Thread(target=_flush_periodically, daemon=True).start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f"Exiting JobData context at input dir {self._input_dir}")
        self._running_flush = False
        self._flush()

    def process_files(self, process_function: Callable[[str], bytes]) -> None:
        with self:
            for input_file in self.input_files():
                processed_data = process_function(input_file.path)
                self.write(input_file, processed_data)
