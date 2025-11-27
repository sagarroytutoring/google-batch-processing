import threading
import time
import os
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Iterator, BinaryIO
from .intspan import IntSpan
from .star_format import StarFormat


@dataclass
class InputFile:
    idx: str
    data: BinaryIO


DEFAULT_INTERVAL = int(os.environ['CHECKPOINT_INTERVAL'])


class JobData(ABC):
    def __init__(self,
        output_format: str,
        interval: Optional[int]=None,
        complete_mode: Optional[str]=None,
        span: Optional[str]=None,
    ) -> None:
        input_path = os.environ['INPUT_BUCKET_PATH']
        output_path = os.environ['OUTPUT_BUCKET_PATH']
        print(f"Initializing JobData for input: {input_path}")
        self._input_path = os.path.join(os.environ['INPUT_MOUNT_PATH'], input_path)
        self._output_path = os.path.join(os.environ['OUTPUT_MOUNT_PATH'], output_path)
        if not os.path.exists(self._input_path):
            print("Input directory contents: " + str(os.listdir(os.environ['INPUT_MOUNT_PATH'])))
            raise ValueError("Input path does not exist in input bucket")
        os.makedirs(self._output_path, exist_ok=True)

        self._output_format = StarFormat(output_format)

        self._interval = interval or DEFAULT_INTERVAL
        self._output_dict: dict[str, bytes] = {}
        self._output_lock = threading.Lock()
        self._running_flush = False

        self._complete_mode = complete_mode or os.environ['COMPLETE_MODE']
        spanstr = os.environ['SPAN'] if span is None else span  # Cannot use 'or' because '' is valid
        self._span = IntSpan(spanstr) if spanstr else None

        self._ins_list = self._list_ins()
        self.__job_ins_range = self._job_ins_range()
        self._first_attempt_init()
        print(f"Job initialized for path: {input_path}")
        print(f"Number of inputs to process for task: {self.__job_ins_range[1] - self.__job_ins_range[0]}")

    @abstractmethod
    def _list_all_input_idxs(self) -> list[Optional[str]]:
        pass

    def _list_ins(self) -> list[str]:
        # Create a set of indices to include, if a span is specified
        spanset = set(self._span) if self._span else None

        # Create a set of indices to exclude, if in REMAINING mode
        # Otherwise, all files matching the input format are included, redoing any previously completed
        outset = set()
        if self._complete_mode == 'REMAINING':
            filenames = [os.path.basename(path) for path in os.environ["OUTPUT_BUCKET_FILES"].split()[1:]]  # Skip folder  (TODO: check if splitting logic is right)
            for filename in filenames:
                idx = self._output_format.match(filename)
                if idx is not None:
                    outset.add(idx)
        print(f"Excluding {len(outset)} completed files from processing.")

        # List input indices based on the above sets
        idxs = self._list_all_input_idxs()
        print(f"Found {len(idxs)} inputs.")
        ins = set()
        idx_nones = 0
        for idx in idxs:
            idx_nones += idx is None
            if idx is not None and (spanset is None or int(idx) in spanset) and (idx not in outset):
                ins.add(idx)
        print("Number of inputs not matching format:", idx_nones)
        print("Number of inputs passing filters:", len(ins))
        return sorted(ins)

    def _job_ins_range(self) -> tuple[int, int]:
        ins_count = len(self._ins_list)
        job_count = int(os.environ['BATCH_TASK_COUNT'])
        job_index = int(os.environ['BATCH_TASK_INDEX'])

        print(f"Total inputs to process: {ins_count}")
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
            output_path = os.path.join(self._output_path, self._output_format.format(self._ins_list[i]))
            if os.path.exists(output_path):
                print(f"Removing existing output file: {output_path}")
                os.remove(output_path)
        print("Cleared output files for this task's input files.")

    @abstractmethod
    def _stream_from_idx(self, idx) -> BinaryIO:
        pass

    def input_files(self) -> Iterator[InputFile]:  # FLAGGED
        start_idx, end_idx = self.__job_ins_range

        for i in range(start_idx, end_idx):
            # This check is here because in task retries, some files may have been completed in previous attempts
            # If this is the first attempt, all output files would have been cleared already, so all files are included
            if os.path.exists(os.path.join(self._output_path, self._output_format.format(self._ins_list[i]))):
                continue

            idx = self._ins_list[i]
            f = self._stream_from_idx(idx)
            yield InputFile(idx=idx, data=f)

    def write(self, input_file: InputFile, data: bytes) -> None:
        with self._output_lock:
            self._output_dict[input_file.idx] = data

    def _flush(self):
        print("Flushing output data.")
        with self._output_lock:
            for idx, data in self._output_dict.items():
                output_path = os.path.join(self._output_path, self._output_format.format(idx))
                with open(output_path, 'wb') as f:
                    f.write(data)
            print(f"Wrote {len(self._output_dict)} output files.")
            self._output_dict.clear()

    def __enter__(self):
        print(f"Entering JobData context at input dir {self._input_path}")  # FLAGGED
        def _flush_periodically():
            while self._running_flush:
                time.sleep(self._interval)
                self._flush()
        self._running_flush = True
        threading.Thread(target=_flush_periodically, daemon=True).start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f"Exiting JobData context at input dir {self._input_path}")  # FLAGGED
        self._running_flush = False
        self._flush()

    def process_files(self, process_function: Callable[[BinaryIO], bytes]) -> None:
        with self:
            for input_file in self.input_files():
                processed_data = process_function(input_file.data)
                self.write(input_file, processed_data)

    @classmethod
    def get_data(
        cls,
        input: Callable[[str], list[tuple[str, BinaryIO]]] | str,
        output_format: str,
        interval: Optional[int]=None,
        complete_mode: Optional[str]=None,
        span: Optional[str]=None
    ):
        packed = os.environ['INPUT_PACKED'].lower() == 'true'
        return (
            JobDataSingleFile(input, output_format, interval=interval, complete_mode=complete_mode, span=span)
            if packed else
            JobDataMultiFile(input, output_format, interval=interval, complete_mode=complete_mode, span=span)
        )


class JobDataSingleFile(JobData):
    def __init__(
        self,
        input_unpacker: Callable[[str], list[tuple[str, BinaryIO]]],
        output_format: str,
        interval: Optional[int]=None,
        complete_mode: Optional[str]=None,
        span: Optional[str]=None,
    ) -> None:
        self._input_unpacker = input_unpacker
        self._input_unpacked: Optional[dict[str, BinaryIO]] = None
        super().__init__(output_format, interval=interval, complete_mode=complete_mode, span=span)

    def _list_all_input_idxs(self) -> list[Optional[str]]:
        # This is the first usage of the unpacked input, so I just unpack it here. It's difficult to unpack it any earlier
        if self._input_unpacked is None:
            self._input_unpacked = dict(self._input_unpacker(self._input_path))
        return list(self._input_unpacked.keys())

    def _stream_from_idx(self, idx) -> BinaryIO:
        return self._input_unpacked[idx]


class JobDataMultiFile(JobData):
    def __init__(
        self,
        input_format: str,
        output_format: str,
        interval: Optional[int]=None,
        complete_mode: Optional[str]=None,
        span: Optional[str]=None
    ) -> None:
        self._input_format = StarFormat(input_format)
        super().__init__(output_format, interval=interval, complete_mode=complete_mode, span=span)

    def _list_all_input_idxs(self) -> list[Optional[str]]:
        filenames = os.listdir(self._input_path)
        return [self._input_format.match(filename) for filename in filenames]

    def _stream_from_idx(self, idx) -> BinaryIO:
        file_path = os.path.join(self._input_path, self._input_format.format(idx))
        return open(file_path, 'rb')

