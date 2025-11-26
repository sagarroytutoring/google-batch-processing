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
export OUTPUT_BUCKET_FILES=$(gcloud storage ls gs://${OUTPUT_BUCKET_NAME}/${OUTPUT_BUCKET_PATH}/ 2> /dev/null || :)

if [ -n "${GPU_TYPE}" ] && [ -n "${GPU_COUNT}" ]; then
    export INSTANCE_CONFIG=$(MSYS_NO_PATHCONV=1 envsubst < ./instances_w_gpu.json)
else
    export INSTANCE_CONFIG=$(MSYS_NO_PATHCONV=1 envsubst < ./instances_no_gpu.json)
fi

gcloud batch jobs submit --job-prefix=${1} --location=${REGION} --project=${PROJECT_ID} --config - <<EOF
$(MSYS_NO_PATHCONV=1 envsubst < ./batch_job.json)
EOF