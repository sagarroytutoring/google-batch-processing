#!/bin/bash
set -e

span=$SPAN
mode=$COMPLETE_MODE
task_count=$TASK_COUNT
parallelism=$PARALLELISM

while getopts "s:m:t:p:" opt; do
    case "$opt" in
        s) span="$OPTARG" ;;
        m) mode="$OPTARG" ;;
        t) task_count="$OPTARG" ;;
        p) parallelism="$OPTARG" ;;
        *) echo "Invalid option: $opt" && exit 1 ;;
    esac
done
shift $((OPTIND - 1))

export SPAN=${span}
export COMPLETE_MODE=${mode}
export TASK_COUNT=${task_count}
export PARALLELISM=${parallelism}
export ENTRYSCRIPT=${1}

output_bucket_json="tmp_ls.json"

gcloud storage ls gs://${OUTPUT_BUCKET_NAME}/${OUTPUT_BUCKET_PATH}/ 2> /dev/null -j > ${output_bucket_json} || :
python - <<EOF
import json
import os
with open("${output_bucket_json}", "r") as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        data = []
existing_files = [os.path.basename(item['metadata']['name']) for item in data]
with open("${OUTPUT_BUCKET_LS_NAME}", "w") as f:
    f.write("\n".join(existing_files))
EOF
rm -f ${output_bucket_json}

gcloud storage cp ${OUTPUT_BUCKET_LS_NAME} gs://${OUTPUT_BUCKET_NAME}/${OUTPUT_BUCKET_PATH}/${OUTPUT_BUCKET_LS_NAME} || :
rm -f ${OUTPUT_BUCKET_LS_NAME}

if [ -n "${GPU_TYPE}" ] && [ -n "${GPU_COUNT}" ]; then
    export INSTANCE_CONFIG=$(MSYS_NO_PATHCONV=1 envsubst < ./instances_w_gpu.json)
else
    export INSTANCE_CONFIG=$(MSYS_NO_PATHCONV=1 envsubst < ./instances_no_gpu.json)
fi

gcloud batch jobs submit --job-prefix=${1} --location=${REGION} --project=${PROJECT_ID} --config - <<EOF
$(MSYS_NO_PATHCONV=1 envsubst < ./batch_job.json)
EOF